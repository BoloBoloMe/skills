#!/usr/bin/env bash
# V1-perf 一次性测量脚本 (非正式 TC, 仅测量, 不改产品源码).
# 计时区: 从 fork/exec python3 之前到进程退出之后, 即整条 app.py export 进程端到端.
# 计时工具: bash 内建 date +%s%N (纳秒), 差值换算毫秒, 保留 3 位小数.
set -u
cd /tmp/orchestra-10/methods-green || exit 99

EV=docs/changes/vault/evidence/r1-ea94082/V1-perf
OUT=runtime/export.jsonl
CMD="python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data"

echo "== harness start: $(date -Is) =="
echo "harness cmd string (exact): $CMD"
echo "nproc=$(nproc)"
echo "loadavg at harness start: $(cat /proc/loadavg)"
echo

for i in 1 2 3 4 5; do
  la_before=$(cat /proc/loadavg)
  up_before=$(uptime)
  ts_before=$(date +%s%N)
  iso_before=$(date -Is)
  stdout=$($CMD 2>/tmp/v1perf_err.$$)
  rc=$?
  ts_after=$(date +%s%N)
  iso_after=$(date -Is)
  stderr=$(cat /tmp/v1perf_err.$$ 2>/dev/null)
  la_after=$(cat /proc/loadavg)
  dur_ms=$(awk -v a="$ts_before" -v b="$ts_after" 'BEGIN{printf "%.3f", (b-a)/1000000}')

  echo "--- run $i ---"
  echo "command: $CMD"
  echo "start_iso: $iso_before  start_ns: $ts_before"
  echo "end_iso:   $iso_after  end_ns: $ts_after"
  echo "duration_ms: $dur_ms"
  echo "exit_code: $rc"
  echo "stdout: $stdout"
  echo "stderr: ${stderr:-<empty>}"
  echo "loadavg_before: $la_before"
  echo "loadavg_after:  $la_after"
  echo "uptime_before: $up_before"

  # 工作量与正确性核对 (计时区之外, 只读)
  echo "out_bytes: $(wc -c <"$OUT")"
  echo "out_lines: $(wc -l <"$OUT")"
  echo "out_sha256: $(sha256sum "$OUT" | cut -d' ' -f1)"
  echo "out_first: $(head -1 "$OUT")"
  echo "out_last:  $(tail -1 "$OUT")"
  echo "out_mtime: $(date -Is -r "$OUT")"
  echo
  sleep 0.3
done

rm -f /tmp/v1perf_err.$$
echo "== harness end: $(date -Is)  loadavg: $(cat /proc/loadavg) =="
