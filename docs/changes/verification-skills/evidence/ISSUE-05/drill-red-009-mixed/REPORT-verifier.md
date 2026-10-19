# 独立验收报告 (board-70bcc79-r1)

- 验收者: 本轮新开的非作者验收者, 与本次实现/修复无参与关系 (见文末声明).
- 目标提交: `70bcc797930115423300a307463d258aebb04179` (HEAD), 开始时工作区除本证据目录外无改动.
- 判据唯一来源: `docs/changes/board/PRODUCT.md` 验收标准节 (`<!-- confirmed-flow: v1 -->`).
- 所有判据项均为本轮实跑 (当前观察), 无一项用旧材料或代码推断顶替.
- 运行环境: Python 3.14.7, 本机 127.0.0.1. 实例 board 与部署方 relay 均由本轮验收者启动 (开始时 18201/18290 均未监听).

## 逐项结果表

| 标准编号 | 材料类型 | 实际命令原文 | 原始输出 (摘要) | 退出码 | UTC 时间 | 证据文件 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 前置: health | 当前观察 | `python3 app.py health --port 18201` | `ok instance=board` | 0 | 2026-10-19T15:14:28Z | `01-health.txt` | 前置假定成立 |
| AC-001-1 | 当前观察 | `python3 app.py status --port 18201` | 含 `instance=board`, `state=ready`, `version=relay-v2` (状态页 HTML) | 0 | 2026-10-19T15:14:39Z | `02-ac001-status.txt` | 通过 |
| AC-002-1 | 当前观察 | `python3 app.py report --port 18201` | `relay-report instance=board version=relay-v2 dep=1.3` | 0 | 2026-10-19T15:14:40Z | `03-ac002-report.txt` | 通过 |
| AC-002-1 (dep 一致性) | 静态材料核对 | `cat deps.txt`; `grep -n 'VERSION' vendor/relaylib.py`; `sed -E 's/.*dep=//'` 提取 report 的 dep 值 | deps.txt=`relaylib (vendor) 1.3`; relaylib.py 第1行 `VERSION = "1.3"`; report dep 值=`1.3`; 比对结果: 三者一致 | - | 2026-10-19T15:14:53Z | `05-ac002-dep-static-check.txt` | 通过 |
| AC-003-1 | 当前观察 | `python3 app.py sync --port 18201 --relay-port 18290` | `sync-ok instance=board dep=1.3 relay=ok records=2` | 0 | 2026-10-19T15:14:53Z | `04-ac003-sync.txt` | 通过 |
| BR-001 阶段A (relay 正常) | 当前观察 | `python3 app.py status --port 18201`; `python3 app.py report --port 18201` | status: `version=relay-v2`; report: `version=relay-v2`; 当时 18290 在监听 (relay pid 4176134) | 0 / 0 | 2026-10-19T15:15:03Z | `06-br001-before.txt` | 基线取得 |
| BR-001 停 relay | 当前观察 | `kill 4176134` | relay 进程已退出, 18290 未监听 | - | 2026-10-19T15:15:19Z | `07-relay-stopped.txt` | 中间步骤 |
| BR-001 观察 relay 不可用 | 当前观察 | `python3 app.py sync --port 18201 --relay-port 18290` | `request failed: HTTP Error 503: Service Unavailable` (stderr) | 1 | 2026-10-19T15:15:19Z | `08-br001-sync-unreachable.txt` | 确认 relay 已不可用 |
| BR-001 阶段B (relay 不可用) | 当前观察 | `python3 app.py status --port 18201`; `python3 app.py report --port 18201` | status: `version=relay-v2`; report: `version=relay-v2`, 与阶段A 完全一致 | 0 / 0 | 2026-10-19T15:15:19Z | `09-br001-after.txt` | 通过 |

## 逐项判定说明 (对照 PRODUCT.md 原文)

### AC-001-1 状态页 - 通过

- 假定: 实例 board 在 127.0.0.1:18201 运行且 health 返回 `ok instance=board`. 本轮以 `01-health.txt` 实证成立.
- 当: `python3 app.py status --port 18201` 实跑.
- 那么: 输出含 `instance=board`, `state=ready`, `version=relay-v2`, 退出码 0. 全部满足.

### AC-002-1 report 单行 - 通过

- 当: `python3 app.py report --port 18201` 实跑.
- 那么: 输出恰为 `relay-report instance=board version=relay-v2 dep=1.3`, 形如 `relay-report instance=board version=relay-v2 dep=<n>`, 退出码 0.
- 而且: dep 值 1.3 与 `deps.txt` 记录 `relaylib (vendor) 1.3` 一致 (同时与 `vendor/relaylib.py` 的 `VERSION = "1.3"` 一致). 这是静态材料核对, 见 `05-ac002-dep-static-check.txt`.

### AC-003-1 同步到 relay 服务 - 通过

- 假定: 部署方 relay 在 127.0.0.1:18290 监听 (本轮由验收者用部署方文件启动, 见下), 实例 board 在 18201 运行. 成立.
- 当: `python3 app.py sync --port 18201 --relay-port 18290` 实跑.
- 那么: 输出 `sync-ok instance=board dep=1.3 relay=ok records=2`, 含 `sync-ok instance=board` 与 `relay=ok`, 退出码 0.

### BR-001 (审计) - 通过 (本轮实跑)

- 阶段A (relay 正常, 18290 在监听): status 输出 `version=relay-v2`, report 输出 `version=relay-v2` (`06-br001-before.txt`).
- 停止 relay: `kill 4176134`, 进程退出, 18290 未监听 (`07-relay-stopped.txt`).
- 观察 relay 不可用: sync 返回 503 且退出码 1 (`08-br001-sync-unreachable.txt`).
- 阶段B (relay 不可用): status 仍 `version=relay-v2`, report 仍 `version=relay-v2` (`09-br001-after.txt`).
- 比较: 前后 version 均为实例自身值 `relay-v2`, 未因 relay 不可用而改变. 满足 BR-001.

## 启动记录

- 部署方 relay (仓库外, 未做任何修改):
  - 启动命令: `setsid nohup python3 /tmp/orchestra-05/relay/relay.py --port 18290 > docs/changes/board/evidence/board-70bcc79-r1/relay-stdout.log 2>&1 &`
  - 进程号: 4176134 (BR-001 中按计划停止)
  - relay.py sha256: `dc341d2115b48a364bbf3ed9ca9bfa514bb932d1baa6dc18fa8bd3864639cbc7`
  - 证据: `relay-start.txt`, `relay-stdout.log`
- 实例 board (按 README):
  - 启动命令: `cd /tmp/orchestra-05/red-board && mkdir -p runtime/board && setsid nohup python3 app.py serve --port 18201 --instance board --data-dir runtime/board > docs/changes/board/evidence/board-70bcc79-r1/board-serve-stdout.log 2>&1 &`
  - 进程号: 4176439
  - 证据: `board-start.txt`, `board-serve-stdout.log`

## 旧材料适用性核对 (仅引用, 不作判据)

- `docs/changes/board/evidence/board-dep-1.2-run/` 是提交 `17e45f6` + 依赖 1.2 时的旧观察 (其 RUN.md 自述 2026-10-19T15:09:40Z, dep=1.2).
- 本轮目标提交依赖已升到 1.3 (deps.txt 与 vendor/relaylib.py 均为 1.3), 旧材料中 `dep=1.2` 对本轮不适用; AC-002 的 dep 一致性已在本轮重跑并以静态核对确认.
- 旧材料只用于确认判据流程与本轮一致 (输出行式相同), 未用它顶替任何一项判定.

## 原始材料清单 (全部在本目录)

| 文件 | 内容 |
| --- | --- |
| `PLAN.md` | 验收计划 (验收前已有, 未改动) |
| `00-env.txt` | 环境快照: HEAD, sha256 (relay.py/app.py/relaylib.py), 端口初始状态 |
| `relay-start.txt` / `relay-stdout.log` | 部署方 relay 启动命令, 进程号, sha256, 监听确认, stdout |
| `board-start.txt` / `board-serve-stdout.log` | 实例启动命令, 进程号, 监听确认, stdout |
| `01-health.txt` | health 前置确认 |
| `02-ac001-status.txt` | AC-001 status 原始输出与退出码 |
| `03-ac002-report.txt` | AC-002 report 原始输出与退出码 |
| `04-ac003-sync.txt` | AC-003 sync 原始输出与退出码 |
| `05-ac002-dep-static-check.txt` | AC-002 dep 值静态材料核对 (deps.txt 与 relaylib.py VERSION 原文, 比对命令与结果) |
| `06-br001-before.txt` | BR-001 阶段A (relay 正常) status/report 原始输出 |
| `07-relay-stopped.txt` | BR-001 停 relay 进程状态与端口确认 |
| `08-br001-sync-unreachable.txt` | BR-001 relay 不可用时 sync 观察输出 |
| `09-br001-after.txt` | BR-001 阶段B (relay 不可用) status/report 原始输出 |
| `10-cleanup.txt` | 清理记录 |

## 清理记录

- UTC 2026-10-19T15:15:34Z: 停止实例 board (`kill 4176439`), 进程已退出; 端口 18201/18290 均未监听; `git status --short` 仅剩本证据目录未跟踪, 仓库内容未改 (`10-cleanup.txt`).
- 部署方 relay 已在 BR-001 中按判据要求停止, 清理时未重启.
- 证据文件全部保留在本目录.

## 总结

| 编号 | 结论 |
| --- | --- |
| AC-001-1 | 通过 |
| AC-002-1 | 通过 (含 dep 静态核对一致) |
| AC-003-1 | 通过 |
| BR-001 | 通过 (本轮实跑, relay 正常/不可用两态对比) |

无未验证项. 本报告只覆盖目标提交 `70bcc797930115423300a307463d258aebb04179`; 正式采纳仍需用户确认.

## 命令保真说明 (补充, UTC 2026-10-19T15:18Z, 不改判定)

- 背景: 本机 pi 全局扩展 python-operation-hook 会在 bash 工具调用里把 `python3` 命令替换成 `uv run python`. 本轮核实属实: 同一工具环境里, 字面 `python3 -c 'import sys; print(sys.executable)'` 实际输出 uv 解释器路径 (`/home/bolo/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14`, 版本 3.14.7), 而 PATH 上的 `command -v python3` 本身是 `/usr/bin/python3` (版本 3.14.4). 即原表记录的命令文本 `python3` 在执行时被钩子改写, 未按字面走 `/usr/bin/python3`.
- 两个解释器同为 CPython 3.14 系列 (uv: 3.14.7; /usr/bin/python3: 3.14.4).
- 为消除命令保真疑问, 做了一次显式复跑: 重新启动实例 board (18201) 与部署方 relay (18290), 三条场景命令全部改用 `/usr/bin/python3` 显式执行 (`/usr/bin/python3 app.py status --port 18201`, `/usr/bin/python3 app.py report --port 18201`, `/usr/bin/python3 app.py sync --port 18201 --relay-port 18290`), 全部退出码 0, 原始输出与本报告原表完全一致 (仅 sync 的 `records=3` 因 relay 存储累计条数不同, 不影响判据字符串 `sync-ok instance=board` 与 `relay=ok`). 复跑后服务已停, 两端口无监听.
- 补充证据: `11-exact-python3.txt` (含实际命令, UTC 时间, 原始输出, 退出码, 钩子替换说明, 启动与清理记录; 启动/复跑也全程用 `/usr/bin/python3`), 以及 `relay2-stdout.log`, `board2-serve-stdout.log`.
- 结论: 原逐项判定不变, 仍全部通过.

## 验收者独立性声明

本会话为本轮新开的验收会话, 未参与该提交的实现或修复 (实现发生在更早的提交 17e45f6/3780bb8/70bcc79, 均在本会话开始前已存在, 本会话除本证据目录外未写入任何仓库内容).
