# Condition-Number-Triggered Gain Scheduling for Inverse Kinematics Control of Tendon-Driven Continuum Robots

Code and data for the paper. OpenCR-MuJoCo is used as the evaluation platform
(backbone discretized into a rigid-link chain with elastic joints, tendons
actuated by MuJoCo's native tendon model, calibrated against SoRoSim
Cosserat-rod solutions).

> **Scope.** Everything here is simulation: a three-segment TDCR with six
> Clarke-space DOFs and nine tendon actuators tracking a figure-eight, at
> `dt = 0.001 s` with a 50 Hz controller, scored over `t ∈ (10, 20) s`
> (n = 499 steps). Gravity is disabled so that stiffness is the only quantity
> moving the numbers, and every run uses the single seed `SEED = 42`, so the
> tables reproduce exactly. There is no hardware experiment and no repeated-seed
> statistics.

## TL;DR

C2 reads the Jacobian condition number `cond_J` and, when its 20-step window
mean `cond_slide` runs high, moves the outer gain from 40 down to 20, restoring
it as the conditioning recovers. Over **S = 2.2–4.5** C2 cuts steady-state
error by **42%–88.5%** at **zero saturation** (Table 2). For **S ≤ 1.0** C2
returns exactly C1's 1.93 mm; the transition band costs at most ~1.3 mm, with a
single misfire at S = 1.5 costing 0.79 mm.

## Result figure

<p align="center">
  <img src="paper_figs/fig2_C1_vs_C2.png" width="70%" alt="Figure 3: C1 vs C2, mean error vs stiffness"/>
</p>

*Figure 3 of the paper: C1 against C2 over the full sweep S = 1.0–5.0.*

## Abstract

Task-space inverse kinematics (IK) for tendon-driven continuum robots (TDCR)
degrades two ways at once under high-stiffness contact: tracking error grows and
the actuator command clip engages. The damped least squares (DLS) core is left
as it is, and around it we place an external gain scheduler, C2, driven by the
Jacobian condition number `cond_J`. A 20-step window mean, `cond_slide`, exceeds
`C_up` on a fraction of steps that never falls as stiffness rises, holding 0% at
S = 1.0 and reaching 35.41% at S = 2.5, and the fraction stays monotone for
S ≤ 2.5; that is what makes `cond_slide` usable as an online flag. When
`cond_slide` runs high, C2 moves the outer gain from 40 down to 20 and restores
it as the conditioning recovers. Over S = 2.2–4.5, C2 cuts error by 42%–88.5% at
zero saturation, while below S = 1.0 C2 keeps C1's 1.93 mm (transition ≤ ~1.3 mm;
misfire 0.79 mm at S = 1.5). On a circular path with noise to σ = 5 mm, C2 holds
5.8–12.1 mm chatter-free, which is one trajectory under one noise model and
therefore a bounded check rather than evidence of generality. The envelope
defended here stops at S ≤ 4.5. At S = 5.0 the actuators saturate for physical
reasons and `cond_slide` can no longer distinguish gain mismatch from saturation.

**Keywords:** tendon-driven continuum robot; inverse kinematics; damped least
squares; gain scheduling; Jacobian condition number; variable stiffness
(identical to the paper's Index Terms).

## Method

- **C1 (baseline):** fixed-gain (`G = 40`) task-space IK controller over an
  unchanged DLS core (`λ = 0.05`, clip `v_max = 1.0`); it degrades at high
  stiffness, reaching 18.86 mm error and 23.85% saturation at S = 2.5.
- **Observation:** the trigger ratio — the fraction of scored steps on which the
  20-step window mean `cond_slide` exceeds `C_up = 160` — holds 0% at S = 1.0 and
  1.5, then rises to 28.06% / 35.41% at S = 2.2 / 2.5. It is monotone only up to
  S ≤ 2.5 and falls back to 25.61% at S = 3.0, which is why the trigger is used
  as a coarse regime flag rather than a calibrated measure.
- **C2:** lowers the gain (40 → 20) when `cond_slide` is high and restores it
  when low, with hysteresis band `C_up = 160` / `C_down = 70` and asymmetric
  ramping (−4.0 per step over 5 steps down, +0.4 per step over 50 steps up).
  Nothing inside the DLS solver is modified.
- **Results:** at S = 2.2 error drops 8.37 → 4.82 mm (42.4%); at S = 2.5,
  18.86 → 5.41 mm (71.3%); at S = 3.0, 39.40 → 6.49 mm (83.5%); at S = 4.5,
  66.87 → 7.66 mm (88.5%). C2 saturation stays at 0% for every S ≤ 4.5 (not
  "throughout": at S = 5.0 C2 reaches 54.95 mm with 39.08% saturation, where the
  plant itself is clipped and the algorithm is out of its controllable range).

## Quick start (reproducing the paper)

> **Runtime note:** the scripts resolve paths relative to their own locations
> and run in any Linux environment. On Windows, keep the repository at a path
> without non-ASCII characters.

```bash
pip install -r requirements.txt

python 脚本包/28评估脚本/表1.py                  # Table 1  (S = 1.0/1.5/2.2/2.5/3.0)
python 脚本包/控制器阈值论证脚本.py               # Figure 1 (threshold-margin plot)
python 脚本包/28评估脚本/C2泛化_圆形噪声.py       # Figure 4 data (circle path + noise)
python 脚本包/28评估脚本/C2泛化_圆形噪声_画图.py  # Figure 4 (generalization plot)
python 脚本包/全扫描/plot_all.py                 # overview panels used to cross-check Figs. 2/3
```

## Reproducing the paper

| Item | Content | Command / artefact |
|---|---|---|
| Table 1 | Core table, S = 1.0/1.5/2.2/2.5/3.0: trigger ratio, C1 / Fix20 / C2 error and saturation | `python 脚本包/28评估脚本/表1.py` (prints table + LaTeX, writes `数据集/28/analysis/table1_final.csv`) |
| Table 2 | **Extended stiffness scan over eight levels, S = 1.0–5.0: C1 vs C2 error, saturation, and relative reduction (0.0% → +88.5%, −40.9% at S = 1.5)** | No dedicated script is shipped. Recompute from `数据集/C1/刚度扫描_8字` and `数据集/C2/刚度扫描_8字` with the same convention as `表1.py` (20-step window mean, first 50 steps discarded as warm-up, `err_true.mean()`, `sat_flag.mean()`). Reference values: `paper_figs/tables/T12_c2_S_sweep.csv`, `数据集/28/analysis/` |
| Figure 1 | Percentile margins of the C1 `cond_slide` distribution used to set `C_up` / `C_down` (normal vs degraded, with safety margins) | `python 脚本包/控制器阈值论证脚本.py` → `paper_figs/fig3_threshold.pdf` / `.png` |
| Figure 2 | C1 stiffness sweep: mean error vs S, with the transition band and the unstable region shaded | Pre-rendered: `paper_figs/fig1_S_err.png` (plotting script not shipped) |
| Figure 3 | C1 vs C2 over the full sweep S = 1.0–5.0 | Pre-rendered: `paper_figs/fig2_C1_vs_C2.png` (plotting script not shipped) |
| Figure 4 | Extension: circular path at S = 2.5 vs observation noise σ | `python 脚本包/28评估脚本/C2泛化_圆形噪声_画图.py` → `paper_figs/fig4_c2_circle_noise.png` |

> Note: the file stems under `paper_figs/` follow the plotting order in which the
> figures were produced, **not** the numbering in the paper. `fig1_S_err` is
> Figure 2, `fig2_C1_vs_C2` is Figure 3, and `fig3_threshold` is Figure 1.
>
> Note: `python 脚本包/全扫描/plot_all.py` produces the overview panels
> `F1_8shape` / `F1_circle` (stiffness and noise panels, C1/C2 curves) used to
> cross-check the data behind Figures 2 and 3.

## Data

- `数据集/`: stiffness and noise sweeps for C1 / C2 / Fix20 as npz files
  (figure-8 and circle trajectories; S from 0.5 to 5.0, several σ levels).
- Table 1 covers S = 1.0/1.5/2.2/2.5/3.0. The extended levels
  S = 3.5/4.0/4.5/5.0 support the boundary analysis (C2 still holds at S ≤ 4.5;
  S = 5.0 is physical saturation clipping).
- Derived tables and figure sources: `数据集/28/analysis/`,
  `paper_figs/tables/`. Figures are written to `paper_figs/`.

## Scope and limitations

- **Simulation only.** No physical robot was used; there is no hardware
  validation.
- **Single seed, no error bars.** All reported numbers come from `SEED = 42`
  with n = 499 scored steps per run, so the tables reproduce exactly but carry
  no statistical spread.
- **Gravity is disabled**, so the sweeps isolate stiffness; results under
  gravity are not covered.
- **Thresholds are scale-bound.** `C_up = 160` / `C_down = 70` and the two gain
  levels are calibrated for this robot, this trajectory and this clip limit; a
  different platform means recalibration.
- **The noise check is bounded.** One extra trajectory (circle), one stiffness
  (S = 2.5), one noise model (additive Gaussian). It does not support claims
  about other paths, other stiffnesses, non-Gaussian noise, or S > 4.5.
- **Two gain levels only.** Continuous scheduling, multi-trajectory validation
  and hardware trials are left as future work.

## Dependencies and license

- Python 3.10+, MuJoCo ≥ 3.0 (installed automatically from pip).
- The repository is MIT licensed (see [LICENSE](LICENSE)). The bundled Franka
  assets under `assets/franka_assets/` come from MuJoCo Menagerie and are
  Apache-2.0 (see `assets/franka_assets/LICENSE.md`); that notice must be kept.

## Contributing

Contributions that reproduce or extend the paper's experiments (new stiffness
levels, trajectories, or noise settings) are welcome; please report results
using the Table 1 / Table 2 conventions defined above. See
[.github/CONTRIBUTING.md](.github/CONTRIBUTING.md).
