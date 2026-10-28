# 13a_make_fig1_active_only.py
# Active-voice-only Figure 1 with significance annotations.

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

plt.rcParams["savefig.dpi"] = 300
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["font.size"] = 11

JOURNAL_COLORS = {
    "Cancer":                           "#2a7eb8",
    "Clinical Genetics":                "#e07b39",
    "Developmental Dynamics":           "#8e44ad",
    "Ecology":                          "#27ae60",
    "Journal of Neuroscience Research": "#c0392b",
    "Molecular Ecology":                "#e91e8c",
    "Molecular Microbiology":           "#00bcd4",
}

BASE = "/Users/reganwhite/Desktop/Scientific_Writing/Class_Project"
CSV = os.path.join(BASE, "analysis", "master_with_jif_cleaned.csv")
OUT_DIR = os.path.join(BASE, "manuscript")
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(CSV)
df["active_ratio"] = pd.to_numeric(df["active_ratio"], errors="coerce")
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df = df.dropna(subset=["active_ratio", "year"])
df["year"] = df["year"].astype(int)
df["journal_clean"] = df["journal"].str.replace("_", " ")

print(f"Loaded {len(df)} papers")


def sig_stars(p):
    if p < 0.001: return "***"
    if p < 0.01: return "**"
    if p < 0.05: return "*"
    return "n.s."


# ============================================================
# Figure
# ============================================================
fig = plt.figure(figsize=(14, 8))
gs = fig.add_gridspec(2, 1, height_ratios=[1.2, 1.5], hspace=0.4)

# ---------- Panel (a): Overall trend with significance
ax = fig.add_subplot(gs[0])
g = df.groupby("year")["active_ratio"].agg(["mean", "std", "count"]).reset_index()
g["se"] = g["std"] / np.sqrt(g["count"])

ax.plot(g["year"], g["mean"], "o-", color="black", lw=1.8, ms=7)
ax.fill_between(g["year"], g["mean"] - 1.96*g["se"], g["mean"] + 1.96*g["se"],
                color="black", alpha=0.15, linewidth=0)

for _, r in g.iterrows():
    ax.annotate(f"n={int(r['count'])}", (r["year"], r["mean"]),
                xytext=(0, 14), textcoords="offset points",
                ha="center", fontsize=9, color="#333333")

# Overall OLS trend + significance
slope, intercept, r, p, se = stats.linregress(df["year"], df["active_ratio"])
sig = sig_stars(p)

# Draw the OLS fit line as a dashed overlay
xs = np.linspace(g["year"].min(), g["year"].max(), 100)
ax.plot(xs, intercept + slope*xs, "--", color="black", lw=1.2, alpha=0.6)

# Stats annotation for panel (a)
txt_a = (f"OLS trend: b = {slope:+.4f}/year\n"
         f"R² = {r**2:.3f}, p = {p:.3g} {sig}\n"
         f"n = {len(df)} papers")
ax.text(0.03, 0.97, txt_a, transform=ax.transAxes,
        va="top", ha="left", fontsize=9, fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                  edgecolor="black", alpha=0.9, lw=0.8))

overall_mean = df["active_ratio"].mean()
ax.axhline(overall_mean, ls=":", color="grey", lw=1)
# Place overall mean label inside the plot, near the left edge
x_lo = sorted(df["year"].unique())[0]
ax.text(x_lo + 0.3, overall_mean + 0.008,
        f"overall mean = {overall_mean:.3f}",
        va="bottom", ha="left", fontsize=8.5, color="grey",
        style="italic")

ax.set_ylabel("Proportion of sentences (active voice)")
ax.set_xlabel("Publication year")
ax.set_xticks(sorted(df["year"].unique()))
ax.set_ylim(0, 1)
ax.set_title("(a)  Overall active voice usage over time", loc="left",
             fontsize=12, fontweight="bold")

# ---------- Panel (b): Per journal with significance
journals = sorted(df["journal_clean"].unique())
n_j = len(journals)
ncols = 4
nrows = int(np.ceil(n_j / ncols))
gs_b = gs[1].subgridspec(nrows, ncols, hspace=0.6, wspace=0.45)

for i, j in enumerate(journals):
    ax = fig.add_subplot(gs_b[i // ncols, i % ncols])
    sub = df[df["journal_clean"] == j]
    g = sub.groupby("year")["active_ratio"].agg(["mean", "std", "count"]).reset_index()
    g["se"] = g["std"] / np.sqrt(g["count"])

    color = JOURNAL_COLORS.get(j, "#333333")
    ax.plot(g["year"], g["mean"], "o-", color=color, lw=1.5, ms=4)
    ax.fill_between(g["year"], g["mean"] - 1.96*g["se"], g["mean"] + 1.96*g["se"],
                    color=color, alpha=0.2, linewidth=0)

    if len(sub) > 5:
        slope, intercept, r, p, se = stats.linregress(sub["year"], sub["active_ratio"])
        sig = sig_stars(p)

        # Draw OLS fit line
        xs = np.linspace(sub["year"].min(), sub["year"].max(), 100)
        ax.plot(xs, intercept + slope*xs, "--", color="black", lw=1.0, alpha=0.5)

        # Stats box
        ann = (f"b = {slope:+.4f}\n"
               f"p = {p:.3g} {sig}")
        ax.text(0.96, 0.04, ann, transform=ax.transAxes,
                va="bottom", ha="right", fontsize=7.5, fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          alpha=0.9, edgecolor=color, lw=0.8))

    ax.set_title(f"{j}  (n={len(sub)})", fontsize=9, fontweight="bold", color=color)
    ax.set_xlabel("Year", fontsize=8)
    ax.set_ylabel("Active voice", fontsize=8)
    ax.set_xticks(sorted(df["year"].unique()))
    ax.tick_params(labelsize=7.5)
    ax.set_ylim(0, 1)

for k in range(n_j, nrows * ncols):
    fig.add_subplot(gs_b[k // ncols, k % ncols]).axis("off")

fig.text(0.005, 0.985, "b", fontsize=14, fontweight="bold", va="top")
fig.suptitle("Active voice usage over time", fontsize=15, fontweight="bold", y=0.995)

out_path = os.path.join(OUT_DIR, "fig1_active_only.png")
fig.savefig(out_path)
plt.close(fig)
print(f"Wrote {out_path}")
