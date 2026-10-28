# make_stats_summary.py
# Regenerates the statistical analysis summary as a plain text file.
# Reads: analysis/master_with_jif_cleaned.csv (926 papers)
# Writes: manuscript/statistical_summary.txt

import os
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

BASE = "/Users/reganwhite/Desktop/Scientific_Writing/Class_Project"
CSV = os.path.join(BASE, "analysis", "master_with_jif_cleaned.csv")
OUT_DIR = os.path.join(BASE, "manuscript")
OUT_PATH = os.path.join(OUT_DIR, "statistical_summary.txt")
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(CSV)
df["active_ratio"] = pd.to_numeric(df["active_ratio"], errors="coerce")
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["citations_per_year"] = pd.to_numeric(df["citations_per_year"], errors="coerce")
df["jif"] = pd.to_numeric(df["jif"], errors="coerce")

# Different analysis subsets
df_all = df.dropna(subset=["active_ratio", "year"]).copy()
df_cit = df.dropna(subset=["active_ratio", "year", "citations_per_year", "jif"]).copy()
df_all["journal_clean"] = df_all["journal"].str.replace(" ", "_")
df_cit["journal_clean"] = df_cit["journal"].str.replace(" ", "_")

lines = []
def w(s=""):
    lines.append(s)
    print(s)

w("=" * 70)
w("STATISTICAL ANALYSIS SUMMARY")
w("=" * 70)
w()
w(f"Analysis date: 2026-10-28")
w(f"Data source: {CSV}")
w()
w(f"Total papers in corpus:        {len(df)}")
w(f"Papers with active_ratio:       {len(df_all)}")
w(f"Papers with citations + JIF:   {len(df_cit)}")
w()

# ================================================================
# 1. Descriptive stats per journal
# ================================================================
w("=" * 70)
w("1. ACTIVE VOICE BY JOURNAL")
w("=" * 70)
w(f"{'Journal':<35} {'N':>5} {'Mean':>7} {'SD':>7} {'95% CI':>18}")
w("-" * 70)

journal_stats = []
for j in sorted(df_all["journal"].unique()):
    sub = df_all[df_all["journal"] == j]["active_ratio"]
    n = len(sub)
    mean = sub.mean()
    sd = sub.std(ddof=1)
    se = sd / np.sqrt(n)
    lo, hi = mean - 1.96*se, mean + 1.96*se
    journal_stats.append((j, n, mean, sd, lo, hi))
    w(f"{j:<35} {n:>5} {mean:>7.3f} {sd:>7.3f} [{lo:>6.3f}, {hi:>6.3f}]")

w()
overall_mean = df_all["active_ratio"].mean()
overall_sd = df_all["active_ratio"].std()
w(f"{'Overall':<35} {len(df_all):>5} {overall_mean:>7.3f} {overall_sd:>7.3f}")
w()

# ANOVA
groups = [df_all[df_all["journal"] == j]["active_ratio"].values
          for j in df_all["journal"].unique()]
f_stat, p_val = stats.f_oneway(*groups)
w(f"One-way ANOVA:  F({len(groups)-1}, {len(df_all)-len(groups)}) = {f_stat:.2f}, p = {p_val:.2e}")
w()

# ================================================================
# 2. Descriptives by year
# ================================================================
w("=" * 70)
w("2. ACTIVE VOICE BY PUBLICATION YEAR")
w("=" * 70)
w(f"{'Year':<8} {'N':>5} {'Mean':>7} {'SD':>7}")
w("-" * 30)
for year in sorted(df_all["year"].dropna().unique()):
    sub = df_all[df_all["year"] == year]["active_ratio"]
    w(f"{int(year):<8} {len(sub):>5} {sub.mean():>7.3f} {sub.std(ddof=1):>7.3f}")
w()

# ================================================================
# 3. Temporal trends
# ================================================================
w("=" * 70)
w("3. TEMPORAL TRENDS (OLS of active_ratio on year)")
w("=" * 70)
w(f"{'Journal':<35} {'N':>5} {'Slope':>10} {'SE':>9} {'p':>10} {'R2':>8}")
w("-" * 80)

for j in sorted(df_all["journal"].unique()):
    sub = df_all[df_all["journal"] == j].dropna(subset=["year", "active_ratio"])
    if len(sub) < 10: continue
    slope, ic, r, p, se = stats.linregress(sub["year"], sub["active_ratio"])
    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."
    w(f"{j:<35} {len(sub):>5} {slope:>+10.5f} {se:>9.5f} {p:>10.2e} {r**2:>8.3f}  {sig}")

# Sample-wide
sub = df_all.dropna(subset=["year", "active_ratio"])
slope, ic, r, p, se = stats.linregress(sub["year"], sub["active_ratio"])
sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."
w("-" * 80)
w(f"{'SAMPLE-WIDE':<35} {len(sub):>5} {slope:>+10.5f} {se:>9.5f} {p:>10.2e} {r**2:>8.3f}  {sig}")

# Save temporal slope before section 6 overwrites it
temporal_slope = slope
temporal_p = p
temporal_r2 = r**2
w()

# ================================================================
# 4. OLS models predicting citations_per_year
# ================================================================
w("=" * 70)
w("4. OLS MODELS PREDICTING CITATIONS PER YEAR")
w("=" * 70)
w()

m1 = smf.ols("citations_per_year ~ active_ratio", data=df_cit).fit()
m2 = smf.ols("citations_per_year ~ active_ratio + jif", data=df_cit).fit()
m3 = smf.ols("citations_per_year ~ active_ratio + jif + year", data=df_cit).fit()
m4 = smf.ols("citations_per_year ~ active_ratio + jif + year + C(journal_clean)", data=df_cit).fit()

for name, model in [("Model 1 (active only)", m1),
                     ("Model 2 (+ JIF)", m2),
                     ("Model 3 (+ year)", m3),
                     ("Model 4 (+ journal FE)", m4)]:
    w(f"--- {name} ---")
    w(f"  N: {int(model.nobs)}")
    w(f"  R²: {model.rsquared:.3f}")
    w(f"  Active voice:  b = {model.params.get('active_ratio', np.nan):+.3f}, "
      f"SE = {model.bse.get('active_ratio', np.nan):.3f}, "
      f"p = {model.pvalues.get('active_ratio', np.nan):.3g}")
    if 'jif' in model.params:
        w(f"  JIF:           b = {model.params['jif']:+.3f}, "
          f"SE = {model.bse['jif']:.3f}, "
          f"p = {model.pvalues['jif']:.3g}")
    if 'year' in model.params:
        w(f"  Year:          b = {model.params['year']:+.4f}, "
          f"SE = {model.bse['year']:.4f}, "
          f"p = {model.pvalues['year']:.3g}")
    w()

# ================================================================
# 5. Negative binomial
# ================================================================
w("=" * 70)
w("5. NEGATIVE BINOMIAL REGRESSION (total citations)")
w("=" * 70)
w()

df_nb = df.dropna(subset=["active_ratio", "citations_total", "jif"]).copy()
if "citations_total" in df_nb.columns and len(df_nb) > 0:
    try:
        nb = smf.negativebinomial("citations_total ~ active_ratio + jif",
                                   data=df_nb).fit(disp=0)
        w(f"  N: {int(nb.nobs)}")
        for term in nb.params.index:
            coef = nb.params[term]
            se = nb.bse[term]
            irr = np.exp(coef)
            p = nb.pvalues[term]
            w(f"  {term:<20}  coef = {coef:+.4f}, SE = {se:.4f}, "
              f"IRR = {irr:.3f}, p = {p:.3g}")
    except Exception as e:
        w(f"  (failed: {e})")
else:
    w("  (skipped — no citations_total column)")
w()

# ================================================================
# 6. JIF-normalized analysis
# ================================================================
w("=" * 70)
w("6. JIF-NORMALIZED CITATIONS")
w("=" * 70)
w()

df_cit["jif_norm"] = df_cit["citations_per_year"] / df_cit["jif"]
sub = df_cit.dropna(subset=["active_ratio", "jif_norm"])
slope, ic, r, p, se = stats.linregress(sub["active_ratio"], sub["jif_norm"])
sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."
w(f"JIF-normalized citations vs active voice:")
w(f"  N: {len(sub)}")
w(f"  Slope: {slope:+.4f}")
w(f"  SE: {se:.4f}")
w(f"  R²: {r**2:.4f}")
w(f"  p: {p:.4g} {sig}")
w()

# ================================================================
# Summary
# ================================================================
w("=" * 70)
w("SUMMARY OF KEY FINDINGS")
w("=" * 70)
w()
w(f"Sample size:                     {len(df_all)} papers")
w(f"Active voice overall mean:       {overall_mean:.3f}")
w(f"Active voice range:              {df_all['active_ratio'].min():.3f} – {df_all['active_ratio'].max():.3f}")
highest = max(journal_stats, key=lambda s: s[2])
lowest = min(journal_stats, key=lambda s: s[2])
w(f"Highest journal:                 {highest[0]} ({highest[2]:.3f})")
w(f"Lowest journal:                  {lowest[0]} ({lowest[2]:.3f})")

w()
w(f"Sample-wide temporal trend:      {temporal_slope:+.5f}/year (p = {temporal_p:.2e}, R² = {temporal_r2:.3f})")
w()

w("=" * 70)
w("END OF SUMMARY")
w("=" * 70)

with open(OUT_PATH, "w") as f:
    f.write("\n".join(lines))

print(f"\n✓ Wrote {OUT_PATH}")
