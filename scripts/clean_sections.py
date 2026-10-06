# scripts/clean_sections.py
# Removes non-literary elements from each section using regex.

import os
import re
import json
import sys
from tqdm import tqdm
from config import (
    TARGET_JOURNALS, journal_path, ensure_journal_folders,
    SECTIONS_SUBDIR, CLEANED_SUBDIR,
)

# ---------- REGEX PATTERNS ----------
CITATION_PATTERNS = [
    r"\([A-Z][a-z]+(?:\s+(?:and|&)\s+[A-Z][a-z]+)?(?:\s+et\s+al\.)?,?\s+\d{4}[a-z]?\)",
    r"\([A-Z][a-z]+\s+et\s+al\.,\s+\d{4}\)",
    r"\b[A-Z][a-z]+\s+et\s+al\.,?\s+\d{4}\b",
    r"\([A-Z][a-z]+\s+\d{4}\)",
    r"\b[A-Z][a-z]+\s+\(\d{4}\)",
]

FIGURE_PATTERNS = [
    r"\bFigure\s+\d+[A-Z]?\b",
    r"\bFig\.\s*\d+[A-Z]?\b",
    r"\bTable\s+\d+[A-Z]?\b",
    r"\bFigure\s+S\d+[A-Z]?\b",
    r"\bAppendix\s+[A-Z0-9]+\b",
    r"\bEq\.\s*\d+\b",
    r"\bEquation\s+\d+\b",
]

STATS_PATTERNS = [
    r"\bp\s*[<>=]\s*0?\.\d+\b",
    r"\bn\s*=\s*\d+\b",
    r"\([F|t|χ²|U|r|R²]\s*\([^)]+\)\s*=\s*[\d.]+[^)]*\)",
]

REFERENCE_MARKERS = [
    r"\[\d+(?:[,-]\d+)*\]",
]


def remove_non_literary(text):
    for pattern_list in [CITATION_PATTERNS, FIGURE_PATTERNS, STATS_PATTERNS, REFERENCE_MARKERS]:
        for pattern in pattern_list:
            text = re.sub(pattern, "", text)
    # Clean up whitespace
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,;:])", r"\1", text)
    text = re.sub(r"\(\s*\)", "", text)
    text = text.strip()
    return text


def process_journal(journal):
    ensure_journal_folders(journal)
    src = journal_path(journal, SECTIONS_SUBDIR)
    dst = journal_path(journal, CLEANED_SUBDIR)

    if not os.path.exists(src):
        print(f"\n=== {journal} ===")
        print(f"  No sections folder found. Skipping.")
        return

    section_files = sorted([f for f in os.listdir(src) if f.endswith(".json")])
    print(f"\n=== {journal} ===")
    print(f"  Found {len(section_files)} section files")

    if not section_files:
        return

    processed = skipped = failed = 0

    for filename in tqdm(section_files, desc=f"  {journal}"):
        paper_id = filename.replace(".json", "")
        output_path = os.path.join(dst, f"{paper_id}.json")

        if os.path.exists(output_path):
            skipped += 1
            continue

        try:
            with open(os.path.join(src, filename)) as f:
                data = json.load(f)

            # Skip papers flagged as incomplete
            if data.get("_skip"):
                with open(output_path, "w") as f:
                    json.dump({"_skip": True, "paper_id": paper_id, "journal": journal}, f, indent=2)
                skipped += 1
                continue

            cleaned = {
                "paper_id": paper_id,
                "journal": journal,
            }
            for section in ["introduction", "methods", "results", "discussion"]:
                text = data.get(section)
                cleaned[section] = remove_non_literary(text) if text else None

            if data.get("_combined_sections"):
                cleaned["_combined_sections"] = data["_combined_sections"]

            with open(output_path, "w") as f:
                json.dump(cleaned, f, indent=2)
            processed += 1

        except Exception as e:
            print(f"\n    FAILED: {paper_id} — {e}")
            failed += 1

    print(f"  Processed: {processed}, Skipped: {skipped}, Failed: {failed}")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    journals = [target] if target else TARGET_JOURNALS

    for journal in journals:
        process_journal(journal)


if __name__ == "__main__":
    main()
