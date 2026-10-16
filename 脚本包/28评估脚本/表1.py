#!/usr/bin/env python3
"""
论文表 1：cond_J 信号有效性 + 补偿对比

八列：
  S | frac>160% | C1_err | C1_sat% | Fix20_err | Fix20_sat% | C2_err | C2_sat%

数据源（全部统一：8字轨迹, λ=0.05, σ=0）：
  C1:     数据集/C1/刚度扫描_8字（G=40）
  C2:     数据集/C2/刚度扫描_8字（自适应）
  Fix20:  数据集/28/results（G=20）

S 列表覆盖四态：
  1.0  正常
  1.5  过渡区边界（避免选择性报告）
  2.2  开始退化
  2.5  严重退化
  3.0  机制转变（饱和主导）
"""
import numpy as np, glob
from pathlib import Path

COND_TH = 160.0
WIN = 20
S_LIST = [1.0, 1.5, 2.2, 2.5, 3.0]


def rolling(x, w=20):
    o = np.full_like(x, np.nan, dtype=float)
    if len(x) < w: return o
    cs = np.cumsum(np.insert(x, 0, 0))
    o[w-1:] = (cs[w:] - cs[:-w]) / w
    return o


def fmt(x):
    return str(x).replace(".", "p")


def load_c1(S):
    fs = glob.glob(f"/root/opencr-mujoco-main/数据集/C1/刚度扫描_8字/*S{S}_sig0.0.npz")
    return np.load(fs[0], allow_pickle=True) if fs else None


def load_c2(S):
    fs = glob.glob(f"/root/opencr-mujoco-main/数据集/C2/刚度扫描_8字/*S{S}_sig0.0.npz")
    return np.load(fs[0], allow_pickle=True) if fs else None


def load_fix20(S):
    fs = glob.glob(
        f"/root/opencr-mujoco-main/数据集/28/results/"
        f"c1_8_S{fmt(S)}_sig0p0_G20p0_lam0p05_seed42.npz"
    )
    return np.load(fs[0], allow_pickle=True) if fs else None


def compute_row(S):
    d1  = load_c1(S)
    d2  = load_c2(S)
    d20 = load_fix20(S)
    if d1 is None or d2 is None:
        return None

    # 触发占比：滑动窗 > 160 的时间占比（跳过 warmup 50 步）
    c_slide = rolling(d1['cond_J'], WIN)[50:]
    frac = 100.0 * np.nanmean(c_slide > COND_TH)

    return {
        'S': S,
        'frac': frac,
        'C1_err':  float(d1['err_true'].mean()),
        'C1_sat':  100.0 * float(d1['sat_flag'].mean()),
        'Fix20_err': float(d20['err_true'].mean()) if d20 is not None else np.nan,
        'Fix20_sat': 100.0 * float(d20['sat_flag'].mean()) if d20 is not None else np.nan,
        'C2_err':  float(d2['err_true'].mean()),
        'C2_sat':  100.0 * float(d2['sat_flag'].mean()),
    }


def main():
    rows = [compute_row(S) for S in S_LIST]
    rows = [r for r in rows if r is not None]

    # 终端打印
    hdr = (f"{'S':>5} {'frac%':>7} {'C1_err':>9} {'C1_sat%':>9} "
           f"{'Fix20_err':>11} {'Fix20_sat%':>12} {'C2_err':>9} {'C2_sat%':>9}")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r['S']:>5.1f} {r['frac']:>7.2f} {r['C1_err']:>9.2f} "
              f"{r['C1_sat']:>9.2f} {r['Fix20_err']:>11.2f} "
              f"{r['Fix20_sat']:>12.2f} {r['C2_err']:>9.2f} "
              f"{r['C2_sat']:>9.2f}")

    # CSV
    out = Path("/root/opencr-mujoco-main/数据集/28/analysis/table1_final.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w') as f:
        f.write("S,frac_above_160,C1_err,C1_sat_pct,"
                "Fix20_err,Fix20_sat_pct,C2_err,C2_sat_pct\n")
        for r in rows:
            f.write(f"{r['S']:.1f},{r['frac']:.2f},"
                    f"{r['C1_err']:.2f},{r['C1_sat']:.2f},"
                    f"{r['Fix20_err']:.2f},{r['Fix20_sat']:.2f},"
                    f"{r['C2_err']:.2f},{r['C2_sat']:.2f}\n")
    print(f"\nCSV -> {out}")

    # LaTeX
    print("\n=== LaTeX ===")
    print(r"\begin{table}[t]")
    print(r"\centering")
    print(r"\caption{Trigger validity and compensation effectiveness}")
    print(r"\begin{tabular}{cccccccc}")
    print(r"\hline")
    print(r"$S$ & frac$_{>160}$ & $e_{C1}$ & sat$_{C1}$ "
          r"& $e_{g20}$ & sat$_{g20}$ & $e_{C2}$ & sat$_{C2}$ \\")
    print(r"     & (\%) & (mm) & (\%) & (mm) & (\%) & (mm) & (\%) \\")
    print(r"\hline")
    for r in rows:
        print(f"{r['S']:.1f} & {r['frac']:.2f} & {r['C1_err']:.2f} & "
              f"{r['C1_sat']:.2f} & {r['Fix20_err']:.2f} & "
              f"{r['Fix20_sat']:.2f} & {r['C2_err']:.2f} & "
              f"{r['C2_sat']:.2f} \\\\")
    print(r"\hline")
    print(r"\end{tabular}")
    print(r"\end{table}")


if __name__ == "__main__":
    main()
