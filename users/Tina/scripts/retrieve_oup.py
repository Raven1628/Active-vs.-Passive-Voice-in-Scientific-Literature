# retrieve_oup.py — OUP downloader using Playwright CDP (cross-platform).
# Usage:
#   python retrieve_oup.py --setup    (installs Playwright + launches debug Chrome)
#   python retrieve_oup.py            (downloads PDFs using the running Chrome)

import os
import sys
import time
import platform
import subprocess
import yaml
from playwright.sync_api import sync_playwright

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.dirname(SCRIPT_DIR)
JOURNALS_DIR = os.path.join(USER_DIR, "journals")
CDP_URL = "http://localhost:9222"

def sanitize(doi):
    return doi.replace("/", "_").replace(":", "_")

def get_journals_from_config():
    config_path = os.path.join(USER_DIR, "config.yaml")
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    return [j["name"].replace(" ", "_") for j in cfg.get("journals", [])]

def launch_debug_chrome():
    """Launch Chrome with remote debugging on any OS."""
    system = platform.system()
    print(f"Detected OS: {system}")

    # Common Chrome executable paths
    if system == "Darwin":  # macOS
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    elif system == "Windows":
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
    else:  # Linux
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]

    chrome_exe = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_exe = path
            break

    if not chrome_exe:
        print("ERROR: Could not find Chrome. Please install Google Chrome.")
        sys.exit(1)

    # Launch command
    cmd = [
        chrome_exe,
        "--remote-debugging-port=9222",
        "--user-data-dir=/tmp/chrome-oup-debug",  # Works on all OS (Windows maps to C:\tmp)
        "--no-first-run",
        "--no-default-browser-check",
    ]

    print(f"Launching: {' '.join(cmd)}")
    print("\n--> ACTION REQUIRED <--")
    print("1. A Chrome window will open.")
    print("2. Log into Oxford Academic via Georgia Tech Library.")
    print("3. Navigate to https://academic.oup.com and confirm you are logged in.")
    print("4. Leave the Chrome window OPEN, then run this script again WITHOUT --setup.\n")

    subprocess.Popen(cmd)

def download_one(page, doi, out_path):
    url = f"https://doi.org/{doi}"
    print(f"    Navigating to: {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(2)

        pdf_link = page.query_selector('a[href*="/article-pdf/"]')
        if not pdf_link:
            pdf_link = page.query_selector('a:has-text("PDF")')
        if not pdf_link:
            return "no_pdf_link"

        href = pdf_link.get_attribute("href")
        if href.startswith("/"):
            href = "https://academic.oup.com" + href
        elif not href.startswith("http"):
            href = "https://academic.oup.com/" + href.lstrip("/")

        with page.expect_download(timeout=60000) as dl_info:
            page.goto(href, wait_until="commit")

        download = dl_info.value
        download.save_as(out_path)

        with open(out_path, "rb") as f:
            if f.read(4) != b"%PDF":
                os.remove(out_path)
                return "not_pdf"
        return "ok"
    except Exception as e:
        return f"exception: {str(e)[:100]}"

def main():
    if "--setup" in sys.argv:
        print("=== Installing Playwright dependencies ===")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("\n=== Launching Debug Chrome ===")
        launch_debug_chrome()
        return

    journals = get_journals_from_config()
    
    with sync_playwright() as p:
        print(f"Connecting to Chrome at {CDP_URL}...")
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            print(f"ERROR: Could not connect to Chrome. Did you run --setup? ({e})")
            sys.exit(1)

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        for journal in journals:
            journal_dir = os.path.join(JOURNALS_DIR, journal)
            raw_dir = os.path.join(journal_dir, "raw_papers")
            dois_file = os.path.join(journal_dir, "dois.txt")
            os.makedirs(raw_dir, exist_ok=True)

            if not os.path.exists(dois_file):
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

                print(f"  [{i}/{len(dois)}] {doi}")
                status = download_one(page, doi, out_path)

                if status == "ok":
                    success += 1
                    print(f"    ✓ Saved")
                else:
                    failed += 1
                    print(f"    ✗ {status}")
                time.sleep(1.5)

            print(f"  {journal}: downloaded={success}, skipped={skipped}, failed={failed}")
        browser.close()

if __name__ == "__main__":
    main()
