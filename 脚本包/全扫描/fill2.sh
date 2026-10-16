#!/bin/bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MUJOCO_GL=disable
TRAJ=$1; S=$2; SIG=$3
TAG="fill2_${TRAJ}_C2_S${S}_sig${SIG}"
cd /root/opencr-mujoco-main
CORE=$((RANDOM % 40))
taskset -c $CORE env TRAJ=$TRAJ FIXED_GAIN=0 S_TEST=$S LAMBDA=0.05 \
  OBS_NOISE_MM=$SIG NOISE_SEED=42 TAG="$TAG" \
  /root/opencr_env/bin/python /tmp/traj_run.py > "logs/fill2/${TAG}.log" 2>&1
