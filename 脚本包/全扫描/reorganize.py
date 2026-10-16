import os, re, glob, shutil

ROOT = "/root/opencr-mujoco-main"
SRC_DIRS = glob.glob(f"{ROOT}/logs/*/") + [f"{ROOT}/results_official_dt/",
             f"{ROOT}/results_noise_v2/", f"{ROOT}/results_noise_obs/"]

def classify(path):
    """返回 (mode, task_type)"""
    b = os.path.basename(path)

    # 1) 识别 C1/C2
    mode = "unknown"
    if re.search(r"_C2_|c2_|c2asym|c2b|c2c|c2deg|c2high|c2_lock|c2_T12|c2_refinal", b, re.I):
        mode = "C2"
    elif re.search(r"_C1_|c1_|c2asym2", b, re.I):  # c2asym2 是 C2 的文件命名
        if "c2asym2" in b: mode = "C2"
        else: mode = "C1"

    # 2) 从内容判断（读前 500 字节）
    if mode == "unknown":
        try:
            with open(path, errors="ignore") as f:
                txt = f.read(2000)
            m = re.search(r"gain:\s+min=([\d.]+)\s+max=([\d.]+)", txt)
            if m:
                gmin = float(m.group(1))
                mode = "C2" if gmin < 39 else "C1"
            elif "current_gain" in txt or "switches" in txt:
                mode = "C2"
        except: pass

    # 3) 识别任务类型
    task = "other"
    if re.search(r"S[\d.]+.*sig0", b) or re.search(r"stiff|_S[\d.]+_", b):
        task = "stiffness"
    if re.search(r"sig[\d.]+", b) or "sigma" in b or "noise" in b:
        task = "noise"
    if re.search(r"circle|spiral|traj", b, re.I):
        task = "trajectory"
    if re.search(r"tv|sched", b, re.I):
        task = "timevarying"
    if re.search(r"coupling|clip|s13|ratio|thr|audit|diag|gain", b, re.I):
        task = "special"
    return mode, task

# 扫描所有数据文件
print("=== DRY RUN：分类预览（不实际移动）===\n")
plan = {"C1": {}, "C2": {}, "unknown": {}}
n_scanned = 0
for d in SRC_DIRS:
    if not os.path.isdir(d): continue
    for f in glob.glob(f"{d}*"):
        if not os.path.isfile(f): continue
        if not re.search(r"\.(log|npz|csv)$", f): continue
        n_scanned += 1
        mode, task = classify(f)
        plan.setdefault(mode, {}).setdefault(task, []).append(f)

for mode in ["C1", "C2", "unknown"]:
    print(f"\n{'='*60}\n{mode}\n{'='*60}")
    for task in sorted(plan[mode].keys()):
        files = plan[mode][task]
        print(f"  [{task}]  {len(files)} 个文件")
        for f in files[:3]:
            print(f"      {os.path.relpath(f, ROOT)}")
        if len(files) > 3:
            print(f"      ... 还有 {len(files)-3} 个")

print(f"\n=== 总计扫描 {n_scanned} 个文件 ===")
