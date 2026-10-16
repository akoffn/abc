#!/bin/bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MUJOCO_GL=disable
CTRL=$1; S=$2
if [ "$CTRL" = "C1" ]; then FIXED=40; else FIXED=0; fi
cd /root/opencr-mujoco-main
CORE=$((RANDOM % 40))
taskset -c $CORE \
  env TRAJ=8 FIXED_GAIN=$FIXED S_TEST=$S LAMBDA=0.05 OBS_NOISE_MM=0.0 NOISE_SEED=42 \
      /root/opencr_env/bin/python /tmp/traj_run.py \
  > "logs/clean/${CTRL}_S${S}.log" 2>&1
