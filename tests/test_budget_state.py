import pandas as pd

from src.dashboard import state


def test_campaign_spend_edit_recalculates_cost(monkeypatch):
    monkeypatch.setattr(state.st, "session_state", {
        "campaign_spend_overrides": {"C02": 100000},
        "budget_override": 350000,
    })
    frame = pd.DataFrame([
        {
            "campaign_id": "C02",
            "campaign_name": "Paid Social",
            "spend": 93000,
            "attributed_attendees": 340,
            "cost_per_attendee": 273.529411,
        }
    ])
    result = state.apply_campaign_spend_edits(frame)
    assert result.loc[0, "spend"] == 100000
    assert result.loc[0, "cost_per_attendee"] == 100000 / 340
    assert state.effective_budget(300000) == 350000


def test_reset_budget_state_clears_edits(monkeypatch):
    monkeypatch.setattr(state.st, "session_state", {
        "campaign_spend_overrides": {"C02": 100000},
        "budget_override": 350000,
    })
    state.reset_budget_state()
    assert state.campaign_spend_overrides() == {}
    assert state.effective_budget(300000) == 300000


def test_negative_campaign_spend_is_rejected(monkeypatch):
    monkeypatch.setattr(state.st, "session_state", {
        "campaign_spend_overrides": {},
        "budget_override": None,
    })
    try:
        state.set_campaign_spend("C02", -1)
    except ValueError as exc:
        assert "cannot be negative" in str(exc)
    else:
        raise AssertionError("Negative spend was accepted")
