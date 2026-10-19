#!/usr/bin/env bash
# 最便宜的复现: 在临时副本里跑真实入口, 不写两个仓库.
# 用法: bash repro.sh   需要 git, tar, uv, node.
set -u
SRC=/tmp/orchestra-07/drill-ts003-gap
CONS=/tmp/orchestra-07/orders-consumer
T=$(mktemp -d)
git -C "$SRC" archive HEAD | tar -x -C "$T"
(
  cd "$T" || exit 1
  uv run --no-project python db/seed.py >/dev/null
  uv run --no-project python scripts/dump_orders.py >/dev/null
) || exit 1
echo "== 导出文件 =="
cat "$T/var/orders.export.json"; echo

echo "== 现版消费者读新导出 =="
node "$CONS/src/ledger.js" "$T/var/orders.export.json"
echo "consumer exit=$?"

echo "== 只解包 .rows, 仍读旧键 amount 的消费者 =="
cat > "$T/peek.mjs" <<'JS'
import fs from "node:fs";
const payload = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const rows = payload.rows ?? payload;
let total = 0; const missing = [];
for (const row of rows) {
  if (row.amount === null) { missing.push(row.id); continue; }
  total += Number(row.amount);
}
console.log(JSON.stringify({ total, missing }));
JS
node "$T/peek.mjs" "$T/var/orders.export.json"
echo "peek exit=$?"
rm -rf "$T"
