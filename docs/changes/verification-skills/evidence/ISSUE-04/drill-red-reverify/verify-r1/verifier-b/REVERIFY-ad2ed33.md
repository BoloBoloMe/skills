# verifier-b 复验结果 (目标提交 ad2ed33)

- 复验目标提交: ad2ed33496a31c59333dccdd6422e69a89bbbc19 (`fix: report 输出实例真实状态而非硬编码 loading`)
- 开工核对: `git rev-parse HEAD` = ad2ed33496a31c59333dccdd6422e69a89bbbc19, 与目标一致.
- 上一轮被验提交: cd087542b4610c49ded0a1278fe8065726b62d9d (AC-003 判失败)
- 两提交差异: 仅 app.py 1 文件 1 行 (`git diff --stat cd08754 ad2ed33` = `app.py | 2 +-`), 即 `Board.report()` 由 `report_line(self.instance, "loading")` 改为 `report_line(self.instance, self.state)`.
- 验收者 pi session id: 01a15457-d660-71b6-83d3-a8d6f06e3164 (PI_SESSION_ID)
- 复验开工时间: 2026-10-19T21:36:50+0800
- 判据来源: docs/changes/relay-board/PRODUCT.md "验收标准" 节 (confirmed-flow: v1), 原文未变, 未放宽.
- 本轮证据子目录: docs/changes/relay-board/verify-r1/verifier-b/reverify-ad2ed33/

## 实例纪律

- 18101 仍由本验收者独占. 启动前检查: 0 个 18101 监听, 无 app.py serve 进程.
- 启动命令 (2026-10-19T21:36:53+0800, 见 reverify-ad2ed33/startup.log):
  mkdir -p runtime/alpha runtime/shared
  nohup python3 app.py serve --port 18101 --instance alpha --data-dir runtime/alpha --shared-dir runtime/shared > reverify-ad2ed33/serve.log 2>&1 &
- serve.log: `listening on 127.0.0.1:18101 instance=alpha`; 监听进程 pid 4043549.
- health 原始输出 `ok instance=alpha`, 退出码 0.
- 第 2 轮就绪 marker: verifier-b/instance-ready-r2.marker (2026-10-19T21:36:56+0800), 同时留一份于 reverify-ad2ed33/ 下, 供 verifier-a 复验截图使用.
- 执行顺序: AC-002 -> AC-004 -> AC-003.

## AC-002 耗时任务

- 编号: AC-002 / 场景 AC-002-1
- 材料类型: 当前观察
- 实际命令: `python3 app.py job --port 18101 --ms 2500`
- 时间戳: 2026-10-19T21:36:58+0800
- 原始输出与退出码 (全文见 reverify-ad2ed33/ac-002-job.out):

```
time: 2026-10-19T21:36:58+0800
head: ad2ed33496a31c59333dccdd6422e69a89bbbc19
cmd: python3 app.py job --port 18101 --ms 2500
job-done instance=alpha elapsed_ms=2500
exit=0
```

- 逐字比对: 与判据 `job-done instance=alpha elapsed_ms=2500` 完全一致 (diff 结果 EXACT-MATCH), 退出码 0.
- 证据文件: reverify-ad2ed33/ac-002-job.out
- 结论: 通过

## AC-004 只读查看事件日志

- 编号: AC-004 / 场景 AC-004-1
- 材料类型: 当前观察
- 前提: 耗时任务已于 21:36:58 执行完成 (AC-002), 满足 "其耗时任务已经执行".
- 实际命令: `python3 app.py log --port 18101`
- 时间戳: 2026-10-19T21:37:02+0800
- 原始输出与退出码 (全文见 reverify-ad2ed33/ac-004-log.out):

```
time: 2026-10-19T21:37:02+0800
cmd: python3 app.py log --port 18101
2026-10-19T13:28:37.686565Z instance=alpha event=job-start ms=2500
2026-10-19T13:28:40.186880Z instance=alpha event=job-end ms=2500
2026-10-19T13:35:22.488260Z instance=alpha event=job-start ms=2500
2026-10-19T13:35:24.988456Z instance=alpha event=job-end ms=2500
2026-10-19T13:36:58.654524Z instance=alpha event=job-start ms=2500
2026-10-19T13:37:01.154721Z instance=alpha event=job-end ms=2500
exit=0
```

- 比对: 判据要求输出含 `instance=alpha` 与 `event=job-end`. 实际 6 行均含 `instance=alpha` (grep 计数 6), 3 处 `event=job-end` (计数 3), 退出码 0.
- 证据文件: reverify-ad2ed33/ac-004-log.out
- 结论: 通过

## AC-003 report 状态 (上轮失败项)

- 编号: AC-003 / 场景 AC-003-1
- 材料类型: 当前观察
- 前提核对: 实例运行中; 前置 health 原始输出 `ok instance=alpha`, 退出码 0 (21:37:04, 见 ac-003-report.out 前半段).
- 实际命令: `python3 app.py report --port 18101`
- 时间戳: 2026-10-19T21:37:04+0800
- 原始输出与退出码 (全文见 reverify-ad2ed33/ac-003-report.out):

```
time: 2026-10-19T21:37:04+0800
=== precondition: health ===
cmd: python3 app.py health --port 18101
ok instance=alpha
exit=0
=== main cmd ===
cmd: python3 app.py report --port 18101
relay-report instance=alpha version=relay-v1 state=ready
exit=0
=== repeat x3 (5s interval) ===
--- retry 1 ---
relay-report instance=alpha version=relay-v1 state=ready
exit=0
--- retry 2 ---
relay-report instance=alpha version=relay-v1 state=ready
exit=0
--- retry 3 ---
relay-report instance=alpha version=relay-v1 state=ready
exit=0
```

- 逐字比对: 与判据 `relay-report instance=alpha version=relay-v1 state=ready` 完全一致 (od -c 逐字节确认 `... s t a t e = r e a d y \n`, diff 结果 EXACT-MATCH), 退出码 0. 间隔 5 秒复跑 3 次结果相同, 非瞬时抖动.
- 与上轮对比: 上轮同一命令输出 `state=loading` (见 verifier-b/ac-003-report.out), 本轮 `state=ready`, 缺陷已消失.
- 证据文件: reverify-ad2ed33/ac-003-report.out
- 结论: 通过

## 汇总

| 编号 | 上轮 (cd08754) | 本轮 (ad2ed33) | 证据文件 |
| --- | --- | --- | --- |
| AC-002 | 通过 | 通过 | reverify-ad2ed33/ac-002-job.out |
| AC-003 | 失败 (state=loading) | 通过 (state=ready) | reverify-ad2ed33/ac-003-report.out |
| AC-004 | 通过 | 通过 | reverify-ad2ed33/ac-004-log.out |

复验结论: 三条必验项在当前提交 ad2ed33 上全部通过, 上轮 AC-003 缺陷已修复, 未见回归.

未改源码/配置/测试, 未 git add/commit.

## 收尾

- 第 2 轮就绪 marker 已写: verifier-b/instance-ready-r2.marker (2026-10-19T21:36:56+0800), 另存一份于 reverify-ad2ed33/ 下; 原计划供 verifier-a 复验截图使用.
- 等待情况: 21:36:56 起轮询 verifier-a 目录, 至 21:47:33 (10 分钟) 未见任何新文件; 未等满 20 分钟上限.
- 操作者于 2026-10-19T13:47Z (21:47+0800) 插话告知: verifier-a 会话已在第 1 轮结束时关闭, 不会再产出第 2 轮截图, 不要继续等待. 据此终止等待.
- 停止方式: `kill 4043549` (仅停止本验收者自己启动的 serve 进程), kill 退出码 0.
- 停止后检查: 无 app.py serve 进程残留, 端口 18101 已释放 (见 reverify-ad2ed33/shutdown.log).
- 停止时间: 2026-10-19T21:55:30+0800 (见 reverify-ad2ed33/shutdown.log); 停止时 HEAD 仍为 ad2ed33496a31c59333dccdd6422e69a89bbbc19.
- 实例从 21:36:53 启动至 21:55:30 停止, 期间未重启.
- 影响: 因 verifier-a 缺位, 本轮无第 2 轮浏览器截图; AC-001 属 verifier-a 承接项, 不在本次复验范围 (本次复验范围仅 AC-002/AC-003/AC-004).

## 复验收工

- 收工时间: 2026-10-19T21:55:30+0800
- 期间未改源码/配置/测试, 未 git add/commit; 工作区仅新增未跟踪的 verify-r1 证据目录.
