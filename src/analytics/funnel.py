from __future__ import annotations

import pandas as pd

from ..models import CanonicalDataset
from .attendance import valid_external_attendance


def external_people(dataset: CanonicalDataset) -> set[str]:
    people = dataset.working["People"]
    return set(people.loc[people["person_type"].eq("external"), "person_id"].dropna())


def latest_registration_status(dataset: CanonicalDataset, as_of: pd.Timestamp) -> pd.DataFrame:
    history = dataset.working["Registration History"]
    eligible = history[
        history["effective_at"].notna()
        & history["effective_at"].le(as_of)
    ].copy()
    if eligible.empty:
        return pd.DataFrame(columns=history.columns)
    return eligible.sort_values(["registration_id", "effective_at", "history_id"]).groupby(
        "registration_id", as_index=False
    ).tail(1)


def identified_funnel(dataset: CanonicalDataset, as_of: pd.Timestamp) -> dict[str, int]:
    engagement = dataset.working["Interest and Engagement"]
    engagement = engagement[
        engagement["occurred_at"].notna()
        & engagement["occurred_at"].le(as_of)
    ]
    external_ids = external_people(dataset)

    page_visitors = engagement[
        engagement["event_type"].eq("page_visit")
        & engagement["person_id"].isin(external_ids)
    ]["person_id"].nunique()
    registration_starters = engagement[
        engagement["event_type"].eq("registration_start")
        & engagement["person_id"].isin(external_ids)
    ]["person_id"].nunique()
    brochure_downloaders = engagement[
        engagement["event_type"].eq("brochure_download")
        & engagement["person_id"].isin(external_ids)
    ]["person_id"].nunique()

    registrations = dataset.working["Registrations"]
    external_registrations = registrations[
        registrations["person_id"].isin(external_ids)
        & registrations["registered_at"].le(as_of)
    ]
    external_registration_ids = set(external_registrations["registration_id"].dropna())

    latest = latest_registration_status(dataset, as_of)
    confirmed_ids = set(
        latest.loc[latest["status"].eq("confirmed"), "registration_id"].dropna()
    ) & external_registration_ids

    _, attendee_ids = valid_external_attendance(dataset, as_of)
    registered_attendees = len(
        attendee_ids & set(external_registrations["person_id"].dropna())
    )

    return {
        "identified_page_visitors": int(page_visitors),
        "registration_starters": int(registration_starters),
        "external_registrations": len(external_registration_ids),
        "confirmed_external_registrations": len(confirmed_ids),
        "registered_attendees": registered_attendees,
        "brochure_downloaders": int(brochure_downloaders),
    }


def conversion_rate(numerator: int, denominator: int) -> float:
    return (numerator / denominator) if denominator else 0.0
