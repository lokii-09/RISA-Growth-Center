from pathlib import Path

import pandas as pd
import pytest

from src.ingestion import REQUIRED_SHEETS, load_workbook


WORKBOOK = Path(__file__).resolve().parents[1] / "data" / "Attendee Dataset.xlsx"


def test_real_workbook_ingestion():
    dataset = load_workbook(WORKBOOK)
    assert set(REQUIRED_SHEETS).issubset(dataset.original)
    assert len(dataset.original["People"]) == 3685
    assert len(dataset.original["Registrations"]) == 2840
    assert len(dataset.original["Check-ins"]) == 3390


def test_missing_sheet_raises(tmp_path):
    path = tmp_path / "missing.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({"a": [1]}).to_excel(writer, sheet_name="Wrong", index=False)
    with pytest.raises(ValueError, match="Missing required worksheets"):
        load_workbook(path)


def test_missing_required_column_raises(tmp_path):
    path = tmp_path / "bad.xlsx"
    with pd.ExcelWriter(path) as writer:
        for sheet, columns in REQUIRED_SHEETS.items():
            pd.DataFrame({columns[0]: [1]}).to_excel(writer, sheet_name=sheet, index=False)
    with pytest.raises(ValueError, match="missing required columns"):
        load_workbook(path)


def test_invalid_dates_and_numbers_are_reported_and_coerced(tmp_path):
    path = tmp_path / "invalid-values.xlsx"
    with pd.ExcelWriter(path) as writer:
        for sheet, columns in REQUIRED_SHEETS.items():
            data = {column: [1] for column in columns}
            if sheet == "Daily Marketing":
                data["activity_date"] = ["not a date"]
                data["impressions"] = ["not a number"]
            pd.DataFrame(data).to_excel(writer, sheet_name=sheet, index=False)
        pd.DataFrame({
            "topic": ["test"],
            "description": ["test"],
        }).to_excel(writer, sheet_name="Read me", index=False)
    dataset = load_workbook(path)
    source_daily = dataset.original["Daily Marketing"]
    daily = dataset.working["Daily Marketing"]
    assert pd.api.types.is_numeric_dtype(daily["impressions"])
    assert pd.isna(daily.loc[0, "impressions"])
    assert pd.isna(daily.loc[0, "activity_date"])
    assert source_daily.loc[0, "impressions"] == "not a number"
    assert source_daily.loc[0, "activity_date"] == "not a date"
    issue_types = {issue.issue_type for issue in dataset.quality["issues"]}
    assert issue_types == {"invalid_datetime", "invalid_numeric"}
