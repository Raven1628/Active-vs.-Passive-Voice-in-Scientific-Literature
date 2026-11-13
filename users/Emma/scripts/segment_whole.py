# scripts/segment_whole.py
# Tokenizes the whole-paper body into sentences.

import os
import re
import json
import sys
from tqdm import tqdm
from config import (
    TARGET_JOURNALS, journal_path, ensure_journal_folders,
    WHOLE_PAPERS_SUBDIR, SENTENCES_WHOLE_SUBDIR, MIN_SENTENCE_WORDS,
)

# Sentence splitter: break on . ! ? followed by space+capital or end of string.
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")


def split_sentences(text):
    if not text:
        return []
    raw = SENT_SPLIT.split(text)
    out = []
    for s in raw:
        s = s.strip()
        if len(s.split()) >= MIN_SENTENCE_WORDS:
            out.append(s)
    return out


def process_journal(journal):
    ensure_journal_folders(journal)
    src = journal_path(journal, WHOLE_PAPERS_SUBDIR)
    dst = journal_path(journal, SENTENCES_WHOLE_SUBDIR)

    if not os.path.exists(src):
        print(f"\n=== {journal} ===\n  No whole_papers folder. Skipping.")
        return

    files = sorted(f for f in os.listdir(src) if f.endswith(".json"))
    print(f"\n=== {journal} ===\n  Found {len(files)} whole-paper files")

    processed = skipped = 0
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

        sentences = split_sentences(data.get("text", ""))
        result = {
            "paper_id": data.get("paper_id"),
            "journal": journal,
            "sentences": sentences,
            "num_sentences": len(sentences),
        }
        if len(sentences) < 20:
            result["_skip"] = True
            result["_reason"] = "too few sentences"

        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        processed += 1

    print(f"  Processed: {processed}, Skipped: {skipped}")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    journals = [target] if target else TARGET_JOURNALS
    for journal in journals:
        process_journal(journal)


if __name__ == "__main__":
    main()
