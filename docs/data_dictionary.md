# RISA Growth Center Data Dictionary

Generated from the workbook Field guide and actual worksheet inspection.

| Source table | Field | Data type | Meaning |
|---|---|---|---|
| event.csv | event_name | text | Fictional event display name. |
| event.csv | history_start | date | First covered snapshot date. |
| event.csv | history_end | date | Last covered snapshot date. |
| event.csv | event_starts_at | datetime | Planned event opening timestamp in IST. |
| event.csv | event_ends_at | datetime | Planned event closing timestamp in IST. |
| event.csv | timezone | text | Timezone for selected-day snapshots. |
| event.csv | currency | text | Currency used for marketing spend and reported sponsor values. |
| event.csv | fictional | boolean | All source records are synthetic. |
| targets.csv | effective_at | datetime | This full version of the targets takes effect at this timestamp. |
| targets.csv | identified_external_people_goal | number | Target cumulative distinct identified external people. |
| targets.csv | registration_goal | number | Target distinct external people with a registration. |
| targets.csv | unique_external_visitors_goal | number | Target distinct verified external event visitors. |
| targets.csv | marketing_budget_inr | number | Approved marketing spend limit, whole INR. |
| targets.csv | target_version | text | Readable label for the dated target plan. |
| campaigns.csv | campaign_name | text | Readable campaign label. campaign_id is the stable campaign key. |
| campaigns.csv | channel | text | Marketing distribution channel label. |
| campaigns.csv | target_audience | text | Intended audience description, not an observed audience count. |
| campaigns.csv | objective | text | Campaign purpose, not proof of an achieved outcome. |
| campaigns.csv | owner_name | text | Readable synthetic owner label. owner_id is the stable owner key. |
| campaigns.csv | created_at | datetime | When this source entity was created, as an ISO8601 IST timestamp. |
| campaigns.csv | planned_start_at | datetime | Planned campaign start known at creation. It is not an actual result. |
| campaigns.csv | planned_end_at | datetime | Planned campaign end known at creation. It is not an actual result. |
| campaigns.csv | campaign_id | text | Stable campaign key. In registrations this is the recorded acquisition source; in interactions it is the action context. Empty on check-ins means unattributed. |
| campaigns.csv | owner_id | text | Stable owner key matching the shared team dictionary. |
| campaign_daily.csv | campaign_name | text | Readable campaign label. campaign_id is the stable campaign key. |
| campaign_daily.csv | owner_name | text | Readable synthetic owner label. owner_id is the stable owner key. |
| campaign_daily.csv | activity_date | date | Daily reporting date in IST, as ISO8601 YYYY-MM-DD. The aggregate is available at end of this day. |
| campaign_daily.csv | impressions | number | Anonymous daily reported impression events. Not distinct people. |
| campaign_daily.csv | clicks | number | Anonymous daily reported click events. Not distinct people and not registrations. |
| campaign_daily.csv | reported_reach | number | Platform-reported reach for this day. Cross-day identity overlap is not supplied, so summing does not give globally unique people. |
| campaign_daily.csv | landing_page_sessions | number | Anonymous daily landing-page sessions. Includes traffic without an identified person and repeat sessions. |
| campaign_daily.csv | registration_starts | number | Anonymous daily form-start events. Not unique people or completed registrations. Identified form-start interactions are a subset. |
| campaign_daily.csv | marketing_spend_inr | number | Net posted marketing ledger amount for this campaign/date in whole INR. Debit minus credit. Draft quotes excluded, import copies deduplicated. Negative values are vendor credits. Tax is not modeled. |
| campaign_daily.csv | platform | text | Source reporting context for anonymous daily observations. |
| campaign_daily.csv | activity_id | text | Stable daily reporting record ID. Exact repeated IDs are import copies and count once. |
| campaign_daily.csv | campaign_id | text | Stable campaign key. In registrations this is the recorded acquisition source; in interactions it is the action context. Empty on check-ins means unattributed. |
| campaign_daily.csv | owner_id | text | Stable owner key matching the shared team dictionary. |
| people.csv | person_name | text | Synthetic natural full-name display label. Names can repeat; person_id is the identity key. |
| people.csv | person_type | text | external, internal, staff or test. Historical attendee targets apply to distinct external visitors. |
| people.csv | first_seen_at | datetime | When this identity first appears in the supplied acquisition or access records. Earlier than registration where upstream actions exist. |
| people.csv | first_touch_source | text | campaign, internal_registration, walk_in or event_access. An external walk-in can have no campaign or registration. |
| people.csv | first_campaign_name | text | Readable fixed first-source campaign label, if identified. Empty for unattributed walk-ins or event-access identities. |
| people.csv | owner_name | text | Readable synthetic owner label. owner_id is the stable owner key. |
| people.csv | person_id | text | Stable identity key. Preserved from earlier core attendance records or L-prefixed for new unregistered interested people. |
| people.csv | first_campaign_id | text | Stable fixed first-source campaign key. Empty means no campaign assignment, not proof of zero acquisition cost. |
| people.csv | owner_id | text | Stable owner key matching the shared team dictionary. |
| lead_interactions.csv | person_name | text | Synthetic natural full-name display label. Names can repeat; person_id is the identity key. |
| lead_interactions.csv | campaign_name | text | Readable campaign label. campaign_id is the stable campaign key. |
| lead_interactions.csv | owner_name | text | Readable synthetic owner label. owner_id is the stable owner key. |
| lead_interactions.csv | occurred_at | datetime | When this identified engagement action or admission observation occurs, as an ISO8601 IST timestamp. Filter it at or before the selected end of day. |
| lead_interactions.csv | event_type | text | Dated identified action: page_visit, brochure_download, registration_start, event_question_submitted, nurture_email_sent, nurture_email_opened, nurture_email_clicked or opted_out. |
| lead_interactions.csv | detail | text | Human-readable description of the identified action. It does not replace the structured event fields. |
| lead_interactions.csv | interaction_id | text | Unique identified-action record key. |
| lead_interactions.csv | person_id | text | Stable identity key. Preserved from earlier core attendance records or L-prefixed for new unregistered interested people. |
| lead_interactions.csv | campaign_id | text | Stable campaign key. In registrations this is the recorded acquisition source; in interactions it is the action context. Empty on check-ins means unattributed. |
| lead_interactions.csv | owner_id | text | Stable owner key matching the shared team dictionary. |
| registrations.csv | person_name | text | Synthetic natural full-name display label. Names can repeat; person_id is the identity key. |
| registrations.csv | campaign_name | text | Readable campaign label. campaign_id is the stable campaign key. |
| registrations.csv | owner_name | text | Readable synthetic owner label. owner_id is the stable owner key. |
| registrations.csv | registered_at | datetime | When this registration was created. An earlier lead action is not a completed registration. |
| registrations.csv | registration_id | text | Stable registration key joining registrations, status history and check-ins. Empty for people without a registration. |
| registrations.csv | person_id | text | Stable identity key. Preserved from earlier core attendance records or L-prefixed for new unregistered interested people. |
| registrations.csv | campaign_id | text | Stable campaign key. In registrations this is the recorded acquisition source; in interactions it is the action context. Empty on check-ins means unattributed. |
| registrations.csv | owner_id | text | Stable owner key matching the shared team dictionary. |
| registration_history.csv | person_name | text | Synthetic natural full-name display label. Names can repeat; person_id is the identity key. |
| registration_history.csv | campaign_name | text | Readable campaign label. campaign_id is the stable campaign key. |
| registration_history.csv | owner_name | text | Readable synthetic owner label. owner_id is the stable owner key. |
| registration_history.csv | effective_at | datetime | When this full registration-state version takes effect. For any date, choose latest eligible version per registration_id. |
| registration_history.csv | status | text | interested, confirmed, cancelled or waitlisted. Reconfirmation updates the same registration/person. |
| registration_history.csv | history_id | text | Stable registration-state version ID. Exact repeated IDs are import copies and count once. |
| registration_history.csv | registration_id | text | Stable registration key joining registrations, status history and check-ins. Empty for people without a registration. |
| registration_history.csv | person_id | text | Stable identity key. Preserved from earlier core attendance records or L-prefixed for new unregistered interested people. |
| registration_history.csv | campaign_id | text | Stable campaign key. In registrations this is the recorded acquisition source; in interactions it is the action context. Empty on check-ins means unattributed. |
| registration_history.csv | owner_id | text | Stable owner key matching the shared team dictionary. |
| checkins.csv | person_name | text | Synthetic natural full-name display label. Names can repeat; person_id is the identity key. |
| checkins.csv | campaign_name | text | Readable campaign label. campaign_id is the stable campaign key. |
| checkins.csv | owner_name | text | Readable synthetic owner label. owner_id is the stable owner key. |
| checkins.csv | occurred_at | datetime | When this identified engagement action or admission observation occurs, as an ISO8601 IST timestamp. Filter it at or before the selected end of day. |
| checkins.csv | result | text | admitted, denied or pending. Only admitted+verified records establish a verified admission. |
| checkins.csv | verification | text | verified or unverified. Pending/unverified observations do not by themselves establish actual attendance. |
| checkins.csv | source | text | scanner or manual. Manual records can add visitors or overlap scanner records. |
| checkins.csv | event_id | text | Stable admission-event ID. Exact repeated IDs are import copies and count once. Multiple different admission events can belong to one visitor. |
| checkins.csv | person_id | text | Stable identity key. Preserved from earlier core attendance records or L-prefixed for new unregistered interested people. |
| checkins.csv | registration_id | text | Stable registration key joining registrations, status history and check-ins. Empty for people without a registration. |
| checkins.csv | campaign_id | text | Stable campaign key. In registrations this is the recorded acquisition source; in interactions it is the action context. Empty on check-ins means unattributed. |
| checkins.csv | owner_id | text | Stable owner key matching the shared team dictionary. |