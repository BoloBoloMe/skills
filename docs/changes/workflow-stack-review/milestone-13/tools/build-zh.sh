#!/bin/bash
# 构建期汉化流水线 (在 /tmp/cc-build 内验证用). 用法: ./build-zh.sh [工作目录]
# 1. 克隆指定 tag (缓存复用)  2. npm ci  3. 模板+.ts+.绑定字面量替换  4. ng build
set -euo pipefail

TAG="${CC_TAG:-vis-2.9.1}"
ROOT="${1:-/tmp/cc-build/e2e}"
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$ROOT/src"
VIS="$SRC/visualization"

mkdir -p "$ROOT"
if [ ! -d "$SRC/.git" ]; then
    git clone --depth 1 --branch "$TAG" https://github.com/MaibornWolff/codecharta "$SRC"
fi
cd "$VIS"
if [ ! -d node_modules ]; then
    npm ci
fi

# 汉化: 先恢复上游原样 (保证可重放)
python3 "$HERE/localize.py" --restore
# 在原始模板上先体检词表: 未使用的词条 = 上游改了文案, 需要人工跟进
python3 "$HERE/localize.py" --check || echo "WARN: 词表里有上游已不存在的词条, 见上面列表"
python3 "$HERE/localize.py" --apply
CC_TS_DICT="$HERE/../i18n/zh-ts.txt" CC_TS_STAT="$ROOT/ts-apply-report.json" \
    python3 "$HERE/localize_ts.py" --apply
CC_TS_DICT="$HERE/../i18n/zh-lit.txt" CC_TS_STAT="$ROOT/lit-apply-report.json" \
    python3 "$HERE/localize_ts.py" --apply --allow-any

npm run build
echo "产物: $VIS/dist/bundler/browser"
