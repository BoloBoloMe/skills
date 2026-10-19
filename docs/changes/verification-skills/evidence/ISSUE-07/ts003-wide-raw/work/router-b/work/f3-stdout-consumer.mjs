// F3 证明: 读 dump_orders.py stdout (裸数组, 字段已改名 amount_value) 的旧消费者会怎样.
// 判定错则以非零退出. stdout 原文来自 work/dump-head-stdout.txt (真实运行 HEAD 的 dump_orders.py 所得).
import fs from "node:fs";
import assert from "node:assert";

const stdoutText = fs.readFileSync("dump-head-stdout.txt", "utf8").trim();
const fileText = fs.readFileSync("../repo/var/orders.export.json", "utf8");

const stdoutRows = JSON.parse(stdoutText);
const fileObj = JSON.parse(fileText);

// 断言: stdout 与文件不再同构
assert.ok(Array.isArray(stdoutRows), "stdout 解析出来应是裸数组");
assert.ok(!Array.isArray(fileObj) && typeof fileObj === "object", "文件解析出来应是包裹对象");
assert.deepStrictEqual(Object.keys(fileObj), ["schema", "rows"], "文件外层应是 {schema, rows}");
assert.deepStrictEqual(stdoutRows, fileObj.rows, "stdout 数组与文件 rows 内容应一致");

// 旧 stdout 消费者的循环语义 (与 ledger.js:5-12 相同): 期待数组与 amount 字段
let total = 0;
const missing = [];
for (const row of stdoutRows) {
  if (row.amount === null) {
    missing.push(row.id);
    continue;
  }
  total += Number(row.amount);
}

assert.ok(Number.isNaN(total), `total 应为 NaN, 实际 ${total}`);
assert.deepStrictEqual(missing, [], "missing 应为空数组 (id 3 的 null 标记丢失)");

console.log("F3 证实: stdout 仍是裸数组, for...of 不崩, 循环正常走完 (退出码 0).");
console.log("  但 row.amount 是 undefined, total=NaN, missing 丢掉 id 3. 与文件消费者不同: 不崩, 改为静默算错.");
