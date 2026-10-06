# scripts/make_fig2.py
# Figure 2: statistical summary — journal means and per-journal trends.

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
OUTDIR   = os.path.join(ANALYSIS, "output")
FIGDIR   = os.path.join(ANALYSIS, "figures")
os.makedirs(FIGDIR, exist_ok=True)

plt.rcParams["savefig.dpi"] = 300
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["font.size"] = 12

df = pd.read_csv(MASTER)
df["active_ratio"] = pd.to_numeric(df["active_ratio"], errors="coerce")
df["year"] = df["year"].astype(int)
df = df.dropna(subset=["active_ratio"])
print(f"Loaded {len(df)} papers")

# Compute summaries directly (no dependency on R output files)
by_j = df.groupby("journal")["active_ratio"].agg(
    ["mean", "std", "count"]).reset_index()
by_j.columns = ["journal", "mean_ratio", "sd_ratio", "n"]
by_j["se_ratio"] = by_j["sd_ratio"] / np.sqrt(by_j["n"])
by_j = by_j.sort_values("mean_ratio")

# Per-journal slopes
trend_rows = []
for journal, g in df.groupby("journal"):
    slope, intercept, r, p, se = stats.linregress(g["year"], g["active_ratio"])
    trend_rows.append({
        "journal": journal, "estimate": slope,
        "std.error": se, "p.value": p,
    })
trend = pd.DataFrame(trend_rows).sort_values("estimate")

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# --- Left: journal means with CI
ax = axes[0]
y_pos = np.arange(len(by_j))
err = 1.96 * by_j["se_ratio"]
colors = [journal_color(j) for j in by_j["journal"]]
ax.errorbar(by_j["mean_ratio"], y_pos, xerr=err,
            fmt="o", ecolor="black", capsize=5, linewidth=2,
            markersize=0)
for i, (c, m, n) in enumerate(zip(colors, by_j["mean_ratio"], by_j["n"])):
    ax.plot(m, i, marker="o", markersize=12, color=c,
            markeredgecolor="black", markeredgewidth=0.6, zorder=3)
ax.set_yticks(y_pos)
ax.set_yticklabels([journal_short(j) for j in by_j["journal"]])
ax.axvline(df["active_ratio"].mean(), linestyle="--", color="grey")
ax.set_xlabel("Mean active voice score (95% CI)")
ax.set_title("Journal means")
for i, r in by_j.iterrows():
    i = list(by_j.index).index(i)
    ax.text(r["mean_ratio"] + 0.015, i,
            f"{r['mean_ratio']:.3f}  (n={int(r['n'])})",
            va="center", fontsize=10)

# --- Right: per-journal slopes
ax = axes[1]
y_pos = np.arange(len(trend))
colors = [journal_color(j) if p < 0.05 else "#bbbbbb"
          for j, p in zip(trend["journal"], trend["p.value"])]
ax.barh(y_pos, trend["estimate"], color=colors, alpha=0.9,
        edgecolor="black", linewidth=0.6)
ax.errorbar(trend["estimate"], y_pos, xerr=1.96*trend["std.error"],
            fmt="none", ecolor="black", capsize=4)
ax.axvline(0, color="black", linewidth=1)
ax.set_yticks(y_pos)
ax.set_yticklabels([journal_short(j) for j in trend["journal"]])
ax.set_xlabel("Slope (active-voice change per year)")
ax.set_title("Per-journal temporal trend")
for i, r in trend.iterrows():
    i = list(trend.index).index(i)
    sig = "***" if r["p.value"] < 0.001 else \
          "**"  if r["p.value"] < 0.01 else \
          "*"   if r["p.value"] < 0.05 else "n.s."
    offset = 0.00015 if r["estimate"] >= 0 else -0.0006
    ax.text(r["estimate"] + offset, i, sig,
            va="center", fontsize=11, fontweight="bold")

slope, intercept, r_val, p_val, se = stats.linregress(
    df["year"], df["active_ratio"])
fig.suptitle(
    f"Statistical summary   |   Overall slope = {slope:+.4f}/yr  "
    f"(p = {p_val:.1e}, R² = {r_val**2:.3f})",
    fontsize=14, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(os.path.join(FIGDIR, "fig2_statistics.png"))
plt.close(fig)
print("Wrote fig2_statistics.png")
