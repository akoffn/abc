#!/bin/bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MUJOCO_GL=disable
MODE=$1; TASK=$2; TRAJ=$3; S=$4; SIG=$5; G=$6

case "$TASK" in
  stiffness) TASKN="刚度扫描" ;;
  noise)     TASKN="噪声扫描" ;;
  *) echo "BAD TASK=$TASK"; exit 1 ;;
esac
case "$TRAJ" in
  8)      TRAJN="8字" ;;
  circle) TRAJN="圆形" ;;
  *) echo "BAD TRAJ=$TRAJ"; exit 1 ;;
esac

DIR="${MODE}/${TASKN}_${TRAJN}"
TAG="${MODE}_${TASK}_${TRAJN}_S${S}_sig${SIG}"
cd /root/opencr-mujoco-main
CORE=$((RANDOM % 40))
MODE=$MODE TASK=$TASK S_TEST=$S OBS_NOISE_MM=$SIG FIXED_GAIN=$G \
  NOISE_SEED=42 LAMBDA=0.05 TAG=$TAG TRAJ=$TRAJ OUT_DIR=$DIR \
  taskset -c $CORE /root/opencr_env/bin/python experiments/run.py > /tmp/log_${TAG}.log 2>&1
