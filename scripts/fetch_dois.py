# scripts/fetch_dois.py
# Queries Crossref for DOIs by journal ISSN and year.
# Filters to primary research articles using Crossref subtype + title heuristics.

import os
import time
import requests
import sys
from config import (
    TARGET_JOURNALS, JOURNAL_YEARS, PAPERS_PER_YEAR,
    journal_path, is_wiley_doi,
)

CROSSREF_BASE = "https://api.crossref.org/journals"
HEADERS = {"User-Agent": "VoiceAnalysisProject/1.0 (mailto:reganwhite@example.com)"}

# Crossref `subtype` values that indicate primary research
ALLOWED_SUBTYPES = {"original article", "research article", "research-article",
                    "article", "brief report", "short communication",
                    "rapid communication", "full-length article"}

# Crossref `subtype` values that mean "not a paper"
BLOCKED_SUBTYPES = {"editorial", "letter", "letter to the editor",
                    "correction", "erratum", "corrigendum", "retraction",
                    "book review", "commentary", "comment", "reply",
                    "review article", "review-article", "mini-review",
                    "perspective", "opinion", "viewpoint", "debate",
                    "abstract", "meeting abstract", "index", "front matter",
                    "back matter", "table of contents", "in memoriam",
                    "obituary", "news", "announcement", "addendum"}

# Title-based keyword excludes (fallback if subtype is missing)
EXCLUDE_TITLE_KEYWORDS = [
    "editorial", "erratum", "correction", "corrigendum", "retraction",
    "book review", "in memoriam", "obituary", "letter to the editor",
    "reply to", "comment on", "commentary on", "response to",
    "table of contents", "front matter", "back matter",
    "issue information", "cover image", "issue highlights",
    "author index", "subject index", "acknowledgment of reviewers",
    "list of reviewers", "reviewer list",
    "call for papers", "announcement", "news and views",
    "editor's note", "editors' note", "editorial board",
    "minireview", "perspective", "viewpoint", "opinion piece",
    "research highlights", "in this issue", "in the spotlight",
]


def is_likely_research_article(item):
    """Return True only if this Crossref item looks like a primary research article."""
    title = (item.get("title") or [""])[0] if item.get("title") else ""
    subtype = (item.get("subtype") or "").strip().lower()

    # 1. If subtype is known and blocked, exclude immediately
    if subtype in BLOCKED_SUBTYPES:
        return False

    # 2. If subtype is known and allowed, accept
    if subtype in ALLOWED_SUBTYPES:
        return True

    # 3. If subtype is unknown/empty, fall back to title heuristic
    if not title:
        return False  # no title at all → probably a fragment
    tl = title.lower()
    if any(kw in tl for kw in EXCLUDE_TITLE_KEYWORDS):
        return False
    # Titles with "correction", "erratum" etc. anywhere are excluded above
    # Titles under 15 chars are usually not research papers
    if len(title) < 15:
        return False
    return True


def fetch_dois_for_journal_year(issn, year, count):
    url = f"{CROSSREF_BASE}/{issn}/works"
    params = {
        "filter": f"from-pub-date:{year}-01-01,until-pub-date:{year}-12-31,type:journal-article",
        "rows": count * 5,   # ask for more since we filter aggressively
        "select": "DOI,title,subtype,type,subject",   # <-- pull subtype
        "mailto": "reganwhite@example.com",
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
        excluded_nonwiley = 0

        for it in items:
            doi = it.get("DOI", "")
            if not doi:
                continue
            if not is_wiley_doi(doi):
                excluded_nonwiley += 1
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
              f"non-Wiley={excluded_nonwiley})")
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
    target = sys.argv[1] if len(sys.argv) > 1 else None
    journals = [target] if target else list(TARGET_JOURNALS.keys())

    for journal in journals:
        print(f"\n=== {journal} ===")
        process_journal(journal)


if __name__ == "__main__":
    main()
