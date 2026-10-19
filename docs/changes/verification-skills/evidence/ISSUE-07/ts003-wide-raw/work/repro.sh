#!/usr/bin/env bash
# payout-service e807b06 合并前最便宜复现: 真 seed + 真导出 + 未改动的消费者.
# 两条链路都检查: 读文件应崩溃; 读 stdout 应静默给出 total:null.
# 任一预期不符, 本脚本非零退出.
set -uo pipefail
W=/tmp/orchestra-07/out/ts003-wide-work/head
CONS=/tmp/orchestra-07/orders-consumer/src/run.sh
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

cd "$W" || exit 2
uv run python -B db/seed.py >"$TMP/seed.out" 2>&1 || { cat "$TMP/seed.out"; exit 2; }
uv run python -B -c 'import amountlib,pathlib,sys; assert amountlib.VERSION=="2.4.0"; p=pathlib.Path(amountlib.__file__).resolve(); assert str(p).startswith("/tmp/orchestra-07/out/ts003-wide-work/head/"); print("amountlib", amountlib.VERSION, p)' || exit 2
uv run python -B scripts/dump_orders.py >"$TMP/stdout.json" 2>"$TMP/dump.err" || { cat "$TMP/dump.err"; exit 2; }

echo "=== 1) 消费者读导出文件 ==="
bash "$CONS" "$W/var/orders.export.json" >"$TMP/file.out" 2>"$TMP/file.err"
file_rc=$?
cat "$TMP/file.err"
echo "file_consumer_exit=$file_rc"
[ "$file_rc" -eq 1 ] || { echo "FAIL: 期望退出 1"; exit 1; }
grep -q "TypeError: rows is not iterable" "$TMP/file.err" || { echo "FAIL: 缺 TypeError"; exit 1; }
grep -q "ledger.js:6" "$TMP/file.err" || { echo "FAIL: 报错行不符"; exit 1; }

echo "=== 2) 消费者读导出脚本 stdout (裸数组, 旧字段名) ==="
bash "$CONS" "$TMP/stdout.json" >"$TMP/stdout.out" 2>"$TMP/stdout.err"
stdout_rc=$?
cat "$TMP/stdout.out"
echo "stdout_consumer_exit=$stdout_rc"
[ "$stdout_rc" -eq 0 ] || { echo "FAIL: 期望退出 0"; exit 1; }
grep -q '"total": null' "$TMP/stdout.out" || { echo "FAIL: 期望 total:null"; exit 1; }
grep -q '"missing": \[\]' "$TMP/stdout.out" || { echo "FAIL: 期望 missing:[]"; exit 1; }

echo "PASS: 文件消费者崩 (exit 1), stdout 消费者静默错账 (exit 0, total:null, missing:[])."
