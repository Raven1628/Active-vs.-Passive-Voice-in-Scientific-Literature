# Gracie — MDPI Voice Analysis Setup (Windows)

## Prerequisites

Install Python from https://www.python.org/downloads/ (check "Add Python to PATH").

Then open Command Prompt:

    pip install pymupdf pyyaml requests python-dotenv spacy statsmodels matplotlib pandas scipy tqdm playwright
    python -m spacy download en_core_web_sm
    python -m playwright install chromium

## Step 1 — Launch Chrome with debugging

Close any open Chrome windows first. Then:

    "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\temp\chrome-mdpi-debug

(Adjust path if Chrome is in `Program Files (x86)`.)

A Chrome window opens. In that window:

1. Go to https://www.mdpi.com
2. Complete any Cloudflare "I'm human" challenge if it appears
3. Leave the Chrome window OPEN

## Step 2 — Fetch DOIs

Open a SECOND Command Prompt window (leave Chrome running in the first):

    cd path\to\users\Gracie
    python scripts\fetch_dois.py

## Step 3 — Download PDFs

The pipeline uses two downloaders:
- `retrieve_mdpi.py` — fast CDN download (works for 2010+ papers)
- `retrieve_mdpi_playwright.py` — slower browser fallback (for 2005-era DOIs the CDN doesn't host)

Run both via:

    python run.py

Or double-click `run.bat`.

## Step 4 — Send back

Zip and send:
- `journals\_overall\scores_whole\`
- `journals\_overall\stats_v2_lg\`
- `journals\_overall\summary_by_journal.csv`
- `journals\_overall\summary_by_year.csv`

## Troubleshooting

- **"Could not connect to Chrome"**: Chrome isn't running with `--remote-debugging-port=9222`. Restart from Step 1.
- **Many `parse_failed` for old DOIs**: Expected for 2005. The Playwright fallback handles those.
- **CDN download fails for 2010+ paper**: Try re-running — MDPI CDN occasionally rate-limits.
- **"python not found"**: Reinstall Python with "Add Python to PATH" checked.
