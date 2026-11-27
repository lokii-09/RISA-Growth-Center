import pytest

from src.dashboard.scenario import ScenarioInputs, calculate_scenario


def test_historical_scenario_defaults_reproduce_baseline():
    result = calculate_scenario(ScenarioInputs(
        visitor_target=3625,
        registration_conversion=2800 / 3625,
        confirmation_rate=2500 / 2800,
        show_up_rate=1925 / 2500,
        walk_ins=125,
        marketing_budget=300000,
    ))
    assert result.projected_registrations == 2800
    assert result.projected_confirmed == 2500
    assert result.projected_registered_attendees == 1925
    assert result.projected_total_attendees == 2050
    assert result.projected_cost_per_attendee == pytest.approx(300000 / 2050)


def test_scenario_recalculates_modified_assumptions():
    result = calculate_scenario(ScenarioInputs(
        visitor_target=4000,
        registration_conversion=0.8,
        confirmation_rate=0.9,
        show_up_rate=0.8,
        walk_ins=150,
        marketing_budget=300000,
    ))
    assert result.projected_registrations == 3200
    assert result.projected_confirmed == 2880
    assert result.projected_registered_attendees == 2304
    assert result.projected_total_attendees == 2454


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("registration_conversion", -0.1, "Registration conversion"),
        ("confirmation_rate", 1.1, "Confirmation rate"),
        ("show_up_rate", -0.1, "Show-up rate"),
        ("visitor_target", -1, "Visitor target"),
        ("walk_ins", -1, "Walk-ins"),
        ("marketing_budget", -1, "Marketing budget"),
    ],
)
def test_scenario_rejects_invalid_inputs(field, value, message):
    values = {
        "visitor_target": 100,
        "registration_conversion": 0.5,
        "confirmation_rate": 0.5,
        "show_up_rate": 0.5,
        "walk_ins": 10,
        "marketing_budget": 1000,
    }
    values[field] = value
    with pytest.raises(ValueError, match=message):
        calculate_scenario(ScenarioInputs(**values))
