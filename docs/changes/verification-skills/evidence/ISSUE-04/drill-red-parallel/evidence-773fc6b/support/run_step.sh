#!/bin/bash
# 验收记录辅助: 每次调用留 .cmd.txt / .stdout.txt / .stderr.txt
EV="/tmp/orchestra-04/red-parallel/docs/changes/relay-board/evidence-773fc6b"
run_step() {
  local name="$1"; shift
  local base="$EV/$name"
  local start end t0 t1 rc
  start=$(date -Iseconds)
  t0=$(date +%s%N)
  "$@" >"$base.stdout.txt" 2>"$base.stderr.txt"
  rc=$?
  t1=$(date +%s%N)
  end=$(date -Iseconds)
  {
    echo "step: $name"
    echo "cwd: $(pwd)"
    echo "cmd: $*"
    printf 'command-line:'; printf ' %q' "$@"; echo
    echo "start: $start"
    echo "end: $end"
    echo "exit: $rc"
    echo "duration_ns: $((t1-t0))"
    echo "duration_ms: $(( (t1-t0)/1000000 ))"
  } >"$base.cmd.txt"
  echo "[$name] exit=$rc duration_ms=$(( (t1-t0)/1000000 ))"
  return $rc
}
