import os, sys, glob, time
import numpy as np
from multiprocessing import Pool

import mujoco
print('mujoco', mujoco.__version__, flush=True)

REPO = os.environ.get('OPENCR_REPO', '/root/opencr-mujoco-main')
PKG = REPO + '/脚本包/29返修构型覆盖'
sys.path.insert(0, PKG)
os.chdir(PKG)
import traj_family as tf
print('OUT', tf.OUTDIR, '| C_UP', tf.C_UP, flush=True)

SIGMAS = [1.0, 2.0, 5.0]
SS = [1.0, 1.5, 2.0, 2.2, 2.5]
jobs = [('base', S, c, sg) for sg in SIGMAS for S in SS for c in ('C1', 'C2')
        if not (tf.OUTDIR / f'{c}_base_S{tf.fmt(S)}_sig{tf.fmt(sg)}_seed42.npz').exists()]
print('待跑', len(jobs), '次', flush=True)

def one(j):
    m, S, c, sg = j
    t = time.time()
    tf.run_one(m, S, c, seed=42, sigma_mm=sg)
    return f'{c}_base_S{tf.fmt(S)}_sig{tf.fmt(sg)}  {time.time()-t:.0f}s'

if jobs:
    with Pool(6) as pool:
        for r in pool.imap_unordered(one, jobs, chunksize=1):
            print('  ' + r, flush=True)

# ---- 汇总 ----
R = {}
for f in glob.glob(str(tf.OUTDIR / '*.npz')):
    d = np.load(f, allow_pickle=True)
    if str(d['member']) != 'base':
        continue
    key = (float(d['S']), str(d['ctrl']), float(d['sigma_mm']))
    R[key] = (float(np.nanmean(d['err_true'])), float(np.nanmean(d['sat_flag'])) * 100,
              float(np.nanpercentile(d['cond_J'], 95)),
              float(np.nanmean(tf.rolling(np.asarray(d['cond_J'], float), 20) > tf.C_UP)) * 100)

print('\n=== 噪声扫描：base 8 字 ----', flush=True)
print(f"{'sigma':>6}{'S':>6} | {'C1 err':>8}{'C2 err':>8}{'delta%':>8} | {'C1 sat%':>8}{'C2 sat%':>8} | {'k95':>7}{'fire%':>7}", flush=True)
for sg in [0.0] + SIGMAS:
    for S in SS:
        a, b = R.get((S, 'C1', sg)), R.get((S, 'C2', sg))
        if not a or not b:
            continue
        dl = (a[0] - b[0]) / a[0] * 100 if a[0] else float('nan')
        print(f'{sg:>6.1f}{S:>6.1f} | {a[0]:>8.2f}{b[0]:>8.2f}{dl:>+8.1f} | '
              f'{a[1]:>8.1f}{b[1]:>8.1f} | {a[2]:>7.0f}{a[3]:>7.1f}', flush=True)
    print('-' * 74, flush=True)
