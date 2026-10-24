#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================================
返修 · 意见① —— 标定轨迹参数族外推（family extrapolation）
=====================================================================
审稿意见原文（两条意见其实是一条）：
  (1) "...the thresholds are calibrated on a single figure-eight, so the
       validation is essentially one figure-eight plus one circular path.
       The authors should cover different curvature directions, workspace
       regions, tendon combinations ..."
  (2) "...contact locations and free/contact transitions. The
       condition-number scheduler should therefore be evaluated across the
       configuration space rather than along a small number of paths."

本脚本的设计判断
---------------------------------------------------------------------
不另造若干"不相干的新轨迹"，而是把 8 字轨迹本身参数化，沿审稿人点名的
维度做**单变量**外推（one-factor-at-a-time）。理由有三条：

1. 8 字轨迹在代码里只有 5 个可调量，审稿人点名的三项正好落在其中三个：
       轨迹 = c + r·( a_x·sin(phi)·u  +  a_y·sin(k·phi + psi)·v )
       a_x, a_y : 幅值 / 宽高比   -> 工作空间区域、曲率大小
       u, v     : 平面基向量      -> 弯 曲 平 面
       c        : 中心            -> 工 作 空 间 区 域
       k        : 频率比          -> 曲率符号反转次数 = 2(k-1)
   "换一条不相干的轨迹"会同时改动上述多个量，差异无法归因；本设计每次
   只动一个量，步长明确，边界移动的规律可解释。

2. 阈值标定的漏洞恰好在这里。论文的 C_up = 160 取自 8 字轨迹
   max(cond p95) = 153.04 加固定裕度，这是一个**曲线上的点估计**。
   把"某条曲线的最大值"升级成"某参数族的上界"，只能靠在族内做外推，
   换赛道（新轨迹）反而答不对这个问题。

3. 与论文现有数据可以直接对账。base 成员与原 8 字完全等价，跑出来的
   cond p95 / 误差必须复现 数据集/C1|C2/刚度扫描_8字 的数值，用于自检。

族成员（10 条，base 为标定成员）
---------------------------------------------------------------------
  base       a=(70, 37.5) mm, u=x, v=y, k=2          <- 标定成员（=原 8 字）
  scale_s    幅值 x0.70                              尺度 / 工作空间内圈
  scale_l    幅值 x1.40                              尺度 / 工作空间外圈
  ar_thin    a_y x0.55（宽高比 0.59）                窄 8 字，拐点更尖
  ar_fat     a_y x1.60（宽高比 1.71）                胖 8 字，拐点更缓
  tilt45     平面基绕 x 轴转 45 度                   弯曲平面
  tilt90     平面基改为 (x, z)                       弯曲平面（正交）
  off_z      中心 +25 mm（z）                        工作空间区域
  off_x      中心 +25 mm（x）                        工作空间区域
  k3         k=3，三个瓣，曲率反转 4 次              曲率符号反转

矩阵（默认，共 50 次）
---------------------------------------------------------------------
  base          x S{1.0, 1.5, 2.0, 2.5} x {C1, C2} =  8
  其余 7 个成员  x S{1.5, 2.0, 2.5}      x {C1, C2} = 42
  阈值全程冻结 C_up=160 / C_down=70，任何一次运行都不改参数。

为什么是这三个刚度点
---------------------------------------------------------------------
  1.5 是"危险边"：base 的 cond p95=141、max=157，距 C_up=160 只有 2%，
      是最容易被新成员推到越界的位置 —— 族上界到底有没有超 160 看这里。
  2.0 是"分歧点"：圆形在此 +59.6%、8 字 −49.5%，符号相反。它决定
      "κ 是不是单独的判据"，因此所有成员都必须跑。
  2.5 是论文主张的锚点：现有降幅 71.3%，任何成员在此翻车都意味着
      论文的核心结论需要加限定。
  1.0 只给 base，用于与论文既有数据对账（自检闸门）。

用法
---------------------------------------------------------------------
先做可达性预检（只跑 S=1.5 / C2，看误差是否爆炸、cond 是否 nan）：

    MUJOCO_GL=disable python "脚本包/29返修构型覆盖/traj_family.py" --probe

确认后跑完整矩阵：

    MUJOCO_GL=disable python "脚本包/29返修构型覆盖/traj_family.py"

自定义：

    python traj_family.py --members k3 tilt90 --S 1.5 2.5 4.5
    python traj_family.py --force         # 覆盖已有 npz 重跑
    python traj_family.py --list          # 只列出族成员，不跑

支持断点续跑：已存在的 npz 默认跳过。

输出
---------------------------------------------------------------------
  数据集/29_revision/family_scan/*.npz          每次一个（字段与既有 npz 对齐）
  数据集/29_revision/family_envelope.csv        逐成员汇总
  终端打印 LaTeX 表 + 族上界判据
=====================================================================
"""
import os
import sys
import types
import csv
import time
import argparse
from pathlib import Path

# ---- pynput 桩：与 traj_run.py 一致，避免无头环境 import 失败 ----
_p = types.ModuleType("pynput")
_kb = types.ModuleType("pynput.keyboard")
_kb.Key = type("Key", (), {})
_kb.Listener = type("Listener", (), {
    "__init__": lambda *a, **k: None,
    "start": lambda *a, **k: None,
    "stop": lambda *a, **k: None,
})
_p.keyboard = _kb
sys.modules["pynput"] = _p
sys.modules["pynput.keyboard"] = _kb

os.environ.setdefault("MUJOCO_GL", "disable")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

REPO = str(Path(__file__).resolve().parents[2])
sys.path.insert(0, REPO)

import numpy as np  # noqa: E402
import mujoco  # noqa: E402
from opencr_mujoco.controllers.tdcr_ik_controller_c2 import TDCRIKControllerC2  # noqa: E402

# ----------------------------- 常量（与 traj_run.py 完全一致） -----------------------------
SCENE = REPO + "/assets/tdcr/tdcr_3seg.xml"
DT = 0.001
FPS = 50
PERIOD = 10.0          # 轨迹渐入段
SIM_T = 20.0           # 总时长；只统计 t > PERIOD 的稳态段
LAMBDA = 0.05          # DLS 阻尼
CLIP_LIM = 1.0         # 控制量裁剪
# 每个控制周期推进的物理子步数：与 traj_run.py 的 sub 完全一致（1/(50*0.001)=20）。
# 这一行是 base 能否复现论文数据的前提，改动即为协议变更，不要再改。
SUB = max(1, int(round(1.0 / (FPS * DT))))
GAIN_C1 = 40.0         # C1 固定增益
C_UP, C_DOWN = 160.0, 70.0   # C2 冻结阈值，全程不改

OUTDIR = Path(REPO) / "数据集/29_revision/family_scan"
SUMMARY = Path(REPO) / "数据集/29_revision/family_envelope.csv"

# 原始 8 字系数（traj_8: 0.070*sin(phi) 与 0.075*sin(phi)cos(phi)）
# 注意 0.075*sin*cos == 0.0375*sin(2phi)，后续统一按 sin(k*phi) 的幅值书写。
A_X0 = 0.070
A_Y0 = 0.0375


# ----------------------------- 轨迹族 -----------------------------
def _ramp(t, period=PERIOD):
    return min(t / period, 1.0)


def make_lissajous(a_x, a_y, u, v, k=2.0, psi=0.0, shift=(0.0, 0.0, 0.0)):
    """通用 Lissajous 族。k=2, psi=0, shift=0 时与 traj_run.traj_8 逐点等价。

    u, v   : 平面基向量（单位向量）。改变二者即改变弯曲平面。
    k      : 频率比。曲线在平面内曲率符号反转的次数约等于 2(k-1)。
    shift  : 轨迹中心相对起始末端的偏移（米），改变工作空间区域。
    """
    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)
    sh = np.asarray(shift, dtype=float)

    def f(c, t):
        r = _ramp(t)
        phi = 2.0 * np.pi * t / PERIOD
        return (c + sh) + r * (a_x * np.sin(phi) * u + a_y * np.sin(k * phi + psi) * v)

    return f


def build_family():
    """返回 {name: {"fn":..., "params":..., "desc":...}}，base 必须等价于原 8 字。"""
    EX = np.array([1.0, 0.0, 0.0])
    EY = np.array([0.0, 1.0, 0.0])
    EZ = np.array([0.0, 0.0, 1.0])

    fam = {}

    def add(name, fn, params, desc):
        fam[name] = {"fn": fn, "params": params, "desc": desc}

    # --- 标定成员：必须复现原 8 字 ---
    add("base", make_lissajous(A_X0, A_Y0, EX, EY, k=2.0),
        "a=70/37.5 k=2 tilt=0", "calibration member (= original figure-eight)")

    # --- 尺度轴 ---
    add("scale_s", make_lissajous(A_X0 * 0.70, A_Y0 * 0.70, EX, EY, k=2.0),
        "scale=0.70", "inner workspace, larger curvature")
    add("scale_l", make_lissajous(A_X0 * 1.40, A_Y0 * 1.40, EX, EY, k=2.0),
        "scale=1.40", "outer workspace, smaller curvature")

    # --- 宽高比轴（改变瓣形与拐点尖度，幅值 x 不变） ---
    add("ar_thin", make_lissajous(A_X0, A_Y0 * 0.55, EX, EY, k=2.0),
        "ay=0.55x", "narrow eight, sharper crossing")
    add("ar_fat", make_lissajous(A_X0, A_Y0 * 1.60, EX, EY, k=2.0),
        "ay=1.60x", "wide eight, blunter crossing")

    # --- 弯曲平面轴 ---
    v45 = np.array([0.0, np.cos(np.pi / 4), np.sin(np.pi / 4)])
    add("tilt45", make_lissajous(A_X0, A_Y0, EX, v45, k=2.0),
        "plane=45deg", "eight lying in a 45deg inclined plane")
    add("tilt90", make_lissajous(A_X0, A_Y0, EX, EZ, k=2.0),
        "plane=XZ", "eight in the vertical XZ plane (orthogonal bending)")

    # --- 工作空间区域轴 ---
    add("off_z", make_lissajous(A_X0, A_Y0, EX, EY, k=2.0, shift=(0.0, 0.0, 0.025)),
        "center +25mm z", "workspace region shifted along z")
    add("off_x", make_lissajous(A_X0, A_Y0, EX, EY, k=2.0, shift=(0.025, 0.0, 0.0)),
        "center +25mm x", "workspace region shifted along x")

    # --- 曲率符号反转轴（k 决定反转次数 2(k-1)） ---
    add("k3", make_lissajous(A_X0, A_Y0, EX, EY, k=3.0),
        "k=3 (4 reversals)", "three-lobe curve, four curvature-sign reversals")

    return fam


FAMILY = build_family()

# 默认矩阵 = 50 次：
#   base  x S{1.0, 1.5, 2.0, 2.5} x {C1,C2} =  8
#   其余7 x S{1.5, 2.0, 2.5}      x {C1,C2} = 42
# S=2.0 是"分歧点"：圆形在此 +59.6%、8 字 −49.5%，最能暴露收益符号的成因，
# 因此所有成员都必须跑这个点，它决定"κ 是否单独的判据"这一问的答案。
# ar_fat / off_x 保留在族里但不默认跑（ar_thin 已代表宽高比轴，off_x 半径 95 mm
# 可达性风险最高），需要时用 --members 显式指定。
DEFAULT_S = {"base": [1.0, 1.5, 2.0, 2.5]}
DEFAULT_S_OTHER = [1.5, 2.0, 2.5]
DEFAULT_MEMBERS = ["base", "scale_s", "scale_l", "ar_thin",
                   "tilt45", "tilt90", "off_z", "k3"]


# ----------------------------- 工具 -----------------------------
def rolling(x, w=20):
    """滑动平均，与控制器/论文中 win=20 的口径一致。"""
    o = np.full_like(x, np.nan, dtype=float)
    if len(x) < w:
        return o
    cs = np.cumsum(np.insert(x, 0, 0))
    o[w - 1:] = (cs[w:] - cs[:-w]) / w
    return o


def fmt(x):
    return str(x).replace(".", "p").replace("-", "m")


def robust_p95(x):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    return float(np.percentile(x, 95)) if len(x) else float("nan")


def spearman(a, b):
    """秩相关系数（不依赖 scipy）。用于检验"κ 越高、收益越大"是否成立。"""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    m = np.isfinite(a) & np.isfinite(b)
    a, b = a[m], b[m]
    if len(a) < 3:
        return float("nan")
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


# ----------------------------- 与论文既有数据对账 -----------------------------
def existing_npz(S, ctrl):
    """论文数据里同名同条件的 npz（仅 8 字有）。用于 base 成员的自检。"""
    for s in (f"{S:g}", f"{S:.1f}"):
        p = Path(REPO) / f"数据集/{ctrl}/刚度扫描_8字/{ctrl}_stiffness_8字_S{s}_sig0.0.npz"
        if p.exists():
            return p
    return None


def selfcheck(S, ctrl, r):
    """base 必须复现论文既有数字。返回 (ok, msg)。"""
    p = existing_npz(S, ctrl)
    if p is None:
        return None, f"无既有数据可比（{ctrl} S={S:g}）"
    d = np.load(p, allow_pickle=True)
    e0 = float(np.nanmean(np.asarray(d["err_true"], float)))
    c0 = float(np.nanpercentile(np.asarray(d["cond_J"], float), 50))
    d_err = abs(r["err_mean"] - e0) / max(e0, 1e-9) * 100.0
    d_cond = abs(r["cond_p50"] - c0) / max(c0, 1e-9) * 100.0
    ok = d_err < 2.0 and d_cond < 2.0
    return ok, (f"对账 {ctrl} S={S:g}: err {r['err_mean']:.3f} vs {e0:.3f} mm "
                f"({d_err:+.1f}%), cond_p50 {r['cond_p50']:.1f} vs {c0:.1f} "
                f"({d_cond:+.1f}%)  -> {'通过' if ok else '不一致，先查协议'}")


# ----------------------------- 单次运行 -----------------------------
def run_one(member, S, ctrl, seed=42, sigma_mm=0.0, sim_t=SIM_T, save=True):
    """跑一次。每次重新加载 model —— jnt_stiffness 是 *= S，复用会累积相乘。"""
    m = mujoco.MjModel.from_xml_path(SCENE)
    d = mujoco.MjData(m)
    m.opt.gravity[:] = 0
    m.opt.timestep = DT
    m.jnt_stiffness[:] *= S

    kid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_KEY, "pretension")
    if kid >= 0:
        mujoco.mj_resetDataKeyframe(m, d, kid)
    mujoco.mj_forward(m, d)

    ctl = TDCRIKControllerC2(m, d, tendon_distance_mm=4.0, velocity_scale=2.0,
                             damping_factor=LAMBDA, fps=FPS, verbose=False)

    for _ in range(int(1.0 / DT)):
        mujoco.mj_step(m, d)

    rng = np.random.default_rng(seed)
    c0 = d.body("EE_pos").xpos.copy() + np.array([0, 0, 0.012])
    sig_m = sigma_mm * 0.001
    tfun = FAMILY[member]["fn"]
    fixed = GAIN_C1 if ctrl == "C1" else 0.0

    log_t, log_err, log_sat, log_gain, log_cond, log_q = [], [], [], [], [], []

    for tick in range(int(sim_t * FPS)):
        t = tick / FPS
        target = tfun(c0, t)
        err = target - d.body("EE_pos").xpos
        err_c = err + (rng.normal(0, sig_m, 3) if sig_m > 0 else 0)
        gain_used = fixed if fixed > 0 else ctl.current_gain
        cr = gain_used * err_c
        cmd = np.clip(cr, -CLIP_LIM, CLIP_LIM)
        sat = bool(np.any(np.abs(cr) > CLIP_LIM))
        d.ctrl[:] = ctl.compute_target_qpos({"vx": cmd[0], "vy": cmd[1], "vz": cmd[2]})

        if t > PERIOD:
            try:
                c_j = float(np.linalg.cond(ctl.jacobian_pos @ ctl.jacobian_pos.T))
            except Exception:
                c_j = float("nan")
            log_t.append(t)
            log_err.append(np.linalg.norm(err) * 1000.0)
            log_sat.append(sat)
            log_gain.append(gain_used)
            log_cond.append(c_j)
            # 存 qpos 以便事后离线计算方位角/肌腱覆盖，无需再跑仿真
            log_q.append(d.qpos.copy())

        # ---- 关键：推进物理仿真。缺这一步则轨迹不会动，base 也无法与论文对账。
        for _ in range(SUB):
            mujoco.mj_step(m, d)

    t_a = np.asarray(log_t, dtype=float)
    e_a = np.asarray(log_err, dtype=float)
    g_a = np.asarray(log_gain, dtype=float)
    c_a = np.asarray(log_cond, dtype=float)
    s_a = np.asarray(log_sat, dtype=bool)

    if save:
        OUTDIR.mkdir(parents=True, exist_ok=True)
        tag = f"{ctrl}_{member}_S{fmt(S)}_sig{fmt(sigma_mm)}_seed{seed}"
        np.savez_compressed(
            OUTDIR / f"{tag}.npz",
            t=t_a, err_true=e_a, sat_flag=s_a, cur_gain=g_a, cond_J=c_a,
            qpos=np.asarray(log_q, dtype=np.float32),
            S=np.float64(S), gain_used=np.float64(GAIN_C1 if fixed > 0 else 0.0),
            sigma_mm=np.float64(sigma_mm), lam=np.float64(LAMBDA),
            member=np.array(member), ctrl=np.array(ctrl),
            params=np.array(FAMILY[member]["params"]),
        )

    # 触发比例：用与控制器一致的 win=20 滑窗后的 cond 越过 C_up 的时间占比
    sm = rolling(c_a, 20)
    fired_frac = float(np.nanmean(sm > C_UP)) if np.isfinite(sm).any() else 0.0

    return {
        "member": member, "ctrl": ctrl, "S": S, "sigma_mm": sigma_mm, "seed": seed,
        "n": len(e_a),
        "err_mean": float(np.nanmean(e_a)),
        "err_tail": float(np.nanmean(e_a[-120:])),
        "err_p95": float(np.nanpercentile(e_a, 95)),
        "rmse": float(np.sqrt(np.nanmean(e_a ** 2))),
        "sat_frac": float(np.nanmean(s_a)),
        "cond_p50": float(np.nanpercentile(c_a, 50)),
        "cond_p95": robust_p95(c_a),
        "cond_max": float(np.nanmax(c_a)) if np.isfinite(c_a).any() else float("nan"),
        "gain_min": float(np.nanmin(g_a)),
        "gain_max": float(np.nanmax(g_a)),
        "gain_end": float(g_a[-1]) if len(g_a) else float("nan"),
        "gain_reversals": int(np.sum(np.abs(np.diff(np.sign(np.diff(g_a)))) > 0)),
        "fired_frac": fired_frac,
        "params": FAMILY[member]["params"],
    }


# ----------------------------- 判定 -----------------------------
def verdict(cond_p95_c1, delta_pct, fired):
    """按"该成员实际 cond 水平"判定，而不是按 S 分档 —— 这是本脚本相对旧版的关键修正。

    旧版按 S<=1.5 / S>=2.2 分 normal/degraded，但同一 S 下不同成员的 cond 可以差 36%
    （圆 191 vs 8 字 141），按 S 分档会把"本该触发"的成员判成误触发。
    """
    near = cond_p95_c1 >= 0.85 * C_UP          # 进入 C_up 的 15% 危险带
    if fired and not near:
        return "FALSE-TRIGGER"
    if fired and delta_pct < 0:
        return "TRUE-TRIGGER-NEGATIVE"         # 触发正确但降过头（锁存机制）
    if fired:
        return "triggered-OK"
    if (not fired) and near:
        return "MISSED"
    return "quiet-OK"


# ----------------------------- 主流程 -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--members", nargs="*", default=None,
                    help="要跑的族成员，默认全部")
    ap.add_argument("--S", nargs="*", type=float, default=None,
                    help="刚度点，默认 base=[1.0,1.5,2.0,2.5]，其余=[1.5,2.0,2.5]")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--sigma", type=float, default=0.0, help="观测噪声 (mm)")
    ap.add_argument("--probe", action="store_true",
                    help="可达性预检：只跑 S=1.5 的 C2，不写 npz")
    ap.add_argument("--force", action="store_true", help="覆盖已有 npz 重跑")
    ap.add_argument("--list", action="store_true", help="只列出族成员")
    ap.add_argument("--shard", default=None, metavar="i/N",
                    help="任务分片：只跑第 i 片（1-based），共 N 片，用于多进程并行")
    ap.add_argument("--no-report", action="store_true",
                    help="只跑仿真并落盘 npz，跳过汇总表/图（并行时由单个进程统一出表）")
    args = ap.parse_args()

    if args.list:
        print(f"{'member':<10}{'params':<28}description")
        print("-" * 96)
        for k, v in FAMILY.items():
            print(f"{k:<10}{v['params']:<28}{v['desc']}")
        return

    members = args.members or DEFAULT_MEMBERS

    jobs = []
    for mem in members:
        if args.S is not None:
            Ss = args.S
        else:
            Ss = DEFAULT_S.get(mem, DEFAULT_S_OTHER)
        for S in Ss:
            for ctrl in ("C1", "C2"):
                jobs.append((mem, S, ctrl))

    if args.probe:
        jobs = [(m, 1.5, "C2") for m in members]
        print(f"[probe] {len(jobs)} 次可达性预检（不写 npz，强制实跑）\n")

    # ---- 分片：按 job 顺序取模，保证各片负载均衡且互不重叠 ----
    if args.shard:
        try:
            si, sn = (int(x) for x in args.shard.split("/"))
        except ValueError:
            ap.error("--shard 需形如 1/8")
        if not (1 <= si <= sn):
            ap.error("--shard 需满足 1 <= i <= N")
        full = len(jobs)
        jobs = [j for k, j in enumerate(jobs) if k % sn == si - 1]
        print(f"[shard {si}/{sn}] 全矩阵 {full} 次，本片 {len(jobs)} 次")

    print(f"共 {len(jobs)} 次运行；阈值冻结 C_up={C_UP:g} / C_down={C_DOWN:g}\n")

    rows, t_start = [], time.time()
    gates = []
    total = len(jobs)

    for i, (mem, S, ctrl) in enumerate(jobs, 1):
        tag = f"{ctrl}_{mem}_S{fmt(S)}_sig{fmt(args.sigma)}_seed{args.seed}"
        npz = OUTDIR / f"{tag}.npz"
        if (not args.probe) and npz.exists() and not args.force:
            print(f"[{i}/{total}] skip (exists)  {tag}")
            continue

        t0 = time.time()
        r = run_one(mem, S, ctrl, seed=args.seed, sigma_mm=args.sigma,
                    save=not args.probe)
        dt = time.time() - t0
        el = time.time() - t_start
        eta = el / i * (total - i)

        flag = ""
        if not np.isfinite(r["cond_p95"]) or r["err_p95"] > 200:
            flag = "  <-- 检查可达性"
        print(f"[{i}/{total}] {tag:<44} err={r['err_mean']:7.3f}mm "
              f"p95={r['cond_p95']:7.1f} cond_max={r['cond_max']:7.1f} "
              f"sat={r['sat_frac']*100:5.1f}% fired={r['fired_frac']*100:5.1f}% "
              f"({dt:.1f}s, ETA {eta/60:.1f}min){flag}")

        if mem == "base":
            ok, msg = selfcheck(S, ctrl, r)
            print(f"         {msg}")
            if ok is False:
                gates.append(f"{ctrl} S={S:g}")

        rows.append(r)

    if args.probe:
        # 预检报告同时落盘，便于直接回传（不需要回传 npz）
        rep = Path(REPO) / "数据集/29_revision/probe_report.csv"
        rep.parent.mkdir(parents=True, exist_ok=True)
        with open(rep, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["member", "S", "ctrl", "err_mean_mm", "err_p95_mm",
                        "cond_p50", "cond_p95", "cond_max", "sat_pct", "verdict_hint"])
            for r in rows:
                hint = "OK"
                if not np.isfinite(r["cond_p95"]) or r["err_p95"] > 200:
                    hint = "UNREACHABLE?"
                elif r["err_p95"] > 60:
                    hint = "marginal"
                w.writerow([r["member"], r["S"], r["ctrl"], f"{r['err_mean']:.3f}",
                            f"{r['err_p95']:.3f}", f"{r['cond_p50']:.1f}",
                            f"{r['cond_p95']:.1f}", f"{r['cond_max']:.1f}",
                            f"{r['sat_frac']*100:.1f}", hint])
        print(f"\n[probe] 判定：err_p95 > 200 mm 或 cond_p95 为 nan 的成员不可达，需调整幅值后重跑。")
        print(f"[probe] 报告 -> {rep}")
        return

    if args.no_report:
        print(f"\n[done] 本片 {len(rows)} 次完成，npz 已落盘；--no-report 跳过汇总")
        return

    # ---- 补全：对跳过的项也读回 npz，保证汇总表完整 ----
    have = {(r["member"], r["S"], r["ctrl"]) for r in rows}
    for mem, S, ctrl in jobs:
        if (mem, S, ctrl) in have:
            continue
        tag = f"{ctrl}_{mem}_S{fmt(S)}_sig{fmt(args.sigma)}_seed{args.seed}"
        npz = OUTDIR / f"{tag}.npz"
        if not npz.exists():
            continue
        d = np.load(npz, allow_pickle=True)
        e_a = np.asarray(d["err_true"], float)
        c_a = np.asarray(d["cond_J"], float)
        g_a = np.asarray(d["cur_gain"], float)
        s_a = np.asarray(d["sat_flag"], bool)
        sm = rolling(c_a, 20)
        rows.append({
            "member": mem, "ctrl": ctrl, "S": S, "sigma_mm": args.sigma, "seed": args.seed,
            "n": len(e_a),
            "err_mean": float(np.nanmean(e_a)), "err_tail": float(np.nanmean(e_a[-120:])),
            "err_p95": float(np.nanpercentile(e_a, 95)),
            "rmse": float(np.sqrt(np.nanmean(e_a ** 2))),
            "sat_frac": float(np.nanmean(s_a)),
            "cond_p50": float(np.nanpercentile(c_a, 50)),
            "cond_p95": robust_p95(c_a),
            "cond_max": float(np.nanmax(c_a)),
            "gain_min": float(np.nanmin(g_a)), "gain_max": float(np.nanmax(g_a)),
            "gain_end": float(g_a[-1]),
            "gain_reversals": int(np.sum(np.abs(np.diff(np.sign(np.diff(g_a)))) > 0)),
            "fired_frac": float(np.nanmean(sm > C_UP)) if np.isfinite(sm).any() else 0.0,
            "params": FAMILY[mem]["params"],
        })

    # ---- 以 (member, S) 为键配 C1/C2 ----
    idx = {(r["member"], r["S"], r["ctrl"]): r for r in rows}
    pairs = []
    for (mem, S, ctrl) in sorted({(r["member"], r["S"], r["ctrl"]) for r in rows}):
        if ctrl != "C2":
            continue
        a = idx.get((mem, S, "C1"))
        b = idx.get((mem, S, "C2"))
        if not a or not b:
            continue
        delta = 100.0 * (a["err_mean"] - b["err_mean"]) / a["err_mean"] if a["err_mean"] > 0 else float("nan")
        pairs.append({
            "member": mem, "S": S, "params": FAMILY[mem]["params"],
            "cond_p95_C1": a["cond_p95"], "cond_max_C1": a["cond_max"],
            "cond_p95_C2": b["cond_p95"],
            "err_C1": a["err_mean"], "err_C2": b["err_mean"],
            "delta_pct": delta,
            "sat_C1": a["sat_frac"], "sat_C2": b["sat_frac"],
            "gain_switches": b["gain_reversals"], "fired": b["fired_frac"] > 0.01,
            "verdict": verdict(a["cond_p95"], delta, b["fired_frac"] > 0.01),
        })

    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    keys = ["member", "params", "S", "cond_p95_C1", "cond_max_C1", "cond_p95_C2",
            "err_C1", "err_C2", "delta_pct", "sat_C1", "sat_C2",
            "gain_switches", "fired", "verdict"]
    # 按 κ95 升序写盘：这样 CSV 直接就是 envelope 图的横轴顺序
    pairs_by_k = sorted(pairs, key=lambda x: x["cond_p95_C1"])
    with open(SUMMARY, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for p in pairs_by_k:
            w.writerow({k: p[k] for k in keys})

    # ---- 终端：逐 S 的 LaTeX 表 ----
    if gates:
        print("\n" + "!" * 92)
        print(f"自检未通过: {', '.join(gates)}")
        print("base 未复现论文既有数据 —— 其余成员的结论暂不可用。请先核对 SUB / DT / 增益 / 预热步数。")
        print("!" * 92)
    print("\n" + "=" * 92)
    for S in sorted({p["S"] for p in pairs}):
        sub = [p for p in pairs if p["S"] == S]
        print(f"\n%% S = {S:g}\n")
        print(r"\begin{tabular}{lccccl}")
        print(r"\hline")
        print(r"Member (unseen) & $\kappa_{95}$ & C1 (mm) & C2 (mm) & $\Delta$ (\%) & Verdict \\")
        print(r"\hline")
        for p in sub:
            name = p["member"] + (" (calib.)" if p["member"] == "base" else "")
            print(f"{name:<16}& {p['cond_p95_C1']:.1f} & {p['err_C1']:.2f} & "
                  f"{p['err_C2']:.2f} & {p['delta_pct']:+.1f} & {p['verdict']} \\\\")
        print(r"\hline")
        print(r"\end{tabular}")

    # ---- 族上界判据：response letter 的核心数字 ----
    print("\n" + "=" * 92)
    for S in sorted({p["S"] for p in pairs}):
        sub = [p for p in pairs if p["S"] == S]
        worst = max(sub, key=lambda p: p["cond_p95_C1"])
        over = [p["member"] for p in sub if p["cond_p95_C1"] > C_UP]
        print(f"S={S:g}: 族内最坏成员 cond p95 = {worst['cond_p95_C1']:.1f} "
              f"({worst['member']})  vs C_up = {C_UP:g}  ->  "
              f"{'覆盖 (C_up 是该族上界)' if not over else '越界: ' + ','.join(over)}")
        bad = [p["member"] for p in sub if p["delta_pct"] < 0]
        if bad:
            print(f"        负收益成员: {','.join(bad)}  (需在 envelope 中作为边界报告)")

    # ---- 每个成员的边界位置：首个出现正收益的 S ----
    print("\n" + "=" * 92)
    print("边界位置（该成员首个正收益的刚度点）—— 用于说明边界随构型移动")
    print("-" * 92)
    for mem in members:
        ps = sorted([p for p in pairs if p["member"] == mem], key=lambda x: x["S"])
        if not ps:
            continue
        edge = next((p for p in ps if p["delta_pct"] > 0), None)
        if edge is None:
            print(f"{mem:<10} 在 {[p['S'] for p in ps]} 内始终负收益")
            continue
        lo = [p for p in ps if p["S"] < edge["S"]]
        lo_s = f"{lo[-1]['S']:g} -> " if lo else ""
        print(f"{mem:<10} 转正于 S {lo_s}{edge['S']:g}"
              f"   κ95(C1)@转正 = {edge['cond_p95_C1']:.0f}"
              f"   C1 基线 = {edge['err_C1']:.2f} mm")

    # ---- κ 轴收敛检验：κ 越高收益是否越大 ----
    rho = spearman([p["cond_p95_C1"] for p in pairs], [p["delta_pct"] for p in pairs])
    print("\n" + "=" * 92)
    print(f"κ 轴收敛检验: Spearman rho(κ95, Δ%) = {rho:.2f}  （{len(pairs)} 个 member×S 点）")
    print("  接近 +1 => κ 单调决定收益，阈值有物理身份；明显偏低 => 收益还依赖第二个量")
    if np.isfinite(rho) and rho >= 0.8:
        print("  结论：可在论文中主张 κ 是主判据，C_up 是其拐点。")
    elif np.isfinite(rho):
        print("  结论：κ 必要但不充分，论文应写双判据（κ + 当前误差水平）。")

    print(f"\n逐成员汇总 -> {SUMMARY}")
    print(f"时序 npz    -> {OUTDIR}")
    print(f"总耗时 {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
