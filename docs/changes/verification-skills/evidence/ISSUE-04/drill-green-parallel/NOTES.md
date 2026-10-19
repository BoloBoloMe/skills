# drill-green-parallel: 并行执行与共享原始证据 (绿, AC-006-1 / AC-006-3)

## 目的

验证改动后的 `workflow/verify-change/SKILL.md` (md5 `82cb7913d710dfaf3b898c56d17c618c`) 在可隔离资源上真的并行, 并在两名验收者需要同一份材料时保留产生者, 版本, 位置, 由接收方自行核对适用性后独立下结论.

## 待测版本与加载方式

- 源文件: 工作树 `workflow/verify-change/SKILL.md`, 原件 `../logs/SKILL-v3-green.md`.
- 加载方式: 复制到 `/tmp/orchestra-04/parallel/.agents/skills/verify-change/`, 新 pi 会话用 `/skill:verify-change <任务>` 点名加载. 会话记录首条用户消息含 `<skill name="verify-change" location="/tmp/orchestra-04/parallel/.agents/skills/verify-change/SKILL.md">`, 见 `../sessions/green-parallel/` 中指挥者会话.
- 源文件与提交: 夹具目标提交 `e398c7cc7ca4e493d23689bee3cca1a34d306000`, 产品标准 `docs/changes/relay-board/PRODUCT.md`.

## 夹具

- 路径: `/tmp/orchestra-04/parallel` (建立方式见 `../setup-drills.sh` 的 `rebuild-parallel`), 起始提交 `b2d3aed`, 目标提交 `e398c7c`.
- 两个实例各自独立: alpha 在 127.0.0.1:18101 与 `runtime/alpha`, beta 在 18102 与 `runtime/beta`; 共享目录 `runtime/shared/` 放 `record.jsonl` 与 `events.log`.
- 产品标准: 8 个场景 + 2 条审计 BR. AC-001-1 与 AC-005-1 都需要 alpha/beta 两侧的状态页截图与 report 输出.

## 会话

| 角色 | 会话名 | pi session id | 创建 (CST) |
| --- | --- | --- | --- |
| 指挥者 | `i04-g1c` | 见 `../sessions/green-parallel/` 与报告名册 | 2026-10-19T22:12:2x |
| alpha 组 | `rev-alpha` | `01a15483-3add-74a0-a077-1b434d6cb4d0` | 22:14:08 |
| beta 组 | `rev-beta` | `01a15483-4f6f-70ee-ab4b-8bb426dba77c` | 22:14:14 |
| 共享记录与尾部只读组 | `rev-shared` | `01a15483-642c-73fc-8bda-578e542ac6d6` | 22:14:19 |

## 实际结果

- 计划 (`evidence-e398c7c-r1/plan.md`) 写明: 组划分与并行标记, 共用准备 (两个实例各由本组启动) 与原始材料归属, 争用对象与先后依据, 人数 3 = min(3 组, 可用 3).
- 并行: 三组创建时间 22:14:08/14/19; 报告 `### 各可隔离组的开始与结束` 记 G1 22:14:58 起, G2 22:15:03 起, G3 22:15:03.7 起; 产品事件日志显示 beta 的 4 秒 job (14:15:12.59-14:15:16.59) 与 alpha 侧 append (14:15:14.38) 真实重叠 (`../drill-green-parallel/runtime-shared/events.log`).
- 争用: 共享记录由 rev-shared 一段一段写, AC-003-1 (22:15:13.13-14.39, seq=1) 先于 AC-003-2 (22:15:16.45-17.72, seq=2), 顺序记录见 `tail/order.md` 与报告"争用片段执行顺序记录"表; 跨验收者的两段写同一记录见 `drill-green-parallel-run1`.
- 共用准备: alpha 实例由 rev-alpha 启动与停止, beta 实例由 rev-beta 启动与停止, 未各自重做; 报告"共用准备与原始材料归属"节逐条列出.
- 共享材料: AC-001-1 在 alpha 组产出截图与 report, AC-005-1 由 rev-shared 承接. 报告"共享材料的产生者 / 版本 / 位置 / 接收方"表逐项记录产生者会话, 版本 e398c7c/relay-v1, 位置与接收方 rev-shared 22:17:08 的适用性核对; rev-shared 自己判读两张 PNG, 并另跑 health/report 做旁证, 没有照抄 alpha/beta 组的结论.

## 结论

- AC-006-1 通过: 可隔离的两组真实并行, 各有自己的开始与结束时间与观察结果; 派工计划写明每组操作, 共用准备执行人, 原始材料归属.
- AC-006-3 通过: 共享材料保留产生者, 版本, 位置; 接收方自行核对适用范围并独立给出结论.
- 不覆盖: 并发多写者下的记录一致性 (产品标准没有这条要求, 未擅自加判).

## 限制

- 本轮 AC-003 的两个追加片段由同一名验收者执行 (它同时是共享记录的唯一写者), 因此"跨验收者两段写同一记录"的行为证据用同夹具的另一次运行 `drill-green-parallel-run1` 承接.
- 早前一次运行 (`drill-green-parallel-run1`) 使用的产品标准把 AC-001-1 定为文本 status 输出, AC-005-1 只涉及 alpha; 该次没有出现跨组共享材料, 所以本目录改用修订后的标准重跑.
