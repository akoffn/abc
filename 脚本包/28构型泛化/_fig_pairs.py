"""Redraw the 88-pair scatter for a single IEEE column (3.4 x 2.0 in, 8 pt).

Data: all_pairs.csv  (name, S, k = kappa95, sat = saturation %, d = delta %, grp, pos)
  pos = 1  -> the gain helps (d > 0)
Output: fig4_pairs.png (300 dpi) and fig4_pairs.svg
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(HERE, "all_pairs.csv"), encoding="utf-8-sig")))

k = np.array([float(r["k"]) for r in rows])
sat = np.array([float(r["sat"]) for r in rows])
d = np.array([float(r["d"]) for r in rows])
pos = np.array([int(r["pos"]) for r in rows])

# log axis cannot hold an exact zero: park sat == 0 at half a decade left of 0.1
X0 = 0.01
x = np.where(sat > 0, sat, X0)
hi = k > 160.0

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "legend.frameon": False,
})

fig, ax = plt.subplots(figsize=(3.4, 2.0))
fig.subplots_adjust(left=0.155, right=0.975, bottom=0.165, top=0.965)

# four groups: (kappa above/below 160) x (gain / no gain)
style = [
    (hi & (pos == 1), "#C0392B", "o", 12, r"$\kappa_{95}>160$, gain"),
    (hi & (pos == 0), "#C0392B", "o", 12, r"$\kappa_{95}>160$, no gain"),
    (~hi & (pos == 1), "#2E5E9E", "o", 12, r"$\kappa_{95}\leq160$, gain"),
    (~hi & (pos == 0), "#2E5E9E", "o", 12, r"$\kappa_{95}\leq160$, no gain"),
]
for sel, color, marker, size, label in style:
    filled = "gain" in label and "no gain" not in label
    ax.scatter(x[sel], d[sel], s=size, marker=marker,
               facecolors=color if filled else "none",
               edgecolors=color, linewidths=0.6, zorder=3)

ax.axhline(0, color="0.35", linewidth=0.6, zorder=2)
ax.axvline(1.0, color="0.35", linewidth=0.6, linestyle=(0, (4, 2)), zorder=2)
ax.set_xscale("log")
ax.set_xlim(0.006, 600)
ax.set_ylim(-115, 100)

ax.set_xticks([0.01, 0.1, 1, 10, 100])
ax.set_xticklabels(["0", "0.1", "1", "10", "100"])
ax.set_xlabel("Sustained saturation ratio (%)", labelpad=1.5)
ax.set_ylabel("Error reduction (%)", labelpad=1.5)

# the two counts the caption quotes
left = (sat < 1.0) & (d <= 0)
right = sat >= 1.0
ax.text(0.012, -108, f"all {int(left.sum())} non-positive", fontsize=6.5, color="0.25")
ax.text(1.6, -108, f"{int((right & (d > 0)).sum())} of {int(right.sum())} positive",
        fontsize=6.5, color="0.25")

handles = [
    plt.Line2D([], [], marker="o", linestyle="", markersize=3.4, markerfacecolor="#C0392B",
               markeredgecolor="#C0392B", label=r"$\kappa_{95}>160$, gain"),
    plt.Line2D([], [], marker="o", linestyle="", markersize=3.4, markerfacecolor="none",
               markeredgecolor="#C0392B", label=r"$\kappa_{95}>160$, no gain"),
    plt.Line2D([], [], marker="o", linestyle="", markersize=3.4, markerfacecolor="#2E5E9E",
               markeredgecolor="#2E5E9E", label=r"$\kappa_{95}\leq160$, gain"),
    plt.Line2D([], [], marker="o", linestyle="", markersize=3.4, markerfacecolor="none",
               markeredgecolor="#2E5E9E", label=r"$\kappa_{95}\leq160$, no gain"),
]
ax.legend(handles=handles, loc="lower right", fontsize=6, handletextpad=0.3,
          labelspacing=0.25, borderpad=0.2)

fig.savefig(os.path.join(HERE, "fig4_pairs.png"), dpi=300)
fig.savefig(os.path.join(HERE, "fig4_pairs.svg"))
print("saved fig4_pairs.png / .svg |", len(rows), "points |",
      f"left non-positive={int(left.sum())}, right positive={int((right & (d > 0)).sum())}/{int(right.sum())}")
