#!/bin/bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MUJOCO_GL=disable
MODE=$1; S=$2; SIG=$3
FIXED=0; [ "$MODE" = "C1" ] && FIXED=40
TAG="fill4_${MODE}_S${S}_sig${SIG}"
cd /root/opencr-mujoco-main
CORE=$((RANDOM % 40))
taskset -c $CORE env TRAJ=8 FIXED_GAIN=$FIXED S_TEST=$S LAMBDA=0.05 \
  OBS_NOISE_MM=$SIG NOISE_SEED=42 TAG="$TAG" \
  /root/opencr_env/bin/python /tmp/traj_run.py > "logs/fill4/${TAG}.log" 2>&1
