#!/bin/bash
# 一次性实验脚本 (milestone-23): 官方 codecharta-analysis:2.3.0 对目标 Java 库的实际成功配方 (2026-11-01 实测通过).
# 用法: run-analysis.sh <目标库绝对路径> <输出目录绝对路径> [镜像引用, 默认 2.3.0]
# 纪律: 源码只读挂载 (:ro), 输出写独立目录, 容器无网络, 用完即删 (--rm), rootless 需 --userns=keep-id.
# 历史: 最早版本 (无 keep-id/-nc, 官方管道合并) 已失败并废弃, 失败证据见
#   /tmp/m23-evidence/raw-logs/run-a-deps.log (首次: 分析成功但写盘 Permission denied, uid 映射见 logs/uid-map-verify.log)
#   /tmp/m23-evidence/raw-logs/run-b-merged.log (官方 unifiedparser|dependencyparser 管道: piped JSON 截断判无效)
# 本文件现内容 = 实际成功并产出全部数据的命令序列, 可直接复跑.
set -uo pipefail
TARGET="${1:?用法: run-analysis.sh <目标库> <输出目录> [镜像]}"
OUTDIR="${2:?缺输出目录}"
IMAGE="${3:-docker.io/codecharta/codecharta-analysis:2.3.0}"
LOGDIR="$(dirname "$0")/../logs"
mkdir -p "$OUTDIR"
stamp() { date -Is; }

echo "[$(stamp)] target=$TARGET outdir=$OUTDIR image=$IMAGE" | tee "$LOGDIR/analysis-run.log"

echo "[$(stamp)] [1/4] ccsh 版本 (注意: 自报串可能与镜像 tag 不一致, 核对以 digest 为准)" | tee -a "$LOGDIR/analysis-run.log"
podman run --rm --network=none "$IMAGE" ccsh --version 2>&1 | tee "$LOGDIR/ccsh-version.log"

echo "[$(stamp)] [2/4] Run A: 纯依赖图 (工具默认: 排除测试, gitignore 生效, 排除 build 目录); keep-id 使容器 uid 对齐宿主调用者, -nc 出未压缩 json" | tee -a "$LOGDIR/analysis-run.log"
podman run --rm --network=none --userns=keep-id \
  -v "$TARGET":/proj:ro \
  -v "$OUTDIR":/out \
  "$IMAGE" \
  ccsh dependencyparser /proj -o /out/deps-only.cc.json -nc 2>&1 | tr '\r' '\n' | grep -v "^[[:space:]]*[0-9]*% \[" | tee "$LOGDIR/run-a.trimmed.log"
# 注: 原始 stdout 的进度条流内嵌全部文件名枚举, 此处入库前已剔除; 完整原件不落仓库.

echo "[$(stamp)] [3/4] 指标: unifiedparser 单独出文件 (官方管道合并实测损坏, 不用管道)" | tee -a "$LOGDIR/analysis-run.log"
podman run --rm --network=none --userns=keep-id \
  -v "$TARGET":/proj:ro -v "$OUTDIR":/out \
  "$IMAGE" \
  ccsh unifiedparser /proj -nc -o /out/metrics.cc.json 2>&1 | tr '\r' '\n' | grep -v "^[[:space:]]*[0-9]*% \[" | tee "$LOGDIR/run-metrics.trimmed.log"

echo "[$(stamp)] [4/4] merge 合并依赖与指标" | tee -a "$LOGDIR/analysis-run.log"
podman run --rm --network=none --userns=keep-id \
  -v "$OUTDIR":/data \
  "$IMAGE" \
  ccsh merge /data/metrics.cc.json /data/deps-only.cc.json -o /data/merged.cc.json -nc 2>&1 | tr '\r' '\n' | grep -v "^[[:space:]]*[0-9]*% \[" | tee "$LOGDIR/run-merge.trimmed.log"

ls -la "$OUTDIR"
echo "[$(stamp)] 完成" | tee -a "$LOGDIR/analysis-run.log"
