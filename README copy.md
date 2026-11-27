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

## Deployment

Deployment is a manual user action; this project has not been published or deployed. Follow
[docs/deployment_guide.md](docs/deployment_guide.md) for GitHub preparation, Streamlit Community Cloud setup, and
post-deployment checks.

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
