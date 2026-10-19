// 证明 F2/F3: 消费者只适配外层, 仍用 amount 字段时, 结果静默错误.
// 用法: node probe_rows_old_field.mjs <json 文件或 'stdout:<文件>'>
import fs from "node:fs";

const arg = process.argv[2];
let payload;
if (arg.startsWith("stdout:")) {
  payload = JSON.parse(fs.readFileSync(arg.slice(7), "utf8")); // dump_orders.py 的 stdout: 裸数组
} else {
  payload = JSON.parse(fs.readFileSync(arg, "utf8"));
}
const rows = Array.isArray(payload) ? payload : payload.rows; // 假设消费者已适配外层

let total = 0;
const missing = [];
for (const row of rows) {
  if (row.amount === null) {
    missing.push(row.id);
    continue;
  }
  total += Number(row.amount);
}
console.log(JSON.stringify({ total, missing, isNaN: Number.isNaN(total), rows: rows.length }));
if (!Number.isNaN(total)) {
  console.error("FAIL: 期望旧字段读到 undefined 导致 NaN, 实际不是");
  process.exit(1);
}
if (missing.length !== 0) {
  console.error("FAIL: 期望 missing 为空 (undefined !== null), 实际不是");
  process.exit(1);
}
console.log("CONFIRMED: 只改外层不崩溃, 但 total=NaN, missing=[] (静默错误)");
