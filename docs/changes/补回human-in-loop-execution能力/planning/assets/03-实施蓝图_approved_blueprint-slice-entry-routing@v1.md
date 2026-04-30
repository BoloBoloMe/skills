asset_id: hilp-execution-capability-restoration-slice-entry-routing
artifact_name: stage-4-5/blueprint-slice-entry-routing
version: v1
state: approved
state_label: 已批准
owner_skill: hilp-blueprint
created_from: stage-3/design-choice@v1 [state=approved｜中文状态=已批准]
last_event: human-approval-granted
last_decision: human-approval-2026-04-29-approve-blueprint-package-v1
approval_marker: approved
approval_marker_label: 已批准

# 子蓝图：entry-routing

## 适用范围

本切片补强执行入口、路由、交接接收和 inline fallback 的边界纪律。

## 所属主蓝图

- `stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`

## 文件范围

- 修改：`human-in-loop-execution/SKILL.md`
- 修改：`human-in-loop-execution/README.md`
- 修改：`human-in-loop-execution/references/hilp-handoff-intake.md`
- 修改：`human-in-loop-execution/references/execution-routing.md`
- 修改：`human-in-loop-execution/references/executing-plans.md`

## 职责边界

- 只补强执行层入口和路由纪律。
- 不恢复 brainstorming、using-git-worktrees、using-superpowers 独立入口。
- 不补写 HILP 需求、设计、审批或蓝图职责。

## 具体改动约束

### `SKILL.md`

- 保留 frontmatter `name: human-in-loop-execution`。
- 在概览中增加一句：本技能补回的是执行强制门和抗误用细节，不接管 HILP 规划审批。
- 在资源加载顺序中强调：生产代码或行为变更先读 TDD；失败先读 systematic-debugging；完成声明先读 verification-before-completion；审查先读 code-review。
- 在路由规则中保留 HILP 重审回退优先级。

### `README.md`

- 在“保留能力”中增加：补回 Superpowers 对应执行技能的强制门、红旗、反误用规则和 prompt 校准。
- 在“明确不包含”中保留：不复制插件、hooks、commands、assets、历史 plans/specs、测试目录。

### `hilp-handoff-intake.md`

- 增加入口失败处理：资产状态、版本、执行范围、禁止越界项任一缺失时，只输出失败原因和回退阶段。
- 增加“不接受自然语言开工许可替代 asset_ref”的强制语句。

### `execution-routing.md`

- 增加路由优先级：HILP 资产校验、越界检查、当前任务状态、失败 / 审查 / 收尾触发。
- 增加禁止恢复被裁剪入口的说明。

### `executing-plans.md`

- 补回先审查计划再执行。
- 补回任务清单状态：pending、in_progress、completed、blocked。
- 补回停止条件：计划存在关键缺口、指令不清、验证失败、主分支风险、蓝图外文件需求。
- 补回完成后进入 code-review 和 verification-before-completion，再进入 finishing-branch。

## 局部风险检查点

- `SKILL.md` 不得新增 `using-git-worktrees` 独立入口。
- `execution-routing.md` 不得允许草稿或已批准资产进入执行。
- `executing-plans.md` 不得允许验证失败后继续声明完成。

## 局部验证命令

```bash
grep -R "brainstorming\|using-superpowers" human-in-loop-execution/SKILL.md human-in-loop-execution/references/execution-routing.md && exit 1 || true
grep -n "执行交接" human-in-loop-execution/references/hilp-handoff-intake.md
grep -n "验证失败" human-in-loop-execution/references/executing-plans.md
grep -n "blocked\|阻断" human-in-loop-execution/references/executing-plans.md
```

## 确定性检查

- 未确定项：无。
- 模糊表达：无。
- 需要执行者自行裁量的规划判断：无。
- 禁止越界项：不触碰 `superpowers/`。
