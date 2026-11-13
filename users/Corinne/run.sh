#!/bin/bash
# Corinne's pipeline — Elsevier, section-based processing

cd "$(dirname "$0")"
S="scripts"

echo "============================================================"
echo "  CORRINNE — Elsevier Pipeline"
echo "============================================================"

# Pre-flight checks
if [ ! -f "config.yaml" ]; then
    echo "ERROR: config.yaml not found."
    exit 1
fi

if ! grep -q "^journals:" config.yaml || grep -q "journals: \[\]" config.yaml; then
    echo "ERROR: config.yaml has no journals. Add them before running."
    exit 1
fi

if ! grep -q "ELSEVIER_API_KEY=[^Y]" .env 2>/dev/null; then
    echo "WARNING: ELSEVIER_API_KEY may not be set in .env"
    echo "         PDF download will fail if it's still YOUR_KEY_HERE."
    echo ""
    read -p "Continue anyway? (y/n): " yn
    if [ "$yn" != "y" ]; then
        exit 1
    fi
fi

echo ""
echo ">>> 1/15  Fetching DOIs from Crossref..."
python $S/fetch_dois.py || { echo "FAILED at fetch_dois.py"; exit 1; }

echo ""
echo ">>> 2/15  Downloading PDFs from Elsevier..."
python $S/retrieve_elsevier.py || { echo "FAILED at retrieve_elsevier.py"; exit 1; }

echo ""
echo ">>> 3/15  Extracting text from PDFs..."
python $S/extract_text.py || { echo "FAILED at extract_text.py"; exit 1; }

echo ""
echo ">>> 4/15  Splitting into IMRaD sections..."
python $S/split_sections.py || { echo "FAILED at split_sections.py"; exit 1; }

echo ""
echo ">>> 5/15  Cleaning sections..."
python $S/clean_sections.py || { echo "FAILED at clean_sections.py"; exit 1; }

echo ""
echo ">>> 6/15  Segmenting sentences..."
python $S/segment_sentences.py || { echo "FAILED at segment_sentences.py"; exit 1; }

echo ""
echo ">>> 7/15  Classifying voice (LONG — 30 to 90 minutes)..."
python $S/classify_voice.py || { echo "FAILED at classify_voice.py"; exit 1; }

echo ""
echo ">>> 8/15  Computing per-paper scores..."
python $S/compute_scores.py || { echo "FAILED at compute_scores.py"; exit 1; }

echo ""
echo ">>> 9/15  Fetching publication years..."
python $S/fetch_years.py || { echo "FAILED at fetch_years.py"; exit 1; }

echo ""
echo ">>> 10/15 Fetching citations from OpenAlex..."
python $S/fetch_citations.py || { echo "FAILED at fetch_citations.py"; exit 1; }

echo ""
echo ">>> 11/15 Building master CSV (scores + years + citations)..."
python $S/build_master.py || { echo "FAILED at build_master.py"; exit 1; }

echo ""
echo ">>> 12/15 Merging JIF and running regression models..."
python $S/analyze_with_jif.py || { echo "FAILED at analyze_with_jif.py"; exit 1; }

echo ""
echo ">>> 13/15 Robustness checks..."
python $S/check_robust_se.py || { echo "FAILED at check_robust_se.py"; exit 1; }
python $S/check_negbin.py || { echo "FAILED at check_negbin.py"; exit 1; }

echo ""
echo ">>> 14/15 Generating figures..."
python $S/make_fig1_combined.py || { echo "FAILED at make_fig1_combined.py"; exit 1; }
python $S/make_fig2.py || { echo "FAILED at make_fig2.py"; exit 1; }
python $S/make_fig4_active.py || { echo "FAILED at make_fig4_active.py"; exit 1; }
python $S/make_fig4_passive.py || { echo "FAILED at make_fig4_passive.py"; exit 1; }
python $S/make_fig5_models.py || { echo "FAILED at make_fig5_models.py"; exit 1; }
python $S/make_fig6_jif.py || { echo "FAILED at make_fig6_jif.py"; exit 1; }
python $S/make_fig8_irr.py || { echo "FAILED at make_fig8_irr.py"; exit 1; }
python $S/make_fig9_normalized.py || { echo "FAILED at make_fig9_normalized.py"; exit 1; }

echo ""
echo ">>> 15/15 Generating tables..."
python $S/make_all_tables.py || { echo "FAILED at make_all_tables.py"; exit 1; }

echo ""
echo "============================================================"
echo "  PIPELINE COMPLETE"
echo "============================================================"
echo "Master data:  analysis/master_with_jif_analyzed.csv"
echo "Figures:      analysis/figures/"
echo "Tables:       analysis/figures/"
