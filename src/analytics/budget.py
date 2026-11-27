from __future__ import annotations

import pandas as pd

from ..models import CanonicalDataset


def revised_budget(dataset: CanonicalDataset, as_of: pd.Timestamp) -> float:
    targets = dataset.working["Targets"].copy()
    targets = targets[targets["effective_at"].le(as_of)].sort_values("effective_at")
    if targets.empty:
        return 0.0
    return float(targets.iloc[-1]["marketing_budget_inr"])


def campaign_spend(dataset: CanonicalDataset, as_of: pd.Timestamp, campaign_id: str | None = None) -> float:
    daily = dataset.working["Daily Marketing"].copy()
    end_date = as_of.normalize()
    daily = daily[daily["activity_date"].notna() & daily["activity_date"].le(end_date)]
    if campaign_id is not None:
        daily = daily[daily["campaign_id"].eq(campaign_id)]
    return float(pd.to_numeric(daily["marketing_spend_inr"], errors="coerce").fillna(0).sum())
