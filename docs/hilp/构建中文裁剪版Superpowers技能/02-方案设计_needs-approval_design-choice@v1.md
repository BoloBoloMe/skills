---
asset_id: hilp-superpowers-skills-design-choice
artifact_name: stage-3/design-choice
version: v1
state: ready-for-approval
state_label: 待审批
owner_skill: hilp-design-approval
created_from: stage-1-2/requirements-and-facts@v1
last_event: none
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批
asset_path: D:/Workspace/skills/docs/hilp/构建中文裁剪版Superpowers技能/02-方案设计_needs-approval_design-choice@v1.md
---

# 方案设计与审批阶段

## 这个阶段要做什么
比较可行裁剪方案，给出推荐路径，并明确哪些内容需要用户决定或批准。

## 推荐方案

### 名称
HILP 门控下的中文 Superpowers 执行层技能包。

### 核心思路
在 `superpowers-skills/` 中构建中文技能集合；保留 Superpowers 执行纪律和质量门，删除或改写会与 HILP 需求、方案、审批和蓝图冲突的部分。技能包不再以 Superpowers `brainstorming` 作为设计入口，而是以 HILP 执行交接资产为进入实现准备的唯一治理输入。

### 为什么推荐
- 与 `裁剪superpowers.md` 的边界完全一致：HILP 管“做什么、选哪种方案、是否批准、能否交接”，Superpowers 管“如何安全实现、如何测试、如何 review、如何收尾”。
- 避免双审批系统：不再同时维护 HILP 设计资产和 Superpowers design doc/spec approval。
- 保留源仓最有价值的执行机制：worktree 隔离、计划拆分、TDD、subagent 执行、inline fallback、code review、branch finish、系统调试与完成前验证。
- 中文化后更适配当前仓库与用户交互；frontmatter 名称仍保持 ASCII/hyphen，以减少不同 agent skill loader 的兼容风险。

## 推荐保留与改造边界

### 保留并中文化的执行主链路
- `using-git-worktrees`：保留为执行交接后的隔离工作区准备。
- `writing-plans`：改造为“从 HILP 已批准蓝图与执行交接资产机械拆分执行计划”，不得重新设计。
- `subagent-driven-development`：保留为默认执行编排，subagent prompt 必须引用 HILP 执行交接资产和禁止越界项。
- `executing-plans`：保留为无 subagent 或任务紧耦合时的 fallback。
- `test-driven-development`：保留为每个实现 task 的强制 TDD 纪律。
- `requesting-code-review` / `receiving-code-review`：保留为执行层代码质量 gate 与 review 反馈处理。
- `finishing-a-development-branch`：保留为分支、PR、worktree 清理的收尾流程，并要求出现偏差或新事实时回到 HILP 重审。

### 保留为执行安全与质量辅助能力
- `systematic-debugging`：保留，用于 bug、失败测试和异常行为的根因调查；不得越过 HILP 去改设计边界。
- `verification-before-completion`：保留，用于所有完成声明前的证据验证。
- `dispatching-parallel-agents`：保留，用于多个互不干扰问题域的并行执行或调查；必须受执行交接范围约束。
- `writing-skills`：保留为元技能，仅在创建或修改技能时启用；不进入普通业务开发主链路。

### 删除或降级的源仓能力
- 删除独立 `brainstorming` 入口：其上下文探索和多方案比较思想已由 HILP 需求事实与方案审批阶段承接。
- 删除 Superpowers design doc 作为正式源文档的地位：正式源文档只认 HILP 资产链。
- 删除 Superpowers spec approval gate：正式批准只认 HILP 对具体 `asset_ref` / version 的 Human Approval Granted。
- 不复制源仓插件分发、hooks、commands、assets、历史 plans/specs 和上游贡献规则，除非后续蓝图明确将其中某个文件作为本地技能包支持文件。

## 备选方案

### 方案 A：最小执行主链路包
- 核心思路：只保留 `using-git-worktrees`、`writing-plans`、`subagent-driven-development`、`executing-plans`、`test-driven-development`、`requesting-code-review`、`finishing-a-development-branch`。
- 优点：范围最小，写作和审查成本低。
- 代价：缺少系统调试、完成前验证、review 接收和技能编写纪律；执行中遇到失败或需要维护技能时会回到 ad-hoc 行为。
- 不选原因：用户要求“详细分析 superpowers/ 下的内容”，而源仓中执行质量相关技能与主链路高度互补；最小包过度裁剪。

### 方案 B：完整中文翻译 fork
- 核心思路：把 `superpowers/` 的技能、插件、hooks、commands、docs、tests 基本全量中文化，并在冲突处补充 HILP 注释。
- 优点：保留源仓完整生态，迁移成本低。
- 代价：会重新引入 `brainstorming`、spec approval、全局 using-superpowers 强制入口等与 HILP 冲突的治理逻辑；也会复制大量当前仓库不需要的插件分发和测试资产。
- 不选原因：与 `裁剪superpowers.md` 的核心判断冲突，容易形成双审批和双入口。

### 方案 C：只写 README/说明，不创建技能包
- 核心思路：用一份中文文档描述如何在 HILP 后使用原始 Superpowers 技能。
- 优点：改动最少。
- 代价：不会形成可复用技能；无法通过 skill 触发语义强制执行 HILP 边界、TDD、review 和禁止越界项。
- 不选原因：用户明确要求在仓库根目录构建 `superpowers-skills`。

## 关键取舍
- 正确性 / 安全性：选择 HILP 作为唯一规划治理源，牺牲 Superpowers 原始“从创意开始”的完整闭环，避免审批状态混乱。
- 可回退性：新增独立目录，不修改 `superpowers/` 源仓；如方案不满意，可删除新目录或重建，不影响已有技能。
- 改动范围：比最小包更大，但比完整翻译 fork 小得多；聚焦执行层技能和必要元技能。
- 可维护性：中文技能以 HILP 边界为顶层契约，后续维护时可按技能逐个更新，不需要追随上游插件分发结构。
- 未来扩展性：保留 `writing-skills` 元技能与 README 安装说明，后续可以增加压力测试或 harness-specific 安装适配，而不改变主链路。

## 需要用户决定什么
- 是否存在：建议人工裁决。
- 是否会阻止继续：无阻断项；若用户未特别选择，默认采用推荐方案。
- 问题描述：是否接受“完整执行层技能包”作为裁剪粒度，并保留调试、验证、review 接收、并行 agent 和 writing-skills 等辅助技能。
- 可选项：
  1. 采用推荐方案：完整执行层技能包。
  2. 改为方案 A：最小执行主链路包。
  3. 改为方案 B：完整中文翻译 fork。
  4. 改为方案 C：只写说明文档。
- 建议：采用推荐方案。
- 默认路径：采用推荐方案，因为它满足 HILP 边界、保留执行质量，并避免复制无关插件生态。
- 用户是否已选择：未选择。
- 不得写成既定事实的内容：在用户批准前，不得声称用户已同意保留 `writing-skills` 或已同意某个安装发现方式。

## 当前状态
- 中文状态名：待审批。
- 内部状态值：`ready-for-approval`。
- 进入该状态的理由：目标、范围、成功标准、源仓事实和影响面已建立；不存在阻断性的必须人工裁决；推荐方案和备选方案已足以提交人工审批。

## 下一步
- 下一阶段：等待用户明确批准本资产版本后，才能进入实施蓝图阶段。
- 继续前提：用户需要明确批准 `stage-3/design-choice@v1 [state=ready-for-approval｜中文状态=待审批]`。例如：“批准 02-方案设计_needs-approval_design-choice@v1，采用推荐方案”。
- 当前阻断项：无阻断项；但没有人工批准前，不能进入实施蓝图或开始构建 `superpowers-skills/`。