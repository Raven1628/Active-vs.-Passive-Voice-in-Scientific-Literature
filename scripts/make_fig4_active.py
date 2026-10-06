# scripts/make_fig4_active.py
# Figure 4 (active voice):
#   - Top panel: overall fit — BLACK points, forest green fit line
#   - Sub-panels: per journal — journal-colored points, black fit lines

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

from colors import COLOR_ACTIVE, journal_color, journal_short

BASE     = "/Users/reganwhite/Desktop/Scientific_Writing/Class_Project"
ANALYSIS = os.path.join(BASE, "analysis")
MASTER   = os.path.join(ANALYSIS, "master_with_citations.csv")
FIGDIR   = os.path.join(ANALYSIS, "figures")
os.makedirs(FIGDIR, exist_ok=True)

plt.rcParams["savefig.dpi"] = 300
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["font.size"] = 11

df = pd.read_csv(MASTER)
df["active_ratio"] = pd.to_numeric(df["active_ratio"], errors="coerce")
df["citations_per_year"] = pd.to_numeric(df["citations_per_year"], errors="coerce")
df = df.dropna(subset=["active_ratio", "citations_per_year"])
print(f"Loaded {len(df)} papers with citations")


def fit_and_plot(ax, x, y, xlabel, ylabel, title,
                 point_color, line_color="black", point_size=20):
    slope, intercept, r, p, se = stats.linregress(x, y)

    ax.scatter(x, y, s=point_size, alpha=0.5, color=point_color,
               edgecolors="white", linewidths=0.4, zorder=2)

    xs = np.linspace(x.min(), x.max(), 100)
    ys = intercept + slope * xs
    ax.plot(xs, ys, color=line_color, linewidth=2.0, zorder=3)

    n = len(x)
    resid = y - (intercept + slope * x)
    s_err = np.sqrt(np.sum(resid**2) / max(n - 2, 1))
    x_mean = x.mean()
    sxx = np.sum((x - x_mean) ** 2)
    if sxx > 0:
        se_fit = s_err * np.sqrt(1/n + (xs - x_mean)**2 / sxx)
        ax.fill_between(xs, ys - 1.96*se_fit, ys + 1.96*se_fit,
                        color=line_color, alpha=0.12, linewidth=0, zorder=1)

    ax.set_title(f"{title}  (n={n})", fontsize=11)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."
    txt = f"b = {slope:+.2f}\nR² = {r**2:.3f}\np = {p:.3g} {sig}"
    ax.text(0.04, 0.96, txt,
            transform=ax.transAxes, va="top", ha="left",
            fontsize=9, fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.35",
                      facecolor="white", alpha=0.85,
                      edgecolor=line_color))

    y_upper = np.percentile(y, 99) * 1.15
    ax.set_ylim(0, max(y_upper, 5))

    return slope, r**2, p


journals = sorted(df["journal"].unique())
n_j = len(journals)
ncols = 4
nrows = 1 + ((n_j + ncols - 1) // ncols)

fig = plt.figure(figsize=(4*ncols, 4*nrows))
gs = fig.add_gridspec(nrows, ncols)

# ---------- Overall panel: BLACK points, green fit line ----------
ax_overall = fig.add_subplot(gs[0, :])
s_overall, r2_overall, p_overall = fit_and_plot(
    ax_overall,
    df["active_ratio"].values, df["citations_per_year"].values,
    "Active voice score", "Citations per year", "Overall",
    point_color="black",
    line_color=COLOR_ACTIVE,
    point_size=18)
print(f"Overall:  b = {s_overall:+.2f}  R² = {r2_overall:.3f}  p = {p_overall:.3g}")

# ---------- Per-journal panels ----------
for i, journal in enumerate(journals):
    ax = fig.add_subplot(gs[1 + i // ncols, i % ncols])
    g = df[df["journal"] == journal]
    s_j, r2_j, p_j = fit_and_plot(
        ax, g["active_ratio"].values, g["citations_per_year"].values,
        "Active voice score", "Citations per year", journal_short(journal),
        point_color=journal_color(journal),
        line_color="black",
        point_size=14)
    print(f"{journal:40s}  b = {s_j:+.2f}  R² = {r2_j:.3f}  p = {p_j:.3g}")

for j in range(1 + n_j, nrows * ncols):
    ax = fig.add_subplot(gs[j // ncols, j % ncols])
    ax.axis("off")

fig.suptitle("Citations per year vs active voice score",
             fontsize=15, fontweight="bold", y=0.995)
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(os.path.join(FIGDIR, "fig4_active.png"))
plt.close(fig)
print("\nWrote fig4_active.png")
