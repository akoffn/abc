# ================= B1 外推检验：粘进一个 Jupyter 单元，回车 =================
# 24 次 = 4 个 held-out 构型 x S{1.5, 2.0, 2.5} x {C1, C2}，8 核约 5-7 分钟。
# 不动仓库任何文件；rot90 / circ55 只在内存里补进 FAMILY。
# kernel 必须是装有 mujoco 的那个（和跑 50 次同一个，一般是 /root/opencr_env）。
import os, sys, glob, time
import numpy as np
from multiprocessing import Pool

try:
    import mujoco  # noqa: F401
except ImportError:
    raise SystemExit('这个 kernel 没有 mujoco。请切到 opencr_env 那个 kernel 再跑。')

# --- 定位仓库（路径变了也能自己找到） --------------------------------------
cands = [os.environ.get('OPENCR_REPO', '/root/opencr-mujoco-main')] + glob.glob('/root/*opencr*') + glob.glob('/home/*/*opencr*')
REPO = next((p for p in cands if os.path.isdir(os.path.join(p, 'opencr_mujoco'))), None)
assert REPO, '找不到 opencr-mujoco 仓库，请把 REPO 手动改成实际路径'
sys.path.insert(0, os.path.join(REPO, '脚本包/29返修构型覆盖'))
import traj_family as tf
print('REPO =', REPO, '| OUTDIR =', tf.OUTDIR)

# --- 只补两个新成员（ar_fat / off_x 本来就在族里，从未跑过，天然 held-out） --
EX, EY = np.array([1., 0., 0.]), np.array([0., 1., 0.])
if 'rot90' not in tf.FAMILY:
    tf.FAMILY['rot90'] = dict(fn=tf.make_lissajous(tf.A_X0, tf.A_Y0, EY, EX, k=2.0),
                              params='in-plane rot 90deg', desc='held-out')
if 'circ55' not in tf.FAMILY:
    tf.FAMILY['circ55'] = dict(fn=tf.make_lissajous(0.055, 0.055, EX, EY, k=1.0, psi=np.pi / 2),
                               params='circle r=55mm', desc='held-out')

HELD = ['ar_fat', 'off_x', 'rot90', 'circ55']
IN8 = ['base', 'scale_s', 'scale_l', 'ar_thin', 'tilt45', 'tilt90', 'off_z', 'k3']
SS = [1.5, 2.0, 2.5]
tag = lambda m, S, c: f'{c}_{m}_S{tf.fmt(S)}_sig0p0_seed42'
JOBS = [(m, S, c) for m in HELD for S in SS for c in ('C1', 'C2')
        if not (tf.OUTDIR / f'{tag(m, S, c)}.npz').exists()]
print(f'待跑 {len(JOBS)} 次')

def one(j):
    m, S, c = j
    t0 = time.time()
    tf.run_one(m, S, c)
    return f'{tag(m, S, c):<40} {time.time() - t0:.0f}s'

if JOBS:
    t0 = time.time()
    with Pool(6) as pool:
        for msg in pool.imap_unordered(one, JOBS, chunksize=1):
            print('  ' + msg, flush=True)
    print(f'用时 {(time.time() - t0) / 60:.1f} min')

# --- 从 npz 汇总 ------------------------------------------------------------
rows = {}
for p in glob.glob(str(tf.OUTDIR / '*.npz')):
    d = np.load(p, allow_pickle=True)
    if 'member' not in d or 'ctrl' not in d or float(d['sigma_mm']) != 0.0:
        continue
    rows[(str(d['member']), float(d['S']), str(d['ctrl']))] = dict(
        err=float(np.nanmean(np.asarray(d['err_true'], float))),
        sat=float(np.nanmean(np.asarray(d['sat_flag'], float))),
        k=float(np.nanpercentile(np.asarray(d['cond_J'], float), 95)))

def pair(m, S):
    a, b = rows.get((m, S, 'C1')), rows.get((m, S, 'C2'))
    if not a or not b:
        return None
    return dict(m=m, S=S, k=a['k'], e1=a['err'], e2=b['err'], sat=a['sat'],
                d=(a['err'] - b['err']) / a['err'] * 100 if a['err'] else 0.0)

def show(title, ms):
    print('\n' + title)
    print(f"{'member':<12}{'S':>5}{'k95':>8}{'C1':>8}{'C2':>8}{'delta%':>9}{'satC1%':>8}")
    out = []
    for m in ms:
        for S in SS:
            r = pair(m, S)
            if r:
                out.append(r)
                print(f"{m:<12}{S:>5.1f}{r['k']:>8.1f}{r['e1']:>8.2f}{r['e2']:>8.2f}{r['d']:>9.1f}{r['sat']*100:>8.1f}")
    return out

IN = show('=== in-sample（8 成员，核对用）===', IN8)
HO = show('=== held-out（4 个未参与推导的构型）===', HELD)

def gate(title, data, use_sat):
    tp = fp = fn = tn = 0; bad = []
    for r in data:
        pred = (r['k'] > tf.C_UP) and (r['sat'] > 0 if use_sat else True)
        act = r['d'] > 0
        if pred and act: tp += 1
        elif pred: fp += 1; bad.append((r['m'], r['S'], 'FP', round(r['d'], 1), round(r['sat'] * 100, 1)))
        elif act: fn += 1; bad.append((r['m'], r['S'], 'FN', round(r['d'], 1), round(r['sat'] * 100, 1)))
        else: tn += 1
    n = tp + fp + fn + tn
    print(f'{title:<30} TP={tp:<3} FP={fp:<3} FN={fn:<3} TN={tn:<3} n={n:<3} acc={(tp+tn)/max(n,1)*100:.0f}%')
    for b in bad: print('     ', b)

print('\n=== 门限检验（把这一段发回给我）===')
gate('in-sample  k>160', IN, False)
gate('in-sample  k>160 & sat>0', IN, True)
gate('held-out   k>160', HO, False)
gate('held-out   k>160 & sat>0', HO, True)
print('\n判读：held-out 上 FP=0 且 FN=0 → 门限可写成"族外预测"；有 FP/FN → 如实写"族外失效"。')
