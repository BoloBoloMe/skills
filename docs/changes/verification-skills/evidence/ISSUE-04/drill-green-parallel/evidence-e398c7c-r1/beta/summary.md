# beta 验收总结 (rev-beta, 第 1 轮)

- 目标提交: e398c7cc7ca4e493d23689bee3cca1a34d306000
- HEAD 核对: `git rev-parse HEAD` = e398c7cc7ca4e493d23689bee3cca1a34d306000 (一致)
- `git status --porcelain` 开始: `?? docs/changes/relay-board/evidence-e398c7c-r1/` (只有证据目录; runtime/ 被 .gitignore 覆盖)
- 收尾时 git status 与 HEAD 相同, 产品文件 (app.py/README.md/deps.txt/tests/) 未改动.
- 判据来源: docs/changes/relay-board/PRODUCT.md (`confirmed-flow: v1`), 只用"验收标准"场景原文与"业务规则"原文.
- 我的会话: PI_SESSION_ID=01a15483-4f6f-70ee-ab4b-8bb426dba77c
  (PI_SESSION_FILE=/home/bolo/.pi/agent/sessions/--tmp-orchestra-04-parallel--/2026-10-19T14-14-14-127Z_01a15483-4f6f-70ee-ab4b-8bb426dba77c.jsonl)
- 起止时间: 2026-10-19T22:14:14+08:00 (会话建立) ~ 2026-10-19T22:15:37+08:00 (收尾核对)

## 结论一览

| 标准 | 结论 | 材料类型 | 证据路径 | 关键命令 | 退出码 | 执行时间 |
|------|------|----------|----------|----------|--------|----------|
| AC-001-2 beta 实例状态页 | 通过 | 当前观察 | beta/ac001-2/out.txt, beta/ac001-2/health-pre.txt, beta/ac001-2/notes.md | `python3 app.py status --port 18102` | 0 | 2026-10-19T22:15:10+08:00 (65 ms) |
| AC-002-2 beta 耗时任务 | 通过 | 当前观察 | beta/ac002-2/out.txt, beta/ac002-2/notes.md | `python3 app.py job --port 18102 --ms 4000` | 0 | 2026-10-19T22:15:12~22:15:16+08:00 (4067 ms) |
| 第 8 项 beta 侧材料 (AC-005-1) | 材料齐备 (自证一致), 跨实例判定归 G4 | 当前观察 | beta/ac005-1/beta-status.png, beta/ac005-1/report-and-status.txt, beta/ac005-1/screenshot.log, beta/ac005-1/notes.md | `python3 app.py report --port 18102` + google-chrome headless 截图 | report 0, chrome 0 | 截图与 report 均在 2026-10-19T22:15:20~22:15:22+08:00 |

## AC-001-2 判定依据

- 前提: `python3 app.py health --port 18102` 在 22:15:08 输出 `ok instance=beta`, exit=0 — 与假定一致.
- 输出含 `instance=beta`, `state=ready`, `version=relay-v1` (三个 `<p>` 行逐字出现), exit=0.
- 判据三项 + 退出码全部满足 → 通过.

## AC-002-2 判定依据

- 输出单行逐字为 `job-done instance=beta elapsed_ms=4000`, exit=0.
- 实际耗时 4067 ms (date +%s%N 前后差 4067314976 ns), >= 4000 ms.
- 判据三项全部满足 → 通过.

## 第 8 项 beta 侧材料

- beta 状态页截图: `/tmp/orchestra-04/parallel/docs/changes/relay-board/evidence-e398c7c-r1/beta/ac005-1/beta-status.png`
  - 产生时间 2026-10-19T22:15:22+08:00, 8695 字节, sha256=d52bb2deb308eeddfba77975795b332827e00f875fc5152641d9efb16ee8f21c
  - 画面: instance=beta, state=ready, version=relay-v1
- beta report 原始输出: `/tmp/orchestra-04/parallel/docs/changes/relay-board/evidence-e398c7c-r1/beta/ac005-1/report-and-status.txt`
  - 产生时间 2026-10-19T22:15:20+08:00
  - 原文: `relay-report instance=beta version=relay-v1 state=ready`
- 同一实例同一版本: 两者都由 PID 4090715 应答, 该进程 22:15:03 启动后未重启; 两次命令间隔约 2 秒, 期间只有这一个 beta 进程在 18102 上.

## beta 实例状态

- 仍在运行: PID 4090715 (setsid 包装进程 4090711), 会话/进程组 4090715, 启动 2026-10-19T22:15:03+08:00, 独立会话, 本回合结束后继续运行.
- 启动命令: `setsid nohup python3 app.py serve --port 18102 --instance beta --data-dir runtime/beta --shared-dir runtime/shared > runtime/beta-serve.log 2>&1 < /dev/null &`
- 启动日志: runtime/beta-serve.log (`listening on 127.0.0.1:18102 instance=beta`)
- 收尾核对 22:15:37: 进程在, 探测 `curl -s http://127.0.0.1:18102/health` 返回 `ok instance=beta` (该探测仅用于活性确认, 不作为判据; 判据只用 app.py 命令).
- 未停止、未重启; 等指挥者通知后再停.

## 边界与缺口

- 我未执行 `append`, 未创建/改写 runtime/shared/record.jsonl. 观察时 record.jsonl 已存在, 是 rev-shared 的操作结果 (events.log 里有 alpha/beta 两条 append 记录), 不影响我的两项标准.
- 我的 job 按产品设计写入 events.log 的 job-start/job-end 两行, 属预期; BR-002 的安静窗口由 G4 负责.
- 未发现无法执行的项目; 无未验证项.
- 未采信任何他人结论; 上述通过/失败均由本轮我自己的命令输出判定.

## 停止记录

- 实例已停止 + 时间: 2026-10-19T22:18:33+08:00 (`kill -TERM 4090715`; 100 ms 内退出; 18102 不再监听; 无残留进程). 详见 beta/stop.txt
