# 扫描脚本包

生成 `数据集/C1` 和 `数据集/C2` 的完整链路。

## 核心链路

1. **fill.py** — 生成任务清单 `/tmp/jobs.txt`
   - S_LIST: 37 个刚度值 (0.5~5.0)
   - SIG_LIST: 11 个噪声值 (0~5.0)
   - 4 组: C1×8字, C1×圆形, C2×8字, C2×圆形
   - C1 通过 FIXED_GAIN=40，C2 通过 FIXED_GAIN=0

2. **fill.sh** — 单次运行包装
   - 参数顺序: FIXED TRAJ S SIG TASK OUTDIR TAG

3. **run_row.sh** — 另一种包装（参数顺序不同）

4. **run_official.py** — 真正的内核（即 experiments/run.py）
   - 加载 TDCRIKControllerC2
   - FIXED_GAIN>0 → C1，否则 → C2
   - 保存 npz: t, err_true, sat_flag, cur_gain, cond_J, switches, ...

## 数据生成命令

    # 1. 生成任务清单
    /root/opencr_env/bin/python fill.py

    # 2. 并行跑（4 路）
    cat /tmp/jobs.txt | xargs -P 4 -L 1 /tmp/fill.sh

    # 3. 画图
    /root/opencr_env/bin/python plot_all.py

## 辅助脚本

- **plot_all.py** — 生成 F1_8shape / F1_circle 对比图
- **reorganize.py** — 分类整理旧数据
- **run_clean.sh** — 单点 C1/C2 清洁版
- **run_highS.sh** — 高刚度 C2
- **run28.sh** — 28 数据集
- **traj_run.py** — 备份内核（字段名略不同）
- **fill2~6.sh** — fill 变体

## 关键参数

- 场景: assets/tdcr/tdcr_3seg.xml
- 基准刚度: 0.2454369260617026 N·m/rad
- DT=0.001, FPS=50, PERIOD=10.0, SIM_T=20.0
- C2: gain_hi=40, gain_lo=20, cond_in=160, cond_out=70, win=20, warmup=50

---

## 28 数据集扫描（子目录 28/）

独立的 28 行表扫描（C1 × 8字 × S/sig/G/λ），跟 C1/C2 主扫描用不同内核。

### 文件

- **28/run28.sh** — 单次运行（参数顺序: S SIG G LAM）
- **28/run_all.sh** — 一键跑完 28 组，参数为并行数
- **28/jobs28.txt** — 28 组任务清单（格式: S SIG G LAM）
- **28/traj_run.py** — 28 专用内核（读 OUTDIR，文件名带 G/lam/seed）

### 用法

    # 单条
    bash 28/run28.sh 2.5 0.0 40 0.05

    # 全部（4 路并行）
    bash 28/run_all.sh 4

### 输出

    数据集/28/results/*.npz
    数据集/28/logs/*.log

### 与主扫描的区别

| 项 | 主扫描 (fill.py) | 28 扫描 (run28.sh) |
|---|---|---|
| 内核 | experiments/run.py | 28/traj_run.py |
| 输出变量 | OUT_DIR | OUTDIR |
| 文件命名 | C1_stiffness_8字_S2.5_... | c1_8_S2p5_sig0p0_G40p0_lam0p05_seed42 |
| 覆盖 | C1/C2 × 8字/圆形 × 刚度/噪声 | C1 × 8字 × S/sig/G/λ |
| 用途 | 论文主图/Table2 | 论文 28 行表 |
