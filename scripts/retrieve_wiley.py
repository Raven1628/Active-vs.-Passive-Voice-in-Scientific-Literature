# scripts/retrieve_wiley.py
# Downloads PDFs from Wiley TDM API using DOI lists.

import os
import sys
import time
import requests
from tqdm import tqdm
from config import (
    TARGET_JOURNALS, journal_path,
    RAW_PAPERS_SUBDIR, WILEY_TDM_TOKEN, is_wiley_doi,
)

WILEY_API = "https://api.wiley.com/onlinelibrary/tdm/v1/articles"
SLEEP_BETWEEN_CALLS = 10  # Wiley rate limit: 60 requests per 10 minutes


def download_pdf(doi, output_path):
    """Download a single PDF from Wiley TDM API."""
    url = f"{WILEY_API}/{doi}"
    headers = {"Wiley-TDM-Client-Token": WILEY_TDM_TOKEN}
    try:
        r = requests.get(url, headers=headers, timeout=60, allow_redirects=True)
        if r.status_code == 200 and r.content[:5] == b"%PDF-":
            with open(output_path, "wb") as f:
                f.write(r.content)
            return "ok"
        elif r.status_code == 404:
            return "not_found"
        elif r.status_code == 403:
            return "forbidden"
        else:
            return f"status_{r.status_code}"
    except Exception as e:
        return f"error: {e}"


def process_journal(journal):
    dois_file = os.path.join(journal_path(journal), "dois.txt")
    if not os.path.exists(dois_file):
        print(f"  No dois.txt for {journal}")
        return

    dois = [d for d in open(dois_file).read().strip().split("\n") if d]
    print(f"\n=== {journal} ===")
    print(f"  Total DOIs: {len(dois)}")

    out_dir = journal_path(journal, RAW_PAPERS_SUBDIR)
    os.makedirs(out_dir, exist_ok=True)

    skipped = downloaded = failed = 0
    failed_dois = []

    for doi in tqdm(dois, desc=f"  {journal}"):
        if not is_wiley_doi(doi):
            skipped += 1
            continue

        safe_doi = doi.replace("/", "_").replace(":", "_")
        output_path = os.path.join(out_dir, f"{safe_doi}.pdf")

        if os.path.exists(output_path):
            skipped += 1
            continue

        status = download_pdf(doi, output_path)
        if status == "ok":
            downloaded += 1
        else:
            failed += 1
            failed_dois.append((doi, status))

        # Always sleep to respect rate limits
        time.sleep(SLEEP_BETWEEN_CALLS)

    print(f"  Downloaded: {downloaded}, Skipped: {skipped}, Failed: {failed}")
    if failed_dois:
        fail_file = os.path.join(journal_path(journal), "failed_dois.txt")
        with open(fail_file, "w") as f:
            for doi, status in failed_dois:
                f.write(f"{doi}\t{status}\n")
        print(f"  Full list written to {fail_file}")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    journals = [target] if target else list(TARGET_JOURNALS.keys())

    print(f"Journals: {journals}")
    for journal in journals:
        process_journal(journal)


if __name__ == "__main__":
    main()
