// 假设只修外层 rows, 仍执行旧 ledger 的金额循环. 不改消费者.
import assert from "node:assert/strict";
import fs from "node:fs";

assert.equal(process.version, "v24.19.0", "重跑时若换 Node 版本, 必须重新核对运行环境");
const pkg = JSON.parse(fs.readFileSync("/tmp/orchestra-07/orders-consumer/package.json", "utf8"));
assert.equal(pkg.name, "orders-consumer");
assert.equal(pkg.version, "0.9.2");
assert.equal(pkg.type, "module");
const document = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
assert.equal(document.schema, "orders-export/2");
assert.ok(Array.isArray(document.rows));
assert.equal(document.rows.length, 3);
const rows = document.rows;
let total = 0;
const missing = [];
const steps = [];
for (const row of rows) {
  assert.equal(Object.hasOwn(row, "amount"), false);
  assert.equal(row.amount, undefined);
  assert.equal(row.amount === null, false);
  assert.ok(Number.isNaN(Number(row.amount)));
  if (row.amount === null) {
    missing.push(row.id);
    continue;
  }
  total += Number(row.amount);
  steps.push({id: row.id, amountIsUndefined: row.amount === undefined, totalIsNaN: Number.isNaN(total)});
}
assert.ok(Number.isNaN(total));
assert.deepEqual(missing, []);
const encoded = JSON.stringify({ total, missing }, null, 2);
assert.equal(encoded, '{\n  "total": null,\n  "missing": []\n}');
console.log(JSON.stringify({node: process.version, steps, internalTotalIsNaN: Number.isNaN(total), assertions: "PASS"}, null, 2));
console.log(encoded);
