asset_id: hilp-execution-capability-restoration-implementation-blueprint
artifact_name: stage-4-5/implementation-blueprint
version: v1
state: ready-for-approval
state_label: 待审批
owner_skill: human-in-loop-planning
created_from: stage-3/design-choice@v1 [state=approved｜中文状态=已批准]
last_event: none
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批

# 实施蓝图阶段：补回 human-in-loop-execution 执行能力

## 这个阶段要做什么

把已批准的补回方案转成可执行的改动切片、顺序、约束和验证检查点。

## 已保存资产

- 文件路径：`docs/hilp/补回human-in-loop-execution能力/03-实施蓝图_needs-approval_implementation-blueprint@v1.md`
- asset_ref：`stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`
- 蓝图形式：分层蓝图包
- 上游设计：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`
- 当前状态：待审批（`ready-for-approval`）
- 当前是否需要审批：需审批。批准后才能进入执行交接阶段。

## 改动拓扑

### 改动切片

1. `entry-routing`：补强入口、路由、接收和 inline fallback 的执行边界。
2. `hard-disciplines`：补强 TDD、完成前验证、系统化调试和测试 / 调试支持技术。
3. `planning-orchestration`：补强执行计划、subagent 编排、并行 agent 和相关 prompt。
4. `review-finishing`：补强代码审查、反馈处理、最终审查 prompt 和分支收尾。
5. `meta-skill`：补强技能编写元纪律。

### 依赖顺序

1. 先执行 `entry-routing`，固定全局边界和资源加载入口。
2. 再执行 `hard-disciplines`，建立后续所有补写内容依赖的硬纪律。
3. 再执行 `planning-orchestration`，把硬纪律嵌入计划和 subagent 流程。
4. 再执行 `review-finishing`，把审查和收尾作为执行后质量门。
5. 最后执行 `meta-skill`，补齐未来维护技能时的元纪律。
6. 全部切片完成后执行覆盖矩阵验证与发布检查。

### 风险检查点

- 每个切片完成后检查目标文件是否仍包含固定结构：适用时机、输入契约、执行规则、禁止事项、输出契约、检查清单。
- 每个切片完成后检查新增内容是否包含 HILP asset_ref、禁止越界项、停止并回退条件。
- 每个切片完成后检查未新增 Superpowers 被裁剪入口、插件、hooks、commands、assets、tests。
- 全部切片完成后检查 `superpowers/` 无工作区改动。

### 发布检查点

- 发布对象只包含 `human-in-loop-execution/` 下目标文件。
- 不发布 `superpowers/`、插件、hooks、commands、assets、历史 plans/specs、测试工程。
- 发布前必须运行覆盖矩阵列出的验证命令。

### 验证检查点

- 文本结构验证：每个 reference 保留六段固定结构。
- 关键词验证：各核心文件包含其能力补回应有关键词。
- 禁止路径验证：不触碰 `superpowers/`。
- prompt 验证：prompt templates 包含 HILP 三类 asset_ref、禁止越界项、状态输出和阻断输出。

### 涉及模块 / 子系统 / 文件范围

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/README.md`
- `human-in-loop-execution/references/*.md`
- `human-in-loop-execution/references/prompt-templates/*.md`

禁止修改：

- `superpowers/**`
- 插件、hooks、commands、assets、历史 plans/specs、测试工程
- HILP 规划协议文件，除本变更目录内规划资产外

## 分层蓝图包 manifest

### 使用条件

使用分层蓝图包。原因：本次补回覆盖多个执行纪律域和多个 prompt template，按切片审查能保持边界清晰。

### 包内资产清单

- `stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`，role: manifest
- `stage-4-5/blueprint-slice-entry-routing@v1 [state=ready-for-approval｜中文状态=待审批]`，role: slice
- `stage-4-5/blueprint-slice-hard-disciplines@v1 [state=ready-for-approval｜中文状态=待审批]`，role: slice
- `stage-4-5/blueprint-slice-planning-orchestration@v1 [state=ready-for-approval｜中文状态=待审批]`，role: slice
- `stage-4-5/blueprint-slice-review-finishing@v1 [state=ready-for-approval｜中文状态=待审批]`，role: slice
- `stage-4-5/blueprint-slice-meta-skill@v1 [state=ready-for-approval｜中文状态=待审批]`，role: slice
- `stage-4-5/coverage-matrix@v1 [state=ready-for-approval｜中文状态=待审批]`，role: coverage-matrix

### 切片索引

| 切片 | 子蓝图 | 风险等级 | 依赖 | 发布波次 |
|---|---|---|---|---|
| entry-routing | `blueprint-slice-entry-routing@v1` | 中 | 无 | 1 |
| hard-disciplines | `blueprint-slice-hard-disciplines@v1` | 高 | entry-routing | 2 |
| planning-orchestration | `blueprint-slice-planning-orchestration@v1` | 高 | hard-disciplines | 3 |
| review-finishing | `blueprint-slice-review-finishing@v1` | 中 | hard-disciplines | 4 |
| meta-skill | `blueprint-slice-meta-skill@v1` | 中 | entry-routing | 5 |

### 跨切片依赖图 / 波次

```text
entry-routing
  -> hard-disciplines
      -> planning-orchestration
      -> review-finishing
  -> meta-skill
all slices -> coverage-matrix verification
```

### 覆盖矩阵

- 覆盖矩阵引用：`stage-4-5/coverage-matrix@v1 [state=ready-for-approval｜中文状态=待审批]`

### 审批边界

本次审批精确覆盖 manifest、五个子蓝图和覆盖矩阵的 v1 固定版本集合。任何成员内容性变化均需要递增对应版本，并更新 manifest。

## 实现约束

### 数据形状

所有 reference 文件保持以下六段结构：

```text
# 标题
## 适用时机
## 输入契约
## 执行规则
## 禁止事项
## 输出契约
## 检查清单
```

prompt template 文件保持以下六段结构：

```text
# 标题
## 适用时机
## 输入契约
## 执行规则
## 禁止事项
## 输出契约
## 检查清单
```

### 接口约束

- `human-in-loop-execution/SKILL.md` 的 frontmatter `name` 保持 `human-in-loop-execution`。
- `description` 仍只描述触发条件，不写完整流程摘要。
- 不新增独立技能目录。
- 不新增 Superpowers 命令、插件、hooks、assets 或测试工程。

### 局部算法骨架

每个目标文件按以下顺序补回：

1. 定位该文件对应的 Superpowers 原技能能力点。
2. 只抽取影响执行可靠性的强制门、停止条件、反误用规则、关键示例、输出校准。
3. 将抽取内容改写为中文，并加入 HILP asset_ref、禁止越界项、停止并回退条件。
4. 保持文件固定结构。
5. 运行覆盖矩阵中该文件对应的文本检查。

### 错误处理要求

- 发现某补回内容需要新增执行技能入口时，停止并回到 HILP 变更重审。
- 发现某补回内容要求修改 `superpowers/` 时，停止并回到 HILP 变更重审。
- 发现某补回内容要求执行者补做需求、设计、接口或数据形状裁决时，停止并回到 HILP 变更重审。
- 发现验证命令失败时，不得声明蓝图执行完成。

### 测试承诺

- 文本检查覆盖全部目标文件。
- 关键词检查覆盖 TDD、调试、验证、subagent、审查、收尾、写技能。
- 禁止路径检查覆盖 `superpowers/` 和被裁剪 Superpowers 资产类别。
- prompt 检查覆盖四类 prompt template。

## 确定性检查

- 未确定项：无。
- 模糊表达：无。
- 分支待选方案：无。
- 需要执行者自行裁量的实现决策：无。
- 分层蓝图包成员检查：主蓝图、五个子蓝图和覆盖矩阵均在本目录落盘，版本固定为 v1。

## 当前判断

- 当前是否可交接到执行层：否。蓝图状态为待审批，不是已批准。
- 当前阻断项：无阻断项。
- 是否存在兼容 / 回滚约束：无兼容窗口；回滚边界为还原 `human-in-loop-execution/` 目标文件的文档改动。
- 当前状态：待审批（`ready-for-approval`）。

## 下一步需要用户做什么

请明确批准当前分层蓝图包固定版本集合：manifest、五个子蓝图和覆盖矩阵的 v1。批准后可进入执行交接阶段。
