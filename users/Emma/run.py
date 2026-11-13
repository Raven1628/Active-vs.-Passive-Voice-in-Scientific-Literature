#!/usr/bin/env python3
"""Cross-platform pipeline runner for Emma's T&F analysis."""

import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# Use the current Python interpreter (works on any OS)
PY = sys.executable

STAGES = [
    ("1/11  Fetching DOIs",                     "fetch_dois.py"),
    ("2/11  Downloading PDFs (manual — see SETUP.md)", "retrieve_tandf.py"),
    ("3/11  Extracting text",                   "extract_text.py"),
    ("4/11  Building whole-paper text",         "build_whole_papers.py"),
    ("5/11  Segmenting into sentences",         "segment_whole.py"),
    ("6/11  Classifying voice (LONG)",          "classify_whole.py"),
    ("7/11  Computing scores",                  "compute_whole_scores.py"),
    ("8/11  Fetching years",                    "fetch_years.py"),
    ("9/11  Fetching citations",                "fetch_citations.py"),
    ("10/11 Building master CSV + analysis",    "build_master.py"),
    ("11/11 Analysis + figures + tables",       None),  # multiple scripts
]

def run(script):
    path = os.path.join("scripts", script)
    if not os.path.exists(path):
        print(f"ERROR: {path} not found")
        sys.exit(1)
    print(f"\n>>> {script}")
    result = subprocess.run([PY, path])
    if result.returncode != 0:
        print(f"FAILED at {script}")
        sys.exit(result.returncode)

print("=" * 60)
print("  EMMA — T&F Whole-Paper Pipeline")
print("=" * 60)

# Basic stages
for label, script in STAGES[:-1]:
    print(f"\n>>> {label}")
    run(script)

# Final stage: analysis + figures + tables
print(f"\n>>> {STAGES[-1][0]}")
for script in [
    "analyze_with_jif.py",
    "check_robust_se.py",
    "check_negbin.py",
    "make_fig1_combined.py",
    "make_fig2.py",
    "make_fig4_active.py",
    "make_fig4_passive.py",
    "make_fig5_models.py",
    "make_fig6_jif.py",
    "make_fig8_irr.py",
    "make_fig9_normalized.py",
    "make_all_tables.py",
]:
    run(script)

print("\n" + "=" * 60)
print("  PIPELINE COMPLETE")
print("=" * 60)
print("Results: journals/_overall/scores_whole/")
