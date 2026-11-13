# fetch_dois.py — queries Crossref for DOIs by journal ISSN and year.
# Reads journals/years from config.yaml. No publisher filter.

import os
import time
import requests
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(USER_DIR, "config.yaml")
JOURNALS_DIR = os.path.join(USER_DIR, "journals")

HEADERS = {"User-Agent": "VoiceAnalysis/1.0 (mailto:doilist39@gmail.com)"}

def sanitize(name):
    return name.replace(" ", "_").replace("/", "_")

def fetch_year(issn, year, limit):
    url = f"https://api.crossref.org/journals/{issn}/works"
    params = {
        "filter": f"from-pub-date:{year}-01-01,until-pub-date:{year}-12-31,type:journal-article",
        "rows": min(limit, 1000),
        "select": "DOI",
        "sort": "published",
        "order": "asc",
    }
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            print(f" HTTP {r.status_code}", flush=True)
            return []
        items = r.json()["message"]["items"]
        return [item["DOI"] for item in items if "DOI" in item]
    except Exception as e:
        print(f" error {e}", flush=True)
        return []

def main():
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    journals = config.get("journals", [])
    years = config.get("years", [2005, 2010, 2015, 2020, 2025])
    papers_per_year = config.get("papers_per_year", 40)

    print(f"Fetching DOIs for {len(journals)} journals × {len(years)} years")
    print(f"Target: {papers_per_year} papers per journal-year")
    print()

    for journal_entry in journals:
        name = journal_entry["name"]
        issn = journal_entry.get("issn", "").strip()
        if not issn:
            print(f"=== {name} ===\n  WARNING: no ISSN. Skipping.")
            continue

        journal_dir = os.path.join(JOURNALS_DIR, sanitize(name))
        os.makedirs(journal_dir, exist_ok=True)
        out_path = os.path.join(journal_dir, "dois.txt")

        print(f"=== {name} (ISSN {issn}) ===")
        all_dois = []
        for year in years:
            print(f"  {year}...", end="", flush=True)
            dois = fetch_year(issn, year, papers_per_year)
            print(f" {len(dois)} DOIs")
            all_dois.extend(dois)
            time.sleep(0.3)

        with open(out_path, "w") as f:
            for doi in all_dois:
                f.write(doi + "\n")

        print(f"  Wrote {len(all_dois)} DOIs to {out_path}")
        print()

if __name__ == "__main__":
    main()
