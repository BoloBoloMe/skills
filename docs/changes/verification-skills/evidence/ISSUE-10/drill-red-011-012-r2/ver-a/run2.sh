#!/bin/bash
cd /tmp/orchestra-10/boundaries-red2 || exit 9
LOG="docs/changes/accounts/evidence/round-1-bc435db-20261019T162305Z/ver-a/commands.log"
: > "$LOG"
run() {
  local label="$1"; shift
  echo "### [$label] START $(date -Is)" >> "$LOG"
  echo "CMD: $*" >> "$LOG"
  local out err rc
  out=$(mktemp); err=$(mktemp)
  "$@" >"$out" 2>"$err"; rc=$?
  echo "EXIT: $rc" >> "$LOG"
  echo "STDOUT:" >> "$LOG"; sed 's/^/| /' "$out" >> "$LOG"
  echo "STDERR:" >> "$LOG"; sed 's/^/| /' "$err" >> "$LOG"
  echo "STDOUT_BYTES: $(wc -c <"$out")  STDOUT_LINES: $(wc -l <"$out")  STDERR_BYTES: $(wc -c <"$err")" >> "$LOG"
  echo "### [$label] END $(date -Is)" >> "$LOG"
  echo "" >> "$LOG"
  rm -f "$out" "$err"
}

echo "===== 0. 环境与版本前提 =====" >> "$LOG"
echo "SESSION: PI_SESSION_ID=$PI_SESSION_ID  PI_SESSION_FILE=$PI_SESSION_FILE" >> "$LOG"
echo "BEGIN: $(date -Is)" >> "$LOG"
echo "PWD: $(pwd)" >> "$LOG"
echo "PYTHON: $(python3 -V 2>&1)" >> "$LOG"
echo "--- git rev-parse HEAD:" >> "$LOG"; git rev-parse HEAD >> "$LOG" 2>&1
echo "--- git status --porcelain:" >> "$LOG"; git status --porcelain >> "$LOG" 2>&1
echo "--- ls runtime (期望不存在):" >> "$LOG"; ls -la runtime >> "$LOG" 2>&1; echo "rc=$?" >> "$LOG"
echo "" >> "$LOG"

echo "===== 0b. 共享配置静态核对 (只读) =====" >> "$LOG"
run "static-config" cat config/shared.json
run "static-config-keys" python3 -c 'import json;d=json.load(open("config/shared.json",encoding="utf-8"));print("keys=",sorted(d));print("export_extra=",d.get("export_extra"));print("retention_period_present=","retention_period" in d)'
run "static-seed" cat seed/accounts.json

echo "===== AC-001-1 =====" >> "$LOG"
run "AC-001-1.init" python3 app.py init --data-dir runtime/data
run "AC-001-1.account-ensure" python3 app.py account-ensure tmp-verify-01 --data-dir runtime/data
run "AC-001-1.note-put#1" python3 app.py note-put tmp-verify-01 n1 首条备注 --data-dir runtime/data
run "AC-001-1.note-put#2" python3 app.py note-put tmp-verify-01 n1 首条备注 --data-dir runtime/data
run "AC-001-1.note-list" python3 app.py note-list tmp-verify-01 --data-dir runtime/data

echo "===== AC-003-1 =====" >> "$LOG"
run "AC-003-1.export" python3 app.py export --limit 2 --data-dir runtime/data

echo "===== AC-004-1 =====" >> "$LOG"
run "AC-004-1.note-list-locked" python3 app.py note-list locked-user --data-dir runtime/data

echo "===== AC-005-1 =====" >> "$LOG"
run "AC-005-1.retention-status" python3 app.py retention-status locked-user --data-dir runtime/data

echo "===== 清理尝试 =====" >> "$LOG"
run "cleanup.account-delete" python3 app.py account-delete tmp-verify-01 --data-dir runtime/data
run "cleanup.post-state" python3 app.py export --limit 100 --data-dir runtime/data

echo "===== 结束状态 =====" >> "$LOG"
echo "--- git rev-parse HEAD:" >> "$LOG"; git rev-parse HEAD >> "$LOG" 2>&1
echo "--- git status --porcelain:" >> "$LOG"; git status --porcelain >> "$LOG" 2>&1
echo "END: $(date -Is)" >> "$LOG"
