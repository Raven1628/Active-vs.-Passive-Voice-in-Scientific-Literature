# scripts/classify_whole.py
# Classifies each sentence in the whole-paper body as ACTIVE or PASSIVE.

import os
import json
import sys
import spacy
from tqdm import tqdm
from config import (
    TARGET_JOURNALS, journal_path, ensure_journal_folders,
    SENTENCES_WHOLE_SUBDIR, CLASSIFICATIONS_WHOLE_SUBDIR,
    SPACY_MODEL,
)

nlp = spacy.load(SPACY_MODEL)


def classify_sentence(sent_text):
    doc = nlp(sent_text)
    for token in doc:
        if token.dep_ in ("nsubjpass", "auxpass"):
            return "PASSIVE"
    return "ACTIVE"


def process_journal(journal):
    ensure_journal_folders(journal)
    src = journal_path(journal, SENTENCES_WHOLE_SUBDIR)
    dst = journal_path(journal, CLASSIFICATIONS_WHOLE_SUBDIR)

    if not os.path.exists(src):
        print(f"\n=== {journal} ===\n  No sentences_whole folder. Skipping.")
        return

    files = sorted(f for f in os.listdir(src) if f.endswith(".json"))
    print(f"\n=== {journal} ===\n  Found {len(files)} sentence files")

    processed = skipped = failed = 0
    for filename in tqdm(files, desc=f"  {journal}"):
        out_path = os.path.join(dst, filename)
        if os.path.exists(out_path):
            skipped += 1
            continue

        with open(os.path.join(src, filename)) as f:
            data = json.load(f)

        if data.get("_skip"):
            with open(out_path, "w") as f:
                json.dump({"_skip": True, "paper_id": data.get("paper_id"),
                           "journal": journal}, f, indent=2)
            skipped += 1
            continue

        try:
            labels = []
            for sent in data.get("sentences", []):
                labels.append({"sentence": sent, "label": classify_sentence(sent)})
            result = {
                "paper_id": data.get("paper_id"),
                "journal": journal,
                "classifications": labels,
                "num_sentences": len(labels),
            }
            with open(out_path, "w") as f:
                json.dump(result, f, indent=2)
            processed += 1
        except Exception as e:
            print(f"    FAILED: {filename} — {e}")
            failed += 1

    print(f"  Processed: {processed}, Skipped: {skipped}, Failed: {failed}")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    journals = [target] if target else TARGET_JOURNALS
    for journal in journals:
        process_journal(journal)


if __name__ == "__main__":
    main()
