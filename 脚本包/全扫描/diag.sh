#!/bin/bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MUJOCO_GL=disable
S=$1
TAG="diagC1_S${S}"
cd /root/opencr-mujoco-main
CORE=$((RANDOM % 40))
taskset -c $CORE env TRAJ=8 FIXED_GAIN=40 S_TEST=$S LAMBDA=0.05 \
  OBS_NOISE_MM=0.0 NOISE_SEED=42 TAG="$TAG" \
  /root/opencr_env/bin/python /tmp/traj_run.py > "logs/diag/${TAG}.log" 2>&1
