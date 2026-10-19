# ISSUE-04 交接报告

## 交付了什么

- 在既有 `workflow/verify-change/SKILL.md` 上增量补齐两个切片, 没有推翻 ISSUE-01/02/03 已实现部分:
  - AC-006 并行验收与证据共享: 第 4 步先分资源, 独立实例/端口/数据目录可同时开工, 只有争用同一实例或同一条记录的写入片段先后执行, 只读检查不受牵连; 派工计划写明每组操作, 共用准备执行人, 原始材料归属, 争用片段与先后依据; 共用准备只做一次. 第 5 步让可隔离组同时开始, 后一段写者等前一段完成通知再开始, 每段留执行顺序记录. 第 7 步允许共享原始材料, 但交出一方记产生者, 版本, 位置, 接收方自己核对适用范围后独立下结论, 不照抄. 第 8 步的派工记录增加共用准备, 原始材料归属, 各组起止时间, 争用顺序与共享材料字段.
  - AC-007 修复后复验: 新增"复验"一节. 绑新版本, 另开证据目录; 参与过修复的验收者或指挥者换掉, 旧证据只作材料; 按影响列出受影响项本轮实跑, 未受影响的旧观察复核适用性后才引用; 作者日志只当材料, 受影响关键路径由验收者本轮自己跑. 首次验收的会话可恢复也可新开, 调用方没选恢复就直接新开, 不阻塞也不沿用旧结论.
- 新增 `docs/changes/verification-skills/evidence/ISSUE-04/`: 夹具生成脚本, 2 个红演练, 2 次并行绿演练, 3 轮复验 (首次失败, 恢复复验, 不恢复复验), 会话原始记录, 说明与交接.
- 未改 `PRODUCT.md` / `TECHNICAL.md` / `DECISIONS.md` / 既有 Spec; 未改其他既有技能; 未写全局部署副本; 未运行 `sync-to-pi.py`; 未在 ISSUE 文件或 EXECUTION.md 勾选复选框; 没有改被验项目的产品代码.

## 每个验收标准对应证据

| 验收标准 | 证据文件 |
| --- | --- |
| AC-006-1 可隔离组真实并行, 计划含操作/共用准备/材料归属 | `drill-green-parallel/evidence-e398c7c-r1/plan.md`, `.../VERIFY-REPORT.md` (各可隔离组起止), `drill-green-parallel/runtime-shared/events.log`; 失败对照 `drill-red-parallel-load2/plan.md` |
| AC-006-2 争用片段先后且留顺序记录, 无关只读继续 | `drill-green-parallel-run1/evidence-773fc6b-r1/ver-beta/RESULT.md` (等标记后 append), `.../ver-alpha` 的 `coord/record-alpha-done.txt`; 修订版顺序记录 `drill-green-parallel/.../tail/order.md` 与报告"争用片段执行顺序记录"表 |
| AC-006-3 共享材料保留产生者/版本/位置, 各自独立结论 | `drill-green-parallel/.../VERIFY-REPORT.md` "共享材料的产生者 / 版本 / 位置 / 接收方"表, `.../tail/notes.md`; 失败对照 `drill-red-parallel-load2/verifier-g1/results-g1.md` |
| AC-007-1 复验绑新提交, 恢复或新开, 按影响重验并复核旧证据 | `drill-reverify-round2/VERIFY-REPORT.md` (绑 `5906913`, 影响范围, 旧证据适用性), `drill-reverify-round3/VERIFY-REPORT.md` 与 `PLAN.md` (不恢复分支), `drill-reverify-round1/VERIFY-REPORT.md` (首轮真实失败) |
| AC-007-2 参与修复者不再验收, 旧证据只作材料 | `drill-reverify-round2/VERIFY-REPORT.md` 第 6.1 节; 失败对照 `drill-red-reverify/verify-r1/verifier-b/REVERIFY-ad2ed33.md` |
| AC-007-3 调用方未选择恢复时新开非作者, 不阻塞, 不沿用旧结论 | `drill-reverify-round3/NOTES.md`, `.../VERIFY-REPORT.md`, `.../PLAN.md` |
| AC-007-4 作者日志只作材料, 关键路径非作者本轮实跑 | `drill-reverify-round2/VERIFY-REPORT.md` "复验重点: AC-003-1", `drill-reverify-author-materials/` |

## 跑了哪些命令与退出码

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md` | 0 | `OK` |
| 全角标点扫描 (SKILL.md + 我写的 37 个证据文件) | 0 | 无命中; 会话原始材料保留原样, 命中只在原始记录里 |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | 0 | 7 passed, 18 subtests passed |
| `uv run --with pytest python -m pytest -m "not e2e" -q` | 1 | `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed in 275.03s`; 失败集合与 `evidence/BASELINE.md` 完全一致 (present 5 条 + mailbox pending_cap 1 条), 未新增失败 |
| `bash setup-drills.sh init` / `rebuild-parallel` / `install-skill` / `reset-runtime` / `status` | 0 | 建 4 个夹具, 各带起始与目标提交; 实例清理后端口无监听 |
| `herdr tab create` / `agent start` / `pane send-text` / `agent send-keys` / `agent read` / `tab close` | 0 | 会话一览见 `README.md`; 收尾 `logs/agents-final.json` 无本 ISSUE 会话 |

## 会话与临时项目

- 有效会话: 红 `i04-r1`+`verify-relay-1`, `i04-r1c`+`i04-rp-v1`, `i04-r2`+`verify-g1`+`verify-g2`; 绿 `i04-g1b`+`ver-alpha/beta/read`, `i04-g1c`+`rev-alpha/beta/shared`, `i04-v1`+`i04-a1-ac`+`i04-a1-br`, 同 `i04-v1`+`i04-a2-ac`+`i04-a2-br`, `i04-v3`+`i04-a3-verify`. 会话 ID 与目录见 `README.md`.
- 作废: `i04-g1` (多行提交未触发 `/skill` 展开), `probe-skill-load` (单行加载探测), `i04-g1b` 首轮 (未出现共享材料, 转为 `drill-green-parallel-run1`).
- 临时项目: `/tmp/orchestra-04/{parallel,red-parallel,reverify,red-reverify}`, 起始与目标提交见 `README.md` 夹具表. 证据抄完后删除 (见"清理结果").
- 宿主与版本: Ubuntu 26.04, herdr 0.9.4, pi 1.3.0, Python 3.14.7; 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking high, 启动带 `-a`.

## 缺口与风险

1. **首版红演练加载方式偏差**: 红演练第一版任务是多行提交, 首行只有 `/skill:verify-change`, pi 没有展开技能命令, 模型自己读取了 `.agents/skills/verify-change/SKILL.md`. 这批会话保留在 `drill-red-parallel/` 与 `drill-red-reverify/`, 只作补充对照; TS-001 的主证据改用 `drill-red-parallel-load2/` (单行 `/skill` 点名, 记录里有 `<skill name=... location=...>`). TS-002 的红证据仍是首版会话, 所以它的"实际加载方式"是模型自读项目内文件, 不是点名加载; 这是本轮未补做的缺口.
2. **红演练收尾受宿主干扰**: `drill-red-parallel-load2` 的指挥者在收尾阶段反复找已退出会话, 操作者关闭了它的 tab; 结论只取已落盘的 `plan.md` 与 `verifier-g1/`. `drill-red-reverify` 的复验者等待已关闭会话 16 分钟, 操作者插话后才收尾; 这段等待本身是旧版行为证据.
3. **共享材料的必要性来自产品标准的交叉核对**: AC-005-1 要求两侧截图与 report 交叉一致, 才会出现"A 产出, B 引用"的材料移交. 这不是所有验收任务的常态, 本轮只证明技能在这种情形下保留产生者并要求接收方独立判断.
4. **争用证据分在两次运行**: 修订版夹具里两个追加片段由同一名验收者执行 (它是共享记录唯一写者), 跨验收者的先后用第一版夹具那轮 (`drill-green-parallel-run1`) 承接. 两次用的是同一夹具代码, 产品标准略有差异, 已在各自 NOTES 说明.
5. **复验演练的会话恢复由操作者完成**: "恢复原指挥会话"用的是仍在运行的同一 pi 会话; "已关闭会话"由操作者 `herdr tab close` 制造. 技能只规定何时恢复, 何时换人, 不规定恢复技术; 其他运行时的恢复方式未验证.
6. **宿主审批与外部关闭**: `i04-v3` 的验收者 pane 被操作者关闭后用同一 pi 会话恢复, 另有一次命令审批由操作者选"允许本次"; `drill-red-parallel-load2` 有一次全盘 `find` 审批被操作者取消. 都是宿主或操作问题, 不是技能行为结论.
7. **样本少**: 每个场景基本跑一次; 并行是否重叠依赖任务的真实耗时 (4 秒 job 与 1.2 秒写入窗口). 没有重复抽样, 不能说明成功率; 也没有测其他模型.
8. **未验证**: 其他运行时或全局部署下的加载与行为; tdd-as-orchestra 接入 (ISSUE-14); 需要更大规模并行的任务; 并发多写者下的记录一致性 (产品标准未要求, 未擅自加判).

## 提交哈希

- 实现与证据提交: 见本分支 `git log` 的 `feat: ISSUE-04` 提交; 本文件的该行由随后的 `docs: ISSUE-04` 提交补记.
