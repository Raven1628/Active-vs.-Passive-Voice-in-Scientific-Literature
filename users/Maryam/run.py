#!/usr/bin/env python3
"""Cross-platform pipeline runner for Maryam's Springer Nature analysis.

Usage:
  python3 run.py              # full pipeline (fetch DOIs + download PDFs + analysis)
  python3 run.py --no-download  # skip DOI fetch and PDF download (if you already have them)
"""

import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
PY = sys.executable
SKIP_DOWNLOAD = "--no-download" in sys.argv


def run(script, skip_if_missing=False):
    path = os.path.join("scripts", script)
    if not os.path.exists(path):
        if skip_if_missing:
            print(f"  (skip: {script} not found)")
            return
        print(f"ERROR: {path} not found")
        sys.exit(1)
    print(f"\n>>> {script}")
    result = subprocess.run([PY, path])
    if result.returncode != 0:
        print(f"FAILED at {script}")
        sys.exit(result.returncode)


print("=" * 60)
print("  MARYAM — Springer Nature Whole-Paper Pipeline")
if SKIP_DOWNLOAD:
    print("  Mode: --no-download (skipping DOI fetch + PDF download)")
print("=" * 60)

if not SKIP_DOWNLOAD:
    run("fetch_dois.py")
    run("retrieve_springer_playwright.py")

run("extract_text.py")

for script in [
    "build_whole_papers.py", "segment_whole.py", "classify_whole.py",
    "compute_whole_scores.py",
    "fetch_years.py", "fetch_citations.py", "build_master.py",
    "analyze_with_jif.py", "check_robust_se.py", "check_negbin.py",
    "make_fig1_combined.py", "make_fig2.py",
    "make_fig4_active.py", "make_fig4_passive.py", "make_fig5_models.py",
    "make_fig6_jif.py", "make_fig8_irr.py", "make_fig9_normalized.py",
    "make_all_tables.py",
]:
    run(script, skip_if_missing=True)

print("\n" + "=" * 60)
print("  PIPELINE COMPLETE")
print("=" * 60)
print("Results: journals/_overall/scores_whole/")
