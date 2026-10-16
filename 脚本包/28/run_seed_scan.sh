#!/bin/bash
# 多 seed 重复性验证（S=2.2 / 2.5，G=40）
# 输出到 数据集/测试/seedscan/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(dirname "$SCRIPT_DIR")"
PROJ_DIR="$(dirname "$PKG_DIR")"

OUT="$PROJ_DIR/数据集/测试/seedscan"
mkdir -p "$OUT"

for S in 2.2 2.5; do
  for SEED in 42 43 44 45 46; do
    TAG="c1_8_S${S}_seed${SEED}"
    OUTDIR="$OUT" TRAJ=8 FIXED_GAIN=40 S_TEST=$S LAMBDA=0.05 \
      OBS_NOISE_MM=0.0 NOISE_SEED=$SEED \
      /root/opencr_env/bin/python "$SCRIPT_DIR/traj_run.py" > "$OUT/${TAG}.log" 2>&1
    echo "done $TAG"
  done
done
