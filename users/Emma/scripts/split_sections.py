# scripts/split_sections.py
# Splits raw_text into IMRaD sections using flexible regex patterns,
# with positional inference for papers that omit the Introduction heading.

import os
import re
import json
import sys
from config import (
    TARGET_JOURNALS, journal_path, ensure_journal_folders,
    RAW_TEXT_SUBDIR, SECTIONS_SUBDIR, TARGET_SECTIONS,
)

# ---------------------------------------------------------------------------
# Heading patterns
# ---------------------------------------------------------------------------

INTRO_PATTERNS = [
    r"introduction",
    r"background",
    r"background\s+and\s+aims?",
    r"background\s+and\s+objectives?",
    r"background\s+and\s+significance",
    r"background\s+and\s+rationale",
    r"background\s+and\s+purpose",
    r"aims?\s+and\s+background",
    r"objectives?\s+and\s+background",
    r"introduction\s+and\s+background",
]

METHODS_PATTERNS = [
    r"methods?",
    r"materials?\s+and\s+methods?",     # matches "Material and methods" too
    r"methods?\s+and\s+materials?",
    r"patients?\s+and\s+methods?",
    r"subjects?\s+and\s+methods?",
    r"methodology",
    r"experimental\s+procedures?",
    r"study\s+design",
    r"methods?\s+and\s+study\s+design",
    r"participants?\s+and\s+methods?",
    r"data\s+and\s+methods?",
    r"sampling\s+and\s+methods?",
    r"material\s+and\s+methods?",       # explicit singular form
]

RESULTS_PATTERNS = [
    r"results?",
    r"findings?",
    r"results?\s+and\s+discussion",
]

DISCUSSION_PATTERNS = [
    r"discussion",
    r"discussion\s+and\s+conclusions?",
    r"conclusions?",
    r"summary\s+and\s+conclusions?",
]

_TAIL = r"[\s:.\d]*"

def _build_section_re(patterns):
    alts = "|".join(f"(?:{p})" for p in patterns)
    return re.compile(
        r"^[ \t]*(?:\d+(?:\.\d+)*\.?|[IVX]+\.?)?[ \t]*"
        + f"(?:{alts})"
        + _TAIL
        + r"$",
        re.IGNORECASE | re.MULTILINE,
    )

INTRO_RE = _build_section_re(INTRO_PATTERNS)
METHODS_RE = _build_section_re(METHODS_PATTERNS)
RESULTS_RE = _build_section_re(RESULTS_PATTERNS)
DISCUSSION_RE = _build_section_re(DISCUSSION_PATTERNS)
INTRODUCTION_PATTERN = INTRO_RE


# Abstract heading patterns — used to bound the inferred Introduction
ABSTRACT_RE = re.compile(
    r"^[ \t]*(?:Abstract|ABSTRACT|Summary|SUMMARY)[\s:.]*$",
    re.MULTILINE,
)

# Reference heading — anything after this is references, not Introduction
REFERENCES_RE = re.compile(
    r"^[ \t]*(?:References?|REFERENCES?|Bibliography|Literature\s+cited)"
    r"[\s:.]*$",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Section extraction
# ---------------------------------------------------------------------------

SECTION_RES = {
    "introduction": INTRO_RE,
    "methods": METHODS_RE,
    "results": RESULTS_RE,
    "discussion": DISCUSSION_RE,
}


def _find_headings(text):
    hits = []
    for section, rx in SECTION_RES.items():
        for m in rx.finditer(text):
            hits.append((m.start(), m.end(), section))
    hits.sort()
    return hits


def _body_after(text, hit, all_hits):
    _, end, _ = hit
    later = [h for h in all_hits if h[0] > end]
    body_end = later[0][0] if later else len(text)
    return text[end:body_end].strip()


def _looks_like_discussion_subsection(body):
    DISC_STARTS = (
        "in this study", "in the present study", "in this paper",
        "in this report", "here we", "in our study",
        "we have shown", "we show", "we found", "we report",
        "taken together", "in summary", "in conclusion",
        "the aim of this study", "this study aimed",
    )
    head = body[:200].lower().lstrip()
    return any(head.startswith(p) for p in DISC_STARTS)


def _infer_introduction(text, hits):
    """
    When no Introduction/Background heading is present, infer the
    Introduction as the text between the abstract and the first
    detected body heading (Methods or Results).

    If there is no abstract heading either, return None.
    """
    # Find end of abstract
    abs_matches = list(ABSTRACT_RE.finditer(text))
    if abs_matches:
        # Use the last abstract match (sometimes there's one in the header)
        abs_end = abs_matches[-1].end()
    else:
        # No abstract marker — fall back to start of text
        abs_end = 0

    # Find the first body heading (methods or results) after abstract
    body_headings = [h for h in hits if h[2] in ("methods", "results") and h[0] > abs_end]
    if not body_headings:
        return None

    first_body_start = min(h[0] for h in body_headings)

    # Also stop at References if present
    ref_match = REFERENCES_RE.search(text, abs_end)
    if ref_match and ref_match.start() < first_body_start:
        first_body_start = ref_match.start()

    intro_text = text[abs_end:first_body_start].strip()

    # Strip obvious front matter: lines that are pure author names,
    # affiliations, DOI, conflict-of-interest, etc.
    lines = intro_text.splitlines()
    cleaned_lines = []
    skip_until_blank = True
    for line in lines:
        s = line.strip()
        if not s:
            cleaned_lines.append("")
            skip_until_blank = False
            continue
        # Skip lines that look like author lists or affiliations
        if re.match(r"^[A-Z]\.\s*[A-Z][a-z]+", s):        # "C. Vanlerberghe..."
            continue
        if re.match(r"^[\w\.\-]+@", s):                    # email
            continue
        if re.match(r"^(doi|DOI|https?://)", s):
            continue
        if re.match(r"^(Conflict of interest|Con\ufb02ict of interest|Competing interests)", s, re.I):
            continue
        if re.match(r"^(Received|Accepted|Published|Revised)", s, re.I):
            continue
        if re.match(r"^\d+\s*$", s):                       # page numbers
            continue
        cleaned_lines.append(line)

    intro_text = "\n".join(cleaned_lines).strip()
    return intro_text if len(intro_text) > 200 else None


def extract_sections(full_text):
    sections = {
        "introduction": None,
        "methods": None,
        "results": None,
        "discussion": None,
    }

    hits = _find_headings(full_text)
    by_section = {sec: [] for sec in sections}
    for h in hits:
        by_section[h[2]].append(h)

    # Handle combined Results + Discussion
    combined = False
    for (start, end, sec) in hits:
        raw = full_text[start:end]
        if re.search(r"results?", raw, re.I) and re.search(r"discussion", raw, re.I):
            later = [h for h in hits if h[0] > end]
            body_end = later[0][0] if later else len(full_text)
            body = full_text[end:body_end].strip()
            sections["results"] = body
            sections["discussion"] = body
            sections["_combined_sections"] = ["results", "discussion"]
            combined = True
            break

    # Introduction — heading-based, else positional inference
    if by_section["introduction"]:
        candidates = [_body_after(full_text, h, hits) for h in by_section["introduction"]]
        clean = [c for c in candidates if c and not _looks_like_discussion_subsection(c)]
        pool = clean if clean else [c for c in candidates if c]
        if pool:
            sections["introduction"] = max(pool, key=len)
    if not sections["introduction"]:
        inferred = _infer_introduction(full_text, hits)
        if inferred:
            sections["introduction"] = inferred
            sections["_intro_inferred"] = True

    # Methods
    if by_section["methods"]:
        candidates = [_body_after(full_text, h, hits) for h in by_section["methods"]]
        candidates = [c for c in candidates if c]
        if candidates:
            sections["methods"] = max(candidates, key=len)

    # Results
    if not combined and by_section["results"]:
        candidates = [_body_after(full_text, h, hits) for h in by_section["results"]]
        candidates = [c for c in candidates if c]
        if candidates:
            sections["results"] = max(candidates, key=len)

    # Discussion
    if not combined and by_section["discussion"]:
        candidates = [_body_after(full_text, h, hits) for h in by_section["discussion"]]
        candidates = [c for c in candidates if c]
        if candidates:
            sections["discussion"] = max(candidates, key=len)

    return sections


# ---------------------------------------------------------------------------
# Journal processing
# ---------------------------------------------------------------------------

def process_journal(journal):
    ensure_journal_folders(journal)
    src = journal_path(journal, RAW_TEXT_SUBDIR)
    dst = journal_path(journal, SECTIONS_SUBDIR)

    if not os.path.exists(src):
        print(f"\n=== {journal} ===\n  No raw_text folder. Skipping.")
        return

    files = sorted(f for f in os.listdir(src) if f.endswith(".json"))
    print(f"\n=== {journal} ===\n  Found {len(files)} raw text files")

    processed = skipped_existing = 0
    skipped_papers = []

    for filename in files:
        paper_id = filename.replace(".json", "")
        out_path = os.path.join(dst, f"{paper_id}.json")

        if os.path.exists(out_path):
            skipped_existing += 1
            continue

        with open(os.path.join(src, filename)) as f:
            raw_data = json.load(f)

        if raw_data.get("_skip") or not raw_data.get("text"):
            with open(out_path, "w") as f:
                json.dump({"_skip": True, "paper_id": paper_id,
                           "journal": journal, "_reason": "empty raw_text"},
                          f, indent=2)
            skipped_papers.append(paper_id)
            continue

        try:
            sections = extract_sections(raw_data["text"])
        except Exception as e:
            print(f"    FAILED: {paper_id} — {e}")
            continue

        result = {"paper_id": paper_id, "journal": journal}
        for sec in TARGET_SECTIONS:
            result[sec] = sections.get(sec)
        if sections.get("_combined_sections"):
            result["_combined_sections"] = sections["_combined_sections"]
        if sections.get("_intro_inferred"):
            result["_intro_inferred"] = True

        missing = [s for s in TARGET_SECTIONS if not result.get(s)]
        if missing:
            result["_flagged"] = True
            result["_missing_sections"] = missing
            result["_skip"] = True
            skipped_papers.append(paper_id)

        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        processed += 1

    print(f"  Processed: {processed}, Skipped (already existed): {skipped_existing}")
    print(f"  Skipped (missing sections): {len(skipped_papers)}")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    journals = [target] if target else TARGET_JOURNALS
    for journal in journals:
        process_journal(journal)


if __name__ == "__main__":
    main()
