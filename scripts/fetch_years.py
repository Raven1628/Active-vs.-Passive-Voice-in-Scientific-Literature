# scripts/fetch_years.py
# Builds a permanent DOI -> year manifest.
# Priority:
#   1. Cache (journals/_overall/doi_years.csv)
#   2. Year parsed from the raw_papers PDF filename
#   3. Crossref API lookup

import os
import re
import sys
import csv
import time
import requests
from config import TARGET_JOURNALS, journal_path, RAW_TEXT_SUBDIR, RAW_PAPERS_SUBDIR

OUT = "/Users/reganwhite/Desktop/Scientific_Writing/Class_Project/journals/_overall/doi_years.csv"
HEADERS = {"User-Agent": "VoiceAnalysisProject/1.0 (mailto:reganwhite@example.com)"}


def paper_id_to_doi(paper_id):
    return paper_id.replace("_", "/", 1)


def year_from_filename(fname):
    """Extract a 4-digit year from various filename patterns."""
    # 'Ecology - 2015 - Castorani - ...'
    m = re.search(r" - (19|20)\d{2} - ", fname)
    if m:
        y = int(m.group(0).strip(" -"))
        if 1900 <= y <= 2050:
            return y
    # '(20050701)' - legacy Wiley DOI format
    m = re.search(r"\((\d{4})\d{4}\)", fname)
    if m:
        y = int(m.group(1))
        if 1900 <= y <= 2050:
            return y
    # '001-10.1890_05-0195.pdf' -> year is not encoded; skip
    return None


def find_pdf_for_paper(journal, paper_id):
    """Locate the PDF file corresponding to this paper_id in raw_papers."""
    rp_dir = journal_path(journal, RAW_PAPERS_SUBDIR)
    if not os.path.exists(rp_dir):
        return None
    for fname in os.listdir(rp_dir):
        if not fname.lower().endswith(".pdf"):
            continue
        # Direct match: paper_id appears in filename
        if paper_id in fname:
            return fname
    return None


def crossref_year(doi):
    url = f"https://api.crossref.org/works/{doi}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return None, f"http_{r.status_code}"
        data = r.json().get("message", {})
        for key in ("published-print", "published-online", "issued", "created"):
            parts = data.get(key, {}).get("date-parts")
            if parts and parts[0] and parts[0][0]:
                return parts[0][0], "ok"
        return None, "no_date_parts"
    except Exception:
        return None, "exception"


def load_cache():
    cache = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            for row in csv.DictReader(f):
                if row.get("year"):
                    cache[(row["journal"], row["paper_id"])] = {
                        "doi": row.get("doi", ""),
                        "year": row["year"],
                        "source": row.get("source", "cache"),
                    }
    return cache


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    journals = [target] if target else TARGET_JOURNALS

    cache = load_cache()
    print(f"Loaded {len(cache)} cached entries")

    rows = []
    stats = {"cache": 0, "filename": 0, "crossref": 0, "unknown": 0}

    for journal in journals:
        src = journal_path(journal, RAW_TEXT_SUBDIR)
        if not os.path.exists(src):
            continue
        files = sorted(f for f in os.listdir(src) if f.endswith(".json"))
        print(f"\n=== {journal} ({len(files)} papers) ===")

        for filename in files:
            paper_id = filename.replace(".json", "")
            key = (journal, paper_id)

            # 1. Cache
            if key in cache and cache[key].get("year"):
                rows.append({
                    "journal": journal,
                    "paper_id": paper_id,
                    "doi": cache[key]["doi"],
                    "year": cache[key]["year"],
                    "source": "cache",
                })
                stats["cache"] += 1
                continue

            doi = paper_id_to_doi(paper_id)
            year = None
            source = "unknown"

            # 2. Parse year from paper_id itself (works when paper_id is a descriptive filename)
            y = year_from_filename(paper_id)
            if y:
                year = y
                source = "paper_id"

            # 2b. Also try the actual PDF filename
            if not year:
                pdf = find_pdf_for_paper(journal, paper_id)
                if pdf:
                    y = year_from_filename(pdf)
                    if y:
                        year = y
                        source = "filename"

            # 3. Crossref
            if not year:
                y, status = crossref_year(doi)
                if y:
                    year = y
                    source = f"crossref:{status}"
                    time.sleep(0.3)  # be polite only when actually hitting the API

            if year:
                print(f"  {paper_id}  ->  {year}  ({source})")
                stats["filename" if source == "filename" else "crossref"] += 1
            else:
                print(f"  {paper_id}  ->  UNKNOWN")
                stats["unknown"] += 1

            rows.append({
                "journal": journal,
                "paper_id": paper_id,
                "doi": doi,
                "year": year or "",
                "source": source,
            })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["journal", "paper_id", "doi", "year", "source"])
        w.writeheader()
        w.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {OUT}")
    print(f"  cache hits: {stats['cache']}")
    print(f"  from filename: {stats['filename']}")
    print(f"  from Crossref: {stats['crossref']}")
    print(f"  unknown: {stats['unknown']}")


if __name__ == "__main__":
    main()
