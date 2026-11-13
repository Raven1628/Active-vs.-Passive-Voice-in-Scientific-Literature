#!/bin/bash
cd "$(dirname "$0")"
S="scripts"

echo "============================================================"
echo "  TINA — Oxford University Press Pipeline"
echo "============================================================"

if [ ! -f "config.yaml" ]; then
    echo "ERROR: config.yaml not found."; exit 1
fi

echo ">>> 1/15  Fetching DOIs..."
python $S/fetch_dois.py || exit 1

echo ">>> 2/15  Downloading PDFs from OUP (API + proxy)..."
python $S/retrieve_oup.py || exit 1

echo ">>> 3/15  Extracting text..."
python $S/extract_text.py || exit 1

echo ">>> 4/15  Splitting sections..."
python $S/split_sections.py || exit 1

echo ">>> 5/15  Cleaning sections..."
python $S/clean_sections.py || exit 1

echo ">>> 6/15  Segmenting sentences..."
python $S/segment_sentences.py || exit 1

echo ">>> 7/15  Classifying voice (LONG)..."
python $S/classify_voice.py || exit 1

echo ">>> 8/15  Computing scores..."
python $S/compute_scores.py || exit 1

echo ">>> 9/15  Fetching years..."
python $S/fetch_years.py || exit 1

echo ">>> 10/15 Fetching citations..."
python $S/fetch_citations.py || exit 1

echo ">>> 11/15 Building master CSV..."
python $S/build_master.py || exit 1

echo ">>> 12/15 Merging JIF and analyzing..."
python $S/analyze_with_jif.py || exit 1

echo ">>> 13/15 Robustness checks..."
python $S/check_robust_se.py || exit 1
python $S/check_negbin.py || exit 1

echo ">>> 14/15 Generating figures..."
for fig in make_fig1_combined.py make_fig2.py make_fig4_active.py make_fig4_passive.py make_fig5_models.py make_fig6_jif.py make_fig8_irr.py make_fig9_normalized.py; do
    python $S/$fig || exit 1
done

echo ">>> 15/15 Generating tables..."
python $S/make_all_tables.py || exit 1

echo "============================================================"
echo "  PIPELINE COMPLETE"
echo "============================================================"
