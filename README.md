# Condition-Number-Triggered Gain Scheduling for Inverse Kinematics Control of Tendon-Driven Continuum Robots

Repository for the paper. OpenCR-MuJoCo is used as the evaluation platform
(backbone discretized into a rigid-link chain with elastic joints, tendons
actuated by MuJoCo's native tendon model, calibrated against SoRoSim
Cosserat-rod solutions).

## 一句话

C2 用雅可比条件数 cond_J 在线触发降增益（40→20），在高刚度退化区把跟踪误差降低 42%~71%（表 1），饱和率归零，低刚度无额外精度损失。

## 效果图

<p align="center">
  <img src="paper_figs/fig2_C1_vs_C2.png" width="70%" alt="C1 vs C2: error vs stiffness"/>
</p>

## Abstract（论文摘要）

腱驱动连续体机器人（TDCR）的任务空间逆运动学控制器在高刚度工况下会出现性能退化。本文针对原生控制器（C1）的退化问题，提出基于雅可比条件数（cond_J）的增益调度策略 C2。实验表明，cond_J 的滑动窗均值超过阈值的时间占比（frac）从 S≤1.5 的 0% 上升至 S=2.2/2.5 的 28.06%/35.41%，在 S=2.2~3.0 区间保持 20% 以上，可作为在线工况指标。C2 据此在 cond_J 高时降低增益（40→20），低时恢复。在五个刚度工况下，C2 将退化区误差降低 42%~71%，饱和率归零，低刚度下无额外精度损失。C2 有效缓解了 S≤2.5 的增益失配区；当 S≥5.0 时，系统进入物理饱和截断（C2 饱和率亦显著上升），超出算法可控范围，这明确了 C2 的适用边界。

**关键词：** 腱驱动连续体机器人；逆运动学；增益调度；雅可比条件数；鲁棒控制；自适应增益

## 方法（4 句）

- **C1（基线）**：固定增益 GAIN=40 的任务空间 IK 控制器；高刚度下退化，S=2.5 时误差达 18.86 mm、饱和率 23.85%。
- **观测**：cond_J 的 20 步滑动窗均值超过阈值（160）的时间占比 frac 从 S≤1.5 的 0% 上升至 S=2.2/2.5 的 28.06%/35.41%，可作为在线工况指标。
- **C2**：cond_J 高时降低增益（40→20），低时恢复；切换带 C_up=160 / C_down=70，非对称渐变（降 5 步，升 50 步）。
- **结果**：S=2.2 误差 8.37→4.82 mm（降 42.4%），S=2.5 误差 18.86→5.41 mm（降 71.3%），C2 饱和率全为 0；S=5.0 时 C2 误差升至 54.95 mm、饱和率 39.08%，进入物理饱和截断，超出算法可控范围。

## 快速开始（复现论文）

> **运行环境说明：** 脚本使用相对路径（基于脚本自身位置解析），可在任意 Linux 环境直接运行。Windows 用户只需把仓库放在无中文路径下即可。

```bash
pip install -r requirements.txt

python 脚本包/28评估脚本/表1.py                  # 表 1：cond_J 信号有效性 + C1/C2 对比
python 脚本包/28评估脚本/C2泛化_圆形噪声.py       # 表 2：泛化验证数据
python 脚本包/控制器阈值论证脚本.py               # 图 2：阈值裕度图
python 脚本包/28评估脚本/C2泛化_圆形噪声_画图.py  # 图 4：泛化效果图
python 脚本包/全扫描/plot_all.py                 # 图 1/图 3 的数据与综合图（F1_8shape/F1_circle）
```

## 复现论文

| 图表 | 内容 | 命令 |
|---|---|---|
| 表 1 | 五行核心表（S=1.0/1.5/2.2/2.5/3.0，触发占比、C1/Fix20/C2 误差与饱和率） | `python 脚本包/28评估脚本/表1.py` |
| 表 2 | 泛化验证（8 字/圆 × 无噪/加噪，降幅 71%~83%，跨轨迹范围广于表 1） | `python 脚本包/28评估脚本/C2泛化_圆形噪声.py` |
| 图 1 | C1 刚度扫描（err vs S，叠加 sat%） | 成品见 `paper_figs/fig1_S_err.png`；绘图脚本未随仓库提供 |
| 图 2 | 阈值裕度图（正常组 vs 退化组 cond_J 分布） | `python 脚本包/控制器阈值论证脚本.py` |
| 图 3 | C1 vs C2 双线（err vs S，三段标注） | 成品见 `paper_figs/fig2_C1_vs_C2.png`；绘图脚本未随仓库提供 |
| 图 4 | 泛化效果（圆形轨迹 + 噪声） | `python 脚本包/28评估脚本/C2泛化_圆形噪声_画图.py` |

> 注：`python 脚本包/全扫描/plot_all.py` 输出综合图 `F1_8shape` / `F1_circle`（stiffness + noise 双面板、C1/C2 双线），用于核对图 1/图 3 的数据来源。

## 数据

- `数据集/`：C1 / C2 / Fix20 的刚度扫描与噪声扫描 npz（8 字与圆形轨迹，S ∈ {0.5…5.0}，σ 分档）。
- 表 1 覆盖 S=1.0/1.5/2.2/2.5/3.0；S=3.5/4.0/4.5/5.0 数据用于边界验证（C2 在 S≤4.5 仍有效，S=5.0 进入物理饱和截断）。
- 结果按论文表 1 / 表 2 约定汇总，图表输出至 `paper_figs/`。

## 依赖与许可

- Python 3.10+，MuJoCo ≥ 3.0（pip 自动安装）。
- MIT License，见 [LICENSE](LICENSE)。

## 贡献

欢迎复现或扩展论文实验（新增刚度档位、轨迹、噪声设置），并按表 1 / 表 2 约定汇报结果。详见 [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md)。
