# scripts/analyze_with_jif.py
import os
import pandas as pd
import statsmodels.api as sm

BASE     = "/Users/reganwhite/Desktop/Scientific_Writing/Class_Project"
ANALYSIS = os.path.join(BASE, "analysis")
MASTER   = os.path.join(ANALYSIS, "master_with_citations.csv")
JIF_CSV  = os.path.join(BASE, "scripts", "jif_lookup.csv")
OUT_CSV  = os.path.join(ANALYSIS, "master_with_jif.csv")

df = pd.read_csv(MASTER)
jif = pd.read_csv(JIF_CSV)
print(f"Loaded {len(df)} papers and {len(jif)} JIF entries")

jif["year"] = jif["year"].astype(int)
df["year"]  = df["year"].astype(int)
df = df.merge(jif, on=["journal", "year"], how="left")

missing = df["jif"].isna().sum()
print(f"Papers with JIF: {len(df)-missing}/{len(df)}  (missing {missing})")

df["active_ratio"] = pd.to_numeric(df["active_ratio"], errors="coerce")
df["citations_per_year"] = pd.to_numeric(df["citations_per_year"], errors="coerce")
df = df.dropna(subset=["active_ratio", "citations_per_year", "jif"])
df.to_csv(OUT_CSV, index=False)
print(f"Wrote {OUT_CSV}")

y = df["citations_per_year"]

print("\n" + "="*70 + "\nModel 1: citations_per_year ~ active_ratio\n" + "="*70)
X = sm.add_constant(df[["active_ratio"]])
m = sm.OLS(y, X).fit()
print(m.summary().tables[1])
print(f"R² = {m.rsquared:.4f}")

print("\n" + "="*70 + "\nModel 2: citations_per_year ~ active_ratio + jif\n" + "="*70)
X = sm.add_constant(df[["active_ratio", "jif"]])
m = sm.OLS(y, X).fit()
print(m.summary().tables[1])
print(f"R² = {m.rsquared:.4f}")

print("\n" + "="*70 + "\nModel 3: citations_per_year ~ active_ratio + jif + year\n" + "="*70)
X = sm.add_constant(df[["active_ratio", "jif", "year"]])
m = sm.OLS(y, X).fit()
print(m.summary().tables[1])
print(f"R² = {m.rsquared:.4f}")

print("\n" + "="*70 + "\nModel 4: + journal fixed effects\n" + "="*70)
X = pd.get_dummies(df[["active_ratio", "jif", "year", "journal"]],
                   columns=["journal"], drop_first=True, dtype=float)
X = sm.add_constant(X)
m = sm.OLS(y, X).fit()
print(f"active_ratio: b={m.params['active_ratio']:+.3f}  SE={m.bse['active_ratio']:.3f}  p={m.pvalues['active_ratio']:.3g}")
print(f"jif:          b={m.params['jif']:+.3f}  SE={m.bse['jif']:.3f}  p={m.pvalues['jif']:.3g}")
print(f"year:         b={m.params['year']:+.3f}  SE={m.bse['year']:.3f}  p={m.pvalues['year']:.3g}")
print(f"R² = {m.rsquared:.4f}")
