import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.analytics.metrics import calculate_all_kpis
from src.assistant.engine import answer_question, configured_provider, resolve_followup
from src.assistant.proposals import (
    apply_confirmed_proposal,
    is_explicit_proposal_confirmation,
)
from src.assistant.provider import AIProviderError, OpenAICompatibleProvider, ProviderSettings
from src.assistant.tools import (
    build_context,
    draft_budget_reallocation,
    execute_tool,
    get_budget_status,
    get_campaign_performance,
    get_funnel,
    get_overview,
    get_data_coverage,
    project_scenario,
)
from src.cleaning import clean_dataset
from src.dashboard import state
from src.ingestion import load_workbook
from question_bank import QUESTION_BANK


WORKBOOK = Path(__file__).resolve().parents[1] / "data" / "Attendee Dataset.xlsx"


@pytest.fixture(scope="module")
def context():
    dataset = clean_dataset(load_workbook(WORKBOOK))
    return build_context(dataset, calculate_all_kpis(dataset), {})


def test_question_bank_has_at_least_30_questions_across_categories():
    assert len(QUESTION_BANK) >= 10
    assert sum(map(len, QUESTION_BANK.values())) >= 30
    assert all(QUESTION_BANK.values())


def test_all_question_bank_prompts_have_safe_local_responses(context):
    approved_tools = {
        "get_overview",
        "get_funnel",
        "get_campaign_performance",
        "get_budget_status",
        "project_scenario",
        "get_data_coverage",
        "draft_budget_reallocation",
    }
    for prompts in QUESTION_BANK.values():
        for prompt in prompts:
            response = answer_question(prompt, context)
            assert response.text.strip(), prompt
            assert set(response.tools_used).issubset(approved_tools), prompt
            assert response.pending_proposal is None or response.pending_proposal["applied"] is False


def test_overview_tool_uses_authoritative_historical_kpis(context):
    result = get_overview(context)
    assert result["identified_external_people"] == 3625
    assert result["external_registrations"] == 2800
    assert result["confirmed_external_registrations"] == 2500
    assert result["registered_attendees"] == 1925
    assert result["walk_in_attendees"] == 125
    assert result["unique_external_attendees"] == 2050
    assert result["historical_campaign_spend"] == 276500
    assert result["historical_budget_remaining"] == 23500
    assert result["attendance_by_day"] == {
        "2025-04-12": 1430,
        "2025-04-13": 1345,
    }


def test_funnel_and_campaign_tools_use_canonical_analytics(context):
    funnel = get_funnel(context)
    assert funnel["largest_bottleneck"]["dropoff_from_previous"] == 575

    campaigns = get_campaign_performance(context, ["College Partnerships", "Paid Social"])["campaigns"]
    assert {item["campaign_name"] for item in campaigns} == {"College Partnerships", "Paid Social"}
    paid = next(item for item in campaigns if item["campaign_name"] == "Paid Social")
    assert paid["attendees"] == 340
    assert paid["historical_cost_per_attendee"] == pytest.approx(273.5294, rel=1e-4)


def test_budget_coverage_tools_separate_actuals_and_planning(context):
    budget = get_budget_status(context)
    assert budget["historical_actual"]["spend"] == 276500
    assert budget["current_planning_state"]["remaining"] == 23500
    coverage = get_data_coverage(context)
    assert "attendee_satisfaction_or_nps" in coverage["unsupported"]
    assert "Attendance" not in coverage["available_tables"]


def test_tool_argument_validation_and_unknown_tool(context):
    with pytest.raises(ValidationError):
        execute_tool("project_scenario", {"show_up_rate": 1.1}, context)
    with pytest.raises(ValueError, match="not approved"):
        execute_tool("run_python", {}, context)


def test_scenario_tool_projects_show_rate_without_mutating_actuals(context):
    before = get_overview(context)["unique_external_attendees"]
    result = project_scenario(context, {"show_up_rate": 0.85})
    assert result["classification"] == "hypothetical scenario, not actual results"
    assert result["base_projection"]["projected_total_attendees"] == 2050
    assert result["proposed_projection"]["projected_total_attendees"] == 2250
    assert result["attendee_difference"] == 200
    assert get_overview(context)["unique_external_attendees"] == before


def test_local_analyst_answers_overview_funnel_campaign_scenario_and_unsupported(context):
    overview = answer_question("How many attendees came?", context)
    assert "2,050 unique verified external attendees" in overview.text
    assert "125 walk-ins" in overview.text
    attendance_by_day = answer_question("How many attendees came each day?", context)
    assert "2025-04-12: 1,430" in attendance_by_day.text
    assert "should not be summed" in attendance_by_day.text

    funnel = answer_question("What is our biggest growth problem?", context)
    assert "575 people" in funnel.text
    assert "get_funnel" in funnel.tools_used

    traffic = answer_question(
        "Are we losing people in high traffic but low registration conversion?",
        context,
    )
    assert "80.0%" in traffic.text
    assert "700 fewer" in traffic.text
    assert "no benchmark" in traffic.text
    confirmation = answer_question("How many registrations failed to confirm?", context)
    assert "2,500 of 2,800" in confirmation.text
    assert "300" in confirmation.text

    campaign = answer_question("Why is Paid Social performing poorly?", context)
    assert "College Partnerships" in campaign.text
    assert "does not show why" in campaign.text

    comparison = answer_question(
        "Compare College Partnerships with Paid Social.",
        context,
    )
    assert "College Partnerships: 385 attendees" in comparison.text
    assert "Paid Social: 340 attendees" in comparison.text
    assert "registration conversion" in comparison.text

    scenario = answer_question("What if our show rate increases to 85%?", context)
    assert "Hypothetical only" in scenario.text
    assert "2,250" in scenario.text

    conversion_scenario = answer_question(
        "What if registration conversion improves by 5 percentage points?",
        context,
    )
    assert "2,050" in conversion_scenario.text
    assert "2,170" in conversion_scenario.text

    transfer_scenario = answer_question(
        "What happens if I move ₹10,000 from Paid Social to Student Referrals?",
        context,
    )
    assert transfer_scenario.pending_proposal is None
    assert "Hypothetical only" in transfer_scenario.text

    referral_scenario = answer_question(
        "What if we spend another ₹20,000 on referrals?",
        context,
    )
    assert "₹320,000.00" in referral_scenario.text
    assert "historical average CPA" in referral_scenario.text
    assert "exceeds its current planning budget by ₹20,000.00" in referral_scenario.text
    assert "no budget values have been changed" in referral_scenario.text

    unsupported = answer_question("What was attendee satisfaction?", context)
    assert "No survey/NPS table or field" in unsupported.text
    assert unsupported.tools_used == ["get_data_coverage"]
    causal_roi = answer_question("What was the exact causal ROI of each campaign?", context)
    assert "no randomized experiment" in causal_roi.text
    assert causal_roi.tools_used == ["get_data_coverage"]

    working_well = answer_question("What is working well?", context)
    assert "Student Referrals" in working_well.text
    assert "not causal proof" in working_well.text
    allocation = answer_question("How should we allocate remaining budget?", context)
    assert "₹23,500.00" in allocation.text
    assert "No allocation has been changed" in allocation.text

    ambiguous_transfer = answer_question("Transfer ₹10,000 to Student Referrals.", context)
    assert "Which source campaign" in ambiguous_transfer.text
    assert ambiguous_transfer.pending_proposal is None
    code_request = answer_question("Can you execute Python code on the dataset?", context)
    assert "can’t execute arbitrary code" in code_request.text
    assert code_request.tools_used == []


def test_budget_proposal_is_draft_only_until_explicit_application(context, monkeypatch):
    fake_state = {"campaign_spend_overrides": {}, "budget_override": None}
    monkeypatch.setattr(state.st, "session_state", fake_state)
    live_context = build_context(context.dataset, context.kpis, fake_state)

    reply = answer_question("Move ₹10,000 from Paid Social to Student Referrals", live_context)
    proposal = reply.pending_proposal
    assert proposal is not None
    assert proposal["status"] == "pending_confirmation"
    assert proposal["applied"] is False
    assert fake_state["campaign_spend_overrides"] == {}
    referral_before = next(
        item["planning_spend"]
        for item in get_campaign_performance(live_context)["campaigns"]
        if item["campaign_name"] == "Student Referrals"
    )

    confirmation_text = answer_question("Now apply it", live_context, pending_proposal=proposal)
    assert "No changes have been applied" in confirmation_text.text
    assert fake_state["campaign_spend_overrides"] == {}

    apply_confirmed_proposal(live_context, proposal)
    updated = build_context(context.dataset, context.kpis, fake_state)
    campaigns = {item["campaign_name"]: item for item in get_campaign_performance(updated)["campaigns"]}
    assert campaigns["Paid Social"]["planning_spend"] == 83000
    assert campaigns["Student Referrals"]["planning_spend"] == referral_before + 10000
    assert campaigns["Paid Social"]["historical_spend"] == 93000


def test_confirmation_requires_clear_intent_for_the_pending_proposal():
    pending = {"status": "pending_confirmation"}
    assert is_explicit_proposal_confirmation("Now apply it.", pending)
    assert is_explicit_proposal_confirmation("Confirm this transfer", pending)
    assert not is_explicit_proposal_confirmation("Looks good", pending)
    assert not is_explicit_proposal_confirmation("Now apply it", None)


def test_proposal_validation_and_stale_state_do_not_apply(context, monkeypatch):
    fake_state = {"campaign_spend_overrides": {}, "budget_override": None}
    monkeypatch.setattr(state.st, "session_state", fake_state)
    live_context = build_context(context.dataset, context.kpis, fake_state)

    with pytest.raises(ValueError, match="exceeds source"):
        draft_budget_reallocation(live_context, {
            "source_campaign": "Paid Social",
            "destination_campaign": "Student Referrals",
            "amount": 100000,
        })

    proposal = draft_budget_reallocation(live_context, {
        "source_campaign": "Paid Social",
        "destination_campaign": "Student Referrals",
        "amount": 10000,
    })
    state.set_campaign_spend("C02", 80000)
    changed_context = build_context(context.dataset, context.kpis, fake_state)
    with pytest.raises(ValueError, match="changed after"):
        apply_confirmed_proposal(changed_context, proposal)
    assert fake_state["campaign_spend_overrides"] == {"C02": 80000}


def test_proposal_respects_current_budget_limit(context):
    over_budget = build_context(
        context.dataset,
        context.kpis,
        {
            "campaign_spend_overrides": {"C02": 120000},
            "budget_override": 300000,
        },
    )
    with pytest.raises(ValueError, match="already exceeds"):
        draft_budget_reallocation(over_budget, {
            "source_campaign": "Paid Social",
            "destination_campaign": "Student Referrals",
            "amount": 10000,
        })


def test_followup_resolution_uses_recent_campaign_context(context):
    history = [
        {"role": "user", "content": "Which campaigns should we scale?"},
        {"role": "assistant", "content": "Pilot Student Referrals and Organic Search."},
    ]
    assert "Organic Search" in resolve_followup("What about the second one?", history, context)
    assert "Student Referrals with Organic Search" in resolve_followup("Compare those.", history, context)
    second = answer_question("What about the second one?", context, history)
    assert "Organic Search" in second.text
    comparison = answer_question("Compare those.", context, history)
    assert "Student Referrals:" in comparison.text
    assert "Organic Search:" in comparison.text
    why_history = [
        {"role": "user", "content": "Which campaigns should we scale?"},
        {"role": "assistant", "content": "Pilot Student Referrals and Organic Search."},
    ]
    why = answer_question("Why?", context, why_history)
    assert "historical association, not guaranteed incremental lift" in why.text


def test_local_fallback_and_provider_configuration_are_safe(context, monkeypatch):
    monkeypatch.delenv("RISA_AI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    provider, notice = configured_provider()
    assert provider is None
    assert "deterministic local analyst" in notice
    assert answer_question("How much budget is left?", context).tools_used == ["get_budget_status"]
    unknown = answer_question("Can you analyze the FIFA finals?", context)
    assert "don’t have enough context" in unknown.text
    assert unknown.tools_used == ["get_data_coverage"]


def test_provider_settings_support_streamlit_secrets(monkeypatch):
    from src.assistant import provider as provider_module

    for key in ("GROQ_API_KEY", "RISA_AI_API_KEY", "RISA_AI_BASE_URL", "RISA_AI_MODEL", "RISA_AI_TIMEOUT_SECONDS"):
        monkeypatch.delenv(key, raising=False)
    configured = {
        "GROQ_API_KEY": "secret-from-streamlit",
        "RISA_AI_BASE_URL": "https://llm.example/v1",
        "RISA_AI_MODEL": "compatible-model",
        "RISA_AI_TIMEOUT_SECONDS": "18",
    }
    monkeypatch.setattr(
        provider_module,
        "_read_streamlit_secret",
        lambda name, default="": configured.get(name, default),
    )
    settings = ProviderSettings.from_environment()
    assert settings is not None
    assert settings.api_key == "secret-from-streamlit"
    assert settings.endpoint == "https://llm.example/v1/chat/completions"
    assert settings.model == "compatible-model"
    assert settings.timeout_seconds == 18


def test_provider_settings_accept_legacy_risa_api_key_secret(monkeypatch):
    from src.assistant import provider as provider_module

    for key in ("GROQ_API_KEY", "RISA_AI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(
        provider_module,
        "_read_streamlit_secret",
        lambda name, default="": {
            "RISA_AI_API_KEY": "legacy-streamlit-key",
        }.get(name, default),
    )

    settings = ProviderSettings.from_environment()

    assert settings is not None
    assert settings.api_key == "legacy-streamlit-key"


def test_provider_defaults_to_groq_gpt_oss(monkeypatch):
    from src.assistant import provider as provider_module

    monkeypatch.setenv("GROQ_API_KEY", "groq-test-key")
    monkeypatch.delenv("RISA_AI_API_KEY", raising=False)
    for key in ("RISA_AI_BASE_URL", "RISA_AI_MODEL", "RISA_AI_TIMEOUT_SECONDS"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(
        provider_module,
        "_read_streamlit_secret",
        lambda _name, default="": default,
    )

    settings = ProviderSettings.from_environment()

    assert settings is not None
    assert settings.endpoint == "https://api.groq.com/openai/v1/chat/completions"
    assert settings.model == "openai/gpt-oss-120b"


def test_provider_environment_values_take_precedence_over_streamlit_secrets(monkeypatch):
    from src.assistant import provider as provider_module

    environment = {
        "GROQ_API_KEY": "environment-key",
        "RISA_AI_API_KEY": "legacy-environment-key",
        "RISA_AI_BASE_URL": "https://env.example/v1",
        "RISA_AI_MODEL": "environment-model",
        "RISA_AI_TIMEOUT_SECONDS": "30",
    }
    for name, value in environment.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(
        provider_module,
        "_read_streamlit_secret",
        lambda name, default="": "streamlit-secret",
    )
    settings = ProviderSettings.from_environment()
    assert settings is not None
    assert settings.api_key == "environment-key"
    assert settings.endpoint == "https://env.example/v1/chat/completions"
    assert settings.model == "environment-model"
    assert settings.timeout_seconds == 30


def test_provider_handles_malformed_response_without_leaking_secret(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"not-json"

    monkeypatch.setattr("src.assistant.provider.urlopen", lambda *_args, **_kwargs: Response())
    provider = OpenAICompatibleProvider(ProviderSettings(
        api_key="test-secret",
        model="test-model",
        endpoint="https://example.test/v1/chat/completions",
    ))
    with pytest.raises(AIProviderError) as error:
        provider.complete([], [])
    assert "malformed response" in str(error.value)
    assert "test-secret" not in str(error.value)


def test_provider_falls_back_when_answer_omits_required_tool(context):
    class NoToolProvider:
        def complete(self, _messages, _tools):
            return {"choices": [{"message": {"content": "There were 999 attendees."}}]}

    reply = answer_question("How many attendees came?", context, provider=NoToolProvider())
    assert reply.mode == "local"
    assert "2,050" in reply.text
    assert "999" not in reply.text


def test_provider_receives_approved_tool_results_before_answering(context):
    class ToolCallingProvider:
        def __init__(self):
            self.called = False

        def complete(self, messages, _tools):
            if not self.called:
                self.called = True
                return {"choices": [{"message": {
                    "tool_calls": [{
                        "id": "call-overview",
                        "type": "function",
                        "function": {"name": "get_overview", "arguments": "{}"},
                    }],
                }}]}
            tool_result = json.loads(messages[-1]["content"])
            assert tool_result["unique_external_attendees"] == 2050
            return {"choices": [{"message": {
                "content": "The verified external attendee count is 2,050."
            }}]}

    reply = answer_question(
        "How many attendees came?",
        context,
        provider=ToolCallingProvider(),
    )
    assert reply.mode == "provider"
    assert reply.tools_used == ["get_overview"]
    assert "2,050" in reply.text


def test_provider_numeric_claims_must_match_approved_tool_results(context):
    class HallucinatingProvider:
        def __init__(self):
            self.called = False

        def complete(self, _messages, _tools):
            if not self.called:
                self.called = True
                return {"choices": [{"message": {
                    "tool_calls": [{
                        "id": "call-overview",
                        "type": "function",
                        "function": {"name": "get_overview", "arguments": "{}"},
                    }],
                }}]}
            return {"choices": [{"message": {"content": "There were 999 attendees."}}]}

    reply = answer_question(
        "How many attendees came?",
        context,
        provider=HallucinatingProvider(),
    )
    assert reply.mode == "local"
    assert "2,050" in reply.text
    assert "999" not in reply.text


def test_provider_failure_falls_back_without_exposing_provider_details(context):
    class FailingProvider:
        def complete(self, _messages, _tools):
            raise AIProviderError("AI provider could not be reached. Check the connection and try again.")

    reply = answer_question("How many attendees came?", context, provider=FailingProvider())
    assert reply.mode == "local_fallback"
    assert reply.provider_error is not None
    assert "2,050" in reply.text


def test_reset_request_restores_planning_baseline_only(context, monkeypatch):
    fake_state = {
        "campaign_spend_overrides": {"C02": 80000},
        "budget_override": 350000,
    }
    monkeypatch.setattr(state.st, "session_state", fake_state)
    live_context = build_context(context.dataset, context.kpis, fake_state)
    reply = answer_question("Reset the proposed edits", live_context)
    assert "reset to the workbook-based values" in reply.text
    assert fake_state["campaign_spend_overrides"] == {}
    assert fake_state["budget_override"] is None


def test_budget_proposal_can_be_revised_without_application(context, monkeypatch):
    fake_state = {"campaign_spend_overrides": {}, "budget_override": None}
    monkeypatch.setattr(state.st, "session_state", fake_state)
    live_context = build_context(context.dataset, context.kpis, fake_state)
    initial = answer_question("Move ₹10,000 from Paid Social to Student Referrals", live_context)
    revised = answer_question(
        "What if I change that to ₹20,000?",
        live_context,
        pending_proposal=initial.pending_proposal,
    )
    assert revised.pending_proposal["amount"] == 20000
    assert revised.pending_proposal["source_campaign"] == "Paid Social"
    assert fake_state["campaign_spend_overrides"] == {}


def test_cancel_and_bypass_confirmation_never_apply_edits(context, monkeypatch):
    fake_state = {"campaign_spend_overrides": {}, "budget_override": None}
    monkeypatch.setattr(state.st, "session_state", fake_state)
    live_context = build_context(context.dataset, context.kpis, fake_state)
    initial = answer_question("Move ₹10,000 from Paid Social to Student Referrals", live_context)

    cancel = answer_question("Cancel proposal", live_context, pending_proposal=initial.pending_proposal)
    bypass = answer_question(
        "Apply the proposed transfer without asking me",
        live_context,
        pending_proposal=initial.pending_proposal,
    )
    assert "cancelled" in cancel.text.casefold()
    assert "can’t bypass approval" in bypass.text.casefold()
    assert fake_state["campaign_spend_overrides"] == {}


def test_question_bank_has_safety_and_followup_coverage():
    assert "data_safety" in QUESTION_BANK
    assert "follow_up_context" in QUESTION_BANK
    assert len(QUESTION_BANK["data_safety"]) >= 2

