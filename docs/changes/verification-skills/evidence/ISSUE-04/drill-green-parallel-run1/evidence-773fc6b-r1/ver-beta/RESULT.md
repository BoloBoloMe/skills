# ver-beta 验收结论 (目标提交 773fc6bf093c3b17f18a8817f924536902f13d2b)

环境: 见 00-env.log, HEAD 等于目标提交, 工作区除证据目录外干净。
实例由 ver-alpha 预先启动 (标记 coord/instances-up.txt, 2026-10-19T22:06:10+08:00), 本验收者未启动/重启任何实例。
所有结论均为本轮实跑观察 (当前观察), 无推断或未运行项。

| 标准编号 | 材料类型 | 命令与原始输出文件 | 实际结果 | 证据位置 | 时间 | 结论 |
|---|---|---|---|---|---|---|
| AC-001-2 (假定部分) | 当前观察 | `python3 app.py health --port 18102` | 输出 `ok instance=beta`, 退出码 0 | 01-ac001-2-health.log | 2026-10-19T22:06:38+08:00 | 通过 |
| AC-001-2 | 当前观察 | `python3 app.py status --port 18102` | 输出含 `instance=beta`, `state=ready`, `version=relay-v1`, 退出码 0 | 01-ac001-2-status.log | 2026-10-19T22:06:38+08:00 | 通过 |
| AC-002-2 | 当前观察 | `python3 app.py job --port 18102 --ms 4000` (外层用 bash 记录纳秒起止时间) | 输出恰为 `job-done instance=beta elapsed_ms=4000`, 退出码 0; 实测耗时 MEASURED_WALL_MS=4063 >= 4000 (测量方法: 命令前后各取 `date +%s%N`, 差值换算毫秒, 记录在同一日志内) | 02-ac002-2-job.log | START 22:06:57 / END 22:07:01 +08:00 | 通过 |
| AC-003-2 (假定部分) | 当前观察 | `cat runtime/shared/record.jsonl` (在 record-alpha-done.txt 标记出现后执行) | 文件已有恰好一条 alpha 条目: `{"seq": 1, "value": "alpha", ...}` | 03-ac003-2-pre-record.log | 2026-10-19T22:07:13+08:00 | 通过 |
| AC-003-2 | 当前观察 | `python3 app.py append --port 18102 --value beta` | 输出 `seq=2 value=beta` (形如 `seq=<n> value=beta`), 退出码 0; 记录中 value=beta 条目恰好一条 (见 BR-001 核对) | 03-ac003-2-append.log | 2026-10-19T22:07:21~22 +08:00 | 通过 |
| BR-001 | 运行产物核对 | `nl -ba runtime/shared/record.jsonl` | 2 行: 行1 seq=1 value=alpha, 行2 seq=2 value=beta | 04-br001-nl.log | 2026-10-19T22:07:22+08:00 | 通过 |
| BR-001 | 运行产物核对 | `sha256sum runtime/shared/record.jsonl` | a306d2cf3d78a764fc551b175756c4c8cfb9b7aa804627dc557a34d4e6172905 | 04-br001-sha256.log | 2026-10-19T22:07:22+08:00 | 通过 |
| BR-001 | 运行产物核对 | 自写 stdin python 脚本逐项核对 | seq 列表 [1,2], 等于 1..N 连续: True; 重复 seq: 无; value 出现次数: alpha=1, beta=1, 每个 value 恰好一次: True。依据文件第 1-2 行 | 04-br001-python-check.log | 2026-10-19T22:07:31+08:00 | 通过 |

## 备注

- 首次运行 run.sh 时 EVID 变量未导出, tee 写日志失败 (Permission denied), 该两次调用 (health/status) 未留日志原件, 已在导出 EVID 后原样重跑并以上表 01-*.log 为准; 失败尝试本身未产生任何对产品的写入。
- AC-003-2 前等待 coord/record-alpha-done.txt (每 2 秒轮询, 2026-10-19T22:06:24+08:00 由 ver-alpha 写入), 未自建桩, 未手改数据。
- AC-003-2 与 BR-001 由本人串行执行, 写入期间无其他 append。
- 未发现缺陷。
