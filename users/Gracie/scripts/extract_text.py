# scripts/extract_text.py
# Reads PDFs from each journal's raw_papers folder and saves text to raw_text.

import os
import json
import pymupdf
from tqdm import tqdm
from config import (
    TARGET_JOURNALS, journal_path, ensure_journal_folders,
    RAW_PAPERS_SUBDIR, RAW_TEXT_SUBDIR,
)


def extract_text_from_pdf(pdf_path):
    """Open a PDF and return its full text plus page count."""
    doc = pymupdf.open(pdf_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return {"text": "\n\n".join(pages), "num_pages": len(pages)}


def find_pdfs(folder):
    """Return a list of (paper_id, pdf_path) for all PDFs in a folder."""
    pdfs = []
    if not os.path.exists(folder):
        return pdfs
    for filename in os.listdir(folder):
        if filename.lower().endswith(".pdf"):
            paper_id = filename.replace(".pdf", "")
            pdfs.append((paper_id, os.path.join(folder, filename)))
    return pdfs


def main():
    for journal in TARGET_JOURNALS:
        ensure_journal_folders(journal)
        src = journal_path(journal, RAW_PAPERS_SUBDIR)
        dst = journal_path(journal, RAW_TEXT_SUBDIR)

        pdfs = find_pdfs(src)
        print(f"\n=== {journal} ===")
        print(f"  Source: {src}")
        print(f"  Found {len(pdfs)} PDFs")

        if not pdfs:
            continue

        processed = skipped = failed = 0
        for paper_id, pdf_path in tqdm(pdfs, desc=f"  {journal}"):
            output_path = os.path.join(dst, f"{paper_id}.json")

            if os.path.exists(output_path):
                skipped += 1
                continue

            try:
                result = extract_text_from_pdf(pdf_path)
                result["paper_id"] = paper_id
                result["journal"] = journal
                result["pdf_path"] = pdf_path
                with open(output_path, "w") as f:
                    json.dump(result, f, indent=2)
                processed += 1
            except Exception as e:
                print(f"\n    FAILED: {paper_id} — {e}")
                failed += 1

        print(f"  Processed: {processed}, Skipped: {skipped}, Failed: {failed}")


if __name__ == "__main__":
    main()
