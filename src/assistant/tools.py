from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ..analytics.metrics import calculate_all_kpis
from ..cleaning import clean_dataset
from ..dashboard.scenario import ScenarioInputs, calculate_scenario
from ..dashboard.state import apply_campaign_spend_edits
from ..ingestion import load_workbook
from ..models import CanonicalDataset


@dataclass(frozen=True)
class AnalystContext:
    dataset: CanonicalDataset
    kpis: dict[str, Any]
    spend_overrides: dict[str, float] = field(default_factory=dict)
    budget_override: float | None = None
    scenario_assumptions: dict[str, Any] | None = None


def build_context(
    dataset: CanonicalDataset,
    kpis: dict[str, Any],
    session_state: Any | None = None,
) -> AnalystContext:
    session = session_state or {}
    return AnalystContext(
        dataset=dataset,
        kpis=kpis,
        spend_overrides=dict(session.get("campaign_spend_overrides", {})),
        budget_override=session.get("budget_override"),
        scenario_assumptions=session.get("scenario_assumptions"),
    )


def load_analyst_context(path: str, session_state: Any | None = None) -> AnalystContext:
    dataset = clean_dataset(load_workbook(path))
    kpis = calculate_all_kpis(dataset)
    return build_context(dataset, kpis, session_state)


class CampaignArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    campaign_names: list[str] | None = None


class ScenarioArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    visitor_target: int | None = Field(default=None, ge=0)
    registration_conversion: float | None = Field(default=None, ge=0, le=1)
    confirmation_rate: float | None = Field(default=None, ge=0, le=1)
    show_up_rate: float | None = Field(default=None, ge=0, le=1)
    walk_ins: int | None = Field(default=None, ge=0)
    marketing_budget: float | None = Field(default=None, ge=0)
    additional_campaign_budget: float | None = Field(default=None, ge=0)
    campaign_name: str | None = None
    source_campaign: str | None = None
    destination_campaign: str | None = None
    reallocation_amount: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_reallocation(self):
        if (self.source_campaign is None) != (self.destination_campaign is None):
            raise ValueError("Both source_campaign and destination_campaign are required for a reallocation.")
        if self.reallocation_amount is not None and self.source_campaign is None:
            raise ValueError("A reallocation amount requires source and destination campaigns.")
        return self


class ReallocationArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_campaign: str = Field(min_length=1)
    destination_campaign: str = Field(min_length=1)
    amount: float = Field(gt=0)
    reason: str = Field(default="Requested budget reallocation", max_length=400)

    @model_validator(mode="after")
    def distinct_campaigns(self):
        if self.source_campaign.strip().casefold() == self.destination_campaign.strip().casefold():
            raise ValueError("Source and destination campaigns must be different.")
        return self


TOOL_SCHEMAS: list[dict[str, Any]] = [
    {"type": "function", "function": {
        "name": "get_overview",
        "description": "Retrieve observed event growth KPIs, target progress, daily attendance and current planning spend/budget.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    }},
    {"type": "function", "function": {
        "name": "get_funnel",
        "description": "Retrieve identified visitor funnel counts, sequential conversions and drop-offs.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    }},
    {"type": "function", "function": {
        "name": "get_campaign_performance",
        "description": "Retrieve all campaigns or selected campaign names for comparison.",
        "parameters": {
            "type": "object",
            "properties": {"campaign_names": {"type": ["array", "null"], "items": {"type": "string"}}},
            "additionalProperties": False,
        },
    }},
    {"type": "function", "function": {
        "name": "get_budget_status",
        "description": "Retrieve historical actual spend and current editable planning budget/spend separately.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    }},
    {"type": "function", "function": {
        "name": "project_scenario",
        "description": "Project a hypothetical scenario using the shared deterministic Scenario Lab calculator.",
        "parameters": ScenarioArgs.model_json_schema(),
    }},
    {"type": "function", "function": {
        "name": "get_data_coverage",
        "description": "List supported data, definitions, and unsupported questions for honest abstention.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    }},
    {"type": "function", "function": {
        "name": "draft_budget_reallocation",
        "description": "Draft but never apply a proposed transfer between campaign spending allocations.",
        "parameters": ReallocationArgs.model_json_schema(),
    }},
]


def _as_of(context: AnalystContext) -> datetime:
    return context.kpis["baseline"].as_of


def _campaign_frame(context: AnalystContext) -> pd.DataFrame:
    return apply_campaign_spend_edits(context.kpis["campaigns"], context.spend_overrides)


def _effective_budget(context: AnalystContext) -> float:
    baseline = context.kpis["baseline"]
    return float(baseline.revised_budget if context.budget_override is None else context.budget_override)


def _current_scenario(context: AnalystContext) -> dict[str, Any]:
    if context.scenario_assumptions:
        return dict(context.scenario_assumptions)
    baseline = context.kpis["baseline"]
    funnel = context.kpis["funnel"]
    return {
        "visitor_target": int(funnel["identified_page_visitors"]),
        "registration_conversion": (
            funnel["external_registrations"] / funnel["identified_page_visitors"]
            if funnel["identified_page_visitors"] else 0
        ),
        "confirmation_rate": (
            funnel["confirmed_external_registrations"] / funnel["external_registrations"]
            if funnel["external_registrations"] else 0
        ),
        "show_up_rate": context.kpis["registered_show_rate"],
        "walk_ins": baseline.walk_in_attendees,
        "marketing_budget": _effective_budget(context),
    }


def get_overview(context: AnalystContext) -> dict[str, Any]:
    baseline = context.kpis["baseline"]
    targets = context.dataset.working["Targets"]
    effective = targets[targets["effective_at"].le(pd.Timestamp(_as_of(context)))].sort_values("effective_at")
    visitor_target = int(effective.iloc[-1]["unique_external_visitors_goal"]) if not effective.empty else 0
    planned_campaigns = _campaign_frame(context)
    planned_spend = float(planned_campaigns["spend"].sum())
    current_budget = _effective_budget(context)
    return {
        "evidence": "observed historical data plus separately labeled planning state",
        "as_of": pd.Timestamp(_as_of(context)).isoformat(),
        "identified_external_people": baseline.identified_external_people,
        "external_registrations": baseline.external_registrations,
        "confirmed_external_registrations": baseline.confirmed_external_registrations,
        "registered_attendees": baseline.registered_attendees,
        "walk_in_attendees": baseline.walk_in_attendees,
        "unique_external_attendees": baseline.unique_external_attendees,
        "attendee_target": visitor_target,
        "target_achievement": baseline.unique_external_attendees / visitor_target if visitor_target else 0.0,
        "registered_show_rate": context.kpis["registered_show_rate"],
        "attendance_by_day": dict(context.kpis["attendance_by_day"]),
        "historical_campaign_spend": baseline.campaign_spend,
        "historical_budget": baseline.revised_budget,
        "historical_budget_remaining": baseline.budget_remaining,
        "planning_spend": planned_spend,
        "current_planning_budget": current_budget,
        "planning_budget_remaining": current_budget - planned_spend,
        "blended_cost_per_attendee": context.kpis["blended_cost_per_attendee"],
        "attribution_caveat": "Campaign attribution is recorded attribution, not proof of causal impact.",
    }


def get_funnel(context: AnalystContext) -> dict[str, Any]:
    funnel = context.kpis["funnel"]
    stages = [
        ("identified_page_visitors", "Identified visitors"),
        ("registration_starters", "Registration starters"),
        ("external_registrations", "Completed registrations"),
        ("confirmed_external_registrations", "Confirmed registrations"),
        ("registered_attendees", "Registered attendees"),
    ]
    results: list[dict[str, Any]] = []
    for index, (key, label) in enumerate(stages):
        count = int(funnel[key])
        if index == 0:
            conversion, dropoff, dropoff_rate = None, 0, None
            previous_label = None
        else:
            previous_key, previous_label = stages[index - 1]
            previous = int(funnel[previous_key])
            conversion = count / previous if previous else 0
            dropoff = max(previous - count, 0)
            dropoff_rate = dropoff / previous if previous else 0
        results.append({
            "stage": label,
            "count": count,
            "denominator_count": previous if index else None,
            "conversion_from_previous": conversion,
            "dropoff_from_previous": dropoff,
            "dropoff_rate": dropoff_rate,
            "denominator_stage": previous_label,
        })
    bottleneck = max(results[1:], key=lambda row: row["dropoff_from_previous"])
    return {
        "as_of": pd.Timestamp(_as_of(context)).isoformat(),
        "stages": results,
        "largest_bottleneck": bottleneck,
        "definition": "Distinct external people at identified stages; attendance is registered attendees only. Walk-ins are a separate route.",
        "source_tables": ["People", "Interest and Engagement", "Registrations", "Registration History", "Check-ins"],
    }


def get_campaign_performance(context: AnalystContext, campaign_names: list[str] | None = None) -> dict[str, Any]:
    frame = _campaign_frame(context)
    if campaign_names:
        wanted = {name.casefold() for name in campaign_names}
        unknown = wanted - {str(name).casefold() for name in frame["campaign_name"]}
        if unknown:
            raise ValueError(f"Unknown campaign name(s): {', '.join(sorted(unknown))}")
        frame = frame[frame["campaign_name"].str.casefold().isin(wanted)]
    frame = frame.sort_values("cost_per_attendee", na_position="last")
    campaigns = []
    for row in frame.itertuples(index=False):
        historical_row = context.kpis["campaigns"].loc[
            context.kpis["campaigns"]["campaign_id"].eq(row.campaign_id)
        ].iloc[0]
        campaigns.append({
            "campaign_id": row.campaign_id,
            "campaign_name": row.campaign_name,
            "historical_spend": float(historical_row["spend"]),
            "planning_spend": float(row.spend),
            "identified_people": int(row.identified_people),
            "registrations": int(row.external_registrations),
            "confirmed_registrations": int(row.confirmed_external_registrations),
            "attendees": int(row.attributed_attendees),
            "registration_conversion": (
                float(row.external_registrations / row.identified_people) if row.identified_people else 0
            ),
            "confirmation_rate": (
                float(row.confirmed_external_registrations / row.external_registrations)
                if row.external_registrations else 0
            ),
            "confirmed_to_attended_rate": (
                float(row.confirmed_to_attended) if row.confirmed_to_attended else 0
            ),
            "historical_cost_per_attendee": (
                float(historical_row["cost_per_attendee"])
                if pd.notna(historical_row["cost_per_attendee"]) else None
            ),
            "planning_cost_per_attendee": (
                float(row.cost_per_attendee) if pd.notna(row.cost_per_attendee) else None
            ),
        })
    return {
        "campaigns": campaigns,
        "comparison_note": "Attribution reflects recorded registration source and is not causal incrementality.",
        "as_of": pd.Timestamp(_as_of(context)).isoformat(),
    }


def get_budget_status(context: AnalystContext) -> dict[str, Any]:
    baseline = context.kpis["baseline"]
    campaigns = _campaign_frame(context)
    budget = _effective_budget(context)
    spend = float(campaigns["spend"].sum())
    details = [
        {
            "campaign": row.campaign_name,
            "historical_actual_spend": float(context.kpis["campaigns"].loc[
                context.kpis["campaigns"]["campaign_id"].eq(row.campaign_id), "spend"
            ].iloc[0]),
            "current_planning_spend": float(row.spend),
        }
        for row in campaigns.itertuples(index=False)
    ]
    return {
        "historical_actual": {
            "budget": baseline.revised_budget,
            "spend": baseline.campaign_spend,
            "remaining": baseline.budget_remaining,
        },
        "current_planning_state": {
            "budget": budget,
            "spend": spend,
            "remaining": budget - spend,
            "utilization": spend / budget if budget else 0,
            "is_over_budget": spend > budget,
            "campaign_spending": details,
        },
        "editing_note": "Planning values are session-only; source workbook and historical actuals are unchanged.",
    }


def project_scenario(context: AnalystContext, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    parsed = ScenarioArgs.model_validate(arguments or {})
    base_values = _current_scenario(context)
    base_inputs = ScenarioInputs(**base_values)
    overrides = parsed.model_dump(exclude_none=True)
    for key in ("source_campaign", "destination_campaign", "reallocation_amount", "additional_campaign_budget", "campaign_name"):
        overrides.pop(key, None)
    proposed_values = {**base_values, **overrides}

    allocation_amount = parsed.reallocation_amount or 0
    if parsed.additional_campaign_budget:
        proposed_values["marketing_budget"] = (
            float(proposed_values["marketing_budget"]) + parsed.additional_campaign_budget
        )
    proposed_inputs = ScenarioInputs(**proposed_values)
    base_output = calculate_scenario(base_inputs)
    proposed_output = calculate_scenario(proposed_inputs)

    historic_efficiency_estimate: dict[str, Any] | None = None
    if parsed.source_campaign and parsed.destination_campaign and allocation_amount:
        campaigns = get_campaign_performance(context)["campaigns"]
        by_name = {item["campaign_name"].casefold(): item for item in campaigns}
        source = by_name.get(parsed.source_campaign.casefold())
        destination = by_name.get(parsed.destination_campaign.casefold())
        if source is None or destination is None:
            raise ValueError("Both scenario campaigns must match known campaign names.")
        source_cpa = source["historical_cost_per_attendee"]
        destination_cpa = destination["historical_cost_per_attendee"]
        delta = (
            allocation_amount / destination_cpa - allocation_amount / source_cpa
            if source_cpa and destination_cpa else None
        )
        historic_efficiency_estimate = {
            "source_campaign": source["campaign_name"],
            "destination_campaign": destination["campaign_name"],
            "amount": allocation_amount,
            "estimated_attendee_difference_at_historical_cpa": delta,
            "basis": "Linear estimate from observed average cost per attributed attendee; not causal or guaranteed.",
        }
    elif parsed.additional_campaign_budget:
        if not parsed.campaign_name:
            raise ValueError("campaign_name is required when estimating an additional campaign budget.")
        campaign_list = get_campaign_performance(context)["campaigns"]
        selected = next(
            (item for item in campaign_list if item["campaign_name"].casefold() == parsed.campaign_name.casefold()),
            None,
        )
        if selected is None:
            raise ValueError(f"Unknown campaign name: {parsed.campaign_name}")
        cpa = selected["historical_cost_per_attendee"]
        historic_efficiency_estimate = {
            "campaign": selected["campaign_name"],
            "additional_budget": parsed.additional_campaign_budget,
            "estimated_attendees_at_historical_cpa": (
                parsed.additional_campaign_budget / cpa if cpa else None
            ),
            "basis": "Linear estimate from observed average cost per attributed attendee; not causal or guaranteed.",
        }

    return {
        "classification": "hypothetical scenario, not actual results",
        "base_inputs": base_values,
        "proposed_inputs": proposed_values,
        "base_projection": base_output.__dict__,
        "proposed_projection": proposed_output.__dict__,
        "attendee_difference": proposed_output.projected_total_attendees - base_output.projected_total_attendees,
        "budget_difference": proposed_inputs.marketing_budget - base_inputs.marketing_budget,
        "historical_efficiency_estimate": historic_efficiency_estimate,
        "limitation": "The deterministic Scenario Lab applies funnel rates, not a causal spend-response curve. Any campaign efficiency estimate is historical average CPA only.",
    }


def get_data_coverage(context: AnalystContext) -> dict[str, Any]:
    event = context.dataset.working["Event"].iloc[0]
    return {
        "available_tables": {
            name: int(len(context.dataset.working[name]))
            for name in (
                "Event", "Targets", "Campaigns", "Daily Marketing", "People",
                "Interest and Engagement", "Registrations", "Registration History", "Check-ins",
            )
        },
        "history_window": {
            "start": pd.Timestamp(event["history_start"]).isoformat(),
            "end": pd.Timestamp(event["history_end"]).isoformat(),
            "timezone": str(event["timezone"]),
        },
        "supported": [
            "External people, registrations and latest registration status",
            "Distinct verified admitted external attendees and walk-in split",
            "Distinct external attendance by event day",
            "Recorded campaign attribution and net posted spend",
            "Identified funnel, targets and planning budget overrides",
        ],
        "unsupported": {
            "attendee_satisfaction_or_nps": "No survey/NPS table or field.",
            "causal_campaign_lift": "Observational source attribution only; no randomized experiment.",
            "global_unique_platform_reach": "No identity overlap across platform-reported daily reach.",
            "venue_capacity": "No approved capacity is included in the workbook.",
            "demographics_or_college_affiliation": "No age, geography or college affiliation fields.",
            "weather_or_travel_effects": "No weather, route or travel data.",
            "emails_or_contact_details": "The application analytics tools do not expose contact data.",
        },
        "definitions": {
            "unique_attendee": "Distinct external person_id with an admitted AND verified check-in.",
            "registered_attendee": "Valid external attendee who has an external registration.",
            "walk_in": "Valid external attendee with no registration.",
            "registered_show_rate": "Registered external attendees divided by confirmed external registrations.",
            "attendance_by_day": "Distinct valid external attendees per event date; a repeat attendee can appear on multiple days.",
            "campaign_attribution": "Recorded registration campaign source; not proof of causal impact.",
            "reported_reach": "Daily platform count; never a cross-day unique person count.",
        },
    }


def draft_budget_reallocation(context: AnalystContext, arguments: dict[str, Any]) -> dict[str, Any]:
    parsed = ReallocationArgs.model_validate(arguments)
    campaign_list = get_campaign_performance(context)["campaigns"]
    by_name = {item["campaign_name"].casefold(): item for item in campaign_list}
    source = by_name.get(parsed.source_campaign.casefold())
    destination = by_name.get(parsed.destination_campaign.casefold())
    if source is None or destination is None:
        raise ValueError("Source and destination must be existing campaign names.")

    amount = float(parsed.amount)
    current_source = source["planning_spend"]
    current_destination = destination["planning_spend"]
    if amount > current_source:
        raise ValueError(
            f"Requested transfer ({amount:,.0f}) exceeds source planning spend ({current_source:,.0f})."
        )
    budget = _effective_budget(context)
    planned_total = sum(item["planning_spend"] for item in campaign_list)
    if planned_total > budget:
        raise ValueError("Current planning spend already exceeds the configured budget; reset or raise the budget before drafting a transfer.")

    source_new, destination_new = current_source - amount, current_destination + amount
    source_cpa = source["historical_cost_per_attendee"]
    destination_cpa = destination["historical_cost_per_attendee"]
    estimated_change = (
        amount / destination_cpa - amount / source_cpa
        if source_cpa and destination_cpa else None
    )
    return {
        "proposal_id": str(uuid4()),
        "source_campaign": source["campaign_name"],
        "source_campaign_id": source["campaign_id"],
        "source_before": current_source,
        "source_after": source_new,
        "destination_campaign": destination["campaign_name"],
        "destination_campaign_id": destination["campaign_id"],
        "destination_before": current_destination,
        "destination_after": destination_new,
        "amount": amount,
        "reason": parsed.reason,
        "current_planning_budget": budget,
        "planned_spend_before": planned_total,
        "planned_spend_after": planned_total,
        "estimated_attendee_difference_at_historical_cpa": estimated_change,
        "risk": "Historical campaign CPA is not causal or guaranteed; a budget move may not reproduce prior performance.",
        "measurement": "Review updated registrations, confirmed registrations, verified attendees, and CPA after the next campaign window.",
        "status": "pending_confirmation",
        "applied": False,
    }


def execute_tool(name: str, arguments: dict[str, Any], context: AnalystContext) -> dict[str, Any]:
    if name == "get_overview":
        return get_overview(context)
    if name == "get_funnel":
        return get_funnel(context)
    if name == "get_campaign_performance":
        args = CampaignArgs.model_validate(arguments)
        return get_campaign_performance(context, args.campaign_names)
    if name == "get_budget_status":
        return get_budget_status(context)
    if name == "project_scenario":
        return project_scenario(context, arguments)
    if name == "get_data_coverage":
        return get_data_coverage(context)
    if name == "draft_budget_reallocation":
        return draft_budget_reallocation(context, arguments)
    raise ValueError(f"Tool is not approved: {name}")
