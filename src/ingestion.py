from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .models import CanonicalDataset, QualityIssue


REQUIRED_SHEETS: dict[str, tuple[str, ...]] = {
    "Event": ("event_name", "history_start", "history_end", "event_starts_at", "event_ends_at", "timezone", "currency", "fictional"),
    "Targets": ("effective_at", "identified_external_people_goal", "registration_goal", "unique_external_visitors_goal", "marketing_budget_inr", "target_version"),
    "Campaigns": ("campaign_name", "channel", "target_audience", "objective", "owner_name", "created_at", "planned_start_at", "planned_end_at", "campaign_id", "owner_id"),
    "Daily Marketing": ("campaign_name", "owner_name", "activity_date", "impressions", "clicks", "reported_reach", "landing_page_sessions", "registration_starts", "marketing_spend_inr", "platform", "activity_id", "campaign_id", "owner_id"),
    "People": ("person_name", "person_type", "first_seen_at", "first_touch_source", "first_campaign_name", "owner_name", "person_id", "first_campaign_id", "owner_id"),
    "Interest and Engagement": ("person_name", "campaign_name", "owner_name", "occurred_at", "event_type", "detail", "interaction_id", "person_id", "campaign_id", "owner_id"),
    "Registrations": ("person_name", "campaign_name", "owner_name", "registered_at", "registration_id", "person_id", "campaign_id", "owner_id"),
    "Registration History": ("person_name", "campaign_name", "owner_name", "effective_at", "status", "history_id", "registration_id", "person_id", "campaign_id", "owner_id"),
    "Check-ins": ("person_name", "campaign_name", "owner_name", "occurred_at", "result", "verification", "source", "event_id", "person_id", "registration_id", "campaign_id", "owner_id"),
}

DATE_COLUMNS = {
    "history_start", "history_end", "event_starts_at", "event_ends_at", "effective_at",
    "created_at", "planned_start_at", "planned_end_at", "activity_date", "first_seen_at",
    "occurred_at", "registered_at",
}
NUMERIC_COLUMNS = {
    "impressions", "clicks", "reported_reach", "landing_page_sessions", "registration_starts",
    "marketing_spend_inr", "identified_external_people_goal", "registration_goal",
    "unique_external_visitors_goal", "marketing_budget_inr",
}


def load_workbook(path: str | Path) -> CanonicalDataset:
    workbook = Path(path)
    if not workbook.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook}")

    issues: list[QualityIssue] = []
    with pd.ExcelFile(workbook) as excel:
        missing_sheets = [name for name in REQUIRED_SHEETS if name not in excel.sheet_names]
        if missing_sheets:
            raise ValueError(f"Missing required worksheets: {', '.join(missing_sheets)}")

        originals: dict[str, pd.DataFrame] = {}
        typed_tables: dict[str, pd.DataFrame] = {}
        for sheet, required in REQUIRED_SHEETS.items():
            source_frame = excel.parse(sheet_name=sheet)
            frame = source_frame.copy(deep=True)
            missing_columns = [column for column in required if column not in frame.columns]
            if missing_columns:
                raise ValueError(
                    f"Worksheet '{sheet}' is missing required columns: {', '.join(missing_columns)}"
                )
            for column in frame.columns:
                if column in DATE_COLUMNS:
                    source = frame[column]
                    converted = pd.to_datetime(source, errors="coerce")
                    populated = source.notna()
                    if pd.api.types.is_object_dtype(source) or pd.api.types.is_string_dtype(source):
                        populated &= source.astype("string").str.strip().ne("")
                    invalid_count = int((populated & converted.isna()).sum())
                    if invalid_count:
                        issues.append(QualityIssue(
                            sheet,
                            "invalid_datetime",
                            invalid_count,
                            column,
                            "Nonblank source values failed datetime conversion and were retained as missing.",
                        ))
                    frame[column] = converted
                elif column in NUMERIC_COLUMNS:
                    source = frame[column]
                    converted = pd.to_numeric(source, errors="coerce")
                    populated = source.notna()
                    if pd.api.types.is_object_dtype(source) or pd.api.types.is_string_dtype(source):
                        populated &= source.astype("string").str.strip().ne("")
                    invalid_count = int((populated & converted.isna()).sum())
                    if invalid_count:
                        issues.append(QualityIssue(
                            sheet,
                            "invalid_numeric",
                            invalid_count,
                            column,
                            "Nonblank source values failed numeric conversion and were retained as missing.",
                        ))
                    frame[column] = converted
            originals[sheet] = source_frame.copy(deep=True)
            typed_tables[sheet] = frame.copy(deep=True)

        optional = ["Read me", "Field guide"]
        for sheet in optional:
            if sheet in excel.sheet_names:
                source_frame = excel.parse(sheet_name=sheet)
                originals[sheet] = source_frame.copy(deep=True)
                typed_tables[sheet] = source_frame.copy(deep=True)

    return CanonicalDataset(
        original=originals,
        working=typed_tables,
        quality={"issues": issues},
    )
