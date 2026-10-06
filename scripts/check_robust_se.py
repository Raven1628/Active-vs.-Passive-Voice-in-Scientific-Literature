# scripts/check_robust_se.py
# Compare OLS standard errors to HC3 robust standard errors for Model 2.

import os
import pandas as pd
import statsmodels.api as sm

BASE     = "/Users/reganwhite/Desktop/Scientific_Writing/Class_Project"
ANALYSIS = os.path.join(BASE, "analysis")
MASTER   = os.path.join(ANALYSIS, "master_with_jif.csv")

df = pd.read_csv(MASTER)
df["active_ratio"] = pd.to_numeric(df["active_ratio"], errors="coerce")
df["citations_per_year"] = pd.to_numeric(df["citations_per_year"], errors="coerce")
df["jif"] = pd.to_numeric(df["jif"], errors="coerce")
df = df.dropna(subset=["active_ratio", "citations_per_year", "jif"])
print(f"Loaded {len(df)} papers")

y = df["citations_per_year"]
X = sm.add_constant(df[["active_ratio", "jif"]])

m_ols    = sm.OLS(y, X).fit()
m_robust = sm.OLS(y, X).fit(cov_type="HC3")

print("\n=== Standard OLS ===")
print(m_ols.summary().tables[1])
print(f"R² = {m_ols.rsquared:.4f}")

print("\n=== HC3 robust standard errors ===")
print(m_robust.summary().tables[1])
print(f"R² = {m_robust.rsquared:.4f}")

print("\n=== Side-by-side for active_ratio ===")
print(f"OLS:    b = {m_ols.params['active_ratio']:+.3f}  SE = {m_ols.bse['active_ratio']:.3f}  p = {m_ols.pvalues['active_ratio']:.4g}")
print(f"Robust: b = {m_robust.params['active_ratio']:+.3f}  SE = {m_robust.bse['active_ratio']:.3f}  p = {m_robust.pvalues['active_ratio']:.4g}")
