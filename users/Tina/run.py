#!/usr/bin/env python3
"""Cross-platform pipeline runner for Tina's OUP analysis."""

import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

PY = sys.executable

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
print("  TINA — OUP Whole-Paper Pipeline")
print("=" * 60)

stages = [
    "fetch_dois.py",
    "retrieve_oup.py",
    "retrieve_oup.py",   # second pass catches timing races
    "extract_text.py",
    "build_whole_papers.py",
    "segment_whole.py",
    "classify_whole.py",
    "compute_whole_scores.py",
    "fetch_years.py",
    "fetch_citations.py",
    "build_master.py",
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
]

for i, script in enumerate(stages, 1):
    print(f"\n>>> {i}/{len(stages)}  {script}")
    run(script)

print("\n" + "=" * 60)
print("  PIPELINE COMPLETE")
print("=" * 60)
print("Results: journals/_overall/scores_whole/")
