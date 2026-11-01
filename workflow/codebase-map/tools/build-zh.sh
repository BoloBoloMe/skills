#!/bin/bash
# CodeCharta 前端汉化构建流水线 (milestone-21, 依据 m13 D013-D016/D021/D023/D024/D030)
#
# 用法: build-zh.sh [选项]
#   --tag TAG        上游可视化版本, 钉死 vis-2.9.1 (升级时人工改, 见 README)
#   --cache DIR      缓存根, 默认 ~/.agents/codebase-map/cache (上游克隆/依赖/报告都在这, 不入仓库)
#   --skip-smoke     只构建不冒烟 (调试用, 正常不要用)
#
# 步骤: 克隆钉死 tag (换 tag 整体替换缓存, D030) -> npm ci -> 先还原再三通道替换 (幂等, D013)
#       -> npm run build -> 渲染冒烟 (D014, 失败即构建失败) -> 汇报未使用词条与未命中统计.
set -euo pipefail

CC_TAG="vis-2.9.1"
CC_CACHE_ROOT="${CC_CACHE_ROOT:-$HOME/.agents/codebase-map/cache}"
SKIP_SMOKE=0
while [ $# -gt 0 ]; do
    case "$1" in
        --tag) CC_TAG="$2"; shift 2 ;;
        --cache) CC_CACHE_ROOT="$2"; shift 2 ;;
        --skip-smoke) SKIP_SMOKE=1; shift ;;
        *) echo "未知参数: $1" >&2; exit 2 ;;
    esac
done

HERE="$(cd "$(dirname "$0")" && pwd)"
I18N="$(cd "$HERE/../i18n" && pwd)"
SRC="$CC_CACHE_ROOT/src"
VIS="$SRC/visualization"
APP="$VIS/app"
DIST="$VIS/dist/bundler/browser"
RUN="$CC_CACHE_ROOT/run-latest"
STAMP="$CC_CACHE_ROOT/src-tag.txt"
T0=$(date +%s)

mkdir -p "$RUN"

echo "== 1/6 克隆上游 (tag: $CC_TAG) =="
if [ ! -d "$SRC/.git" ] || [ "$(cat "$STAMP" 2>/dev/null)" != "$CC_TAG" ]; then
    echo "缓存不存在或 tag 变更, 整体替换 $SRC (D030: 不叠加)"
    rm -rf "$SRC"
    git clone --depth 1 --branch "$CC_TAG" https://github.com/MaibornWolff/codecharta "$SRC"
    echo "$CC_TAG" > "$STAMP"
else
    echo "复用现有克隆 ($SRC)"
fi

echo "== 2/6 npm ci =="
cd "$VIS"
if [ ! -d node_modules ]; then
    npm ci
else
    echo "node_modules 已在, 跳过 (升级 tag 会随整体替换重装)"
fi

echo "== 3/6 还原上游原文 (幂等前提) =="
git -C "$APP" checkout -- .

echo "== 4/6 三通道替换 =="
# 先 --check 打印未使用词条 (升级探针: 上游改了哪句) 与复核提示, 再 --apply.
# 注: 通道 B 的"同一字面量命中多次"是已知复核项 (见 README 已知坑), 不视为失败.
CC_ROOT="$APP" CC_DICT="$I18N/zh.txt" CC_REPORT="$RUN/stat-A.json" \
    python3 "$HERE/localize.py" --check || echo "WARN 通道 A check 有告警, 见上一行输出"
CC_ROOT="$APP" CC_DICT="$I18N/zh.txt" CC_REPORT="$RUN/stat-A.json" \
    python3 "$HERE/localize.py" --apply
CC_ROOT="$APP" CC_TS_DICT="$I18N/zh-ts.txt" CC_TS_STAT="$RUN/ts-apply-report.json" \
    python3 "$HERE/localize_ts.py" --check || echo "WARN 通道 B check 有告警 (多命中复核项), 见上一行输出"
CC_ROOT="$APP" CC_TS_DICT="$I18N/zh-ts.txt" CC_TS_STAT="$RUN/ts-apply-report.json" \
    python3 "$HERE/localize_ts.py" --apply
CC_ROOT="$APP" CC_TS_DICT="$I18N/zh-lit.txt" CC_TS_STAT="$RUN/lit-apply-report.json" \
    python3 "$HERE/localize_ts.py" --apply --allow-any

echo "== 5/6 npm run build =="
npm run build
T_BUILD=$(date +%s)

echo "== 6/6 渲染冒烟 (D014) =="
if [ "$SKIP_SMOKE" = "1" ]; then
    echo "跳过冒烟 (--skip-smoke)"
else
    CC_SMOKE_PYTHON="${CC_SMOKE_PYTHON:-python3}"
    $CC_SMOKE_PYTHON "$HERE/smoke.py" --dist "$DIST" --out "$RUN"
fi

echo "== 结果 =="
echo "tag: $CC_TAG"
echo "产物: $DIST ($(du -sh "$DIST" | cut -f1))"
echo "构建耗时: $((T_BUILD - T0))s (含克隆复用判断/npm ci 判断/替换); 端到端含冒烟: $(( $(date +%s) - T0 ))s"
echo "报告与截图: $RUN (stat-A.json / ts-apply-report.json / lit-apply-report.json / smoke.json / shot-*.png)"
echo "未使用词条: 见上方 --check 输出与 stat-A.json 的 dict_unused; 未命中: untranslated 计数"
