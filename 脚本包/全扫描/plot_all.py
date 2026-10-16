import numpy as np, glob, os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.family":"STIXGeneral","mathtext.fontset":"stix",
    "font.size":11,"axes.labelsize":12,"axes.titlesize":12,"legend.fontsize":9,
    "axes.grid":True,"grid.alpha":0.25,"grid.linestyle":":","axes.linewidth":0.9,
    "savefig.bbox":"tight","savefig.pad_inches":0.02})

OUT = "/root/opencr-mujoco-main/paper_figs"
os.makedirs(OUT, exist_ok=True)

def load(ctrl, task, traj):
    """返回 [(S或sig, err_mean)] 排序"""
    d = f"{ctrl}/{'刚度扫描' if task=='stiffness' else '噪声扫描'}_{traj}"
    out = []
    for f in sorted(glob.glob(f"{d}/*.npz")):
        a = np.load(f, allow_pickle=True)
        key = float(a["S"]) if task=="stiffness" else float(a["sigma_mm"])
        e   = float(np.asarray(a["err_true"]).mean())
        out.append((key, e))
    return sorted(out)

# 检查 8 个目录
print("=== 数据清点 ===")
for ctrl in ["C1","C2"]:
    for task in ["stiffness","noise"]:
        for traj in ["8字","圆形"]:
            x = load(ctrl, task, traj)
            print(f"  {ctrl}/{task}/{traj}: {len(x)} 组")

def plot_pair(ax_st, ax_no, ctrl_st, ctrl_no, traj, ttl):
    ax = ax_st
    ax.plot([x for x,_ in ctrl_st], [e for _,e in ctrl_st], "s--",
            color="#c0392b", lw=1.5, ms=5, mfc="#c0392b", mec="k", mew=0.4, label="C1")
    ax.plot([x for x,_ in ctrl_no], [e for _,e in ctrl_no], "o-",
            color="#2980b9", lw=1.6, ms=5.5, mfc="#2980b9", mec="k", mew=0.4, label="C2")
    ax.set_xlabel(r"Stiffness $S$"); ax.set_ylabel("err mean (mm)")
    ax.set_title(f"(a) Stiffness, {ttl}")
    ax.legend(loc="upper left")

    ax = ax_no
    ax.plot([x for x,_ in ctrl_st], [e for _,e in ctrl_st], "s--",
            color="#c0392b", lw=1.5, ms=5, mfc="#c0392b", mec="k", mew=0.4, label="C1")
    ax.plot([x for x,_ in ctrl_no], [e for _,e in ctrl_no], "o-",
            color="#2980b9", lw=1.6, ms=5.5, mfc="#2980b9", mec="k", mew=0.4, label="C2")
    ax.set_xlabel(r"Noise $\sigma$ (mm)"); ax.set_ylabel("err mean (mm)")
    ax.set_title(f"(b) Noise, {ttl} ($S{{=}}2.5$)")
    ax.legend(loc="upper left")

# 8 字
C1s = load("C1","stiffness","8字"); C2s = load("C2","stiffness","8字")
C1n = load("C1","noise","8字");     C2n = load("C2","noise","8字")
fig, ax = plt.subplots(1,2,figsize=(8,3.2))
plot_pair(ax[0], ax[1], C1s, C2s, "8字", "8-shape")
fig.tight_layout(); fig.savefig(f"{OUT}/F1_8shape.pdf"); fig.savefig(f"{OUT}/F1_8shape.png", dpi=300)
plt.close(fig); print("→ F1_8shape")

# 圆形
C1s = load("C1","stiffness","圆形"); C2s = load("C2","stiffness","圆形")
C1n = load("C1","noise","圆形");     C2n = load("C2","noise","圆形")
fig, ax = plt.subplots(1,2,figsize=(8,3.2))
plot_pair(ax[0], ax[1], C1s, C2s, "圆形", "Circle")
fig.tight_layout(); fig.savefig(f"{OUT}/F1_circle.pdf"); fig.savefig(f"{OUT}/F1_circle.png", dpi=300)
plt.close(fig); print("→ F1_circle")

print("\n输出目录:", OUT)
