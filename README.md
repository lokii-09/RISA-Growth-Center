# RISA — Attendee Growth Command Center

RISA is a data-driven growth command center for the CampusFest 2025 attendee-growth assignment. It turns the supplied
workbook into reproducible attendance and campaign metrics, an interactive Streamlit dashboard, and a grounded AI
Growth Analyst. The workbook identifies its data as synthetic; do not treat this sample as live operational data.

## Problem and features

Festival organizers need a consistent view of the registration funnel, verified attendance, campaign efficiency, and
budget. RISA provides:

- Validated Excel ingestion, typed working tables, duplicate/relationship checks, and generated quality reporting.
- Deterministic KPI and funnel calculations with documented sources and definitions.
- Six dashboard pages for the command center, funnel, campaigns, budget, scenarios, and the AI analyst.
- Scenario projections clearly separated from actual historical outcomes.
- Approved analytics tools and optional Groq Cloud inference; local deterministic answers work without a key.
- Draft-only campaign reallocations that require explicit confirmation before changing session planning values.

## Architecture and technology

`data/Attendee Dataset.xlsx` → schema-checked ingestion → immutable `original` source DataFrames plus typed `working`
DataFrames → deterministic cleaning and validation → shared analytics → Streamlit dashboard and AI tools.

The app is Python 3.12 compatible and uses pandas, openpyxl, Pydantic, Streamlit, and Plotly. pytest covers data
processing, analytics, assistant safety, scenarios, proposals, and dashboard rendering. The source of KPI definitions is
[docs/kpi_definitions.md](docs/kpi_definitions.md).

## Documentation guide: where to find what

Start with the item matching your question:

| If you need to know… | Read this | What it contains |
|---|---|---|
| What the assignment requires and how it is graded | [Assignment PDF](docs/assignment.pdf) | Original brief, deliverables, and evaluation rubric. This is the highest-priority requirements source. |
| A searchable text version of the brief | [Assignment text](docs/assignment.txt) | Text extraction of the PDF; use the PDF if formatting or wording differs. |
| Which strategic and product-design choices were selected | [Final architecture blueprint](docs/final_blueprint.md) | Selected challenge/city, evidence interpretation, strategic choices, product architecture, and intended behavior. It is the primary design reference after the assignment. |
| What the alternative blueprint drafts proposed | [Claude blueprint](docs/blueprint_claude.md) and [Gemini blueprint](docs/blueprint_gemini.md) | Supplementary design alternatives only. They contain assumptions that conflict with the selected blueprint and verified workbook—for example, the Gemini draft proposes Delhi NCR and a different event/budget. Do not treat those draft values as current decisions or historical results. |
| What each workbook field means | [Generated data dictionary](docs/data_dictionary.md) | Worksheet fields, source types, and field-guide meanings, generated from the supplied workbook. |
| How a KPI is defined and calculated | [Central KPI definitions](docs/kpi_definitions.md) | Human-readable numerators, denominators, filters, source tables, and caveats. Executable code: [`metrics.py`](src/analytics/metrics.py) orchestrates calculations; [`funnel.py`](src/analytics/funnel.py), [`attendance.py`](src/analytics/attendance.py), [`campaigns.py`](src/analytics/campaigns.py), and [`budget.py`](src/analytics/budget.py) implement the metric areas. |
| What the workbook actually calculated | [Historical baseline report](reports/historical_baseline.md) | Reproducible workbook-derived historical results, including attendance split, spend, funnel, and campaign metrics. These are actuals, not the blueprint’s future planning projections. |
| What was missing, duplicated, or cleaned | [Data quality report](reports/data_quality.md) | Raw-versus-clean record counts, missing values, duplicate handling, and cleaning decisions. |
| Whether QA and deployment preparation passed | [Final QA report](docs/final_qa_report.md) | Audit findings, test commands/results, KPI reconciliation, security/deployment status, and final readiness. |
| How the AI analyst performed | [AI evaluation](docs/ai_evaluation.md) | The 40-prompt test bank, observed behavior, supported/unsupported requests, safety checks, and evaluation limitations. |
| How to publish and deploy manually | [Deployment guide](docs/deployment_guide.md) | GitHub setup, Streamlit Community Cloud configuration, secrets, and post-deployment smoke checks. |
| What the app cannot answer or persist | [Known limitations](docs/known_limitations.md) | Data, attribution, AI, scenario, and session-state limitations. |

### Source-of-truth and results rule

Resolve conflicts in this order: **assignment requirements → final architecture blueprint → alternative blueprints**.
For historical metrics, use the supplied workbook, the KPI definitions, and the executable analytics—not proposed
targets, projections, or numbers copied from a design draft. The final blueprint includes strategic planning scenarios;
those are not historical outcomes. The reports under `reports/` are regenerated from the workbook by the Phase 0
pipeline:

```powershell
python -m src.run_phase0 "data\Attendee Dataset.xlsx" --reports reports --data-dictionary docs\data_dictionary.md
```

In short: **design choices are in `docs/final_blueprint.md`; formulas are in `docs/kpi_definitions.md` and implemented
in `src/analytics/`; calculated historical results are in `reports/historical_baseline.md`.**

## Project phases and structure

- **Phase 0 — Data foundation:** ingestion, cleaning, canonical tables, analytics, and reproducible reports.
- **Phase 1 — Dashboard:** historical KPIs, filters, campaign analysis, planning edits, and scenario calculator.
- **Phase 2 — AI analyst:** grounded answers, approved tools, follow-up handling, and confirmation-based proposals.
- **Phase 3 — QA and deployment preparation:** regression, AI question-bank evaluation, secrets support, and deployment documentation.

```text
app.py                  Streamlit entry point
src/
  ingestion.py          Excel schema checks and typed working tables
  cleaning.py           Stable-ID, category, and relationship checks
  analytics/            Shared KPI, funnel, attendance, campaign, and budget logic
  dashboard/            Page and session-state logic
  assistant/             Local analyst, approved tools, proposals, provider
tests/                  pytest suite and AI evaluation question bank
data/                   Supplied workbook
docs/                   Definitions, blueprints, and QA/deployment reports
reports/                Generated historical and data-quality outputs
```

## Install and run locally

Use Python 3.12. From the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
streamlit run app.py
```

Run the Phase 0 report pipeline separately:

```powershell
python -m src.run_phase0 "data\Attendee Dataset.xlsx" --reports reports --data-dictionary docs\data_dictionary.md
```

The report command creates/updates `reports\data_quality.md`, `reports\historical_baseline.md`, and
`docs\data_dictionary.md`.

## Optional Groq Cloud AI configuration

Without credentials, RISA uses its deterministic local analyst. The default provider is Groq Cloud's
OpenAI-compatible chat-completions endpoint with `openai/gpt-oss-120b`. To use another model available to your Groq
account, replace the model ID with the exact ID shown in Groq Cloud. Configure either environment variables or
Streamlit secrets; environment variables take precedence.

Environment variables:

```powershell
$env:GROQ_API_KEY = "your-groq-api-key"
$env:RISA_AI_MODEL = "openai/gpt-oss-120b"
$env:RISA_AI_BASE_URL = "https://api.groq.com/openai/v1"
$env:RISA_AI_TIMEOUT_SECONDS = "25"
streamlit run app.py
```

For Streamlit Community Cloud, add the following in the app's **Settings → Secrets** (replace the key with your Groq
Cloud API key):

```toml
GROQ_API_KEY = "your-groq-api-key"
RISA_AI_MODEL = "openai/gpt-oss-120b"
RISA_AI_BASE_URL = "https://api.groq.com/openai/v1"
RISA_AI_TIMEOUT_SECONDS = "25"
```

Paste the key generated in Groq Cloud into `GROQ_API_KEY`. The older `RISA_AI_API_KEY` name is still accepted for
compatibility. Never commit API keys or `.streamlit/secrets.toml`; both are ignored by `.gitignore`. RISA handles absent
secrets by continuing in local mode. Provider requests contain the question, bounded conversation history, and approved
aggregated tool results—not raw workbook rows or attendee contact fields. Groq still processes the question and tool
results under its service terms; review those terms before using non-synthetic data.

## Tests and evaluation

Run the full suite with `python -m pytest -q`. The AI question bank contains more than 30 prompts across metrics,
funnel, campaigns, budget, scenarios, recommendations, follow-ups, unsupported requests, and safety. See
[docs/ai_evaluation.md](docs/ai_evaluation.md) for scope and limitations and
[docs/final_qa_report.md](docs/final_qa_report.md) for the latest local QA evidence.


## State and known limitations

Budget allocations, budget overrides, scenario inputs, and chat context are Streamlit session state. They are available
while that session is active, are not shared across users or browser sessions, and are not persisted across app restarts
or redeployments. Historical workbook data is read-only in the app. No database or durable planning store is configured.

Campaign attribution is observational, not causal. The workbook does not support satisfaction/NPS, venue capacity,
individual contact details, demographics, or causal ROI. Scenarios are not forecasts and do not estimate causal
spend-response curves. Review [docs/known_limitations.md](docs/known_limitations.md) before using RISA for decisions.

## Future work

If RISA is adapted for real events, replace the synthetic workbook with a privacy-reviewed source, define governance and
retention, add measured experiment outcomes, and introduce durable multi-user planning storage only if required.
