# RISA Phase 3 — Final QA and Deployment Readiness

## Executive status

**Ready for deployment; not deployed or publicly verified.** Local regression tests and a local Streamlit health check
passed. No Git repository was present in the workspace; no repository was initialized, pushed, or published.

## A. Audit findings

| Severity | Finding | Resolution |
|---|---|---|
| Medium | Ingestion coerced invalid dates/numbers in the same DataFrames used as the source copy, losing original invalid cell values. | Preserved workbook-parsed source tables separately from typed working tables; conversion failures are reported. |
| Medium | Duplicate conflict counts were inferred from row arithmetic, which could misclassify conflicting groups; missing stable IDs could be deduplicated together. | Compare duplicate group contents, classify exact/conflicting groups deterministically, preserve every missing-ID row, and report both. |
| Medium | A single-destination budget transfer could be answered as a campaign lookup; causal ROI wording was not explicitly abstained on; over-budget scenario spend lacked a warning. | Ask for the missing source campaign, explicitly abstain on causal ROI, and flag hypothetical planning-budget overages without applying edits. |
| Low | Baseline report asserted a fixed blueprint reconciliation and a hardcoded status-count explanation. | Replaced with definition-based, data-independent discrepancy guidance and regression coverage. |
| Low | AI provider configuration did not read Streamlit Cloud secrets; the project lacked secret/cache ignore rules. | Added environment-first/Streamlit-secrets fallback, `.gitignore`, deployment configuration guidance, and precedence tests. |

### Security-review summary

The read-only security review found no exploitable vulnerabilities in the reviewed scope. The local code/tool path
uses an explicit approved-tool dispatcher, rejects unknown tools, validates tool arguments, does not expose attendee
contact fields to the analyst, and requires UI confirmation for budget edits. A source scan found no committed-looking
API keys; expected placeholder strings remain in documentation. No local `.env` or Streamlit secrets file was present.

| # | Severity | File | Lines | Vulnerability | Confidence |
|---|----------|------|-------|---------------|------------|

No findings to report.

## B. Test and runtime results

| Command/check | Result |
|---|---|
| `python -m src.run_phase0 "data\Attendee Dataset.xlsx" --reports reports --data-dictionary docs\data_dictionary.md` | Completed; generated quality, baseline, and data-dictionary reports. |
| `python -B -m pytest tests\test_assistant.py -q -p no:cacheprovider` with `PYTHONDONTWRITEBYTECODE=1` | 27 passed in 6.19 seconds, including Groq settings and fallback checks. |
| `python -B -m pytest -q -p no:cacheprovider` with `PYTHONDONTWRITEBYTECODE=1` | 61 passed in 84.30 seconds; no remaining failures and no project cache directories were recreated. |
| `python -m streamlit run app.py --server.headless true --server.port 8502 --server.fileWatcherType none` | Local app started; `GET /_stcore/health` returned HTTP 200 `ok`; root returned HTTP 200. Port 8501 was already occupied, so validation used 8502. |

The complete suite includes ingestion/schema checks, cleaning and stable-ID behavior, analytics/KPIs, dashboard
rendering and state, scenario calculations, assistant/tool/provider behavior, question-bank checks, proposal safety,
and report generation. The final test run followed code changes and cache cleanup. Remaining automated test failures:
none.

## C. KPI verification

The workbook-derived baseline report and deterministic analytics reproduce all supplied checkpoints:

| Metric | Verified value |
|---|---:|
| Identified external people | 3,625 |
| External registrations | 2,800 |
| Confirmed external registrations | 2,500 |
| Unique verified external attendees | 2,050 |
| Registered attendees | 1,925 |
| Walk-ins | 125 |
| Event-close campaign spend | ₹276,500 |
| Revised marketing budget | ₹300,000 |
| Remaining budget | ₹23,500 |
| Registered show rate | 77.0% |
| Blended cost per attendee | ₹134.88 |
| Attendance by day | 1,430 (Apr 12); 1,345 (Apr 13) |

The data quality report shows raw-to-clean counts of 483→481 Daily Marketing rows, 5,911→5,907 Registration History
rows, and 3,390→3,370 Check-ins. Workbook duplicates were exact in the supplied data; focused tests also introduce a
conflicting duplicate group and verify its classification. The registered/walk-in split reconciles to 2,050 total.

## D. AI evaluation

The local deterministic analyst was checked against a 40-prompt question bank spanning KPI retrieval, funnel, campaign
comparison, budget, diagnosis, recommendations, scenarios, follow-ups, unsupported questions, safety, and ambiguous
actions. The full automated question-bank test passed: answers are nonempty, use only approved tools, and leave
proposals unapplied. Focused assertions cover numerical checkpoints, uncertainty language, causal ROI abstention,
contextual follow-ups, code-execution refusal, and ambiguous transfer clarification.

Mock provider tests cover missing tool calls, ungrounded numeric claims, malformed responses, and provider failures.
**Live provider/model quality was not evaluated** because no credentials were supplied. See
[ai_evaluation.md](./ai_evaluation.md) for the individual prompts and outcomes.

## E. Deployment readiness

- **GitHub:** project contains README, entrypoint, pinned direct requirements, `.gitignore`, required sample workbook,
  and deployment documentation. No `.git` directory exists; repository creation/push remains a user step.
- **Streamlit:** `app.py` resolves the workbook relative to its own file; the local server health check passed on port
  8502. Python 3.12.12 and pinned dependencies were used for validation.
- **Secrets/provider:** Groq Cloud is the default OpenAI-compatible endpoint, using `openai/gpt-oss-120b`; model and
  endpoint remain configurable. `GROQ_API_KEY` is read from environment first, then Streamlit secrets, with legacy
  `RISA_AI_API_KEY` support. Missing credentials leave the local analyst available. No key was supplied or tested live.
- **Persistence:** planning edits/chat/scenario state are session-only. No database or durable cross-user persistence is
  configured.
- **Public deployment:** not performed. No public URL exists to verify.

## F. Files created or modified

- `.gitignore`
- `README.md`
- `requirements.txt`
- `src/assistant/engine.py`
- `src/assistant/provider.py`
- `src/cleaning.py`
- `src/ingestion.py`
- `src/reports.py`
- `tests/question_bank.py`
- `tests/test_assistant.py`
- `tests/test_cleaning.py`
- `tests/test_ingestion.py`
- `tests/test_reports.py` (new)
- `docs/ai_evaluation.md` (new)
- `docs/deployment_guide.md` (new)
- `docs/final_qa_report.md` (new)
- `docs/known_limitations.md` (new)
- Regenerated `docs/data_dictionary.md`, `reports/data_quality.md`, and `reports/historical_baseline.md`

No project source files or datasets were removed. The identified Python and pytest cache directories were removed;
the final no-cache test run left no cache directories behind.

## G. User deployment steps

1. Review the staged file list and confirm no secrets or real personal data are included.
2. Create an empty GitHub repository, then initialize, commit, and push the project to `main`.
3. In Streamlit Community Cloud, create an app from that repository and branch.
4. Select `app.py` and Python 3.12.
5. Add the four `RISA_AI_*` values under app **Settings → Secrets** only if using a live AI provider; otherwise omit them.
6. Deploy and wait for the build to complete.

The exact PowerShell commands and configuration are in [deployment_guide.md](./deployment_guide.md).

## H. Post-deployment verification

Open the public URL and check startup, all six navigation pages/charts, historical KPIs, campaign filters, budget
validation/edit/reset, scenario labeling and non-mutation, local/provider chatbot behavior, unsupported-question
abstention, explicit proposal confirmation/cancellation, safe API failure handling, and browser/mobile layout. Confirm
that the URL points to the intended repository and branch. The live checks remain pending until deployment.

## I. Final classification

**Ready for deployment.** Local functional and regression evidence is complete. RISA is **not deployed and not publicly
verified**; GitHub publication, Cloud configuration, live-provider evaluation, and public smoke testing require the
user's deployment action.
