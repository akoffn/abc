#!/bin/bash
export OMP_NUM_THREADS=1 MUJOCO_GL=disable
FIXED=$1; TRAJ=$2; S=$3; SIG=$4; TASK=$5; OUTDIR=$6; TAG=$7
cd /root/opencr-mujoco-main
mkdir -p "$OUTDIR"
taskset -c $((RANDOM%40)) env \
  FIXED_GAIN=$FIXED TRAJ=$TRAJ S_TEST=$S OBS_NOISE_MM=$SIG TASK=$TASK \
  OUT_DIR="$OUTDIR" TAG="$TAG" \
  /root/opencr_env/bin/python experiments/run.py > "/tmp/${TAG}.log" 2>&1
echo "done $TAG"
