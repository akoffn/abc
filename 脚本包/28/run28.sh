#!/bin/bash
# 用法:
#   run28.sh S SIG G LAM               # 默认输出到 数据集/28/results
#   run28.sh S SIG G LAM --test        # 输出到 数据集/28/测试结果
#   run28.sh S SIG G LAM --out DIR     # 指定输出目录
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MUJOCO_GL=disable

S=$1; SIG=$2; G=$3; LAM=$4
shift 4

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(dirname "$SCRIPT_DIR")"
PROJ_DIR="$(dirname "$PKG_DIR")"

# 默认输出
OUT_DATA="$PROJ_DIR/数据集/28"
OUT_SUB="results"

# 解析可选参数
while [ $# -gt 0 ]; do
  case "$1" in
    --test)  OUT_SUB="测试结果/results" ;;
    --out)   OUT_DATA="$2"; OUT_SUB=""; shift ;;
    *)       echo "未知参数: $1"; exit 1 ;;
  esac
  shift
done

if [ -n "$OUT_SUB" ]; then
  OUT_RESULTS="$OUT_DATA/$OUT_SUB"
  OUT_LOGS="$OUT_DATA/$(dirname "$OUT_SUB")/logs"
else
  OUT_RESULTS="$OUT_DATA"
  OUT_LOGS="$OUT_DATA/../logs"
fi
mkdir -p "$OUT_RESULTS" "$OUT_LOGS"

TRAJ_PY="$SCRIPT_DIR/traj_run.py"

if [ -x "/root/opencr_env/bin/python" ]; then
  PYTHON=/root/opencr_env/bin/python
else
  PYTHON=$(command -v python3)
fi

NCORE=$(nproc)
CORE=$((RANDOM % NCORE))

echo "[run28] S=$S SIG=$SIG G=$G LAM=$LAM"
echo "[run28] OUT_RESULTS=$OUT_RESULTS"
echo "[run28] OUT_LOGS=$OUT_LOGS"

cd "$PROJ_DIR"
taskset -c $CORE \
  env TRAJ=8 FIXED_GAIN=$G S_TEST=$S LAMBDA=$LAM OBS_NOISE_MM=$SIG NOISE_SEED=42 \
      OUTDIR="$OUT_RESULTS" \
  "$PYTHON" "$TRAJ_PY" > "$OUT_LOGS/S${S}_sig${SIG}_G${G}_lam${LAM}.log" 2>&1
