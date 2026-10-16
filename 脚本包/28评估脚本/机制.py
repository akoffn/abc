#!/usr/bin/env python3
"""
生成论文表1：cond_J 信号有效性 + C2 触发机制 + 饱和截断验证

六列：
  S | 触发占比% | C1_err | C1_sat% | Fix20_err | C2_err

数据源：
  C1:       数据集/C1/刚度扫描_8字
  C2:       数据集/C2/刚度扫描_8字
  Fix20:    数据集/28/results (G=20 的文件)
"""
import sys as _sys
from pathlib import Path as _Path
REPO = str(_Path(__file__).resolve().parents[2])
_sys.path.insert(0, REPO)
import numpy as np, glob
from pathlib import Path

COND_TH = 160.0
WIN = 20
S_LIST = [1.0, 2.2, 2.5]


def rolling(x, w=20):
    o = np.full_like(x, np.nan, dtype=float)
    if len(x) < w:
        return o
    cs = np.cumsum(np.insert(x, 0, 0))
    o[w-1:] = (cs[w:] - cs[:-w]) / w
    return o


def fmt(x):
    return str(x).replace(".", "p")


def load_c1(S):
    fs = glob.glob(f"{REPO}/数据集/C1/刚度扫描_8字/*S{S}_sig0.0.npz")
    return np.load(fs[0], allow_pickle=True) if fs else None


def load_c2(S):
    fs = glob.glob(f"{REPO}/数据集/C2/刚度扫描_8字/*S{S}_sig0.0.npz")
    return np.load(fs[0], allow_pickle=True) if fs else None


def load_fix20(S):
    fs = glob.glob(
        f"{REPO}/数据集/28/results/"
        f"c1_8_S{fmt(S)}_sig0p0_G20p0_lam0p05_seed42.npz"
    )
    return np.load(fs[0], allow_pickle=True) if fs else None


def compute_row(S):
    d1 = load_c1(S)
    d2 = load_c2(S)
    d20 = load_fix20(S)
    if d1 is None or d2 is None:
        return None

    # 触发占比：滑动窗 > 160 的时间占比（跳过 warmup 50 步）
    c_slide = rolling(d1['cond_J'], WIN)[50:]
    frac = 100.0 * np.nanmean(c_slide > COND_TH)

    return {
        'S': S,
        'frac': frac,
        'C1_err': float(d1['err_true'].mean()),
        'C1_sat': 100.0 * float(d1['sat_flag'].mean()),
        'Fix20_err': float(d20['err_true'].mean()) if d20 is not None else np.nan,
        'C2_err': float(d2['err_true'].mean()),
    }


def main():
    rows = [compute_row(S) for S in S_LIST]
    rows = [r for r in rows if r is not None]

    # 终端打印
    hdr = (f"{'S':>5} {'触发%':>8} {'C1_err':>9} "
           f"{'C1_sat%':>9} {'Fix20_err':>11} {'C2_err':>9}")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r['S']:>5.1f} {r['frac']:>8.2f} {r['C1_err']:>9.2f} "
              f"{r['C1_sat']:>9.2f} {r['Fix20_err']:>11.2f} {r['C2_err']:>9.2f}")

    # 写 CSV（论文用）
    out = Path(f"{REPO}/数据集/28/analysis/table1_final.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w') as f:
        f.write("S,frac_above_160,C1_err,C1_sat_pct,Fix20_err,C2_err\n")
        for r in rows:
            f.write(f"{r['S']:.1f},{r['frac']:.2f},{r['C1_err']:.2f},"
                    f"{r['C1_sat']:.2f},{r['Fix20_err']:.2f},{r['C2_err']:.2f}\n")
    print(f"\nCSV -> {out}")


if __name__ == "__main__":
    main()
