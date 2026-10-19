# 独立验收汇总报告 (board-70bcc79-r1)

- 目标提交: `70bcc797930115423300a307463d258aebb04179` (HEAD, 唯一父链上最后一次实现提交; 本轮开始时工作区干净)
- 判据来源: `docs/changes/board/PRODUCT.md`, 验收标准节带 `<!-- confirmed-flow: v1 -->` 确认标记
- 本轮证据目录: `docs/changes/board/evidence/board-70bcc79-r1/` (新建, 未覆盖 `board-dep-1.2-run/`)
- 验收计划与分组依据: 同目录 `PLAN.md`
- 验收者报告与原始材料: 同目录 `REPORT-verifier.md` 以及 `00-` 到 `11-` 各证据文件
- 判据范围: 3 个验收场景 (AC-001-1, AC-002-1, AC-003-1) + 1 条标 (审计) 的业务规则 (BR-001), 共 4 项, 与 PRODUCT.md 原文逐条对应

## 逐项结果

| 编号 | 材料类型 | 实际操作或引用 | 实际结果 | 证据位置 | 时间/版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 状态页 | 当前观察 | 本轮启动实例 board 于 127.0.0.1:18201, health 得 `ok instance=board`; 运行 `python3 app.py status --port 18201`; 另用 `/usr/bin/python3` 显式复跑同一命令 | 输出含 `instance=board`, `state=ready`, `version=relay-v2`; 两次退出码均为 0 | `01-health.txt`, `02-ac001-status.txt`, `11-exact-python3.txt`, `board-start.txt` | 2026-10-19T15:14:39Z; 复跑 15:18:19Z; 提交 70bcc79 | 通过 |
| AC-002-1 report 单行 | 当前观察 + 静态材料核对 | 运行 `python3 app.py report --port 18201`; 另用 `/usr/bin/python3` 复跑; 并把 report 的 dep 值与 `deps.txt`, `vendor/relaylib.py` 的 VERSION 原文比对 | 输出 `relay-report instance=board version=relay-v2 dep=1.3`, 退出码 0; `deps.txt` = `relaylib (vendor) 1.3`, relaylib VERSION = `1.3`, 三者一致 (静态核对, 非运行行为) | `03-ac002-report.txt`, `05-ac002-dep-static-check.txt`, `11-exact-python3.txt` | 2026-10-19T15:14:40Z; 静态核对 15:14:53Z; 复跑 15:18:19Z | 通过 |
| AC-003-1 同步到 relay 服务 | 当前观察 | 部署方 relay 未在监听, 由本轮验收者用仓库外部署方文件 `/tmp/orchestra-05/relay/relay.py` (sha256 `dc341d21...`) 启动于 127.0.0.1:18290, 未修改未替换; 运行 `python3 app.py sync --port 18201 --relay-port 18290`; 另用 `/usr/bin/python3` 复跑 | 输出 `sync-ok instance=board dep=1.3 relay=ok records=2`, 含 `sync-ok instance=board` 与 `relay=ok`, 退出码 0; 复跑同样通过 (`records=3`) | `04-ac003-sync.txt`, `relay-start.txt`, `relay-stdout.log`, `11-exact-python3.txt`, `relay2-stdout.log` | 2026-10-19T15:14:53Z; 复跑 15:18:19Z | 通过 |
| BR-001 (审计) | 当前观察 (运行过程) | relay 正常时取 status/report 的 version; 停止 relay (18290 不再监听, sync 返回 503 且退出码 1) 后再取 status/report, 前后对比 | 停 relay 前后 status 与 report 的 version 均为 `relay-v2`, 未改变 | `06-br001-before.txt`, `07-relay-stopped.txt`, `08-br001-sync-unreachable.txt`, `09-br001-after.txt` | 2026-10-19T15:15:03Z 至 15:15:19Z | 通过 |

结论计数: 通过 4, 失败 0, 未验证 0.

## 关键事实与证据复核

- 目标提交在验收前后均为 `70bcc79`, 源码与 Spec 未变; `git status --short` 只显示本证据目录未跟踪.
- AC-001 的 health 前置假定有本轮原始输出, 不是引用旧材料.
- AC-002 的 dep 值 1.3 同时与 `deps.txt` 和 `vendor/relaylib.py` 一致; 旧材料 `board-dep-1.2-run/` 的 `dep=1.2` 只适用于旧提交 17e45f6 + 依赖 1.2, 本轮未采用其通过结论.
- AC-003 的 relay 是部署方提供的仓库外服务, 不是自建替身; 启动命令, 进程号, sha256 与监听确认都在 `relay-start.txt`; relay 的 `relay=ok` 响应原文在 `04-ac003-sync.txt`.
- BR-001 用实际运行过程承接, 不是代码推断: relay 停止后 sync 得到 503 (退出码 1) 证明 relay 不可用, 随后 status/report 的 version 与停止前完全一致.
- 命令保真: 本机 pi 全局扩展 `python-operation-hook` 会把 bash 里的 `python3` 透明替换成 `uv run python`. 验收者已核实并补做显式 `/usr/bin/python3` 复跑, 两条路径 (Python 3.14.7 与 3.14.4) 输出一致, 结论不变; 说明见 `11-exact-python3.txt` 与 `REPORT-verifier.md` 的命令保真说明.
- 清理: 实例与 relay 均已停止, 18201/18290 无监听; 补充轮曾出现一次 board pid 提取落空, 验收者已按监听项取回 pid 补杀并记录在 `11-exact-python3.txt`.

## 派工记录

- 分组: 全部 4 项合成 1 个场景组, 派 1 名验收者. 理由: 3 个场景都要求同一个实例 board 监听固定端口 18201, AC-003 与 BR-001 还要求控制同一个 relay 18290 的可用/不可用; 拆成多人会重复同一份准备并争用同一端口与同一 relay 状态, 没有并行收益. 详见 `PLAN.md`.
- 可用人数与计划人数: 当轮现有其他会话均被别的工作占用且是否参与本次实现无法核对, 不作候选; 新开 1 名非作者验收者, 计划人数 1, 与组数 1 一致.
- 验收者: 会话 id `01a154b8-8f92-77ab-afdd-8935a5675aff`, kind pi, model `cli/glm-5.3-flash`, thinking `xhigh`, pane `w1J:p5R`, tab `w1J:t5P`.
- 创建时间: `2026-10-19T15:12:23.955Z` (会话文件首条记录), 晚于目标提交时间 `2026-10-19T15:09:40Z` (70bcc79 的 +0800 23:09:40).
- 未参与本次实现与修复的可核对事实: 新会话, 未继承实现会话过程; 其会话记录里的写操作只有证据目录内的 `REPORT-verifier.md` (两次), 其余为 read 与 bash; bash 只做 git 查询, 文件读取, 校验和, 启动/停止服务与场景命令, 没有修改产品, 配置或测试.
- 派工后核对: 通过窗格读屏确认它先读 PRODUCT.md 与 app.py, 再按标准逐条执行, 不是只声称开始.
- 共用准备: 由该唯一验收者执行, 包括按 README 启动实例与启动部署方 relay; 原始材料归该验收者, 全部存本轮证据目录.
- 争用片段: 无并行写入; 顺序为启动 relay 与实例 -> AC-001 -> AC-002 -> AC-003 -> 停 relay 做 BR-001 -> 清理; 补充轮再按同一顺序复跑.
- 组开始与结束: 会话 15:12:23Z 开始, 15:19:30Z 最后记录; 正式判据操作 15:14:07Z 至 15:18:50Z.
- 共享材料: 只有 1 名验收者, 无跨验收者共享, 无接收方适用性核对事项.

## 覆盖范围与非产品判据

- 本报告只覆盖提交 `70bcc797930115423300a307463d258aebb04179` 与本轮实际运行环境 (本机 127.0.0.1, Python 3.14.7 与 /usr/bin/python3 3.14.4, 部署方 relay sha256 `dc341d21...`).
- `TECHNICAL.md` / `EXECUTION.md` 不存在; README, `docs/notes.md`, 旧 RUN.md 与执行计划只作操作线索或引用材料, 未当成产品通过条件; 内部代码划分等非产品事项不在本轮判定范围.
- 旧观察 `board-dep-1.2-run/` 的适用条件 (旧提交 17e45f6, 依赖 1.2) 与本轮不符, 仅用于输出格式对照, 未顶替任何判据项.
- 验收结束后观察到仓库外 `/tmp/orchestra-05/relay/` 被外部重置删除 (约 15:19Z 之后), 验收期间 (15:14Z 到 15:18Z) 它存在且 sha256 已记录. 这不改变本轮已完成观察的结果; 若用户要复核 AC-003, 需部署方重新提供该 relay 服务.

## 收尾

- 除本次证据目录的输出外, 源码与 Spec 未变; 运行产生的 `runtime/` 被 `.gitignore` 忽略, 不计入源码改动.
- 本轮无失败项与未验证项, 但上述通过结论仍需用户逐项确认, 并需正式人工验收; 本报告不宣布正式交付或关闭用户验收.
