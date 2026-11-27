from __future__ import annotations

import pandas as pd

from ..models import CanonicalDataset


def valid_external_attendance(dataset: CanonicalDataset, as_of: pd.Timestamp) -> tuple[pd.DataFrame, set[str]]:
    people = dataset.working["People"]
    checkins = dataset.working["Check-ins"]
    external_ids = set(people.loc[people["person_type"].eq("external"), "person_id"].dropna())

    valid = checkins[
        checkins["result"].eq("admitted")
        & checkins["verification"].eq("verified")
        & checkins["occurred_at"].notna()
        & checkins["occurred_at"].le(as_of)
        & checkins["person_id"].isin(external_ids)
    ].copy()
    valid_person_ids = set(valid["person_id"].dropna())
    return valid, valid_person_ids


def attendance_by_day(valid: pd.DataFrame) -> dict[str, int]:
    if valid.empty:
        return {}
    daily = valid.assign(day=valid["occurred_at"].dt.strftime("%Y-%m-%d"))
    return daily.groupby("day")["person_id"].nunique().to_dict()
