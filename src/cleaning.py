from __future__ import annotations

import pandas as pd

from .models import CanonicalDataset, QualityIssue
from .validation import foreign_key_check


STABLE_IDS = {
    "Daily Marketing": "activity_id",
    "Interest and Engagement": "interaction_id",
    "People": "person_id",
    "Campaigns": "campaign_id",
    "Registrations": "registration_id",
    "Registration History": "history_id",
    "Check-ins": "event_id",
}

ALLOWED_PERSON_TYPES = {"external", "internal", "staff", "test"}
ALLOWED_HISTORY_STATUS = {"interested", "confirmed", "cancelled", "waitlisted"}
ALLOWED_CHECKIN_RESULT = {"admitted", "denied", "pending"}
ALLOWED_CHECKIN_VERIFICATION = {"verified", "unverified"}


def clean_dataset(dataset: CanonicalDataset) -> CanonicalDataset:
    working = {name: frame.copy(deep=True) for name, frame in dataset.working.items()}
    issues: list[QualityIssue] = list(dataset.quality.get("issues", []))

    for table, stable_id in STABLE_IDS.items():
        frame = working[table]
        missing_id = int(frame[stable_id].isna().sum())
        if missing_id:
            issues.append(QualityIssue(table, "missing_stable_id", missing_id, stable_id))
        identified = frame.loc[frame[stable_id].notna()]
        duplicated_rows = identified.loc[identified.duplicated(subset=[stable_id], keep=False)]
        if not duplicated_rows.empty:
            exact_groups = conflicting_groups = exact_extra = conflicting_extra = 0
            for _, group in duplicated_rows.groupby(stable_id, sort=False):
                extra_rows = len(group) - 1
                if group.drop(columns=[stable_id]).drop_duplicates().shape[0] == 1:
                    exact_groups += 1
                    exact_extra += extra_rows
                else:
                    conflicting_groups += 1
                    conflicting_extra += extra_rows
            issues.append(QualityIssue(
                table,
                "duplicate_stable_id_rows",
                len(duplicated_rows),
                stable_id,
                f"{exact_groups} exact groups ({exact_extra} extra rows); "
                f"{conflicting_groups} conflicting groups ({conflicting_extra} extra rows). "
                "Kept the first row per ID; rows without an ID were preserved.",
            ))
            frame = pd.concat([
                identified.drop_duplicates(subset=[stable_id], keep="first"),
                frame.loc[frame[stable_id].isna()],
            ]).sort_index(kind="stable")
            working[table] = frame

    people = working["People"]
    campaigns = working["Campaigns"]
    owners = people[["owner_id", "owner_name"]].drop_duplicates()

    for table in ("Registrations", "Registration History", "Check-ins", "Interest and Engagement", "Daily Marketing"):
        frame = working[table]
        bad_person = foreign_key_check(frame, "person_id", people, "person_id") if "person_id" in frame else pd.Series(False, index=frame.index)
        bad_campaign = foreign_key_check(frame, "campaign_id", campaigns, "campaign_id") if "campaign_id" in frame else pd.Series(False, index=frame.index)
        bad_owner = foreign_key_check(frame, "owner_id", owners, "owner_id") if "owner_id" in frame else pd.Series(False, index=frame.index)
        if bad_person.any():
            issues.append(QualityIssue(table, "orphan_person_id", int(bad_person.sum()), "person_id"))
        if bad_campaign.any():
            issues.append(QualityIssue(table, "orphan_campaign_id", int(bad_campaign.sum()), "campaign_id"))
        if bad_owner.any():
            issues.append(QualityIssue(table, "orphan_owner_id", int(bad_owner.sum()), "owner_id"))

    invalid_types = ~people["person_type"].isin(ALLOWED_PERSON_TYPES)
    if invalid_types.any():
        issues.append(QualityIssue("People", "invalid_person_type", int(invalid_types.sum()), "person_id"))

    history = working["Registration History"]
    invalid_status = ~history["status"].isin(ALLOWED_HISTORY_STATUS)
    if invalid_status.any():
        issues.append(QualityIssue("Registration History", "invalid_status", int(invalid_status.sum()), "history_id"))

    checkins = working["Check-ins"]
    invalid_result = ~checkins["result"].isin(ALLOWED_CHECKIN_RESULT)
    invalid_verification = ~checkins["verification"].isin(ALLOWED_CHECKIN_VERIFICATION)
    if invalid_result.any():
        issues.append(QualityIssue("Check-ins", "invalid_checkin_result", int(invalid_result.sum()), "event_id"))
    if invalid_verification.any():
        issues.append(QualityIssue("Check-ins", "invalid_checkin_verification", int(invalid_verification.sum()), "event_id"))

    bad_registration_fk = foreign_key_check(checkins, "registration_id", working["Registrations"], "registration_id")
    if bad_registration_fk.any():
        issues.append(QualityIssue("Check-ins", "orphan_registration_id", int(bad_registration_fk.sum()), "registration_id"))

    quality: dict[str, object] = {
        "issues": issues,
        "raw_counts": {name: int(len(frame)) for name, frame in dataset.original.items()},
        "clean_counts": {name: int(len(frame)) for name, frame in working.items()},
        "stable_id_duplicates": {
            table: int(dataset.working[table].loc[
                dataset.working[table][stable_id].notna()
            ].duplicated(subset=[stable_id]).sum())
            for table, stable_id in STABLE_IDS.items()
        },
        "missing_values": {
            table: {
                column: int(count)
                for column, count in frame.isna().sum().items()
                if count
            }
            for table, frame in dataset.original.items()
        },
    }
    return CanonicalDataset(original=dataset.original, working=working, quality=quality)
