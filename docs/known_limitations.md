# Known Limitations

## Data and measurement

- The supplied CampusFest workbook identifies its records as synthetic. RISA has not been validated against a live event.
- Campaign source attribution is observational. Historical CPA and channel comparisons do not prove incremental or
  causal impact; the workbook contains no randomized experiment or causal ROI data.
- The source does not include attendee satisfaction/NPS, venue capacity, demographics, contact details for analyst
  tools, or reasons for registration/attendance drop-off.
- Reported reach, impressions, clicks, sessions, identified people, registrations, and verified attendance are distinct
  measures and should not be substituted for one another.
- Scenario results apply deterministic funnel assumptions. They are hypothetical planning estimates, not forecasts or
  causal spend-response models. Historical CPA extrapolations assume linear performance and may not generalize.
- Data quality decisions are deterministic: exact duplicate rows with stable IDs are removed from the working copy;
  conflicting stable-ID copies retain the first source row and are reported. Missing stable-ID rows remain in the
  working data and are reported.

## AI analyst

- The local analyst is rule-based and deliberately abstains outside its supported metrics and definitions. It is not a
  general-purpose assistant.
- The default Groq Cloud GPT-OSS provider was not evaluated live for this QA pass because no API credentials were
  supplied. Mocked provider behavior and local deterministic behavior are tested.
- Provider requests contain the user's question, bounded conversation history, and approved aggregated tool results.
  Do not submit confidential content unless the configured provider and its data terms are approved for it.
- The local safety checks and tool allowlist are not a substitute for provider-specific privacy/security review.

## State and hosting

- Budget allocations, budget overrides, scenario inputs, pending proposal context, and chat history are held in
  Streamlit session state. They are available during the active session/reruns, not shared between users or reliably
  retained after the session ends, app restarts, or redeployments.
- Historical workbook data is read-only. Planning changes do not write to the workbook.
- There is no database, user authentication layer, or durable multi-user planning store. If durable shared edits become
  a requirement, add authenticated access control and an appropriately secured database before relying on them.
- Public deployment has not been performed or verified. Keep sensitive data out of a public app and repository.
