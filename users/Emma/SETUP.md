# Emma — T&F Voice Analysis Setup (Windows)

## Prerequisites

Open Command Prompt, then:

    pip install pymupdf pyyaml requests python-dotenv spacy statsmodels matplotlib pandas scipy tqdm
    python -m spacy download en_core_web_sm

## Step 1 — Fetch DOIs

    cd path\to\users\Emma
    python scripts\fetch_dois.py

Writes DOIs to `journals\<journal>\dois.txt` for each of the 7 journals.

## Step 2 — Manual PDF download (REQUIRED)

Taylor & Francis' license prohibits automated downloading. Download PDFs manually:

1. Open browser → https://www.tandfonline.com
2. Log in via Georgia Tech Library
3. For each DOI in `journals\<journal>\dois.txt`:
   - Visit `https://doi.org/<DOI>`
   - Click the PDF button
   - Save as: `journals\<journal>\raw_papers\<DOI with / replaced by _>.pdf`
   - Example: DOI `10.1080/00222933.2020.1780331` →
     save as `10.1080_00222933.2020.1780331.pdf`

Recommendation: 5-10 papers per journal (35-70 total).

## Step 3 — Run the pipeline

Once PDFs are in `journals\<journal>\raw_papers\`:

    python run.py

(Or double-click `run.bat` on Windows.)

## Step 4 — Send back

Zip and send:
- `journals\_overall\scores_whole\`
- `journals\_overall\stats_v2_lg\`
- `journals\_overall\summary_by_journal.csv`
- `journals\_overall\summary_by_year.csv`

## Troubleshooting

- **`ModuleNotFoundError: pymupdf`** → `pip install pymupdf`
- **`ModuleNotFoundError: spacy`** → `pip install spacy` + `python -m spacy download en_core_web_sm`
- **`FileNotFoundError`** → ensure you're in the `users\Emma` folder
- **`python` not found** → install Python from python.org (check "Add Python to PATH")
