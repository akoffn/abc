import os, sys, types, numpy as np, time
p = types.ModuleType("pynput"); kb = types.ModuleType("pynput.keyboard")
kb.Key = type("Key", (), {}); kb.Listener = type("Listener", (), {"__init__": lambda *a,**k: None, "start": lambda *a,**k: None, "stop": lambda *a,**k: None})
p.keyboard = kb; sys.modules["pynput"]=p; sys.modules["pynput.keyboard"]=kb
sys.path.insert(0, "/root/opencr-mujoco-main")
import mujoco
from opencr_mujoco.controllers.tdcr_ik_controller_c2 import TDCRIKControllerC2

TRAJ       = os.environ.get("TRAJ", "8")
S_TEST     = float(os.environ.get("S_TEST", "1.0"))
LAMBDA     = float(os.environ.get("LAMBDA", "0.05"))
SIGMA_MM   = float(os.environ.get("OBS_NOISE_MM", "0.0"))
SEED       = int(os.environ.get("NOISE_SEED", "42"))
FIXED_GAIN = float(os.environ.get("FIXED_GAIN", "0"))
MODE       = "C1" if FIXED_GAIN > 0 else "C2"
TASK       = os.environ.get("TASK", "stiffness")
TAG        = os.environ.get("TAG", "test")
OUT_DIR    = os.environ.get("OUT_DIR", f"DATA/{MODE}/{TASK}")

SCENE = "/root/opencr-mujoco-main/assets/tdcr/tdcr_3seg.xml"
DT=0.001; FPS=50; PERIOD=10.0; SIM_T=20.0
SIGMA_M = SIGMA_MM * 0.001

m = mujoco.MjModel.from_xml_path(SCENE); d = mujoco.MjData(m)
m.opt.gravity[:]=0; m.opt.timestep=DT
m.jnt_stiffness[:] *= S_TEST
kid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_KEY, "pretension")
if kid>=0: mujoco.mj_resetDataKeyframe(m,d,kid)
mujoco.mj_forward(m,d)
ctl = TDCRIKControllerC2(m,d,tendon_distance_mm=4.0,velocity_scale=2.0,
                          damping_factor=LAMBDA,fps=FPS,verbose=False)
for _ in range(int(1.0/DT)): mujoco.mj_step(m,d)
rng = np.random.default_rng(SEED)
c0 = d.body('EE_pos').xpos.copy()+np.array([0,0,0.012])

def traj_fn(c,t):
    if TRAJ=="8":
        r=min(t/PERIOD,1.0); phi=2*np.pi*t/PERIOD
        return c+r*(0.07*np.sin(phi)*np.array([1,0,0])+0.075*np.sin(phi)*np.cos(phi)*np.array([0,1,0]))
    if TRAJ=="circle":
        phi=2*np.pi*t/(PERIOD*0.8); r=0.06*min(t/PERIOD,1.0)
        return c+r*np.cos(phi)*np.array([1,0,0])+r*np.sin(phi)*np.array([0,1,0])
    if TRAJ=="spiral":
        tau=t/PERIOD; phi=4*np.pi*tau; r=0.03*tau
        return c+r*np.cos(phi)*np.array([1,0,0])+r*np.sin(phi)*np.array([0,1,0])
    return c

sub=max(1,int(round(1.0/(FPS*DT))))
T,E,S_,G,C = [],[],[],[],[]
t0=time.time()
for tick in range(int(SIM_T*FPS)):
    t=tick/FPS
    target=traj_fn(c0,t)
    err=target-d.body('EE_pos').xpos
    err_c=err+(rng.normal(0,SIGMA_M,3) if SIGMA_M>0 else 0)
    gain=FIXED_GAIN if FIXED_GAIN>0 else ctl.current_gain
    cr=gain*err_c
    cmd=np.clip(cr,-1,1)
    sat=bool(np.any(np.abs(cr)>1.0))
    d.ctrl[:]=ctl.compute_target_qpos({"vx":cmd[0],"vy":cmd[1],"vz":cmd[2]})
    if t>PERIOD:
        try: cj=float(np.linalg.cond(ctl.jacobian_pos@ctl.jacobian_pos.T))
        except: cj=float('nan')
        T.append(t); E.append(np.linalg.norm(err)*1000)
        S_.append(sat); G.append(gain); C.append(cj)
    for _ in range(sub): mujoco.mj_step(m,d)

e=np.array(E); s=np.array(S_); g=np.array(G); c=np.array(C)
os.makedirs(OUT_DIR,exist_ok=True)
np.savez(f"{OUT_DIR}/{TAG}.npz", t=np.array(T), err_true=e, sat_flag=s, cur_gain=g, cond_J=c,
    switches=np.array(ctl.gain_switches,dtype=object) if ctl.gain_switches else np.array([]),
    S=S_TEST, sigma_mm=SIGMA_MM, gain=FIXED_GAIN, lam=LAMBDA, seed=SEED, dt=DT, traj=TRAJ, mode=MODE, task=TASK)
print(f"[{MODE}|{TASK}] S={S_TEST} σ={SIGMA_MM} gain={'FIXED='+str(FIXED_GAIN) if FIXED_GAIN>0 else 'adaptive'}")
print(f"  err_mean={e.mean():.3f} err_max={e.max():.3f} sat={s.mean()*100:.2f}% gain=[{g.min():.0f},{g.max():.0f}] time={time.time()-t0:.1f}s")
print(f"  → {OUT_DIR}/{TAG}.npz")
