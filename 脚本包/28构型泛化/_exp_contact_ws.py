#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""意见二清单化实验：工作空间 / 接触位置 / 自由-接触过渡 / 真碰撞"""
import os, sys, types, json, time
import numpy as np
from multiprocessing import Pool

_p = types.ModuleType("pynput"); _kb = types.ModuleType("pynput.keyboard")
_kb.Key = type("Key", (), {})
_kb.Listener = type("Listener", (), {"__init__": lambda *a, **k: None,
                                     "start": lambda *a, **k: None,
                                     "stop": lambda *a, **k: None})
_p.keyboard = _kb; sys.modules["pynput"] = _p; sys.modules["pynput.keyboard"] = _kb
os.environ.setdefault("MUJOCO_GL", "disable")
REPO = os.environ.get("OPENCR_REPO", "/root/opencr-mujoco-main"); sys.path.insert(0, REPO)
import mujoco  # noqa: E402
from opencr_mujoco.controllers.tdcr_ik_controller_c2 import TDCRIKControllerC2  # noqa: E402

SCENE = REPO + "/assets/tdcr/tdcr_3seg.xml"
DT, FPS, SUB = 0.001, 50, 20
CLIP, GAIN, LAM, PERIOD, SIM_T = 1.0, 40.0, 0.05, 10.0, 20.0
AX0, AY0 = 0.070, 0.0375
R_BALL, R_LINK, PEN = 0.008, 0.006, 0.004
TOUCH = R_LINK + R_BALL - PEN          # 球心到杆轴 10mm
BASE = open(SCENE, encoding="utf-8").read()

MOCAP = ('<body name="obst" pos="0 0 0" mocap="true">'
         '<geom name="obst_ball" type="sphere" size="%.4f" rgba="1 0 0 1" '
         'contype="1" conaffinity="1" condim="3" friction="1.0 0.005 0.0001"/></body>' % R_BALL)
S_MOCAP = "/tmp/sc_mocap.xml"
with open(S_MOCAP, "w", encoding="utf-8") as f:
    f.write(BASE.replace('<geom type="plane"', MOCAP + '\n        <geom type="plane"', 1))

S_FIX = {}
for tag, off in (("a", TOUCH), ("b", TOUCH + 0.004)):
    fx = ('<body name="obst" pos="0 0 0"><geom name="obst_ball" type="sphere" size="%.4f" '
          'rgba="1 0 0 1" contype="1" conaffinity="1" condim="3" '
          'friction="1.0 0.005 0.0001"/></body>' % R_BALL)
    p = "/tmp/sc_fix_%s.xml" % tag
    with open(p, "w", encoding="utf-8") as f:
        f.write(BASE.replace('<geom type="plane"', fx + '\n        <geom type="plane"', 1))
    S_FIX[tag] = p


def target(c0, t):
    r = min(t / PERIOD, 1.0)
    phi = 2.0 * np.pi * t / PERIOD
    return c0 + r * (AX0 * np.sin(phi) * np.array([1.0, 0, 0])
                     + AY0 * np.sin(2 * phi) * np.array([0, 1.0, 0]))


def run(j):
    S, ctrl, ball, ton, c0off = j["S"], j["ctrl"], j["ball"], j["ton"], j["c0off"]
    if ball == "fix":
        scene = S_FIX[j["fixtag"]]
    elif ball:
        scene = S_MOCAP
    else:
        scene = SCENE
    m = mujoco.MjModel.from_xml_path(scene); d = mujoco.MjData(m)
    m.opt.gravity[:] = 0; m.opt.timestep = DT; m.jnt_stiffness[:] *= S
    kid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_KEY, "pretension")
    if kid >= 0:
        mujoco.mj_resetDataKeyframe(m, d, kid)
    if ball == "fix":
        bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "obst")
        gid = m.body_geomadr[bid]
        m.geom_pos[gid] = j["fixat"]
    mujoco.mj_forward(m, d)
    ctl = TDCRIKControllerC2(m, d, tendon_distance_mm=4.0, velocity_scale=2.0,
                             damping_factor=LAM, fps=FPS, verbose=False)
    for _ in range(int(1.0 / DT)):
        mujoco.mj_step(m, d)
    c0 = d.body("EE_pos").xpos.copy() + np.array([0, 0, 0.012]) + np.asarray(c0off, float)

    mid = -1
    if ball in ("x", "y", "z"):
        bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "obst")
        mid = int(m.body_mocapid[bid])
        d.mocap_pos[mid] = c0 + np.array([0.0, 0.0, 0.10])
    AX = {"x": np.array([1.0, 0, 0]), "y": np.array([0, 1.0, 0]), "z": np.array([0, 0, 1.0])}

    fixed = GAIN if ctrl == "C1" else 0.0
    E, C, Sf, NC, PN, E1, E2, CAP = [], [], [], 0, [], [], [], []
    first_hit = None
    n = 0
    for tick in range(int(SIM_T * FPS)):
        t = tick / FPS
        p = target(c0, t)
        if mid >= 0 and t >= ton:
            ee = d.body("EE_pos").xpos
            d.mocap_pos[mid] = ee + TOUCH * AX[ball]
        err = p - d.body("EE_pos").xpos
        g = fixed if fixed > 0 else ctl.current_gain
        cr = g * err
        cmd = np.clip(cr, -CLIP, CLIP)
        sat = bool(np.any(np.abs(cr) > CLIP))
        d.ctrl[:] = ctl.compute_target_qpos({"vx": cmd[0], "vy": cmd[1], "vz": cmd[2]})
        if t > PERIOD:
            try:
                C.append(float(np.linalg.cond(ctl.jacobian_pos @ ctl.jacobian_pos.T)))
            except Exception:
                C.append(np.nan)
            e = np.linalg.norm(err) * 1000.0
            E.append(e); Sf.append(sat)
            (E1 if t < ton else E2).append(e)
        for _ in range(SUB):
            mujoco.mj_step(m, d)
        if j.get("cap"):
            CAP.append((round(t, 3), [round(float(v), 5) for v in d.body("EE_pos").xpos]))
        if t > PERIOD:
            n += 1
            if d.ncon > 0:
                NC += 1
                if first_hit is None:
                    first_hit = round(t, 3)
                PN.append(max(-min(d.contact[i].dist for i in range(d.ncon)), 0.0) * 1000.0)
    E = np.asarray(E); C = np.asarray(C)
    out = dict(member=j["member"], S=S, ctrl=ctrl, ball=ball, ton=ton,
               err=float(E.mean()), p95=float(np.percentile(E, 95)),
               cond=float(np.percentile(C, 95)), sat=100 * float(np.mean(Sf)),
               nc=NC, n=n, pen=float(np.mean(PN)) if PN else 0.0,
               e1=float(np.mean(E1)) if E1 else None,
               e2=float(np.mean(E2)) if E2 else None, hit=first_hit)
    if j.get("cap"):
        out["traj"] = CAP
    return out


def main():
    t0 = time.time()
    print("=== 阶段0 采集自由空间末端路径（S=2.5, C1）===", flush=True)
    cap = run(dict(member="base", S=2.5, ctrl="C1", ball=None, ton=0.0,
                   c0off=(0, 0, 0), cap=True))
    traj = cap["traj"]
    pick = [q for q in traj if 14.0 <= q[0] <= 18.0]
    p_ref = np.array(pick[len(pick) // 2][1])
    p_nxt = np.array(pick[len(pick) // 2 + 4][1])
    tang = p_nxt - p_ref; tang /= (np.linalg.norm(tang) + 1e-12)
    side = np.array([1.0, 0.0, 0.0])
    side = side - tang * float(side @ tang)
    side /= (np.linalg.norm(side) + 1e-12)
    print("  捕获 %d 点 | 参考点 %s | 切向 %s" % (len(traj), np.round(p_ref, 4), np.round(tang, 3)), flush=True)

    jobs = []
    for S in (1.0, 1.5, 2.5):
        for c in ("C1", "C2"):
            jobs.append(dict(member="off_x60", S=S, ctrl=c, ball=None, ton=0.0,
                             c0off=(0.060, 0, 0)))
    for v, ton in (("x", 12.0), ("y", 0.0), ("z", 0.0)):
        for S in (1.0, 1.5, 2.5):
            for c in ("C1", "C2"):
                jobs.append(dict(member="con_%s_t%d" % (v, int(ton)), S=S, ctrl=c,
                                 ball=v, ton=ton, c0off=(0, 0, 0)))
    for tag, lab, ext in (("a", "fix_near", 0.0), ("b", "fix_off", 0.006)):
        for c in ("C1", "C2"):
            jobs.append(dict(member=lab, S=2.5, ctrl=c, ball="fix", ton=0.0,
                             c0off=(0, 0, 0), fixtag=tag,
                             fixat=p_ref + (TOUCH + ext) * side))

    print("=== 阶段1 并行 %d 次（6 进程）===" % len(jobs), flush=True)
    with Pool(6) as p:
        res = p.map(run, jobs)
    print("\n%-14s %-4s %-4s %8s %8s %8s %6s %8s %9s %8s" %
          ("member", "S", "ctrl", "k95", "err", "p95", "sat%", "ncon/n", "pen", "Δ%"))
    print("-" * 92)
    for r in res:
        print("%-14s %-4.1f %-4s %8.1f %8.3f %8.3f %6.1f %8s %9s %8s" % (
            r["member"], r["S"], r["ctrl"], r["cond"], r["err"], r["p95"], r["sat"],
            "%d/%d" % (r["nc"], r["n"]), "%.2f" % r["pen"] if r["nc"] else "-", "-"))
    print("\n=== Δ% = (C1_err - C2_err)/C1_err，按场景配对 ===")
    idx = {}
    for r in res:
        idx[(r["member"], r["S"], r["ctrl"])] = r
    pairs = []
    for (mn, S, c), r1 in idx.items():
        if c != "C1":
            continue
        r2 = idx[(mn, S, "C2")]
        dl = 100 * (r1["err"] - r2["err"]) / r1["err"] if r1["err"] > 0 else float("nan")
        pairs.append((mn, S, r1["cond"], r1["sat"], r2["sat"], r1["err"], r2["err"], dl, r1["nc"], r2["nc"]))
    pairs.sort(key=lambda x: (x[0], x[1]))
    print("%-14s %-4s %8s %7s %7s %8s %8s %8s %6s" %
          ("member", "S", "k95", "satC1", "satC2", "errC1", "errC2", "Δ%", "ncon"))
    print("-" * 84)
    ok = bad = 0
    for q in pairs:
        flag = ""
        if q[3] > 0 and q[7] > 0: ok += 1; flag = "sat+ / gain"
        elif q[3] == 0 and q[7] <= 0: ok += 1; flag = "sat0 / no-gain"
        else: bad += 1; flag = "MISMATCH"
        print("%-14s %-4.1f %8.1f %7.1f %7.1f %8.3f %8.3f %+8.1f %6s  %s" % (
            q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], "%d/%d" % (q[8], q[9]), flag))
    print("\n判据一致性: sat>0 ⟺ Δ>0 命中 %d / 冲突 %d （共 %d 对）" % (ok, bad, len(pairs)))
    json.dump(dict(pairs=pairs, raw=[{k: v for k, v in r.items() if k != "traj"} for r in res]),
              open("/tmp/exp2.json", "w"), ensure_ascii=False, default=str)
    print("=== 总耗时 %.0fs ===" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
