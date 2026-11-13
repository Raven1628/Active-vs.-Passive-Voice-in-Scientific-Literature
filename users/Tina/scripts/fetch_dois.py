# fetch_dois.py - OUP version. DOIs must start with 10.1093/
import os
import time
import requests
from config import (
    TARGET_JOURNALS, JOURNAL_YEARS, PAPERS_PER_YEAR,
    journal_path, is_target_doi,
)

CROSSREF_BASE = "https://api.crossref.org/journals"
HEADERS = {"User-Agent": "VoiceAnalysisProject/1.0 (mailto:doilist39@gmail.com)"}

BLOCKED_SUBTYPES = {
    "editorial", "letter", "letter to the editor", "correction",
    "erratum", "corrigendum", "retraction", "book review", "commentary",
    "comment", "reply", "review article", "review-article", "mini-review",
    "perspective", "opinion", "viewpoint", "debate", "abstract",
    "meeting abstract", "index", "front matter", "back matter",
    "table of contents", "in memoriam", "obituary", "news",
    "announcement", "addendum",
}

def is_likely_research_article(item):
    """Filter to actual original research papers.

    Two heuristics are applied to catch editorials/commentaries:
      - page span < 3 pages
      - references-count < 15

    But both were calibrated on modern papers. For pre-2010 papers, Crossref
    often has no subtype, no references-count, and short-format research
    articles (Applications Notes, etc.) that span only 2-3 pages. So:
      - If subtype is missing, skip the length heuristics entirely (title
        blacklist still applies)
      - For reference-count, only reject when the count is explicitly in
        (0, 15) — 0 or None means "metadata missing", not "editorial"
    """
    subtype = (item.get("subtype") or "").strip().lower()

    title = (item.get("title") or [""])[0].strip()
    title_lower = title.lower()

    # --- Title blacklist (always applied) ---
    blocked_prefixes = (
        "correction", "corrigendum", "erratum", "retraction",
        "editorial", "reply", "response", "comment on", "commentary on",
        "letter", "letters", "in this issue", "in memoriam",
        "obituary", "book review", "review of", "proceedings of",
        "abstracts from", "issue information", "front matter", "back matter",
        "editor's choice", "highlights from", "correction to:",
        "erratum to:", "corrigendum to:", "retraction to:",
    )
    if any(title_lower.startswith(p) for p in blocked_prefixes):
        return False

    blocked_anywhere = (
        "corrigendum", "erratum to", "correction to", "retraction to",
        "table of contents", "in memoriam",
    )
    if any(w in title_lower for w in blocked_anywhere):
        return False

    # --- Pre-2010 papers: skip length heuristics ---
    if not subtype:
        return True

    # --- Page span check (modern papers only) ---
    page = (item.get("page") or "").strip()
    if page:
        if "-" in page:
            try:
                s, e = page.split("-", 1)
                sn = int(''.join(c for c in s if c.isdigit()) or 0)
                en = int(''.join(c for c in e if c.isdigit()) or 0)
                if (en - sn) < 3:
                    return False
            except (ValueError, AttributeError):
                pass
        else:
            digits = ''.join(c for c in page if c.isdigit())
            if digits and len(digits) <= 4:
                return False

    # --- Reference-count check (only if explicitly small but nonzero) ---
    ref_count = item.get("references-count")
    if ref_count is not None:
        try:
            n = int(ref_count)
            if 0 < n < 15:
                return False
        except (ValueError, TypeError):
            pass

    return True

def fetch_dois_for_journal_year(issn, year, count):
    url = f"{CROSSREF_BASE}/{issn}/works"
    params = {
        "filter": f"from-pub-date:{year}-01-01,until-pub-date:{year}-12-31,type:journal-article",
        "rows": count * 5,
        "mailto": "doilist39@gmail.com",
    }
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            print(f"    HTTP {r.status_code}")
            return []
        return r.json().get("message", {}).get("items", [])
    except Exception as e:
        print(f"    error: {e}")
        return []

def process_journal(journal):
    issn = TARGET_JOURNALS[journal]
    years = JOURNAL_YEARS.get(journal, [])
    dois_file = os.path.join(journal_path(journal), "dois.txt")
    all_dois = []
    per_year = {}

    for year in years:
        print(f"  {journal} {year}...", end=" ")
        items = fetch_dois_for_journal_year(issn, year, PAPERS_PER_YEAR)
        kept = []
        excluded_subtype = 0
        excluded_title = 0
        excluded_offpublisher = 0

        for it in items:
            doi = it.get("DOI", "")
            if not doi:
                continue
            if not is_target_doi(doi):
                excluded_offpublisher += 1
                continue
            if not is_likely_research_article(it):
                if (it.get("subtype") or "").strip().lower() in BLOCKED_SUBTYPES:
                    excluded_subtype += 1
                else:
                    excluded_title += 1
                continue
            kept.append(doi)
            if len(kept) >= PAPERS_PER_YEAR:
                break

        per_year[year] = len(kept)
        print(f"kept {len(kept)}  "
              f"(excl: subtype={excluded_subtype}, title={excluded_title}, "
              f"off-publisher={excluded_offpublisher})")
        all_dois.extend(kept)
        time.sleep(1)

    seen = set()
    unique = []
    for d in all_dois:
        if d not in seen:
            seen.add(d)
            unique.append(d)

    with open(dois_file, "w") as f:
        f.write("\n".join(unique))

    print(f"  Wrote {len(unique)} DOIs to {dois_file}")
    print(f"  Per-year breakdown:")
    for year, count in per_year.items():
        print(f"    {year}: {count}")

def main():
    print(f"Fetching DOIs for {len(TARGET_JOURNALS)} journals")
    print(f"Target: {PAPERS_PER_YEAR} papers per journal-year")
    print()
    for journal in TARGET_JOURNALS:
        print(f"=== {journal} (ISSN {TARGET_JOURNALS[journal]}) ===")
        process_journal(journal)
        print()

if __name__ == "__main__":
    main()
