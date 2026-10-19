# 独立验收结果 G1 (relay-board v1)

## 版本与时间

- 工作目录: /tmp/orchestra-04/red-parallel
- `git rev-parse HEAD`: `e398c7cc7ca4e493d23689bee3cca1a34d306000` (与派工目标一致)
- 复核时间: 2026-10-19T22:47:58+08:00 (`git rev-parse HEAD` 与 `git status --short` 见下)
- 开始时间: 2026-10-19T22:48:05+08:00 (启动 alpha/beta)
- 结束时间: 2026-10-19T22:49:16+08:00 (清理进程完成)
- 起点 `git status --short`: 仅 `?? docs/changes/relay-board/evidence-v1-e398c7c/` (证据目录, 本轮新建)
- 运行环境: Python 3.14.7 (`/usr/bin/python3`), google-chrome `/usr/bin/google-chrome`
- 启动前置: `runtime/shared/` 为空 (无 record.jsonl, 无 events.log)

## 逐条结论

| 标准编号 | 材料类型 | 实际操作或引用信息 | 实际结果 | 证据位置 | 时间或版本 | 结论 |
|---|---|---|---|---|---|---|
| AC-001-1 | 当前观察 | health 18101 -> `ok instance=alpha`; chrome 无头截图 http://127.0.0.1:18101/status-page; `python3 app.py report --port 18101` | 截图目视: `relay board` / `instance=alpha` / `state=ready` / `version=relay-v1`; report 输出 `relay-report instance=alpha version=relay-v1 state=ready`, 与期望逐字一致, 退出码 0 | ac-001-1.log, ac-001-1-alpha-status.png | 2026-10-19T22:48:10+08:00, e398c7c | 通过 |
| AC-001-2 | 当前观察 | `python3 app.py status --port 18102` | stdout 含 `instance=beta`, `state=ready`, `version=relay-v1`; 退出码 0 | ac-001-2.log | 2026-10-19T22:48:10+08:00, e398c7c | 通过 |
| AC-002-1 | 当前观察 | `python3 app.py job --port 18101 --ms 4000`, 用 date +%s%N 计实际耗时 | 输出 `job-done instance=alpha elapsed_ms=4000`, 退出码 0, 实际耗时 4064 ms (>= 4000) | ac-002-1.log | 2026-10-19T22:48:15+08:00, e398c7c | 通过 |
| AC-002-2 | 当前观察 | `python3 app.py job --port 18102 --ms 4000`, 同法计时 | 输出 `job-done instance=beta elapsed_ms=4000`, 退出码 0, 实际耗时 4066 ms (>= 4000) | ac-002-2.log | 2026-10-19T22:48:21+08:00, e398c7c | 通过 |
| AC-003-1 | 当前观察 | 先确认 `ls -l runtime/shared/record.jsonl` 报 No such file (ls 退出码 2); 再 `python3 app.py append --port 18101 --value alpha`; 再 `record` 并计数 | 前置成立(文件不存在); 输出 `seq=1 value=alpha`, 退出码 0; 记录中 `"value": "alpha"` 恰好 1 条, 记录 1 行 | ac-003-1.log | 2026-10-19T22:48:27+08:00, e398c7c | 通过 |
| AC-003-2 | 当前观察 | 先确认记录已含 alpha 条目; 再 `python3 app.py append --port 18102 --value beta`; 再 `record` 并计数 | 前置成立(已有 seq=1 alpha); 输出 `seq=2 value=beta`, 退出码 0; `"value": "beta"` 恰好 1 条, alpha 仍 1 条 | ac-003-2.log | 2026-10-19T22:48:30+08:00, e398c7c | 通过 |
| AC-004-1 | 当前观察 | 后台先起 `python3 app.py job --port 18101 --ms 8000`, sleep 1 后 `ps` 确认进程仍在运行, 再 `python3 app.py log --port 18101` | ps 显示 job 进程存活(etime 00:01); log 输出含 `instance=alpha event=job-start ms=8000`, 且当时尚无对应 job-end; 退出码 0; 之后后台 job 正常结束退出码 0 | ac-004-1.log, ac-004-1-job-bg.out | 2026-10-19T22:48:34~35+08:00, e398c7c | 通过 |
| AC-005-1 | 当前观察 | 两侧 report + 两侧无头截图, 各自核对 instance/version | alpha: 截图 `instance=alpha` `version=relay-v1`, report `relay-report instance=alpha version=relay-v1 state=ready`; beta: 截图 `instance=beta` `version=relay-v1`, report `relay-report instance=beta version=relay-v1 state=ready`; 每侧截图与 report 的 instance/version 相同, 两侧 report 都含 `state=ready`, 退出码均 0 | ac-005-1.log, ac-005-1-alpha-status.png, ac-005-1-beta-status.png | 2026-10-19T22:48:48+08:00, e398c7c | 通过 |
| BR-001 | 当前观察 | (a) 验收流程串行追加后的记录审计; (b) 同一共享记录上 alpha/beta 同时各追加一条(值 gamma/delta)的并发审计 | (a) 串行: seq=[1,2], 1..n 连续且唯一, value 全部唯一 -> 满足; (b) 并发: alpha 输出 `seq=3 value=gamma`, beta 同时输出 `seq=3 value=delta`, 记录出现 `"seq": 3` 两次, seq=[1,2,3,3], `seq_is_1_to_n=False` -> 序号重复, 违反 "不重复" | br-001.log, br-001-record-after-ac003.jsonl.txt, br-001-probe-alpha.out, br-001-probe-beta.out | 2026-10-19T22:49:06+08:00 (a) / 2026-10-19T22:49:09+08:00 (b), e398c7c | 失败 |
| BR-002 | 当前观察 | 查看前后对 runtime/shared/events.log 取 sha256/大小/mtime, 期间执行 `log --port 18101` 与 `log --port 18102`, 再比对并做 cmp 与 before 副本对比 | 查看前: size=540, mtime=2026-10-19 22:48:42.274268620 +0800, sha256=09801156...314d34; 查看后: 三项完全相同, cmp 退出码 0, log 退出码 0 | br-002.log, br-002-events-before.log | 2026-10-19T22:49:04+08:00, e398c7c | 通过 |

## 未验证 / 失败项汇总

- 失败: BR-001 (1 项)。
  - 现象: 两实例对同一共享记录并发追加时, 双方都先算出同一个 seq (3) 再各自写入, 记录中出现重复序号。
  - 原始输出: `[alpha] seq=3 value=gamma` / `[beta] seq=3 value=delta`; record 末两行 seq 均为 3。
  - 触发条件: AC-003-1/AC-003-2 的串行追加不触发; 只有同刻并发追加才触发。代码中 `append_record` 在"算出 seq"与"写文件"之间 sleep 1.2s 且没有加锁, 所以并发窗口真实存在(此句为读代码解释, 结论以上面实测为准)。
  - 判定依据: PRODUCT.md BR-001 原文 "共享记录的序号从 1 开始连续递增且不重复, 每个 value 只出现一次"; 背景也写明 "可以同时开多个实例 ... 所有实例共用一条记录", 并发追加属于该规则覆盖的共享记录用法, 故记失败。
- 未验证: 无。
- 说明: 验收场景 AC-003-1 / AC-003-2 的串行追加本身通过, 二者产物满足 BR-001; BR-001 的失败来自并发写法。
- 无权限/依赖缺失: 无需记录, 全部材料均为本轮实跑。

## 额外观察 (不作为判据)

- `ps -o cmd` 显示后台 job 的命令行为 `uv run python app.py job ...`, 但实际调用的是 `/usr/bin/python3 app.py`; 不影响任何场景输出与退出码, 仅记录现场。
- 证据目录中不放任何 .py; 未改产品代码/配置/测试, 未 commit, 未 push; 工作区改动仅新增本证据目录。

## 清理记录

- 清理时间: 2026-10-19T22:49:16+08:00
- 停止的进程: alpha pid=4134574 (127.0.0.1:18101), beta pid=4134575 (127.0.0.1:18102), 由 `ss -ltnp` 定位后 kill。
- 清理后核对: `ss -ltnp` 无 18101/18102 监听; `python3 app.py health --port 18101` 报 Connection refused, 退出码 1。
- 未删除 runtime/ 下由验收产生的 record.jsonl / events.log, 保留原始状态便于复核; 未改动仓库任何受版本控制文件。
- 详情见 cleanup.log。
