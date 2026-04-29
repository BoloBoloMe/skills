---
asset_id: hilp-superpowers-skills-blueprint-slice-execution-protocol
artifact_name: stage-4-5/blueprint-slice-execution-protocol
version: v1
state: ready-for-approval
state_label: 待审批
owner_skill: hilp-blueprint
created_from: stage-4-5/implementation-blueprint@v1
last_event: none
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批
asset_path: D:/Workspace/skills/docs/hilp/构建中文裁剪版Superpowers技能/03-实施蓝图_needs-approval_blueprint-slice-execution-protocol@v1.md
blueprint_form: package-slice
parent_blueprint: stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]
---

# 实施蓝图切片：执行主协议

## 职责边界
写入 HILP 执行交接后的主执行链路规则，包括执行入口检查、计划拆分、执行编排、TDD、代码审查、review 反馈处理和分支收尾。

## 前置依赖
- `package-structure` 切片已创建目录。

## 禁止越界项
- 不重新定义需求、设计或蓝图。
- 不把 HILP 待审批资产当作已批准资产。
- 不允许执行者自行补齐蓝图缺口。
- 不恢复 Superpowers brainstorming 或 spec approval。
- 不要求或创建 worktree。

## 涉及文件范围
创建并写入：
- `human-in-loop-execution/references/execution-routing.md`
- `human-in-loop-execution/references/hilp-handoff-intake.md`
- `human-in-loop-execution/references/writing-plans.md`
- `human-in-loop-execution/references/subagent-driven-development.md`
- `human-in-loop-execution/references/executing-plans.md`
- `human-in-loop-execution/references/test-driven-development.md`
- `human-in-loop-execution/references/code-review.md`
- `human-in-loop-execution/references/finishing-branch.md`

修改：
- `human-in-loop-execution/SKILL.md`，补齐资源加载顺序、阶段名、路由规则和参考文件列表。

## 数据形状
`execution-routing.md` 固定包含阶段名映射：
```text
执行入口检查阶段
执行计划阶段
subagent 执行阶段
inline 执行阶段
TDD 实现阶段
代码审查阶段
review 反馈处理阶段
分支收尾阶段
HILP 重审回退
```

`hilp-handoff-intake.md` 固定要求输入：
```text
stage-3/design-choice@vN [state=approved｜中文状态=已批准]
stage-4-5/implementation-blueprint@vM [state=approved｜中文状态=已批准]
stage-6/execution-handoff@vK [state=<state>｜中文状态=<state_label>]
执行入口检查：无阻断项
当前工作区：用户指定的执行工作区
```

`writing-plans.md` 固定输出计划路径：
```text
docs/human-in-loop-execution/plans/<yyyy-mm-dd>-<任务概括>.md
```
计划头固定引用 HILP 资产：
```text
HILP design asset_ref:
HILP blueprint asset_ref:
HILP execution handoff asset_ref:
禁止越界项:
```

## 接口约束
- `writing-plans.md` 只能把已批准蓝图机械拆分成任务，不得新增方案选择。
- `subagent-driven-development.md` 的每个 subagent prompt 必须包含 HILP 执行交接 asset_ref 和禁止越界项。
- `executing-plans.md` 是 fallback，仅在无 subagent、任务强耦合或平台不支持多 agent 时使用。
- `test-driven-development.md` 保留 RED-GREEN-REFACTOR 铁律：无失败测试，不写生产代码。
- `code-review.md` 合并 requesting 与 receiving 规则：请求 review、按 Critical/Important/Minor 处理、外部反馈先验证再实现。
- `finishing-branch.md` 在执行偏差、新事实或蓝图错误出现时必须停止收尾并要求回到 HILP 重审。

## 局部算法骨架
1. 在 `SKILL.md` 中写入入口检查：缺少 HILP 已批准资产或执行交接时，停止并要求回到 HILP。
2. 写入 `execution-routing.md`：根据任务处于计划、执行、审查、反馈、收尾或故障状态选择对应 reference。
3. 写入 `hilp-handoff-intake.md`：定义最小输入契约和禁止入口情形。
4. 写入 `writing-plans.md`：将 Superpowers planning 降级为 HILP 蓝图转执行任务。
5. 写入 `subagent-driven-development.md` 与 `executing-plans.md`。
6. 写入 `test-driven-development.md`。
7. 写入 `code-review.md`。
8. 写入 `finishing-branch.md`。

## 错误处理要求
- 若执行输入缺少 approved 设计或 approved 蓝图，输出“不能进入执行，需回到 HILP 方案设计或实施蓝图”。
- 若执行交接入口检查不是“无阻断项”，输出“不能进入执行，需回到 HILP 执行交接或变更重审”。
- 若执行中发现蓝图无法实施，输出“停止执行，回到 HILP 变更重审”。

## 测试承诺
- grep 检查 `执行交接`、`已批准`、`禁止越界项` 在主执行链路文件中出现。
- grep 检查 `using-git-worktrees` 不作为文件路径存在。
- grep 检查 `brainstorming` 不作为独立技能入口存在。

## 局部确定性检查
- 未确定项：无。
- 模糊表达：无。
- 需要执行者自行裁量的实现决策：无。