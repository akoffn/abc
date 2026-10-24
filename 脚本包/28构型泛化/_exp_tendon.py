# -*- coding: utf-8 -*-
"""肌腱组合轴完整实验：5 种组合 × S{1.0,1.5,2.0,2.5} × {C1,C2} = 40 次。

协议与 traj_family.py 完全一致（同一 DT / FPS / PERIOD / SIM_T / LAMBDA /
CLIP_LIM / GAIN_C1），仅把 clark->tendon 映射换成不同肌腱组合，
因此结果与既有 50 对同口径、可直接并入判据检验。
"""
import os, sys, json, time
import numpy as np

TF_DIR = os.environ.get("TF_DIR", "/root/opencr-mujoco-main/脚本包/29返修构型覆盖")
sys.path.insert(0, TF_DIR)
import traj_family as TF

import mujoco
from opencr_mujoco.controllers.tdcr_ik_controller_c2 import TDCRIKControllerC2

OUT = os.environ.get("TF_OUT", "/root/opencr-mujoco-main/数据集/29_revision/tendon")
os.makedirs(OUT, exist_ok=True)

# 9 根腱索引：段 s 占 3s..3s+2
MODES = {
    "drop_s1_t2": "seg1 uses 2 of 3 tendons (t2 slack)",
    "drop_s3_t0": "seg3 uses 2 of 3 tendons (t0 slack)",
    "drop_s1s3":  "seg1 and seg3 both 2 of 3",
    "gain_085":   "all nine tendons at 85% effective stroke",
    "gain_115":   "all nine tendons at 115% effective stroke",
}
SS = [1.0, 1.5, 2.0, 2.5]
CTRLS = ["C1", "C2"]


class KinWrap:
    def __init__(self, k, mode):
        object.__setattr__(self, "_k", k)
        object.__setattr__(self, "_mode", mode)

    def __getattr__(self, n):
        return getattr(object.__getattribute__(self, "_k"), n)

    def __setattr__(self, n, v):
        if n in ("_k", "_mode"):
            object.__setattr__(self, n, v)
        else:
            setattr(object.__getattribute__(self, "_k"), n, v)

    def clark_to_tendons_mm(self, clark):
        t = np.asarray(self._k.clark_to_tendons_mm(clark), float).copy()
        m = self._mode
        if m == "drop_s1_t2":   t[2] = 0.0
        elif m == "drop_s3_t0": t[6] = 0.0
        elif m == "drop_s1s3":  t[2] = 0.0; t[6] = 0.0
        elif m == "gain_085":   t *= 0.85
        elif m == "gain_115":   t *= 1.15
        return t


def run(job):
    mode, S, ctrl = job
    m = mujoco.MjModel.from_xml_path(TF.SCENE)
    d = mujoco.MjData(m)
    m.opt.gravity[:] = 0
    m.opt.timestep = TF.DT
    m.jnt_stiffness[:] *= S

    kid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_KEY, "pretension")
    if kid >= 0:
        mujoco.mj_resetDataKeyframe(m, d, kid)
    mujoco.mj_forward(m, d)

    c = TDCRIKControllerC2(m, d, tendon_distance_mm=4.0, velocity_scale=2.0,
                           damping_factor=TF.LAMBDA, fps=TF.FPS, verbose=False)
    c.kinematics = KinWrap(c.kinematics, mode)

    for _ in range(int(1.0 / TF.DT)):
        mujoco.mj_step(m, d)

    c0 = d.body("EE_pos").xpos.copy() + np.array([0, 0, 0.012])
    tfun = TF.FAMILY["base"]["fn"]
    fixed = TF.GAIN_C1 if ctrl == "C1" else 0.0

    errs, conds, sats = [], [], []
    for tick in range(int(TF.SIM_T * TF.FPS)):
        t = tick / TF.FPS
        err = tfun(c0, t) - d.body("EE_pos").xpos
        g = fixed if fixed > 0 else c.current_gain
        cr = g * err
        cmd = np.clip(cr, -TF.CLIP_LIM, TF.CLIP_LIM)
        sat = bool(np.any(np.abs(cr) > TF.CLIP_LIM))
        d.ctrl[:] = c.compute_target_qpos({"vx": cmd[0], "vy": cmd[1], "vz": cmd[2]})
        if t > TF.PERIOD:
            errs.append(np.linalg.norm(err) * 1000.0)
            try:
                conds.append(float(np.linalg.cond(c.jacobian_pos @ c.jacobian_pos.T)))
            except Exception:
                conds.append(float("nan"))
            sats.append(sat)
        for _ in range(TF.SUB):
            mujoco.mj_step(m, d)

    e = np.asarray(errs); cd = np.asarray(conds); sa = np.asarray(sats)
    np.savez_compressed(os.path.join(OUT, "C1_%s_S%s.npz" % (mode, str(S).replace(".", "p")))
                        if ctrl == "C1" else os.path.join(OUT, "C2_%s_S%s.npz" % (mode, str(S).replace(".", "p"))),
                        t=np.arange(len(e)) / TF.FPS + TF.PERIOD,
                        err_true=e, cond_J=cd, sat_flag=sa)
    return dict(mode=mode, S=S, ctrl=ctrl, n=len(e),
                err=float(np.nanmean(e)), err_p95=float(np.nanpercentile(e, 95)),
                cond95=TF.robust_p95(cd),
                cond_max=float(np.nanmax(cd)) if np.isfinite(cd).any() else float("nan"),
                sat=100.0 * float(np.nanmean(sa)))


if __name__ == "__main__":
    import multiprocessing as mp
    jobs = [(m, S, c) for m in MODES for S in SS for c in CTRLS]
    print("== 肌腱组合实验：%d 次（%d 组合 × %d 档 × 2 控制器） ==" % (len(jobs), len(MODES), len(SS)), flush=True)
    t0 = time.time()
    with mp.Pool(16) as p:
        res = p.map(run, jobs)
    print("完成 %d 次，%.0fs\n" % (len(res), time.time() - t0), flush=True)

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(res, f, indent=1)

    idx = {(r["mode"], r["S"], r["ctrl"]): r for r in res}
    print("%-11s %5s %8s %8s %8s %7s | %8s %8s %7s | %7s %s" % (
        "mode", "S", "k95_C1", "errC1", "errC2", "satC1", "d%", "k95_C2", "satC2", "gate", ""), flush=True)
    print("-" * 104, flush=True)
    rows = []
    for md in MODES:
        for S in SS:
            a = idx.get((md, S, "C1")); b = idx.get((md, S, "C2"))
            if not a or not b:
                continue
            dd = 100.0 * (a["err"] - b["err"]) / a["err"] if a["err"] > 0 else float("nan")
            gate = (a["cond95"] > TF.C_UP) and (a["sat"] >= 1.0)
            rows.append(dict(mode=md, S=S, k=a["cond95"], e1=a["err"], e2=b["err"],
                             d=dd, s1=a["sat"], s2=b["sat"], gate=gate,
                             pos=int(dd > 0.05)))
            print("%-11s %5.1f %8.1f %8.2f %8.2f %7.1f | %+8.1f %8.1f %7.1f | %7s %s" % (
                md, S, a["cond95"], a["err"], b["err"], a["sat"], dd, b["cond95"], b["sat"],
                "1" if gate else "0", "" if (gate == bool(dd > 0.05)) else "<-- 不一致"), flush=True)

    # 并入 50 对做总检验
    with open("/tmp/tendon_rows.json", "w") as f:
        json.dump(rows, f)
    tp = sum(1 for r in rows if r["gate"] and r["pos"])
    fp = sum(1 for r in rows if r["gate"] and not r["pos"])
    fn = sum(1 for r in rows if not r["gate"] and r["pos"])
    tn = len(rows) - tp - fp - fn
    print("\n本批 n=%d：判据(κ95>160 且 sat≥1%%) TP%d FP%d FN%d TN%d" % (len(rows), tp, fp, fn, tn), flush=True)
    kp = sum(1 for r in rows if r["k"] > 160 and r["pos"])
    kf = sum(1 for r in rows if r["k"] > 160 and not r["pos"])
    print("单判据 κ95>160：TP%d FP%d  (饱和率单独：TP%d FP%d)" % (
        kp, kf,
        sum(1 for r in rows if r["s1"] >= 1.0 and r["pos"]),
        sum(1 for r in rows if r["s1"] >= 1.0 and not r["pos"])), flush=True)
    print("=== 总耗时 %.0fs ===" % (time.time() - t0), flush=True)
