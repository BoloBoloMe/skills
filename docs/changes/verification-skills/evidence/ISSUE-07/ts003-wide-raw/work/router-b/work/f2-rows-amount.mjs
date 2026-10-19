// F2 证明: 消费者先适配外层 (只遍历 rows), 但仍读 row.amount, 会发生什么.
// 判定错则以非零退出. 数据来自本任务 repo/ (HEAD) 的真实导出文件.
import fs from "node:fs";
import assert from "node:assert";

const EXPORT = process.argv[2];
const raw = JSON.parse(fs.readFileSync(EXPORT, "utf8"));

// 断言环境: 读的确实是 HEAD 的新格式文件
assert.deepStrictEqual(Object.keys(raw), ["schema", "rows"], "外层应是 {schema, rows}");
assert.strictEqual(raw.schema, "orders-export/2", "schema 应为 orders-export/2");

// 假设消费者已适配外层, 复用 ledger.js 原有的循环语义 (src/ledger.js:5-12):
// for (const row of rows) { if (row.amount === null) {...} total += Number(row.amount); }
const rows = raw.rows;
let total = 0;
const missing = [];
for (const row of rows) {
  if (row.amount === null) {
    missing.push(row.id);
    continue;
  }
  total += Number(row.amount);
}

// 断言判断: 不崩, 但静默算错
for (const row of rows) {
  assert.ok(!("amount" in row), `row ${row.id} 不应有 amount 字段, 实际字段: ${Object.keys(row).join(",")}`);
  assert.strictEqual(row.amount, undefined, `row ${row.id}.amount 应为 undefined`);
}
assert.ok(Number.isNaN(Number(undefined)), "Number(undefined) 应为 NaN");
assert.ok(Number.isNaN(total), `total 应为 NaN, 实际 ${total}`);
assert.deepStrictEqual(missing, [], "id 3 的缺失标记应丢掉: missing 应为空数组");
assert.strictEqual(
  JSON.stringify({ total, missing }, null, 2),
  `{
  "total": null,
  "missing": []
}`,
  "console.log(JSON.stringify(...)) 的真实输出应为 total:null, missing:[] (NaN 序列化成 null)"
);

console.log("F2 证实: 遍历 rows 不崩, row.amount 全是 undefined,");
console.log("  total 变 NaN (JSON 输出成 null), id 3 的 missing 标记丢失. 静默算错, 无任何报错.");
console.log("消费者代码将打印:", JSON.stringify({ total, missing }));
