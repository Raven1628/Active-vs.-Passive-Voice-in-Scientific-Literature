# scripts/make_all_tables.py
# Generates Tables 1-4 (main text) and S1-S2 (supplement).

import os
import numpy as np
import pandas as pd
import statsmodels.api as sm

BASE     = "/Users/reganwhite/Desktop/Scientific_Writing/Class_Project"
ANALYSIS = os.path.join(BASE, "analysis")
MASTER   = os.path.join(ANALYSIS, "master_with_jif.csv")
OUTDIR   = os.path.join(ANALYSIS, "output")
os.makedirs(OUTDIR, exist_ok=True)

df = pd.read_csv(MASTER)
for c in ["active_ratio", "citations_per_year", "citations_total", "jif", "year", "years_since"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
df["passive_ratio"] = 1 - df["active_ratio"]

print(f"Loaded {len(df)} papers")


# ==================================================================
# Table 1 — Sample composition by journal × year
# ==================================================================
t1 = df.pivot_table(index="journal", columns="year",
                    values="paper_id", aggfunc="count", fill_value=0)
t1 = t1.reindex(columns=[2005, 2010, 2015, 2020, 2025], fill_value=0)
t1["Total"] = t1.sum(axis=1)
t1.loc["Total"] = t1.sum()
t1 = t1.sort_index()
t1.to_csv(os.path.join(OUTDIR, "table1_sample_composition.csv"))
print("\n=== TABLE 1: Sample composition ===")
print(t1.to_string())


# ==================================================================
# Table 2 — Mean active voice by journal with 95% CI
# ==================================================================
rows = []
for j, g in df.groupby("journal"):
    n = len(g)
    m = g["active_ratio"].mean()
    s = g["active_ratio"].std()
    se = s / np.sqrt(n)
    ci_lo = m - 1.96 * se
    ci_hi = m + 1.96 * se
    rows.append({"journal": j, "n": n, "mean": m, "sd": s,
                 "ci_low": ci_lo, "ci_high": ci_hi})
t2 = pd.DataFrame(rows).sort_values("mean", ascending=False).round(4)
t2.to_csv(os.path.join(OUTDIR, "table2_journal_means.csv"), index=False)
print("\n=== TABLE 2: Journal means ===")
print(t2.to_string(index=False))


# ==================================================================
# Table 3 — Per-journal temporal trends
# ==================================================================
from scipy import stats
rows = []
for j, g in df.groupby("journal"):
    slope, intercept, r, p, se = stats.linregress(g["year"], g["active_ratio"])
    direction = ("↑ Significant" if p < 0.05 and slope > 0
                 else "↓ Significant" if p < 0.05 and slope < 0
                 else "n.s.")
    rows.append({"journal": j, "slope_per_year": slope, "se": se,
                 "p_value": p, "direction": direction})
# Sample-wide
slope, intercept, r, p, se = stats.linregress(df["year"], df["active_ratio"])
rows.append({"journal": "Sample-wide", "slope_per_year": slope, "se": se,
             "p_value": p, "direction": "↑ Significant" if p < 0.05 else "n.s."})
t3 = pd.DataFrame(rows)
t3["slope_per_year"] = t3["slope_per_year"].round(4)
t3["se"] = t3["se"].round(4)
t3["p_value"] = t3["p_value"].apply(lambda x: "<0.001" if x < 0.001 else f"{x:.3f}")
t3.to_csv(os.path.join(OUTDIR, "table3_journal_trends.csv"), index=False)
print("\n=== TABLE 3: Per-journal temporal trends ===")
print(t3.to_string(index=False))


# ==================================================================
# Table 4 — Model comparison
# ==================================================================
df4 = df.dropna(subset=["active_ratio", "citations_per_year", "jif", "year"]).copy()
y = df4["citations_per_year"]

def fit_model(X_cols, journal_fe=False):
    if journal_fe:
        X = pd.get_dummies(df4[X_cols + ["journal"]],
                           columns=["journal"], drop_first=True, dtype=float)
    else:
        X = df4[X_cols].copy()
    X = sm.add_constant(X)
    m = sm.OLS(y, X).fit()
    return m

m1 = fit_model(["active_ratio"])
m2 = fit_model(["active_ratio", "jif"])
m3 = fit_model(["active_ratio", "jif", "year"])
m4 = fit_model(["active_ratio", "jif", "year"], journal_fe=True)

def star(p):
    if pd.isna(p): return ""
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""

def fmt(m, var):
    if var not in m.params:
        return "—"
    return f"{m.params[var]:+.3f}{star(m.pvalues[var])} ({m.bse[var]:.3f})"

t4 = pd.DataFrame({
    "Predictor": ["Active voice", "Journal Impact Factor",
                  "Publication year", "Journal fixed effects",
                  "R²", "N"],
    "Model 1": [fmt(m1, "active_ratio"), "—", "—", "No",
                f"{m1.rsquared:.3f}", int(m1.nobs)],
    "Model 2": [fmt(m2, "active_ratio"), fmt(m2, "jif"), "—", "No",
                f"{m2.rsquared:.3f}", int(m2.nobs)],
    "Model 3": [fmt(m3, "active_ratio"), fmt(m3, "jif"), fmt(m3, "year"), "No",
                f"{m3.rsquared:.3f}", int(m3.nobs)],
    "Model 4": [fmt(m4, "active_ratio"), fmt(m4, "jif"), fmt(m4, "year"), "Yes",
                f"{m4.rsquared:.3f}", int(m4.nobs)],
})
t4.to_csv(os.path.join(OUTDIR, "table4_model_comparison.csv"), index=False)
print("\n=== TABLE 4: Model comparison ===")
print(t4.to_string(index=False))


# ==================================================================
# Table S1 — Negative binomial
# ==================================================================
df_nb = df.dropna(subset=["active_ratio", "citations_total", "jif", "years_since"]).copy()
df_nb = df_nb[df_nb["citations_total"] > 0]
X = sm.add_constant(df_nb[["active_ratio", "jif"]])
offset = np.log(df_nb["years_since"])
m_nb = sm.GLM(df_nb["citations_total"], X,
              family=sm.families.NegativeBinomial(), offset=offset).fit()

coef_ar = m_nb.params["active_ratio"]
se_ar = m_nb.bse["active_ratio"]
# Rescale to per-0.10 active increase
coef_ar_10 = coef_ar * 0.10
se_ar_10 = se_ar * 0.10
irr_10 = np.exp(coef_ar_10)
ci_low_10 = np.exp(coef_ar_10 - 1.96 * se_ar_10)
ci_high_10 = np.exp(coef_ar_10 + 1.96 * se_ar_10)

coef_jif = m_nb.params["jif"]
se_jif = m_nb.bse["jif"]
irr_jif = np.exp(coef_jif)
ci_low_jif = np.exp(coef_jif - 1.96 * se_jif)
ci_high_jif = np.exp(coef_jif + 1.96 * se_jif)

def fmt_p(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"

tS1 = pd.DataFrame([
    {"Predictor": "Active voice (per 0.10)",
     "Coefficient": f"{coef_ar_10:+.3f}",
     "SE": f"{se_ar_10:.3f}",
     "IRR": f"{irr_10:.2f}",
     "95% CI": f"[{ci_low_10:.2f}, {ci_high_10:.2f}]",
     "p-value": fmt_p(m_nb.pvalues["active_ratio"])},
    {"Predictor": "Journal Impact Factor (per 1.0)",
     "Coefficient": f"{coef_jif:+.3f}",
     "SE": f"{se_jif:.3f}",
     "IRR": f"{irr_jif:.2f}",
     "95% CI": f"[{ci_low_jif:.2f}, {ci_high_jif:.2f}]",
     "p-value": fmt_p(m_nb.pvalues["jif"])},
])
tS1.to_csv(os.path.join(OUTDIR, "tableS1_negbin.csv"), index=False)
print(f"\n=== TABLE S1: Negative binomial (N = {int(m_nb.nobs)}) ===")
print(tS1.to_string(index=False))


# ==================================================================
# Table S2 — Descriptives by year
# ==================================================================
rows = []
for y, g in df.groupby("year"):
    n = len(g)
    rows.append({
        "year": int(y),
        "n": n,
        "mean_active": round(g["active_ratio"].mean(), 3),
        "sd_active": round(g["active_ratio"].std(), 3),
        "mean_cites_per_year": round(g["citations_per_year"].mean(), 2),
        "sd_cites_per_year": round(g["citations_per_year"].std(), 2),
    })
tS2 = pd.DataFrame(rows).sort_values("year")
tS2.to_csv(os.path.join(OUTDIR, "tableS2_descriptives_by_year.csv"), index=False)
print("\n=== TABLE S2: Descriptives by year ===")
print(tS2.to_string(index=False))


print(f"\n\nAll tables written to: {OUTDIR}")
