# ver-alpha 验收结果

- 目标提交: 773fc6bf093c3b17f18a8817f924536902f13d2b (HEAD, 见 00-env.log)
- 验收依据: docs/changes/relay-board/PRODUCT.md 验收场景与业务规则原文
- 证据目录: docs/changes/relay-board/evidence-773fc6b-r1/ver-alpha
- 全部命令均按场景字面使用 `python3 app.py ...`, 由 run.sh 记录命令原文, 原始 stdout/stderr, 退出码, 起止时间
- 产品源码/测试/配置未改动; 仅产生 runtime 数据与本人证据/标记文件

## 环境与共用准备 (当前观察)

| 项 | 结果 | 证据 |
| --- | --- | --- |
| HEAD 等于目标提交 | 是, 773fc6b... | 00-env.log |
| git status --porcelain | 只有 `?? docs/changes/relay-board/evidence-773fc6b-r1/` (证据目录) | 00-env.log |
| 建 runtime/alpha runtime/beta runtime/shared | 完成 | 01a-start-instances.log, 00-env.log 中 ls -l runtime/shared/ |
| 启动 alpha :18101 | pid 4078331, 启动时间 2026-10-19 22:06:01 | 01a-start-instances.log, 01e-instance-pids.log, serve-alpha.out |
| 启动 beta :18102 | pid 4078332, 启动时间 2026-10-19 22:06:01 | 01a-start-instances.log, 01e-instance-pids.log, serve-beta.out |
| health alpha | `ok instance=alpha`, exit 0 | 01b-health-alpha.log |
| health beta | `ok instance=beta`, exit 0 | 01c-health-beta.log |
| 协调标记 instances-up.txt | 已写 (2026-10-19T22:06:10) | 01d-coord-instances-up.log, coord/instances-up.txt |
| 收尾时实例仍在运行且未被重启 | 是, 同一 PID, health 仍 ok | 06b-instances-still-up.log |

## 标准化结论表

| 标准编号 | 材料类型 | 命令与原始输出文件 | 实际结果 | 证据位置 | 时间 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 alpha 实例状态页 | 当前观察 | `python3 app.py status --port 18101` / 02-ac001-status-alpha.log | 输出 HTML 含 `<p>instance=alpha</p>` `<p>state=ready</p>` `<p>version=relay-v1</p>`, EXIT 0 | 02-ac001-status-alpha.log | START 22:06:12, END 22:06:12 | 通过 |
| AC-003-1 追加 alpha 条目 | 当前观察 | 前置 `ls -l runtime/shared/`+test: 03a-ac003-precheck.log ; `python3 app.py append --port 18101 --value alpha`: 03b-ac003-append-alpha.log ; 记录核对: 03c-ac003-verify-record.log | 前置时 record.jsonl 不存在 (ABSENT, 目录 total 0); append 输出 `seq=1 value=alpha`, EXIT 0; 事后记录共 1 条, `value=alpha` 条目恰好 1 条 (seq=1) | 03a / 03b / 03c 三个 log | 前置 22:06:15; append START 22:06:16 END 22:06:18; 核对 22:06:20 | 通过 |
| AC-002-1 alpha 耗时任务 | 当前观察 | `python3 app.py job --port 18101 --ms 4000` / 04-ac002-job-alpha.log | 输出恰为 `job-done instance=alpha elapsed_ms=4000`, EXIT 0; 用时测量方法: 同 shell 内命令前后 `date +%s%N` 相减, ELAPSED_S 4.071, >= 4 秒 | 04-ac002-job-alpha.log | START 22:06:24, END 22:06:28 | 通过 |
| AC-004-1 只读查看事件日志 | 当前观察 | 后台 `python3 app.py job --port 18101 --ms 6000 &`, 1.5 秒后 `python3 app.py log --port 18101`, 之后 wait 等后台 job 结束 / 05-ac004-log-during-job.log, 后台 job stdout: 05a-bgjob.out | log 输出含 `instance=alpha` 与 `event=job-start` (含正在执行的 `event=job-start ms=6000` 且当时尚无对应 job-end), EXIT 0; 时间窗口 job=[22:06:32.128, 22:06:38.195], log=[22:06:33.636, 22:06:33.708], LOG_INSIDE_JOB_WINDOW yes; 后台 job 最后正常结束 `job-done instance=alpha elapsed_ms=6000`, EXIT 0 | 05-ac004-log-during-job.log, 05a-bgjob.out | job START 22:06:32, log 22:06:33, job END 22:06:38 | 通过 |

## 协同标记

| 标记 | 内容 | 时间 | 证据 |
| --- | --- | --- | --- |
| coord/instances-up.txt | `... ver-alpha instances-up ports=18101,18102` | 2026-10-19T22:06:10+08:00 | 01d-coord-instances-up.log |
| coord/record-alpha-done.txt | `... ver-alpha record-alpha-done` | 2026-10-19T22:06:24+08:00 | 03d-coord-record-alpha-done.log |
| coord/alpha-writes-done.txt | `... ver-alpha alpha-writes-done` | 2026-10-19T22:06:41+08:00 | 06-coord-alpha-writes-done.log |

## 说明

- 场景 4 因场景未指定 --ms 数值, 取 6000 毫秒, 以便 log 调用完整落在任务执行窗口内; 场景只要求"耗时任务正在执行", 未约束时长.
- 场景 3 的前置"记录尚不存在"在 append 前用 `ls -l runtime/shared/` 与 test 双重确认 (目录当时为空, 无 record.jsonl).
- 本报告中通过项均为本轮实跑观察, 无一条依赖推断或代码阅读替代执行.
