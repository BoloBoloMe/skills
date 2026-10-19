#!/usr/bin/env bash
# 独立验收运行脚本 (只读产品, 输出写入本证据目录)
set -u
cd "$(dirname "$0")/../../../../.." || exit 9
OUT=docs/changes/tool-cli/evidence/bb25738-round1/ac-cases
run_case() {
  local id="$1"; shift
  local cmd="$*"
  echo "===== $id ====="
  echo "CMD: $cmd"
  "$@" > "$OUT/$id.stdout" 2> "$OUT/$id.stderr"
  local rc=$?
  echo "EXIT: $rc"
  echo "STDOUT_BEGIN"
  cat "$OUT/$id.stdout"
  echo "STDOUT_END"
  echo "STDERR_BEGIN"
  cat "$OUT/$id.stderr"
  echo "STDERR_END"
  echo
}
run_case AC-001-1 python3 tool.py greet --name Ada
run_case AC-001-2 python3 tool.py greet --name Ada --shout
run_case AC-001-3 python3 tool.py greet --name Ada --sep '; '
run_case AC-001-4 python3 tool.py greet
run_case AC-002-1 python3 tool.py count --file notes.txt
run_case AC-002-2 python3 tool.py count --file notes.txt --chars
run_case AC-002-3 python3 tool.py count --file empty.txt
run_case AC-002-4 python3 tool.py count --file missing.txt
run_case AC-003-1 python3 tool.py export --name Ada
run_case AC-003-2 python3 tool.py export --name Ada --pretty
run_case AC-003-3 python3 tool.py export --name Ada --format yaml
run_case AC-004-1 python3 tool.py health --url http://127.0.0.1:18080/health
