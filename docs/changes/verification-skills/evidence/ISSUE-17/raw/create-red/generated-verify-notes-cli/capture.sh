#!/usr/bin/env bash
# 跑一条验证命令, 把命令, 退出码, stdout/stderr 原样落成证据.
# 用法: capture.sh <label> -- <命令...>
# 依赖环境变量 EVIDENCE (证据目录), 由调用者创建.
set -uo pipefail

if [ $# -lt 3 ] || [ "$2" != "--" ]; then
  echo "usage: capture.sh <label> -- <command...>" >&2
  exit 2
fi
label=$1
shift 2

if [ -z "${EVIDENCE:-}" ] || [ ! -d "$EVIDENCE" ]; then
  echo "capture.sh: EVIDENCE 未设置或不是目录" >&2
  exit 2
fi

log="$EVIDENCE/$label.log"
tmp=$(mktemp)
"$@" >"$tmp" 2>&1
rc=$?

{
  printf '# label: %s\n' "$label"
  printf '# cwd: %s\n' "$PWD"
  printf '# cmd: %s\n' "$*"
  printf 'exit=%d\n' "$rc"
  printf -- '--- output ---\n'
  cat "$tmp"
} | tee "$log"

rm -f "$tmp"
exit "$rc"
