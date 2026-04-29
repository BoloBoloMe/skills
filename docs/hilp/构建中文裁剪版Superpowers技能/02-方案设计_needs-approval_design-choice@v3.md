---
asset_id: hilp-superpowers-skills-design-choice
artifact_name: stage-3/design-choice
version: v3
state: ready-for-approval
state_label: 待审批
owner_skill: hilp-design-approval
created_from: stage-reapproval/reapproval-decision@v2
last_event: naming-guidance-before-approval
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批
asset_path: D:/Workspace/skills/docs/hilp/构建中文裁剪版Superpowers技能/02-方案设计_needs-approval_design-choice@v3.md
replaces: stage-3/design-choice@v2 [state=needs-revision｜中文状态=待修订]
---

# 方案设计与审批阶段

## 这个阶段要做什么
根据用户的命名族建议修订方案名称，重新形成可审批的设计版本。

## 推荐方案

### 名称
Human-in-loop 执行技能包。

### 推荐目录名
`human-in-loop-execution/`

### 核心思路
在仓库根目录构建 `human-in-loop-execution/`：一个中文化、受 `human-in-loop-planning/` 执行交接约束的执行层技能包。它来源于 Superpowers 的裁剪和汉化，但不使用 `superpowers-skills` 命名，不保留 Superpowers 的设计审批入口，不假设仓库内技能会被 agents 自动发现，也不保留 `using-git-worktrees`。

### 为什么推荐
- 与现有 `human-in-loop-planning/` 构成清晰命名对：`planning` 负责规划治理，`execution` 负责执行纪律。
- `execution` 比 `implementation` 更贴近 HILP 的“执行交接”语义：它覆盖计划执行、TDD、review、验证和分支收尾，而不仅是写代码。
- `human-in-loop-` 前缀表达同一协议族，避免误解为 Superpowers 的完整翻译 fork。
- 名称短、稳定、可扩展，后续若出现归档、评审或发布相关技能，也能保持同一命名体系。

## 修订后的保留与改造边界

### 保留并中文化的执行主链路
- `writing-plans`：改造为“从 HILP 已批准蓝图与执行交接资产机械拆分执行计划”，不得重新设计。计划输出应引用 HILP `execution-handoff`、已批准蓝图和禁止越界项。
- `subagent-driven-development`：保留为默认执行编排；subagent prompt 必须引用 HILP 执行交接资产和禁止越界项。
- `executing-plans`：保留为无 subagent、任务强耦合或当前平台不支持多 agent 时的 fallback。
- `test-driven-development`：保留为每个实现 task 的强制 TDD 纪律。
- `requesting-code-review` / `receiving-code-review`：保留为执行层代码质量 gate 与 review 反馈处理。
- `finishing-a-development-branch`：保留为分支、PR、worktree 清理或保留决策的收尾流程；若执行偏离蓝图或发现新事实，必须回到 HILP 重审。

### 保留为执行安全与质量辅助能力
- `systematic-debugging`：保留，用于 bug、失败测试和异常行为的根因调查；不得越过 HILP 改设计边界。
- `verification-before-completion`：保留，用于所有完成声明前的证据验证。
- `dispatching-parallel-agents`：保留，用于多个互不干扰问题域的并行执行或调查；必须受执行交接范围约束。
- `writing-skills`：保留为元技能，仅在创建或修改技能时启用；不进入普通业务开发主链路。

### 明确删除或不纳入的能力
- 不纳入 `brainstorming`：其需求探索、多方案比较、设计审批和 design doc 写入由 HILP 承接。
- 不纳入 `using-git-worktrees`：用户通常已在 HILP 前手动创建 worktree；技能包只要求执行者确认当前目录就是用户指定的执行工作区。
- 不纳入原始 `using-superpowers` 的“任意响应前强制使用 Superpowers skill”模式：会与 HILP 和当前 agent harness 的技能治理冲突。
- 不复制 Superpowers design doc / spec approval gate：正式源文档只认 HILP 资产链。
- 不复制源仓插件分发、hooks、commands、assets、历史 plans/specs、测试仓库和上游贡献规则。
- 不要求仓库内 skill 被 agents 自动发现：本仓库只保存技能源；真实使用时由用户触发安装。

## 命名备选方案

### 方案 A：`human-in-loop-implementation/`
- 核心思路：强调实现代码。
- 优点：与开发实现直接相关。
- 代价：范围偏窄，不能自然覆盖 code review、验证、分支收尾和执行偏差回写。
- 不选原因：本包职责是执行层全流程，不只是 implementation。

### 方案 B：`human-in-loop-delivery/`
- 核心思路：强调交付与收尾。
- 优点：覆盖 PR、merge、完成验证等后段工作。
- 代价：弱化 TDD、计划执行和调试等中段执行纪律。
- 不选原因：delivery 更像发布/交付阶段，不如 execution 与 planning 对称。

### 方案 C：`human-in-loop-development/`
- 核心思路：强调开发活动。
- 优点：覆盖面较宽。
- 代价：development 容易重新包含需求、设计、实现全流程，边界不如 execution 清晰。
- 不选原因：会弱化 HILP 已接管 planning 的事实。

## 关键取舍
- 正确性 / 安全性：使用 `execution` 明确技能包只能在 HILP 执行交接之后工作，不能回头接管 planning。
- 可回退性：新增独立 `human-in-loop-execution/`，不修改 `superpowers/` 源仓。
- 改动范围：继续删除 worktree 技能和自动发现假设。
- 可维护性：与 `human-in-loop-planning/` 并列，便于仓库中按“规划 / 执行”维护技能族。
- 未来扩展性：后续可围绕 `human-in-loop-*` 增加其他协议族技能，但当前仅新增 execution。

## 需要用户决定什么
- 是否存在：建议人工裁决。
- 是否会阻止继续：无阻断项；若用户未提出其他名称，默认推荐 `human-in-loop-execution/`。
- 问题描述：是否接受推荐的新名称与裁剪边界。
- 可选项：
  1. 采用推荐方案：目录名 `human-in-loop-execution/`。
  2. 改用 `human-in-loop-implementation/`。
  3. 改用 `human-in-loop-delivery/`。
  4. 改用 `human-in-loop-development/`。
  5. 用户指定其他 `human-in-loop-*` 名称。
- 建议：采用 `human-in-loop-execution/`。
- 默认路径：采用 `human-in-loop-execution/`，因为它与 `human-in-loop-planning/` 在层次和职责上最直接呼应。
- 用户是否已选择：未选择。
- 不得写成既定事实的内容：在用户批准前，不得声称用户已接受 `human-in-loop-execution/` 名称。

## 当前状态
- 中文状态名：待审批。
- 内部状态值：`ready-for-approval`。
- 进入该状态的理由：新命名约束已吸收；目标、范围、成功标准、保留/删除清单和推荐名称已重新收敛；不存在阻断性的必须人工裁决。

## 下一步
- 下一阶段：等待用户明确批准本资产版本后，才能进入实施蓝图阶段。
- 继续前提：用户需要明确批准 `stage-3/design-choice@v3 [state=ready-for-approval｜中文状态=待审批]`，并接受或替换推荐目录名。
- 当前阻断项：无阻断项；但没有人工批准前，不能进入实施蓝图或开始构建目录。