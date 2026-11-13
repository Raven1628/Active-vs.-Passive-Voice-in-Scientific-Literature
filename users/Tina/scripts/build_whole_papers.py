# scripts/build_whole_papers.py
# Reads raw_text/<paper>.json and writes a cleaned whole-paper body.
# Aggressive cleaning: strips front matter, figure/table captions, inline citations,
# references, and acknowledgments. Also detects and filters out non-research
# articles (reviews, letters, editorials, corrections) to keep only original research.

import os
import re
import json
import sys
from tqdm import tqdm
from config import (
    TARGET_JOURNALS, journal_path, ensure_journal_folders,
    RAW_TEXT_SUBDIR, WHOLE_PAPERS_SUBDIR,
)

# ============================================================================
# SECTION 1: Article type detection (banner + structural fallback)
# ============================================================================
# Strategy:
#   1. Check first 500 chars for a non-research banner (review, editorial,
#      letter, memoriam, commentary, announcement, short report). If matched →
#      return that type (skip).
#   2. If no non-research banner, check for structural markers that identify a
#      research article: Abstract heading, Introduction heading, or IMRaD-style
#      headings (Methods, Results, Discussion, Conclusions). If found →
#      return "research" (keep).
#   3. If neither banner nor structure matches → return "unknown" (flag for
#      hand-check; do NOT silently include).

NON_RESEARCH_PATTERNS = [
    ("review", r"(?im)^[ \t]*(?:review(?:\s+article)?|minireview|"
               r"invited\s+review)\s*$"),
    ("short_report", r"(?im)^[ \t]*(?:short\s+report|brief\s+report|"
                     r"short\s+communication|brief\s+communication|"
                     r"technical\s+note|research\s+letter)\s*$"),
    ("editorial", r"(?im)^[ \t]*editorial\s*$"),
    ("letter", r"(?im)^[ \t]*(?:letter\s+to\s+the\s+editor|"
               r"correspondence|letter)\s*$"),
    ("memoriam", r"(?im)^[ \t]*(?:in\s+memoriam|memoriam)\s*$"),
    ("commentary", r"(?im)^[ \t]*(?:commentary|perspective|opinion|"
                   r"viewpoint)\s*$"),
    ("announcement", r"(?im)^[ \t]*announcement\s*$"),
]

# Structural markers that identify a research article
ABSTRACT_PATTERN = re.compile(
    r"(?im)^[ \t]*(?:\d+\.?\s*)?(?:abstract|summary)\s*[:.]?\s*$"
)
INTRO_PATTERN = re.compile(
    r"(?im)^[ \t]*(?:\d+\.?\s*)?(?:introduction|background)\s*[:.]?\s*$"
)
IMRAD_PATTERN = re.compile(
    r"(?im)^[ \t]*(?:\d+\.?\s*)?"
    r"(?:methods?|materials\s+and\s+methods?|"
    r"results?|discussion|conclusions?|concluding\s+remarks?)"
    r"\s*[:.]?\s*$"
)
# Cancer-style inline abstract: BACKGROUND. / METHODS. / RESULTS. / CONCLUSIONS.
CANCER_STYLE_PATTERN = re.compile(
    r"(?im)^[ \t]*BACKGROUND[.:]\s"
)

def has_research_structure(text):
    """Return True if the text shows typical research article structure."""
    if not text:
        return False
    # Look at first 5000 chars — enough to catch the abstract and first headings
    head = text[:15000]
    # Cancer-style abstract is a strong signal
    if CANCER_STYLE_PATTERN.search(head):
        return True
    # Standard structure: Abstract + (Intro OR IMRaD heading)
    has_abstract = ABSTRACT_PATTERN.search(head) is not None
    has_intro = INTRO_PATTERN.search(head) is not None
    has_imrad = IMRAD_PATTERN.search(head) is not None
    if has_abstract and (has_intro or has_imrad):
        return True
    # Even without "Abstract", if we see both Introduction and IMRaD headings,
    # it's very likely a research paper.
    if has_intro and has_imrad:
        return True
    return False

def detect_article_type(text):
    """Return 'research', 'unknown', or one of the non-research types."""
    if not text:
        return "unknown"

    head = text[:500]

    # 1. Non-research banner?
    for label, pattern in NON_RESEARCH_PATTERNS:
        if re.search(pattern, head):
            return label

    # 2. Explicit research banner? (Article + Original Research variants)
    research_banner = re.compile(
        r"(?im)^[ \t]*(?:"
        r"original\s+research|"
        r"original\s+article|"
        r"original\s+paper|"
        r"research\s+article|"
        r"research\s+paper|"
        r"article"
        r")\s*$"
    )
    if research_banner.search(head):
        return "research"

    # 3. Structural evidence of research article?
    if has_research_structure(text):
        return "research"

    # 3. Can't tell — flag for hand-check
    return "unknown"

# ============================================================================
# SECTION 2: Body boundary detection
# ============================================================================

ABSTRACT_HEADING = re.compile(
    r"^[ \t]*(?:\d+\.?\s*)?(?:Abstract|ABSTRACT|Summary|SUMMARY)[\s:.]*$",
    re.MULTILINE,
)
CANCER_ABSTRACT_START = re.compile(
    r"^[ \t]*BACKGROUND[.:]\s",
    re.MULTILINE,
)
# Nature Comms: after the header block, body starts with the Introduction (unlabeled)
# Anchor: skip past "www.nature.com/naturecommunications" + blank line
NATURE_COMMS_START = re.compile(
    r"www\.nature\.com/naturecommunications[^\n]*\n[\s\S]{0,300}?\n\s*\n",
    re.MULTILINE,
)
FIRST_BODY_HEADING = re.compile(
    r"^[ \t]*(?:\d+\.?\s*)?"
    r"(?:Introduction|INTRODUCTION|Background|BACKGROUND|"
    r"Methods?|METHODS?|Materials?\s+and\s+Methods?|MATERIALS?\s+AND\s+METHODS?)"
    r"[\s:.]*$",
    re.MULTILINE,
)
REFERENCES_HEADING = re.compile(
    r"^[ \t]*(?:\d+\.?\s*)?"
    r"(?:References|REFERENCES|Reference|REFERENCE|"
    r"Literature\s+Cited|LITERATURE\s+CITED|"
    r"Bibliography|BIBLIOGRAPHY|"
    r"Works\s+Cited|WORKS\s+CITED|"
    r"References\s+Cited|REFERENCES\s+CITED)"
    r"[\s:.]*$",
    re.MULTILINE,
)
ACK_HEADING = re.compile(
    r"^[ \t]*(?:\d+\.?\s*)?"
    r"(?:Acknowledgments?|ACKNOWLEDGMENTS?|Acknowledgements?|ACKNOWLEDGEMENTS?|"
    r"Author\s+Contributions?|AUTHOR\s+CONTRIBUTIONS?|"
    r"Funding|FUNDING|Conflict\s+of\s+Interest|CONFLICT\s+OF\s+INTEREST)"
    r"[\s:.]*$",
    re.MULTILINE,
)

def find_prose_start(text, min_words=5):
    """Fallback: find first substantial prose line if no heading is found."""
    lines = text.split("\n")
    cumulative = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        cumulative += len(line) + 1
        if cumulative < 400:
            continue
        if not stripped:
            continue
        words = stripped.split()
        if len(words) < min_words:
            continue
        if not stripped[0].isupper():
            continue
        lowercase_words = sum(1 for w in words if w[0].islower())
        if lowercase_words < 2:
            continue
        return sum(len(l) + 1 for l in lines[:i])
    return None

def extract_body(text):
    """Return body text between abstract and references, or None."""
    if not text:
        return None

    abstract_match = ABSTRACT_HEADING.search(text)
    cancer_match = CANCER_ABSTRACT_START.search(text)
    nature_match = NATURE_COMMS_START.search(text)
    body_match = FIRST_BODY_HEADING.search(text)

    if abstract_match:
        body_start = abstract_match.end()
    elif cancer_match:
        body_start = cancer_match.start()
    elif nature_match:
        body_start = nature_match.end()
    elif body_match:
        body_start = body_match.start()
    else:
        body_start = find_prose_start(text)
        if body_start is None:
            return None

    ref_match = REFERENCES_HEADING.search(text, pos=body_start)
    ack_match = ACK_HEADING.search(text, pos=body_start)

    end_candidates = []
    if ref_match:
        end_candidates.append(ref_match.start())
    if ack_match:
        end_candidates.append(ack_match.start())

    body_end = min(end_candidates) if end_candidates else len(text)
    return text[body_start:body_end].strip()

# ============================================================================
# SECTION 3: Aggressive cleaning
# ============================================================================

INLINE_CITATION_PAREN = re.compile(r"\([^()]{0,80}?(?:19|20)\d{2}[a-z]?[^()]{0,40}?\)")
INLINE_CITATION_NUM = re.compile(r"\[\s*\d+(?:\s*[,\u2013-]\s*\d+)*\s*\]")
SUPERSCRIPT_GROUP = re.compile(r"[A-Za-z]([0-9]{1,2}(?:,[0-9]{1,2})+)(?=[\s.,])")

MIN_WORDS = 300

def clean_body(body):
    """Aggressive cleanup: figures, tables, citations, metadata."""
    if not body:
        return ""

    lines = body.split("\n")
    cleaned = []
    in_caption = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^(?:Figure|Fig\.?|Table)\s+\d+", stripped, re.IGNORECASE):
            in_caption = True
            continue
        if in_caption:
            if stripped and stripped[0].isupper() and stripped[-1] in ".?!" and len(stripped) > 40:
                in_caption = False
                cleaned.append(line)
            continue
        cleaned.append(line)
    body = "\n".join(cleaned)

    body = INLINE_CITATION_PAREN.sub("", body)
    body = INLINE_CITATION_NUM.sub("", body)
    body = SUPERSCRIPT_GROUP.sub(r"\1", body)

    drop_patterns = [
        re.compile(r"^\s*(?:doi|DOI|Published online|Received|Accepted|Revised|"
                   r"©|Copyright|First published|Edited by)\b", re.IGNORECASE),
        re.compile(r"^\s*\d+\s*$"),
        re.compile(r"^\s*www\.", re.IGNORECASE),
        re.compile(r"^\s*https?://"),
    ]
    filtered = [l for l in body.split("\n") if not any(p.match(l) for p in drop_patterns)]
    body = "\n".join(filtered)

    body = re.sub(r"-\n(?=[a-z])", "", body)
    body = re.sub(r"\n{2,}", "\n\n", body)
    body = re.sub(r"[ \t]{2,}", " ", body)
    return body.strip()

# ============================================================================
# SECTION 4: Journal processing
# ============================================================================

def process_journal(journal):
    ensure_journal_folders(journal)
    src = journal_path(journal, RAW_TEXT_SUBDIR)
    dst = journal_path(journal, WHOLE_PAPERS_SUBDIR)

    if not os.path.exists(src):
        print(f"\n=== {journal} ===\n  No raw_text folder. Skipping.")
        return

    files = sorted(f for f in os.listdir(src) if f.endswith(".json"))
    print(f"\n=== {journal} ===\n  Found {len(files)} raw text files")

    processed = skipped = too_short = non_research = 0
    orig_chars = clean_chars = 0

    for filename in tqdm(files, desc=f"  {journal}"):
        path = os.path.join(src, filename)
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            skipped += 1
            continue

        text = data.get("text", "")
        if not text:
            skipped += 1
            continue

        art_type = detect_article_type(text)
        # Only skip papers that are definitively non-research.
        # "unknown" papers get processed — the <20 sentence filter in
        # segment_whole.py will catch short non-research content.
        NON_RESEARCH_TYPES = {"review", "editorial", "letter", "correction",
                              "erratum", "retraction", "book_review",
                              "memoriam", "commentary", "announcement"}
        if art_type in NON_RESEARCH_TYPES:
            non_research += 1
            out_path = os.path.join(dst, filename)
            reason = f"non_research:{art_type}"
            with open(out_path, "w") as f:
                json.dump({
                    "paper_id": data.get("paper_id", filename.replace(".json", "")),
                    "journal": journal,
                    "_skip": True,
                    "_skip_reason": reason,
                    "article_type": art_type,
                }, f, indent=2)
            continue

        body = extract_body(text)
        if body is None:
            if len(text.split()) < MIN_WORDS:
                too_short += 1
            else:
                skipped += 1
            continue

        cleaned = clean_body(body)
        orig_chars += len(body)
        clean_chars += len(cleaned)

        if len(cleaned.split()) < MIN_WORDS:
            too_short += 1
            continue

        out_path = os.path.join(dst, filename)
        with open(out_path, "w") as f:
            json.dump({
                "paper_id": data.get("paper_id", filename.replace(".json", "")),
                "journal": journal,
                "article_type": art_type,
                "text": cleaned,
                "word_count": len(cleaned.split()),
                "original_char_count": len(body),
                "cleaned_char_count": len(cleaned),
            }, f, indent=2)
        processed += 1

    if orig_chars > 0:
        pct = 100 * (1 - clean_chars / orig_chars)
        print(f"  Processed: {processed}, Skipped: {skipped}, Too short: {too_short}, Non-research: {non_research}")
        print(f"  Removed {pct:.1f}% of body chars")
    else:
        print(f"  Processed: 0, Skipped: {skipped}, Too short: {too_short}, Non-research: {non_research}")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    journals = [target] if target else TARGET_JOURNALS
    for j in journals:
        process_journal(j)


if __name__ == "__main__":
    main()
