#!/usr/bin/env bash
# ISSUE-07 演练夹具的第二段: 在 setup-fixture.sh 建好的 payout-service 上
# 派生两个变体, 并自检关键行为. 只写 /tmp/orchestra-07/.
# 注意: 提交哈希含生成时间, 每次跑会不同; 证据文件里记录的是当次实际哈希.
set -euo pipefail

ROOT=/tmp/orchestra-07
APP="$ROOT/payout-service"
CONS="$ROOT/orders-consumer"
[ -d "$APP/.git" ] || { echo "先跑 setup-fixture.sh"; exit 2; }

# ---------- 变体一: 宽影响, 2 行改动但改了跨仓库共享线格式 ----------
WIDE="$ROOT/payout-service-wide"
rm -rf "$WIDE"
git clone -q "$APP" "$WIDE"
cd "$WIDE"
git config user.email drill@example.invalid
git config user.name "drill fixture"
python3 - <<'PY'
import pathlib

p = pathlib.Path("app/orders.py")
s = p.read_text()
assert '{"id": row[0], "amount":' in s
s = s.replace('{"id": row[0], "amount":', '{"id": row[0], "amount_value":')
p.write_text(s)

d = pathlib.Path("scripts/dump_orders.py")
s = d.read_text()
assert "json.dumps(rows," in s
s = s.replace(
    "json.dumps(rows, ensure_ascii=False, indent=2)",
    'json.dumps({"schema": "orders-export/2", "rows": rows}, ensure_ascii=False, indent=2)',
)
d.write_text(s)
PY
git add app/orders.py scripts/dump_orders.py
git commit -qm "导出线格式改为 orders-export/2, 金额字段改名 amount_value"
WIDE_COMMIT=$(git rev-parse HEAD)

# ---------- 变体二: 局限变更, 只动一个内部函数 ----------
LOCAL="$ROOT/payout-service-local"
rm -rf "$LOCAL"
git clone -q "$APP" "$LOCAL"
cd "$LOCAL"
git config user.email drill@example.invalid
git config user.name "drill fixture"
python3 - <<'PY'
import pathlib

p = pathlib.Path("app/clamp.py")
s = p.read_text()
assert "upper=99" in s
p.write_text(s.replace("upper=99", "upper=50"))
PY
git add app/clamp.py
git commit -qm "内部数量上限从 99 收到 50"
LOCAL_COMMIT=$(git rev-parse HEAD)

# ---------- 自检: 变体行为必须与演练时记录的一致 ----------
work="$ROOT/verify"
rm -rf "$work"
mkdir -p "$work"

run_case() {  # $1=源码目录 $2=输出目录
  cp -r "$1" "$2"
  ( cd "$2" && uv run --quiet python db/seed.py >/dev/null && uv run --quiet python scripts/dump_orders.py >/dev/null )
}

check() {  # $1=说明 $2=期望退出码 $3=命令...
  local label=$1 want=$2; shift 2
  local got=0
  "$@" >/dev/null 2>&1 || got=$?
  if [ "$got" -eq "$want" ]; then
    echo "PASS $label (exit $got)"
  else
    echo "FAIL $label (want exit $want, got $got)"; exit 1
  fi
}

run_case "$APP" "$work/head"
check "改动后现有消费者读新导出" 0 bash "$CONS/src/run.sh" "$work/head/var/orders.export.json"
run_case "$WIDE" "$work/wide"
check "宽影响变体的消费者崩掉" 1 bash "$CONS/src/run.sh" "$work/wide/var/orders.export.json"

grep -q '"amount_value"' "$work/wide/var/orders.export.json" \
  && echo "PASS 宽影响变体导出字段改名" \
  || { echo "FAIL 宽影响变体导出字段未改名"; exit 1; }
grep -q '"schema": "orders-export/2"' "$work/wide/var/orders.export.json" \
  && echo "PASS 宽影响变体导出外层加 schema" \
  || { echo "FAIL 宽影响变体导出外层未加 schema"; exit 1; }
grep -q 'upper=50' "$LOCAL/app/clamp.py" \
  && echo "PASS 局限变体上限改为 50" \
  || { echo "FAIL 局限变体未改上限"; exit 1; }

cat >> "$ROOT/fixture-facts.txt" <<EOF
payout-service 宽影响变体: $WIDE_COMMIT
payout-service 局限变体: $LOCAL_COMMIT
EOF
tail -2 "$ROOT/fixture-facts.txt"
