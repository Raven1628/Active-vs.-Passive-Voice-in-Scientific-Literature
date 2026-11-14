# retrieve_mdpi.py — MDPI downloader via static CDN (mdpi-res.com)
# Bypasses MDPI's Cloudflare block on www.mdpi.com.

import os
import re
import time
import requests
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.dirname(SCRIPT_DIR)
JOURNALS_DIR = os.path.join(USER_DIR, "journals")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36",
}

def sanitize(doi):
    return doi.replace("/", "_").replace(":", "_")

def doi_to_cdn_url(doi):
    """Convert MDPI DOI to static CDN PDF URL.

    Two DOI formats are supported:

    Modern (2007+):
      DOI: 10.3390/molecules25010181
      CDN: https://mdpi-res.com/d_attachment/molecules/molecules-25-00181/
           article_deploy/molecules-25-00181.pdf

    Legacy i-prefix (IJMS, 2000-2007):
      DOI: 10.3390/i6010045  -> volume 6, issue 01, article 45
      CDN: https://mdpi-res.com/d_attachment/ijms/ijms-06-00045/
           article_deploy/ijms-06-00045.pdf
    """
    if not doi.startswith("10.3390/"):
        return None

    code = doi.replace("10.3390/", "")

    # --- Legacy i-prefix: i{vol}{issue}{article}, e.g. i6010045 ---
    # Volume is 1-2 digits, issue is 2 digits, article is the rest.
    # i6010045 -> vol=6, issue=01, article=0045
    # i1001001 -> vol=10, issue=01, article=001 (if ever encountered)
    m_legacy = re.match(r'^i(\d{1,2})(\d{2})(\d{4})$', code)
    if m_legacy:
        vol, _issue, article = m_legacy.groups()
        vol = vol.zfill(2)
        article = article.zfill(5)
        base = f"ijms-{vol}-{article}"
        return (f"https://mdpi-res.com/d_attachment/ijms/{base}/"
                f"article_deploy/{base}.pdf")

    # --- Modern format: journal(YY)(II)(AAAA+) ---
    match = re.match(r'^([a-z]+)(\d{2})(\d{2})(\d{4,})$', code)
    if not match:
        match = re.match(r'^([a-z][a-z0-9]*?)(\d{2})(\d{2})(\d{4,})$', code)
        if not match:
            return None

    journal, vol, issue, article = match.groups()
    article_padded = article.zfill(5)

    return (f"https://mdpi-res.com/d_attachment/{journal}/"
            f"{journal}-{vol}-{article_padded}/article_deploy/"
            f"{journal}-{vol}-{article_padded}.pdf")

def download_pdf(doi, out_path, debug=False):
    url = doi_to_cdn_url(doi)
    if not url:
        if debug:
            print(f"    Could not parse DOI: {doi}", flush=True)
        return "parse_failed"

    if debug:
        print(f"    URL: {url[:80]}", flush=True)

    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200 and r.content.startswith(b"%PDF"):
            with open(out_path, "wb") as f:
                f.write(r.content)
            return "ok"
        elif r.status_code == 404:
            return "not_found"
        else:
            return f"http_{r.status_code}"
    except Exception as e:
        if debug:
            print(f"    Exception: {e}", flush=True)
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

            debug = (i <= 2)
            status = download_pdf(doi, out_path, debug=debug)
            if status == "ok":
                success += 1
                print(f"  [{i}/{len(dois)}] OK: {doi}")
            else:
                failed += 1
                print(f"  [{i}/{len(dois)}] FAIL: {doi} ({status})")

            time.sleep(0.5)

        print(f"  {journal}: downloaded={success}, skipped={skipped}, failed={failed}")

if __name__ == "__main__":
    main()
