# scripts/make_fig8_irr.py
# Figure 8: incidence rate ratios from negative binomial regression.

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm

BASE     = "/Users/reganwhite/Desktop/Scientific_Writing/Class_Project"
ANALYSIS = os.path.join(BASE, "analysis")
MASTER   = os.path.join(ANALYSIS, "master_with_jif.csv")
FIGDIR   = os.path.join(ANALYSIS, "figures")

df = pd.read_csv(MASTER)
for c in ["active_ratio", "citations_total", "jif", "years_since"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df = df.dropna(subset=["active_ratio", "citations_total", "jif", "years_since"])
df = df[df["citations_total"] > 0]

X = sm.add_constant(df[["active_ratio", "jif"]])
offset = np.log(df["years_since"])
m = sm.GLM(df["citations_total"], X,
           family=sm.families.NegativeBinomial(), offset=offset).fit()

# IRR and CI
irr = np.exp(m.params)
ci_low = np.exp(m.conf_int()[0])
ci_high = np.exp(m.conf_int()[1])

# Rescale active_ratio IRR to per-0.1 for interpretability
irr_active_10 = irr["active_ratio"] ** 0.10
ci_active_10_low = ci_low["active_ratio"] ** 0.10
ci_active_10_high = ci_high["active_ratio"] ** 0.10

labels = ["Active voice\n(per 0.10 increase)", "JIF\n(per 1.0 unit increase)"]
irr_vals = [irr_active_10, irr["jif"]]
ci_lows = [ci_active_10_low, ci_low["jif"]]
ci_highs = [ci_active_10_high, ci_high["jif"]]

fig, ax = plt.subplots(figsize=(8, 5))
y_pos = np.arange(len(labels))
ax.barh(y_pos, irr_vals, color=["#228B22", "#2a7eb8"],
        alpha=0.85, edgecolor="black", linewidth=0.7)
ax.errorbar(irr_vals, y_pos,
            xerr=[np.array(irr_vals) - np.array(ci_lows),
                  np.array(ci_highs) - np.array(irr_vals)],
            fmt="none", ecolor="black", capsize=6, linewidth=1.5)
ax.axvline(1.0, color="black", linestyle="--", linewidth=1.2,
           label="No effect (IRR = 1)")
ax.set_yticks(y_pos)
ax.set_yticklabels(labels)
ax.set_xlabel("Incidence Rate Ratio (IRR)")
ax.set_title("Negative binomial regression: incidence rate ratios")
ax.legend()
for i, (v, l, h) in enumerate(zip(irr_vals, ci_lows, ci_highs)):
    ax.text(v * 1.02, i, f"{v:.2f} [{l:.2f}, {h:.2f}]",
            va="center", fontsize=10, fontfamily="monospace")
ax.set_xlim(0.9, max(ci_highs) * 1.2)
ax.grid(True, alpha=0.3, axis="x")
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "fig8_irr.png"))
plt.close(fig)
print("Wrote fig8_irr.png")
print(f"Active voice IRR (per 0.10): {irr_active_10:.3f} [{ci_active_10_low:.3f}, {ci_active_10_high:.3f}]")
print(f"JIF IRR (per 1.0):           {irr['jif']:.3f} [{ci_low['jif']:.3f}, {ci_high['jif']:.3f}]")
