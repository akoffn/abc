# -*- coding: utf-8 -*-
_exp2b_src = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""意见二清单化实验 v2：环境外生（球沿自由空间名义路径），固定球写入 XML"""
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
TOUCH = R_LINK + R_BALL - PEN
BASE = open(SCENE, encoding="utf-8").read()

MOCAP = ('<body name="obst" pos="0 0 0" mocap="true">'
         '<geom name="obst_ball" type="sphere" size="%.4f" rgba="1 0 0 1" '
         'contype="1" conaffinity="1" condim="3" friction="1.0 0.005 0.0001"/></body>' % R_BALL)
S_MOCAP = "/tmp/sc_mocap.xml"
with open(S_MOCAP, "w", encoding="utf-8") as f:
    f.write(BASE.replace('<geom type="plane"', MOCAP + '\n        <geom type="plane"', 1))

S_FIX = {}
AX = {"x": np.array([1.0, 0, 0]), "y": np.array([0, 1.0, 0]), "z": np.array([0, 0, 1.0])}
NOMINAL = {}     # S -> list of (t, pos)


def mkfix(tag, pos):
    fx = ('<body name="obst" pos="%.5f %.5f %.5f"><geom name="obst_ball" type="sphere" '
          'size="%.4f" rgba="1 0 0 1" contype="1" conaffinity="1" condim="3" '
          'friction="1.0 0.005 0.0001"/></body>' % (pos[0], pos[1], pos[2], R_BALL))
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
    S, ctrl, ball, ton = j["S"], j["ctrl"], j["ball"], j["ton"]
    scene = S_FIX[j["fixtag"]] if ball == "fix" else (S_MOCAP if ball else SCENE)
    m = mujoco.MjModel.from_xml_path(scene); d = mujoco.MjData(m)
    m.opt.gravity[:] = 0; m.opt.timestep = DT; m.jnt_stiffness[:] *= S
    kid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_KEY, "pretension")
    if kid >= 0:
        mujoco.mj_resetDataKeyframe(m, d, kid)
    mujoco.mj_forward(m, d)
    ctl = TDCRIKControllerC2(m, d, tendon_distance_mm=4.0, velocity_scale=2.0,
                             damping_factor=LAM, fps=FPS, verbose=False)
    for _ in range(int(1.0 / DT)):
        mujoco.mj_step(m, d)
    c0 = d.body("EE_pos").xpos.copy() + np.array([0, 0, 0.012]) + np.asarray(j["c0off"], float)

    mid = -1
    if ball in ("x", "y", "z"):
        bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "obst")
        mid = int(m.body_mocapid[bid])
        d.mocap_pos[mid] = c0 + np.array([0.0, 0.0, 0.12])
    nominal = NOMINAL.get(S) if ball in ("x", "y", "z") else None

    fixed = GAIN if ctrl == "C1" else 0.0
    E, C, Sf, NC, PN, E1, E2, CAP = [], [], [], 0, [], [], [], []
    hit0 = None
    n = 0
    for tick in range(int(SIM_T * FPS)):
        t = tick / FPS
        p = target(c0, t)
        if mid >= 0 and t >= ton and nominal is not None:
            q = np.asarray(nominal[tick][1])
            d.mocap_pos[mid] = q + TOUCH * AX[ball]      # 外生：沿名义路径，与控制器无关
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
                if hit0 is None:
                    hit0 = round(t, 3)
                PN.append(max(-min(d.contact[i].dist for i in range(d.ncon)), 0.0) * 1000.0)
    E = np.asarray(E); C = np.asarray(C)
    out = dict(member=j["member"], S=S, ctrl=ctrl, ball=ball, ton=ton,
               err=float(E.mean()), p95=float(np.percentile(E, 95)),
               cond=float(np.percentile(C, 95)), sat=100 * float(np.mean(Sf)),
               nc=NC, n=n, pen=float(np.mean(PN)) if PN else 0.0,
               e1=float(np.mean(E1)) if E1 else None,
               e2=float(np.mean(E2)) if E2 else None, hit=hit0)
    if j.get("cap"):
        out["traj"] = CAP
    return out


def main():
    t0 = time.time()
    print("=== 阶段0 采 3 档自由空间名义路径（C1, 无接触）===", flush=True)
    caps = Pool(3).map(run, [dict(member="base", S=s, ctrl="C1", ball=None, ton=0.0,
                                  c0off=(0, 0, 0), cap=True) for s in (1.0, 1.5, 2.5)])
    for c in caps:
        NOMINAL[c["S"]] = c["traj"]
        print("  S=%.1f 路径 %d 点, 自由空间 err=%.3f mm, k95=%.1f" %
              (c["S"], len(c["traj"]), c["err"], c["cond"]), flush=True)

    tr = NOMINAL[2.5]
    pick = [q for q in tr if 14.0 <= q[0] <= 18.0]
    p_ref = np.array(pick[len(pick) // 2][1])
    p_nxt = np.array(pick[len(pick) // 2 + 4][1])
    tang = p_nxt - p_ref; tang /= (np.linalg.norm(tang) + 1e-12)
    side = np.array([1.0, 0.0, 0.0]); side = side - tang * float(side @ tang)
    side /= (np.linalg.norm(side) + 1e-12)
    mkfix("a", p_ref + TOUCH * side)
    mkfix("b", p_ref + (TOUCH + 0.006) * side)
    print("  固定球参考点 %s | 切向 %s | 球心 a=%s b=%s" %
          (np.round(p_ref, 4), np.round(tang, 3),
           np.round(p_ref + TOUCH * side, 4), np.round(p_ref + (TOUCH + 0.006) * side, 4)), flush=True)

    jobs = []
    for v, ton in (("x", 12.0), ("y", 0.0), ("z", 0.0)):
        for S in (1.0, 1.5, 2.5):
            for c in ("C1", "C2"):
                jobs.append(dict(member="con_%s_t%d" % (v, int(ton)), S=S, ctrl=c,
                                 ball=v, ton=ton, c0off=(0, 0, 0)))
    for tag, lab in (("a", "fix_near"), ("b", "fix_off")):
        for c in ("C1", "C2"):
            jobs.append(dict(member=lab, S=2.5, ctrl=c, ball="fix", ton=0.0,
                             c0off=(0, 0, 0), fixtag=tag))
    print("=== 阶段1 并行 %d 次（6 进程）===" % len(jobs), flush=True)
    with Pool(6) as p:
        res = p.map(run, jobs)

    print("\n%-12s %-4s %-4s %8s %8s %8s %6s %9s %6s %7s" %
          ("member", "S", "ctrl", "k95", "err", "p95", "sat%", "ncon/n", "pen", "hit"))
    print("-" * 84)
    for r in res:
        print("%-12s %-4.1f %-4s %8.1f %8.3f %8.3f %6.1f %9s %6s %7s" % (
            r["member"], r["S"], r["ctrl"], r["cond"], r["err"], r["p95"], r["sat"],
            "%d/%d" % (r["nc"], r["n"]), "%.2f" % r["pen"] if r["nc"] else "-", r["hit"]))

    idx = {(r["member"], r["S"], r["ctrl"]): r for r in res}
    pairs = []
    for (mn, S, c), r1 in idx.items():
        if c != "C1":
            continue
        r2 = idx[(mn, S, "C2")]
        dl = 100 * (r1["err"] - r2["err"]) / r1["err"] if r1["err"] > 0 else float("nan")
        pairs.append([mn, S, r1["cond"], r1["sat"], r2["sat"], r1["err"], r2["err"], dl, r1["nc"], r2["nc"]])
    pairs.sort(key=lambda x: (x[0], x[1]))
    print("\n=== 配对 Δ% = (C1-C2)/C1 ===")
    print("%-12s %-4s %8s %7s %7s %8s %8s %8s %8s  %s" %
          ("member", "S", "k95", "satC1", "satC2", "errC1", "errC2", "Δ%", "ncon", "sat判号"))
    print("-" * 94)
    ok = bad = 0
    for q in pairs:
        if q[3] > 0 and q[7] > 0:
            ok += 1; flag = "OK"
        elif q[3] == 0 and q[7] <= 0:
            ok += 1; flag = "OK"
        else:
            bad += 1; flag = "MISMATCH"
        print("%-12s %-4.1f %8.1f %7.1f %7.1f %8.3f %8.3f %+8.1f %8s  %s" % (
            q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], "%d/%d" % (q[8], q[9]), flag))
    print("\n一致性: sat>0 ⟺ Δ>0 命中 %d / 冲突 %d （共 %d 对）" % (ok, bad, len(pairs)))
    json.dump(dict(pairs=pairs, raw=[{k: v for k, v in r.items() if k != "traj"} for r in res]),
              open("/tmp/exp2b.json", "w"), ensure_ascii=False, default=str)
    print("=== 总耗时 %.0fs ===" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
'''
open('/tmp/_exp2b_pen.py','w',encoding='utf-8').write(_exp2b_src)


# ================= 驱动：接触压入深度（加载量级）扫描 =================
import sys as _sys, json as _json, time as _time
_sys.path.insert(0, "/tmp")
import _exp2b_pen as E
import numpy as np
from multiprocessing import Pool

def run_pen(j):
    jj = dict(j)
    pen = jj.pop("pen")
    E.TOUCH = E.R_LINK + E.R_BALL - pen      # 越深 = 压得越紧 = 载荷越大
    return E.run(jj)

if __name__ == "__main__":
    t0 = _time.time()
    print("=== 阶段0 自由空间名义路径（3 档）===", flush=True)
    caps = Pool(3).map(E.run, [dict(member="base", S=s, ctrl="C1", ball=None, ton=0.0,
                                    c0off=(0, 0, 0), cap=True) for s in (1.0, 1.5, 2.5)])
    for c in caps:
        E.NOMINAL[c["S"]] = c["traj"]
        print("  S=%.1f k95=%.1f err=%.3f" % (c["S"], c["cond"], c["err"]), flush=True)

    jobs = []
    for pen in (0.002, 0.004, 0.006):
        for S in (1.0, 1.5, 2.5):
            for c in ("C1", "C2"):
                jobs.append(dict(member="pen%d" % round(pen * 1000), S=S, ctrl=c,
                                 ball="x", ton=0.0, c0off=(0, 0, 0), pen=pen))
    print("=== 阶段1 %d 次 ===" % len(jobs), flush=True)
    with Pool(6) as p:
        res = p.map(run_pen, jobs)

    print("\n%-8s %-4s %-3s %8s %8s %8s %6s %9s %6s" %
          ("pen", "S", "ctl", "k95", "err", "p95", "sat%", "ncon/n", "penum"))
    print("-" * 70)
    for r in res:
        print("%-8s %-4.1f %-3s %8.1f %8.3f %8.3f %6.1f %9s %6s" % (
            r["member"], r["S"], r["ctrl"], r["cond"], r["err"], r["p95"], r["sat"],
            "%d/%d" % (r["nc"], r["n"]), "%.2f" % r["pen"] if r["nc"] else "-"))

    idx = {(r["member"], r["S"], r["ctrl"]): r for r in res}
    pairs = []
    for (mn, S, c), r1 in idx.items():
        if c != "C1":
            continue
        r2 = idx[(mn, S, "C2")]
        dl = 100 * (r1["err"] - r2["err"]) / r1["err"] if r1["err"] > 0 else float("nan")
        pairs.append([mn, S, r1["cond"], r1["sat"], r2["sat"], dl])
    pairs.sort(key=lambda x: (x[0], x[1]))
    print("\n=== 配对 ===")
    print("%-8s %-4s %8s %7s %7s %9s  %s" % ("pen", "S", "k95", "satC1", "satC2", "D%", "gate"))
    ng = 0
    for q in pairs:
        on = (q[2] > 160.0) and (q[3] >= 1.0)
        hit = (on and q[5] > 0) or ((not on) and q[5] <= 0)
        ng += 1 if hit else 0
        print("%-8s %-4.1f %8.1f %7.1f %7.1f %+9.1f  %s" %
              (q[0], q[1], q[2], q[3], q[4], q[5], ("ON " if on else "off") + ("" if hit else "  <-- MISS")))
    print("\n判据命中 %d / %d" % (ng, len(pairs)))
    print("PAIRS_JSON=" + _json.dumps([[q[0], q[1], round(q[2], 1), round(q[3], 1), round(q[5], 1)] for q in pairs]))
    print("=== 总耗时 %.0fs ===" % (_time.time() - t0), flush=True)
