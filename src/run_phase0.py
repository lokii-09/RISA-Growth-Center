from __future__ import annotations

import argparse
from pathlib import Path

from .analytics.metrics import calculate_all_kpis
from .cleaning import clean_dataset
from .ingestion import load_workbook
from .reports import generate_baseline_report, generate_data_dictionary, generate_quality_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RISA Growth Center Phase 0")
    parser.add_argument("workbook", nargs="?", default="data/Attendee Dataset.xlsx")
    parser.add_argument("--reports", default="reports")
    parser.add_argument("--data-dictionary", default="docs/data_dictionary.md")
    args = parser.parse_args()

    dataset = clean_dataset(load_workbook(args.workbook))
    kpis = calculate_all_kpis(dataset)
    baseline = kpis["baseline"]

    reports = Path(args.reports)
    reports.mkdir(parents=True, exist_ok=True)
    generate_quality_report(dataset, reports / "data_quality.md")
    generate_baseline_report(
        baseline,
        kpis["campaigns"],
        kpis["funnel"],
        kpis["attendance_by_day"],
        reports / "historical_baseline.md",
    )
    generate_data_dictionary(dataset, Path(args.data_dictionary))
    print(f"Generated reports in {reports}")
    print(f"Unique external attendees: {baseline.unique_external_attendees}")
    print(f"External registrations: {baseline.external_registrations}")
    print(f"Confirmed external registrations: {baseline.confirmed_external_registrations}")
    print(f"Campaign spend: INR {baseline.campaign_spend:,.2f}")


if __name__ == "__main__":
    main()
