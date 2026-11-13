import pathlib
p = pathlib.Path("retrieve_oup.py")
text = p.read_text()

old_func_start = 'def download_one(page, doi, out_path):'
old_func_end = 'def main():'

start_idx = text.find(old_func_start)
end_idx = text.find(old_func_end)

if start_idx == -1 or end_idx == -1:
    print("Could not locate function boundaries")
    raise SystemExit(1)

new_func = '''def download_one(page, doi, out_path):
    """Navigate to article, find PDF link, fetch bytes via page.request."""
    url = f"https://doi.org/{doi}"
    print(f"    Navigating to: {url}")

    try:
        page.goto(url, wait_until="commit", timeout=90000)
        time.sleep(4)

        # Find the PDF link
        pdf_link = page.query_selector('a[href*="/article-pdf/"]')
        if not pdf_link:
            pdf_link = page.query_selector('a:has-text("PDF")')
        if not pdf_link:
            all_links = page.query_selector_all("a")
            for link in all_links:
                href = link.get_attribute("href") or ""
                if "pdf" in href.lower() and ("article" in href.lower() or "doi" in href.lower()):
                    pdf_link = link
                    break

        if not pdf_link:
            print(f"    No PDF link on page (title: {page.title()[:60]})")
            return "no_pdf_link"

        href = pdf_link.get_attribute("href") or ""
        if href.startswith("/"):
            href = "https://academic.oup.com" + href
        elif not href.startswith("http"):
            href = "https://academic.oup.com/" + href.lstrip("/")

        print(f"    PDF href: {href[:80]}")

        # Fetch PDF bytes using the page's own request context (reuses cookies)
        response = page.request.get(href, timeout=90000)
        print(f"    HTTP {response.status}")

        if response.status != 200:
            return f"http_{response.status}"

        body = response.body()

        if not body.startswith(b"%PDF"):
            print(f"    Not a PDF (first bytes: {body[:30]})")
            return "not_pdf"

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(body)

        size_kb = len(body) / 1024
        print(f"    ✓ Saved ({size_kb:.0f} KB)")
        return "ok"

    except Exception as e:
        err = str(e)[:150]
        print(f"    Error: {err}")
        return f"exception"


'''

text = text[:start_idx] + new_func + text[end_idx:]
p.write_text(text)
print("Patched: download_one now fetches via page.request")

