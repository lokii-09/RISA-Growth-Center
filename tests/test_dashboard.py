from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.analytics.metrics import calculate_all_kpis
from src.cleaning import clean_dataset
from src.ingestion import load_workbook


WORKBOOK = Path(__file__).resolve().parents[1] / "data" / "Attendee Dataset.xlsx"


@pytest.fixture
def kpis():
    dataset = clean_dataset(load_workbook(WORKBOOK))
    return calculate_all_kpis(dataset)


def test_dashboard_historical_kpis_from_shared_analytics(kpis):
    baseline = kpis["baseline"]
    assert baseline.identified_external_people == 3625
    assert baseline.external_registrations == 2800
    assert baseline.confirmed_external_registrations == 2500
    assert baseline.unique_external_attendees == 2050
    assert baseline.registered_attendees == 1925
    assert baseline.walk_in_attendees == 125
    assert baseline.campaign_spend == 276500
    assert baseline.revised_budget == 300000
    assert baseline.budget_remaining == 23500
    assert kpis["registered_show_rate"] == pytest.approx(0.77)
    assert kpis["blended_cost_per_attendee"] == pytest.approx(134.8780487804878)


def test_dashboard_campaign_filter_and_sort_shape(kpis):
    frame = kpis["campaigns"].copy()
    filtered = frame[frame["campaign_name"].isin(["Paid Social", "College Partnerships"])]
    assert len(filtered) == 2
    assert filtered.sort_values("cost_per_attendee").iloc[0]["campaign_name"] == "College Partnerships"


def test_dashboard_attendance_day_shape(kpis):
    assert kpis["attendance_by_day"] == {"2025-04-12": 1430, "2025-04-13": 1345}


def test_funnel_table_displays_percent_points():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=60)
    app.radio[0].set_value("Funnel Analysis").run(timeout=60)
    stages = app.dataframe[0].value
    assert stages.loc[1, "Conversion"] == pytest.approx(87.8571, rel=1e-4)
    assert stages.loc[4, "Conversion"] == pytest.approx(77.0)
    assert stages.loc[4, "Drop-off %"] == pytest.approx(23.0)
    assert not app.exception


def test_ai_growth_analyst_page_renders_without_provider(monkeypatch):
    monkeypatch.delenv("RISA_AI_API_KEY", raising=False)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=60)
    app.radio[0].set_value("AI Growth Analyst").run(timeout=60)
    assert any("AI Growth Analyst" in title.value for title in app.title)
    assert any("deterministic local analyst" in info.value for info in app.info)
    assert not app.exception

    next(button for button in app.button if button.label == "What is our biggest growth problem?").click().run(timeout=60)
    assert any("575 people" in item.value for item in app.markdown)

    app.chat_input[0].set_value("Which campaign should we prioritize?").run(timeout=60)
    assert any("Student Referrals" in item.value for item in app.markdown)

    app.chat_input[0].set_value("What if we move ₹10,000 from Paid Social to Student Referrals?").run(timeout=60)
    assert "pending_budget_proposal" not in app.session_state
    assert any("Hypothetical only" in item.value for item in app.markdown)

    app.chat_input[0].set_value("Move ₹10,000 from Paid Social to Student Referrals").run(timeout=60)
    assert app.session_state["pending_budget_proposal"]["status"] == "pending_confirmation"
    assert app.session_state["campaign_spend_overrides"] == {}
    app.chat_input[0].set_value("Looks good").run(timeout=60)
    assert app.session_state["campaign_spend_overrides"] == {}
    assert app.session_state["pending_budget_proposal"]["status"] == "pending_confirmation"
    app.chat_input[0].set_value("Now apply it").run(timeout=60)
    assert app.session_state["campaign_spend_overrides"]["C02"] == 83000
    assert "pending_budget_proposal" not in app.session_state

    app.chat_input[0].set_value("What is the current Paid Social allocation?").run(timeout=60)
    assert any("current session planning allocation is ₹83,000.00" in item.value for item in app.markdown)

    app.radio[0].set_value("Budget Management").run(timeout=60)
    next(button for button in app.button if button.label == "Reset all planning edits").click().run(timeout=60)
    assert app.session_state["campaign_spend_overrides"] == {}
    assert app.session_state["budget_override"] is None

    app.radio[0].set_value("Scenario Lab").run(timeout=60)
    assert not app.exception
    next(slider for slider in app.slider if slider.label == "Registered show-up rate").set_value(0.8).run(timeout=60)
    assert not app.exception
    assert app.session_state["scenario_assumptions"]["show_up_rate"] == pytest.approx(0.8)
    app.radio[0].set_value("AI Growth Analyst").run(timeout=60)
    app.chat_input[0].set_value("What if our show rate increases to 85%?").run(timeout=60)
    assert any("current scenario projects 1,339 total attendees" in item.value for item in app.markdown)
    assert not app.exception
