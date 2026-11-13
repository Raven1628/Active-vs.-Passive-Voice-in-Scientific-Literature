# retrieve_frontiers.py — Frontiers downloader (fully open access)
# Frontiers PDFs: https://www.frontiersin.org/articles/{doi}/pdf

import os
import time
import requests
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.dirname(SCRIPT_DIR)
JOURNALS_DIR = os.path.join(USER_DIR, "journals")

HEADERS = {
    "User-Agent": "VoiceAnalysis/1.0 (mailto:doilist39@gmail.com)",
    "Accept": "application/pdf",
}

def sanitize(doi):
    return doi.replace("/", "_").replace(":", "_")

def download_pdf(doi, out_path):
    # Frontiers URL pattern: https://www.frontiersin.org/articles/10.3389/fpsyg.2020.01234/full
    # PDF: https://www.frontiersin.org/articles/10.3389/fpsyg.2020.01234/pdf
    url = f"https://www.frontiersin.org/articles/{doi}/pdf"

    try:
        r = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        if r.status_code == 200 and r.content.startswith(b"%PDF"):
            with open(out_path, "wb") as f:
                f.write(r.content)
            return "ok"
        elif r.status_code == 404:
            return "not_found"
        else:
            return f"http_{r.status_code}"
    except Exception:
        return "exception"

def main():
    config_path = os.path.join(USER_DIR, "config.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    journals = [j["name"].replace(" ", "_") for j in config.get("journals", [])]
    if not journals:
        raise SystemExit("No journals in config.yaml")

    for journal in journals:
        journal_dir = os.path.join(JOURNALS_DIR, journal)
        raw_dir = os.path.join(journal_dir, "raw_papers")
        dois_file = os.path.join(journal_dir, "dois.txt")

        os.makedirs(raw_dir, exist_ok=True)
        if not os.path.exists(dois_file):
            print(f"{journal}: No dois.txt. Skipping.")
            continue

        with open(dois_file) as f:
            dois = [line.strip() for line in f if line.strip()]

        print(f"\n{journal}: {len(dois)} DOIs")
        success = skipped = failed = 0

        for i, doi in enumerate(dois, 1):
            out_path = os.path.join(raw_dir, f"{sanitize(doi)}.pdf")
            if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
                skipped += 1
                continue

            status = download_pdf(doi, out_path)
            if status == "ok":
                success += 1
            else:
                failed += 1
            time.sleep(0.5)

        print(f"  {journal}: downloaded={success}, skipped={skipped}, failed={failed}")

if __name__ == "__main__":
    main()
