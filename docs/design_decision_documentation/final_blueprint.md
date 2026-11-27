# RISA Growth APM — Final Design & Architecture Blueprint

**Selected challenge:** A — Attendee Growth  
**Selected city:** Bengaluru (strategic planning choice; not present in the historical workbook)  
**Historical reference event:** CampusFest 2025, 12–13 April 2025 (fictional and synthetic)  
**Historical revised marketing budget:** ₹3,00,000  
**Product concept:** Festival Growth Center — analytics, campaign execution, experimentation and an embedded AI Growth Analyst.

---

## 1. Executive recommendation

Build a data-driven Festival Growth Center, not a generic chatbot with charts attached.

The product should have one reliable analytics and decision layer. The dashboard and chatbot both read the same live calculations. The LLM explains results, compares options and drafts actions; deterministic Python/SQL functions calculate metrics and write changes only after confirmation.

**Design principle:**

> Data computes. Rules decide. AI explains and proposes. A human approves. The system records and refreshes.

The product should demonstrate one complete loop:

1. A campaign or funnel problem appears in live data.
2. The dashboard identifies the bottleneck.
3. The AI Analyst diagnoses it using typed tools.
4. The Analyst recommends a budget move or task.
5. The user reviews and confirms.
6. The database, dashboard, campaign statuses, projections and audit log update.
7. A follow-up question reads the new state rather than repeating stale context.

## 2. Assessment of the two reference blueprints

### Keep from Blueprint 1 — analytical rigor

- One source of truth and live recalculation.
- Immutable original data and a reset-to-original control.
- Editable targets, assumptions and decision thresholds.
- Confidence-weighted prioritisation.
- Minimum sample gates and an explicit “insufficient data” state.
- Capacity-aware reserve release.
- Driver decomposition and sensitivity analysis.
- Typed chatbot tools over live application data.
- Deterministic calculations outside the LLM.
- Data provenance, cannot-answer behaviour, confirm-before-write and audit logging.

### Keep from Blueprint 2 — communication and presentation

- Action-oriented slide titles.
- Three-zone slide compositions and strong base/stretch comparison.
- Explicit choices to double down, cap, change or reject.
- Risk-first experimentation tables.
- The workflow: Live telemetry → AI diagnosis → confirmed execution.
- Verification in referral mechanics and explicit failure risks.

### Discard or rebuild

- Do not carry forward either blueprint’s ₹6.5 lakh or ₹15 lakh budget. The workbook’s revised approved budget is ₹3 lakh.
- Do not carry forward a three-day event. CampusFest 2025 is a two-day event.
- Do not use assumed attendance goals of 12,500–32,000. Historical unique external attendance is 2,050.
- Do not use a 10% overlap haircut. Person IDs let us deduplicate actual people and assign the recorded acquisition source.
- Do not use last-touch attribution. The workbook records first-source acquisition campaign IDs; these match the registration campaign IDs for registered people.
- Do not use unsupported city market sizes, 50–60% metro-driven show-up assumptions, an invented viral K-factor, or unexplained RICE-C scores.
- Do not count a killed offline strategy in a contribution total or include its budget in the core plan.

## 3. Workbook inspection and evidence base

### 3.1 What the source contains

The workbook has 11 worksheets. All source people and campaign activity are synthetic.

| Sheet | Source rows (excluding header) | Main use |
|---|---:|---|
| Read me | 8 | Event and data-handling guidance |
| Field guide | 86 | Field definitions and aggregation rules |
| Event | 1 | Event dates and timezone |
| Targets | 2 | Original and revised targets |
| Campaigns | 7 | Campaign/channel/owner dictionary |
| Daily Marketing | 483 | Anonymous daily traffic and spend events |
| People | 3,685 | Stable person identities and first-touch source |
| Interest and Engagement | 11,650 | Identified engagement events |
| Registrations | 2,840 | Registration entities |
| Registration History | 5,911 | Effective-dated status versions |
| Check-ins | 3,390 | Admission events |

Event: CampusFest 2025, 12 April 2025 10:00 to 13 April 2025 20:00, Asia/Kolkata. History coverage: 15 January to 20 April 2025.

### 3.2 Actual performance versus revised targets

The revised target version took effect on 15 March 2025:

| Metric | Revised target | Historical actual | Achievement |
|---|---:|---:|---:|
| Identified external people | 3,600 | 3,625 | 100.7% |
| External registrations | 3,200 | 2,800 | 87.5% |
| Unique verified external visitors | 2,200 | 2,050 | 93.2% |
| Approved marketing budget | ₹3,00,000 | ₹2,76,500 spent by event close | 92.2% |

At event close, ₹23,500 remained unspent. Two later credits totalling ₹2,500 were posted on 16 and 18 April, bringing the net ledger total through 20 April to ₹2,74,000. For event-acquisition CAC, use spend posted through event close: ₹2,76,500.

### 3.3 Correct attendance definitions and counts

Do not equate check-in rows with unique attendees.

- 3,370 unique check-in event IDs remain after removing 20 exact import duplicates.
- 3,290 records are admitted AND verified admission events across all person types.
- Those valid events represent 2,090 unique people, including 20 internal, 10 staff and 10 test identities.
- **Unique verified external attendees = 2,050 distinct external `person_id` values.**
- 1,925 of those attendees had a registration; 125 were unregistered external walk-ins.
- There were 2,500 distinct external registrations in confirmed status at event close.
- **Registered show rate = 1,925 / 2,500 = 77.0%.** Do not divide all 2,050 visitors by 2,500 and call it a registered show rate: that would include walk-ins.

Other attendance signals:

- 12 April: 1,430 unique external visitors.
- 13 April: 1,345 unique external visitors.
- 725 people attended on both days.
- Unique visitor-days: 2,775; average days attended per unique visitor: 2,775 / 2,050 = 1.354.
- Peak arrival window: 400 admitted-and-verified external admission events from 18:00–18:59 on 12 April. These are admission events, not 400 unique people.

### 3.4 Identified funnel and high-intent leakage

The person-level funnel is unusually clean:

| Stage | Unique people | Conversion from previous stage |
|---|---:|---:|
| Identified campaign page visitors | 3,500 | — |
| Registration starts | 3,075 | 87.9% |
| Completed external registrations | 2,800 | 91.1% |
| Confirmed external registrations | 2,500 | 89.3% |
| Registered external attendees | 1,925 | 77.0% of confirmed |

Among the 3,500 identified campaign page visitors, 700 did not complete a registration:

- 425 did not start registration.
- 275 started registration but did not complete it.
- 319 of the 700 non-registrants downloaded the brochure; these overlap with the two groups above and must not be added again.

This creates a measurable Intent Recovery opportunity.

### 3.5 Engagement signals

| Behaviour | Events / unique actors |
|---|---:|
| Page visits | 3,500 |
| Registration starts | 3,075 |
| Brochure downloads | 1,818 |
| Nurture emails sent | 1,400 |
| Nurture emails opened | 992 |
| Nurture email clicks | 409 |
| Event questions submitted | 227 |
| Opt-outs | 229 |

Within the sent cohort, 992/1,400 opened (70.9%), and 409/992 openers clicked (41.2%). 178 people in the sent cohort opted out (12.7%); 229 opt-out actors appear in total. The application must suppress opted-out people from future nurture actions.

### 3.6 Campaign performance

Campaign-level cost per attendee uses campaign spend posted by event close divided by unique verified external visitors attributed through the registration’s recorded source campaign. Walk-ins remain unattributed.

| Campaign | Spend by event close | Identified people | External registrations | Confirmed | Attributed attendees | Confirmed-to-attended | Cost / attendee |
|---|---:|---:|---:|---:|---:|---:|---:|
| Campus Ambassadors | ₹42,000 | 600 | 520 | 480 | 390 | 81.3% | ₹107.69 |
| Paid Social | ₹93,000 | 960 | 680 | 580 | 340 | 58.6% | ₹273.53 |
| Creator Partners | ₹61,000 | 490 | 350 | 290 | 175 | 60.3% | ₹348.57 |
| College Partnerships | ₹31,000 | 500 | 450 | 420 | 385 | 91.7% | ₹80.52 |
| Student Referrals | ₹19,500 | 410 | 350 | 320 | 275 | 85.9% | ₹70.91 |
| Organic Search | ₹14,000 | 290 | 250 | 225 | 195 | 86.7% | ₹71.79 |
| Community Groups | ₹16,000 | 250 | 200 | 185 | 165 | 89.2% | ₹96.97 |

Blended event-close cost per unique external attendee = ₹2,76,500 / 2,050 = **₹134.88**.

Key implications:

1. College Partnerships has the highest attributed volume (385) and a 91.7% confirmed-to-attended rate at ₹80.52 per attendee.
2. Student Referrals is the lowest-cost channel (₹70.91 per attendee), with an 85.9% show rate.
3. Organic Search is similarly efficient (₹71.79 per attendee).
4. Paid Social and Creator Partners together spent ₹1,54,000 and produced 515 campaign-attributed attendees. Their combined cost per attributed attendee is about ₹299. They need a major redesign, not more broad spend.
5. Campus Ambassadors and Community Groups remain useful supporting channels; their costs and show rates should stay visible in the dashboard.

These are recorded-attribution comparisons, not proof of causal incrementality.

### 3.7 Data-quality findings and rules

| Table | Exact duplicate stable IDs |
|---|---:|
| Daily Marketing | 2 activity IDs |
| Registration History | 4 history IDs |
| Check-ins | 20 event IDs |

Additional validated rules:

- Use stable IDs (`person_id`, `campaign_id`, `registration_id`, `history_id`, `event_id`, `activity_id`) rather than display names.
- Referential checks for people, campaigns, owners and registration IDs passed in the inspected source tables.
- Select the latest eligible `registration_history` version by `effective_at` per `registration_id` as of the selected date.
- Deduplicate identical stable source IDs but retain the original rows in the immutable source copy.
- For attendance, keep `result = admitted` AND `verification = verified`; count distinct external `person_id` once across the full event window.
- For daily attendance, count distinct external `person_id` by date. For gate-load analysis, count valid admission events and label them as events.
- Campaign `reported_reach` is daily platform-reported reach. Cross-day unique identity overlap is not available; never sum it and label the result global unique reach.
- `Daily Marketing` impressions, clicks, sessions and registration starts are anonymous event counts, not unique people.
- `Interest and Engagement.campaign_id` is the action context; `Registrations.campaign_id` is the recorded acquisition source.
- Respect Asia/Kolkata timestamps and date cut-offs. Do not show future or post-event outcomes in earlier snapshots.
- Campaign spend is net posted debits less credits on posting date; negative values are credits. Draft requests are excluded; tax is not modelled.

### 3.8 What the workbook cannot answer

The workbook does not contain:

- The historical event's city, venue or approved venue capacity.
- College affiliation, student demographics, age or geographic home location per person.
- Globally deduplicated cross-day platform reach.
- Multi-touch attribution or controlled causal experiments.
- Attendee satisfaction or survey/NPS data.
- Group size, referral invitations sent, verified squad IDs or a measured viral K-factor.
- Competition participation/supporter relationships.
- Weather, travel time, transport mode or competitor-event impact.

These are missing fields, not values the chatbot should infer. Capacity, city and new growth tactics can be added as clearly labelled planning assumptions.

---

## 4. Strategic choices

### 4.1 Challenge

Challenge A is retained. The attendee funnel has enough person-level volume, multiple campaign channels, a measurable registration and attendance journey, and fast operational feedback. This makes it particularly suitable for the dashboard, experiments and AI decision loop.

### 4.2 City: Bengaluru

Choose Bengaluru as the next-edition planning city because the strategy relies on campus alliances, student societies, ambassadors and referral groups. Bengaluru Urban was reported as having 1,148 colleges in AISHE 2023–24, the highest district count in the country. This supports a dense institutional-partner strategy, not an assumed 1,148-college addressable audience.

Sources:

- AISHE Final Report 2023–24: https://aishe.gov.in/document/aishe-final-report-2023-24/
- AISHE district college count reporting: https://www.newindianexpress.com/cities/bengaluru/2026/Jul/14/karnataka-bengaluru-lead-in-higher-education

The source workbook does not identify a city. Bengaluru is therefore an external strategic choice [S], not a historical dataset fact [D].

### 4.3 Festival and budget planning assumptions

- Two-day event, following the historical reference structure [D].
- ₹3,00,000 total marketing budget ceiling [D: revised target].
- The next edition is a planning scenario; its targets are not historical observations.
- The number and size of partner colleges must be built from an actual shortlisted institution list. Do not convert the 1,148-college count into a student TAM without additional research.

### 4.4 Evidence tags

Use these labels on slides, in the README and in chatbot outputs:

- `[D]` — directly present in the supplied dataset.
- `[C]` — calculated from dataset fields or stated assumptions.
- `[A]` — planning assumption, target, scenario input or proposed experiment.
- `[S]` — external source with a link.

---

## 5. Next-edition base and stretch model

### 5.1 Historical conversion rates

- Page visitor → completed registration = 2,800 / 3,500 = 80.0% [C].
- Registration → confirmed = 2,500 / 2,800 = 89.3% [C].
- Confirmed → registered attendance = 1,925 / 2,500 = 77.0% [C].
- Walk-ins = 125 [D].

### 5.2 Scenario model

| Funnel stage | Historical actual [D] | Base [A/C] | Stretch [A/C] |
|---|---:|---:|---:|
| Unique campaign page visitors | 3,500 | 4,000 | 4,375 |
| Registration starts | 3,075 | 3,514 | 3,844 |
| Completed external registrations | 2,800 | 3,200 | 3,500 |
| Confirmed registrations | 2,500 | 2,880 (90%) | 3,220 (92%) |
| Registered attendees | 1,925 | 2,304 (80% of confirmed) | 2,576 (80% of confirmed) |
| Unregistered walk-ins | 125 | 125 | 150 |
| **Unique external attendees** | **2,050** | **2,429 (~2,430)** | **2,726** |

Base arithmetic: `3,200 × 90% × 80% + 125 = 2,429`.

Stretch arithmetic: `3,500 × 92% × 80% + 150 = 2,726`.

The projected 4,000 and 4,375 page visitors use the historical 80% identified page-visitor-to-registration conversion. Registration starts are projected using the historical 87.9% page-visitor-to-start rate, and completed registration uses the historical 91.1% start-to-registration rate.

### 5.3 Unit economics

At the full ₹3,00,000 budget ceiling:

- Base: ₹3,00,000 / 2,429 = about ₹123.51 per unique external attendee.
- Stretch: ₹3,00,000 / 2,726 = about ₹110.05 per unique external attendee.
- Historical actual: ₹2,76,500 / 2,050 = ₹134.88 per unique external attendee.

These estimates assume the planned budget is fully used; unused reserve reduces actual spend per attendee.

### 5.4 Capacity model

The source has no venue capacity. Add an editable planning cap of **1,800 unique external visitor entries per day [A]** as a temporary scenario input; the organiser must replace it with the venue-approved limit.

Historical attendance behaviour:

- 2,775 visitor-days / 2,050 unique visitors = 1.354 days per visitor [C].
- Day 1 share of visitor-days = 1,430 / 2,775 = 51.5% [C].
- Day 2 share = 48.5% [C].

At this historical pattern:

- Base 2,429 attendees imply about 3,288 visitor-days, approximately 1,694 on Day 1 and 1,594 on Day 2. This fits the illustrative cap.
- Stretch 2,726 attendees imply about 3,690 visitor-days, approximately 1,902 on Day 1 and 1,788 on Day 2. This slightly exceeds the illustrative total two-day capacity of 3,600 visitor-days and the Day 1 cap.

Operational response: use day-specific passes, release slots against verified capacity, incentivise Day 2 distribution and monitor arrival peaks. If the actual venue cap differs, the scenario must recalculate.

### 5.5 Sensitivity checks

For the base scenario (3,200 registrations, 90% confirmation, 80% show rate, 125 walk-ins):

- Show rate falls from 80% to 75%: about 144 fewer registered attendees (`2,880 × 5%`).
- Registration volume falls 10%: about 230 fewer total attendees (`320 × 90% × 80%`).
- Confirmation rate falls from 90% to 85%: about 128 fewer attendees (`3,200 × 5% × 80%`).
- Walk-ins fall by 50: total attendance falls by 50.

The dashboard must show the assumption being changed, the recalculated outcome, the delta and the capacity impact.

---

## 6. Five growth bets and budget allocation

### 6.1 Prioritisation framework

Use **confidence-weighted incremental unique attendees per ₹ lakh**:

`Score = (Base-case incremental unique attendees × evidence-confidence weight) / incremental budget in ₹ lakh`

This is deliberately simpler and more auditable than the reference RICE-C score. It directly rewards attendee impact and capital efficiency, while confidence discounts tactics that have weak evidence. Confidence weights are management judgements [A], not probabilities calculated from the workbook. Apply a separate dependency, time-to-first-signal and operational-risk review before releasing money. One person can count under only one recorded acquisition source; deduplicate by `person_id`. No flat overlap haircut.

| Initiative | Base incremental attendees used in score | Confidence weight [A] | Budget (₹ lakh) | Score |
|---|---:|---:|---:|---:|
| Attendance Commitment Journey | 104.0 | 0.65 | 0.30 | **225.3** |
| Verified Squad Referral Pass | 82.5 | 0.80 | 0.55 | **120.0** |
| Campus Partnership League | 96.25 | 0.75 | 0.80 | **90.2** |
| Intent Recovery Engine | 55.0 | 0.50 | 0.35 | **78.6** |
| Creator/Paid Retargeting Rebuild | 41.25 | 0.35 | 0.35 | **41.3** |

The confidence weights reflect the quality of historical channel evidence and the novelty of the proposed tactic. For example, referrals have a strong historical baseline but the squad-pass mechanic is new; paid/creator receives a lower weight because its observed cost per attendee was highest. The score is a prioritisation aid, not a promise of causal lift. The attendance-commitment contribution includes both the modest confirmation-rate improvement and the show-rate improvement; it must not be added twice elsewhere.

### 6.2 The five initiatives

| Priority | Initiative | Historical evidence | Base / stretch registration contribution [A] | Budget cap | Owner and window | Decision |
|---|---|---|---:|---:|---|---|
| 1 | Attendance Commitment Journey | 2,500 confirmed registrations; 575 did not attend; registered show rate 77% | No new registrations; improves confirmation/show conversion | ₹30,000 | CRM + Event Operations; T-21 to T-0 | Double down as a measured multiplier |
| 2 | Verified Squad Referral Pass | Referrals: 275 attendees, ₹70.91 per attendee, 85.9% show | +120 / +180 registrations | ₹55,000 | Growth + Campus Partnerships; T-42 to T-7 | Double down |
| 3 | Campus Partnership League | Partnerships: 385 attendees, ₹80.52 per attendee, 91.7% show | +140 / +230 registrations | ₹80,000 | Campus Partnerships lead; T-56 to T-7 | Double down |
| 4 | Intent Recovery Engine | 700 unique page visitors did not register; 319 of them downloaded the brochure | +80 / +140 registrations | ₹35,000 | Lifecycle/CRM; T-28 to T-3 | Pilot and gate |
| 5 | Creator/Paid Retargeting Rebuild | Paid Social: ₹273.53 per attendee; Creators: ₹348.57 | +60 / +150 registrations | ₹35,000 | Performance Marketing; test T-21 to T-10, retarget T-10 to T-3 | Cap broad acquisition; test only high-intent retargeting |

**Reserve:** ₹65,000, released only to initiatives that pass scale gates and capacity checks. Total budget: ₹80k + ₹55k + ₹35k + ₹30k + ₹35k + ₹65k = ₹3,00,000.

Campus Ambassadors and Community Groups remain support channels within the partner/squad distribution system. Organic Search stays as a low-cost always-on channel. All seven historical campaigns remain visible in the product.

### 6.3 Reconciliation of contributions — no double counting

Registration-generation assumptions:

- Base: 140 + 120 + 80 + 60 = **400** additional completed registrations, taking 2,800 to 3,200.
- Stretch: 230 + 180 + 140 + 150 = **700** additional completed registrations, taking 2,800 to 3,500.

Historical registered-attendance yield is `1,925 / 2,800 = 68.75%`. This combines the historical registration-to-confirmation and confirmed-to-attendance stages.

**Base case**

1. New registrations at the historical yield: `400 × 68.75% = 275` incremental registered attendees.
2. Better conversion across the 3,200-registration cohort: `3,200 × (90% × 80% − 68.75%) = 104` additional registered attendees.
3. Keep 125 walk-ins unchanged.
4. Total: `1,925 + 275 + 104 + 125 = 2,429` unique external attendees.

The 104 conversion uplift can be decomposed into approximately 17.6 attendees from improving registration-to-confirmation from 89.3% to 90%, and 86.4 from improving confirmed-to-attended from 77% to 80%. The Attendance Commitment Journey owns this combined confirmation/show-up improvement in the planning model; do not count it again under the registration-generating initiatives.

**Stretch case**

1. New registrations at the historical yield: `700 × 68.75% = 481.25` incremental registered attendees.
2. Better conversion across the 3,500-registration cohort: `3,500 × (92% × 80% − 68.75%) = 169.75` additional registered attendees.
3. Walk-ins increase from 125 to 150: `+25`.
4. Total: `1,925 + 481.25 + 169.75 + 25 = 2,726` unique external attendees.

The 169.75 conversion uplift comprises approximately 73.1 attendees from the confirmation-rate improvement and 96.6 from the show-rate improvement.

| Contribution | Base | Stretch |
|---|---:|---:|
| Attendance Commitment Journey (confirmation/show-up uplift) | 104.0 | 169.75 |
| Squad Referral registrations at historical yield | 82.5 | 123.75 |
| Campus Partnership registrations at historical yield | 96.25 | 158.13 |
| Intent Recovery registrations at historical yield | 55.0 | 96.25 |
| Paid/Creator Retargeting registrations at historical yield | 41.25 | 103.13 |
| Additional walk-ins | 0 | 25 |
| **Increment over historical 2,050** | **379** | **676** |
| **Total unique external attendees** | **2,429** | **2,726** |

**Implementation rule:** The scenario calculator must calculate totals from stage rates. The table above is an explanatory reconciliation, not a second independent calculator. New registrations must be multiplied by historical yield, and rate uplift applied only to the scenario's total registration cohort. Never add a separate “commitment” estimate on top of a model that already includes the same show-rate improvement.

### 6.4 Experiment concepts

**1. Attendance Commitment Journey**

- Give confirmed registrants a clear QR pass, calendar add, event-day plan and opt-in reminder sequence (e.g. T-7, T-1, T-0).
- Segment by channel and suppress opted-out users.
- Randomise treatment/control to measure attendance lift; reminders alone should not be described as causal without the experiment.
- KPI: unique verified attendance among confirmed registrants; opt-out rate and QR completion as secondary signals.

**2. Verified Squad Referral Pass**

- Give each captain a unique referral/group code and one shareable registration link.
- Reward verified completed registrations and attendance, not raw invitations or unverified email entries.
- Use student ID/partner verification plus OTP where suitable; do not assume every Indian student has a `.edu` email.
- KPI: captain activation, verified invite-to-registration conversion, group size, show rate, cost per unique attendee and duplicate/fraud rate.

**3. Campus Partnership League**

- Recruit college societies and club captains; create a transparent inter-college leaderboard based on verified registrations and attendance.
- Fold ambassadors into this distribution layer rather than inventing a second competing attribution system.
- KPI: partner activation, registrations per partner, confirmed-to-attended rate and cost per attributed unique attendee.

**4. Intent Recovery Engine**

- Build audiences from the 425 page visitors who never started registration and the 275 who started but did not finish; use the 319 brochure-only people as a high-intent subset, not an additive cohort.
- Use only permitted/consented contact channels. Respect the 229 opt-out actors.
- KPI: recovered completed registrations / eligible non-registrants; incremental cost per recovered registration; opt-out/complaint rate.

**5. Creator/Paid Retargeting Rebuild**

- Stop broad paid-social spend as the default growth engine.
- Keep a small capped test for high-intent retargeting, campus-specific creative and creator links with UTMs.
- Evaluate verified attendees rather than views, clicks or low-quality registrations.
- KPI: cost per unique verified attendee, show rate, local/college-audience quality and verified registration rate.

### 6.5 Scale / change / stop guardrails

These are initial planning rules [A]; keep them editable.

| Initiative | SCALE | CHANGE | STOP / PAUSE | Minimum evidence gate |
|---|---|---|---|---|
| Attendance Commitment | Show rate reaches ≥80% and randomised treatment uplift is positive with a usable confidence interval | Positive but uncertain uplift; adjust message/timing | No uplift or opt-out rate worsens materially | Aim for ≥500 people per arm; below this label directional/insufficient |
| Squad Referrals | Cost per attendee ≤₹90 and show rate ≥80% | ₹90–₹130 or show 70–80% | >₹130 after sufficient outcomes | At least 50 verified attendees and 100 completed registrations |
| Campus Partnerships | Cost per attendee ≤₹100 and show rate ≥85% | ₹100–₹140 or partner activation weak | >₹140 after sufficient outcomes | At least 50 verified attendees and 100 completed registrations; review partner mix |
| Intent Recovery | ≥15% of eligible non-registrants convert | 5–15% | <5% after adequate reach | At least 200 eligible non-registrants; remove opted-out users |
| Paid/Creator Retargeting | Cost per attendee ≤₹150 and show rate ≥70% | ₹150–₹220 | >₹220 after enough spend/outcomes | At least ₹20k spend or 150 clicks plus 30 verified attendees; otherwise insufficient |

Do not force a Scale/Stop label when the sample gate is not met. The correct state is **Insufficient data**.

### 6.6 Budget reserve release

Keep ₹65,000 uncommitted at launch. Release in ₹10,000–₹15,000 tranches only when:

1. The initiative has passed its minimum sample gate.
2. Its cost/show-rate rule is in SCALE.
3. It has a named owner and a measurable next action.
4. Capacity headroom exists for the relevant event day.
5. The move is approved by a user and logged.

---

## 7. Three-slide strategy architecture

### Slide 1 — “Move unique verified attendance from 2,050 to 2,429 base / 2,726 stretch within ₹3 lakh”

- Header: candidate name, Challenge A, Bengaluru, two-day event and ₹3 lakh cap.
- Left: audience segments and partner-universe strategy. Do not invent student TAM; clearly tag sizing assumptions.
- Centre: historical → base → stretch funnel with walk-ins shown separately.
- Right: unique external attendees, cost per attendee, target attainment and capacity risk.
- Footer: evidence tags [D]/[C]/[A]/[S], city-source note and top risks.

### Slide 2 — “Shift spend from weak broad acquisition to verified partner, referral and attendance conversion”

- Five ranked initiative rows.
- Include one-line concept, historical evidence, incremental registrations or attendance contribution, budget cap, owner, timeline, test and KPI.
- Show ₹3 lakh allocation and ₹65k reserve.
- Explicitly state: stop/cap broad paid social and creator acquisition unless retargeting tests meet cost-per-attendee gates.
- Prioritisation formula: confidence-weighted incremental unique attendees per ₹ lakh, with dependency/time-to-signal review.

### Slide 3 — “Use leading signals and controlled tests to reallocate before attendance is lost”

- Main table: critical variable, early signal, scale/change/stop thresholds, minimum sample, action.
- Add the historical registration pacing curve and the decision checkpoints.
- Bottom workflow: Live data → Copilot diagnosis → user-confirmed task/budget action → refreshed analytics.
- Include at least one example of an insufficient-data answer.

Historical cumulative registration pacing curve (registrations observed by each T-minus date):

| Checkpoint | T-56 | T-42 | T-28 | T-14 | T-7 | T-0 |
|---|---:|---:|---:|---:|---:|---:|
| Historical cumulative share | 21.0% | 40.9% | 55.8% | 80.1% | 92.2% | 100% |

Use this curve as the initial pacing reference because it comes from the actual synthetic history. Recalculate it when a new event dataset is loaded.

---

## 8. Growth Center product architecture

### 8.1 Logical architecture

```text
Uploaded XLSX / CSV
       |
       v
Ingestion + validation + stable-ID deduplication
       |
       +------------------------------+
       |                              |
       v                              v
Immutable original tables       Editable working tables
       |                              |
       |                              v
       |                     Analytics / metrics engine
       |                              |
       |                              v
       |                     Growth rules + scenario engine
       |                              |
       +------------------------------+
                                      |
                        +-------------+-------------+
                        |                           |
                        v                           v
                 Dashboard UI                Typed tool/API layer
                        |                           |
                        |                           v
                        |                   LLM Growth Analyst
                        |                           |
                        +<------ shared live data--+
                                    |
                                    v
                         Draft action / confirmation
                                    |
                                    v
                         Transactional write + audit log
                                    |
                                    v
                         Recompute and refresh UI/chat
```

### 8.2 Recommended build stack

- UI: Streamlit multi-page app with Plotly charts.
- Analytics/business logic: Python modules; use SQL for joins and aggregations where practical.
- Local development store: SQLite.
- Shared/deployed persistence: PostgreSQL (e.g. Supabase) behind the same repository/data-access interface.
- AI: any available LLM API with reliable tool/function calling; keep the provider behind an adapter.
- Validation: Pydantic schemas for tool arguments and action payloads.
- Tests: pytest for analytics, data quality, rule boundaries and action workflows.

Streamlit is appropriate for a first implementation because the project is Python-heavy and benefits from a short build cycle. Avoid authentication and multi-role permission work for the single-workspace demo.

### 8.3 Data layers

**A. Immutable source tables**

Load the workbook sheets into read-only `original_*` tables. Preserve source rows exactly, including duplicate import copies, so the original remains testable.

**B. Editable working tables**

Create a working copy of the source data. All dashboard and chatbot analytics read from this working copy. User edits affect the working copy; a reset operation restores it from the immutable original.

**C. Operational application tables**

- `campaign_plan`: editable owner, planned budget, status and notes.
- `scenario_inputs`: event targets, budget cap, event dates, day-level capacity and day-mix assumptions.
- `growth_initiatives`: the five bets, their owner, scope, budget and status.
- `experiment_rules`: scale/change/stop thresholds, sample gates and measurement windows.
- `tasks`: task, owner, due date, campaign/initiative, status, origin and linked insight.
- `budget_moves`: source, destination, amount, reason, approver and status.
- `audit_log`: actor, timestamp, before/after values and reason.
- `chat_sessions` and `chat_messages`: conversation/testing trace, excluding unnecessary personal data.

**D. Derived analytics**

Compute metrics from working tables on request. Do not manually persist or hardcode dashboard numbers. If caching is added later, invalidate it on every data, target, rule or constraint change.

### 8.4 Core analytics definitions

- Unique external attendee: distinct `person_id` with at least one admitted-and-verified check-in during the selected event window and person type `external`.
- Registered external attendee: the unique external attendee joined to a valid `registration_id`.
- Walk-in: valid external attendee without a registration ID.
- Registered show rate: registered external attendees / distinct external confirmed registrations at the selected as-of date.
- Campaign cost per attendee: campaign net spend through the selected date / unique verified external attendees attributed to the recorded registration campaign.
- Blended cost per attendee: total relevant campaign spend / all unique external attendees, including walk-ins.
- Registration status: latest eligible history version per registration ID as of selected date.
- Unique visitor-days: distinct external person/date combinations with valid admission.
- Anonymous traffic funnel: impressions → clicks → landing sessions → registration-start events. These are events, not unique people.
- Identified funnel: unique page visitors → unique registration starters → completed external registrations → confirmed registrations → registered attendees. Walk-ins are shown as a separate route into attendance.

### 8.5 Core screens

**1. Command Center**

- Unique external attendees vs base/stretch target.
- Registration and show-rate progress.
- Blended cost per attendee, spend, available budget and reserve.
- Top campaign winners/risks.
- Capacity/day-mix warning and next decision checkpoint.
- Top three action alerts.

**2. Funnel & Audience Intent**

- Separate anonymous traffic and identified person funnels.
- Filter by campaign, source, date and status.
- Show 425 no-start page visitors, 275 incomplete starters and 319 brochure-download non-registrants with overlap handled by person ID.
- Engagement and nurture cohort views; opted-out suppression.

**3. Campaigns**

- All seven historical campaigns and all new initiatives.
- Spend, clicks, session events, identified people, registrations, confirmations, unique attendees, show rate and cost per attendee.
- Source labels and warning that attributed performance is not causal incrementality.
- Editable budget, owner, active status and notes.

**4. Experiments & Scenario Lab**

- Five initiatives with sample size, leading indicator and automatic status.
- Editable thresholds, sample gates and scenario assumptions.
- Budget allocation slider/table and live projected attendance.
- Capacity/day-slot simulation and sensitivity checks.

**5. Actions & Decision Log**

- Persistent task board with owner, due date, status and linked initiative.
- Proposed/approved budget moves.
- Before/after audit history and why a decision was made.

**6. Copilot panel**

- Persistent conversational panel available from every page.
- Source references, calculation explanations, evidence tags and caveats.
- Draft action cards with Confirm / Cancel.

**7. Data & Settings (supporting screen)**

- Dataset version, import status, duplicate-ID summary and data coverage.
- Original vs working data and reset control.
- Event date, timezone, target versions, assumptions and daily capacity settings.

### 8.6 Copilot architecture — tool calling, not fine-tuning

Do not fine-tune a model on the workbook for the first version. The values change and the grader may edit them. Fine-tuning would not keep numeric knowledge current.

Build a tool-connected assistant instead:

1. Give the LLM the field guide, domain definitions, evidence labels and tool schemas.
2. The LLM chooses a typed tool based on the user question.
3. Python/SQL reads the current working database and performs calculations.
4. The tool returns structured values, denominators, date scope, provenance and caveats.
5. The LLM explains the result and recommends a next step.
6. For any write, the tool creates a draft; the user explicitly confirms before the database transaction.

Optional retrieval can be used for text-only documents such as the field guide, campaign descriptions or README sources. Do not use vector search/RAG as the numeric analytics engine.

### 8.7 Initial typed tool set

| Tool | Responsibility |
|---|---|
| `get_overview(filters)` | Current north-star metrics, target progress and alerts |
| `get_funnel(filters)` | Stage counts, conversion rates and denominators |
| `get_campaign_performance(filters)` | Campaign ranking, spend and attributed unique attendees |
| `get_campaign_detail(campaign_id, period)` | Funnel and driver detail for one campaign |
| `get_intent_cohorts(filters)` | Drop-offs, brochure intent and nurture engagement |
| `get_attendance_detail(filters)` | Verified attendees, walk-ins, visitor-days and arrival peaks |
| `get_budget_status()` | Actual spend, budget ceiling, reserve and available amount |
| `get_capacity_risk(scenario)` | Day-level visitor-day demand versus editable cap |
| `get_rules_and_status()` | Current rules, minimum samples and campaign status |
| `project_scenario(inputs)` | Deterministic base/stretch or what-if projection |
| `get_data_coverage()` | Available and unavailable fields; supports cannot-answer behaviour |
| `get_provenance(metric)` | Source tables, date range, formula and evidence tag |
| `propose_budget_move(args)` | Draft a budget move; does not save |
| `propose_task(args)` | Draft a task; does not save |
| `commit_approved_action(action_id)` | Commit a previously reviewed action and write audit entry |

Never expose arbitrary SQL execution or direct filesystem/database access to the LLM.

### 8.8 Standard answer contract

Every numerical answer should contain:

1. Direct answer.
2. Metric definition and denominator.
3. Period/as-of date and filters.
4. Source tables and evidence tag `[D]`, `[C]`, `[A]` or `[S]`.
5. Interpretation and suggested action if asked.
6. Sample-size or coverage caveat.

### 8.9 Cannot-answer behaviour

The assistant must clearly decline to infer:

- Satisfaction/NPS without a survey.
- Unique all-time reach from summed platform reach.
- Causal campaign lift without a controlled test.
- College, age or geographic demographics not present in the workbook.
- Actual venue capacity before it is supplied.
- Weather/travel effects without those fields.

It should identify the missing field and suggest the closest valid proxy or the data needed to answer.

### 8.10 A staged chatbot build — learn before adding complexity

**Version 1: read-only Growth Analyst**

- Six tools only: `get_overview`, `get_funnel`, `get_campaign_performance`, `get_budget_status`, `project_scenario` and `get_data_coverage`.
- No write tools, no fine-tuning and no open-ended database access.
- Test exact counts, denominators, filters, date handling and cannot-answer behaviour.

**Version 2: diagnostic analyst**

- Add intent cohorts, campaign detail, attendance detail, rules/status and provenance tools.
- Teach the assistant to compare channels, locate the bottleneck and explain a result with evidence labels.
- Add a small benchmark set with expected numerical outputs and expected abstentions.

**Version 3: action copilot**

- Add `propose_task` and `propose_budget_move` as draft-only actions.
- Show the before/after impact and ask the user to confirm.
- Only then allow `commit_approved_action`, with database transaction and audit record.

**Version 4: improve from observed failures**

- Classify test failures as data/metric bug, tool-selection error, reasoning/prompt error, missing coverage or UI/action-state bug.
- Fix deterministic data and metric bugs in Python/SQL first; update tool schemas and system instructions for routing/format failures.
- Consider model/provider changes only after measuring the same evaluation set.
- Fine-tuning is not a first-version requirement. The workbook changes, so live tool access is more important than embedding its current values in model weights.

### 8.11 Human approval and persistence

For a task or budget move:

1. Assistant calls a `propose_*` tool.
2. UI displays the exact before/after values, reason, affected initiative and expected impact.
3. User clicks Confirm or Cancel.
4. Confirm commits one database transaction, creates an audit record and updates operational tables.
5. Analytics recalculate from the updated working state.
6. The next chatbot turn calls tools again; it does not trust stale conversation numbers.

---

## 9. Chatbot demo workflow

**Question 1:** “Why is Paid Social underperforming?”

Expected tool sequence: `get_campaign_detail(C02)`, `get_rules_and_status()`, `get_provenance()`.

Expected grounded diagnosis: Paid Social has ₹93,000 spend, 680 external registrations, 580 confirmed registrations and 340 unique verified external attendees; cost per attributed attendee is ₹273.53 and confirmed-to-attended is 58.6%. Compare with College Partnerships at ₹80.52 and 91.7%. State that this is recorded attribution, not causal proof. Recommend pausing broad acquisition and testing only high-intent retargeting.

**Question 2:** “What if we move ₹15,000 from broad paid acquisition to Student Referrals?”

Expected tool sequence: `get_budget_status()`, `project_scenario()`, `propose_budget_move()`.

The assistant must use the current editable model and diminishing-return assumptions, show the calculation and caveat, then wait for approval.

**Question 3:** “Create a task to launch the referral pilot next week.”

Expected tool sequence: `propose_task()` then explicit confirmation. After confirmation, the task appears on Actions and the audit log.

**Follow-up:** “What was attendee satisfaction?”

Expected answer: the workbook has no satisfaction survey; cannot answer. Offer a post-event survey as a way to collect it next time.

---

## 10. Chatbot and product test suite

Build a small in-app evaluation page with deterministic expected values from the original workbook. Suggested tests:

1. How many unique external attendees were there? → 2,050.
2. How many external registrations were created? → 2,800.
3. How many external registrations were confirmed at event close? → 2,500.
4. What is the registered show rate? → 77.0% (1,925 / 2,500).
5. How many walk-ins were there? → 125.
6. Which campaign has the lowest cost per attributed attendee? → Student Referrals, about ₹70.91.
7. Which campaign has the highest cost per attendee? → Creator Partners, about ₹348.57.
8. Compare Paid Social with College Partnerships → ₹273.53 vs ₹80.52, show rate 58.6% vs 91.7%.
9. How many page visitors did not register? → 700 unique people.
10. How many of those downloaded the brochure? → 319; warn this is a subset, not additive.
11. How many people attended both days? → 725.
12. What was total unique visitor-days? → 2,775.
13. Why are there more admission events than unique visitors? → Repeated admissions and multiple person types; count unique external person IDs for north-star attendance.
14. Is unique platform reach 666,297? → No; this is a sum of daily reported reach values, not cross-day unique people.
15. What was attendee satisfaction? → Cannot answer; no survey field.
16. Did Paid Social cause the increase in registrations? → Cannot establish causality from observational data.
17. What happens if the daily cap is changed from 1,800 to 2,000? → Recompute capacity warnings.
18. Edit a campaign spend value; repeat its cost question → answer must change.
19. Change a registration status; repeat confirmed/show-rate question → answer must change.
20. Change a check-in to denied or unverified; attendee count must update.
21. Add a duplicate `event_id`; it must not increase unique attendee count.
22. Change the target version; target progress must update.
23. Ask for the source of a number → return table, time window and formula.
24. Ask to move budget; no write before Confirm.
25. Reset the working dataset → restore original values and log the reset.

Test both numerical correctness and the wording of uncertainty. Do not pass a chatbot test merely because its answer sounds plausible.

---

## 11. Build sequence

### Phase 0 — Data ingestion and validation (first)

- Read the workbook sheets.
- Preserve original source rows.
- Create working copies.
- Validate required columns and foreign keys.
- Deduplicate by stable IDs in analytical views.
- Implement as-of registration status and verified external attendance.
- Write unit tests for the 2,050 attendee baseline and all funnel denominators.

**Gate:** no UI or chatbot work proceeds until the baseline metrics reconcile.

### Phase 1 — Deterministic analytics engine

- Campaign metrics and campaign comparison.
- Funnel and intent cohorts.
- Budget status and scenario calculator.
- Capacity/day-mix calculator.
- Pacing curve and rule-based statuses.
- Provenance and data-coverage functions.

### Phase 2 — Dashboard and management functions

- Build Command Center, Funnel, Campaigns, Experiments/Scenario Lab, Actions/Audit and Data Settings.
- Add editable working data, target/rule settings and reset-to-original.
- Verify that edits update every relevant chart and KPI.

### Phase 3 — Basic AI Growth Analyst

Start with six tools: overview, funnel, campaign comparison, budget status, scenario projection and data coverage. Add the field guide and answer contract. Test 10 grounded and 5 cannot-answer questions.

### Phase 4 — Diagnosis and execution

- Add intent cohorts, campaign decomposition and recommendation rules.
- Add draft task and budget-move tools.
- Add confirmation, transactional writes and audit log.
- Add the complete demo workflow.

### Phase 5 — Deployment and evaluation

- Use persistent PostgreSQL/Supabase for the shared deployed demo.
- Keep local SQLite for offline development and unit tests.
- Store API keys in deployment secrets, never in source code.
- Run the 25-question test suite after every data or prompt change.
- Record model/provider/version and tool outputs for reproducibility.

---

## 12. Definition of done against the rubric

| Rubric | Evidence in the finished project |
|---|---|
| 20% Quantitative reasoning | Reconciled historical funnel; base/stretch; cost per attendee; capacity and sensitivity |
| 20% Creativity and tradeoffs | Five distinct bets, scoring method, budget split, reserve and explicit deprioritisation |
| 15% Experimentation | Leading indicators, thresholds, sample gates, pacing curve and next actions |
| 20% Dashboard/management | Live metrics, editable campaigns/targets, persistent tasks, budget moves and audit history |
| 20% AI utility | Live tool calls, reliable calculations, diagnosis, follow-up, cannot-answer and confirmed actions |
| 5% Ownership | README, source links, assumptions, setup, test results, limitations and tool/provider disclosure |

### Non-goals for the first version

- No model fine-tuning.
- No RAG over raw CSV/XLSX as the numeric calculation layer.
- No direct LLM SQL or arbitrary code execution.
- No automatic writes without user approval.
- No authentication/roles for a single-workspace demo.
- No paid advertising, payment or WhatsApp integration requirement.
- No native mobile app, voice or decorative animation work.

**Final build priority:** make the source data and analytics trustworthy first; make the dashboard useful second; connect the chatbot third; add action execution only after the first three are reliable.
