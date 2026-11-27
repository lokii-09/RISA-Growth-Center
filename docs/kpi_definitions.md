# Central KPI Definitions

## Identified external people

- **Numerator:** Unique `person_id` values where `person_type = external` in People.
- **Denominator:** Not applicable.
- **Source:** People.

## External registrations

- **Numerator:** Unique `registration_id` values whose person is external and registration occurred on/before the selected cutoff.
- **Source:** Registrations joined to People.

## Confirmed external registrations

- **Numerator:** External unique registration IDs whose latest eligible Registration History status is `confirmed` at the selected cutoff.
- **Source:** Registrations, Registration History, People.

## Unique external attendees

- **Numerator:** Unique external `person_id` values with at least one Check-ins row having `result = admitted`, `verification = verified`, and timestamp on/before the cutoff within the event window.
- **Denominator:** Not applicable.
- **Source:** Check-ins and People.

## Registered attendees and walk-ins

- Registered: valid external attendee person IDs that have a valid external registration ID.
- Walk-in: valid external attendee person IDs that have no registration ID.
- **Source:** Check-ins, Registrations, People.

## Registered show rate

- `registered_attendees / confirmed_external_registrations`.
- The denominator excludes walk-ins.

## Campaign metrics

- Registrations and confirmations use the campaign ID recorded on the registration.
- Attributed attendees are distinct valid external attendee person IDs with that same recorded acquisition campaign registration.
- Spend is the sum of net `marketing_spend_inr` on/before the selected date; negative values are credits.
- `cost_per_attendee = spend / attributed_attendees`.
- `confirmed_to_attended = attributed_attendees / confirmed_external_registrations`.
- This is recorded attribution, not causal incrementality.

## Attendance by day

- Distinct external `person_id` values per Asia/Kolkata event date with valid admitted-and-verified check-ins.

## Funnel

Page visits, registration starts and brochure downloads are distinct external identified people by interaction event type. Impressions, clicks, sessions and reported reach are event/platform counts and are never relabeled as unique people.
