#!/bin/bash
# Gracie's pipeline — MDPI (open access)

cd "$(dirname "$0")"
S="scripts"

echo "============================================================"
echo "  GRACIE — MDPI Pipeline"
echo "============================================================"

if [ ! -f "config.yaml" ]; then
    echo "ERROR: config.yaml not found."; exit 1
fi

if ! grep -q "^journals:" config.yaml || grep -q "journals: \[\]" config.yaml; then
    echo "ERROR: config.yaml has no journals."; exit 1
fi

echo ""
echo ">>> 1/15  Fetching DOIs from Crossref..."
python $S/fetch_dois.py || { echo "FAILED"; exit 1; }

echo ""
echo ">>> 2/15  Downloading PDFs from MDPI (open access, no key needed)..."
python $S/retrieve_mdpi.py || { echo "FAILED"; exit 1; }

echo ""
echo ">>> 3/15  Extracting text..."
python $S/extract_text.py || { echo "FAILED"; exit 1; }

echo ""
echo ">>> 4/15  Splitting into IMRaD sections..."
python $S/split_sections.py || { echo "FAILED"; exit 1; }

echo ""
echo ">>> 5/15  Cleaning sections..."
python $S/clean_sections.py || { echo "FAILED"; exit 1; }

echo ""
echo ">>> 6/15  Segmenting sentences..."
python $S/segment_sentences.py || { echo "FAILED"; exit 1; }

echo ""
echo ">>> 7/15  Classifying voice (LONG)..."
python $S/classify_voice.py || { echo "FAILED"; exit 1; }

echo ""
echo ">>> 8/15  Computing scores..."
python $S/compute_scores.py || { echo "FAILED"; exit 1; }

echo ""
echo ">>> 9/15  Fetching years..."
python $S/fetch_years.py || { echo "FAILED"; exit 1; }

echo ""
echo ">>> 10/15 Fetching citations..."
python $S/fetch_citations.py || { echo "FAILED"; exit 1; }

echo ""
echo ">>> 11/15 Building master CSV..."
python $S/build_master.py || { echo "FAILED"; exit 1; }

echo ""
echo ">>> 12/15 Merging JIF and analyzing..."
python $S/analyze_with_jif.py || { echo "FAILED"; exit 1; }

echo ""
echo ">>> 13/15 Robustness checks..."
python $S/check_robust_se.py || { echo "FAILED"; exit 1; }
python $S/check_negbin.py || { echo "FAILED"; exit 1; }

echo ""
echo ">>> 14/15 Generating figures..."
for fig in make_fig1_combined.py make_fig2.py make_fig4_active.py \
           make_fig4_passive.py make_fig5_models.py make_fig6_jif.py \
           make_fig8_irr.py make_fig9_normalized.py; do
    python $S/$fig || { echo "FAILED at $fig"; exit 1; }
done

echo ""
echo ">>> 15/15 Generating tables..."
python $S/make_all_tables.py || { echo "FAILED"; exit 1; }

echo ""
echo "============================================================"
echo "  PIPELINE COMPLETE"
echo "============================================================"
