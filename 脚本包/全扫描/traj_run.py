import os, sys, types, numpy as np
p = types.ModuleType("pynput"); kb = types.ModuleType("pynput.keyboard")
kb.Key = type("Key", (), {}); kb.Listener = type("Listener", (), {"__init__": lambda *a,**k: None, "start": lambda *a,**k: None, "stop": lambda *a,**k: None})
p.keyboard = kb; sys.modules["pynput"]=p; sys.modules["pynput.keyboard"]=kb
import sys as _sys; from pathlib import Path as _Path; REPO = str(_Path(__file__).resolve().parents[2]); _sys.path.insert(0, REPO)
import mujoco
from opencr_mujoco.controllers.tdcr_ik_controller_c2 import TDCRIKControllerC2

SCENE = REPO + "/assets/tdcr/tdcr_3seg.xml"
DT = 0.001; FPS = 50; PERIOD = 10.0; SIM_T = 20.0

TRAJ     = os.environ.get("TRAJ", "8")
S_TEST   = float(os.environ.get("S_TEST", "2.5"))
LAMBDA   = float(os.environ.get("LAMBDA", "0.05"))
SIGMA_MM = float(os.environ.get("OBS_NOISE_MM", "0.0"))
SEED     = int(os.environ.get("NOISE_SEED", "42"))
FIXED    = float(os.environ.get("FIXED_GAIN", "0.0"))
CLIP_LIM = float(os.environ.get("CLIP_LIM", "1.0"))

# C1/C2 判定 —— 唯一开关
if FIXED > 0:
    CTRL = "C1"; _DEF = REPO + "/results_c1_clean"
else:
    CTRL = "C2"; _DEF = REPO + "/results_c2_clean"
OUTDIR = os.environ.get("OUTDIR", _DEF)
os.makedirs(OUTDIR, exist_ok=True)

def fmt(x):
    return str(x).replace(".", "p").replace("-", "m")
TAG = f"{CTRL.lower()}_{TRAJ}_S{fmt(S_TEST)}_sig{fmt(SIGMA_MM)}_G{fmt(FIXED)}_lam{fmt(LAMBDA)}_seed{SEED}"

m = mujoco.MjModel.from_xml_path(SCENE); d = mujoco.MjData(m)
m.opt.gravity[:] = 0; m.opt.timestep = DT
m.jnt_stiffness[:] *= S_TEST
kid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_KEY, "pretension")
if kid >= 0: mujoco.mj_resetDataKeyframe(m, d, kid)
mujoco.mj_forward(m, d)
ctl = TDCRIKControllerC2(m, d, tendon_distance_mm=4.0, velocity_scale=2.0,
                          damping_factor=LAMBDA, fps=FPS, verbose=False)
for _ in range(int(1.0/DT)): mujoco.mj_step(m, d)

rng = np.random.default_rng(SEED)
c0 = d.body('EE_pos').xpos.copy() + np.array([0, 0, 0.012])
sig_m = SIGMA_MM * 0.001

def traj_8(c, t):
    r = min(t/PERIOD, 1.0); phi = 2*np.pi*t/PERIOD
    return c + r*(0.07*np.sin(phi)*np.array([1,0,0]) + 0.075*np.sin(phi)*np.cos(phi)*np.array([0,1,0]))
def traj_circle(c, t):
    r = 0.06 * min(t/PERIOD, 1.0); phi = 2*np.pi*t/(PERIOD*0.8)
    return c + r*np.cos(phi)*np.array([1,0,0]) + r*np.sin(phi)*np.array([0,1,0])
def traj_spiral(c, t):
    tau = t/PERIOD; phi = 4*np.pi*tau; r = 0.03 * tau
    return c + r*np.cos(phi)*np.array([1,0,0]) + r*np.sin(phi)*np.array([0,1,0])
TFUN = {"8": traj_8, "circle": traj_circle, "spiral": traj_spiral}[TRAJ]

sub = max(1, int(round(1.0/(FPS*DT))))
log_t, log_err, log_sat, log_gain, log_cond = [], [], [], [], []
for tick in range(int(SIM_T*FPS)):
    t = tick/FPS
    target = TFUN(c0, t)
    err = target - d.body('EE_pos').xpos
    err_c = err + (rng.normal(0, sig_m, 3) if sig_m > 0 else 0)
    gain_used = FIXED if FIXED > 0 else ctl.current_gain
    cr = gain_used * err_c
    cmd = np.clip(cr, -CLIP_LIM, CLIP_LIM)
    sat = bool(np.any(np.abs(cr) > CLIP_LIM))
    d.ctrl[:] = ctl.compute_target_qpos({"vx": cmd[0], "vy": cmd[1], "vz": cmd[2]})
    if t > PERIOD:
        try: c_j = float(np.linalg.cond(ctl.jacobian_pos @ ctl.jacobian_pos.T))
        except: c_j = float('nan')
        log_t.append(t); log_err.append(np.linalg.norm(err)*1000)
        log_sat.append(sat); log_gain.append(gain_used); log_cond.append(c_j)
    for _ in range(sub): mujoco.mj_step(m, d)

e = np.array(log_err); s = np.array(log_sat); g = np.array(log_gain); c = np.array(log_cond)

print(f"[{TAG}]")
print(f"  ctrl={CTRL}  S={S_TEST}  sigma={SIGMA_MM}  lam={LAMBDA}")
print(f"  err_true: mean={e.mean():.3f} std={e.std():.3f} max={e.max():.3f}")
print(f"  cmd_sat: {s.sum()}/{len(s)} = {s.mean()*100:.2f}%")
print(f"  gain: min={g.min():.1f} max={g.max():.1f}")
print(f"  cond_J: med={np.median(c):.2f} max={c.max():.2f}")

np.savez(os.path.join(OUTDIR, TAG + ".npz"),
         ctrl=CTRL, S=S_TEST, sigma_mm=SIGMA_MM,
         gain_hi=40.0, gain_lo=20.0, gain_used=FIXED, lam=LAMBDA, seed=SEED,
         traj=TRAJ, dt=DT, clip_lim=CLIP_LIM,
         t=np.array(log_t), err_true=e, sat_flag=s,
         cur_gain=g, cond_J=c)
