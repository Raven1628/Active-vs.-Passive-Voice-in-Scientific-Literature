# Active Voice and Citations in Scientific Writing

Analysis code for a study of the relationship between grammatical voice (active vs. passive) and citation rates in scientific research articles.

## Overview

- Sample: 980 primary research articles from 7 Wiley journals
- Sample years: 2005, 2010, 2015, 2020, 2025
- Journals: Cancer, Clinical Genetics, Developmental Dynamics, Ecology, Molecular Ecology, Journal of Neuroscience Research, Molecular Microbiology
- Voice classification: spaCy dependency parsing (nsubjpass / auxpass to passive)
- Outcome: Average citations per year (OpenAlex, retrieved October 2026)
- Robustness: JIF-adjusted models, HC3 robust SEs, negative binomial regression, JIF-normalized outcome

## Key finding

Active voice was positively associated with citations per year (b = +9.79, p < 0.001), robust to controls for publication year, journal identity, journal impact factor, and distributional assumptions.

## Setup

Install dependencies:

    pip install -r requirements.txt
    python -m spacy download en_core_web_sm

For PDF retrieval, create a .env file with:

    WILEY_TDM_TOKEN=your_token_here

## Reproducing the analysis

Run the pipeline scripts in order from the project root:

    python scripts/fetch_dois.py
    python scripts/retrieve_wiley.py
    python scripts/extract_text.py
    python scripts/clean_sections.py
    python scripts/segment_sentences.py
    python scripts/classify_voice.py
    python scripts/compute_scores.py
    python scripts/check_papers.py
    python scripts/fetch_years.py
    python scripts/fetch_citations.py
    python scripts/build_master.py
    python scripts/analyze_with_jif.py
    python scripts/check_robust_se.py
    python scripts/check_negbin.py
    python scripts/make_all_tables.py
    python scripts/make_fig1_combined.py
    python scripts/make_fig2.py
    python scripts/make_fig4_active.py
    python scripts/make_fig4_passive.py
    python scripts/make_fig5_models.py
    python scripts/make_fig6_jif.py
    python scripts/make_fig8_irr.py
    python scripts/make_fig9_normalized.py

## Data availability

- Raw PDFs: Not included (copyright). DOIs listed in the journals folder.
- Derived data: analysis/master_with_jif.csv included for direct reproduction.
- Citation data: From OpenAlex, retrieved October 2026.
- Journal Impact Factors: Compiled from publicly available journal metrics (scripts/jif_lookup.csv).

## License

MIT License - see LICENSE file.
