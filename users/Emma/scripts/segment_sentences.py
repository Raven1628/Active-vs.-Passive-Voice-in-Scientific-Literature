# scripts/segment_sentences.py
# Uses spaCy to split cleaned sections into sentences.

import os
import json
import sys
import spacy
from tqdm import tqdm
from config import (
    TARGET_JOURNALS, journal_path, ensure_journal_folders,
    CLEANED_SUBDIR, SENTENCES_SUBDIR, MIN_SENTENCE_WORDS,
)

# Load spaCy model (small, fast)
nlp = spacy.load("en_core_web_sm")


def segment(text):
    """Split text into sentences, filter out short ones."""
    if not text:
        return []
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    sentences = [s for s in sentences if len(s.split()) >= MIN_SENTENCE_WORDS]
    return sentences


def process_journal(journal):
    ensure_journal_folders(journal)
    src = journal_path(journal, CLEANED_SUBDIR)
    dst = journal_path(journal, SENTENCES_SUBDIR)

    if not os.path.exists(src):
        print(f"\n=== {journal} ===")
        print(f"  No cleaned folder found. Skipping.")
        return

    cleaned_files = sorted([f for f in os.listdir(src) if f.endswith(".json")])
    print(f"\n=== {journal} ===")
    print(f"  Found {len(cleaned_files)} cleaned files")

    if not cleaned_files:
        return

    processed = skipped = failed = 0
    total_sentences = 0

    for filename in tqdm(cleaned_files, desc=f"  {journal}"):
        paper_id = filename.replace(".json", "")
        output_path = os.path.join(dst, f"{paper_id}.json")

        if os.path.exists(output_path):
            skipped += 1
            continue

        try:
            with open(os.path.join(src, filename)) as f:
                data = json.load(f)

            # Skip flagged papers
            if data.get("_skip"):
                with open(output_path, "w") as f:
                    json.dump({"_skip": True, "paper_id": paper_id, "journal": journal}, f, indent=2)
                skipped += 1
                continue

            result = {
                "paper_id": paper_id,
                "journal": journal,
            }
            for section in ["introduction", "methods", "results", "discussion"]:
                text = data.get(section)
                result[section] = segment(text)

            if data.get("_combined_sections"):
                result["_combined_sections"] = data["_combined_sections"]

            with open(output_path, "w") as f:
                json.dump(result, f, indent=2)

            total_sentences += sum(len(result[s]) for s in
                                    ["introduction", "methods", "results", "discussion"])
            processed += 1

        except Exception as e:
            print(f"\n    FAILED: {paper_id} — {e}")
            failed += 1

    print(f"  Processed: {processed}, Skipped: {skipped}, Failed: {failed}")
    print(f"  Total sentences across processed papers: {total_sentences}")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    journals = [target] if target else TARGET_JOURNALS

    for journal in journals:
        process_journal(journal)


if __name__ == "__main__":
    main()
