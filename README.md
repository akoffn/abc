# Condition-Number-Triggered Gain Scheduling for Inverse Kinematics Control of Tendon-Driven Continuum Robots

Repository for the paper. OpenCR-MuJoCo is used as the evaluation platform
(backbone discretized into a rigid-link chain with elastic joints, tendons
actuated by MuJoCo's native tendon model, calibrated against SoRoSim
Cosserat-rod solutions).

## TL;DR

C2 uses the Jacobian condition number cond_J to trigger online gain reduction
(40→20), reducing tracking error in the high-stiffness degraded region by
42%–71% (Table 1), zeroing the saturation rate, with no accuracy loss at low
stiffness.

## Result figure

<p align="center">
  <img src="paper_figs/fig2_C1_vs_C2.png" width="70%" alt="C1 vs C2: error vs stiffness"/>
</p>

## Abstract

Task-space inverse-kinematics (IK) controllers for tendon-driven continuum
robots (TDCRs) degrade under high-stiffness conditions. This paper addresses
the degradation of the native controller (C1) with a gain-scheduling strategy
C2 based on the Jacobian condition number cond_J. Experiments show that the
fraction of time the 20-step sliding-window mean of cond_J exceeds the
threshold (frac) rises from 0% at S≤1.5 to 28.06%/35.41% at S=2.2/2.5, and
stays above 20% for S=2.2–3.0, making it a viable online regime indicator. C2
lowers the gain (40→20) when cond_J is high and restores it when low. Across
five stiffness levels, C2 reduces the degraded-region error by 42%–71%,
zeroes the saturation rate, and incurs no extra accuracy loss at low
stiffness. C2 effectively mitigates the gain-mismatch region S≤2.5; at S≥5.0
the system enters physical saturation clipping (C2's saturation rate also
rises markedly), beyond the algorithm's controllable range — which defines
C2's applicability boundary.

**Keywords:** tendon-driven continuum robot; inverse kinematics; gain
scheduling; Jacobian condition number; robust control; adaptive gain

## Method (4 sentences)

- **C1 (baseline):** fixed-gain (GAIN=40) task-space IK controller;
  degrades at high stiffness, reaching 18.86 mm error and 23.85% saturation
  at S=2.5.
- **Observation:** frac, the fraction of time the 20-step sliding-window
  mean of cond_J exceeds 160, rises from 0% at S≤1.5 to 28.06%/35.41% at
  S=2.2/2.5, serving as an online regime indicator.
- **C2:** lowers the gain (40→20) when cond_J is high and restores it when
  low; switching band C_up=160 / C_down=70, asymmetric ramping (5 steps down,
  50 steps up).
- **Results:** at S=2.2 error drops 8.37→4.82 mm (42.4%); at S=2.5 error
  drops 18.86→5.41 mm (71.3%); C2 saturation is 0% throughout; at S=5.0 C2
  error rises to 54.95 mm with 39.08% saturation — physical saturation
  clipping, beyond the algorithm's controllable range.

## Quick start (reproducing the paper)

> **Runtime note:** the scripts resolve paths relative to their own
> locations and run in any Linux environment. On Windows, simply keep the
> repository at a path without non-ASCII characters.

```bash
pip install -r requirements.txt

python 脚本包/28评估脚本/表1.py                  # Table 1: cond_J trigger validity + C1/C2 comparison
python 脚本包/28评估脚本/C2泛化_圆形噪声.py       # Table 2: generalization data
python 脚本包/控制器阈值论证脚本.py               # Figure 2: threshold-margin plot
python 脚本包/28评估脚本/C2泛化_圆形噪声_画图.py  # Figure 4: generalization plot
python 脚本包/全扫描/plot_all.py                 # Data source check for Figs. 1/3 (F1_8shape/F1_circle)
```

## Reproducing the paper

| Item | Content | Command |
|---|---|---|
| Table 1 | Core table (S=1.0/1.5/2.2/2.5/3.0; trigger fraction, C1/Fix20/C2 error and saturation) | `python 脚本包/28评估脚本/表1.py` |
| Table 2 | Generalization (figure-8/circle × noiseless/noisy; 71%–83% reduction, broader scope than Table 1) | `python 脚本包/28评估脚本/C2泛化_圆形噪声.py` |
| Figure 1 | C1 stiffness sweep (err vs S, with sat%) | Pre-rendered: `paper_figs/fig1_S_err.png` (plotting script not shipped) |
| Figure 2 | Threshold-margin plot (normal vs degraded cond_J distributions) | `python 脚本包/控制器阈值论证脚本.py` |
| Figure 3 | C1 vs C2 curves (err vs S, three-region annotation) | Pre-rendered: `paper_figs/fig2_C1_vs_C2.png` (plotting script not shipped) |
| Figure 4 | Generalization (circle trajectory + noise) | `python 脚本包/28评估脚本/C2泛化_圆形噪声_画图.py` |

> Note: `python 脚本包/全扫描/plot_all.py` produces overview figures
> `F1_8shape` / `F1_circle` (stiffness + noise panels, C1/C2 curves) for
> cross-checking the data behind Figures 1/3.

## Data

- `数据集/`: stiffness and noise sweeps for C1 / C2 / Fix20 as npz files
  (figure-8 and circle trajectories; S ∈ {0.5…5.0}, σ levels).
- Table 1 covers S=1.0/1.5/2.2/2.5/3.0; S=3.5/4.0/4.5/5.0 data support the
  boundary analysis (C2 remains effective at S≤4.5; S=5.0 enters physical
  saturation clipping).
- Results follow the Table 1 / Table 2 conventions; figures are written to
  `paper_figs/`.

## Dependencies and license

- Python 3.10+, MuJoCo ≥ 3.0 (installed automatically from pip).
- MIT License — see [LICENSE](LICENSE).

## Contributing

Contributions that reproduce or extend the paper's experiments (new stiffness
levels, trajectories, or noise settings) are welcome; please report results
using the Table 1 / Table 2 conventions. See
[.github/CONTRIBUTING.md](.github/CONTRIBUTING.md).
