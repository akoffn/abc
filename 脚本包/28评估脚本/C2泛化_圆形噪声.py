#!/usr/bin/env python3
"""
C2 泛化性：圆形轨迹 + 噪声扫描

验证 C2 在圆形轨迹下，对观测噪声是否鲁棒。

数据源：数据集/C2/S=2.5噪声扫描圆形/
输出：σ vs err/sat/gain
"""
import glob
import numpy as np
from pathlib import Path

DATA = Path("/root/opencr-mujoco-main/数据集/C2/S=2.5噪声扫描圆形")
OUT  = Path("/root/opencr-mujoco-main/数据集/28/analysis/c2_generalize_circle.csv")


def meta(d, k, default=np.nan):
    if k in d.files:
        v = d[k]
        return float(v) if np.ndim(v) == 0 else float(np.ravel(v)[0])
    return default


rows = []
for f in sorted(glob.glob(f"{DATA}/*.npz"),
                key=lambda x: float(np.load(x, allow_pickle=True)['sigma_mm'])):
    d = np.load(f, allow_pickle=True)
    sig = meta(d, 'sigma_mm')
    e = d['err_true']; s = d['sat_flag']; g = d['cur_gain']
    rows.append(dict(
        sigma=sig,
        err_mean=float(e.mean()),
        err_max=float(e.max()),
        sat_pct=float(s.mean()) * 100,
        gain_min=float(g.min()),
        gain_max=float(g.max()),
    ))

print(f"C2 圆形轨迹噪声扫描（S=2.5）")
print(f"共 {len(rows)} 个噪声点\n")
print(f"{'σ(mm)':>7} {'err_mean':>9} {'err_max':>9} {'sat%':>7} "
      f"{'gain_min':>9} {'gain_max':>9}")
print("-" * 60)
for r in rows:
    print(f"{r['sigma']:>7.3f} {r['err_mean']:>9.3f} {r['err_max']:>9.3f} "
          f"{r['sat_pct']:>7.2f} {r['gain_min']:>9.1f} {r['gain_max']:>9.1f}")

# 统计
errs = np.array([r['err_mean'] for r in rows])
sats = np.array([r['sat_pct'] for r in rows])
print(f"\n=== 稳定性 ===")
print(f"err_mean: {errs.min():.3f} ~ {errs.max():.3f} mm  (波动 {100*(errs.max()-errs.min())/errs.mean():.1f}%)")
print(f"sat%:     {sats.min():.2f} ~ {sats.max():.2f} %")

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w") as f:
    f.write("sigma,err_mean,err_max,sat_pct,gain_min,gain_max\n")
    for r in rows:
        f.write(f"{r['sigma']:.3f},{r['err_mean']:.3f},{r['err_max']:.3f},"
                f"{r['sat_pct']:.2f},{r['gain_min']:.1f},{r['gain_max']:.1f}\n")
print(f"\nCSV -> {OUT}")
