#!/bin/bash
# Maryam's pipeline — Springer Nature

cd "$(dirname "$0")"
S="scripts"

echo "============================================================"
echo "  MARYAM — Springer Nature Pipeline"
echo "============================================================"

if [ ! -f "config.yaml" ]; then
    echo "ERROR: config.yaml not found."; exit 1
fi

if ! grep -q "^journals:" config.yaml || grep -q "journals: \[\]" config.yaml; then
    echo "ERROR: config.yaml has no journals."; exit 1
fi

if ! grep -q "SPRINGER_API_KEY=[^Y]" .env 2>/dev/null; then
    echo "WARNING: SPRINGER_API_KEY may not be set."
    read -p "Continue anyway? (y/n): " yn
    [ "$yn" != "y" ] && exit 1
fi

echo ""
echo ">>> 1/15  Fetching DOIs from Crossref..."
python $S/fetch_dois.py || { echo "FAILED at fetch_dois.py"; exit 1; }

echo ""
echo ">>> 2/15  Downloading PDFs from Springer..."
python $S/retrieve_springer.py || { echo "FAILED at retrieve_springer.py"; exit 1; }

echo ""
echo ">>> 3/15  Extracting text..."
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
echo ">>> 7/15  Classifying voice (LONG)..."
python $S/classify_voice.py || { echo "FAILED at classify_voice.py"; exit 1; }

echo ""
echo ">>> 8/15  Computing scores..."
python $S/compute_scores.py || { echo "FAILED at compute_scores.py"; exit 1; }

echo ""
echo ">>> 9/15  Fetching publication years..."
python $S/fetch_years.py || { echo "FAILED at fetch_years.py"; exit 1; }

echo ""
echo ">>> 10/15 Fetching citations..."
python $S/fetch_citations.py || { echo "FAILED at fetch_citations.py"; exit 1; }

echo ""
echo ">>> 11/15 Building master CSV..."
python $S/build_master.py || { echo "FAILED at build_master.py"; exit 1; }

echo ""
echo ">>> 12/15 Merging JIF and analyzing..."
python $S/analyze_with_jif.py || { echo "FAILED at analyze_with_jif.py"; exit 1; }

echo ""
echo ">>> 13/15 Robustness checks..."
python $S/check_robust_se.py || { echo "FAILED at check_robust_se.py"; exit 1; }
python $S/check_negbin.py || { echo "FAILED at check_negbin.py"; exit 1; }

echo ""
echo ">>> 14/15 Generating figures..."
for fig in make_fig1_combined.py make_fig2.py make_fig4_active.py \
           make_fig4_passive.py make_fig5_models.py make_fig6_jif.py \
           make_fig8_irr.py make_fig9_normalized.py; do
    python $S/$fig || { echo "FAILED at $fig"; exit 1; }
done

echo ""
echo ">>> 15/15 Generating tables..."
python $S/make_all_tables.py || { echo "FAILED at make_all_tables.py"; exit 1; }

echo ""
echo "============================================================"
echo "  PIPELINE COMPLETE"
echo "============================================================"
