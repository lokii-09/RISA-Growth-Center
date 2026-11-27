from pathlib import Path

import pandas as pd

from src.cleaning import clean_dataset
from src.ingestion import load_workbook


WORKBOOK = Path(__file__).resolve().parents[1] / "data" / "Attendee Dataset.xlsx"


def test_real_duplicate_stable_ids_are_removed_in_working_copy_only():
    dataset = load_workbook(WORKBOOK)
    cleaned = clean_dataset(dataset)
    assert len(dataset.original["Check-ins"]) == 3390
    assert len(cleaned.original["Check-ins"]) == 3390
    assert len(cleaned.working["Check-ins"]) == 3370
    assert len(cleaned.working["Registration History"]) == 5907
    assert len(cleaned.working["Daily Marketing"]) == 481


def test_external_filter_excludes_non_external_people():
    dataset = load_workbook(WORKBOOK)
    cleaned = clean_dataset(dataset)
    people = cleaned.working["People"]
    counts = people["person_type"].value_counts().to_dict()
    assert counts["external"] == 3625
    assert counts["internal"] == 40
    assert counts["staff"] == 10
    assert counts["test"] == 10


def test_missing_ids_are_preserved_and_duplicate_conflicts_are_classified():
    dataset = load_workbook(WORKBOOK)
    original_count = len(dataset.original["Daily Marketing"])
    frame = dataset.working["Daily Marketing"].copy(deep=True)
    duplicate_id = frame.loc[frame.duplicated("activity_id", keep=False), "activity_id"].iloc[0]
    duplicate_indices = frame.index[frame["activity_id"].eq(duplicate_id)].tolist()
    frame.loc[duplicate_indices[-1], "impressions"] += 1
    missing_id_rows = frame.iloc[[0]].copy()
    missing_id_rows["activity_id"] = None
    frame = pd.concat([frame, missing_id_rows, missing_id_rows], ignore_index=True)
    dataset.working["Daily Marketing"] = frame

    cleaned = clean_dataset(dataset)
    cleaned_frame = cleaned.working["Daily Marketing"]
    issues = cleaned.quality["issues"]
    duplicate_issue = next(
        issue for issue in issues
        if issue.table == "Daily Marketing" and issue.issue_type == "duplicate_stable_id_rows"
    )
    missing_issue = next(
        issue for issue in issues
        if issue.table == "Daily Marketing" and issue.issue_type == "missing_stable_id"
    )

    assert cleaned_frame["activity_id"].isna().sum() == 2
    assert len(frame) - len(cleaned_frame) == cleaned.quality["stable_id_duplicates"]["Daily Marketing"]
    assert "conflicting groups" in duplicate_issue.details
    assert missing_issue.count == 2
    assert len(cleaned.original["Daily Marketing"]) == original_count
