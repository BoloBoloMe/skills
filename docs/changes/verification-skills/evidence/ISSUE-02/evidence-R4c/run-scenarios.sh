#!/usr/bin/env bash
# 本轮验收实跑脚本. 在仓库根目录执行, 只写本证据目录.
# 用法: bash docs/changes/tool-cli/evidence-v2-7f360da/run-scenarios.sh
set -uo pipefail

EV="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EV/../../../.." && pwd)"
cd "$ROOT"

run_case() {
  local id="$1"; shift
  local dir="$EV/$id"
  mkdir -p "$dir"
  {
    printf '$'
    printf ' %q' "$@"
    printf '\n'
  } > "$dir/command.txt"
  "$@" > "$dir/stdout.txt" 2> "$dir/stderr.txt"
  local rc=$?
  printf '%s\n' "$rc" > "$dir/exit_code.txt"
  printf '%s\texit=%s\tstdout=%s\tstderr=%s\n' \
    "$id" "$rc" \
    "$(od -An -c "$dir/stdout.txt" | tr -s ' ' | tr '\n' ' ')" \
    "$(od -An -c "$dir/stderr.txt" | tr -s ' ' | tr '\n' ' ')" \
    >> "$EV/summary.tsv"
}

: > "$EV/summary.tsv"

run_case AC-001-1 python3 tool.py greet --name Ada
run_case AC-001-2 python3 tool.py greet --name Ada --shout
run_case AC-001-3 python3 tool.py greet --name Ada --sep '; '
run_case AC-001-4 python3 tool.py greet
run_case AC-002-2 python3 tool.py count --file notes.txt --chars
run_case AC-002-3 python3 tool.py count --file empty.txt
run_case AC-002-4 python3 tool.py count --file missing.txt
run_case AC-003-1 python3 tool.py export --name Ada
run_case AC-003-3 python3 tool.py export --name Ada --format yaml

{
  echo "# 环境与前提"
  echo
  echo "- 时间(UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "- 提交: $(git rev-parse HEAD)"
  echo "- 分支: $(git branch --show-current)"
  echo "- python3: $(python3 -V 2>&1)"
  echo "- 工作区(实跑前): git status --porcelain 输出为"
  git status --porcelain=v1 | sed 's/^/  | /'
} > "$EV/environment.txt"
