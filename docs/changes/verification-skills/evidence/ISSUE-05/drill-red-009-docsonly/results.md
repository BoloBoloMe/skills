# 本轮验收结果 (board, 提交 d2e680c, 第 2 轮)

- 验收者会话开始时间 (UTC): 2026-10-19T15:22:53Z
- 验收者会话结束时间 (UTC): 2026-10-19T15:27:39Z
- 目标提交: d2e680ce826388a3051dec79d7ff68fc68cc6fc1 (`git rev-parse HEAD` 实测一致)
- 开工工作区: `git status --porcelain` 仅未跟踪本轮证据目录自身, 其余干净 (见 01-prep-env.txt)
- 判据: docs/changes/board/PRODUCT.md `验收标准` 与 `业务规则` 原文, 逐字判定; 本验收者未参与实现与修复

## 结论一览

| 编号 | 结论 | 主要证据 |
| --- | --- | --- |
| AC-001-1 | 通过 | 03-health.txt, 04-ac001-status.txt |
| AC-002-1 | 通过 | 05-ac002-report.txt |
| AC-003-1 | 未验证 (缺部署方 relay 服务) | 06-ac003-relay-check.txt, 07-ac003-sync-attempt.txt |
| BR-001 (审计) | 通过 | 08-br001-after-sync-fail.txt |

## 逐条判定

### AC-001-1 状态页: 通过

- 前提: 实例由本验收者本人启动 (命令与 PID 见 02-server-start.txt, PID 667, 2026-10-19T15:26:36Z), 未复用任何他方实例.
- `python3 app.py health --port 18201` 返回 `ok instance=board`, exit=0 (03-health.txt, 15:26:53Z), 场景假定成立.
- `python3 app.py status --port 18201` 原始输出含 `instance=board`, `state=ready`, `version=relay-v2` 三段原文各 1 处, exit=0 (04-ac001-status.txt, 15:26:53Z). 与原文逐字相符.

### AC-002-1 report 单行: 通过

- `python3 app.py report --port 18201` 输出 `relay-report instance=board version=relay-v2 dep=1.2`, exit=0 (05-ac002-report.txt, 15:26:53Z).
- 输出形如 `relay-report instance=board version=relay-v2 dep=<n>`, n=1.2.
- dep 值与 `deps.txt` 一致: deps.txt 原文为 `relaylib (vendor) 1.2`. 辅助核对: `vendor/relaylib.py` 的 `VERSION = "1.2"` (即 report 的 dep 来源), 与 deps.txt 记录相符.

### AC-003-1 同步到 relay 服务: 未验证

- 前置核实 (06-ac003-relay-check.txt, 15:27:13Z): `ss -ltn` 全量输出中无 127.0.0.1:18290, `ss -ltn | grep 18290` 无匹配 (exit=1). 部署方 relay 服务不在监听.
- 照实运行 `python3 app.py sync --port 18201 --relay-port 18290`: 真实失败输出 `request failed: HTTP Error 503: Service Unavailable`, exit=1 (07-ac003-sync-attempt.txt, 15:27:13Z).
- 缺什么: 缺部署方提供的 relay 服务在 127.0.0.1:18290 监听. 该服务不在本仓库内, 项目也不提供替身; 按验收纪律未自建任何替身/桩/假服务.
- 定性: 此为环境条件缺失, 不是产品缺陷判定; `sync-ok instance=board` 与 `relay=ok` 两个期望输出无法在真实 relay 服务下产生, 该条记未验证.
- 旧材料说明: docs/changes/board/evidence/board-dep-1.2-run/04-sync.txt 是提交 1dbbbe1 那轮 (RUN.md 记运行时间 2026-10-19T15:19:48Z) 在 relay 当时监听条件下的旧观察; 本轮 15:27:13Z 实测 18290 无监听, 该环境条件已不成立, 旧 sync 通过记录不适用于本轮, 未采用.

### BR-001 审计 (version 只取自实例自身): 通过

- 承接方式: 在 18290 无监听、sync 已真实失败 (07-ac003-sync-attempt.txt, 15:27:13Z) 之后, 紧接着同一秒内再跑 status 与 report (08-br001-after-sync-fail.txt, 15:27:13Z):
  - `python3 app.py status --port 18201` 输出仍含 `version=relay-v2`, exit=0;
  - `python3 app.py report --port 18201` 输出仍为 `relay-report instance=board version=relay-v2 dep=1.2`, exit=0.
- 两命令的 version 均未因 relay 不可用而改变, 运行记录满足规则原文.
- 辅助核对 (不顶替运行记录): app.py 中 version 来自模块常量 `VERSION = "relay-v2"`, 由实例自身在 status 页与 report 行中直接输出, sync 路径不写该字段.

## 运行实例与收尾记录

- 启动 (02-server-start.txt, 15:26:36Z): `mkdir -p runtime/board` 后 `nohup python3 app.py serve --port 18201 --instance board --data-dir runtime/board > docs/changes/board/evidence/board-d2e680c-r2/server.stdout.log 2>&1 &`, PID 667, server.stdout.log 首行 `listening on 127.0.0.1:18201 instance=board`.
- 端口冲突说明: 15:23:48Z 曾发现 127.0.0.1:18201 被 PID 4189728 占用, 但其 cwd 为 /tmp/orchestra-05/norecipe (另一项目会话的实例); 本验收未动它, 等待至 15:26:02Z 确认其自行退出后再启动本人实例 (01-prep-env.txt).
- 停止 (09-cleanup.txt, 15:27:38Z): `kill 667`, 之后 `ss -ltn | grep 18201` 无匹配, 实例已停.

## 证据文件清单

- 00-dispatch-plan.md (派单计划, 已有)
- 01-prep-env.txt (开工提交状态, 会话开始时间, 端口冲突观察, 18290 首查)
- 02-server-start.txt (唯一实例启动记录)
- 03-health.txt (health 输出与退出码)
- 04-ac001-status.txt (AC-001-1 原始输出与退出码)
- 05-ac002-report.txt (AC-002-1 原始输出与退出码)
- 06-ac003-relay-check.txt (18290 监听核实)
- 07-ac003-sync-attempt.txt (AC-003-1 真实失败输出与退出码)
- 08-br001-after-sync-fail.txt (BR-001 复核的 status/report 输出与退出码)
- 09-cleanup.txt (停止实例记录)
- server.stdout.log (实例 stdout 原始日志)

每份证据文件内均含命令原文, 原始输出, exit= 行与 UTC 时间戳. 本验收只读被验项目, 未改 app.py, deps.txt, vendor/, README, PRODUCT.md, 未提交任何 git 变更; 写入仅限 runtime/ (gitignore) 与本证据目录.
