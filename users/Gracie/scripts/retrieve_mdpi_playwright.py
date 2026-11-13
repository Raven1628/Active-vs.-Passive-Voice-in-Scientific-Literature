# retrieve_mdpi_playwright.py — Playwright-based fallback for MDPI PDFs
# that aren't available on the CDN (e.g., 2005-era i-prefix DOIs).
#
# Requires Chrome running with --remote-debugging-port=9222 and logged into
# mdpi.com (Cloudflare bypass). See SETUP.md.

import os
import sys
import time
import yaml

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && python -m playwright install chromium")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.dirname(SCRIPT_DIR)
JOURNALS_DIR = os.path.join(USER_DIR, "journals")
CDP_URL = "http://localhost:9222"


def sanitize(doi):
    return doi.replace("/", "_").replace(":", "_")


def doi_to_article_url(doi):
    """Convert MDPI DOI to article page URL.
    
    10.3390/i6010045 -> https://www.mdpi.com/1422-0067/6/1/45
    The path is constructed from ISSN + volume + issue + article page number.
    We use the DOI resolver which redirects to the article page.
    """
    return f"https://doi.org/{doi}"


def get_journals_from_config():
    with open(os.path.join(USER_DIR, "config.yaml")) as f:
        cfg = yaml.safe_load(f)
    return [j["name"].replace(" ", "_").replace("/", "_") for j in cfg.get("journals", [])]


def download_one(page, doi, out_path):
    """Navigate to article page, click PDF, save file."""
    url = f"https://doi.org/{doi}"
    print(f"    Navigating to: {url}")

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)

        # MDPI article page has a PDF button with href ending in /pdf
        # Try multiple selectors (MDPI changes these over time)
        pdf_link = None
        for selector in [
            'a[href$="/pdf"]',
            'a[href*="/pdf?"]',
            'a:has-text("Download PDF")',
            'a.UD_ArticleExportButton',  # MDPI's specific class
            'a[title="Download PDF"]',
        ]:
            pdf_link = page.query_selector(selector)
            if pdf_link:
                break

        if not pdf_link:
            # Fallback: search all links for 'pdf'
            all_links = page.query_selector_all("a")
            for link in all_links:
                href = link.get_attribute("href") or ""
                text = (link.inner_text() or "").lower()
                if "pdf" in href.lower() or "pdf" in text:
                    pdf_link = link
                    break

        if not pdf_link:
            return "no_pdf_link"

        href = pdf_link.get_attribute("href") or ""
        if href.startswith("/"):
            href = "https://www.mdpi.com" + href
        elif not href.startswith("http"):
            href = "https://www.mdpi.com/" + href.lstrip("/")

        print(f"    PDF href: {href[:100]}")

        # Fetch via page.request (reuses cookies, avoids download event issues)
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
    if "--setup" in sys.argv:
        import subprocess
        print("Installing Playwright...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("\nNow launch Chrome with debugging (Windows):")
        print('  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222')
        print("\nOr Mac:")
        print('  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222')
        print("\nThen log into mdpi.com and run this script WITHOUT --setup.")
        return

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
            print("  Make sure Chrome is running with --remote-debugging-port=9222")
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

            # Only try DOIs that don't already have a PDF
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
