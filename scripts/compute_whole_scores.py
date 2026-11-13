# scripts/compute_whole_scores.py
# Aggregates whole-paper classifications into one active voice ratio per paper.

import os
import json
import sys
import csv
from config import (
    TARGET_JOURNALS, journal_path, ensure_journal_folders,
    CLASSIFICATIONS_WHOLE_SUBDIR, SCORES_WHOLE_SUBDIR,
)


def process_journal(journal, rows):
    ensure_journal_folders(journal)
    src = journal_path(journal, CLASSIFICATIONS_WHOLE_SUBDIR)
    dst = journal_path(journal, SCORES_WHOLE_SUBDIR)

    if not os.path.exists(src):
        print(f"\n=== {journal} ===\n  No classifications_whole folder. Skipping.")
        return

    files = sorted(f for f in os.listdir(src) if f.endswith(".json"))
    print(f"\n=== {journal} ===\n  Found {len(files)} files")

    processed = skipped = 0
    for filename in files:
        paper_id = filename.replace(".json", "")
        out_path = os.path.join(dst, filename)

        with open(os.path.join(src, filename)) as f:
            data = json.load(f)

        if data.get("_skip"):
            skipped += 1
            continue

        labels = data.get("classifications", [])
        active = sum(1 for s in labels if s.get("label") == "ACTIVE")
        passive = sum(1 for s in labels if s.get("label") == "PASSIVE")
        total = active + passive
        ratio = (active / total) if total > 0 else None

        result = {
            "paper_id": paper_id,
            "journal": journal,
            "active": active,
            "passive": passive,
            "total": total,
            "active_ratio": ratio,
        }
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)

        rows.append({
            "paper_id": paper_id,
            "journal": journal,
            "active": active,
            "passive": passive,
            "total": total,
            "active_ratio": ratio,
        })
        processed += 1

    print(f"  Processed: {processed}, Skipped: {skipped}")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    journals = [target] if target else TARGET_JOURNALS

    rows = []
    for journal in journals:
        process_journal(journal, rows)

    if rows:
        out_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "journals", "_overall", "scores_whole"
        )
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, "all_whole_papers.csv")
        fieldnames = ["paper_id", "journal", "active", "passive", "total", "active_ratio"]
        with open(out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nSummary CSV: {out}")
        print(f"Total papers: {len(rows)}")


if __name__ == "__main__":
    main()
