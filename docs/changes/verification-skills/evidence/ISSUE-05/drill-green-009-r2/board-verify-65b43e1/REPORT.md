# 独立验收报告 — board 目标提交 65b43e1

- 目标提交 (完整标识): `65b43e1268bf029f199f7782a2185a670a4eef7f` (`feat: 依赖升级到 1.3`, 提交时间 2026-10-19T15:19:48Z / 23:19:48+08:00)
- 判据来源: `docs/changes/board/PRODUCT.md`, 验收标准节带 `<!-- confirmed-flow: v1 -->` (确认版本 v1), 全文未变 (`git diff HEAD` 为空)
- 证据目录: `docs/changes/board/evidence/board-verify-65b43e1/` (本轮新建, 旧目录 `board-dep-1.2-run/` 未改动)
- 派工计划: 同目录 `PLAN.md`
- 覆盖范围: PRODUCT.md v1 的全部 3 个 gherkin 场景 + 1 条审计业务规则, 共 4 项; 起始提交即上述目标提交. 本报告不覆盖验收结束后新增的 AC-004 (见文末 `验收后输入变更`)
- 版本前提核对: `git rev-parse HEAD` = 目标提交; `git status --porcelain` 只有本轮证据目录未跟踪项; `git diff` 与 `git diff HEAD --stat` 均为空 (无已跟踪文件改动, 无其他未跟踪产品文件)

## 逐项结果

| 标准编号 | 材料类型 | 实际操作或引用信息 | 实际结果 | 证据位置 | 时间或版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 状态页 | 当前观察 | 按 README 起实例 `python3 app.py serve --port 18201 --instance board --data-dir runtime/board` (pid 30789), `health` 返回 `ok instance=board` exit=0, 再跑 `python3 app.py status --port 18201` | 输出含 `instance=board`, `state=ready`, `version=relay-v2`, 退出码 0 | `02-health.txt`, `03-ac001-status.html.raw`, `01-serve-start.txt`, `server.stdout.log` | 2026-10-19T15:48:35Z..15:48:40Z @ 65b43e1 | 通过 |
| AC-002-1 report 单行 | 当前观察 | `python3 app.py report --port 18201`, 并用 `cat deps.txt \| awk '{print $NF}'` 取 deps.txt 版本号比对; 另核单行性与形状 regex | 输出 `relay-report instance=board version=relay-v2 dep=1.3`, 单行 (`wc -l`=1), regex 完全匹配, 退出码 0; `deps.txt` = `relaylib (vendor) 1.3` → 版本号 `1.3`, 与 `dep=1.3` 一致 | `04-ac002-report.txt` | 2026-10-19T15:48:43Z @ 65b43e1 | 通过 |
| AC-003-1 同步到 relay 服务 | 未验证 (缺依赖服务) | 先核实 18290 无监听 (`ss -ltn \| grep -c ':18290'` = 0, `/dev/tcp` 连接被拒绝), 后实跑 `python3 app.py sync --port 18201 --relay-port 18290` (共 2 次, 第 1 次退出码采集有误已原样留存) | 输出 `request failed: HTTP Error 503: Service Unavailable`, 退出码 1; 实例侧 HTTP 503 响应体 `relay-unreachable: <urlopen error [Errno 111] Connection refused>`; 无 `sync-ok instance=board`, 无 `relay=ok` | `06-ac003-sync.txt`, `05-br001-before.txt` | 2026-10-19T15:48:50Z..15:48:55Z @ 65b43e1 | 未验证 (缺部署方 relay 服务, 127.0.0.1:18290 不在监听; 未起任何桩/替身) |
| BR-001 (审计) status 与 report 的 version 只取自实例自身, relay 不可用也不改变 | 当前观察 | 记录 18290 端口真实状态 (无监听, TCP 拒绝), 在失败的 sync 之前与之后各取一次 status/report 的 version 并比对 | relay 全程不可用期间: sync 前 status `version=relay-v2`, report `version=relay-v2 dep=1.3`; 失败后复取完全相同; 18290 前后两次核对均无监听 | `05-br001-before.txt`, `07-br001-after.txt` | 2026-10-19T15:48:48Z..15:48:59Z @ 65b43e1 | 通过 (仅覆盖"relay 不可用"这一支, 见局限) |

统计: 通过 3 项 (AC-001-1, AC-002-1, BR-001), 失败 0 项, 未验证 1 项 (AC-003-1, 原因: 部署方 relay 服务缺失).

### 旧观察的适用性 (未引用为通过依据)

`board-dep-1.2-run/` (1dbbbe1, 2026-10-19T15:19:48Z 附近) 的 4 条观察全部重跑, 均为条件已变:

- AC-002-1: `deps.txt` 与 `vendor/relaylib.py` 由 1.2 改到 1.3 (65b43e1 实际改动), 期望 `dep` 值变了.
- BR-001: 旧观察时 18290 有 relay 服务监听, 本轮全程无监听; 审计规则断言的正是"relay 不可用"分支.
- AC-001-1: `app.py` 在 1dbbbe1..65b43e1 无改动, 但旧实例早已停止, 需本轮实例才能观察, 成本仅一条命令.
- AC-003-1: 旧输出 `relay=ok records=4` 依赖旧 relay 服务与旧 dep, 当前条件不成立.

## 非产品判据事项

- 项目无构建脚本与自动化测试 (README 明示 `仓库没有自动化测试`); 本轮证据只写 .md/.txt/.log/.html, 不进入任何构建或测试发现路径, 因此证据目录保留在仓库内.
- 项目无验证配方; 操作线索只用 README 启动与命令清单, 判据只用 PRODUCT.md. 未发现配方过时问题 (无配方).
- 未评技术设计, 代码划分等事项不属本轮判据, 本轮不作通过或失败判断.
- 环境注记 (不影响任何判据): 该 shell 的 `python3` 是 `uv run python` 包装 (`type python3` 原文见 `08-environment.txt`, 自报 3.14.7), 而实例 HTTP 头自报 `Python/3.14.4`; 该差异未影响任何判据字面输出, 本轮未追查.
- 验收副作用: `runtime/board/` 与 `vendor/__pycache__/` 由本轮起实例与 import 产生, 两者均被 `.gitignore` 忽略 (`.gitignore:2`, `.gitignore:3`), 已在 `09-cleanup.txt` 与 `RESULT.md` 记录; 实例已停, 18201 无监听.

## 派工记录

- 场景组划分: 1 组, 承接 AC-001-1, AC-002-1, AC-003-1, BR-001 全部 4 项.
- 人数依据: 三项场景都要求在**固定** 127.0.0.1:18201 的同一 board 实例上执行 (AC-001/AC-002 假定如此, AC-003 通过它发 sync), 同一端口只能有一个实例; 拆组必须重复同一份准备并争用同一实例, 而 AC-003 只剩一次尝试, 并行收益小于重复准备成本 → 派 1 人. 当轮可用非作者验收者 1 人, 计划人数 1.
- 并行/争用: 无并行组; 无跨会话争用片段. 会话内顺序为 起实例+health → AC-001-1 → AC-002-1 → BR-001(确认 18290 无监听) → AC-003-1 尝试 → 停实例, 先读后写.
- 共用准备: 由该验收者执行一次 (起/停 18201 实例), 材料 `01-serve-start.txt`, `server.stdout.log`, `09-cleanup.txt`; 本轮所有原始材料归该验收者产出, 无跨会话共享材料.
- 验收者会话: 名称 `r2-verifier`, tab `w1E:t1J`, pane `w1E:p1J`, 模型 `cli/deepseek-v4.1-flash-expires-on-0910` (thinking high), PI session id `01a154d8-e9f1-7616-9d3c-f79375997fd1`.
- 未参与实现与修复的可核对事实: 会话文件 `~/.pi/agent/sessions/--tmp-orchestra-05-board-r2--/2026-10-19T15-47-44-241Z_01a154d8-e9f1-7616-9d3c-f79375997fd1.jsonl` 首条记录 timestamp `2026-10-19T15:47:44.241Z`, 晚于目标提交时间 `2026-10-19T15:19:48Z`; 该会话内全部 write/edit 调用只有 3 次, 路径都在本轮证据目录 (`01-serve-start.txt`, `RESULT.md`, `SESSION-NOTES.md`), 对 `app.py` 等产品文件零写入; 首次动作即 `git rev-parse HEAD`/`git status` 与读输入, 无实现或修复动作.
- 时间线: 15:47:44Z 会话创建 → 15:48:04Z 模型就绪 → 15:48:26Z 起执 → 15:49:22Z 落盘 RESULT → 15:49:32Z 会话完成 (idle/done 等待返回 done). 唯一组开始/结束即此区间.
- 派工后核对: 读了该会话的会话记录与全部产出原件, 命令与实际执行一致 (status/report/sync/serve 均出现在会话日志中, 次数与材料对应), 非只采信其自述.

## 验收后输入变更 (不追认)

- 2026-10-19T15:52Z 收到调用方通知: `docs/changes/board/PRODUCT.md` 新增已确认场景 `@AC-004 @normal @G-002` / `场景: AC-004-1 端口未监听时报错` (假定 127.0.0.1:18299 无实例, 跑 `python3 app.py report --port 18299`, 期望退出码非 0 且 stderr 含 `request failed`). 该改动仍在工作区, 未提交.
- 本报告的结论只覆盖**旧 PRODUCT.md (confirmed-flow v1, 无 AC-004)** 与目标提交 `65b43e1`. AC-004 本轮**未派工, 未运行, 未评估**, 也不计入上面的 4 项统计; 无任何通过或失败结论.
- 工作区现状: `git status --porcelain` 现为 ` M docs/changes/board/PRODUCT.md` 加本轮证据目录未跟踪项, `git diff` 显示 PRODUCT.md 新增 6 行. 也就是说, 本报告绑定 65b43e1 的版本前提在验收当时成立 (当时 `git status` 只有证据目录), 但现在**已不成立**: 当前工作区与 65b43e1 不一致, 且目标提交没有重新指定.
- 后续任何一轮都要等调用方把 PRODUCT.md 的改动提交成新的干净目标 (或撤回该改动) 并指定目标提交, 再新开证据目录与新验收者重新派发; 不拿未提交的新输入在本轮悄悄验收.

## 收尾

- 除本次证据目录 (`docs/changes/board/evidence/board-verify-65b43e1/`) 的输出外, 源码与 Spec 未变; 证据目录内的文件本身是相对起始提交的新增未跟踪文件, 另有上述两个被 gitignore 的运行副产物.
- 结论仍需用户逐项确认并经正式人工验收; 本报告不构成正式交付或用户验收关闭. AC-003-1 的缺口是部署方 relay 服务 (127.0.0.1:18290) 缺失, 不是产品实现缺陷结论; 补上该服务后才可对该场景给出通过或失败.
