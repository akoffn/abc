#!/bin/bash
# 用法:
#   run_all.sh                # 默认输出到 数据集/28/results
#   run_all.sh --test         # 输出到 数据集/28/测试结果
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JOBS="$SCRIPT_DIR/jobs28.txt"

MODE=""
[ "$1" = "--test" ] && MODE="--test"

[ -f "$JOBS" ] || { echo "找不到 jobs28.txt"; exit 1; }

NCORE=$(nproc)
echo "核数: $NCORE   模式: ${MODE:-正式}   任务数: $(wc -l < "$JOBS")"

while read S SIG G LAM; do
  bash "$SCRIPT_DIR/run28.sh" $S $SIG $G $LAM $MODE
done < "$JOBS"

echo "完成。"
