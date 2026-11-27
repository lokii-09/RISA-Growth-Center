from pathlib import Path

from src.analytics.metrics import calculate_all_kpis
from src.cleaning import clean_dataset
from src.ingestion import load_workbook
from src.reports import generate_baseline_report, generate_quality_report


WORKBOOK = Path(__file__).resolve().parents[1] / "data" / "Attendee Dataset.xlsx"


def test_quality_report_includes_missing_values_and_duplicate_decisions(tmp_path):
    dataset = clean_dataset(load_workbook(WORKBOOK))
    output = tmp_path / "quality.md"

    generate_quality_report(dataset, output)

    report = output.read_text(encoding="utf-8")
    assert "Missing values retained in the source copy" in report
    assert "| People | first_campaign_id | 145 |" in report
    assert "2 exact groups (2 extra rows)" in report
    assert "Conflicting copies are also reported" in report


def test_baseline_report_does_not_claim_hardcoded_blueprint_reconciliation(tmp_path):
    dataset = clean_dataset(load_workbook(WORKBOOK))
    kpis = calculate_all_kpis(dataset)
    output = tmp_path / "baseline.md"

    generate_baseline_report(
        kpis["baseline"],
        kpis["campaigns"],
        kpis["funnel"],
        kpis["attendance_by_day"],
        output,
    )

    report = output.read_text(encoding="utf-8")
    assert "| External registrations | 2800 |" in report
    assert "reconciles exactly to the blueprint" not in report
    assert "2,540 latest-status confirmations" not in report
