# scripts/make_fig1_combined.py
# Figure 1 (combined):
#   - Top panel: overall active + passive voice over time (all 980 papers)
#   - Bottom grid: same, one panel per journal (7 panels in a 4-col grid)

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from colors import COLOR_ACTIVE, COLOR_PASSIVE, journal_color, journal_short

BASE     = "/Users/reganwhite/Desktop/Scientific_Writing/Class_Project"
ANALYSIS = os.path.join(BASE, "analysis")
MASTER   = os.path.join(ANALYSIS, "master_with_citations.csv")
FIGDIR   = os.path.join(ANALYSIS, "figures")
os.makedirs(FIGDIR, exist_ok=True)

plt.rcParams["savefig.dpi"] = 300
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["font.size"] = 11

# ---- Load ----
df = pd.read_csv(MASTER)
df["active_ratio"]  = pd.to_numeric(df["active_ratio"], errors="coerce")
df["passive_ratio"] = 1 - df["active_ratio"]
df["year"] = df["year"].astype(int)
df = df.dropna(subset=["active_ratio"])

print(f"Loaded {len(df)} papers")

# ---- Aggregate ----
def agg_block(g):
    return pd.Series({
        "active_mean":  g["active_ratio"].mean(),
        "active_se":    g["active_ratio"].std() / np.sqrt(len(g)),
        "passive_mean": g["passive_ratio"].mean(),
        "passive_se":   g["passive_ratio"].std() / np.sqrt(len(g)),
        "n":            len(g),
    })

by_year = df.groupby("year").apply(agg_block).reset_index()
by_jy   = df.groupby(["journal", "year"]).apply(agg_block).reset_index()

years_ticks = sorted(df["year"].unique())

# ---- Build figure ----
journals = sorted(df["journal"].unique())
n_j = len(journals)
ncols = 4
nrows = 1 + ((n_j + ncols - 1) // ncols)   # 1 for overall + rows for journals

fig = plt.figure(figsize=(4*ncols, 3.0*nrows + 2.5))   # extra height for the big panel
gs = fig.add_gridspec(nrows, ncols, height_ratios=[2.2] + [1.0]*(nrows - 1))

# ==================================================================
# Top panel: overall
# ==================================================================
ax = fig.add_subplot(gs[0, :])

# Active
ax.plot(by_year["year"], by_year["active_mean"],
        marker="o", markersize=9, linewidth=2.6,
        color=COLOR_ACTIVE, label="Active voice", zorder=3)
ax.fill_between(by_year["year"],
                by_year["active_mean"] - by_year["active_se"],
                by_year["active_mean"] + by_year["active_se"],
                color=COLOR_ACTIVE, alpha=0.18, zorder=2)

# Passive
ax.plot(by_year["year"], by_year["passive_mean"],
        marker="s", markersize=9, linewidth=2.6, linestyle="--",
        color=COLOR_PASSIVE, label="Passive voice", zorder=3)
ax.fill_between(by_year["year"],
                by_year["passive_mean"] - by_year["passive_se"],
                by_year["passive_mean"] + by_year["passive_se"],
                color=COLOR_PASSIVE, alpha=0.18, zorder=2)

# n annotations
for _, r in by_year.iterrows():
    ax.text(r["year"], r["active_mean"] + 0.03,
            f"n={int(r['n'])}",
            ha="center", va="bottom", fontsize=9, color="#444")

ax.axhline(0.5, color="grey", linestyle=":", linewidth=1, alpha=0.6)
ax.set_xticks(years_ticks)
ax.set_ylim(0, 1)
ax.set_xlim(2003, 2027)
ax.set_ylabel("Proportion of sentences")
ax.set_title("Overall: active and passive voice over time", fontsize=13)
ax.legend(loc="center right", frameon=True, fontsize=10)
ax.grid(True, alpha=0.3)

# ==================================================================
# Bottom panels: per journal
# ==================================================================
for i, journal in enumerate(journals):
    row = 1 + i // ncols
    col = i % ncols
    ax = fig.add_subplot(gs[row, col])

    g = by_jy[by_jy["journal"] == journal].sort_values("year")
    jc = journal_color(journal)

    # Active (solid, journal color)
    ax.plot(g["year"], g["active_mean"], marker="o",
            color=COLOR_ACTIVE, linewidth=2, markersize=5,
            label="Active", zorder=3)
    ax.fill_between(g["year"], g["active_mean"] - g["active_se"],
                    g["active_mean"] + g["active_se"],
                    color=COLOR_ACTIVE, alpha=0.18, zorder=2)

    # Passive (dashed, red)
    ax.plot(g["year"], g["passive_mean"], marker="s", linestyle="--",
            color=COLOR_PASSIVE, linewidth=2, markersize=5,
            label="Passive", zorder=3)
    ax.fill_between(g["year"], g["passive_mean"] - g["passive_se"],
                    g["passive_mean"] + g["passive_se"],
                    color=COLOR_PASSIVE, alpha=0.18, zorder=2)

    # Title color = the journal's canonical color
    ax.set_title(journal_short(journal), fontsize=11, color=jc)
    ax.set_xticks(years_ticks)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.25)
    if i == 0:
        ax.legend(fontsize=8, loc="center right")

# Hide any unused axes
for j in range(1 + n_j, nrows * ncols):
    ax = fig.add_subplot(gs[j // ncols, j % ncols])
    ax.axis("off")

fig.suptitle("Active vs passive voice usage over time",
             fontsize=15, fontweight="bold", y=0.998)
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(os.path.join(FIGDIR, "fig1_combined.png"))
plt.close(fig)
print("\nWrote fig1_combined.png")
