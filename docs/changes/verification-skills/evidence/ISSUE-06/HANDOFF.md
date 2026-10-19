# ISSUE-06 交付报告

## 交付了什么

- 新建 `workflow/benchmark-checklist/SKILL.md`: `benchmark-checklist` 技能的用户调用入口, 覆盖测量基础切片的三个验收标准.
- 新建 `docs/changes/verification-skills/evidence/ISSUE-06/`: 证据索引 (`README.md`), 三份切片记录 (`TS-001.md`, `TS-002.md`, `TS-003.md`), 会话原始输出 (`sessions/`), 受控测量夹具 (`fixtures/`), 本报告.
- 未改任何既有技能, 三份权威输入, 冻结产品, 全局部署; 未运行 `sync-to-pi.py`.

## 技能内容与覆盖

| 小节 | 覆盖 |
| --- | --- |
| 输入与授权 | 调用者材料与不变更冻结源码, 不取新权限 |
| 测量前 | AC-025: 先写对外结论, 读脚本的计时/计数/忽略项, 核对负载与核心数, 忙时交替并报噪声, 分析器单独跑 |
| 两侧按生产方式调优 | AC-026: 等价构建/配置/数据, 单侧默认是在比配置, 补调优后重测取该轮, 无权调优则无法下结论 |
| 重复与波动 | AC-026: 每侧至少 5 次交替, 中位数与极差, 差距小于波动判无可测差异, 接近时用工具统计或秩和检验, 不新建阈值 |
| 错误计数与工作是否真的发生 | AC-027: 计失败与非成功响应并核输出正确性, 只改授权实验脚本, 未消费生成器/未 await/计时区外计算判无法下结论, 需改冻结源码时只报缺口 |
| 判定 | 四种判定词与 "一律无法下结论" 的情形 |

按 ISSUE 的 TDD 切片分三次写入 (TS-001 -> TS-002 -> TS-003), 每次改完都跑机械检查.

## 每个 AC 的证据文件

- AC-025 (TS-001, TC-025): `evidence/ISSUE-06/TS-001.md`, 原始输出 `sessions/roundA-red.log` (红轮), `sessions/roundB-AC025.log` (绿轮).
- AC-026 (TS-002, TC-026): `evidence/ISSUE-06/TS-002.md`, 原始输出 `sessions/roundB-AC025.log` (红轮), `sessions/roundD-task1.log` 到 `roundD-task4.log` (绿轮).
- AC-027 (TS-003, TC-027): `evidence/ISSUE-06/TS-003.md`, 原始输出 `sessions/roundE-red-v2.log`, `roundE2-red-v2.log`, `roundE2-task2.log` (红轮, 未跑红), `sessions/roundF-task1.log` 到 `roundF-task3.log` (绿轮).

## 跑了哪些命令与退出码

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `uv run python general/writing-for-llm/check_skill.py workflow/benchmark-checklist/SKILL.md` | 0 | `OK` |
| `rg -n "[\x{ff0c}\x{3002}...]" workflow/benchmark-checklist` | 1 | 无命中 |
| 同上, 扫 `evidence/ISSUE-06/*.md` (我自己写的四份中文文档) | 1 | 无命中 |
| 同上, 扫 `evidence/ISSUE-06/sessions/**` | 0 | 有命中, 全部是被原样保留的会话原始输出与模型自己写的记录, 未改动 |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | 0 | 7 passed, 18 subtests |
| `uv run --with pytest python -m pytest -m "not e2e" -q` | 1 | 6 failed, 659 passed, 2 skipped, 103 deselected (275s). 失败全在 `general/present/tests/test_browser_session.py` (5 个) 与 `tests/test_mailbox_admin.py::test_pending_cap_drops_oldest` (1 个), 都是 socket/等待超时. 本次改动只新增 `workflow/benchmark-checklist/` 与 `evidence/ISSUE-06/`, 不涉及这两个模块; 但开工前没有记录基线快照, 所以这只是判断而非已验证的既有失败集合比对 |
| `git status --short` (收工) | 0 | 干净, 见提交哈希一节 |

## 会话与临时项目

- 临时项目: `/tmp/orchestra-06/`, 起始干净提交 `2b7f6dd` (夹具), 演练期间技能版本提交 `48d5ee1` (v1), `52229c9` (v2), `a018313` (v3). 夹具与受控脚本已按 `git archive` 原样复制到 `evidence/ISSUE-06/fixtures/`, 与工作树逐字节一致.
- 会话 (Herdr tab, 全部已关闭):

| 会话名 | 用途 | 结果 |
| --- | --- | --- |
| `bench-a` | 技能不存在时的红轮 | 无主张/无机器条件检查就给对外结论 |
| `bench-b` | 首次加载 v1 (只发 `/skill:` 未带任务) | 补充材料, 记 `sessions/roundB-skillload.log` |
| `bench-b2` | v1 绿轮, 机器上有他人负载 | AC-025 通过, 同时暴露 AC-026 单边默认档选赢家 (红轮) |
| `bench-d` | v2 绿轮, 四个任务 | AC-026 五个分支通过 |
| `bench-e` | v2 红轮两次尝试 | AC-027 未跑红, 如实记录 |
| `bench-f` | v3 绿轮, 三个任务 | AC-027 三个分支通过 |

- 加载方式: `/skill:benchmark-checklist <任务>`, 会话启动横幅 `[Skills]` 出现 `benchmark-checklist`; 宿主 Ubuntu 26.04, 16 核, Herdr 0.9.4, pi 1.3.0, 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`, 启动加 `-a`.
- 清理: 六个演练会话已 `herdr tab close`; 4 个充当 "他人任务" 的负载进程 (PID 3652207/3652208/3652210/3652211) 在演练结束后由我 kill, 已确认消失; `/tmp/orchestra-06/` 与 `/tmp/orchestra-06-evidence/` 保留到证据抄录完毕, 之后随临时目录一起可删 (夹具已入库).

## 缺口 / 风险 / 未验证项

1. AC-025-1 的主张落盘时序: 会话把结论写进记录首节, 但没有观察到 "先写主张再启动测量" 的严格顺序, 原始输出只能证明主张存在且排首位.
2. 分析器分支 ("分析器单独运行且该次数字不进报告") 只有技能文本覆盖, 演练场景没有引入 profiler, 没有运行观测.
3. AC-026-2/AC-026-3 的接近数值分支用的是 AC 给定的受控数值, 没有用临时脚本现场产出同量级接近数据.
4. TS-003 红轮未跑红: 该模型在缺 AC-027 规则时也自己做了错误计数与工作核验, 所以没有复现失败. 规则仍按 AC-027 写入并通过绿轮验证, 但 "规则改变行为" 这点在本模型上未被证明.
5. 已发现待补强: 会话在冻结源码场景里用 "按同一分布重新抽样" 估算失败行数 (`sessions/attachments-roundF/count_sync_rows.py`), 技能正文尚未禁止把重新抽样当实际计数. 本轮未改技能, 留给后续维护.
6. 限制因素 (AC-030), 收益上限, 端到端占比, 粗估例外, PR 单主数字, 基线与脚本固定前检查都属其他 ISSUE, 本技能未提前写.
7. `README.md` 技能索引未加 `benchmark-checklist` 行: 该文件不在 ISSUE-06 允许范围 (允许范围只有新建技能目录与证据目录), 留给覆盖 README 的节点统一处理.
8. 随附 MIT 许可文本与上游差异记录未在本包内: 按 ISSUE 说明由 ISSUE-13 统一补齐; 本包只记录来源固定 SHA, 取回命令, HTTP 200, 5002 字节与 sha256.

## 提交哈希

- 分支 `issue/06`, 提交见本文件所在提交之后的 `git log -1`.
