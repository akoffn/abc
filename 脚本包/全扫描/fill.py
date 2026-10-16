import os, subprocess, itertools

S_LIST   = [0.5,0.75,1.0,1.1,1.2,1.25,1.26,1.28,1.3,1.32,1.34,1.4,1.5,1.6,1.8,1.9,2.0,
            2.05,2.06,2.07,2.08,2.09,2.1,2.11,2.12,2.13,2.14,2.15,2.2,2.25,2.30,2.5,3.0,3.5,4.0,4.5,5.0]
SIG_LIST = [0.0,0.005,0.01,0.02,0.05,0.1,0.2,0.5,1.0,2.0,5.0]

jobs = []
for ctrl, fixed in [("C1", 40), ("C2", 0)]:
    for traj, tkey in [("8", "8字"), ("circle", "圆形")]:
        # 刚度：37 点
        for S in S_LIST:
            tag = f"{ctrl}_stiffness_{tkey}_S{S}_sig0.0"
            out = f"{ctrl}/刚度扫描_{tkey}"
            fp  = f"{out}/{tag}.npz"
            if not os.path.exists(fp):
                jobs.append((fixed, "8" if traj=="8" else "circle", S, 0.0, "stiffness", out, tag))
        # 噪声：11 档
        for sig in SIG_LIST:
            tag = f"{ctrl}_noise_{tkey}_S2.5_sig{sig}"
            out = f"{ctrl}/噪声扫描_{tkey}"
            fp  = f"{out}/{tag}.npz"
            if not os.path.exists(fp):
                jobs.append((fixed, "8" if traj=="8" else "circle", 2.5, sig, "noise", out, tag))

with open("/tmp/jobs.txt", "w") as f:
    for j in jobs:
        f.write(" ".join(map(str, j)) + "\n")
print(f"需补跑: {len(jobs)} 组")
