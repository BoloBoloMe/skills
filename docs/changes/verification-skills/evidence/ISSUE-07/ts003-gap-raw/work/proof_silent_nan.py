"""探针: 消费者若已适配外层信封 (读 .rows), 但仍读旧键 amount, 会静默算出 null 总额.

这条不判"基线正确", 它断言静默错误确实存在: 退出 0, total 变成 null, missing 为空.
"""
import json, pathlib, subprocess

W = pathlib.Path("/tmp/orchestra-07/out/ts003-gap-work")
SNIP = r"""
import fs from "node:fs";
const payload = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const rows = payload.rows ?? payload;          // 已适配信封
let total = 0; const missing = [];
for (const row of rows) {
  if (row.amount === null) { missing.push(row.id); continue; }  // 仍是旧键
  total += Number(row.amount);
}
console.log(JSON.stringify({ total, missing }));
"""
(W / "envelope_consumer.mjs").write_text(SNIP)
for label, f in [("HEAD 导出", W / "head/var/orders.export.json"),
                 ("HEAD stdout", W / "head.stdout.json")]:
    p = subprocess.run(["node", str(W / "envelope_consumer.mjs"), str(f)], capture_output=True, text=True)
    print(f"--- {label} rc={p.returncode} {p.stdout.strip()}")
    got = json.loads(p.stdout)
    assert p.returncode == 0
    assert got["total"] is None and got["missing"] == [], got   # 静默: 退出码 0, 总额 null, 无缺失
print("confirmed: 退出码 0, total=null, missing=[]  -> 静默算错账")
