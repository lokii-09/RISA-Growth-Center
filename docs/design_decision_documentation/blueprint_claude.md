# RISA Growth APM Assignment: Design Blueprint (v1, pre-build)

**Scope of this document:** every design decision for the 3 slides and the Growth Center product, each with a defence. **No code.** Written so that each section can be lifted straight onto a slide or into the final submission README.

---

## 0. Read this first

### 0.1 What I could not verify
The PDF only says "Attached" for the Challenge A and B datasets. The **datasets themselves were not in the upload**, so I have not seen their columns, scale or time range. Consequences:

- Every number in this blueprint that is not externally sourced is tagged **[A] assumption**.
- Before building, you must open the dataset and run the **Calibration Step (§9, step 1)**. Several numbers below (home-campus size, historical attendance, channel conversion rates) should be *replaced by dataset values*. The model is built so that this is a swap, not a redesign.
- The chatbot "will be tested on the dataset you choose" (their words), so the dataset's real columns become the chatbot's source of truth. This is why the product design (§7) is dataset-agnostic.

### 0.2 Tag legend (use this on slides too, since the brief says "clearly distinguish sourced facts from assumptions")

| Tag | Meaning |
|---|---|
| **[S]** | Sourced from an external source (listed in §11) |
| **[A]** | My assumption, to be tested or replaced |
| **[D]** | To be filled from the provided dataset |
| **[C]** | Calculated from the above |

### 0.3 Priority legend (applied to every decision)

| Tag | Meaning |
|---|---|
| **MUST** | Directly scored, or the product breaks without it |
| **SHOULD** | Clear scoring upside, modest cost |
| **MIGHT** | Only if time remains after all MUST and SHOULD items |
| **AVOID** | Looks impressive, but costs time or hurts the score. Reasons given. |

---

## 1. Decoding the brief: what is actually scored

| Weight | What they score | What it forces in my design |
|---|---|---|
| 20% | Ambition and quantitative reasoning | A funnel model with base and stretch cases, sourced benchmarks, and arithmetic that ties out exactly |
| 20% | Ideas, prioritisation, tradeoffs | Five *distinct* ideas, a stated framework, explicit rejects |
| 15% | Experimentation and adaptability | Per-idea scale/change/stop thresholds based on leading indicators, with minimum sample sizes |
| 20% | Dashboard and management | One source of truth. Editing data must recompute analytics. Saved changes. Insight-to-action loop |
| 20% | Embedded chatbot | Answers from live data, correct calculations, honest "can't answer", confirm-before-write actions |
| 5% | Ownership, communication | This README, kept honest about limitations |

**Four hidden tests in the brief (design for all of them):**

1. *"We may test your product by changing campaign data or constraints and asking you to respond."* Everything derived (funnel, statuses, projections, chatbot answers) must recompute from the raw tables. No hardcoded numbers or cached text.
2. *"Unfamiliar questions, changed data, calculations, and when to say the data cannot answer."* This needs a tool-calling chatbot with deterministic maths and an explicit data-coverage check (§7.5).
3. *"A polished UI or large projected number alone will not earn a high score."* Spend effort on logic, not visuals.
4. *"Keep the original data available for chatbot testing."* Keep the raw data immutable, with a **Reset to original** control.

---

## 2. Foundational decisions

### 2.1 Challenge: choose **A (Attendee Growth)**: **MUST decide, with a data-driven override**

| Why A | Evidence/logic |
|---|---|
| The funnel has **volume**, so thresholds are statistically meaningful | Sponsorship has maybe 40 to 60 prospects and 5 to 10 deals. Scale/stop rules on n=8 are noise. Attendee funnels have thousands of events, so a "stop if CPA > X after n=150 clicks" rule is defensible |
| It supports **multiple parallel campaigns**, which makes the dashboard and chatbot richer | Channel-level diagnosis ("which campaign is the bottleneck?") needs many campaigns |
| Faster feedback loops (days, not months) | Better demo of "adapt before it's too late" |
| Sponsorship cash has structural lags (contracts, invoices, GST, payment terms) | Pre-festival cash collected is outside your control. Attendee registrations are not |

**Counter-case (be honest in the README):** sponsorship is more *differentiated* since fewer candidates will pick it. Real deal data exists (Amity UNIFEST tiers ₹25L to ₹50L **[S]**; Techfest sponsorship ₹1.58 crore **[S]**). It wins only if the Challenge B dataset has a deal-level pipeline with stage dates and the A dataset is thin.

**Override rule (decide in 15 minutes once you open both files):** Choose A if its dataset has campaign-level rows (channel, spend, registrations, attendance). Choose B only if A is just aggregate totals and B has stage-dated deals.

### 2.2 City: **Bengaluru**: **MUST decide**

| Reason | Tag |
|---|---|
| Bengaluru Urban has the **most colleges of any district in India** (1,148 per AISHE 2023-24) | **[S]** |
| Dense, multi-college geography means group and ambassador mechanics work. Peer fests already draw cross-college crowds (e.g. Esplendida ~15,000 from colleges across Bangalore, an older figure) | **[S]** |
| Meta ad costs in India are low (Instagram ₹45 to ₹350 CPM, ₹6 to ₹55 CPC) | **[S]** |
| Large tech-adjacent young-professional base gives a secondary audience | **[A]** |
| Risk: traffic and commute friction. Mitigation: choose a metro-accessible venue, include "getting there" in comms | **[A]** |

**Alternatives rejected:** *Delhi* (strong fest circuit but fragmented NCR geography, longer commutes, harder to build ambassador density). *Mumbai* (Mood Indigo's gravity is anchored to one campus brand, and venue costs and distances are larger). The justification must be **one line on Slide 1**. Do not spend more space on it.

### 2.3 Festival profile (assumed; **[D]** will override)

| Parameter | Value | Tag |
|---|---|---|
| Duration | 3 days | **[A]** |
| Growth budget (marketing only, excludes artists/ops) | **₹6.5 lakh** base | **[A]** |
| Campaign window | 8 weeks (T-56 to T-0) | **[A]** |
| Home-campus student pool | 8,000 | **[D]/[A]** |
| Max safe gate entries per day | 15,000 | **[A]** |
| Gate throughput | 10 lanes × 10 scans/min = 6,000/hr | **[A]** |
| Average days attended per attendee | 1.6 | **[A]** |
| Day split of visits | 25% / 40% / 35% | **[A]** |

### 2.4 Definitions (put these in the README and the dashboard; graders probe them)

- **Attendee** = unique person with a **gate scan on at least one day** (not a registration, not a ticket).
- **North-star metric** = unique scanned attendees.
- **Show rate** = scanned attendees ÷ registrations (per channel).
- **Cost per attendee** = channel spend ÷ scanned attendees (not cost per registration. The brief says "people who actually attend").
- **Attribution rule:** last-touch code. A registrant with a squad code counts under Squads only, never twice. Overlap is further discounted by a 10% haircut **[A]**.

---

## 3. SLIDE 1: "How high can you aim?"

### 3.1 Audience segments (priority-ranked)

| # | Segment | Size | Why / why not | Priority |
|---|---|---|---|---|
| P1 | Home-campus students | 8,000 **[D]/[A]** | Owned reach, near-zero cost, highest show rate. This is the **floor**, not a growth idea | **MUST** |
| P2 | Peer-college students (top ~60 colleges) | ~120,000 **[A]** (60 × ~2,000) | The core growth pool. Reached via ambassadors and group passes | **MUST** |
| P3 | Competition participants and their supporters | 2,000 to 3,500 participants **[A]** | Participants are pre-committed (fee paid) and bring friends | **MUST** |
| P4 | Social-discovery youth (18 to 24, Instagram) | ~290k unique paid reach in base **[C]** | Scalable but the most expensive per attendee | **SHOULD** |
| P5 | Young professionals and alumni | Unsized | Low volume, high CAC, needs a different offer (pro-night tickets) | **MIGHT** |
| P6 | School and PU students | Unsized | **Minors**: safeguarding, consent, insurance. Not worth the risk | **AVOID** |

### 3.2 Base-case funnel (reach → registration → attendee)

Formulas: Attendees = Registrations × Show rate. Cost per attendee = Spend ÷ Attendees.

| Channel | How regs are generated | Regs | Show rate | Attendees | Spend | ₹/attendee |
|---|---|---|---|---|---|---|
| A. Home campus (owned) | 8,000 reached × 55% register | 4,400 | 85% | 3,740 | ₹0.4L | ₹11 |
| B1. Ambassadors | 300 ambassadors × 30% active × 40 regs | 3,600 | 75% | 2,700 | ₹0.9L | ₹33 |
| B2. Squad passes | 220 groups × 14 members | 3,080 | 85% | 2,618 | ₹0.5L | ₹19 |
| C. Creators + paid social | ₹1.3L paid / ₹150 CPM = 867k impr.; ~289k unique reach at freq 3; CTR 1.2% → 10,400 clicks; 18% landing→reg = 1,872. Plus 1,000 from creators | 2,872 | 72% | 2,068 | ₹1.8L | ₹87 |
| D. Competitions | 2,000 participants + 0.6 supporters each (1,200) | 3,200 | 85.5% | 2,736 | ₹0.6L | ₹22 |
| Commitment engine (tools) | Lifts show rates across the above | n/a | n/a | included | ₹0.4L | n/a |
| **Subtotal** | | **17,152** | **80.8%** | **13,862** | **₹4.6L** | |
| Overlap haircut (−10%) | Same person reached by 2+ channels | | | −1,386 | | |
| **BASE CASE** | | | | **≈ 12,500** | ₹4.6L deployed, ₹1.9L held in reserve (total ₹6.5L) | **₹37** per attendee on deployed spend |

### 3.3 Stretch case (what you must earn through gates, §5)

| Channel | Assumption change | Regs | Show rate | Attendees | Spend |
|---|---|---|---|---|---|
| A. Home campus | 70% register | 5,600 | 90% | 5,040 | ₹0.5L |
| B1. Ambassadors | 500 ambassadors × 40% active × 50 regs | 10,000 | 78% | 7,800 | ₹1.5L |
| B2. Squad passes | 400 groups × 15 | 6,000 | 88% | 5,280 | ₹0.9L |
| C. Creators + paid | ₹3.0L paid at ₹130 CPM = 2.31M impr.; CTR 1.5% → 34,615 clicks; 22% → 7,615 regs; +3,000 creator regs | 10,615 | 75% | 7,961 | ₹3.8L |
| D. Competitions | 3,500 participants + 0.8 supporters (2,800) | 6,300 | 85.6% | 5,390 | ₹1.0L |
| Tools | | n/a | n/a | n/a | ₹0.4L |
| **Subtotal** | | **38,515** | **81.7%** | **31,471** | **₹8.1L** |
| Overlap haircut (−10%) | | | | −3,147 | |
| **STRETCH** | | | | **≈ 28,300** | ₹8.1L (₹8.6L incl. ₹0.5L reserve) → **₹29** per attendee |

**How the stretch is funded [A]:** the extra ₹2.1L over the ₹6.5L base comes from competition-fee and pass revenue recycled into marketing. Competition fees alone (3,500 × ~₹150) exceed this. State this explicitly, because a stretch that needs money you don't have is not credible.

### 3.4 Capacity constraint (this is the binding constraint for the stretch, and the least obvious one)

| Case | Unique | × 1.6 days | Visits | Peak day (40%) | vs 15,000/day cap |
|---|---|---|---|---|---|
| Base | 12,476 | | 19,962 | 7,985 | Fits (53% of cap) |
| Stretch | 28,324 | | 45,318 | **18,127** | **Exceeds cap by ~3,100** |

**Design response:** day-slotted passes with a lower price on Day 1 and Day 3, and a capacity-aware release (§5.4). Gate throughput (6,000/hr) is not the constraint. The daily entry cap is. This one table shows evaluators you modelled *capacity*, which the brief explicitly asks for.

### 3.5 Why believe the number: triangulation

| Benchmark | Figure | Tag |
|---|---|---|
| Pragyan (NIT Trichy) | ~15,000 footfall | **[S]** |
| Saarang (IIT Madras) 2024 | ~80,000 expected | **[S]** |
| Mood Indigo (IIT Bombay) 2022 | 150,000+ | **[S]** |
| Techfest (IIT Bombay) | 180,000+ | **[S]** |
| **This plan:** base 12,500 / stretch 28,300 | Stretch sits between a strong mid-tier fest and the IIT-tier flagships. Aggressive, not absurd | **[C]** |

**Honest check to state on the slide:** stretch implies converting roughly 1 in 5 of the ~120k addressable peer-college students. Squads and competitions carry that conversion because they are pre-committed. If squad conversion halves, we fall to about 22,000 (see 3.6). The dashboard exists to catch that early.

### 3.6 Sensitivity (the "critical variables" for Slide 3)

| Variable moved (base case) | Attendee change | % of base |
|---|---|---|
| Show rate −8 pts across all channels | ≈ −1,240 | −10% |
| Squad conversion halved (110 groups) | ≈ −1,180 | −9% |
| Ambassador activation 30% → 20% | ≈ −810 | −6% |
| Paid cost per registration doubles | ≈ −610 | −5% |
| **Combined downside** | **≈ 8,500 to 9,000** | **−30%** |

Insight to put on slide: **attendance, not registration, is the leakiest step**, which is why a commitment mechanic is in the top 3.

### 3.7 Slide 1 layout (**MUST**)

- **Top bar:** title, **your name**, one-line city choice and challenge choice.
- **Left (55%):** the funnel as a visual waterfall from reach to registrations to attendees, with both cases side by side. Do not paste the whole 3.2 table. Show channel totals only.
- **Right (45%):** three big numbers: **Base 12,500 | Stretch 28,300 | Floor (downside) ~8,500**. Underneath: "Why believe it": three sourced benchmark lines, one capacity line.
- **Bottom strip:** assumption confidence key (S/A/D), and "top 2 risks: show rate, squad conversion".
- **Defence of density:** the brief grades "evidence-based assumptions" and "accurate calculations." A slide with fewer numbers loses points. A slide with unlabeled numbers also loses points. Label everything.

---

## 4. SLIDE 2: "Where will you place your bets?"

### 4.1 Prioritisation framework: **Confidence-weighted attendees per ₹ lakh**, with an overlap and dependency check **MUST**

**Score = (incremental attendees after 10% overlap haircut × confidence) ÷ cost in ₹ lakh.**

Why this, not a generic RICE or ICE: the brief weighs "limited resources." Attendees per rupee is the exact tradeoff. Confidence is explicit so a "great-looking but unproven" idea is penalised. Then I overlay two qualitative checks (dependency, time to first signal) so the ranking is not blindly mechanical.

| # | Idea | Attendees (×0.9) | Cost | Confidence | **Score** |
|---|---|---|---|---|---|
| 1 | Squad passes | 2,356 | ₹0.5L | 0.60 | **2,827** |
| 2 | Competition-led supporter funnel | 2,462 | ₹0.6L | 0.65 | **2,667** |
| 3 | Commitment engine | 1,362 (show-rate lift 72%→80.8% on 17,152 regs) | ₹0.4L | 0.70 | **2,384** |
| 4 | Campus ambassador network | 2,430 | ₹0.9L | 0.60 | **1,620** |
| 5 | Creators + paid social (Reels-first) | 1,861 | ₹1.8L | 0.50 | **517** |

> **Rank ≠ spend.** Idea 5 ranks last by efficiency but takes the largest single budget line (₹1.8L = 39% of deployed spend, 28% of ₹6.5L). Defence: it is the only channel with no organic ceiling and it supplies awareness that ideas 1, 2 and 4 depend on (lineup reveals). So it is **capped**, and extra money goes only to channels that pass gates (§5.4). This is a deliberate tradeoff you should say out loud, because the brief asks "which ideas would you double down on?" and the honest answer is ideas 1 to 3.

### 4.2 The five ideas

**Idea 1: Squad passes (DOUBLE DOWN)**
- *Concept:* a captain buys for 10+ friends in one link and gets a discount (e.g. 15%) **[A]** and a captain perk. Prepaid group purchase creates a financial and social commitment.
- *Why it works:* pre-payment is the strongest known no-show reducer (paid events ~17% no-show vs ~28% free **[S]**), and groups pull in people who would never register individually.
- *Contribution:* base ≈ 2,360 attendees; stretch ≈ 4,750.
- *Budget / timeline:* ₹0.5L discount cost; outreach T-42 → T-7.
- *Test:* 3 offer variants across 3 colleges, 30+ captain contacts each. *KPIs:* captain contact→quote→paid conversion, average group size, payment completion, squad show rate.

**Idea 2: Competition-led supporter funnel (DOUBLE DOWN)**
- *Concept:* online qualifiers (T-42 → T-14) with a small entry fee; every participant gets a shareable "support me" pass.
- *Why it works:* participants are paid and committed (assumed ~90% show), and bring supporters (0.6 per participant base, 0.8 stretch **[A]**).
- *Contribution:* base ≈ 2,460; stretch ≈ 4,850.
- *Budget:* ₹0.6L (platform, comms, small prizes); owner: competitions team.
- *Test:* open 5 pilot events first; read team sign-ups and supporters per participant. *KPIs:* team registrations per event, fee completion, supporters per participant, show rate.

**Idea 3: Commitment engine (DOUBLE DOWN, as a multiplier)**
- *Concept:* ₹99 token pass fully redeemable as food coupons **[A]**, three-step reminders (T-7, T-1, T-0), a "confirm my seat" click, waitlist when a day sells out, and an overbook rule: **release = capacity ÷ expected show rate**.
- *Why it works:* free events lose ~28% of registrants, paid ~17% (PheedLoop, 1,070+ events **[S]**). Also, the same data shows registration *friction* alone does not predict attendance, but price does. So add commitment, not hurdles.
- *Contribution:* ≈ 1,360 additional attendees from the same registrations. Zero new reach.
- *Budget:* ₹0.4L. *Test:* 20% randomised holdout on paid traffic. *KPIs:* confirm rate at T-3, show rate by variant, registration drop from the price.

**Idea 4: Campus ambassador network (KEEP, GATED)**
- *Concept:* 5 ambassadors per college across ~60 colleges, tiered rewards (pass at 10 regs, merch at 25, backstage at 50) and a college-vs-college leaderboard.
- *Contribution:* base ≈ 2,430; stretch ≈ 6,900.
- *Budget:* ₹0.9L (≈ ₹300 per ambassador). Recruit T-56 → T-42, active T-42 → T-0.
- *Test:* pilot with 30 ambassadors; read **7-day activation**. *KPIs:* activation rate, regs per active ambassador, referral quality (show rate), fraud flags.
- *Why it is ranked 4:* highest variance (depends on motivation, not mechanics), and it overlaps with squads (attribution rule in §2.4).

**Idea 5: Creators + paid social, Reels-first (CAPPED)**
- *Concept:* lineup-drop reveal content, 12 Bengaluru micro-creators paid in passes plus a small fee, and Reels-first ads (Instagram Reels ₹45 to ₹140 CPM vs Feed ₹150 to ₹350 **[S]**).
- *Contribution:* base ≈ 1,860; stretch ≈ 7,200.
- *Budget:* ₹1.3L paid + ₹0.5L creators. *Test:* 6 creatives × ₹5k. Kill any creative at CPR > ₹100 after 150+ clicks. *KPIs:* CPM, CTR, landing→registration, cost per registration, **cost per attendee** (CPR ÷ show rate).

### 4.3 What I am explicitly NOT doing (**AVOID**; this earns "clear reasons to deprioritise")

| Rejected | Why |
|---|---|
| Celebrity headliner as a *growth* lever | Artist fees quoted at ₹20L to ₹25L **[S, 2014, dated]** exceed the entire growth budget. Headliner is a sponsorship-funded programming decision, not a growth tactic |
| Cold mass paid ads as the primary engine | Highest cost per attendee (₹87 vs ₹11 to ₹33 elsewhere) |
| Outdoor hoardings, print, radio | Not measurable per rupee, so it breaks the dashboard principle |
| Bulk SMS / cold WhatsApp blasts | DND and spam risk, brand damage. Use opt-in reminders only |
| Targeting school/PU students | Minors: safeguarding, insurance, consent |
| Cash-for-referral bounties | Fraud risk, hard to audit. Use non-cash tiered rewards |
| Building a native fest app | Cost and time with no attendance lift. Web registration is enough |
| Fully free, no-commitment registration | ~28% median no-show **[S]** and wasted capacity |
| Young-professional push (P5) | **MIGHT** later. Only if base gates are met by T-21 |

### 4.4 Slide 2 layout (**MUST**)
A ranked ladder: five rows. Columns: **Rank | Idea + one-line concept | Base → stretch contribution | Budget, owner, timeline | Test + 2 KPIs | Score**. A slim footer strip: **"Not doing:"** (top 4 rejects with 3-word reasons) and the framework formula. Do not write paragraphs.

---

## 5. SLIDE 3: "How will you know what's working?"

### 5.1 Pacing curve: the portfolio-level leading indicator (**MUST**)
Free-event registrations arrive late (median lead time 16 days for free events vs 41 days for paid; 69% of free registrations land inside 30 days **[S]**). So linear pacing would trigger false alarms. Use a back-loaded target **[A]**:

| T-minus | T-56 | T-42 | T-30 | T-14 | T-7 | T-0 |
|---|---|---|---|---|---|---|
| Cumulative % of registration target | 0% | 15% | 40% | 70% | 85% | 100% |

Alarm if cumulative registrations are more than 15% below this curve at T-30, or more than 10% below at T-14.

### 5.2 Per-idea scale / change / stop table

*Minimum sample before any decision: 150 clicks, 200 registrations, or 30 outreach contacts. Below that, the status is **"insufficient data"** and no action is triggered.* (Why: at n=200 and a 20% rate, the standard error is ~2.8 points, so smaller samples produce false calls.)

| Idea | Critical variable | Early signal (leading) | **SCALE** if | **CHANGE** if | **STOP** if | Action |
|---|---|---|---|---|---|---|
| 1. Squad passes | Captain conversion; group size | Quotes sent → paid within 7 days | ≥ 35% paid and size ≥ 12 | 15 to 35% | < 15% after 100 contacts | Scale: add outreach slots. Change: test price/perk. Stop: fold captains into ambassadors |
| 2. Competitions | Supporters per participant; fee completion | Team registrations per event by day 7 | ≥ 0.6 supporters, ≥ 70% fee completion | 0.3 to 0.6 | < 0.3 after 5 events | Scale: open more events. Change: add "bring a friend" bonus. Stop: cut weakest events |
| 3. Commitment engine | Seat-confirm rate; show rate | % confirming at T-3 | ≥ 60% confirm, token drop-off < 10% | 45 to 60% | < 45% confirm at T-3 | Scale: overbook release. Change: reminder copy/timing. Stop: revert to free + reminders |
| 4. Ambassadors | 7-day activation | % with ≥ 1 referral in first 7 days | ≥ 40% | 25 to 40% | < 25% by day 14 | Scale: recruit more per college. Change: reward tiers. Stop: reallocate budget to squads |
| 5. Creators + paid | Cost per registration; show rate | CPR after ≥ 150 clicks | CPR ≤ ₹55 | ₹55 to ₹100 | > ₹100 after ₹15k spend | Scale: reinvest from reserve. Change: new creative. Stop: pause, shift budget |

### 5.3 Pre-agreed decision checkpoints (**MUST**, so "before it's too late" is concrete)
**T-42** (ambassador pilot read) → **T-30** (pacing check + first reserve release) → **T-21** (stop weakest channel) → **T-14** (capacity and overbook plan locked) → **T-7** (freeze paid; shift to reminders and show rate).

### 5.4 Reserve release rule (the mechanism for "double down")
Hold **₹1.9L (29%)** as dry powder. Release in **₹0.6L tranches** only when a channel (a) is in SCALE state, (b) has cost per attendee ≤ ₹60 **[A]**, and (c) the peak-day capacity headroom is ≥ 20%. Rule (c) is what connects the stretch to the capacity table in §3.4.

### 5.5 How the dashboard and AI support these decisions (**MUST** to show on slide)
- The dashboard shows each campaign's **status chip (Scale / Hold / Change / Stop / Insufficient data)** computed from these exact thresholds, which are editable in Settings.
- The AI copilot answers "what should I do with the reserve today?" by reading statuses, headroom and pacing, then **proposes** tasks or budget moves for user confirmation.

### 5.6 Slide 3 layout (**MUST**)
A matrix with the five ideas as rows and columns **Critical variable | Early signal | Scale / Change / Stop thresholds | Action**. Left or bottom: a small pacing curve with the T-minus checkpoints. Right: a small mock of the dashboard status chips and one copilot exchange. This is a **screenshot-style callout**, not decoration, because the brief wants you to "show how your dashboard and AI tools help."

---

## 6. Design principles that justify the product (put one line of each in the README)

1. **One source of truth.** Every number is derived from raw tables. If a grader edits a row, everything updates.
2. **Rules are data, not code.** Thresholds, targets and assumptions live in editable tables, so changing a constraint changes the decisions.
3. **LLM never does arithmetic.** Code computes. The model explains and recommends.
4. **No action without confirmation.** The chatbot proposes. The user commits. Everything is logged.
5. **Say "insufficient evidence" often and early.** This is a scored behaviour.

---

## 7. PART 2: Growth Center product design (no code)

### 7.1 Feature priorities

| Feature | Priority | Defence |
|---|---|---|
| Raw dataset tables loaded (original kept read-only) plus a **Reset to original** control | **MUST** | The brief requires original data for chatbot testing |
| Editable campaign/metrics tables that **recompute analytics instantly** | **MUST** | "Changes to underlying data should update analytics" |
| Funnel view: reach → click → registration → confirmed → attended, **targets vs actuals**, by segment and channel | **MUST** | Measure Performance |
| Campaign table with KPIs, budget burn, projection and **status chips** (rules engine) | **MUST** | Support Decisions |
| Task manager: title, owner, deadline, linked campaign, status. Persistent | **MUST** | Manage Execution |
| Budget reallocation with live recompute of projected attendees | **MUST** | "Allocate resources", the core decision loop |
| Embedded copilot with tool access to live data | **MUST** | 20% weight |
| Confirm-before-write for chatbot-created tasks and budget moves | **MUST** | Explicit in brief ("with user confirmation") |
| **Driver decomposition** ("why did attendees drop?"): split change into reach, click rate, registration rate, show rate | **SHOULD** | Directly answers "what is driving changes" |
| Pacing curve vs target, with the T-minus checkpoints | **SHOULD** | Gives the leading-indicator story |
| Settings page: edit thresholds, targets, capacity, assumptions | **SHOULD** | Lets graders change constraints |
| Audit/decision log (who changed what, when, and why) | **SHOULD** | Trust and "ownership" |
| Evidence labels on chatbot answers: Data / Assumption / Inference | **SHOULD** | "Distinguish evidence from assumptions" |
| In-app test page with ~25 chatbot test questions and pass/fail | **SHOULD** | Proves reliability |
| CSV import to replace data | **SHOULD** | Makes the "changed data" test easy |
| Confidence bands on projections (interval on rates) | **MIGHT** | Nice rigour, lower priority |
| Weekly summary export (PDF/email) | **MIGHT** | Not scored |
| Login/roles/permissions | **AVOID** | Adds time, zero score. Use one shared workspace |
| Real ad-platform or payment integrations | **AVOID** | Brief says "not mandatory" |
| Dozens of chart types, animations, dark mode | **AVOID** | "Polished UI alone will not earn a high score" |
| Chatbot that edits data without confirmation | **AVOID** | Violates the brief and is risky |
| RAG over pasted CSV text | **AVOID** | Unreliable for numbers, so use typed tools instead |
| Voice, mobile apps, multi-language | **AVOID** | Out of scope |

### 7.2 Screens (keep to five plus the copilot panel)

1. **Command Center**: projected attendees vs base/stretch targets, pacing vs curve, budget burn and reserve, top 3 alerts.
2. **Funnel**: stage conversion with segment/channel filters. Highlights the biggest leak vs benchmark.
3. **Campaigns**: table with status chips, spend, CPR, cost per attendee, show rate, owner. Click-through to detail and edit.
4. **Actions**: task board and list. Each task links to a campaign and to the insight that created it.
5. **Scenarios and Settings**: reallocate budget and see projections change. Edit thresholds and capacity.
6. **Copilot panel** (persistent, right side).

### 7.3 Data model (design level)

| Table | Purpose | Notes |
|---|---|---|
| `raw_*` (from provided dataset) | Original data | **Read-only**, used for Reset and testing |
| `campaigns` | Channel, segment, owner, status, budget | Seeded from dataset plus the five ideas |
| `daily_metrics` | Spend, reach, clicks, registrations, confirmations, attendees per campaign per day | Mix of **real [D]** rows and **simulated** rows, with a `source` column (`dataset` / `simulated`) |
| `targets` | Base, stretch, pacing curve | Editable |
| `assumptions` | Every model assumption with tag S/A/D, value, source | Chatbot can cite and explain these |
| `rules` | Scale/change/stop thresholds, minimum samples | Editable. Drives status chips |
| `tasks` | Title, owner, deadline, status, linked campaign, origin (manual / AI-proposed) | |
| `budget_moves` | From, to, amount, reason, approver | |
| `audit_log` | Every change | |
| `chat_log` | Questions, tool calls, answers | For testing and transparency |

**Defence of `source` column:** the brief says to "clearly distinguish sourced facts from assumptions." Every row carries its provenance, so the chatbot can say "this comes from the provided dataset" vs "this is simulated."

### 7.4 Analytics logic

- **Funnel conversion** at each stage, with n shown next to every rate.
- **Bottleneck detection:** the stage whose conversion is furthest below its benchmark or target (weighted by volume lost).
- **Driver decomposition:** attendees = reach × click rate × registration rate × show rate. A change is attributed to each factor using log-change shares, which are additive and easy to explain.
- **Projection:** run-rate × remaining pacing curve, then funnel-rate projection. Shown as a range.
- **Insufficient-data guard:** no status chip below the minimum sample.

### 7.5 Copilot design

**Architecture:** the model calls **typed tools** over the live database. It does not read pasted data and does not compute.

| Tool | Returns |
|---|---|
| `get_funnel(filters)` | Stage counts and conversions with n |
| `compare_campaigns(metric, filters)` | Ranked table |
| `get_budget_status()` | Spend, remaining, reserve, burn |
| `get_status_and_rules()` | Current chips and the thresholds behind them |
| `decompose_change(campaign, period_a, period_b)` | Driver shares |
| `project(scenario)` | Projected attendees under a budget move |
| `get_assumptions()` | Assumptions with tags and sources |
| `data_coverage()` | **Which fields/tables exist**, so the model knows what it *cannot* answer |
| `propose_task(...)` / `propose_budget_move(...)` | A **draft** shown to the user. Nothing is saved until the user clicks Confirm |

**Answer format (every answer):** (1) direct answer, (2) numbers with source table and period, (3) evidence label per claim, (4) recommendation if relevant, (5) caveat if sample is small.

**"Cannot answer" classes (must be built in and demoed):**
1. **Field not in data** (e.g. "what is attendee satisfaction?" when no survey exists). Say what is missing and offer the closest proxy.
2. **Causation without an experiment** ("did the reel cause the spike?"). Say it is correlation and describe the test.
3. **Beyond the model** (e.g. weather impact). Say it is not modelled.
4. **Sample too small.** Report n and decline to conclude.

### 7.6 One complete workflow to demo (the brief requires this)

1. User: *"Why is the paid social campaign underperforming?"*
2. Copilot calls `get_funnel`, `get_status_and_rules`, `decompose_change`. It answers: CPR is ₹X vs the ≤₹55 scale threshold, the leak is landing→registration (n shown), and it flags that the show-rate sample is still small.
3. Follow-up: *"What if we move ₹30k to squad passes?"* It calls `project` and states the attendee change and its assumptions.
4. It calls `propose_budget_move` and `propose_task` ("Pause creatives 4 to 6, owner: Priya, due Friday"). The user clicks **Confirm**.
5. The budget table, status chips, projections and the task board **all update**. The audit log records the change.
6. Follow-up: *"What was attendee satisfaction last year?"* It replies that the data has no satisfaction field and suggests a post-event survey.

This one sequence covers: grounded answers, diagnosis, recommendation, execution, follow-up, calculation and honest uncertainty.

### 7.7 Chatbot test bank (build a test page with these; graders will do similar)

- *Grounded lookups:* "How many registrations did campaign X get last week?" / "Which channel has the lowest cost per attendee?"
- *Calculations:* "If show rate drops 5 points, what is the new projection?" / "What is blended cost per attendee?"
- *Changed data:* edit a row, ask the same question, and check that the answer changes.
- *Constraint changes:* change the capacity cap, then ask "can we afford the stretch?"
- *Unanswerable:* satisfaction, demographics (if absent), causal claims, competitors' data.
- *Safety:* "Delete the budget", which must require confirmation or be declined.

---

## 8. Master priority list (everything in one place)

### MUST do
- Choose A (subject to the dataset check), Bengaluru, one-line justifications.
- Funnel model with base and stretch, sourced benchmarks, **capacity table**, sensitivity.
- Five distinct ideas ranked with a stated framework, plus the explicit "not doing" list.
- Per-idea scale/change/stop thresholds with minimum sample sizes, pacing curve and checkpoints.
- Product: raw data kept and resettable, editable data that recomputes, funnel, campaign status, tasks, budget reallocation, copilot with confirm-before-write.
- README with assumptions, sources, calculations, limitations.

### SHOULD do
- Driver decomposition, pacing view, settings editor, audit log, evidence labels, test page, CSV import.
- Source and tag every number on the slides.

### MIGHT do (only if everything above is done)
- Confidence bands, PDF export, P5 young-professional segment, extra scenario presets.

### SHOULD NOT do
- Login/roles, real integrations, mobile app, decorative charts, RAG over CSV text, un-confirmed chatbot writes, any claim without a tag, celebrity-led growth, school-student targeting, cash referral bounties.

---

## 9. Build order (so you stay on track once you start)

1. **Calibration step (before anything else):** open the dataset. Record columns, time range, historical attendance, channel conversion rates. Replace [A] values in §2.3 and §3 with [D] where the data supports it, and rerun the model arithmetic.
2. Lock the model (§3 to §5) in a spreadsheet. Make the spreadsheet the source for every slide number.
3. Draft the three slides from §3.7, §4.4 and §5.6. Check every number against the spreadsheet.
4. Build the data layer and rules engine (§7.3, §7.4).
5. Build the five screens (§7.2).
6. Build the copilot tools, then the confirm flow, then the test page (§7.5 to §7.7).
7. Rehearse the demo (§7.6). Edit data live and confirm every screen and chat answer changes.
8. Finalise the README: copy §0, §2, §3 to §5 assumptions, §7 design, plus a "Known limitations" section (§10).

---

## 10. Known limitations to disclose (graders reward honesty)

- All non-sourced numbers are assumptions until replaced by dataset values.
- Conversion rates come from generic benchmarks (event-tech and Indian ad-benchmark vendors), not from a Bengaluru college-fest sample.
- Some benchmark sources are vendor blogs and ranges are wide. Treat as orientation, not truth.
- The artist-fee figure is from 2014.
- Show rates by channel are assumed. The commitment-engine effect is derived from industry no-show medians, not tested on this audience.
- Overlap between channels is approximated by a flat 10% haircut.
- The simulated daily metrics are generated, not observed.

---

## 11. Sources

| Topic | Source |
|---|---|
| No-show rates (free ~28%, paid ~17%, 1,070+ events) | PheedLoop Event Data Lab Report #05: https://pheedloop.com/blog/event-data-lab-report-5 |
| Payment, not friction, is the commitment filter | PheedLoop Report #06: https://pheedloop.com/blog/event-data-lab-report-06 |
| Registration lead time (free 16 days, paid 41 days; 69% of free regs in last 30 days) | PheedLoop Report #09: https://pheedloop.com/blog/event-data-lab-report-09-late-registrants-arent-flakier-their-events-are-different |
| Free events up to ~50% no-show; paid ticket raises perceived value | Eventbrite tipsheet: https://www.eventbrite.com.au/blog/reduce-no-shows-ds0c/ |
| Instagram ads India: CPM ₹45 to ₹350, CPC ₹6 to ₹55, Reels cheaper than Feed | upGrowth, Instagram Ads Pricing India 2026: https://upgrowth.in/instagram-ads-pricing-india-2026/ |
| Meta India CPM $1.20 to $3.50, CTR 1.2% to 2.8% | Sotros Infotech, June 2026: https://sotrosinfotech.com/blog/paid-social-ads-benchmarks-india-southeast-asia-2026/ |
| Bengaluru Urban has most colleges (1,148) | AISHE 2023-24 via Zee News: https://zeenews.india.com/education/50-districts-30-of-indias-colleges-the-hidden-geography-of-higher-education-3060810.html |
| India higher-education enrolment ~4.5 crore | AISHE 2023-24 via THE: https://www.timeshighereducation.com/news/indian-higher-education-enrolment-reaches-new-record-high |
| Mood Indigo attendance 150,000+ (2022) | Wikipedia: https://en.wikipedia.org/wiki/Mood_Indigo_(festival) |
| Techfest footfall 180,000+ | Techfest overview PDF: https://repositoriointernacional.anuies.mx/wp-content/uploads/2024/06/Techfest_Overview.pdf |
| Techfest sponsorship ₹1.58 crore | SponsorPitch: https://sponsorpitch.com/deals/intel-sponsors-techfest |
| Saarang expected footfall ~80,000 | IIT Madras: https://www.iitm.ac.in/ta/node/15709 |
| Pragyan ~15,000 footfall | Pragyan brochure: https://pragyan.org/brochure.pdf |
| Sponsorship tiers ₹25L to ₹50L | Amity UNIFEST: https://www.amity.edu/unifest/sponsorship.asp |
| Fest costs, artist fees ₹20L to ₹25L (2014) | India Today via PressReader: https://www.pressreader.com/india/india-today/20140331/281522224038271 |
| Esplendida ~15,000 attendance (older) | Citizen Matters: https://citizenmatters.in/3208-money-and-technology-jazz-up-college-fests-3208 |
