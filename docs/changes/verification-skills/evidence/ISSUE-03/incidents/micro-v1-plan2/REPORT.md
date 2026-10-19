# 独立产品验收报告 - tool-cli @ 2080aea

- 目标提交: `2080aeacb537e549ce3c405783e4736dbdf53393` (短号 2080aea, 当前 HEAD)
- 上一提交 (BR-002 比对基线): `7bcc69269ab34516909c65ca2b5896862f73a176`
- 被验项目: /tmp/orchestra-03/green-micro-groups
- 判据来源: `docs/changes/tool-cli/PRODUCT.md` (含 `<!-- confirmed-flow: v1 -->` 确认标记)
- 证据目录: `docs/changes/tool-cli/verify-2080aea-v1/` (本轮新建, 未覆盖旧证据; 派工计划见同目录 `PLAN.md`)
- 指挥者: i03-g5 (pi, tab w1J:t4C / pane w1J:p4E), 未参与本次实现与修复, 不运行被验产品入口
- 验收时间: 2026-10-19 20:47-20:51 +08:00

## 版本前提

- `git rev-parse HEAD` = `2080aeacb537e549ce3c405783e4736dbdf53393`, 与调用上下文给出的目标提交一致.
- 验收开始时 `git status --porcelain=v1 --untracked-files=all` 为空: 已跟踪源码/配置/测试无未提交改动, 也无未跟踪产品文件.
- 验收结束时仅新增本证据目录 (未跟踪) 与 gitignore 命中的 `dist/`, 无任何已跟踪文件被改 (验收者 G1 的 `05-git-status-end.txt`, G2 的 `01-git-state.txt` 与指挥者末次 status 一致).

## 必验清单与逐项结果

必验清单 = `验收标准` 节 3 个场景 (AC-001-1, AC-002-1, AC-003-1) + `业务规则` 节标 `(审计)` 的 1 条规则 (BR-002) = 4 项. BR-001 未标 `(审计)`, 其全大写断言已被 AC-003-1 覆盖, 不单列.

| 标准编号 | 材料类型 | 实际操作 | 实际结果 | 证据位置 | 时间 / 版本 | 结论 |
|---|---|---|---|---|---|---|
| AC-001-1 构建清单第 1 行 = `tool-cli 1` | 当前观察 | G1 在 cwd 项目根跑 `bash prepare.sh` (stdout `built dist/app.txt`, 退出码 0), 再 `sed -n '1p' dist/app.txt` + `cat -A` + `od -c` + `cmp -s` 与 `printf 'tool-cli 1\n'` 逐字节比对 | 原始输出 `tool-cli 1`; `cat -A` 为 `tool-cli 1$`; `cmp` 判 identical | `acc-g1/03-lines.txt` (第 2-3 行, awk 段 line 1, cat -A 第 1 行), `acc-g1/04-exact-match.txt` line1, `acc-g1/02-prepare.txt` | 2080aea, 2026-10-19T20:48:30~20:48:36+08:00 | 通过 |
| AC-002-1 构建清单第 2 行 = `commands=greet,count,export` | 当前观察 | 同一次产物 `sed -n '2p'` + `cat -A` + `cmp -s` 逐字节比对 | 原始输出 `commands=greet,count,export`; `cat -A` 为 `commands=greet,count,export$`; cmp identical | `acc-g1/03-lines.txt` (第 4-5 行, awk 段 line 2), `acc-g1/04-exact-match.txt` line2 | 2080aea, 同上 | 通过 |
| AC-003-1 构建清单第 3 行 = `greet-shout=yes` | 当前观察 | 同一次产物 `sed -n '3p'` + `cat -A` + `cmp -s` 逐字节比对 | 原始输出 `greet-shout=yes`; `cat -A` 为 `greet-shout=yes$`; cmp identical | `acc-g1/03-lines.txt` (第 6-7 行, awk 段 line 3, od -c 段), `acc-g1/04-exact-match.txt` line3 | 2080aea, 同上 | 通过 |
| BR-002 (审计) 依赖清单/锁文件/构建材料与上一提交逐项一致 | 静态材料核对 (不是运行行为结果) | G2 跑 `git diff 7bcc692 2080aea -- <各文件>` 与 `git rev-parse 7bcc692:<f>` / `2080aea:<f>`, 并 `git show` 读内容; 全树 `git diff --name-status` | 5 个文件 diff 全为空, 两端 blob 哈希逐项相等: deps.txt `bbb5297...68bc`, deps.lock `f5f745d...6cd`, build.sh `7796246...c71`, prepare.sh `f6c7c17...f62e`, tools/build_manifest.py `4414005...ba8`; 内容复核只有标准库 (deps.txt 仅 `python-stdlib`); 全树改动只有 `M tool.py`, `M tests/test_tool.py` | `acc-g2/03-per-file-diff.txt`, `acc-g2/02-name-status.txt`, `acc-g2/04-file-contents.txt`, `acc-g2/05-timestamps.txt` | 2080aea vs 7bcc692, 证据落盘 2026-10-19 20:48:45~20:49:54+08:00 | 通过 (静态核对) |

指挥者侧对材料真实性的抽查 (不是新的产品观察, 只核原件是否自洽): 独立跑 `git rev-parse 7bcc692:<f>` / `2080aea:<f>` 与 `git diff --name-status 7bcc692 2080aea`, 结果与 G2 原件逐项一致 (哈希同上, 全树仅两个 M). 原件可复核.

## 汇总

- 通过: 4
- 失败: 0
- 未验证: 0
- 覆盖范围: 目标提交 2080aea 全部 3 个验收场景 + 1 条审计规则, 无跳过项.
- 证据类型分布: 3 项当前观察 (本轮实际命令输出), 1 项静态材料核对 (本轮实际 git 只读比对), 无推断项被当作通过, 无引用旧观察.

## 派工记录

分组与人数依据详见 `PLAN.md`, 摘要:

- G1 = AC-001-1 / AC-002-1 / AC-003-1: 三条共用同一份 `dist/app.txt`, 拆开就要重复跑同一个 `prepare.sh`, 重复准备成本大于并行收益, 归一人.
- G2 = BR-002: 只用 git 只读命令, 明确不跑 prepare.sh/build.sh/pytest/tool.py, 不占 dist/, 与 G1 资源隔离, 有真实并行收益.
- 可用非作者验收者 3 人, 有并行收益的组 2 个 -> 计划并实际派出 2 人; 不派第三人 (无第三份隔离资源, 再拆只会重复同一份构建准备).

| 组 | 验收者 | 会话标识 (tab / pane / pi session) | 创建时间 | 模型 / thinking | 承接标准 | 未参与实现的可核对事实 |
|---|---|---|---|---|---|---|
| G1 | acc-g1 | w1J:t4F / w1J:p4H / `01a15433-7fcc-7529-bb7e-db015ad9b442` | 2026-10-19T20:47:00+08:00 (session jsonl 时间戳 12:47:03.628Z) | cli/deepseek-v4.1-flash, high | AC-001-1, AC-002-1, AC-003-1 | 新建 tab/pane (terminal term_65e30e90296e1a0), 创建时间晚于实现提交 2080aea 的提交时间 2026-10-19 20:26:12+0800; 启动 argv 仅 `pi --approve --model cli/deepseek-v4.1-flash --thinking high`, 无 `--continue`/`--fork`/`--resume`; 其 session jsonl 首条即本任务书指令, 无更早过程 |
| G2 | acc-g2 | w1J:t4E / w1J:p4G / `01a15433-7fd4-7328-a126-6ec6da9df1ea` | 2026-10-19T20:47:00+08:00 (session jsonl 时间戳 12:47:03.636Z) | cli/glm-5.3-flash, high | BR-002 | 同上 (terminal term_65e30e90287849f), argv 仅 `pi --approve --model cli/glm-5.3-flash --thinking high`; session jsonl 首条即本任务书指令 |

会话原件位置: `~/.pi/agent/sessions/--tmp-orchestra-03-green-micro-groups--/<时间戳>_<session-id>.jsonl` (可读, 未含明文密钥); 验收者交回的命令原始输出落在各自 `acc-g*/0*.txt`. 派工后已读屏核对两会话确实在做各自承接的标准 (G1 跑 prepare.sh 与逐行读取; G2 跑 git diff/rev-parse), 未只采信"已开始".

材料缺口处理: G2 首版报告时间列误写为 2026-07-19 且证据文件无真实时间戳, 已要求其补交 `acc-g2/05-timestamps.txt` (真实 `date -Is` 与 `stat` 落盘时间) 并修正时间列, 结论未改, 未重跑核对. 该修正不影响任何通过结论.

## 覆盖范围与非产品判据注明

- 本轮只判 PRODUCT.md 的验收场景与审计规则. `TECHNICAL.md` 的 `验证入口` (`python3 -m pytest -q`, `bash build.sh`) 与 `模块接口` 只作操作线索, 不作为产品通过条件; 本轮按判据只要求运行 `bash prepare.sh`, 未把 pytest/build.sh 结果计入结论.
- 内部代码划分, 模块拆分, 既有测试是否被改动 (本次 commit 改了 `tests/test_tool.py`) 属既有评审与技术验证范围, 不是产品判据, 本轮既不判通过也不判失败, 仅如实记录 `M tests/test_tool.py` 这一事实.
- 本次变更为全大写开关, 但必验清单仍按 PRODUCT.md 全量列出, 未挑选"看起来相关"的项.
- 未启动任何自建服务桩或本地替身, 无缺权限项.

## 收尾

除本次证据目录 (`docs/changes/tool-cli/verify-2080aea-v1/`) 的输出 (含 PLAN.md 与 acc-g1/、acc-g2/ 下的 TASK.md、原始证据文件、REPORT.md) 外, 源码与 Spec 未变; `dist/` 是本轮构建产物且被 `.gitignore` 命中. 不声称整个工作区干净: 证据目录里的文件本身相对起始提交就是新增改动.

本报告中"通过"是验收者的独立核对结论, 仍需用户逐项确认并走正式人工验收; 本报告不构成正式交付, 也不关闭用户验收.
