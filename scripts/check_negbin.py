# scripts/check_negbin.py
# Negative binomial regression — appropriate for overdispersed count outcomes.
# Note: requires citations to be integer counts. We use citations_total / years_since
# and round to nearest integer if needed; alternatively use total citations with
# log(years) as offset. We'll use total citations and log-exposure offset.

import os
import pandas as pd
import numpy as np
import statsmodels.api as sm

BASE     = "/Users/reganwhite/Desktop/Scientific_Writing/Class_Project"
ANALYSIS = os.path.join(BASE, "analysis")
MASTER   = os.path.join(ANALYSIS, "master_with_jif.csv")

df = pd.read_csv(MASTER)
for c in ["active_ratio", "citations_total", "jif", "years_since"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df = df.dropna(subset=["active_ratio", "citations_total", "jif", "years_since"])
df = df[df["citations_total"] > 0]   # NB needs positive counts
print(f"Loaded {len(df)} papers with positive citations")

# Model: log(E[citations]) = b0 + b1*active + b2*jif + log(years_since) as offset
X = sm.add_constant(df[["active_ratio", "jif"]])
offset = np.log(df["years_since"])

m_nb = sm.GLM(df["citations_total"], X, family=sm.families.NegativeBinomial(),
              offset=offset).fit()

print("\n=== Negative Binomial Regression ===")
print(m_nb.summary())
print()
print(f"active_ratio: coef = {m_nb.params['active_ratio']:+.4f}  "
      f"IRR = {np.exp(m_nb.params['active_ratio']):.4f}  "
      f"p = {m_nb.pvalues['active_ratio']:.4g}")
print()
print("IRR interpretation: for each 1-unit increase in active_ratio,")
print(f"  citations are multiplied by {np.exp(m_nb.params['active_ratio']):.3f}")
