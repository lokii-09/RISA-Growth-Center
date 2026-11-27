from __future__ import annotations

from datetime import datetime

import pandas as pd

from ..models import CanonicalDataset, HistoricalBaseline
from .attendance import attendance_by_day, valid_external_attendance
from .budget import revised_budget, campaign_spend
from .campaigns import campaign_metrics
from .funnel import external_people, identified_funnel


def _as_timestamp(value: pd.Timestamp | datetime | str | None, dataset: CanonicalDataset) -> pd.Timestamp:
    if value is not None:
        return pd.Timestamp(value)
    event = dataset.working["Event"].iloc[0]
    return pd.Timestamp(event["event_ends_at"])


def calculate_historical_baseline(
    dataset: CanonicalDataset,
    as_of: pd.Timestamp | datetime | str | None = None,
) -> HistoricalBaseline:
    cutoff = _as_timestamp(as_of, dataset)
    external_ids = external_people(dataset)

    registrations = dataset.working["Registrations"]
    external_regs = registrations[
        registrations["person_id"].isin(external_ids)
        & registrations["registered_at"].notna()
        & registrations["registered_at"].le(cutoff)
    ]
    external_registration_ids = set(external_regs["registration_id"].dropna())

    from .funnel import latest_registration_status
    latest = latest_registration_status(dataset, cutoff)
    confirmed_ids = set(latest.loc[latest["status"].eq("confirmed"), "registration_id"].dropna())
    confirmed_external_ids = confirmed_ids & external_registration_ids

    valid_checkins, attendee_ids = valid_external_attendance(dataset, cutoff)
    registered_attendee_ids = attendee_ids & set(external_regs["person_id"].dropna())
    walk_ins = attendee_ids - set(external_regs["person_id"].dropna())

    spend = campaign_spend(dataset, cutoff)
    budget = revised_budget(dataset, cutoff)
    return HistoricalBaseline(
        as_of=cutoff.to_pydatetime(),
        identified_external_people=len(external_ids),
        external_registrations=len(external_registration_ids),
        confirmed_external_registrations=len(confirmed_external_ids),
        unique_external_attendees=len(attendee_ids),
        registered_attendees=len(registered_attendee_ids),
        walk_in_attendees=len(walk_ins),
        campaign_spend=spend,
        revised_budget=budget,
        budget_remaining=budget - spend,
    )


def calculate_all_kpis(
    dataset: CanonicalDataset,
    as_of: pd.Timestamp | datetime | str | None = None,
) -> dict[str, object]:
    cutoff = _as_timestamp(as_of, dataset)
    baseline = calculate_historical_baseline(dataset, cutoff)
    funnel = identified_funnel(dataset, cutoff)
    campaigns = campaign_metrics(dataset, cutoff)
    valid, attendee_ids = valid_external_attendance(dataset, cutoff)
    return {
        "baseline": baseline,
        "attendance_by_day": attendance_by_day(valid),
        "campaigns": campaigns,
        "funnel": funnel,
        "registered_show_rate": (
            baseline.registered_attendees / baseline.confirmed_external_registrations
            if baseline.confirmed_external_registrations else 0.0
        ),
        "page_visit_to_registration_rate": (
            funnel["external_registrations"] / funnel["identified_page_visitors"]
            if funnel["identified_page_visitors"] else 0.0
        ),
        "blended_cost_per_attendee": (
            baseline.campaign_spend / baseline.unique_external_attendees
            if baseline.unique_external_attendees else 0.0
        ),
    }
