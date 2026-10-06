# scripts/make_fig9_normalized.py
# Figure 9: citations vs voice score, raw vs JIF-normalized.
# Two rows: raw (top) and JIF-normalized (bottom).
# Two columns: active voice (left) and passive voice (right).

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

from colors import COLOR_ACTIVE, COLOR_PASSIVE

BASE     = "/Users/reganwhite/Desktop/Scientific_Writing/Class_Project"
ANALYSIS = os.path.join(BASE, "analysis")
MASTER   = os.path.join(ANALYSIS, "master_with_jif.csv")
FIGDIR   = os.path.join(ANALYSIS, "figures")
os.makedirs(FIGDIR, exist_ok=True)

plt.rcParams["savefig.dpi"] = 300
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["font.size"] = 11

df = pd.read_csv(MASTER)
for c in ["active_ratio", "citations_per_year", "jif"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df = df.dropna(subset=["active_ratio", "citations_per_year", "jif"])
df["passive_ratio"] = 1 - df["active_ratio"]
print(f"Loaded {len(df)} papers")

# ---- Compute JIF-normalized citations ----
# Ratio approach: citations per year per unit JIF
df["citations_per_jif"] = df["citations_per_year"] / df["jif"]

# Log approach (alternative) — commented out; swap in if you prefer
# df["citations_per_jif"] = np.log1p(df["citations_per_year"]) / df["jif"]


def fit_and_plot(ax, x, y, xlabel, ylabel, title, color, ylim=None):
    slope, intercept, r, p, se = stats.linregress(x, y)

    ax.scatter(x, y, s=18, alpha=0.45, color=color,
               edgecolors="white", linewidths=0.3, zorder=2)

    xs = np.linspace(x.min(), x.max(), 100)
    ys = intercept + slope * xs
    ax.plot(xs, ys, color="black", linewidth=2.0, zorder=3)

    n = len(x)
    resid = y - (intercept + slope * x)
    s_err = np.sqrt(np.sum(resid**2) / (n - 2))
    x_mean = x.mean()
    sxx = np.sum((x - x_mean) ** 2)
    se_fit = s_err * np.sqrt(1/n + (xs - x_mean)**2 / sxx)
    ax.fill_between(xs, ys - 1.96*se_fit, ys + 1.96*se_fit,
                    color="black", alpha=0.10, linewidth=0, zorder=1)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."
    txt = f"b = {slope:+.3f}\nR² = {r**2:.3f}\np = {p:.3g} {sig}"
    ax.text(0.03, 0.97, txt, transform=ax.transAxes,
            va="top", ha="left", fontsize=9.5, fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      alpha=0.9, edgecolor=color))

    if ylim:
        ax.set_ylim(*ylim)
    else:
        ax.set_ylim(0, np.percentile(y, 99) * 1.15)

    return slope, r**2, p


# ---- Build 2x2 figure ----
fig, axes = plt.subplots(1, 2, figsize=(15, 6))

s1, r1, p1 = fit_and_plot(axes[0],
    df["active_ratio"].values, df["citations_per_year"].values,
    "Active voice score", "Citations per year",
    "Raw citations", COLOR_ACTIVE)
print(f"Raw active:        b = {s1:+.3f}  R² = {r1:.4f}  p = {p1:.3g}")

s3, r3, p3 = fit_and_plot(axes[1],
    df["active_ratio"].values, df["citations_per_jif"].values,
    "Active voice score", "Citations per year / JIF",
    "JIF-normalized citations", COLOR_ACTIVE)
print(f"Normalized active: b = {s3:+.3f}  R² = {r3:.4f}  p = {p3:.3g}")

fig.suptitle("Active voice vs citations: raw and JIF-normalized",
             fontsize=15, fontweight="bold", y=0.99)
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(os.path.join(FIGDIR, "fig9_active_raw_vs_normalized.png"))
plt.close(fig)
print("\nWrote fig9_normalized_comparison.png")
