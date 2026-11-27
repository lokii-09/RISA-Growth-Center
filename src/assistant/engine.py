from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from ..dashboard.state import reset_budget_state
from .provider import AIProviderError, ChatProvider, OpenAICompatibleProvider, ProviderSettings
from .tools import (
    TOOL_SCHEMAS,
    AnalystContext,
    draft_budget_reallocation,
    execute_tool,
    get_budget_status,
    get_campaign_performance,
    get_data_coverage,
    get_funnel,
    get_overview,
    project_scenario,
)


SYSTEM_PROMPT = """You are RISA's AI Growth Analyst for the synthetic CampusFest 2025 dataset.
You may only use the supplied approved tools for authoritative numbers. Never calculate KPIs yourself
from raw records, invent data, infer causation from attribution, or claim a hypothetical outcome is real.
Use tool results as the sole numeric source. Explain denominators, event-close scope and evidence limitations.
Distinguish observed historical facts, session-only planning edits, hypotheses and scenario projections.
For unknown coverage, say what is missing. Do not expose personal names/contact details.
Never execute a write. A draft_budget_reallocation tool only creates a pending proposal; the user must
explicitly confirm it in the UI. Do not claim a change was applied unless the UI confirms it.
Be concise and practical: answer, evidence, interpretation, next step."""


@dataclass
class AnalystReply:
    text: str
    tools_used: list[str] = field(default_factory=list)
    pending_proposal: dict[str, Any] | None = None
    mode: str = "local"
    provider_error: str | None = None


def _money(value: float) -> str:
    return f"₹{value:,.2f}"


def _rate(value: float) -> str:
    return f"{value * 100:.1f}%"


def _clean_history(history: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {"role": item["role"], "content": item["content"][:4000]}
        for item in history[-12:]
        if item.get("role") in {"user", "assistant"} and item.get("content")
    ]


def _numeric_claims_grounded(text: str, tool_results: list[dict[str, Any]]) -> bool:
    available: list[float] = []

    def collect(value: Any) -> None:
        if isinstance(value, bool):
            return
        if isinstance(value, (int, float)):
            available.append(float(value))
        elif isinstance(value, dict):
            for nested in value.values():
                collect(nested)
        elif isinstance(value, (list, tuple)):
            for nested in value:
                collect(nested)

    for result in tool_results:
        collect(result)

    claims = re.finditer(
        r"(?<![\w])(?:₹|INR\s*|Rs\.?\s*)?(-?\d[\d,]*(?:\.\d+)?)\s*(%)?",
        text,
        flags=re.IGNORECASE,
    )
    for claim in claims:
        number = float(claim.group(1).replace(",", ""))
        if claim.group(2):
            if not any(
                0 <= value <= 1 and abs(value * 100 - number) < 0.6
                for value in available
            ):
                return False
        elif not any(abs(value - number) < 0.000001 for value in available):
            return False
    return True


def resolve_followup(question: str, history: list[dict[str, str]], context: AnalystContext) -> str:
    normalized = question.strip().casefold()
    if not history:
        return question
    last_user = next((item["content"] for item in reversed(history) if item.get("role") == "user"), "")
    last_assistant = next((item["content"] for item in reversed(history) if item.get("role") == "assistant"), "")
    campaign_names = context.dataset.working["Campaigns"]["campaign_name"].tolist()
    mentioned = [
        name for name in campaign_names
        if name.casefold() in last_assistant.casefold()
    ]
    mentioned.sort(key=lambda name: last_assistant.casefold().find(name.casefold()))

    if "second one" in normalized or "second campaign" in normalized:
        if len(mentioned) >= 2:
            return f"Tell me about the {mentioned[1]} campaign."
    if "compare those" in normalized or "compare them" in normalized:
        if len(mentioned) >= 2:
            return f"Compare {mentioned[0]} with {mentioned[1]}."
    if normalized in {"why?", "why", "how so?", "how so", "explain", "can you explain?"}:
        return f"Explain the evidence for this follow-up: {last_user}"
    return question


def _mentioned_campaigns(question: str, context: AnalystContext) -> list[str]:
    names = context.dataset.working["Campaigns"]["campaign_name"].tolist()
    normalized = question.casefold()
    matches = [
        (normalized.find(name.casefold()), name)
        for name in names
        if name.casefold() in normalized
    ]
    aliases = {
        "campus ambassador": "Campus Ambassadors",
        "paid social": "Paid Social",
        "creator partner": "Creator Partners",
        "college partnership": "College Partnerships",
        "student referral": "Student Referrals",
        "referral": "Student Referrals",
        "organic search": "Organic Search",
        "community group": "Community Groups",
    }
    for alias, campaign in aliases.items():
        position = normalized.find(alias)
        if position >= 0 and not any(name == campaign for _, name in matches):
            matches.append((position, campaign))
    matches.sort(key=lambda item: item[0])
    return [name for _, name in matches]


def _extract_amount(question: str) -> float | None:
    match = re.search(
        r"(?:₹|INR\s*|Rs\.?\s*)?(\d[\d,]*(?:\.\d+)?)\s*(k|thousand|l|lakh|lakhs)?",
        question,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    value = float(match.group(1).replace(",", ""))
    suffix = (match.group(2) or "").casefold()
    if suffix in {"k", "thousand"}:
        value *= 1000
    elif suffix in {"l", "lakh", "lakhs"}:
        value *= 100000
    return value


def _extract_percent(question: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent)", question, flags=re.IGNORECASE)
    if match:
        return float(match.group(1)) / 100
    points = re.search(r"(\d+(?:\.\d+)?)\s*(?:percentage points?|pp)\b", question, flags=re.IGNORECASE)
    return float(points.group(1)) / 100 if points else None


def _unsupported_answer(question: str, context: AnalystContext) -> AnalystReply | None:
    lower = question.casefold()
    coverage = get_data_coverage(context)
    unsupported_terms = {
        "satisfaction": "attendee_satisfaction_or_nps",
        "nps": "attendee_satisfaction_or_nps",
        "caused": "causal_campaign_lift",
        "cause": "causal_campaign_lift",
        "incremental lift": "causal_campaign_lift",
        "causal roi": "causal_campaign_lift",
        "incremental roi": "causal_campaign_lift",
        "return on investment": "causal_campaign_lift",
        "unique reach": "global_unique_platform_reach",
        "capacity": "venue_capacity",
        "venue cap": "venue_capacity",
        "college affiliation": "demographics_or_college_affiliation",
        "age group": "demographics_or_college_affiliation",
        "weather": "weather_or_travel_effects",
        "travel time": "weather_or_travel_effects",
        "email address": "emails_or_contact_details",
        "phone number": "emails_or_contact_details",
        "list attendee": "emails_or_contact_details",
        "attendee names": "emails_or_contact_details",
    }
    key = next((term for term in unsupported_terms if term in lower), None)
    if key is None:
        return None
    field = unsupported_terms[key]
    return AnalystReply(
        text=f"I can’t answer that from the available dataset: {coverage['unsupported'][field]}",
        tools_used=["get_data_coverage"],
    )


def _scenario_reply(question: str, context: AnalystContext) -> AnalystReply | None:
    lower = question.casefold()
    is_scenario = any(
        phrase in lower
        for phrase in (
            "what if",
            "what happens if",
            "what would happen if",
            "scenario",
            "can we reach",
            "could we reach",
            "budget would we need",
        )
    )
    if "how much budget" in lower and any(term in lower for term in ("reach", "attendee", "target")):
        is_scenario = True
    if not is_scenario:
        return None

    campaigns = _mentioned_campaigns(question, context)
    amount = _extract_amount(question)
    percent = _extract_percent(question)
    args: dict[str, Any] = {}
    if "show" in lower and percent is not None:
        args["show_up_rate"] = percent
    elif "confirm" in lower and percent is not None:
        args["confirmation_rate"] = percent
    elif ("conversion" in lower or "registration rate" in lower) and percent is not None:
        if "percentage point" in lower or "pp" in lower:
            current = project_scenario(context)["base_inputs"]["registration_conversion"]
            args["registration_conversion"] = min(current + percent, 1.0)
        else:
            args["registration_conversion"] = percent

    reallocation_match = re.search(r"\b(?:move|shift|transfer|reallocat\w*)\b", lower)
    if reallocation_match and len(campaigns) >= 2 and amount is not None:
        args.update({
            "source_campaign": campaigns[0],
            "destination_campaign": campaigns[1],
            "reallocation_amount": amount,
        })
    elif amount is not None and ("spend" in lower or "budget" in lower) and campaigns:
        args.update({
            "campaign_name": campaigns[-1],
            "additional_campaign_budget": amount,
        })

    if "budget would we need" in lower or (
        "how much budget" in lower and any(term in lower for term in ("reach", "attendee", "target"))
    ):
        goal = amount
        if goal is None:
            return AnalystReply(
                text="What attendee target should I estimate the budget for?",
                tools_used=["get_data_coverage"],
            )
        overview = get_overview(context)
        estimate = goal * overview["blended_cost_per_attendee"]
        return AnalystReply(
            text=(
                f"At the historical blended cost of {_money(overview['blended_cost_per_attendee'])} per attendee, "
                f"{goal:,.0f} attendees imply approximately {_money(estimate)} in spend. "
                "This is a linear planning estimate from historical average CPA, not a causal or guaranteed budget requirement."
            ),
            tools_used=["get_overview"],
        )

    try:
        result = project_scenario(context, args)
    except (ValueError, ValidationError) as exc:
        return AnalystReply(
            text=f"I could not calculate that scenario: {exc}",
            tools_used=["project_scenario"],
        )
    base = result["base_projection"]
    proposed = result["proposed_projection"]
    diff = result["attendee_difference"]
    text = (
        f"Hypothetical only: the current scenario projects {base['projected_total_attendees']:,} total attendees "
        f"({base['projected_registered_attendees']:,} registered + {base['projected_walk_ins']:,} walk-ins). "
        f"The modified assumptions project {proposed['projected_total_attendees']:,} "
        f"({proposed['projected_registered_attendees']:,} registered + {proposed['projected_walk_ins']:,} walk-ins), "
        f"a change of {diff:+,}. Projected marketing budget is {_money(result['proposed_inputs']['marketing_budget'])} "
        f"and projected cost per attendee is {_money(proposed['projected_cost_per_attendee'])}."
    )
    proposed_inputs = result["proposed_inputs"]
    text += (
        f" Assumptions: {proposed_inputs['visitor_target']:,} visitors, "
        f"{_rate(proposed_inputs['registration_conversion'])} visitor-to-registration, "
        f"{_rate(proposed_inputs['confirmation_rate'])} confirmation, "
        f"{_rate(proposed_inputs['show_up_rate'])} registered show-up, "
        f"{proposed_inputs['walk_ins']:,} walk-ins and {_money(proposed_inputs['marketing_budget'])} budget. "
        f"Scenario Lab target achievement is {_rate(proposed['target_achievement'])} "
        "(projected total attendees divided by its visitor-target input)."
    )
    budget_overage = proposed_inputs["marketing_budget"] - result["base_inputs"]["marketing_budget"]
    if budget_overage > 0:
        text += (
            f" This scenario exceeds its current planning budget by {_money(budget_overage)}; "
            "no budget values have been changed."
        )
    target_match = re.search(
        r"(?:reach|achieve|hit)\s*(?:about\s*)?([\d,]+)\s*(?:attendees|people)",
        lower,
    )
    if target_match:
        target = int(target_match.group(1).replace(",", ""))
        difference = proposed["projected_total_attendees"] - target
        if difference >= 0:
            text += f" This projection is {difference:,} above the {target:,}-attendee goal."
        else:
            text += f" This projection is {abs(difference):,} below the {target:,}-attendee goal."
    estimate = result.get("historical_efficiency_estimate")
    if estimate:
        if "estimated_attendee_difference_at_historical_cpa" in estimate:
            delta = estimate["estimated_attendee_difference_at_historical_cpa"]
            delta_text = "not estimable" if delta is None else f"{delta:+.1f} attendees"
            text += (
                f" Historical-CPA comparison for shifting {_money(estimate['amount'])} from "
                f"{estimate['source_campaign']} to {estimate['destination_campaign']}: {delta_text}."
            )
        else:
            estimate_value = estimate.get("estimated_attendees_at_historical_cpa")
            delta_text = "not estimable" if estimate_value is None else f"about {estimate_value:.1f} attendees"
            text += f" At the historical average CPA, the added allocation could equate to {delta_text}."
    text += " This uses observed funnel rates; historical campaign efficiency is not causal or guaranteed."
    return AnalystReply(text=text, tools_used=["project_scenario"])


def _local_reply(
    question: str,
    context: AnalystContext,
    history: list[dict[str, str]],
    pending_proposal: dict[str, Any] | None = None,
) -> AnalystReply:
    resolved = resolve_followup(question, history, context)
    lower = resolved.casefold()

    unsupported = _unsupported_answer(resolved, context)
    if unsupported:
        return unsupported

    if lower.strip() in {"confirm", "yes", "apply it", "now apply it"}:
        return AnalystReply(
            text="No changes have been applied. Use the explicit Confirm button on the pending proposal card to approve this exact transfer.",
        )
    if "without asking me" in lower or "without confirmation" in lower:
        return AnalystReply(
            text="I can’t bypass approval. Budget changes require an explicit confirmation on the proposal card; no values have been changed.",
        )
    if lower.strip() in {"cancel", "cancel proposal", "reject it", "reject proposal"}:
        return AnalystReply(text="Proposal cancelled. No campaign planning values were changed.")

    if any(term in lower for term in (
        "reset planning edits",
        "reset budget edits",
        "reset proposed edits",
        "reset the proposed edits",
        "reset all planning edits",
        "restore original planning",
    )):
        reset_budget_state()
        return AnalystReply(
            text="Planning edits have been reset to the workbook-based values for this session. Historical source data was not changed.",
            tools_used=["get_budget_status"],
        )

    campaigns_mentioned = _mentioned_campaigns(resolved, context)
    amount = _extract_amount(resolved)
    revising = bool(
        pending_proposal
        and amount is not None
        and any(phrase in lower for phrase in ("change that to", "revise that to", "make it", "change it to"))
    )
    if revising:
        campaigns_mentioned = [
            pending_proposal["source_campaign"],
            pending_proposal["destination_campaign"],
        ]
    explicit_proposal = any(word in lower for word in ("draft", "propose", "proposal", "move", "transfer", "reallocate", "shift"))
    hypothetical = any(
        phrase in lower
        for phrase in ("what if", "what happens if", "what would happen if", "hypothetical")
    )
    if (revising or (explicit_proposal and not hypothetical)) and len(campaigns_mentioned) >= 2 and amount is not None:
        try:
            proposal = draft_budget_reallocation(
                context,
                {
                    "source_campaign": campaigns_mentioned[0],
                    "destination_campaign": campaigns_mentioned[1],
                    "amount": amount,
                    "reason": f"User-requested planning transfer from {campaigns_mentioned[0]} to {campaigns_mentioned[1]}",
                },
            )
        except (ValueError, ValidationError) as exc:
            return AnalystReply(text=f"I couldn’t draft that transfer: {exc}", tools_used=["draft_budget_reallocation"])
        delta = proposal["estimated_attendee_difference_at_historical_cpa"]
        estimate = "not estimable" if delta is None else f"{delta:+.1f} attendees at historical average CPA"
        return AnalystReply(
            text=(
                f"I {'revised' if revising else 'drafted'} a transfer of {_money(amount)} from {proposal['source_campaign']} "
                f"({_money(proposal['source_before'])} → {_money(proposal['source_after'])}) to "
                f"{proposal['destination_campaign']} ({_money(proposal['destination_before'])} → "
                f"{_money(proposal['destination_after'])}). Estimated direction: {estimate}. "
                f"This is based on historical average CPA, not causal evidence. Risk: {proposal['risk']} "
                "Review the proposal card and explicitly Confirm or Cancel."
            ),
            tools_used=["get_campaign_performance", "get_budget_status", "draft_budget_reallocation"],
            pending_proposal=proposal,
        )
    if explicit_proposal and not hypothetical and amount is None:
        return AnalystReply(
            text="I can draft that, but need the transfer amount and the source and destination campaign names.",
            tools_used=["get_campaign_performance", "get_budget_status"],
        )
    if explicit_proposal and not hypothetical and amount is not None and len(campaigns_mentioned) < 2:
        return AnalystReply(
            text="Which source campaign should fund this transfer? I have not drafted or applied any change.",
            tools_used=["get_campaign_performance", "get_budget_status"],
        )

    scenario = _scenario_reply(resolved, context)
    if scenario:
        return scenario

    if any(term in lower for term in (
        "biggest growth problem",
        "biggest bottleneck",
        "where are we losing",
        "funnel",
        "drop off",
        "drop-off",
        "confirmed registrants",
        "not attending",
        "loss before",
        "after confirmation",
        "traffic",
        "registration conversion",
        "confirmation rate",
        "low confirmation",
        "failed to confirm",
    )) and (
        not campaigns_mentioned
        or any(term in lower for term in ("biggest growth problem", "biggest bottleneck", "where are we losing", "funnel"))
    ):
        result = get_funnel(context)
        issue = result["largest_bottleneck"]
        if "traffic" in lower and "conversion" in lower:
            visitors = result["stages"][0]
            registrations = next(item for item in result["stages"] if item["stage"] == "Completed registrations")
            visitor_to_registration_gap = visitors["count"] - registrations["count"]
            return AnalystReply(
                text=(
                    f"{registrations['count']:,} of {visitors['count']:,} identified visitors completed registration "
                    f"({_rate(registrations['count'] / visitors['count'] if visitors['count'] else 0)}); "
                    f"{visitor_to_registration_gap:,} fewer identified visitors reached completion, including "
                    f"{registrations['dropoff_from_previous']:,} drop-offs between registration starters and completions. "
                    "The dataset has no benchmark proving this conversion is low. Test a registration-flow change and compare the rate."
                ),
                tools_used=["get_funnel"],
            )
        elif any(term in lower for term in ("confirmation rate", "low confirmation", "failed to confirm")):
            registrations = next(item for item in result["stages"] if item["stage"] == "Completed registrations")
            confirmed = next(item for item in result["stages"] if item["stage"] == "Confirmed registrations")
            return AnalystReply(
                text=(
                    f"{confirmed['count']:,} of {registrations['count']:,} external registrations were confirmed "
                    f"({_rate(confirmed['conversion_from_previous'])}); {confirmed['dropoff_from_previous']:,} "
                    "did not reach confirmed status. The workbook shows the gap, not its cause."
                ),
                tools_used=["get_funnel"],
            )
        if "confirmed registrants" in lower or "not attending" in lower:
            attendance_drop = next(
                item for item in result["stages"]
                if item["stage"] == "Registered attendees"
            )
            return AnalystReply(
                text=(
                    f"{attendance_drop['dropoff_from_previous']:,} of {attendance_drop['denominator_count']:,} "
                    f"confirmed registrations did not appear as registered attendees "
                    f"({_rate(attendance_drop['dropoff_rate'])} drop-off). "
                    "The dataset can show the size of this gap but not why it happened. Test reminders or arrival support "
                    "and measure changes in verified registered attendance."
                ),
                tools_used=["get_funnel"],
            )
        if "loss before" in lower or "after confirmation" in lower:
            confirmed_stage = next(item for item in result["stages"] if item["stage"] == "Confirmed registrations")
            attendance_drop = next(
                item for item in result["stages"]
                if item["stage"] == "Registered attendees"
            )
            before_confirmation = result["stages"][0]["count"] - confirmed_stage["count"]
            after_confirmation = attendance_drop["dropoff_from_previous"]
            larger = "before" if before_confirmation > after_confirmation else "after"
            return AnalystReply(
                text=(
                    f"More of the identified-to-confirmed funnel loss occurred before confirmation: "
                    f"{before_confirmation:,} fewer identified visitors reached confirmed status, versus "
                    f"{after_confirmation:,} confirmed registrations not appearing as registered attendees. "
                    f"By these cumulative counts, the larger loss is {larger} confirmation. Walk-ins are a separate route."
                ),
                tools_used=["get_funnel"],
            )
        return AnalystReply(
            text=(
                f"The largest single funnel loss is from {issue['denominator_stage']} to {issue['stage']}: "
                f"{issue['dropoff_from_previous']:,} people, or {_rate(issue['dropoff_rate'])} of that stage. "
                f"That leaves {issue['count']:,} registered attendees from {issue['denominator_stage']} "
                f"({_rate(issue['conversion_from_previous'])} conversion). Walk-ins are separate and do not inflate registered show rate. "
                "Prioritize a measured confirmation/show-up recovery test, then compare the result by campaign."
            ),
            tools_used=["get_funnel"],
        )

    if "completed registration" in lower:
        result = get_funnel(context)
        completed = next(
            item for item in result["stages"]
            if item["stage"] == "Completed registrations"
        )
        return AnalystReply(
            text=f"There were {completed['count']:,} completed external registrations, counted by unique registration ID.",
            tools_used=["get_funnel"],
        )

    if "allocate" in lower and "remaining" in lower:
        budget = get_budget_status(context)["current_planning_state"]
        campaigns = get_campaign_performance(context)["campaigns"]
        efficient = sorted(
            campaigns,
            key=lambda item: item["historical_cost_per_attendee"] or float("inf"),
        )[:2]
        return AnalystReply(
            text=(
                f"The current planning balance is {_money(budget['remaining'])}. Consider only a small, capped test "
                f"with {efficient[0]['campaign_name']} and {efficient[1]['campaign_name']}, whose historical "
                f"attributed costs were {_money(efficient[0]['historical_cost_per_attendee'] or 0)} and "
                f"{_money(efficient[1]['historical_cost_per_attendee'] or 0)} per attendee. These are observational "
                "averages, not causal lift; keep the total within budget and measure verified attendees before scaling. "
                "No allocation has been changed."
            ),
            tools_used=["get_budget_status", "get_campaign_performance"],
        )

    if any(term in lower for term in ("budget", "spend", "remaining", "utilization")):
        result = get_budget_status(context)
        actual = result["historical_actual"]
        plan = result["current_planning_state"]
        if plan["remaining"] > 0:
            budget_note = "There is unallocated planning budget; utilization alone does not show that it should be spent."
        elif plan["remaining"] < 0:
            budget_note = "Planning spend currently exceeds the budget; resolve the overage before committing additional spend."
        else:
            budget_note = "The current planning allocation uses the full configured budget."
        return AnalystReply(
            text=(
                f"Historical event-close spend was {_money(actual['spend'])} from a {_money(actual['budget'])} budget, "
                f"leaving {_money(actual['remaining'])}. Current session planning values are "
                f"{_money(plan['spend'])} spend against {_money(plan['budget'])}, leaving "
                f"{_money(plan['remaining'])} ({_rate(plan['utilization'])} utilization). "
                f"{budget_note} Planning edits are temporary and do not change historical actuals."
            ),
            tools_used=["get_budget_status"],
        )

    if any(term in lower for term in (
        "attendance by day",
        "daily attendance",
        "attendees each day",
        "attendees per day",
        "each day",
        "per day",
    )):
        result = get_overview(context)
        daily = result["attendance_by_day"]
        counts = "; ".join(f"{day}: {count:,}" for day, count in daily.items())
        return AnalystReply(
            text=(
                f"Distinct valid external attendance by event day: {counts}. "
                "A repeat attendee may appear once on each day, so these daily counts should not be summed as event-unique people."
            ),
            tools_used=["get_overview"],
        )

    if any(term in lower for term in ("what should i do", "recommend", "prioritize", "scale", "next", "opportunity")):
        campaigns = get_campaign_performance(context)["campaigns"]
        funnel = get_funnel(context)
        best = sorted(campaigns, key=lambda item: item["historical_cost_per_attendee"] or float("inf"))[:2]
        bottleneck = funnel["largest_bottleneck"]
        return AnalystReply(
            text=(
                f"Recommendation: pilot additional effort in {best[0]['campaign_name']} and "
                f"{best[1]['campaign_name']} because their historical costs per attributed attendee were "
                f"{_money(best[0]['historical_cost_per_attendee'] or 0)} and "
                f"{_money(best[1]['historical_cost_per_attendee'] or 0)}. In parallel, test recovery at the "
                f"{bottleneck['denominator_stage']} → {bottleneck['stage']} step, where "
                f"{bottleneck['dropoff_from_previous']:,} people dropped off. Set a small budget cap and measure "
                "verified attendee CPA and show-up rate before scaling. This is a recommendation based on historical "
                "association, not guaranteed incremental lift."
            ),
            tools_used=["get_campaign_performance", "get_funnel", "get_budget_status"],
        )

    if any(term in lower for term in (
        "campaign", "paid social", "referral", "college partnership", "creator",
        "working well", "what is working", "what's working",
    )):
        selected = campaigns_mentioned or None
        is_diagnosis = any(term in lower for term in ("why", "poor", "underperform"))
        result = get_campaign_performance(context, None if is_diagnosis else selected)
        items = result["campaigns"]
        if not items:
            return AnalystReply(text="No campaign data matched that filter.", tools_used=["get_campaign_performance"])
        paid = next((item for item in items if item["campaign_name"] == "Paid Social"), None)
        college = next((item for item in items if item["campaign_name"] == "College Partnerships"), None)
        if paid and college and is_diagnosis:
            return AnalystReply(
                text=(
                    f"Paid Social has a higher historical cost per attributed attendee "
                    f"({_money(paid['historical_cost_per_attendee'] or 0)}) than College Partnerships "
                    f"({_money(college['historical_cost_per_attendee'] or 0)}), and a lower confirmed-to-attended rate "
                    f"({_rate(paid['confirmed_to_attended_rate'])} vs {_rate(college['confirmed_to_attended_rate'])}). "
                    "The workbook does not show why this happened or prove channel causality. "
                    "Recommendation: cap broad paid acquisition and run a measured high-intent retargeting test."
                ),
                tools_used=["get_campaign_performance"],
            )
        if len(items) == 1:
            item = items[0]
            return AnalystReply(
                text=(
                    f"{item['campaign_name']} recorded {_money(item['historical_spend'])} historical spend, "
                    f"while its current session planning allocation is {_money(item['planning_spend'])}. "
                    f"{item['identified_people']:,} identified people, {item['registrations']:,} registrations, "
                    f"{item['confirmed_registrations']:,} confirmed and {item['attendees']:,} attributed attendees. "
                    f"Registration conversion was {_rate(item['registration_conversion'])}, confirmation rate was "
                    f"{_rate(item['confirmation_rate'])} and confirmed-to-attended was "
                    f"{_rate(item['confirmed_to_attended_rate'])}; "
                    f"historical cost per attributed attendee was {_money(item['historical_cost_per_attendee'] or 0)}. "
                    "This is recorded attribution, not proof the campaign caused attendance."
                ),
                tools_used=["get_campaign_performance"],
            )

        if len(items) >= 2 and ("compare" in lower or "vs" in lower or "versus" in lower):
            by_name = {item["campaign_name"]: item for item in items}
            ordered = [by_name[name] for name in campaigns_mentioned if name in by_name]
            first, second = (ordered + [item for item in items if item not in ordered])[:2]
            return AnalystReply(
                text=(
                    f"{first['campaign_name']}: {first['attendees']:,} attendees, "
                    f"{_rate(first['registration_conversion'])} registration conversion, "
                    f"{_rate(first['confirmation_rate'])} confirmation, "
                    f"{_money(first['historical_cost_per_attendee'] or 0)} per attendee, "
                    f"{_rate(first['confirmed_to_attended_rate'])} confirmed-to-attended. "
                    f"{second['campaign_name']}: {second['attendees']:,} attendees, "
                    f"{_rate(second['registration_conversion'])} registration conversion, "
                    f"{_rate(second['confirmation_rate'])} confirmation, "
                    f"{_money(second['historical_cost_per_attendee'] or 0)} per attendee, "
                    f"{_rate(second['confirmed_to_attended_rate'])} confirmed-to-attended. "
                    "These are historical source-attributed outcomes, not causal comparisons."
                ),
                tools_used=["get_campaign_performance"],
            )

        lowest_cpa = min(items, key=lambda item: item["historical_cost_per_attendee"] or float("inf"))
        highest_volume = max(items, key=lambda item: item["attendees"])
        highest_cpa = max(items, key=lambda item: item["historical_cost_per_attendee"] or 0)
        return AnalystReply(
            text=(
                f"By historical average cost per attributed attendee, {lowest_cpa['campaign_name']} is lowest at "
                f"{_money(lowest_cpa['historical_cost_per_attendee'] or 0)}. "
                f"{highest_volume['campaign_name']} delivered the most attributed attendees ({highest_volume['attendees']:,}), "
                f"while {highest_cpa['campaign_name']} had the highest cost ({_money(highest_cpa['historical_cost_per_attendee'] or 0)}). "
                "Prioritize small, measurable investment tests and compare verified attendees, not reach alone. "
                "Observed attribution is not causal proof."
            ),
            tools_used=["get_campaign_performance"],
        )

    if any(term in lower for term in (
        "overall", "performing", "attendees", "walk-in", "walk in", "registration",
        "show rate", "target", "attendance by day", "daily attendance", "each day", "per day",
    )):
        result = get_overview(context)
        return AnalystReply(
            text=(
                f"At event close, RISA recorded {result['unique_external_attendees']:,} unique verified external attendees "
                f"against a {result['attendee_target']:,} target ({_rate(result['target_achievement'])}). "
                f"There were {result['external_registrations']:,} external registrations, "
                f"{result['confirmed_external_registrations']:,} confirmed, "
                f"{result['registered_attendees']:,} registered attendees and {result['walk_in_attendees']:,} walk-ins. "
                f"Registered show rate was {_rate(result['registered_show_rate'])}; historical spend was "
                f"{_money(result['historical_campaign_spend'])}, leaving {_money(result['historical_budget_remaining'])}. "
                "Attendees are distinct people with valid admitted-and-verified scans."
            ),
            tools_used=["get_overview"],
        )

    return AnalystReply(
        text=(
            "I don’t have enough context to answer that from the approved analytics tools. "
            "Try asking about overall attendees, a funnel stage, a named campaign, budget, or a hypothetical scenario."
        ),
        tools_used=["get_data_coverage"],
    )


def _provider_reply(
    question: str,
    context: AnalystContext,
    history: list[dict[str, str]],
    provider: ChatProvider,
) -> AnalystReply:
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(_clean_history(history))
    messages.append({"role": "user", "content": question})
    used: list[str] = []
    tool_results: list[dict[str, Any]] = []
    pending: dict[str, Any] | None = None
    expected_tools = _expected_tools(question)
    for _ in range(5):
        response = provider.complete(messages, TOOL_SCHEMAS)
        message = response["choices"][0]["message"]
        calls = message.get("tool_calls") or []
        if not isinstance(calls, list) or any(
            not isinstance(call, dict) or not isinstance(call.get("function"), dict)
            for call in calls
        ):
            raise AIProviderError("AI provider returned malformed tool calls.")
        if not calls:
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                if not expected_tools.issubset(set(used)):
                    return _local_reply(question, context, history)
                if not _numeric_claims_grounded(content, tool_results):
                    return _local_reply(question, context, history)
                return AnalystReply(content.strip(), used, pending, "provider")
            raise AIProviderError("AI provider returned no answer.")
        messages.append(message)
        for call in calls:
            try:
                function = call["function"]
                name = function["name"]
                arguments = json.loads(function.get("arguments") or "{}")
                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be an object.")
                result = execute_tool(name, arguments, context)
                used.append(name)
                if name == "draft_budget_reallocation":
                    pending = result
                tool_results.append(result)
                tool_content = json.dumps(result, ensure_ascii=False, default=str)
            except (KeyError, json.JSONDecodeError, TypeError, ValidationError, ValueError) as exc:
                tool_content = json.dumps({"error": str(exc)})
                function = call.get("function")
                name = str(function.get("name", "unknown")) if isinstance(function, dict) else "unknown"
            messages.append({
                "role": "tool",
                "tool_call_id": str(call.get("id", "")),
                "name": name,
                "content": tool_content,
            })
    raise AIProviderError("AI analyst exceeded the approved tool-call limit. Please refine the question.")


def _expected_tools(question: str) -> set[str]:
    lower = question.casefold()
    if "completed registration" in lower or any(term in lower for term in (
        "confirmed registrants",
        "not attending",
        "loss before",
        "after confirmation",
    )):
        return {"get_funnel"}
    if "budget would we need" in lower or (
        "how much budget" in lower and any(term in lower for term in ("reach", "attendee", "target"))
    ):
        return {"get_overview"}
    if any(phrase in lower for phrase in (
        "what if",
        "what happens if",
        "what would happen if",
        "scenario",
        "can we reach",
        "could we reach",
    )):
        return {"project_scenario"}
    if "allocate" in lower and "remaining" in lower:
        return {"get_budget_status", "get_campaign_performance"}
    if any(term in lower for term in ("what should i do", "recommend", "prioritize", "scale", "next", "opportunity")):
        return {"get_campaign_performance", "get_funnel"}
    if any(term in lower for term in (
        "campaign", "paid social", "referral", "college partnership", "creator",
        "working well", "what is working", "what's working",
    )):
        return {"get_campaign_performance"}
    if any(term in lower for term in (
        "biggest growth problem", "biggest bottleneck", "where are we losing", "funnel",
        "drop off", "drop-off", "confirmed registrants", "not attending", "loss before",
        "after confirmation", "traffic", "registration conversion", "confirmation rate",
        "low confirmation",
        "failed to confirm",
    )):
        return {"get_funnel"}
    if any(term in lower for term in ("budget", "spend", "remaining", "utilization")):
        return {"get_budget_status"}
    if any(term in lower for term in (
        "overall", "performing", "attendees", "walk-in", "walk in", "registration",
        "show rate", "target", "attendance by day", "daily attendance", "each day", "per day",
    )):
        return {"get_overview"}
    return {"get_data_coverage"}


def answer_question(
    question: str,
    context: AnalystContext,
    history: list[dict[str, str]] | None = None,
    provider: ChatProvider | None = None,
    pending_proposal: dict[str, Any] | None = None,
) -> AnalystReply:
    bounded_history = history or []
    resolved = resolve_followup(question, bounded_history, context)
    unsupported = _unsupported_answer(resolved, context)
    if unsupported:
        return unsupported

    lower = resolved.casefold()
    if any(term in lower for term in (
        "execute python",
        "run python",
        "execute code",
        "run code",
        "run a script",
        "execute script",
        "arbitrary code",
    )):
        return AnalystReply(
            text="I can’t execute arbitrary code. I can only use the approved analytics tools for supported questions.",
        )
    is_action_or_confirmation = (
        lower.strip() in {"confirm", "yes", "apply it", "now apply it", "cancel", "cancel proposal", "reject it", "reject proposal"}
        or any(phrase in lower for phrase in ("draft", "propose", "proposal", "move", "transfer", "reallocate", "shift"))
        and not any(phrase in lower for phrase in (
            "what if",
            "what happens if",
            "what would happen if",
            "hypothetical",
        ))
        or any(phrase in lower for phrase in (
            "reset planning edits",
            "reset budget edits",
            "reset proposed edits",
            "reset the proposed edits",
            "reset all planning edits",
            "restore original planning",
        ))
        or pending_proposal is not None
        and any(phrase in lower for phrase in ("change that to", "revise that to", "make it", "change it to"))
    )
    if is_action_or_confirmation:
        return _local_reply(resolved, context, bounded_history, pending_proposal)

    if provider is not None:
        try:
            return _provider_reply(resolved, context, bounded_history, provider)
        except AIProviderError as exc:
            fallback = _local_reply(resolved, context, bounded_history, pending_proposal)
            fallback.provider_error = str(exc)
            fallback.mode = "local_fallback"
            return fallback
    return _local_reply(resolved, context, bounded_history, pending_proposal)


def configured_provider() -> tuple[ChatProvider | None, str | None]:
    try:
        settings = ProviderSettings.from_environment()
    except AIProviderError as exc:
        return None, str(exc)
    if settings is None:
        return None, "No RISA_AI_API_KEY configured; using the deterministic local analyst."
    return OpenAICompatibleProvider(settings), None
