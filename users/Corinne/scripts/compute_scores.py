# scripts/compute_scores.py
# Aggregates sentence-level ACTIVE/PASSIVE classifications into
# per-section and per-paper active voice scores.

import os
import json
import sys
import csv
from config import (
    TARGET_JOURNALS, journal_path, ensure_journal_folders,
    CLASSIFICATIONS_SUBDIR, SCORES_SUBDIR, TARGET_SECTIONS,
)


def score_section(sentences):
    active = sum(1 for s in sentences if s.get("label") == "ACTIVE")
    passive = sum(1 for s in sentences if s.get("label") == "PASSIVE")
    total = active + passive
    ratio = (active / total) if total > 0 else None
    return {"active": active, "passive": passive,
            "total": total, "active_ratio": ratio}


def process_journal(journal, summary_rows):
    ensure_journal_folders(journal)
    src = journal_path(journal, CLASSIFICATIONS_SUBDIR)
    dst = journal_path(journal, SCORES_SUBDIR)

    if not os.path.exists(src):
        print(f"\n=== {journal} ===\n  No classifications folder. Skipping.")
        return

    files = sorted(f for f in os.listdir(src) if f.endswith(".json"))
    print(f"\n=== {journal} ===\n  Found {len(files)} classification files")

    processed = skipped = 0

    for filename in files:
        paper_id = filename.replace(".json", "")
        out_path = os.path.join(dst, filename)

        with open(os.path.join(src, filename)) as f:
            data = json.load(f)

        if data.get("_skip"):
            skipped += 1
            continue

        result = {"paper_id": paper_id, "journal": journal, "sections": {}}
        paper_active = paper_passive = 0

        for section in TARGET_SECTIONS:
            sentences = data.get(section, [])
            sec = score_section(sentences)
            result["sections"][section] = sec
            paper_active += sec["active"]
            paper_passive += sec["passive"]

        paper_total = paper_active + paper_passive
        result["paper"] = {
            "active": paper_active,
            "passive": paper_passive,
            "total": paper_total,
            "active_ratio": (paper_active / paper_total) if paper_total > 0 else None,
        }

        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)

        row = {
            "paper_id": paper_id,
            "journal": journal,
            "paper_active": paper_active,
            "paper_passive": paper_passive,
            "paper_total": paper_total,
            "paper_active_ratio": result["paper"]["active_ratio"],
        }
        for section in TARGET_SECTIONS:
            row[f"{section}_active_ratio"] = result["sections"][section]["active_ratio"]
            row[f"{section}_total"] = result["sections"][section]["total"]
        summary_rows.append(row)
        processed += 1

    print(f"  Processed: {processed}, Skipped: {skipped}")


def write_summary(summary_rows):
    if not summary_rows:
        print("\nNo rows to write to summary CSV.")
        return
    out_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "journals", "_overall", "scores")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "all_papers_summary.csv")
    fieldnames = list(summary_rows[0].keys())
    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"\nSummary CSV written: {out}")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    journals = [target] if target else TARGET_JOURNALS
    summary_rows = []
    for journal in journals:
        process_journal(journal, summary_rows)
    write_summary(summary_rows)


if __name__ == "__main__":
    main()
