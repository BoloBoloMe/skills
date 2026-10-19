#!/usr/bin/env bash
# 本轮独立验收实跑脚本 (验收输出, 非产品代码)
# 目标提交: 7f360da1d0bdf923472919523760bd4c59eb8576
set -u
export PYTHONDONTWRITEBYTECODE=1   # 避免在工作区落下 __pycache__
cd "$(git rev-parse --show-toplevel)" || exit 99

run() {
  local id="$1"; shift
  echo "===== ${id} ====="
  echo "time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "cwd: $(pwd)"
  echo "cmd: $*"
  local out err rc
  out="$("$@" 2>docs/changes/tool-cli/evidence-7f360da/raw/.accept-stderr)"; rc=$?
  err="$(cat docs/changes/tool-cli/evidence-7f360da/raw/.accept-stderr)"
  echo "exit: ${rc}"
  echo "--- stdout ---"
  printf '%s' "${out}" | od -c | sed 's/^/  /'
  echo "--- stdout(直读) ---"
  printf '%s\n' "${out}"
  echo "--- stderr ---"
  printf '%s\n' "${err}"
  echo
}

run AC-001-1 python3 tool.py greet --name Ada
run AC-001-2 python3 tool.py greet --name Ada --shout
run AC-001-3 python3 tool.py greet --name Ada --sep '; '
run AC-001-4 python3 tool.py greet
run AC-002-2 python3 tool.py count --file notes.txt --chars
run AC-002-3 python3 tool.py count --file empty.txt
echo "===== AC-002-4 前置: missing.txt 是否存在 ====="
ls -l missing.txt 2>&1 | sed 's/^/  /'
echo "  test -e missing.txt -> $( [ -e missing.txt ] && echo EXISTS || echo ABSENT )"
echo
run AC-002-4 python3 tool.py count --file missing.txt
run AC-003-1 python3 tool.py export --name Ada
run AC-003-3 python3 tool.py export --name Ada --format yaml
echo "===== AC-003-2 (按指示不实跑, 本轮未执行) ====="
echo
echo "===== 结束 $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
