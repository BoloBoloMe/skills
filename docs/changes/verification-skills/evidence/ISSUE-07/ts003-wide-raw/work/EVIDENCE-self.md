# 本地自证材料索引 (用于合并)

## 命令与输出
- 导出: `cd head && uv run python db/seed.py && uv run python scripts/dump_orders.py`
  - head/var/orders.export.json (对象, schema=orders-export/2, rows[].amount_value)
  - head.stdout.json (裸数组, rows[].amount_value)
- 基线: base/ 同命令 -> base/var/orders.export.json (裸数组, amount), base.stdout.json
- 真实消费者: `bash /tmp/orchestra-07/orders-consumer/src/run.sh <file>`
  - consumer_head_file.{stdout,stderr,exit}: exit=1, TypeError: rows is not iterable (ledger.js:6)
  - consumer_head_stdout.{stdout,stderr,exit}: exit=0, {"total": null, "missing": []}
  - consumer_base_file.stdout: total 22.490000000000002, missing [3], exit=0
- probe_rows_old_field.mjs: 只适配外层仍用 amount -> total NaN, missing [] (CONFIRMED)
- probe_amounts.py: amountlib 2.4.0 本地路径, 金额值 12.50/9.99/null 不变 (PASS)
