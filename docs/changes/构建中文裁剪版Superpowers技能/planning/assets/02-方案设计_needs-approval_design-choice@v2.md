---
asset_id: hilp-superpowers-skills-design-choice
artifact_name: stage-3/design-choice
version: v2
state: ready-for-approval
state_label: 待审批
owner_skill: hilp-design-approval
created_from: stage-reapproval/reapproval-decision@v1
last_event: new-facts-before-approval
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批
asset_path: D:/Workspace/skills/docs/changes/构建中文裁剪版Superpowers技能/planning/assets/02-方案设计_needs-approval_design-choice@v2.md
replaces: stage-3/design-choice@v1 [state=needs-revision｜中文状态=待修订]
---

# 方案设计与审批阶段

## 这个阶段要做什么
根据用户新增事实修订裁剪方案，重新形成可审批的设计版本。

## 推荐方案

### 名称
HILP 后执行技能包。

### 推荐目录名
`hilp-execution-skills/`

### 核心思路
在仓库根目录构建 `hilp-execution-skills/`：一个中文化、受 HILP 执行交接约束的执行层技能包。它来源于 Superpowers 的裁剪和汉化，但不使用 `superpowers-skills` 命名，不保留 Superpowers 的设计审批入口，不假设仓库内技能会被 agents 自动发现，也不保留 `using-git-worktrees`。

### 为什么推荐
- 名称表达真实定位：这是 HILP 批准和执行交接之后的执行纪律包，而不是 Superpowers 的完整复制或品牌化 fork。
- 与用户使用习惯一致：用户通常在 HILP 前已经手动创建 worktree，因此不重复提供 worktree 技能。
- 与仓库定位一致：当前仓库是 skill 管理仓库，不要求新增目录立即被 agents 自动发现；安装方式只需作为文档说明。
- 与 `裁剪superpowers.md` 一致：HILP 继续接管需求、方案、审批、蓝图和交接；该技能包只服务执行准备、TDD、review、验证和收尾。

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
- 不纳入 `using-git-worktrees`：用户通常已在 HILP 前手动创建 worktree；技能包只要求执行者确认当前工作区就是用户指定的执行工作区。
- 不纳入原始 `using-superpowers` 的“任意响应前强制使用 Superpowers skill”模式：会与 HILP 和当前 agent harness 的技能治理冲突。
- 不复制 Superpowers design doc / spec approval gate：正式源文档只认 HILP 资产链。
- 不复制源仓插件分发、hooks、commands、assets、历史 plans/specs、测试仓库和上游贡献规则。
- 不要求仓库内 skill 被 agents 自动发现：本仓库只保存技能源；真实使用时由用户触发安装。

## 备选方案

### 方案 A：目录名 `post-hilp-dev-skills/`
- 核心思路：强调“在 HILP 之后使用”。
- 优点：边界非常明确。
- 代价：名称较长，且偏流程位置而非能力定位。
- 不选原因：`hilp-execution-skills/` 更短，并且直接表达执行层能力。

### 方案 B：目录名 `execution-discipline-skills/`
- 核心思路：强调执行纪律、TDD、review 和验证。
- 优点：不绑定 HILP 名称，可复用于其他流程。
- 代价：弱化了本任务最重要的 HILP 交接约束。
- 不选原因：本包的关键差异正是受 HILP 资产链约束。

### 方案 C：目录名 `superpowers-cn-trimmed/`
- 核心思路：直说它是 Superpowers 的中文裁剪版。
- 优点：来源清楚。
- 代价：仍以 Superpowers 命名为主，容易让用户误解为完整翻译 fork。
- 不选原因：用户已明确不希望继续叫 `superpowers-skills`，推荐方案应弱化源仓品牌而强调当前职责。

## 关键取舍
- 正确性 / 安全性：删除 `using-git-worktrees` 后，技能包不再负责工作区隔离；该前提转为“执行者必须确认当前目录就是用户指定的执行工作区”。
- 可回退性：新增独立 `hilp-execution-skills/`，不修改 `superpowers/` 源仓。
- 改动范围：比 v1 更小，删除 worktree 相关技能和自动发现假设。
- 可维护性：目录名不绑定 Superpowers，后续可根据 HILP 执行经验继续演进。
- 未来扩展性：安装说明可独立写在 README 中，不污染技能触发语义。

## 需要用户决定什么
- 是否存在：建议人工裁决。
- 是否会阻止继续：无阻断项；若用户未提出新名称，默认推荐 `hilp-execution-skills/`。
- 问题描述：是否接受推荐的新名称与裁剪边界。
- 可选项：
  1. 采用推荐方案：目录名 `hilp-execution-skills/`。
  2. 改用 `post-hilp-dev-skills/`。
  3. 改用 `execution-discipline-skills/`。
  4. 用户指定其他名称。
- 建议：采用 `hilp-execution-skills/`。
- 默认路径：采用 `hilp-execution-skills/`，因为它准确表达“HILP 执行交接后的技能包”。
- 用户是否已选择：未选择。
- 不得写成既定事实的内容：在用户批准前，不得声称用户已接受 `hilp-execution-skills/` 名称。

## 当前状态
- 中文状态名：待审批。
- 内部状态值：`ready-for-approval`。
- 进入该状态的理由：新事实已吸收；目标、范围、成功标准、保留/删除清单和推荐名称已重新收敛；不存在阻断性的必须人工裁决。

## 下一步
- 下一阶段：等待用户明确批准本资产版本后，才能进入实施蓝图阶段。
- 继续前提：用户需要明确批准 `stage-3/design-choice@v2 [state=ready-for-approval｜中文状态=待审批]`，并接受或替换推荐目录名。
- 当前阻断项：无阻断项；但没有人工批准前，不能进入实施蓝图或开始构建目录。