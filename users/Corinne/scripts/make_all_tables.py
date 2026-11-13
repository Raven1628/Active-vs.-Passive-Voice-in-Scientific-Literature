# scripts/make_all_tables.py
# All tables built from master_with_jif_cleaned.csv (949-paper analysis sample).
# Table S1 (negative binomial) uses the 878-paper positive-citation subset.

import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS = os.path.join(BASE, "analysis")
MASTER   = os.path.join(ANALYSIS, "master_with_jif_cleaned.csv")
OUTDIR   = os.path.join(ANALYSIS, "final_figures")
OUTDIR2  = os.path.join(ANALYSIS, "output")
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(OUTDIR2, exist_ok=True)

df = pd.read_csv(MASTER)
for c in ["active_ratio","citations_per_year","citations_total",
          "jif","year","years_since"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
df["passive_ratio"] = 1 - df["active_ratio"]
print(f"Loaded {len(df)} papers")

def save(d, name):
    d.to_csv(os.path.join(OUTDIR,  name), index=False)
    d.to_csv(os.path.join(OUTDIR2, name), index=False)

# ---- Table 1 (949) ----
t1 = df.pivot_table(index="journal", columns="year",
                    values="paper_id", aggfunc="count", fill_value=0)
t1 = t1.reindex(columns=[2005,2010,2015,2020,2025], fill_value=0)
t1["Total"] = t1.sum(axis=1)
t1.loc["Total"] = t1.sum()
t1.index.name = "journal"
save(t1.reset_index(), "tableS1_sample_composition.csv")
print(f"\n=== TABLE 1 (N={int(t1.loc['Total','Total'])}) ===")
print(t1.to_string())

# ---- Table 2 (949) ----
rows = []
for j, g in df.groupby("journal"):
    n = len(g); m = g["active_ratio"].mean()
    s = g["active_ratio"].std(); se = s / np.sqrt(n)
    rows.append({"journal": j, "n": n, "mean": round(m,4), "sd": round(s,4),
                 "ci_low": round(m-1.96*se,4), "ci_high": round(m+1.96*se,4)})
t2 = pd.DataFrame(rows).sort_values("mean", ascending=False)
save(t2, "tableS2_journal_means.csv")
print(f"\n=== TABLE 2 (N={t2['n'].sum()}) ===")
print(t2.to_string(index=False))

# ---- Table 3 (949) ----
rows = []
for j, g in df.groupby("journal"):
    slope, _, _, p, se = stats.linregress(g["year"], g["active_ratio"])
    d = "↑ Significant" if p < 0.05 and slope > 0 else \
        "↓ Significant" if p < 0.05 and slope < 0 else "n.s."
    rows.append({"journal": j, "slope_per_year": round(slope,4),
                 "se": round(se,4),
                 "p_value": "<0.001" if p < 0.001 else f"{p:.3f}",
                 "direction": d})
slope, _, _, p, se = stats.linregress(df["year"], df["active_ratio"])
rows.append({"journal": "Sample-wide", "slope_per_year": round(slope,4),
             "se": round(se,4),
             "p_value": "<0.001" if p < 0.001 else f"{p:.3f}",
             "direction": "↑ Significant" if p < 0.05 else "n.s."})
t3 = pd.DataFrame(rows)
save(t3, "tableS3_journal_trends.csv")
print(f"\n=== TABLE 3 (N={len(df)}) ===")
print(t3.to_string(index=False))

# ---- Table 4 (949) ----
df4 = df.dropna(subset=["active_ratio","citations_per_year","jif","year"]).copy()
y = df4["citations_per_year"]
def fit(cols, jfe=False):
    X = pd.get_dummies(df4[cols+["journal"]], columns=["journal"],
                       drop_first=True, dtype=float) if jfe else df4[cols].copy()
    return sm.OLS(y, sm.add_constant(X)).fit()
m1 = fit(["active_ratio"])
m2 = fit(["active_ratio","jif"])
m3 = fit(["active_ratio","jif","year"])
m4 = fit(["active_ratio","jif","year"], jfe=True)
def star(p): return "***" if p<0.001 else "**" if p<0.01 else "*" if p<0.05 else ""
def fmt(m,v):
    return "—" if v not in m.params else f"{m.params[v]:+.3f}{star(m.pvalues[v])} ({m.bse[v]:.3f})"
t4 = pd.DataFrame({
    "Predictor": ["Active voice","Journal Impact Factor","Publication year",
                  "Journal fixed effects","R²","N"],
    "Model 1": [fmt(m1,"active_ratio"),"—","—","No",f"{m1.rsquared:.3f}",int(m1.nobs)],
    "Model 2": [fmt(m2,"active_ratio"),fmt(m2,"jif"),"—","No",f"{m2.rsquared:.3f}",int(m2.nobs)],
    "Model 3": [fmt(m3,"active_ratio"),fmt(m3,"jif"),fmt(m3,"year"),"No",f"{m3.rsquared:.3f}",int(m3.nobs)],
    "Model 4": [fmt(m4,"active_ratio"),fmt(m4,"jif"),fmt(m4,"year"),"Yes",f"{m4.rsquared:.3f}",int(m4.nobs)],
})
save(t4, "tableS4_model_comparison.csv")
print(f"\n=== TABLE 4 (N={int(m1.nobs)}) ===")
print(t4.to_string(index=False))

# ---- Table S1 (878) ----
df_nb = df.dropna(subset=["active_ratio","citations_total","jif","years_since"]).copy()
df_nb = df_nb[df_nb["citations_total"] > 0]
X = sm.add_constant(df_nb[["active_ratio","jif"]])
off = np.log(df_nb["years_since"])
m_nb = sm.GLM(df_nb["citations_total"], X,
              family=sm.families.NegativeBinomial(), offset=off).fit()
ca, sa = m_nb.params["active_ratio"]*0.10, m_nb.bse["active_ratio"]*0.10
cj, sj = m_nb.params["jif"], m_nb.bse["jif"]
fp = lambda p: "<0.001" if p < 0.001 else f"{p:.3f}"
tS1 = pd.DataFrame([
    {"Predictor":"Active voice (per 0.10)","Coefficient":f"{ca:+.3f}","SE":f"{sa:.3f}",
     "IRR":f"{np.exp(ca):.2f}",
     "95% CI":f"[{np.exp(ca-1.96*sa):.2f}, {np.exp(ca+1.96*sa):.2f}]",
     "p-value":fp(m_nb.pvalues["active_ratio"])},
    {"Predictor":"Journal Impact Factor (per 1.0)","Coefficient":f"{cj:+.3f}","SE":f"{sj:.3f}",
     "IRR":f"{np.exp(cj):.2f}",
     "95% CI":f"[{np.exp(cj-1.96*sj):.2f}, {np.exp(cj+1.96*sj):.2f}]",
     "p-value":fp(m_nb.pvalues["jif"])},
])
save(tS1, "tableS5_negbin.csv")
print(f"\n=== TABLE S1 (N={int(m_nb.nobs)}) ===")
print(tS1.to_string(index=False))

# ---- Table S2 (949) ----
rows = []
for y_, g in df.groupby("year"):
    rows.append({"year": int(y_), "n": len(g),
                 "mean_active": round(g["active_ratio"].mean(),3),
                 "sd_active": round(g["active_ratio"].std(),3),
                 "mean_cites_per_year": round(g["citations_per_year"].mean(),2),
                 "sd_cites_per_year": round(g["citations_per_year"].std(),2)})
tS2 = pd.DataFrame(rows).sort_values("year")
save(tS2, "tableS6_descriptives_by_year.csv")
print(f"\n=== TABLE S2 (N={tS2['n'].sum()}) ===")
print(tS2.to_string(index=False))

print("\nAll tables written.")
