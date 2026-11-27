from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .models import CanonicalDataset, HistoricalBaseline


def generate_data_dictionary(dataset: CanonicalDataset, output: Path) -> None:
    guide = dataset.original.get("Field guide")
    if guide is None:
        raise ValueError("The workbook's 'Field guide' worksheet is required for the data dictionary.")

    lines = [
        "# RISA Growth Center Data Dictionary",
        "",
        "Generated from the workbook Field guide and actual worksheet inspection.",
        "",
        "| Source table | Field | Data type | Meaning |",
        "|---|---|---|---|",
    ]
    for row in guide.itertuples(index=False):
        meaning = str(row.meaning).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {row.source_table} | {row.field} | {row.data_type} | {meaning} |")
    output.write_text("\n".join(lines), encoding="utf-8")


def generate_quality_report(dataset: CanonicalDataset, output: Path) -> None:
    quality = dataset.quality
    issues = quality.get("issues", [])
    lines = [
        "# Phase 0 Data Quality Report",
        "",
        "## Raw and cleaned record counts",
        "",
        "| Table | Raw records | Clean records |",
        "|---|---:|---:|",
    ]
    raw = quality["raw_counts"]
    clean = quality["clean_counts"]
    for table in raw:
        lines.append(f"| {table} | {raw[table]} | {clean[table]} |")

    lines.extend(["", "## Missing values retained in the source copy", ""])
    missing_values = quality.get("missing_values", {})
    missing_rows = [
        (table, column, count)
        for table, columns in missing_values.items()
        for column, count in columns.items()
    ]
    if not missing_rows:
        lines.append("No missing values found.")
    else:
        lines.extend(["| Table | Field | Missing values |", "|---|---|---:|"])
        for table, column, count in missing_rows:
            lines.append(f"| {table} | {column} | {count} |")
        lines.append("")
        lines.append("Missing values are reported rather than silently removed; whether a blank is valid depends on the field.")

    lines.extend(["", "## Cleaning decisions and issues", ""])
    if not issues:
        lines.append("No issues found.")
    else:
        lines.extend(["| Table | Issue | Count | Stable ID | Details |", "|---|---|---:|---|---|"])
        for issue in issues:
            lines.append(
                f"| {issue.table} | {issue.issue_type} | {issue.count} | "
                f"{issue.stable_id or ''} | {issue.details} |"
            )

    lines.extend([
        "",
        "## Stable duplicate handling",
        "",
        "Exact rows with duplicate stable IDs are deduplicated with `keep='first'` in the working copy.",
        "Conflicting copies are also reported and retain the first source row deterministically; they are not merged.",
        "Rows with missing stable IDs are preserved and reported. The original DataFrames remain unchanged.",
        "Nonblank source values that fail date or numeric conversion are reported as issues and represented as missing in the typed working copy.",
        "",
    ])
    output.write_text("\n".join(lines), encoding="utf-8")


def generate_baseline_report(baseline: HistoricalBaseline, campaigns: pd.DataFrame, funnel: dict[str, int],
                             attendance_by_day: dict[str, int], output: Path) -> None:
    lines = [
        "# Historical Baseline Report",
        "",
        f"As-of cutoff: `{baseline.as_of.isoformat()}` (Asia/Kolkata event close)",
        "",
        "## Core KPIs",
        "",
        "| KPI | Value |",
        "|---|---:|",
        f"| Identified external people | {baseline.identified_external_people} |",
        f"| External registrations | {baseline.external_registrations} |",
        f"| Confirmed external registrations | {baseline.confirmed_external_registrations} |",
        f"| Unique verified external attendees | {baseline.unique_external_attendees} |",
        f"| Registered external attendees | {baseline.registered_attendees} |",
        f"| Walk-in external attendees | {baseline.walk_in_attendees} |",
        f"| Campaign spend | ₹{baseline.campaign_spend:,.2f} |",
        f"| Revised marketing budget | ₹{baseline.revised_budget:,.2f} |",
        f"| Budget remaining | ₹{baseline.budget_remaining:,.2f} |",
        f"| Registered show rate | {baseline.registered_attendees / baseline.confirmed_external_registrations:.3%} |",
        f"| Blended cost per attendee | ₹{baseline.campaign_spend / baseline.unique_external_attendees:,.2f} |",
        "",
        "## Attendance by day",
        "",
        "| Day | Unique external attendees |",
        "|---|---:|",
    ]
    for day, count in sorted(attendance_by_day.items()):
        lines.append(f"| {day} | {count} |")

    lines.extend(["", "## Identified funnel", "", "| Stage | Unique people |", "|---|---:|"])
    stage_names = [
        ("identified_page_visitors", "Identified page visitors"),
        ("registration_starters", "Registration starters"),
        ("external_registrations", "Completed external registrations"),
        ("confirmed_external_registrations", "Confirmed external registrations"),
        ("registered_attendees", "Registered external attendees"),
    ]
    for key, name in stage_names:
        lines.append(f"| {name} | {funnel[key]} |")

    lines.extend(["", "## Campaign performance", ""])
    lines.append("| Campaign | Spend | Identified people | External registrations | Confirmed | Attendees | Confirmed→attended | Cost/attendee |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in campaigns.itertuples(index=False):
        cta = f"{row.confirmed_to_attended:.1%}" if row.confirmed_to_attended is not None else "—"
        cpa = f"₹{row.cost_per_attendee:,.2f}" if row.cost_per_attendee is not None else "—"
        lines.append(
            f"| {row.campaign_name} | ₹{row.spend:,.2f} | {row.identified_people} | "
            f"{row.external_registrations} | {row.confirmed_external_registrations} | "
            f"{row.attributed_attendees} | {cta} | {cpa} |"
        )

    lines.extend([
        "",
        "## Discrepancy explanation",
        "",
        "Metrics are calculated from the supplied workbook using the definitions in the application, not from embedded checkpoint values.",
        "Person-level external metrics apply the workbook's external-person filter; status counts can differ when a source-level count includes other person types.",
        "Review the KPI definitions and data quality findings when comparing with independently reported totals.",
        "",
    ])
    output.write_text("\n".join(lines), encoding="utf-8")
