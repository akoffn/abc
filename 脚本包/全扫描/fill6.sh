#!/bin/bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MUJOCO_GL=disable
SIG=$1
TAG="fill6_C1_S2.5_sig${SIG}"
cd /root/opencr-mujoco-main
CORE=$((RANDOM % 40))
taskset -c $CORE env TRAJ=8 FIXED_GAIN=40 S_TEST=2.5 LAMBDA=0.05 \
  OBS_NOISE_MM=$SIG NOISE_SEED=42 TAG="$TAG" \
  /root/opencr_env/bin/python /tmp/traj_run.py > "logs/fill6/${TAG}.log" 2>&1
