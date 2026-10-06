# scripts/make_fig6_jif.py
# Figure 6: citations per year vs journal impact factor, colored by journal.

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

from colors import journal_color, journal_short

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
df["jif"] = pd.to_numeric(df["jif"], errors="coerce")
df = df.dropna(subset=["jif", "citations_per_year"])
print(f"Loaded {len(df)} papers")

journals = sorted(df["journal"].unique())

fig, ax = plt.subplots(figsize=(10, 6.5))

# Jitter x slightly so overlapping JIF values separate visually
rng = np.random.default_rng(42)
jitter = rng.normal(0, 0.06, len(df))

for journal in journals:
    g = df[df["journal"] == journal]
    ax.scatter(g["jif"] + jitter[g.index], g["citations_per_year"],
               s=22, alpha=0.55, color=journal_color(journal),
               edgecolors="white", linewidths=0.4,
               label=journal_short(journal), zorder=2)

# Overall fit
x = df["jif"].values
y = df["citations_per_year"].values
slope, intercept, r, p, se = stats.linregress(x, y)

xs = np.linspace(x.min(), x.max(), 100)
ys = intercept + slope * xs
ax.plot(xs, ys, color="black", linewidth=2.5, zorder=4)

# CI band
n = len(x)
resid = y - (intercept + slope * x)
s_err = np.sqrt(np.sum(resid**2) / (n - 2))
x_mean = x.mean()
sxx = np.sum((x - x_mean) ** 2)
se_fit = s_err * np.sqrt(1/n + (xs - x_mean)**2 / sxx)
ax.fill_between(xs, ys - 1.96*se_fit, ys + 1.96*se_fit,
                color="black", alpha=0.12, linewidth=0)

ax.set_xlabel("Journal Impact Factor")
ax.set_ylabel("Citations per year")
ax.set_title("Citations per year vs Journal Impact Factor")
ax.set_ylim(0, np.percentile(y, 99) * 1.15)
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=10)
ax.grid(True, alpha=0.25)

# Stat annotation
sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."
txt = (f"b = {slope:+.2f}\n"
       f"R² = {r**2:.3f}\n"
       f"p = {p:.3g} {sig}\n"
       f"n = {n}")
ax.text(0.025, 0.97, txt, transform=ax.transAxes, va="top", ha="left",
        fontsize=11, fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                  alpha=0.9, edgecolor="black"))

fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "fig6_jif_vs_citations.png"))
plt.close(fig)
print("Wrote fig6_jif_vs_citations.png")
print(f"  b = {slope:+.3f}  R² = {r**2:.4f}  p = {p:.3g}")
