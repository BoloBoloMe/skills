---
asset_id: hilp-superpowers-skills-blueprint-manifest
artifact_name: stage-4-5/implementation-blueprint
version: v1
state: ready-for-approval
state_label: 待审批
owner_skill: hilp-blueprint
created_from: stage-3/design-choice@v3 [state=approved｜中文状态=已批准]
last_event: none
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批
asset_path: D:/Workspace/skills/docs/hilp/构建中文裁剪版Superpowers技能/03-实施蓝图_needs-approval_implementation-blueprint@v1.md
blueprint_form: package
---

# 实施蓝图阶段

## 这个阶段要做什么
把已批准的 `human-in-loop-execution` 方案转成确定、唯一、可执行的改动切片、顺序、约束和验证检查点。

## 已保存资产
- asset_ref：`stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`
- 蓝图形式：分层蓝图包。
- 上游设计：`stage-3/design-choice@v3 [state=approved｜中文状态=已批准]`
- 当前是否需要审批：需要用户明确批准当前蓝图包固定版本集合。

## 分层蓝图包 manifest

### 包内资产清单
- `stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`，role: manifest。
- `stage-4-5/blueprint-slice-package-structure@v1 [state=ready-for-approval｜中文状态=待审批]`，role: slice。
- `stage-4-5/blueprint-slice-execution-protocol@v1 [state=ready-for-approval｜中文状态=待审批]`，role: slice。
- `stage-4-5/blueprint-slice-quality-and-meta@v1 [state=ready-for-approval｜中文状态=待审批]`，role: slice。
- `stage-4-5/coverage-matrix@v1 [state=ready-for-approval｜中文状态=待审批]`，role: coverage-matrix。

### 切片索引
1. `package-structure`：创建 `human-in-loop-execution/` 的目录、入口文档、README 与仓库根 README 登记。
2. `execution-protocol`：写入 HILP 执行交接后的主执行链路规则，包括计划拆分、subagent 执行、inline fallback、TDD、代码审查和分支收尾。
3. `quality-and-meta`：写入根因调试、完成前验证、并行 agent、技能编写元纪律和支持 prompt/reference 文件。

### 跨切片依赖图 / 波次
- 第 1 波：`package-structure`。
- 第 2 波：`execution-protocol`，依赖第 1 波目录已存在。
- 第 3 波：`quality-and-meta`，依赖第 1 波目录已存在。
- 第 4 波：根 README 登记与验证，依赖第 1 至第 3 波文件全部落盘。

### 审批边界
本次蓝图审批精确覆盖 manifest 和以下成员的 v1 固定集合：
- `blueprint-slice-package-structure@v1`
- `blueprint-slice-execution-protocol@v1`
- `blueprint-slice-quality-and-meta@v1`
- `coverage-matrix@v1`

## 全局实现约束
- 新目录固定为 `human-in-loop-execution/`。
- 入口技能固定为单一顶层 `human-in-loop-execution/SKILL.md`，内部使用 references 组织执行单元，呼应 `human-in-loop-planning/` 的单协议结构。
- 中文为主体语言；frontmatter 的 `name` 固定为 `human-in-loop-execution`。
- 不创建 `superpowers-skills/`。
- 不创建 `human-in-loop-execution/skills/using-git-worktrees` 或任何 worktree 技能入口。
- 不创建独立 `brainstorming` 技能入口。
- 不创建原始 `using-superpowers` 的全局强制入口。
- 不复制 `superpowers/` 的插件、hooks、commands、assets、历史 plans/specs、测试目录和上游贡献规则。
- 技能包不假设仓库内 skill 会被 agents 自动发现；README 只说明“由用户按目标 agent 安装”。
- 所有执行规划必须绑定 HILP 执行交接资产；缺少已批准蓝图或执行交接时，技能只能要求回到 HILP，不能补做设计。

## 全局文件范围
创建：
- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/README.md`
- `human-in-loop-execution/references/execution-routing.md`
- `human-in-loop-execution/references/hilp-handoff-intake.md`
- `human-in-loop-execution/references/writing-plans.md`
- `human-in-loop-execution/references/subagent-driven-development.md`
- `human-in-loop-execution/references/executing-plans.md`
- `human-in-loop-execution/references/test-driven-development.md`
- `human-in-loop-execution/references/code-review.md`
- `human-in-loop-execution/references/finishing-branch.md`
- `human-in-loop-execution/references/systematic-debugging.md`
- `human-in-loop-execution/references/verification-before-completion.md`
- `human-in-loop-execution/references/dispatching-parallel-agents.md`
- `human-in-loop-execution/references/writing-skills.md`
- `human-in-loop-execution/references/prompt-templates/implementer-prompt.md`
- `human-in-loop-execution/references/prompt-templates/spec-reviewer-prompt.md`
- `human-in-loop-execution/references/prompt-templates/code-quality-reviewer-prompt.md`
- `human-in-loop-execution/references/prompt-templates/code-reviewer.md`
- `human-in-loop-execution/references/prompt-templates/plan-document-reviewer-prompt.md`
- `human-in-loop-execution/references/testing-anti-patterns.md`
- `human-in-loop-execution/references/root-cause-tracing.md`
- `human-in-loop-execution/references/defense-in-depth.md`
- `human-in-loop-execution/references/condition-based-waiting.md`

修改：
- `README.md`，在目录结构和技能一览中登记 `human-in-loop-execution/`。

不修改：
- `superpowers/` 下任何文件。
- `human-in-loop-planning/` 下任何文件。
- `cz-sdk-windows-build/` 下任何文件。

## 全局数据形状
每个 reference 文件使用以下固定结构：
```text
# <中文标题>

## 适用时机
## 输入契约
## 执行规则
## 禁止事项
## 输出契约
## 检查清单
```

`SKILL.md` 使用以下固定结构：
```text
---
name: human-in-loop-execution
description: Use when HILP execution handoff has been approved and implementation, testing, review, debugging, or branch finishing needs execution discipline
---

# 人在回路执行
## 概览
## 入口前提
## 阶段名称
## 资源加载顺序
## 路由规则
## HILP 绑定纪律
## 输出纪律
## 参考文件
```

## 全局接口约束
- 对 HILP 资产引用统一使用：`asset_ref: <stage>/<artifact>@vN [state=<state>｜中文状态=<state_label>]`。
- 执行入口必须要求：已批准设计资产、已批准蓝图资产、执行交接资产和执行入口检查“无阻断项”。
- 执行中发现蓝图错误、新事实、越界需求、回滚风险或审批缺失时，输出必须停止执行并要求回到 HILP 变更重审。

## 风险检查点
- 检查点 1：文件创建前确认不存在 `human-in-loop-execution/`；若存在，停止并报告冲突。
- 检查点 2：写入后确认未创建 `superpowers-skills/`。
- 检查点 3：写入后确认未创建 `using-git-worktrees`、`brainstorming`、`using-superpowers` 三类独立入口文件。
- 检查点 4：写入后确认 `README.md` 不声称仓库内 skills 会自动发现。
- 检查点 5：写入后确认所有执行链路文档均要求绑定 HILP 执行交接资产。

## 发布 / 验证检查点
执行完成后运行以下命令：
```bash
test -d human-in-loop-execution
test -f human-in-loop-execution/SKILL.md
test -f human-in-loop-execution/README.md
test -f human-in-loop-execution/references/writing-plans.md
test -f human-in-loop-execution/references/test-driven-development.md
test -f human-in-loop-execution/references/prompt-templates/code-reviewer.md
test ! -e superpowers-skills
test ! -e human-in-loop-execution/skills/using-git-worktrees
test ! -e human-in-loop-execution/skills/brainstorming
grep -q '^name: human-in-loop-execution$' human-in-loop-execution/SKILL.md
grep -q '执行交接' human-in-loop-execution/SKILL.md
grep -q 'human-in-loop-execution' README.md
```

## 确定性检查
- 未确定项：无。
- 模糊表达：无。
- 分支待选方案：无。
- 需要执行者自行裁量的实现决策：无。
- 分层蓝图包成员检查：manifest、三个子蓝图和覆盖矩阵均已固定为 v1，且相互引用一致。

## 当前判断
- 当前是否可交接到执行层：否。蓝图包当前为待审批，不是已批准。
- 当前阻断项：无阻断项；但缺少对当前蓝图包固定版本集合的明确批准。
- 是否存在兼容 / 回滚约束：无运行时兼容窗口；回退方式为删除新增 `human-in-loop-execution/` 并还原 `README.md` 修改。
- 当前状态：待审批（`ready-for-approval`）。

## 下一步需要用户做什么
请明确批准当前蓝图包固定版本集合，才能进入执行交接阶段。批准语句需绑定：
`implementation-blueprint@v1`、`blueprint-slice-package-structure@v1`、`blueprint-slice-execution-protocol@v1`、`blueprint-slice-quality-and-meta@v1`、`coverage-matrix@v1`。