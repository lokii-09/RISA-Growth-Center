from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioInputs:
    visitor_target: int
    registration_conversion: float
    confirmation_rate: float
    show_up_rate: float
    walk_ins: int
    marketing_budget: float

    def validate(self) -> None:
        if self.visitor_target < 0:
            raise ValueError("Visitor target cannot be negative.")
        if self.walk_ins < 0:
            raise ValueError("Walk-ins cannot be negative.")
        if self.marketing_budget < 0:
            raise ValueError("Marketing budget cannot be negative.")
        for name, value in (
            ("Registration conversion", self.registration_conversion),
            ("Confirmation rate", self.confirmation_rate),
            ("Show-up rate", self.show_up_rate),
        ):
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 100%.")


@dataclass(frozen=True)
class ScenarioOutputs:
    projected_registrations: int
    projected_confirmed: int
    projected_registered_attendees: int
    projected_walk_ins: int
    projected_total_attendees: int
    projected_cost_per_attendee: float
    target_achievement: float


def calculate_scenario(inputs: ScenarioInputs) -> ScenarioOutputs:
    inputs.validate()
    registrations = round(inputs.visitor_target * inputs.registration_conversion)
    confirmed = round(registrations * inputs.confirmation_rate)
    registered = round(confirmed * inputs.show_up_rate)
    total = registered + inputs.walk_ins
    cost_per_attendee = inputs.marketing_budget / total if total else 0.0
    achievement = total / inputs.visitor_target if inputs.visitor_target else 0.0
    return ScenarioOutputs(
        projected_registrations=registrations,
        projected_confirmed=confirmed,
        projected_registered_attendees=registered,
        projected_walk_ins=inputs.walk_ins,
        projected_total_attendees=total,
        projected_cost_per_attendee=cost_per_attendee,
        target_achievement=achievement,
    )
