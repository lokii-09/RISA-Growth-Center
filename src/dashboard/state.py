from __future__ import annotations

from typing import Dict, Mapping

import pandas as pd
import streamlit as st


def initialize_state() -> None:
    if "campaign_spend_overrides" not in st.session_state:
        st.session_state["campaign_spend_overrides"] = {}
    if "budget_override" not in st.session_state:
        st.session_state["budget_override"] = None


def campaign_spend_overrides() -> Dict[str, float]:
    return dict(st.session_state.get("campaign_spend_overrides", {}))


def set_campaign_spend(campaign_id: str, value: float) -> None:
    if value < 0:
        raise ValueError("Campaign spend cannot be negative.")
    overrides = campaign_spend_overrides()
    overrides[campaign_id] = float(value)
    st.session_state["campaign_spend_overrides"] = overrides


def set_total_budget(value: float) -> None:
    if value < 0:
        raise ValueError("Marketing budget cannot be negative.")
    st.session_state["budget_override"] = float(value)


def reset_budget_state() -> None:
    st.session_state["campaign_spend_overrides"] = {}
    st.session_state["budget_override"] = None


def effective_budget(historical_budget: float) -> float:
    override = st.session_state.get("budget_override")
    return float(historical_budget if override is None else override)


def apply_campaign_spend_edits(
    campaigns: pd.DataFrame,
    overrides: Mapping[str, float] | None = None,
) -> pd.DataFrame:
    result = campaigns.copy(deep=True)
    effective_overrides = campaign_spend_overrides() if overrides is None else dict(overrides)
    for campaign_id, value in effective_overrides.items():
        mask = result["campaign_id"].eq(campaign_id)
        if mask.any():
            result.loc[mask, "spend"] = float(value)
            attendee_count = int(result.loc[mask, "attributed_attendees"].iloc[0])
            result.loc[mask, "cost_per_attendee"] = (
                float(value) / attendee_count if attendee_count else None
            )
    return result
