from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict

import pandas as pd


@dataclass
class CanonicalDataset:
    """Immutable source tables plus a separate cleaned working copy."""

    original: Dict[str, pd.DataFrame]
    working: Dict[str, pd.DataFrame]
    quality: Dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class QualityIssue:
    table: str
    issue_type: str
    count: int
    stable_id: str | None = None
    details: str = ""


@dataclass(frozen=True)
class HistoricalBaseline:
    as_of: datetime
    identified_external_people: int
    external_registrations: int
    confirmed_external_registrations: int
    unique_external_attendees: int
    registered_attendees: int
    walk_in_attendees: int
    campaign_spend: float
    revised_budget: float
    budget_remaining: float
