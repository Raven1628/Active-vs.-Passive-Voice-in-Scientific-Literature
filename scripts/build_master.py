# scripts/build_master.py
# Joins raw scores + year manifest into a single analysis-ready master table.
# Filters to TARGET_YEARS only.
# Writes:
#   journals/_overall/master.csv              (one row per paper)
#   journals/_overall/summary_by_year.csv     (journal x year aggregates)
#   journals/_overall/summary_by_journal.csv  (journal aggregates)
#   journals/_overall/excluded_papers.csv     (off-target years, for records)

import os
import csv
from collections import defaultdict
from config import TARGET_YEARS

BASE = "/Users/reganwhite/Desktop/Scientific_Writing/Class_Project/journals/_overall"
SCORES_CSV = f"{BASE}/scores_raw/all_raw_papers.csv"
YEARS_CSV  = f"{BASE}/doi_years.csv"
MASTER_CSV = f"{BASE}/master.csv"
BY_YEAR_CSV = f"{BASE}/summary_by_year.csv"
BY_JOURNAL_CSV = f"{BASE}/summary_by_journal.csv"
EXCLUDED_CSV = f"{BASE}/excluded_papers.csv"

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


def load_scores():
    if not os.path.exists(SCORES_CSV):
        raise FileNotFoundError(f"Missing: {SCORES_CSV}")
    with open(SCORES_CSV) as f:
        return list(csv.DictReader(f))


def build_master():
    years = load_years()
    scores = load_scores()

    master = []
    excluded = []
    no_year = 0

    for r in scores:
        key = (r["journal"], r["paper_id"])
        year = years.get(key)

        if year is None:
            no_year += 1
            excluded.append({
                "paper_id": r["paper_id"],
                "journal": r["journal"],
                "year": "",
                "active_ratio": r["active_ratio"],
                "reason": "no_year",
            })
            continue

        if year not in TARGET_YEAR_SET:
            excluded.append({
                "paper_id": r["paper_id"],
                "journal": r["journal"],
                "year": year,
                "active_ratio": r["active_ratio"],
                "reason": "off_target_year",
            })
            continue

        try:
            ratio = float(r["active_ratio"])
        except (ValueError, TypeError):
            ratio = None

        master.append({
            "paper_id": r["paper_id"],
            "journal": r["journal"],
            "year": year,
            "active": r["active"],
            "passive": r["passive"],
            "total": r["total"],
            "active_ratio": ratio,
        })

    master.sort(key=lambda x: (x["journal"], x["year"], x["paper_id"]))

    with open(MASTER_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "paper_id", "journal", "year",
            "active", "passive", "total", "active_ratio"])
        w.writeheader()
        w.writerows(master)

    with open(EXCLUDED_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "paper_id", "journal", "year", "active_ratio", "reason"])
        w.writeheader()
        w.writerows(excluded)

    print(f"Wrote {MASTER_CSV}")
    print(f"  {len(master)} papers  (kept)")
    print(f"Wrote {EXCLUDED_CSV}")
    print(f"  {len(excluded)} papers excluded  "
          f"({no_year} no_year, {len(excluded)-no_year} off_target_year)")
    return master


def summarize(master):
    buckets = defaultdict(list)
    for r in master:
        if r["active_ratio"] is None:
            continue
        buckets[(r["journal"], r["year"])].append(r["active_ratio"])

    rows_jy = []
    for (journal, year), ratios in sorted(buckets.items()):
        n = len(ratios)
        mean = sum(ratios) / n
        sd = (sum((v - mean) ** 2 for v in ratios) / (n - 1)) ** 0.5 if n > 1 else 0.0
        rows_jy.append({
            "journal": journal,
            "year": year,
            "n": n,
            "mean_active_ratio": round(mean, 4),
            "sd": round(sd, 4),
            "min": round(min(ratios), 4),
            "max": round(max(ratios), 4),
        })

    with open(BY_YEAR_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "journal", "year", "n", "mean_active_ratio", "sd", "min", "max"])
        w.writeheader()
        w.writerows(rows_jy)
    print(f"Wrote {BY_YEAR_CSV}  ({len(rows_jy)} journal-year cells)")

    j_buckets = defaultdict(list)
    for r in master:
        if r["active_ratio"] is not None:
            j_buckets[r["journal"]].append(r["active_ratio"])

    rows_j = []
    for journal, ratios in sorted(j_buckets.items()):
        n = len(ratios)
        mean = sum(ratios) / n
        sd = (sum((v - mean) ** 2 for v in ratios) / (n - 1)) ** 0.5 if n > 1 else 0.0
        rows_j.append({
            "journal": journal,
            "n": n,
            "mean_active_ratio": round(mean, 4),
            "sd": round(sd, 4),
            "min": round(min(ratios), 4),
            "max": round(max(ratios), 4),
        })

    with open(BY_JOURNAL_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "journal", "n", "mean_active_ratio", "sd", "min", "max"])
        w.writeheader()
        w.writerows(rows_j)
    print(f"Wrote {BY_JOURNAL_CSV}  ({len(rows_j)} journals)")


def main():
    master = build_master()
    summarize(master)

    print()
    print(f"{'Journal':<40} {'n':>5}  {'mean':>6}")
    print("-" * 55)
    by_j = defaultdict(list)
    for r in master:
        if r["active_ratio"] is not None:
            by_j[r["journal"]].append(r["active_ratio"])
    for j in sorted(by_j):
        v = by_j[j]
        print(f"{j:<40} {len(v):>5}  {sum(v)/len(v):>6.3f}")

    print()
    print(f"{'Year':<6} {'n':>5}  {'mean':>6}")
    print("-" * 25)
    by_y = defaultdict(list)
    for r in master:
        if r["active_ratio"] is not None:
            by_y[r["year"]].append(r["active_ratio"])
    for y in sorted(by_y):
        v = by_y[y]
        print(f"{y:<6} {len(v):>5}  {sum(v)/len(v):>6.3f}")

    print()
    print("Journal x year counts:")
    print(f"{'Journal':<40} " + "  ".join(f"{y:>6}" for y in TARGET_YEARS))
    print("-" * 100)
    counts = defaultdict(lambda: defaultdict(int))
    for r in master:
        counts[r["journal"]][r["year"]] += 1
    for j in sorted(counts):
        cells = "  ".join(f"{counts[j].get(y, 0):>6}" for y in TARGET_YEARS)
        print(f"{j:<40} {cells}")


if __name__ == "__main__":
    main()
