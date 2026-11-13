# Gabby — Frontiers Voice Analysis Setup (Mac)

## Prerequisites

Install Python 3.10+ from https://www.python.org/downloads/ (Mac installer).

Then open **Terminal** (Spotlight → "Terminal" → Enter):

    pip3 install pymupdf pyyaml requests python-dotenv spacy statsmodels matplotlib pandas scipy tqdm
    python3 -m spacy download en_core_web_sm

Takes 5–10 min.

## Step 1 — Fetch DOIs

    cd ~/Desktop/Active-vs.-Passive-Voice-in-Scientific-Literature/users/Gabby
    python3 scripts/fetch_dois.py

Takes 5–10 min. Fetches ~1,400 DOIs (7 journals × 5 years × 40 papers).

## Step 2 — Download PDFs

Frontiers is fully open access — no login, no authentication, no proxy needed.

    python3 scripts/retrieve_frontiers.py

Downloads directly from frontiersin.org. ~20–40 min for ~1,000 PDFs.

## Step 3 — Run the pipeline

    python3 run.py

Or run stages individually:

    python3 scripts/build_whole_papers.py
    python3 scripts/segment_whole.py
    python3 scripts/classify_whole.py
    python3 scripts/compute_whole_scores.py
    python3 scripts/fetch_years.py
    python3 scripts/fetch_citations.py
    python3 scripts/build_master.py
    python3 scripts/analyze_with_jif.py
    python3 scripts/check_robust_se.py
    python3 scripts/check_negbin.py
    python3 scripts/make_fig1_combined.py
    python3 scripts/make_fig2.py
    python3 scripts/make_fig4_active.py
    python3 scripts/make_fig4_passive.py
    python3 scripts/make_fig5_models.py
    python3 scripts/make_fig6_jif.py
    python3 scripts/make_fig8_irr.py
    python3 scripts/make_fig9_normalized.py
    python3 scripts/make_all_tables.py

Takes ~20–40 min (mostly `classify_whole.py` running spaCy over all sentences).

## Step 4 — Send back

Zip and send:
- `journals/_overall/scores_whole/`
- `journals/_overall/stats_v2_lg/`
- `journals/_overall/summary_by_journal.csv`
- `journals/_overall/summary_by_year.csv`

Command to zip:

    cd ~/Desktop
    zip -r gabby_results.zip \
      Active-vs.-Passive-Voice-in-Scientific-Literature/users/Gabby/journals/_overall/scores_whole \
      Active-vs.-Passive-Voice-in-Scientific-Literature/users/Gabby/journals/_overall/stats_v2_lg \
      Active-vs.-Passive-Voice-in-Scientific-Literature/users/Gabby/journals/_overall/summary_by_journal.csv \
      Active-vs.-Passive-Voice-in-Scientific-Literature/users/Gabby/journals/_overall/summary_by_year.csv

## Troubleshooting

- **`ModuleNotFoundError: pymupdf`** → `pip3 install pymupdf`
- **`ModuleNotFoundError: spacy`** → `pip3 install spacy` + `python3 -m spacy download en_core_web_sm`
- **`FileNotFoundError`** → make sure you're in the `users/Gabby` folder
- **`python3: command not found`** → install Python from python.org, or use `brew install python3`
- **Many `parse_failed`** → check `scripts/config.py` has `DOI_PREFIXES = ("10.3389/",)`
