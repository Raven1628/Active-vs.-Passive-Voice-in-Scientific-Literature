# Tina — OUP Voice Analysis Setup (Windows)

## Prerequisites

Install Python from https://www.python.org/downloads/ (check "Add Python to PATH").

Then open Command Prompt:

    pip install pymupdf pyyaml requests python-dotenv spacy statsmodels matplotlib pandas scipy tqdm playwright
    python -m spacy download en_core_web_sm
    python -m playwright install chromium

## Step 1 — Launch Chrome with debugging

Close any open Chrome windows first. Then:

    "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\temp\chrome-oup-debug

(If Chrome is installed in `Program Files (x86)`, adjust the path.)

A Chrome window opens. In that window:

1. Go to https://academic.oup.com
2. Click "Sign in" → "Sign in via your Institution" → Georgia Institute of Technology
3. Complete GT SSO
4. Leave the Chrome window OPEN

## Step 2 — Fetch DOIs

Open a SECOND Command Prompt window (leave Chrome running in the first):

    cd path\to\users\Tina
    python scripts\fetch_dois.py

Writes DOIs to `journals\<journal>\dois.txt` for each of the 7 journals.

## Step 3 — Download PDFs via Playwright

In the second Command Prompt (Chrome still running in the first):

    python scripts\retrieve_oup.py

Runs twice (second pass catches timing races). Downloads PDFs to `journals\<journal>\raw_papers\`.

## Step 4 — Run the pipeline

    python run.py

Or double-click `run.bat`.

## Step 5 — Send back

Zip and send:
- `journals\_overall\scores_whole\`
- `journals\_overall\stats_v2_lg\`
- `journals\_overall\summary_by_journal.csv`
- `journals\_overall\summary_by_year.csv`

## Troubleshooting

- **"Could not connect to Chrome"**: Chrome isn't running with `--remote-debugging-port=9222`. Restart from Step 1.
- **"Execution context was destroyed"**: Timing race on first DOI. Re-run `retrieve_oup.py` — it skips already-downloaded PDFs.
- **HTTP 403 / not_pdf**: OUP session expired. Re-login in Chrome window, then re-run.
- **"python not found"**: Python isn't on PATH. Reinstall Python, check "Add Python to PATH".
