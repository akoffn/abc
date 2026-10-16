#!/bin/bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MUJOCO_GL=disable
TAG_ID=$1; TRAJ=$2; S=$3; SIG=$4
TAG="final_${TAG_ID}"
cd /root/opencr-mujoco-main
CORE=$((RANDOM % 40))
taskset -c $CORE \
  env TRAJ=$TRAJ FIXED_GAIN=0 S_TEST=$S LAMBDA=0.05 OBS_NOISE_MM=$SIG NOISE_SEED=42 \
      TAG="$TAG" \
  /root/opencr_env/bin/python /tmp/traj_run.py > "logs/final/${TAG}.log" 2>&1
