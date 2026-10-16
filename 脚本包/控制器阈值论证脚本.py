#!/usr/bin/env python3
"""
阈值选择论证图：
  1. 从 C1 刚度扫描 npz 读 cond_J
  2. 算正常组(S≤1.5) p95 和退化组(S≥2.2) p5
  3. 画图（含阈值线 160/70、安全裕度、过渡区）
"""
import numpy as np, glob, csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family':'STIXGeneral','mathtext.fontset':'stix',
    'font.size':10,'axes.labelsize':11,'axes.titlesize':11,
    'legend.fontsize':9,'axes.grid':True,'grid.alpha':0.25,
    'axes.linewidth':0.9,'savefig.bbox':'tight'})

D = Path("/root/opencr-mujoco-main/数据集/C1/刚度扫描_8字")
OUT_CSV = Path("/root/opencr-mujoco-main/数据集/28/analysis/threshold_bounds.csv")

def rolling(x, w=20):
    o = np.full_like(x, np.nan, dtype=float)
    if len(x) < w: return o
    cs = np.cumsum(np.insert(x, 0, 0)); o[w-1:] = (cs[w:]-cs[:-w])/w
    return o

# === 读数据 ===
rows = []
for f in sorted(glob.glob(f"{D}/*.npz"),
                key=lambda x: float(np.load(x, allow_pickle=True)['S'])):
    d = np.load(f, allow_pickle=True)
    S = float(d['S'])
    c_slide = rolling(d['cond_J'], 20)[50:]
    rows.append((S, c_slide))

normal = [(S, c) for S, c in rows if S <= 1.5]
degen  = [(S, c) for S, c in rows if S >= 2.2]

S_n = [S for S, _ in normal]
p95 = [float(np.percentile(c, 95)) for _, c in normal]
S_d = [S for S, _ in degen]
p5  = [float(np.percentile(c, 5)) for _, c in degen]

C_UP, C_DOWN = 160, 70
UP_BOUND = max(p95)
DOWN_BOUND = min(p5)

# === 写 CSV ===
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, 'w') as f:
    f.write("S,group,p5,p95\n")
    for (S, c) in normal:
        f.write(f"{S},normal,{np.percentile(c,5):.3f},{np.percentile(c,95):.3f}\n")
    for (S, c) in degen:
        f.write(f"{S},degraded,{np.percentile(c,5):.3f},{np.percentile(c,95):.3f}\n")
print(f"CSV -> {OUT_CSV}")
print(f"正常组 p95 上界 = {UP_BOUND:.1f}  (margin = {C_UP-UP_BOUND:.1f})")
print(f"退化组 p5  下界 = {DOWN_BOUND:.1f}  (margin = {DOWN_BOUND-C_DOWN:.1f})")

# === 画图 ===
fig, ax = plt.subplots(figsize=(7.5, 4.0))

ax.axhline(C_UP, color='gray', ls='--', lw=1.2, zorder=1)
ax.axhline(C_DOWN, color='gray', ls='--', lw=1.2, zorder=1)
ax.text(5.25, C_UP, r'$C_{\rm up}=160$', fontsize=9, color='gray', va='center')
ax.text(5.25, C_DOWN, r'$C_{\rm down}=70$', fontsize=9, color='gray', va='center')

ax.plot(S_n, p95, 'o-', color='#2980b9', lw=1.8, ms=5,
        mfc='#2980b9', mec='k', mew=0.4,
        label=r'Normal: $p_{95}$ of cond$_{\rm slide}$', zorder=3)
ax.plot(S_d, p5, 's-', color='#c0392b', lw=1.8, ms=5,
        mfc='#c0392b', mec='k', mew=0.4,
        label=r'Degraded: $p_{5}$ of cond$_{\rm slide}$', zorder=3)

ax.fill_between([0.4, 5.2], UP_BOUND, C_UP, color='blue', alpha=0.06, zorder=0)
ax.fill_between([0.4, 5.2], C_DOWN, DOWN_BOUND, color='red', alpha=0.06, zorder=0)

ax.annotate('', xy=(4.3, UP_BOUND), xytext=(4.3, C_UP),
            arrowprops=dict(arrowstyle='<->', color='blue', lw=1.1))
ax.text(4.35, (UP_BOUND + C_UP)/2, 'margin 7\n(healthy upper)',
        fontsize=7.5, color='blue', va='center')

ax.annotate('', xy=(4.3, C_DOWN), xytext=(4.3, DOWN_BOUND),
            arrowprops=dict(arrowstyle='<->', color='red', lw=1.1))
ax.text(4.35, (C_DOWN + DOWN_BOUND)/2, 'margin 3\n(degraded lower)',
        fontsize=7.5, color='red', va='center')

ax.axvspan(0.4, 1.55, color='green', alpha=0.05, zorder=0)
ax.axvspan(2.15, 5.2, color='orange', alpha=0.05, zorder=0)

ax.text(0.95, 185, 'Normal region', fontsize=9, color='darkgreen', ha='center')
ax.text(3.65, 185, 'Degraded region', fontsize=9, color='darkorange', ha='center')
ax.text(1.85, 175, 'Transition\nregime', fontsize=8.5, color='gray',
        ha='center', style='italic')

ax.annotate('Slip mode bifurcation', xy=(2.20, 73.2), xytext=(2.6, 45),
            fontsize=7.5, color='gray',
            arrowprops=dict(arrowstyle='->', color='gray', lw=0.7))

ax.set_xlabel(r'Stiffness scaling $S$')
ax.set_ylabel(r'cond$_{\rm slide}$')
ax.set_xlim(0.4, 5.9)
ax.set_ylim(40, 200)
ax.legend(loc='lower right', framealpha=0.92, fontsize=8.5)

fig.tight_layout()
out = "/root/opencr-mujoco-main/paper_figs/fig3_threshold.pdf"
fig.savefig(out)
fig.savefig(out.replace('.pdf','.png'), dpi=300)
print(f"图 -> {out}")
