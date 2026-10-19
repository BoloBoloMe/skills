
import fs from "node:fs";
const payload = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const rows = payload.rows ?? payload;          // 已适配信封
let total = 0; const missing = [];
for (const row of rows) {
  if (row.amount === null) { missing.push(row.id); continue; }  // 仍是旧键
  total += Number(row.amount);
}
console.log(JSON.stringify({ total, missing }));
