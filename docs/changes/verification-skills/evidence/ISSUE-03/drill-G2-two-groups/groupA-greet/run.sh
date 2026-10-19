#!/usr/bin/env bash
# 组 A 验收实际执行脚本 (在项目根目录调用)
# 用法: bash run.sh <tag> <命令...>
set -u
tag="$1"; shift
proj="/tmp/orchestra-03/green-two-groups"
out="$tag.stdout.bin"; err="$tag.stderr.bin"
start=$(date +%s.%N)
( cd "$proj" && "$@" ) >"$out" 2>"$err"
code=$?
end=$(date +%s.%N)
{
  echo "== 场景: $tag"
  echo "== 时间戳(开始): $(date -d "@${start}" -Iseconds 2>/dev/null || echo unknown)"
  echo "== 工作目录: $proj"
  echo "== 完整命令: $*"
  echo "== 解释器: $(cd "$proj" && python3 -V 2>&1)"
  echo "== 退出码: $code"
  echo "== 墙钟耗时(秒): $(echo "$end - $start" | bc 2>/dev/null || echo n/a)"
  echo "== stdout 长度(字节): $(wc -c <"$out")"
  echo "== stderr 长度(字节): $(wc -c <"$err")"
  echo "== stdout 原始字节 (od -c):"
  od -c "$out"
  echo "== stdout python3 repr:"
  python3 -c 'import sys;print(repr(open(sys.argv[1],"rb").read()))' "$out"
  echo "== stderr 原始字节 (od -c):"
  od -c "$err"
  echo "== stderr python3 repr:"
  python3 -c 'import sys;print(repr(open(sys.argv[1],"rb").read()))' "$err"
  echo "== 结束"
} >"$tag.log"
rm -f "$out" "$err"
