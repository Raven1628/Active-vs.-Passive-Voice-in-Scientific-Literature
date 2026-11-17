# retrieve_springer_playwright.py — Playwright downloader for Springer Nature
# All Springer/Nature journals require GT institutional login for scripted access.
# Requires Chrome running with --remote-debugging-port=9222 and logged into
# Springer via GT Library.

import os
import sys
import time
import yaml

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: pip install playwright && python -m playwright install chromium")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.dirname(SCRIPT_DIR)
JOURNALS_DIR = os.path.join(USER_DIR, "journals")
CDP_URL = "http://localhost:9222"


def sanitize(doi):
    return doi.replace("/", "_").replace(":", "_")


def get_journals_from_config():
    with open(os.path.join(USER_DIR, "config.yaml")) as f:
        cfg = yaml.safe_load(f)
    return [j["name"].replace(" ", "_").replace("/", "_") for j in cfg.get("journals", [])]


def download_one(page, doi, out_path):
    url = f"https://doi.org/{doi}"
    print(f"    Navigating to: {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)

        pdf_link = None
        for selector in [
            'a[href*="/content/pdf/"]',
            'a[href$=".pdf"]',
            'a[data-track-action="download pdf"]',
            'a:has-text("Download PDF")',
            'a:has-text("PDF")',
        ]:
            pdf_link = page.query_selector(selector)
            if pdf_link:
                break

        if not pdf_link:
            all_links = page.query_selector_all("a")
            for link in all_links:
                href = link.get_attribute("href") or ""
                if "pdf" in href.lower() and ("springer" in href.lower() or "nature" in href.lower() or href.endswith(".pdf")):
                    pdf_link = link
                    break

        if not pdf_link:
            return "no_pdf_link"

        href = pdf_link.get_attribute("href") or ""
        if href.startswith("/"):
            current_url = page.url
            if "nature.com" in current_url:
                href = "https://www.nature.com" + href
            else:
                href = "https://link.springer.com" + href
        elif not href.startswith("http"):
            href = "https://link.springer.com/" + href.lstrip("/")

        print(f"    PDF href: {href[:100]}")

        resp = page.request.get(href, timeout=90000)
        print(f"    HTTP {resp.status}")

        if resp.status != 200:
            return f"http_{resp.status}"

        body = resp.body()
        if not body.startswith(b"%PDF"):
            return "not_pdf"

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(body)
        print(f"    ✓ Saved ({len(body)/1024:.0f} KB)")
        return "ok"

    except Exception as e:
        return f"exception: {str(e)[:100]}"


def main():
    journals = get_journals_from_config()

    with sync_playwright() as p:
        print(f"Connecting to Chrome at {CDP_URL}...")
        browser = None
        for attempt in range(15):
            try:
                browser = p.chromium.connect_over_cdp(CDP_URL)
                print(f"  Connected (attempt {attempt + 1})")
                break
            except Exception:
                if attempt == 0:
                    print("  Waiting for Chrome...")
                time.sleep(2)

        if browser is None:
            print(f"ERROR: Could not connect to Chrome at {CDP_URL}")
            sys.exit(1)

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        for journal in journals:
            journal_dir = os.path.join(JOURNALS_DIR, journal)
            raw_dir = os.path.join(journal_dir, "raw_papers")
            dois_file = os.path.join(journal_dir, "dois.txt")

            if not os.path.exists(dois_file):
                continue

            with open(dois_file) as f:
                dois = [line.strip() for line in f if line.strip()]

            missing = []
            for doi in dois:
                out_path = os.path.join(raw_dir, f"{sanitize(doi)}.pdf")
                if not os.path.exists(out_path) or os.path.getsize(out_path) < 5000:
                    missing.append(doi)

            if not missing:
                continue

            print(f"\n{journal}: {len(missing)} missing PDFs (of {len(dois)} total)")

            for i, doi in enumerate(missing, 1):
                out_path = os.path.join(raw_dir, f"{sanitize(doi)}.pdf")
                print(f"  [{i}/{len(missing)}] {doi}")
                status = download_one(page, doi, out_path)
                if status != "ok":
                    print(f"    ✗ {status}")
                time.sleep(1.5)

        browser.close()


if __name__ == "__main__":
    main()
