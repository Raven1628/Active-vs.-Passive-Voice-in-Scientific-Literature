# scripts/classify_voice.py
# Classifies each sentence as ACTIVE or PASSIVE using spaCy dependency parsing.
# No API calls, no rate limits, deterministic.

import os
import json
import sys
import spacy
from tqdm import tqdm
from config import (
    TARGET_JOURNALS, journal_path, ensure_journal_folders,
    SENTENCES_SUBDIR, CLASSIFICATIONS_SUBDIR,
)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")


def classify_sentence(doc):
    """
    Classify a spaCy Doc as ACTIVE or PASSIVE.
    Returns 'PASSIVE' if any of these hold:
      - a token with dependency label 'nsubjpass' (passive nominal subject)
      - a token with dependency label 'auxpass' (passive auxiliary)
    Otherwise 'ACTIVE'.
    """
    for token in doc:
        if token.dep_ in ("nsubjpass", "auxpass"):
            return "PASSIVE"
    return "ACTIVE"


def classify_text(text):
    """Classify every sentence in a text block."""
    if not text:
        return []
    doc = nlp(text)
    results = []
    for sent in doc.sents:
        sentence_text = sent.text.strip()
        if len(sentence_text.split()) < 5:
            continue
        label = classify_sentence(sent)
        results.append({"sentence": sentence_text, "label": label})
    return results


def process_journal(journal):
    ensure_journal_folders(journal)
    src = journal_path(journal, SENTENCES_SUBDIR)
    dst = journal_path(journal, CLASSIFICATIONS_SUBDIR)

    if not os.path.exists(src):
        print(f"\n=== {journal} ===")
        print(f"  No sentences folder found. Skipping.")
        return

    sentence_files = sorted([f for f in os.listdir(src) if f.endswith(".json")])
    print(f"\n=== {journal} ===")
    print(f"  Found {len(sentence_files)} sentence files")

    if not sentence_files:
        return

    processed = skipped = failed = 0
    total_sentences = 0

    for filename in tqdm(sentence_files, desc=f"  {journal}"):
        paper_id = filename.replace(".json", "")
        output_path = os.path.join(dst, f"{paper_id}.json")

        if os.path.exists(output_path):
            skipped += 1
            continue

        with open(os.path.join(src, filename)) as f:
            sentences_data = json.load(f)

        # Skip flagged papers
        if sentences_data.get("_skip"):
            with open(output_path, "w") as f:
                json.dump({"_skip": True, "paper_id": paper_id, "journal": journal}, f, indent=2)
            skipped += 1
            continue

        try:
            result = {
                "paper_id": paper_id,
                "journal": journal,
            }
            if sentences_data.get("_combined_sections"):
                result["_combined_sections"] = sentences_data["_combined_sections"]

            for section in ["introduction", "methods", "results", "discussion"]:
                sentences = sentences_data.get(section, [])
                section_results = []
                for sent in sentences:
                    # Re-parse just this sentence to keep it simple
                    doc = nlp(sent)
                    label = classify_sentence(doc)
                    section_results.append({"sentence": sent, "label": label})
                result[section] = section_results
                total_sentences += len(section_results)

            with open(output_path, "w") as f:
                json.dump(result, f, indent=2)
            processed += 1

        except Exception as e:
            print(f"\n    FAILED: {paper_id} — {e}")
            failed += 1

    print(f"\n  Processed: {processed}, Skipped: {skipped}, Failed: {failed}")
    print(f"  Sentences classified: {total_sentences}")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    journals = [target] if target else TARGET_JOURNALS

    for journal in journals:
        process_journal(journal)


if __name__ == "__main__":
    main()
