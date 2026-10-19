# rev-alpha 汇总 (独立验收, 未参与实现)

- 目标提交: e398c7cc7ca4e493d23689bee3cca1a34d306000 (HEAD, main) — 校验一致
- 校验命令与输出: `git rev-parse HEAD` -> e398c7cc7ca4e493d23689bee3cca1a34d306000; `git status --porcelain` -> `?? docs/changes/relay-board/evidence-e398c7c-r1/` (仅证据目录). 见 00-env/env.txt
- 证据根: docs/changes/relay-board/evidence-e398c7c-r1/alpha/
- 判据来源: docs/changes/relay-board/PRODUCT.md `confirmed-flow: v1` 的验收标准场景原文 + 业务规则原文

## alpha 实例
- 命令 (cwd=/tmp/orchestra-04/parallel):
  `setsid nohup python3 app.py serve --port 18101 --instance alpha --data-dir runtime/alpha --shared-dir runtime/shared > .../alpha/00-env/serve.log 2>&1 &`
- PID 4090884, SID 4090884 (setsid 脱离), 启动 2026-10-19 22:15:07 +0800 (2026-10-19T14:15:07Z)
- 启动日志 00-env/serve.log: `listening on 127.0.0.1:18101 instance=alpha`
- 收尾时仍在运行并通过 health: 见 00-env/final-check.txt (2026-10-19T14:15:58Z, `ok instance=alpha`, exit=0)
- 未执行 append, 未创建或改写 runtime/shared/record.jsonl (该文件由 rev-shared 于 22:15:17 创建, 我方未触碰)

## 逐条结论

### AC-001-1 alpha 状态页与 report — 通过 (当前观察)
- 前提 health: `python3 app.py health --port 18101` -> `ok instance=alpha`, exit=0, 70ms, 2026-10-19T14:15:18Z. 证据 01-ac001/health.txt
- 截图: 命令见 01-ac001/screenshot-cmd.txt (google-chrome headless, 900x400, http://127.0.0.1:18101/status-page), exit=0, 376ms, 2026-10-19T14:15:20Z; 图 01-ac001/alpha-status.png (sha256 4374f026...) 与 04-ac005/alpha-status.png 同一文件
- 截图可见文字 (我方直接看图): `instance=alpha`, `state=ready`, `version=relay-v1`
- report: `python3 app.py report --port 18101` -> `relay-report instance=alpha version=relay-v1 state=ready`, exit=0, 70ms, 2026-10-19T14:15:23Z. 证据 01-ac001/report.txt
- 判定依据: 截图三项与 report 单行逐字等于判据要求, 同一实例同一版本.

### AC-002-1 alpha 耗时任务 — 通过 (当前观察)
- 命令: `python3 app.py job --port 18101 --ms 4000`, 2026-10-19T14:15:26Z -> 14:15:30Z
- stdout: `job-done instance=alpha elapsed_ms=4000`; exit=0; 实测 4067 ms (4067316912 ns) >= 4000 ms
- 证据 02-ac002/job.txt

### AC-004-1 只读查看事件日志 — 通过 (当前观察)
- 时序: 14:15:34Z 后台起 `python3 app.py job --port 18101 --ms 4000` (pid 4092125); 14:15:36Z 任务存活时运行 `python3 app.py log --port 18101` -> exit=0, 66ms; 14:15:38Z 后台 job 结束 exit=0. 证据 03-ac004/run.txt, job-bg.out, log.out
- log 原始输出含 `2026-10-19T14:15:34.746476Z instance=alpha event=job-start ms=4000`, 且无对应 job-end (证明读取发生在任务执行中); 含 `instance=alpha` 4 次, `event=job-start` 3 次
- 说明: 该日志为多实例共享, 输出里也有 beta 行, 判据只要求"含"指定两项, 不影响结论.

### 第 8 项 (AC-005-1) 的 alpha 侧材料 — 已交付 (当前观察)
- 截图: alpha/04-ac005/alpha-status.png, 8788 bytes, sha256 4374f026939db8238ab13de9ed80aad7c997cd3ebc9a89504509d5ac51248803, 产生时间 2026-10-19T14:15:20Z (22:15:20+0800)
- report 原始输出: alpha/04-ac005/report.txt (采集于 2026-10-19T14:15:23Z, exit=0), 另有同一实例复跑 alpha/04-ac005/report-fresh.txt (2026-10-19T14:15:47Z, exit=0)
- 两者同源同版本: 同一进程 PID 4090884 / 端口 18101 / --instance alpha / VERSION 常量 relay-v1; 截图 alpha-status.png 与 01-ac001/alpha-status.png 二进制相同
- 说明文: 04-ac005/notes.md

## 缺口与非结论项
- 无未验证项.
- 时序备注: 我方 job 的 job-end 会写入共享 events.log (产品设计使然, 无法避免), 若第 10 项 (BR-002) 需要安静窗口, 请在其开始前确认我方已停止写入; 本轮结束前我已无后续写入.
- 引用旧观察: 无 (所有结论均来自本轮当前观察).
- 未改动产品文件: app.py / README.md / deps.txt / tests/ 均未修改, `git status --porcelain` 只显示证据目录.

## 会话标识与时间
- PI_SESSION_ID: 01a15483-3add-74a0-a077-1b434d6cb4d0
- PI_SESSION_FILE: /home/bolo/.pi/agent/sessions/--tmp-orchestra-04-parallel--/2026-10-19T14-14-08-862Z_01a15483-3add-74a0-a077-1b434d6cb4d0.jsonl
- 开始时间 (首次命令): 2026-10-19T14:14:58Z (22:14:58+0800)
- 结束时间 (本文件写入): 2026-10-19T14:16:10Z 左右 (22:16:10+0800)

## 实例已停止
- 实例已停止: alpha (PID 4090884) 于 2026-10-19T14:18:31Z (2026-10-19 22:18:31 +0800) 用 `kill -TERM` 停止; 停止后 18101 不再监听, 进程不存在, health 探针 Connection refused (exit=1). 详见 alpha/stop.txt.
