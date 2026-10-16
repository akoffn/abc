#!/usr/bin/env python3
"""C2 泛化性图：圆形轨迹 + 噪声扫描（优化版）"""
import sys as _sys
from pathlib import Path as _Path
REPO = str(_Path(__file__).resolve().parents[2])
_sys.path.insert(0, REPO)
import glob
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family':'STIXGeneral','mathtext.fontset':'stix',
    'font.size':10,'axes.labelsize':11,'axes.titlesize':11,
    'legend.fontsize':9,'xtick.labelsize':9,'ytick.labelsize':9,
    'axes.grid':True,'grid.alpha':0.25,'axes.linewidth':0.9,
    'savefig.bbox':'tight','savefig.pad_inches':0.02})

DATA = Path(f"{REPO}/数据集/C2/S=2.5噪声扫描圆形")
OUT  = Path(f"{REPO}/paper_figs/fig4_c2_circle_noise.pdf")


def meta(d, k, default=np.nan):
    if k in d.files:
        v = d[k]
        return float(v) if np.ndim(v) == 0 else float(np.ravel(v)[0])
    return default


rows = []
for f in sorted(glob.glob(f"{DATA}/*.npz"),
                key=lambda x: float(np.load(x, allow_pickle=True)['sigma_mm'])):
    d = np.load(f, allow_pickle=True)
    rows.append(dict(
        sigma=meta(d, 'sigma_mm'),
        err_mean=float(d['err_true'].mean()),
        err_std=float(d['err_true'].std()),
        sat_pct=float(d['sat_flag'].mean()) * 100,
    ))

sig = np.array([r['sigma'] for r in rows])
err = np.array([r['err_mean'] for r in rows])
std = np.array([r['err_std'] for r in rows])
sat = np.array([r['sat_pct'] for r in rows])

fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.4))

# (a) err vs sigma
ax = axes[0]
ax.errorbar(sig, err, yerr=std, fmt='o-', color='#2980b9', lw=1.6,
            ms=5, mfc='#2980b9', mec='k', mew=0.4, capsize=3,
            label='C2 (circle)')
ax.set_xlabel(r'Noise $\sigma$ (mm)')
ax.set_ylabel(r'err mean (mm)')
ax.set_title(r'(a) Error vs noise')
ax.legend(loc='upper left', framealpha=0.9)
ax.set_xscale('symlog', linthresh=0.005)
ax.set_ylim(0, 30)  # 限制上限，避免顶部空白

# (b) sat% vs sigma
ax = axes[1]
ax.plot(sig, sat, 's-', color='#c0392b', lw=1.6, ms=5,
        mfc='#c0392b', mec='k', mew=0.4, label='C2 (circle)')
ax.set_xlabel(r'Noise $\sigma$ (mm)')
ax.set_ylabel(r'Saturation (\%)')
ax.set_title(r'(b) Saturation vs noise')
ax.legend(loc='upper left', framealpha=0.9)
ax.set_xscale('symlog', linthresh=0.005)
ax.set_ylim(-0.3, 0.3)  # 缩到 0 附近
ax.axhline(0, color='gray', ls=':', lw=0.8)

fig.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT)
fig.savefig(str(OUT).replace('.pdf','.png'), dpi=300)
print(f"图 -> {OUT}")

print(f"\nσ: {sig.min():.3f} ~ {sig.max():.3f}")
print(f"err: {err.min():.3f} ~ {err.max():.3f} mm  (波动 {100*(err.max()-err.min())/err.mean():.1f}%)")
print(f"sat%: {sat.min():.2f} ~ {sat.max():.2f} %")
