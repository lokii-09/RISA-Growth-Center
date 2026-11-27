# GitHub and Streamlit Community Cloud Deployment

Deployment is a manual user action. This audit did not create a repository, push code, configure a Cloud app, or publish
a URL. The workspace did not contain a Git repository when inspected.

## 1. Prepare and validate the project

From the project root, use Python 3.12 and run:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
streamlit run app.py
```

Confirm the local app opens and the workbook at `data\Attendee Dataset.xlsx` is present. The workbook is required at
runtime and is a small synthetic sample; do not omit it unless the app is changed to use another source.

Before staging, confirm that no API keys, `.env` files, or `.streamlit\secrets.toml` are in the project. `.gitignore`
excludes these local secret files and Python/test caches. Do not use `git add -f` on secrets.

## 2. Create and push a GitHub repository

Create a new empty GitHub repository in the account/organization intended for the submission. Do not initialize it with
a second README or license; the project already has a README. From PowerShell in the project root:

```powershell
git init
git branch -M main
git add .
git status --short
git diff --cached --stat
git diff --cached --name-only
```

Inspect the staged file list. Confirm that `.streamlit/secrets.toml`, `.env`, keys, and private data are not staged.
Then commit and push:

```powershell
git commit -m "Prepare RISA for Streamlit deployment"
git remote add origin https://github.com/<ACCOUNT>/<REPOSITORY>.git
git push -u origin main
```

Use the repository visibility required for the assignment. The supplied synthetic workbook is part of the application;
do not include any replacement workbook containing real personal or confidential information in a public repository.

## 3. Create the Streamlit Community Cloud app

1. Sign in to Streamlit Community Cloud with the GitHub account that can access the repository.
2. Select **Create app**.
3. Choose the RISA repository, the `main` branch, and `app.py` as the main file path.
4. In advanced settings, select Python 3.12 if the selector is available.
5. Add secrets only if enabling Groq Cloud AI. In the app settings, open **Secrets** and add:

   ```toml
   GROQ_API_KEY = "your-groq-api-key"
   RISA_AI_MODEL = "openai/gpt-oss-120b"
   RISA_AI_BASE_URL = "https://api.groq.com/openai/v1"
   RISA_AI_TIMEOUT_SECONDS = "25"
   ```

   Paste the key from Groq Cloud into `GROQ_API_KEY`; use a different model ID only if it is available to your Groq
   account. Never put the key in code, README, repository files, or chat prompts. The older `RISA_AI_API_KEY` name is
   also accepted for existing configurations. Without a key, RISA uses its deterministic local analyst.

6. Deploy the app and wait for the build to complete. Read the Cloud logs if startup fails; do not paste secret values
   into public issues or logs.

## 4. Post-deployment smoke test

Open the generated public URL in a private/incognito browser window and verify:

- The app loads without a startup error.
- Each of the six navigation pages opens and charts render.
- Historical KPIs match `reports\historical_baseline.md`.
- Campaign filters and comparisons work.
- Budget edits reject invalid or over-budget values, require confirmation where applicable, and reset correctly.
- Scenario Lab values are labeled hypothetical and do not change historical KPIs.
- The AI answers a historical metric and an unsupported question without inventing facts.
- A campaign transfer is only drafted until the visible confirmation action is selected; canceling leaves values unchanged.
- Provider behavior is as configured: local mode works without a key; with a key, a test question is answered and a
  deliberate invalid/unavailable provider case degrades safely.
- Browser/mobile layout is usable and the public URL points to the intended repository and branch.

No live deployment URL exists yet, so public URL verification remains for the deployer.

## Troubleshooting

- **Missing workbook:** check the repository contains `data/Attendee Dataset.xlsx` and that the deployment entry point is
  `app.py`.
- **Dependency/build error:** confirm Python 3.12 and the pinned `requirements.txt` are selected; inspect the Cloud build
  log for the first package error.
- **AI unavailable:** verify the Groq key/model are spelled exactly as above and the secrets use valid TOML. The app should still
  run in local mode without AI credentials.
- **Provider errors:** check provider endpoint/model availability, then confirm the app falls back to local mode. Never
  print or share the API key when debugging.
- **Planning values reset:** this is expected when a Streamlit session ends or the app restarts; planning state is not
  durably stored.
- **Public-access concern:** restrict repository/app access or remove sensitive data before sharing; there is no
  application-level user authentication.
