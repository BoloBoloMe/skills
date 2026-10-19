# 独立验收报告: 记录板 (board) 提交 d2e680c

- 目标提交: `d2e680ce826388a3051dec79d7ff68fc68cc6fc1` ("docs: 补充交接说明"), 提交时间 2026-10-19T15:19:48Z.
- 判据来源: `docs/changes/board/PRODUCT.md`, `验收标准` 节带 `<!-- confirmed-flow: v1 -->`; 用其 3 个 gherkin 场景 + `业务规则` 中 1 条 `(审计)` 规则, 共 4 条必验项.
- 本轮证据目录: `docs/changes/board/evidence/board-d2e680c-r2/` (新开, 未覆盖上一轮 `board-dep-1.2-run/`).
- 派工计划: 同目录 `00-dispatch-plan.md`.
- 覆盖版本: 仅上述目标提交. 验收开始时 `git status --porcelain` 只有证据目录自身未跟踪, 已跟踪源码/配置/测试无改动 (见 `01-prep-env.txt`).

## 汇总

| 结论 | 条数 | 条目 |
| --- | --- | --- |
| 通过 | 3 | AC-001-1, AC-002-1, BR-001 |
| 失败 | 0 | 无 |
| 未验证 | 1 | AC-003-1 (缺部署方 relay 服务, 127.0.0.1:18290 无监听) |

不用"全部通过"概括: AC-003-1 本轮无法在真实 relay 服务下产生期望输出, 记未验证, 未用任何替身改判.

## 逐项结果

| 标准编号 | 材料类型 | 实际操作或引用信息 | 实际结果 | 证据位置 | 时间/版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 当前观察 | 验收者自启唯一实例 (`nohup python3 app.py serve --port 18201 --instance board --data-dir runtime/board`, PID 667), 再跑 `python3 app.py health --port 18201` 与 `python3 app.py status --port 18201` | health 输出 `ok instance=board` exit=0; status 原始 HTML 含 `instance=board`, `state=ready`, `version=relay-v2` 各 1 处, exit=0 | `02-server-start.txt`, `03-health.txt`, `04-ac001-status.txt`, `server.stdout.log` | 2026-10-19T15:26:36Z 启动 / 15:26:53Z 运行 / 提交 d2e680c | 通过 |
| AC-002-1 | 当前观察 | `python3 app.py report --port 18201` | 输出 `relay-report instance=board version=relay-v2 dep=1.2`, exit=0; dep=1.2 与 `deps.txt` 原文 `relaylib (vendor) 1.2` 一致 (辅助核对: `vendor/relaylib.py` `VERSION = "1.2"`) | `05-ac002-report.txt` | 2026-10-19T15:26:53Z / d2e680c | 通过 |
| AC-003-1 | 未运行 (缺依赖服务) | 先 `ss -ltn` 全量输出 + `ss -ltn \| grep 18290` 核实监听; 再照实跑 `python3 app.py sync --port 18201 --relay-port 18290` | 18290 无监听 (grep exit=1); sync 真实输出 `request failed: HTTP Error 503: Service Unavailable` exit=1; 期望的 `sync-ok instance=board` 与 `relay=ok` 无法产生 | `06-ac003-relay-check.txt`, `07-ac003-sync-attempt.txt` | 2026-10-19T15:27:13Z / d2e680c | 未验证: 缺部署方提供的 relay 服务在 127.0.0.1:18290 监听 (该服务不在仓库内, 本轮未自建替身/桩/假服务). 属环境缺口, 不作产品缺陷判定 |
| BR-001 (审计) | 当前观察 | relay 不可用且 sync 已真实失败之后, 紧接着再跑 `python3 app.py status --port 18201` 与 `python3 app.py report --port 18201` | status 仍含 `version=relay-v2` exit=0; report 仍为 `relay-report instance=board version=relay-v2 dep=1.2` exit=0; 两处 version 未因 relay 不可用改变 (辅助: app.py 中 version 取自模块常量 `VERSION = "relay-v2"`, sync 路径不写该字段, 仅作辅助不顶替运行记录) | `08-br001-after-sync-fail.txt` (辅助: `app.py` VERSION 常量) | 2026-10-19T15:27:13Z / d2e680c | 通过 |

## 旧材料核对

`docs/changes/board/evidence/board-dep-1.2-run/` 是提交 `1dbbbe1` 那轮的旧观察, 其 `04-sync.txt` 记 `sync-ok ... relay=ok records=4` (运行时间 2026-10-19T15:19:48Z). 本轮核查:

- 代码/依赖条件仍成立: `git diff --name-status 1dbbbe1..d2e680c` 只动 `docs/`, `app.py` 与 `vendor/relaylib.py`, `deps.txt` 未变.
- 但环境条件已不成立: 本轮实测 18290 无监听 (指挥者开工时与验收者 15:27:13Z 各查一次).
- 处理: 未采用旧 sync 通过记录, AC-003-1 记未验证. 旧材料只作材料, 未作为本轮通过依据.

## 派工记录

- 场景组划分: 1 组, 承接全部 4 条 (AC-001-1, AC-002-1, AC-003-1, BR-001).
- 计划人数 1 名, 实际派出 1 名. 依据: 三条场景与 BR-001 运行部分共用同一实例 127.0.0.1:18201 与同一份 `serve` 启动 (共用准备); 该端口只能有一个实例, 拆成两会话必须先后重复启动同一实例, 重复准备成本大于并行收益. 无并行收益, 未标记并行组. 组内只有一名验收者, 无跨会话争用片段; 组内执行顺序为: 启动实例并核 health → status → report → sync (对外写入) → 失败后紧接 status/report 复核 BR-001.
- 当轮可用非作者验收者: 1 名, 由指挥者新开. 现场 `i05-red009b` (cwd `/tmp/orchestra-05/red-board2`) 为实现/修复会话, 不可用; `acc-r1` 属上一轮 `/tmp/orchestra-05/red-board` 的验收会话, 非本轮新开且不承接本目标提交, 不可用.
- 验收者标识: pi 会话 `01a154c0-88e2-7782-ab41-c7b481dbee5b` (会话文件 `~/.pi/agent/sessions/--tmp-orchestra-05-red-board2--/2026-10-19T15-21-06-531Z_01a154c0-88e2-7782-ab41-c7b481dbee5b.jsonl`), Herdr agent 名 `verif-d2e680c` (pane `w1E:p18`, tab `w1E:t18`).
- 模型选型: `cli/glm-5.3-flash`, thinking `xhigh` (llm-select 评分表 review 画像 1.000, coding 1.000; 与本次实现会话所用 deepseek-v4.1-flash 不同厂商, 减少共同盲区; 失败代价中等, 取第二深档).
- 未参与本次实现与修复的可核对事实:
  - 会话创建时间 `2026-10-19T15:21:06.531Z`, 晚于最后一个实现提交时间 `2026-10-19T15:19:48Z`.
  - 会话以新进程从 cwd `/tmp/orchestra-05/red-board2` 启动, 不继承实现会话 (`i05-red009b`) 的过程; 指挥者提交的任务文本只含目标提交, 判据路径, 证据目录与核对规则, 未含实现对话或作者自证结论.
  - 操作记录核对 (会话 jsonl): 工具调用仅 `bash` 13 次, `read` 5 次 (app.py, PRODUCT.md, README.md, vendor/relaylib.py, 00-dispatch-plan.md), `write` 1 次 (`results.md`); 无对 `app.py`, `deps.txt`, `vendor/`, `PRODUCT.md` 的写入, 无 git 提交.
  - 施工后核对: 指挥者本人 `git status --porcelain` 只有证据目录未跟踪, `git diff` 为空, HEAD 仍为 d2e680c.
- 共用准备执行人: 验收者本人 (唯一一次 `serve` 启动, PID 667, 记录于 `02-server-start.txt`); 原始材料全部归该验收者, 落在本轮证据目录.
- 可隔离组开始/结束: 仅 1 组, 15:22:53Z 开始 (会话内首次工作) / 15:27:39Z 结束.
- 争用片段: 无跨会话争用. 附带记录: 15:23:48Z 验收者发现 18201 被另一项目实例 (PID 4189728, cwd `/tmp/orchestra-05/norecipe`) 占用, 未 kill, 等其 15:26:02Z 自行退出后才启动本人实例 (`01-prep-env.txt`).
- 共享材料: 本轮只有 1 名验收者, 无跨验收者共享材料, 无接收方适用性核对需要.
- 清理: 验收者 `kill 667` 后 `ss -ltn | grep 18201` 无匹配 (`09-cleanup.txt`, 15:27:38Z); 指挥者复核 18201/18290 均无监听. 证据目录外只多出空目录 `runtime/board/` (已在 `.gitignore`).

## 复核说明

- 每条结论都由验收者本轮亲手产生 (当前观察); 未采用推断或旧观察顶替. AC-003-1 的旧观察已被明确排除.
- 材料完整性: 每个证据文件含命令原文, 原始输出, `exit=` 行与 UTC 时间戳; 与验收者会话 jsonl 中的实际命令调用逐条对应 (15:22:47Z 起, 含 serve 启动, health, status, report, sync, kill).
- 非产品判据事项: 本轮未评审代码结构, 模块划分等技术事项, 它们不属本 Spec 通过条件, 此处既不判通过也不判失败.

## 收尾

除本次证据目录的输出外, 源码与 Spec 未变 (相对起始提交 d2e680c, 工作区只新增本证据目录的未跟踪文件与 gitignore 内的空 `runtime/board/`).

本报告结论仍需用户逐项确认和正式人工验收; 通过项不构成正式交付, 也不关闭用户验收.
