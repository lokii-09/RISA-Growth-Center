from __future__ import annotations

import re
from typing import Any

from ..dashboard.state import set_campaign_spend
from .tools import AnalystContext, get_budget_status, get_campaign_performance


def is_explicit_proposal_confirmation(message: str, proposal: dict[str, Any] | None) -> bool:
    if not proposal or proposal.get("status") != "pending_confirmation":
        return False
    normalized = re.sub(r"[.!?]+$", "", message.strip().casefold())
    return normalized in {
        "now apply it",
        "apply this transfer",
        "confirm this transfer",
        "confirm the transfer",
        "approve this transfer",
        "yes, apply it",
        "yes apply it",
    }


def apply_confirmed_proposal(context: AnalystContext, proposal: dict[str, Any]) -> None:
    """Revalidate a pending transfer against live planning state before applying it."""
    if proposal.get("status") != "pending_confirmation" or proposal.get("applied") is not False:
        raise ValueError("This proposal is no longer pending confirmation.")

    campaigns = get_campaign_performance(context)["campaigns"]
    by_id = {item["campaign_id"]: item for item in campaigns}
    source_id = proposal.get("source_campaign_id")
    destination_id = proposal.get("destination_campaign_id")
    if source_id not in by_id or destination_id not in by_id or source_id == destination_id:
        raise ValueError("The proposal references an unknown or duplicate campaign.")

    source = by_id[source_id]
    destination = by_id[destination_id]
    amount = float(proposal.get("amount", 0))
    if amount <= 0:
        raise ValueError("Proposal amount must be greater than zero.")
    if source["planning_spend"] != float(proposal.get("source_before", -1)):
        raise ValueError("Source allocation changed after this proposal was drafted. Draft it again.")
    if destination["planning_spend"] != float(proposal.get("destination_before", -1)):
        raise ValueError("Destination allocation changed after this proposal was drafted. Draft it again.")
    if amount > source["planning_spend"]:
        raise ValueError("The transfer now exceeds the available source allocation.")

    budget = get_budget_status(context)["current_planning_state"]
    if budget["is_over_budget"]:
        raise ValueError("Current planning spend exceeds the budget. Resolve that before applying this transfer.")
    expected_source = source["planning_spend"] - amount
    expected_destination = destination["planning_spend"] + amount
    if expected_source != float(proposal.get("source_after", -1)):
        raise ValueError("Proposal source values are inconsistent. Draft it again.")
    if expected_destination != float(proposal.get("destination_after", -1)):
        raise ValueError("Proposal destination values are inconsistent. Draft it again.")

    set_campaign_spend(source_id, expected_source)
    set_campaign_spend(destination_id, expected_destination)
