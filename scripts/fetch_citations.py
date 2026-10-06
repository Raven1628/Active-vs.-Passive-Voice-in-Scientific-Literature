# scripts/fetch_citations.py
# Fetches citation counts from OpenAlex for every paper in master.csv.
# DOIs are resolved from doi_years.csv (authoritative) rather than derived
# from paper_id (which is a descriptive filename for some Ecology papers).
# Saves incrementally so interruptions don't lose progress.

import os
import csv
import time
import requests

BASE = "/Users/reganwhite/Desktop/Scientific_Writing/Class_Project"
ANALYSIS = os.path.join(BASE, "analysis")
MASTER = os.path.join(ANALYSIS, "master.csv")
DOI_YEARS = os.path.join(BASE, "journals", "_overall", "doi_years.csv")
OUT = os.path.join(BASE, "journals", "_overall", "citations.csv")
HEADERS = {"User-Agent": "VoiceAnalysisProject/1.0 (mailto:reganwhite@example.com)"}

RETRIEVAL_YEAR = 2026
FIELDNAMES = ["journal", "paper_id", "doi", "year", "years_since",
              "citations_total", "citations_per_year", "source"]


def load_doi_map():
    """Return {(journal, paper_id): doi} from doi_years.csv."""
    m = {}
    if os.path.exists(DOI_YEARS):
        with open(DOI_YEARS) as f:
            for row in csv.DictReader(f):
                doi = (row.get("doi") or "").strip()
                if doi:
                    m[(row["journal"], row["paper_id"])] = doi
    return m


def paper_id_to_doi(paper_id):
    """Fallback: derive a DOI-style string from the paper_id."""
    return paper_id.replace("_", "/", 1)


def resolve_doi(journal, paper_id, doi_map):
    """Get the best DOI we can for this paper."""
    # 1. From doi_years.csv
    doi = doi_map.get((journal, paper_id))
    if doi:
        return doi
    # 2. Fall back to paper_id conversion
    return paper_id_to_doi(paper_id)


def fetch_citations(doi):
    url = f"https://api.openalex.org/works/doi:{doi}"
    params = {"mailto": "reganwhite@example.com"}
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=20)
        if r.status_code == 404:
            return None, "not_found"
        if r.status_code != 200:
            return None, f"http_{r.status_code}"
        return r.json().get("cited_by_count"), "ok"
    except Exception:
        return None, "exception"


def load_cache():
    cache = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            for row in csv.DictReader(f):
                cache[(row["journal"], row["paper_id"])] = row
    return cache


def save_all(rows):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows)


def main():
    master = list(csv.DictReader(open(MASTER)))
    doi_map = load_doi_map()
    print(f"Loaded {len(master)} papers from master.csv")
    print(f"Loaded {len(doi_map)} DOIs from doi_years.csv")
    print(f"Retrieval year: {RETRIEVAL_YEAR}")

    cache = load_cache()
    print(f"Loaded {len(cache)} cached entries — skipping these")

    rows = []
    fetched = cached = not_found = 0

    for i, r in enumerate(master, 1):
        journal = r["journal"]
        paper_id = r["paper_id"]
        year = int(r["year"])
        key = (journal, paper_id)

        if key in cache:
            rows.append(cache[key])
            cached += 1
            continue

        doi = resolve_doi(journal, paper_id, doi_map)
        total, status = fetch_citations(doi)
        fetched += 1
        time.sleep(0.15)

        if total is None:
            not_found += 1
            if i % 20 == 0 or not_found <= 10:
                print(f"  [{i}/{len(master)}] {doi}  ->  NOT FOUND ({status})")

        years_since = max(RETRIEVAL_YEAR - year, 1)
        citations_per_year = (total / years_since) if total is not None else None

        rows.append({
            "journal": journal,
            "paper_id": paper_id,
            "doi": doi,
            "year": year,
            "years_since": years_since,
            "citations_total": total if total is not None else "",
            "citations_per_year": round(citations_per_year, 3) if citations_per_year is not None else "",
            "source": status,
        })

        if fetched % 25 == 0:
            save_all(rows)
            print(f"    ...saved {len(rows)} rows so far")

    save_all(rows)
    print(f"\nWrote {OUT}")
    print(f"  fetched:    {fetched}")
    print(f"  cached:     {cached}")
    print(f"  not found:  {not_found}")
    print(f"  total rows: {len(rows)}")


if __name__ == "__main__":
    main()
