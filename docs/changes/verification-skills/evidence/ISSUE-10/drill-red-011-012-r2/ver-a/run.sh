#!/bin/bash
# ver-a 取证脚本: 顺序执行, 逐条记录 时间/命令/退出码/stdout/stderr
LOG="docs/changes/accounts/evidence/round-1-bc435db-20261019T162305Z/ver-a/commands.log"
run() {
  local label="$1"; shift
  local cmd="$*"
  echo "### [$label] START $(date -Is)" >> "$LOG"
  echo "CMD: $cmd" >> "$LOG"
  local out err rc
  out=$(mktemp); err=$(mktemp)
  "$@" > "$out" 2> "$err"; rc=$?
  echo "EXIT: $rc" >> "$LOG"
  echo "STDOUT:" >> "$LOG"; cat -A "$out" | sed 's/\$$//' >> "$LOG"
  echo "STDOUT-RAW:" >> "$LOG"; cat "$out" >> "$LOG"
  echo "STDERR:" >> "$LOG"; cat "$err" >> "$LOG"
  if [ -s "$err" ]; then echo "(stderr bytes: $(wc -c < "$err"))" >> "$LOG"; else echo "(stderr empty)" >> "$LOG"; fi
  echo "### [$label] END $(date -Is)" >> "$LOG"
  echo "" >> "$LOG"
  LAST_RC=$rc; LAST_OUT=$(cat "$out")
  rm -f "$out" "$err"
}
