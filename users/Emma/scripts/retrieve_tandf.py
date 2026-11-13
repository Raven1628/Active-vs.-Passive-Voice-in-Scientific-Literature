# retrieve_tandf.py — Manual download mode
# Taylor & Francis' license prohibits automated harvesting.
# Emma downloads PDFs manually (see SETUP.md).

import sys

print("=" * 60)
print("  MANUAL DOWNLOAD MODE")
print("=" * 60)
print()
print("Taylor & Francis' license prohibits automated downloading.")
print()
print("Steps:")
print("  1. Run: python scripts/fetch_dois.py")
print("  2. For each journals/<journal>/dois.txt:")
print("     - Log into tandfonline.com via GT Library")
print("     - Visit https://doi.org/<DOI>")
print("     - Click PDF, save as journals/<journal>/raw_papers/<DOI_with_underscores>.pdf")
print("  3. Run: python run.py")
print()
print("Skipping automated download.")
