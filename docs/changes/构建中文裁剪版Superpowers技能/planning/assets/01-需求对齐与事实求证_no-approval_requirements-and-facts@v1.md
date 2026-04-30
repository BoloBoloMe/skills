---
asset_id: hilp-superpowers-skills-requirements-facts
artifact_name: stage-1-2/requirements-and-facts
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-requirements-facts
created_from: stage-0/routing@v1
last_event: none
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/changes/构建中文裁剪版Superpowers技能/planning/assets/01-需求对齐与事实求证_no-approval_requirements-and-facts@v1.md
---

# 需求对齐与事实求证阶段

## 这个阶段要做什么
先把“要构建什么”和“Superpowers 源仓真实提供了什么”分开，避免把设计审批、执行纪律和技能分发机制混在一起。

## 需求对齐

### 目标
在仓库根目录规划并随后构建 `superpowers-skills/`：一个中文化、按 `裁剪superpowers.md` 裁剪后的 Superpowers 技能包，使其与 HILP 的阶段门控兼容。

### 范围
- 分析 `裁剪superpowers.md` 对 HILP 与 Superpowers 的边界定义。
- 分析 `superpowers/` 下的技能、文档、命令、插件配置、测试与辅助文件。
- 形成可审批的中文技能包设计方案。
- 在获得明确批准后，再进入确定性实施蓝图阶段，并最终由执行交接后实现。

### 非目标
- 不修改 `superpowers/` 克隆源仓内容。
- 不把 Superpowers 的 `brainstorming` 作为 HILP 后的独立设计入口。
- 不用 Superpowers design doc / spec approval 替代 HILP 资产、版本和审批语义。
- 不在本阶段写 `superpowers-skills/` 的正式技能文件或执行实现。
- 不向上游 Superpowers 仓库提交 PR。

### 成功标准
- 新技能包的设计明确承认：HILP 是需求、事实、方案、蓝图和执行交接的唯一规划治理源。
- 裁剪结果保留 Superpowers 的执行层价值：worktree 隔离、执行计划拆分、TDD、subagent/inline 执行、代码 review、分支收尾、调试和完成前验证。
- 技能内容以中文为主，frontmatter 名称仍满足通用 skill 规范的 ASCII/hyphen 兼容要求。
- 方案明确列出保留、改造、删除和降级的源仓内容。
- 后续蓝图能唯一确定目录、文件范围、技能清单、支持文件清单和验证方式。

### 显式约束
- 必须遵守 HILP 阶段门控：`ready-for-approval` 不等于 `approved`；未获得对具体资产版本的明确批准前不得生成正式实施蓝图或开始实现。
- 从实施蓝图阶段开始不得保留“待定、可能、视情况、后续确认、执行时再判断”等未确定项。
- 生产技能文档中的注释或说明应服务于契约、约束和取舍，避免无意义复述。
- 新目录必须在仓库根目录下，目标名为 `superpowers-skills/`。

### 待确认项
- 若用户希望 `superpowers-skills/` 被当前 agent harness 自动发现，可能需要后续明确安装或链接方式；本规划默认先构建仓库内源技能包，不假设运行时自动发现。

## 事实求证

### 已知事实
1. `裁剪superpowers.md` 明确建议边界：HILP 负责“需求事实 → 方案比较 → 人工裁决/审批 → 确定性实施蓝图 → 执行交接”；Superpowers 保留“worktree → implementation plan → subagent/executing plan → TDD → code review → branch finish”。
2. `裁剪superpowers.md` 要求取消或降级 Superpowers 的 `brainstorming` 独立入口、Superpowers design doc、Superpowers spec approval gate；其多方案比较思想应吸收到 HILP 方案设计与审批阶段。
3. `superpowers/README.md` 描述原始基础流程为：`brainstorming`、`using-git-worktrees`、`writing-plans`、`subagent-driven-development` 或 `executing-plans`、`test-driven-development`、`requesting-code-review`、`finishing-a-development-branch`。
4. `superpowers/skills/` 当前包含 14 个技能：`brainstorming`、`dispatching-parallel-agents`、`executing-plans`、`finishing-a-development-branch`、`receiving-code-review`、`requesting-code-review`、`subagent-driven-development`、`systematic-debugging`、`test-driven-development`、`using-git-worktrees`、`using-superpowers`、`verification-before-completion`、`writing-plans`、`writing-skills`。
5. `brainstorming` 的源技能包含探索上下文、逐个澄清、2–3 方案、分段设计审批、写入 `docs/superpowers/specs/...-design.md` 和用户 review gate；这与 HILP 的需求事实、方案审批和资产版本语义重复。
6. `using-superpowers` 的源技能要求任意响应前都强制检查技能，并把 Superpowers skill 置于默认行为之上；若原样中文化，容易与本仓库已启用的 HILP 规划入口发生治理优先级冲突。
7. `writing-plans` 的源技能价值在于把 spec/requirements 拆成精确文件路径、测试代码、命令、预期输出、最小实现和 commit 步骤；在 HILP 结合场景下，其输入应改为 HILP 已批准蓝图和执行交接资产。
8. `using-git-worktrees`、`subagent-driven-development`、`executing-plans`、`test-driven-development`、`requesting-code-review`、`receiving-code-review`、`finishing-a-development-branch`、`systematic-debugging`、`verification-before-completion` 均属于执行安全、实现纪律或质量验证范畴，不与 HILP 的设计审批职责直接重复。
9. `dispatching-parallel-agents` 是并行调查/修复的执行组织能力；它不替代 HILP 的蓝图或审批，但在执行层可作为受范围约束的辅助能力。
10. `writing-skills` 是元技能，主要用于创建或修改 skill；在本任务后续实现阶段若要撰写中文技能，它可提供技能 frontmatter、触发语义、压力测试和技能 TDD 的约束来源，但不属于普通业务开发主链路。
11. `superpowers/` 还包含插件清单、安装文档、hooks、命令、测试、历史 plans/specs、assets 和上游贡献指南；这些支撑源仓分发和上游维护，不必整体复制到裁剪后的中文技能包。
12. 当前仓库根目录已有 `cz-sdk-windows-build/`、`human-in-loop-planning/` 等 top-level skill 目录；尚未存在 `superpowers-skills/`。

### 证据来源
- `裁剪superpowers.md`
- `superpowers/README.md`
- `superpowers/skills/*/SKILL.md`
- `superpowers/CLAUDE.md`
- `superpowers/docs/README.codex.md`
- `superpowers/package.json`
- `find superpowers -maxdepth 5 -type f` 的文件清单
- 仓库根目录 `README.md` 与目录清单

### 关键未知项
- 当前 agent harness 是否会递归发现 `superpowers-skills/` 下的子技能；该问题影响安装说明，不阻断设计比较。
- 用户是否希望保留 `writing-skills` 元技能；该问题可作为建议裁决点处理，不阻断推荐方案提交审批。
- 是否需要同步更新仓库根 `README.md`；这影响后续实现范围，但不影响本阶段方案比较。

### 初步影响面
- 新增目录：`superpowers-skills/`。
- 可能新增：中文 README、HILP 边界说明、若干中文 `SKILL.md`、支持 prompt/reference 文件、验证清单。
- 不应修改：`superpowers/` 源仓、HILP 已有协议文件、现有技能运行脚本。
- 可能修改：仓库根 `README.md`，仅用于登记新技能包入口；是否修改应在蓝图阶段确定。

## 当前判断
- 是否有事实缺口会阻止继续：无阻断项。
- 是否建议提高治理强度：维持 standard。多技能文档改造需要显式设计和审批，但无运行时兼容窗口或高风险迁移。
- 当前是否足以进入方案设计：是。
- 当前状态：已归档（`archived`），作为无需审批的事实记录保存。
- 若不足，缺的是什么：无。

## 下一步需要用户做什么
当前事实足以进入方案设计与审批阶段。用户需要在下一阶段审阅推荐方案，并明确是否批准具体 `stage-3/design-choice@v1` 资产版本。