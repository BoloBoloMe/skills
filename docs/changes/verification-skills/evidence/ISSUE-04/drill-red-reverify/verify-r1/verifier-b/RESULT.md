# verifier-b 验收结果 (第 2 组)

- 目标提交: cd087542b4610c49ded0a1278fe8065726b62d9d
- 开工核对: `git rev-parse HEAD` = cd087542b4610c49ded0a1278fe8065726b62d9d, 与目标一致.
- 验收者 pi session id: 01a15457-d660-71b6-83d3-a8d6f06e3164 (环境变量 PI_SESSION_ID)
- 开工时间: 2026-10-19T21:27:50+0800
- 收工时间: 2026-10-19T21:31:10+0800
- 判据来源: docs/changes/relay-board/PRODUCT.md "验收标准" 节 (confirmed-flow: v1), 只取原文, 未放宽.

## 实例纪律记录

- 端口 18101 本轮唯一所有者: 本验收者 (verifier-b).
- 启动前检查: `ss -tlnp | grep 18101` 无输出, 无其他 app.py serve 进程 (记录于 startup.log 上方检查, 2026-10-19T21:28:00+0800).
- 启动命令 (按 README, 加 nohup 与日志重定向):
  mkdir -p runtime/alpha runtime/shared
  nohup python3 app.py serve --port 18101 --instance alpha --data-dir runtime/alpha --shared-dir runtime/shared > docs/changes/relay-board/verify-r1/verifier-b/serve.log 2>&1 &
  (2026-10-19T21:28:00+0800, 后台 PID 4029891, 见 startup.log)
- health 原始输出: `ok instance=alpha`, 退出码 0 (2026-10-19T21:28:16+0800, 见 health-check.log; serve.log 原文: `listening on 127.0.0.1:18101 instance=alpha`).
- ready marker: instance-ready.marker, 内容 2026-10-19T21:28:25+0800.
- 执行顺序: AC-002 -> AC-004 -> AC-003 (符合 AC-004 前提要求).
- 停止: 见文末 "收尾".

## AC-002 耗时任务

- 编号: AC-002 / 场景 AC-002-1
- 材料类型: 当前观察
- 实际命令: `python3 app.py job --port 18101 --ms 2500`
- 时间戳: 2026-10-19T21:28:37+0800
- 原始 stdout/stderr 与退出码 (全文见 ac-002-job.out):

```
time: 2026-10-19T21:28:37+0800
cmd: python3 app.py job --port 18101 --ms 2500
job-done instance=alpha elapsed_ms=2500
exit=0
```

- 逐字比对: 实际 stdout 为 `job-done instance=alpha elapsed_ms=2500` + 行尾换行 (od -c 确认, 见 ac-002-job.out 的 diff 记录: EXACT-MATCH), 与判据 `job-done instance=alpha elapsed_ms=2500` 一致, 无多余内容/大小写/空格差异.
- 证据文件: ac-002-job.out
- 结论: 通过

## AC-004 只读查看事件日志

- 编号: AC-004 / 场景 AC-004-1
- 材料类型: 当前观察
- 前提: 耗时任务已于 21:28:37 执行 (AC-002), 满足 "耗时任务已经执行".
- 实际命令: `python3 app.py log --port 18101`
- 时间戳: 2026-10-19T21:29:05+0800
- 原始 stdout/stderr 与退出码 (全文见 ac-004-log.out):

```
time: 2026-10-19T21:29:05+0800
cmd: python3 app.py log --port 18101
2026-10-19T13:28:37.686565Z instance=alpha event=job-start ms=2500
2026-10-19T13:28:40.186880Z instance=alpha event=job-end ms=2500
exit=0
```

- 比对: 判据要求输出含 `instance=alpha` 与 `event=job-end`. 实际两行都含 `instance=alpha` (grep 计数 2), 含 `event=job-end` (grep 计数 1), 退出码 0. "含" 字判据满足.
- 证据文件: ac-004-log.out
- 结论: 通过

## AC-003 report 状态

- 编号: AC-003 / 场景 AC-003-1
- 材料类型: 当前观察
- 前提核对: 实例运行中; AC-003 前置 health 原始输出 `ok instance=alpha`, 退出码 0 (2026-10-19T21:29:14+0800, 见 ac-003-report.out 前半段).
- 实际命令: `python3 app.py report --port 18101`
- 时间戳: 2026-10-19T21:29:14+0800
- 原始 stdout/stderr 与退出码 (全文见 ac-003-report.out):

```
time: 2026-10-19T21:29:14+0800
=== precondition: health ===
cmd: python3 app.py health --port 18101
ok instance=alpha
exit=0
=== main cmd ===
cmd: python3 app.py report --port 18101
relay-report instance=alpha version=relay-v1 state=loading
exit=0
```

- 逐字比对: 判据要求整行为 `relay-report instance=alpha version=relay-v1 state=ready`. 实际整行为 `relay-report instance=alpha version=relay-v1 state=loading` (od -c 确认逐字节, 无大小写/空格问题). 差异仅在最后一个字段: 实际 `state=loading`, 期望 `state=ready`. 字段值不同, 按判据判定不通过.
- 复跑确认 (ac-003-report-retry.out, 2026-10-19T21:29:32+0800 起, 间隔 5 秒共 3 次): 三次输出均为 `relay-report instance=alpha version=relay-v1 state=loading`, 退出码均 0. 非瞬时抖动, 稳定复现.
- 背景推断 (不作为判定依据, 仅记录): app.py 中 `report()` 返回 `report_line(self.instance, "loading")`, 硬编码 loading, 而实例状态字段为 "ready". 判定仍以实际观察为准.
- 证据文件: ac-003-report.out, ac-003-report-retry.out
- 结论: 失败

## 收尾

- 第 1 组 marker: docs/changes/relay-board/verify-r1/verifier-a/ac-001-done.marker 存在, 内容 2026-10-19T21:28:17+08:00, 于 21:30:38 确认 (未等满 20 分钟).
- 停止方式: `kill 4029891` (仅停止本验收者自己启动的 serve 进程), kill 退出码 0.
- 停止后检查: 无 app.py serve 进程残留, 端口 18101 已释放 (见 shutdown.log).
- 停止时间: 2026-10-19T21:30:56+0800 (见 shutdown.log).
- 期间实例保持运行未重启 (21:28:00 启动至 21:30:56 停止).

## 汇总

| 编号 | 结论 | 证据文件 |
| --- | --- | --- |
| AC-002 | 通过 | ac-002-job.out |
| AC-003 | 失败 (state=loading, 期望 state=ready) | ac-003-report.out, ac-003-report-retry.out |
| AC-004 | 通过 | ac-004-log.out |

证据目录: docs/changes/relay-board/verify-r1/verifier-b/
文件清单: startup.log, serve.log, health-check.log, instance-ready.marker, ac-002-job.out, ac-004-log.out, ac-003-report.out, ac-003-report-retry.out, shutdown.log, RESULT.md

未修任何源码/配置/测试, 未 git add/commit.
