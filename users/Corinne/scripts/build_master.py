# build_master.py — reads scores + years + citations, writes master file
import os
import csv
from collections import defaultdict
from config import TARGET_YEARS

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.dirname(SCRIPT_DIR)
JOURNALS_DIR = os.path.join(USER_DIR, "journals")
ANALYSIS_DIR = os.path.join(USER_DIR, "analysis")
os.makedirs(ANALYSIS_DIR, exist_ok=True)

SCORES_CSV = os.path.join(JOURNALS_DIR, "_overall", "scores", "all_papers_summary.csv")
YEARS_CSV = os.path.join(USER_DIR, "doi_years.csv")
CITATIONS_CSV = os.path.join(ANALYSIS_DIR, "citations.csv")
MASTER_CSV = os.path.join(ANALYSIS_DIR, "master_with_citations.csv")
EXCLUDED_CSV = os.path.join(ANALYSIS_DIR, "excluded_papers.csv")

TARGET_YEAR_SET = set(TARGET_YEARS)


def load_years():
    years = {}
    if not os.path.exists(YEARS_CSV):
        print(f"WARNING: {YEARS_CSV} not found")
        return years
    with open(YEARS_CSV) as f:
        for row in csv.DictReader(f):
            y = row.get("year", "").strip()
            if y:
                try:
                    years[(row["journal"], row["paper_id"])] = int(y)
                except ValueError:
                    pass
    return years


def load_citations():
    cites = {}
    if not os.path.exists(CITATIONS_CSV):
        print(f"WARNING: {CITATIONS_CSV} not found")
        return cites
    with open(CITATIONS_CSV) as f:
        for row in csv.DictReader(f):
            key = (row["journal"], row["paper_id"])
            cites[key] = {
                "citations_total": row.get("citations_total", ""),
                "citations_per_year": row.get("citations_per_year", ""),
            }
    return cites


def load_scores():
    if not os.path.exists(SCORES_CSV):
        raise FileNotFoundError(f"Missing: {SCORES_CSV}")
    with open(SCORES_CSV) as f:
        return list(csv.DictReader(f))


def main():
    years = load_years()
    cites = load_citations()
    scores = load_scores()
    print(f"Loaded {len(scores)} scores, {len(years)} years, {len(cites)} citations")

    master = []
    excluded = []
    no_year = 0

    for r in scores:
        key = (r["journal"], r["paper_id"])
        year = years.get(key)
        if year is None:
            no_year += 1
            continue
        if year not in TARGET_YEAR_SET:
            excluded.append({**r, "year": year, "reason": "off_target_year"})
            continue
        try:
            ratio = float(r["active_ratio"])
        except (ValueError, TypeError):
            ratio = None
        cite = cites.get(key, {})
        master.append({
            "paper_id": r["paper_id"],
            "journal": r["journal"],
            "year": year,
            "active": r.get("active", ""),
            "passive": r.get("passive", ""),
            "total": r.get("total", ""),
            "active_ratio": ratio,
            "citations_total": cite.get("citations_total", ""),
            "citations_per_year": cite.get("citations_per_year", ""),
        })

    master.sort(key=lambda x: (x["journal"], x["year"], x["paper_id"]))

    with open(MASTER_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(master[0].keys()) if master else [])
        w.writeheader()
        w.writerows(master)

    print(f"Wrote {MASTER_CSV}")
    print(f"  {len(master)} papers kept")
    print(f"  {no_year} excluded (no year)")
    print(f"  {len(excluded)} excluded (off-target year)")

    if excluded:
        with open(EXCLUDED_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(excluded[0].keys()))
            w.writeheader()
            w.writerows(excluded)
        print(f"Wrote {EXCLUDED_CSV}")

    n_with_cites = sum(1 for r in master if r["citations_total"] != "")
    print(f"  {n_with_cites}/{len(master)} papers have citation data")


if __name__ == "__main__":
    main()
