#!/bin/bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MUJOCO_GL=disable
S=$1; SIG=$2; G=$3; LAM=$4
D="/root/opencr-mujoco-main/数据集/28"
CORE=$((RANDOM % 64))
cd /root/opencr-mujoco-main
taskset -c $CORE \
  env TRAJ=8 FIXED_GAIN=$G S_TEST=$S LAMBDA=$LAM OBS_NOISE_MM=$SIG NOISE_SEED=42 \
      OUTDIR="$D/results" \
  /root/opencr_env/bin/python /tmp/traj_run.py > "$D/logs/S${S}_sig${SIG}_G${G}_lam${LAM}.log" 2>&1
