# scripts/make_fig5_models.py
# Figure 5: active voice coefficient across four model specifications.
# Visualizes how the effect changes as covariates are added.

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm

from colors import journal_color

BASE     = "/Users/reganwhite/Desktop/Scientific_Writing/Class_Project"
ANALYSIS = os.path.join(BASE, "analysis")
MASTER   = os.path.join(ANALYSIS, "master_with_jif.csv")
FIGDIR   = os.path.join(ANALYSIS, "figures")
os.makedirs(FIGDIR, exist_ok=True)

plt.rcParams["savefig.dpi"] = 300
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["font.size"] = 12

df = pd.read_csv(MASTER)
df["active_ratio"] = pd.to_numeric(df["active_ratio"], errors="coerce")
df["citations_per_year"] = pd.to_numeric(df["citations_per_year"], errors="coerce")
df = df.dropna(subset=["active_ratio", "citations_per_year", "jif"])
print(f"Loaded {len(df)} papers with complete data")

y = df["citations_per_year"]

models = []

# Model 1: active only
X = sm.add_constant(df[["active_ratio"]])
m = sm.OLS(y, X).fit()
models.append(("Model 1\nActive voice only", m.params["active_ratio"],
               m.bse["active_ratio"], m.pvalues["active_ratio"], m.rsquared))

# Model 2: + JIF
X = sm.add_constant(df[["active_ratio", "jif"]])
m = sm.OLS(y, X).fit()
models.append(("Model 2\n+ Journal Impact Factor", m.params["active_ratio"],
               m.bse["active_ratio"], m.pvalues["active_ratio"], m.rsquared))

# Model 3: + year
X = sm.add_constant(df[["active_ratio", "jif", "year"]])
m = sm.OLS(y, X).fit()
models.append(("Model 3\n+ Publication year", m.params["active_ratio"],
               m.bse["active_ratio"], m.pvalues["active_ratio"], m.rsquared))

# Model 4: + journal FE
X = pd.get_dummies(df[["active_ratio", "jif", "year", "journal"]],
                   columns=["journal"], drop_first=True, dtype=float)
X = sm.add_constant(X)
m = sm.OLS(y, X).fit()
models.append(("Model 4\n+ Journal fixed effects", m.params["active_ratio"],
               m.bse["active_ratio"], m.pvalues["active_ratio"], m.rsquared))

# ---- Plot ----
fig, ax = plt.subplots(figsize=(10, 6))

labels = [m[0] for m in models]
coefs  = [m[1] for m in models]
ses    = [m[2] for m in models]
pvals  = [m[3] for m in models]
r2s    = [m[4] for m in models]

y_pos = np.arange(len(models))
# CI = ±1.96 * SE
err = [1.96 * se for se in ses]

# Bars
colors = ["#2a7eb8", "#27ae60", "#8e44ad", "#c0392b"]
ax.barh(y_pos, coefs, color=colors, alpha=0.85,
        edgecolor="black", linewidth=0.7)
ax.errorbar(coefs, y_pos, xerr=err, fmt="none",
            ecolor="black", capsize=6, linewidth=1.5)

ax.axvline(0, color="black", linewidth=1.2)
ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=11)
ax.set_xlabel("Active voice coefficient (extra citations per year per unit active ratio)")
ax.set_title("Active voice effect across model specifications")

# Annotate coefficients and R²
for i, (coef, p, r2) in enumerate(zip(coefs, pvals, r2s)):
    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."
    x_pos = coef + 1.96 * ses[i] + 0.4
    ax.text(x_pos, i, f"{coef:+.2f} {sig}\nR² = {r2:.3f}",
            va="center", fontsize=10, fontfamily="monospace")

ax.set_xlim(0, max(coefs) + 5)
ax.grid(True, alpha=0.3, axis="x")
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "fig5_model_comparison.png"))
plt.close(fig)
print("Wrote fig5_model_comparison.png")
for label, coef, se, p, r2 in models:
    print(f"  {label.replace(chr(10), ' '):45s}  b = {coef:+.3f}  p = {p:.3g}  R² = {r2:.3f}")
