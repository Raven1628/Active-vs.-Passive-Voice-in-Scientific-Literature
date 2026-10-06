# scripts/check_papers.py
# Heuristic check: is each raw_text file a real research paper?
# Usage:
#   python check_papers.py                 # all journals, summary only
#   python check_papers.py Cancer          # one journal
#   python check_papers.py Cancer --verbose  # per-paper detail

import os
import re
import sys
import json
from collections import Counter
from config import TARGET_JOURNALS, journal_path, RAW_TEXT_SUBDIR

# ---------- thresholds ----------
MIN_CHARS = 1500            # research papers are rarely under 3k chars
MIN_WORDS = 300
MIN_SENTENCES = 12
MIN_ALPHA_RATIO = 0.45      # at least 55% of chars should be letters
MAX_DIGIT_RATIO = 0.35      # more than 25% digits suggests tables/references
MIN_UNIQUE_WORD_RATIO = 0.10  # low unique ratio = repeated boilerplate

# ---------- markers that suggest a real paper ----------
PAPER_MARKERS = [
    r"\babstract\b",
    r"\bintroduction\b",
    r"\bbackground\b",
    r"\bmethods?\b",
    r"\bmaterials?\s+and\s+methods?\b",
    r"\bresults?\b",
    r"\bdiscussion\b",
    r"\bconclusions?\b",
    r"\breferences?\b",
    r"\bwe\s+(?:report|present|describe|show|found|observed|analyzed|examined)\b",
    r"\bthis\s+study\b",
    r"\bthese\s+(?:data|results|findings)\b",
]
PAPER_MARKER_RE = re.compile("|".join(PAPER_MARKERS), re.IGNORECASE)

# ---------- markers that suggest a non-paper ----------
NON_PAPER_MARKERS = [
    r"\berratum\b", r"\bcorrigendum\b", r"\bcorrection\b",
    r"\beditorial\b", r"\bobituary\b", r"\bbook\s+review\b",
    r"\bletter\s+to\s+the\s+editor\b", r"\bin\s+memoriam\b",
    r"\btable\s+of\s+contents\b", r"\bvolume\s+\d+,\s+issue\b",
    r"^\s*abstract\s+not\s+available\s*$",
    r"\bpublished\s+online\b.*\bcopyright\b",
]
NON_PAPER_RE = re.compile("|".join(NON_PAPER_MARKERS), re.IGNORECASE | re.MULTILINE)

# ---------- page header pattern (repeated "Journal Name Vol X page Y") ----------
PAGE_HEADER_RE = re.compile(
    r"^\s*[A-Z][A-Za-z\s]+\s+\d{4}\s+\d+\s+\d+\s*$",
    re.MULTILINE,
)


def check_paper(text):
    """
    Return (is_paper: bool, reasons: list[str], stats: dict).
    is_paper is True only if no hard-fail reasons are found.
    """
    reasons = []
    stats = {}

    if not text:
        return False, ["empty text"], {"chars": 0}

    stats["chars"] = len(text)
    words = text.split()
    stats["words"] = len(words)

    if stats["chars"] < MIN_CHARS:
        reasons.append(f"too short ({stats['chars']} chars < {MIN_CHARS})")
    if stats["words"] < MIN_WORDS:
        reasons.append(f"too few words ({stats['words']} < {MIN_WORDS})")

    # Alpha ratio
    alpha = sum(1 for c in text if c.isalpha())
    digit = sum(1 for c in text if c.isdigit())
    stats["alpha_ratio"] = alpha / stats["chars"]
    stats["digit_ratio"] = digit / stats["chars"]
    if stats["alpha_ratio"] < MIN_ALPHA_RATIO:
        reasons.append(f"low alpha ratio ({stats['alpha_ratio']:.2f} < {MIN_ALPHA_RATIO})")
    if stats["digit_ratio"] > MAX_DIGIT_RATIO:
        reasons.append(f"high digit ratio ({stats['digit_ratio']:.2f} > {MAX_DIGIT_RATIO})")

    # Unique word ratio — repeated boilerplate gives low unique ratio
    lower_words = [w.lower() for w in words if w.isalpha()]
    stats["unique_ratio"] = len(set(lower_words)) / max(len(lower_words), 1)
    if stats["unique_ratio"] < MIN_UNIQUE_WORD_RATIO:
        reasons.append(f"low unique word ratio ({stats['unique_ratio']:.2f} < {MIN_UNIQUE_WORD_RATIO})")

    # Sentence count
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if len(s.split()) >= 5]
    stats["sentences"] = len(sentences)
    if stats["sentences"] < MIN_SENTENCES:
        reasons.append(f"too few sentences ({stats['sentences']} < {MIN_SENTENCES})")

    # Paper markers present?
    marker_hits = len(set(m.group(0).lower() for m in PAPER_MARKER_RE.finditer(text)))
    stats["paper_markers"] = marker_hits
    if marker_hits < 2:
        reasons.append(f"few paper markers ({marker_hits} < 3)")

    # Non-paper markers
    non_paper_hits = NON_PAPER_RE.findall(text)
    if non_paper_hits:
        stats["non_paper_markers"] = list(set(non_paper_hits))
        reasons.append(f"non-paper markers: {stats['non_paper_markers']}")

    # Page-header spam: many lines that look like "Journal Year Page"
    header_lines = PAGE_HEADER_RE.findall(text)
    header_ratio = len(header_lines) / max(len(text.splitlines()), 1)
    stats["page_header_ratio"] = header_ratio
    if header_ratio > 0.10:
        reasons.append(f"page header spam ({header_ratio:.2f})")

    # Repeated-sentence check: any sentence appears >3 times = boilerplate
    if sentences:
        sent_counts = Counter(s.strip().lower() for s in sentences)
        top_count = sent_counts.most_common(1)[0][1]
        stats["max_repeat"] = top_count
        if top_count > 8:
            reasons.append(f"repeated sentence x{top_count}")

    is_paper = len(reasons) == 0
    return is_paper, reasons, stats


def process_journal(journal, verbose=False):
    src = journal_path(journal, RAW_TEXT_SUBDIR)
    if not os.path.exists(src):
        print(f"\n=== {journal} ===\n  No raw_text folder.")
        return [], []

    files = sorted(f for f in os.listdir(src) if f.endswith(".json"))
    print(f"\n=== {journal} ===\n  {len(files)} files")

    good, bad = [], []
    reason_tally = Counter()

    for filename in files:
        paper_id = filename.replace(".json", "")
        with open(os.path.join(src, filename)) as f:
            data = json.load(f)
        text = data.get("text", "")

        is_paper, reasons, stats = check_paper(text)

        if is_paper:
            good.append(paper_id)
        else:
            bad.append((paper_id, reasons, stats))
            for r in reasons:
                key = r.split(" (")[0]  # strip numbers for tallying
                reason_tally[key] += 1
            if verbose:
                print(f"  FAIL {paper_id}: {', '.join(reasons)}")

    print(f"  OK: {len(good)}   FAIL: {len(bad)}")
    if reason_tally:
        print("  Top failure reasons:")
        for reason, n in reason_tally.most_common(8):
            print(f"    {n:4d}  {reason}")

    return good, bad


def main():
    args = [a for a in sys.argv[1:]]
    verbose = "--verbose" in args
    args = [a for a in args if a != "--verbose"]

    journals = [args[0]] if args else TARGET_JOURNALS
    if isinstance(journals, str):
        journals = [journals]

    total_good = total_bad = 0
    all_good = []
    all_bad = []

    for journal in journals:
        good, bad = process_journal(journal, verbose=verbose)
        total_good += len(good)
        total_bad += len(bad)
        all_good.extend((journal, pid) for pid in good)
        all_bad.extend((journal, pid, rs) for pid, rs, _ in bad)

    print(f"\n{'='*60}\nOVERALL\n{'='*60}")
    print(f"  Total OK:   {total_good}")
    print(f"  Total FAIL: {total_bad}")
    print(f"  Total:      {total_good + total_bad}")

    # Save the good/bad lists
    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "journals", "_overall"
    )
    os.makedirs(out_dir, exist_ok=True)

    import csv
    with open(os.path.join(out_dir, "paper_check_good.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["journal", "paper_id"])
        w.writerows(all_good)

    with open(os.path.join(out_dir, "paper_check_bad.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["journal", "paper_id", "reasons"])
        for j, pid, rs in all_bad:
            w.writerow([j, pid, "; ".join(rs)])

    print(f"\n  Wrote: journals/_overall/paper_check_good.csv")
    print(f"  Wrote: journals/_overall/paper_check_bad.csv")


if __name__ == "__main__":
    main()
