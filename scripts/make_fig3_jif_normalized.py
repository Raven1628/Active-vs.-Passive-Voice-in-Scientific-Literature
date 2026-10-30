# 13b_make_fig3_jif_normalized.py
# JIF-normalized citations vs active voice score.
# Panel (a): overall (all 926 papers)
# Panel (b): 7 panels, one per journal
# Reads from _github_original/analysis/master_with_jif.csv

import os
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from scipy import stats

plt.rcParams["savefig.dpi"] = 300
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["font.size"] = 11

JOURNAL_COLORS = {
    "Cancer":                           "#2a7eb8",
    "Clinical Genetics":                "#e07b39",
    "Clinical_Genetics":                "#e07b39",
    "Developmental Dynamics":           "#8e44ad",
    "Developmental_Dynamics":           "#8e44ad",
    "Ecology":                          "#27ae60",
    "Journal of Neuroscience Research": "#c0392b",
    "Journal_of_Neuroscience_Research": "#c0392b",
    "Molecular Ecology":                "#e91e8c",
    "Molecular_Ecology":                "#e91e8c",
    "Molecular Microbiology":           "#00bcd4",
    "Molecular_Microbiology":           "#00bcd4",
}

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(PROJECT_ROOT, "analysis", "master_with_jif_cleaned.csv")
OUT_DIR = os.path.join(PROJECT_ROOT, "manuscript")
os.makedirs(OUT_DIR, exist_ok=True)

if not os.path.exists(CSV):
    raise SystemExit(f"Missing CSV: {CSV}")

df = pd.read_csv(CSV)
print(f"Loaded {len(df)} papers")

# Detect active-ratio column
candidates = ["active_ratio", "paper_active_ratio", "active"]
ratio_col = next((c for c in candidates if c in df.columns), None)
if ratio_col is None:
    raise SystemExit(f"No active-ratio column. Columns: {list(df.columns)}")

# Detect JIF
if "jif" not in df.columns:
    raise SystemExit("No 'jif' column in CSV")

# Compute JIF-normalized citations per year
# Prefer existing 'citations_per_year', else compute from 'citations' and 'year'
if "citations_per_year" not in df.columns:
    if "citations" in df.columns and "year" in df.columns:
        cy = 2026  # current year for citations-per-year baseline
        df["citations_per_year"] = df["citations"] / (cy - df["year"]).clip(lower=1)
    else:
        raise SystemExit("Cannot compute citations_per_year")

df["jif_norm"] = df["citations_per_year"] / df["jif"].replace(0, np.nan)


# Drop rows without active_ratio, jif_norm
df = df.dropna(subset=[ratio_col, "jif_norm", "jif", "citations_per_year"])
print(f"Papers with active_ratio + JIF-normalized citations: {len(df)}")
print(f"Overall JIF-normalized mean: {df['jif_norm'].mean():.3f}")
print()

# Normalize journal names
df["journal_clean"] = df["journal"].str.replace("_", " ")
journals = sorted(df["journal_clean"].unique())
print(f"Journals: {journals}")
print()

# =============================================================
# Plot
# =============================================================
fig = plt.figure(figsize=(12, 8))
gs = fig.add_gridspec(2, 1, height_ratios=[1.3, 1.5], hspace=0.4)

def scatter_fit(ax, x, y, color="black", show_stats=True):
    """Scatter with OLS fit and 95% CI band."""
    ax.scatter(x, y, s=10, color=color, alpha=0.5, edgecolors="none")
    if len(x) < 3:
        return None
    slope, intercept, r, p, se = stats.linregress(x, y)
    xs = np.linspace(x.min(), x.max(), 100)
    ys = slope * xs + intercept
    ax.plot(xs, ys, color="black", lw=1.6)
    # 95% CI band via residual-based approximation
    resid = y - (slope * x + intercept)
    s = resid.std(ddof=2)
    band = 1.96 * s * np.sqrt(1/len(x) + (xs - x.mean())**2 / ((x - x.mean())**2).sum())
    ax.fill_between(xs, ys - band, ys + band, color="grey", alpha=0.22, linewidth=0)
    if show_stats:
        txt = f"b = {slope:+.3f}\nR² = {r**2:.3f}\np = {p:.4f}"
        if p < 0.001: txt += " ***"
        elif p < 0.01: txt += " **"
        elif p < 0.05: txt += " *"
        else: txt += " n.s."
        ax.text(0.03, 0.97, txt, transform=ax.transAxes,
                va="top", ha="left", fontsize=7,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=0.5))
    return slope, r**2, p

# ---------- Panel (a): Overall
ax = fig.add_subplot(gs[0])
slope, r2, p = scatter_fit(ax, df[ratio_col].values, df["jif_norm"].values, color="grey")
ax.set_xlabel("Active voice score")
ax.set_ylabel("JIF-normalized citations per year")
ax.set_title(f"Overall (n = {len(df)})", loc="left", fontweight="bold", fontsize=12)

# ---------- Panel (b): Per journal
cols = 4
rows = int(np.ceil(len(journals) / cols))
gs_b = gs[1].subgridspec(rows, cols, hspace=0.55, wspace=0.4)

# Compute shared y-axis limits across all panels for comparability
all_ynorm = df["jif_norm"].dropna()
ymax_shared = 12
yticks_shared = np.arange(0, 13, 2)
print(f"Shared y-axis max: {ymax_shared:.2f}")

for i, j in enumerate(journals):
    ax = fig.add_subplot(gs_b[i // cols, i % cols])
    sub = df[df["journal_clean"] == j]
    color = JOURNAL_COLORS.get(j, "#333333")
    scatter_fit(ax, sub[ratio_col].values, sub["jif_norm"].values, color=color)
    ax.set_title(f"{j} (n={len(sub)})", fontsize=8.5, fontweight="bold", color=color)
    ax.set_ylim(0, ymax_shared)
    ax.set_yticks(yticks_shared)
    ax.set_yticks(yticks_shared)
    ax.set_xlabel("Active voice", fontsize=8)
    ax.set_ylabel("JIF-norm cites/yr", fontsize=8)
    ax.tick_params(labelsize=7)

# Hide empty
for k in range(len(journals), rows * cols):
    fig.add_subplot(gs_b[k // cols, k % cols]).axis("off")


out_path = os.path.join(OUT_DIR, "fig3_jif_normalized.png")
fig.text(0.01, 0.97, "(a)", fontsize=13, fontweight="bold", va="top", ha="left")
fig.text(0.01, 0.50, "(b)", fontsize=13, fontweight="bold", va="top", ha="left")

fig.suptitle("JIF-normalized citations vs active voice score", fontsize=15, fontweight="bold", y=0.995)
fig.savefig(out_path)
plt.close(fig)
print(f"Wrote {out_path}")
