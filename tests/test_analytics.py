from pathlib import Path

import pandas as pd
import pytest

from src.analytics.attendance import attendance_by_day, valid_external_attendance
from src.analytics.budget import campaign_spend, revised_budget
from src.analytics.funnel import latest_registration_status, conversion_rate
from src.analytics.metrics import calculate_all_kpis, calculate_historical_baseline
from src.cleaning import clean_dataset
from src.ingestion import load_workbook


WORKBOOK = Path(__file__).resolve().parents[1] / "data" / "Attendee Dataset.xlsx"


@pytest.fixture
def dataset():
    return clean_dataset(load_workbook(WORKBOOK))


def test_historical_baseline_reconciles(dataset):
    baseline = calculate_historical_baseline(dataset)
    assert baseline.identified_external_people == 3625
    assert baseline.external_registrations == 2800
    assert baseline.confirmed_external_registrations == 2500
    assert baseline.unique_external_attendees == 2050
    assert baseline.registered_attendees == 1925
    assert baseline.walk_in_attendees == 125
    assert baseline.campaign_spend == 276500
    assert baseline.revised_budget == 300000
    assert baseline.budget_remaining == 23500


def test_attendance_by_day(dataset):
    cutoff = pd.Timestamp("2025-04-13 20:00:00")
    valid, attendees = valid_external_attendance(dataset, cutoff)
    assert len(attendees) == 2050
    assert attendance_by_day(valid) == {"2025-04-12": 1430, "2025-04-13": 1345}


def test_checkin_repeated_person_counts_once(dataset):
    cutoff = pd.Timestamp("2025-04-13 20:00:00")
    valid, attendees = valid_external_attendance(dataset, cutoff)
    person = next(iter(attendees))
    assert valid.loc[valid["person_id"].eq(person), "person_id"].nunique() == 1


def test_latest_registration_status_uses_latest_date(dataset):
    cutoff = pd.Timestamp("2025-04-13 20:00:00")
    latest = latest_registration_status(dataset, cutoff)
    assert latest["registration_id"].nunique() == 2840
    assert latest["status"].value_counts()["confirmed"] == 2540


def test_campaign_metrics_match_key_real_values(dataset):
    kpis = calculate_all_kpis(dataset)
    campaigns = kpis["campaigns"].set_index("campaign_name")
    assert round(campaigns.loc["Paid Social", "cost_per_attendee"], 2) == 273.53
    assert round(campaigns.loc["College Partnerships", "cost_per_attendee"], 2) == 80.52
    assert campaigns.loc["Student Referrals", "cost_per_attendee"] == pytest.approx(70.909091, rel=1e-5)


def test_conversion_rate_edge_cases():
    assert conversion_rate(1, 4) == 0.25
    assert conversion_rate(1, 0) == 0.0


def test_revised_budget_and_spend(dataset):
    cutoff = pd.Timestamp("2025-04-13 20:00:00")
    assert revised_budget(dataset, cutoff) == 300000
    assert campaign_spend(dataset, cutoff) == 276500
    assert campaign_spend(dataset, cutoff, "C02") == 93000
