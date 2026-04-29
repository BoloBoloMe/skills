---
asset_id: fix-hilp-execution-handoff-intake-ambiguity-implementation-blueprint
artifact_name: stage-4-5/implementation-blueprint
version: v1
state: needs-revision
state_label: 待修订
owner_skill: hilp-blueprint
created_from: stage-3/design-choice@v1 [state=approved｜中文状态=已批准]
last_event: user-new-fact-markdown-table-rendering
last_decision: user-new-fact-2026-04-29-markdown-table-rendering
approval_marker: needs-revision
approval_marker_label: 待修订
asset_path: D:/Workspace/skills/docs/hilp/修正HILP执行交接入口歧义/assets/03-实施蓝图_implementation-blueprint@v1.md
asset_link: [03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
---

# 实施蓝图阶段

## 这个阶段要做什么

把已批准的入口歧义修正方案转成可执行的文件级改动、顺序、约束和验证检查点。

## 已保存资产

- 文件链接：[03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
- asset_ref：`stage-4-5/implementation-blueprint@v1 [state=needs-revision｜中文状态=待修订]`
- 蓝图形式：单体蓝图
- 上游设计：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
- 当前状态：待修订（内部状态值：`needs-revision`）
- 当前是否需要审批：不再等待审批；审核包 [03-implementation-blueprint@v1-review.md](../review-pack/03-implementation-blueprint@v1-review.md) 已关闭，修订内容见 v2 蓝图。

## 改动拓扑

### 改动切片

1. `skill-entry-description`：修正 [human-in-loop-execution/SKILL.md](../../../human-in-loop-execution/SKILL.md) 的 frontmatter description、入口前提和 HILP 绑定纪律。
2. `handoff-intake-contract`：修正 [human-in-loop-execution/references/hilp-handoff-intake.md](../../../human-in-loop-execution/references/hilp-handoff-intake.md) 的输入契约、执行规则、禁止事项和检查清单。

### 依赖顺序

1. 先改 `human-in-loop-execution/SKILL.md`，统一技能触发语义和顶层入口门槛。
2. 再改 `human-in-loop-execution/references/hilp-handoff-intake.md`，把顶层语义落到接收检查规则。
3. 最后运行验证命令，确认旧误导短语已移除、新关键语义已出现、规划侧文件未被修改。

### 风险检查点

- 不修改 `human-in-loop-planning/**`。
- 不修改除本蓝图列明的 2 个文件之外的 skill 文件。
- 不改变设计资产和蓝图资产必须 `approved｜中文状态=已批准` 的硬门槛。
- 不把执行交接资产改成批准资产；只定义有效性检查。
- 不放宽执行范围、禁止越界项、停止并回退条件的必填要求。

### 发布检查点

- 只发布 2 个 Markdown 文件的文案和规则修正。
- 发布前必须运行本蓝图列出的 4 条验证命令。
- 任一验证命令失败时，不得声明完成；按失败信息修正，若需要扩大范围则停止并回到 HILP 变更重审。

### 验证检查点

- `SKILL.md` 不再出现 `handoff has been approved`。
- `SKILL.md` 明确出现“执行交接资产自身不要求已批准”。
- `hilp-handoff-intake.md` 明确出现 `owner_skill=hilp-execution-handoff` 和“执行交接资产自身不要求已批准”。
- `git diff -- human-in-loop-planning` 无输出。

### 涉及模块 / 子系统 / 文件范围

允许修改且仅允许修改：

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/hilp-handoff-intake.md`

禁止修改：

- `human-in-loop-planning/**`
- `human-in-loop-execution/references/execution-routing.md`
- `human-in-loop-execution/references/writing-plans.md`
- `docs/hilp/**` 中除本变更目录资产状态更新外的既有资产
- `docs/review/**`

## 分层蓝图包 manifest

- 使用条件：无。本次仅 2 个文档文件，依赖顺序线性，采用单体蓝图。
- 包内资产清单：无。
- 切片索引：无。
- 跨切片依赖图 / 波次：无。
- 覆盖矩阵：无单独资产；覆盖关系写入本蓝图。
- 审批边界：本蓝图 v1 单一资产。

## 实现约束

### 数据形状

两个目标文件继续保持现有 Markdown 层级结构，不新增 frontmatter 字段，不新增文件。

### 接口约束

#### `human-in-loop-execution/SKILL.md`

1. 将 frontmatter description 从：

```text
description: Use when HILP execution handoff has been approved and implementation, testing, review, debugging, or branch finishing needs execution discipline
```

替换为：

```text
description: Use when HILP execution handoff has completed intake with no blocking items and implementation, testing, review, debugging, or branch finishing needs execution discipline
```

2. 在“入口前提”三类资产列表下，保留设计与蓝图必须 approved，并把执行交接条件写成：

```text
- 有效的 `stage-6/execution-handoff@vK [state=<state>｜中文状态=<state_label>]`
  - `owner_skill=hilp-execution-handoff`
  - 已成功落盘
  - 执行入口检查：无阻断项
  - 执行范围、禁止越界项、停止并回退条件齐备
```

3. 在“入口前提”段落后新增一句：

```text
执行交接资产自身不要求已批准；它是规划出口记录，按有效性检查判定。不得用执行交接资产的 `archived｜中文状态=已归档` 状态否定其入口有效性。
```

4. 将“缺少任一项时”改为按缺口回退：

```text
缺少已批准设计时，回到 HILP 方案设计阶段；缺少已批准蓝图时，回到实施蓝图阶段；缺少有效执行交接、执行范围、禁止越界项或停止条件时，回到执行交接阶段；发现新事实或上游失效时，回到变更重审阶段。
```

5. 将 HILP 绑定纪律中的：

```text
- 不得把 HILP 的待审批、草稿、待修订或已归档规划资产当作已批准输入。
```

替换为：

```text
- 不得把待审批、草稿、待修订或已归档的设计资产或蓝图资产当作已批准输入；执行交接资产按 owner、落盘、无阻断项、执行范围、禁止越界项和停止条件做有效性检查。
```

#### `human-in-loop-execution/references/hilp-handoff-intake.md`

1. 在输入契约代码块内将执行交接行替换为：

```text
HILP execution handoff asset_ref: stage-6/execution-handoff@vK [state=<state>｜中文状态=<state_label>]
HILP execution handoff owner_skill: hilp-execution-handoff
执行交接资产要求：已成功落盘；自身不要求已批准；可为 archived｜中文状态=已归档 的规划出口记录
```

2. 将执行规则第 3 条替换为：

```text
3. 核对执行交接资产 `owner_skill=hilp-execution-handoff`，已成功落盘，并明确写出“无阻断项”、执行范围、禁止越界项和停止并回退条件；执行交接资产自身不要求 `approved｜中文状态=已批准`。
```

3. 将执行规则第 6 条替换为：

```text
6. 设计或蓝图资产状态、版本缺失，或执行交接 owner、落盘证据、执行范围、禁止越界项、停止并回退条件任一缺失时，只输出失败原因和回退阶段，不进入实现。
```

4. 在禁止事项中新增一条：

```text
- 不得仅因执行交接资产为 `archived｜中文状态=已归档` 就拒绝入口；执行交接资产按有效性检查判定，已归档设计或蓝图仍不得作为已批准输入。
```

5. 在检查清单中将第三项替换为：

```text
- [ ] execution handoff asset_ref 存在、owner_skill 正确、已成功落盘且入口检查无阻断项。
```

### 局部算法骨架

1. 定位目标字符串。
2. 做最小文本替换，不调整无关章节顺序。
3. 检查两个目标文件中：设计/蓝图 approved 门槛仍保留。
4. 检查两个目标文件中：执行交接自身不要求 approved 的说明已出现。
5. 检查 `human-in-loop-planning/**` 没有 diff。

### 错误处理要求

- 若目标字符串不存在，停止并回到实施蓝图阶段修订蓝图，不得自由改写相邻语义。
- 若发现必须修改 `execution-routing.md` 才能消除冲突，停止并回到 HILP 变更重审阶段。
- 若验证显示 `human-in-loop-planning/**` 有 diff，撤回规划侧改动并重新验证。

### 测试承诺

执行完成前必须运行：

```bash
! grep -R "handoff has been approved" -n human-in-loop-execution/SKILL.md
```

```bash
grep -R "执行交接资产自身不要求" -n human-in-loop-execution/SKILL.md human-in-loop-execution/references/hilp-handoff-intake.md
```

```bash
grep -R "owner_skill=hilp-execution-handoff" -n human-in-loop-execution/SKILL.md human-in-loop-execution/references/hilp-handoff-intake.md
```

```bash
git diff -- human-in-loop-planning
```

预期输出：

- 第一条命令退出码为 0，且无匹配输出导致 `! grep` 成功。
- 第二条命令至少输出 2 行，分别覆盖两个目标文件。
- 第三条命令至少输出 2 行，分别覆盖两个目标文件。
- 第四条命令无输出。

## 确定性检查

- 未确定项：无。
- 模糊表达：无。
- 分支待选方案：无。
- 需要执行者自行裁量的实现决策：无。
- 分层蓝图包成员检查：无。

## 当前判断

- 当前是否可交接到执行层：否；本蓝图已被新事实置为待修订。
- 当前阻断项：有阻断项；审核包表格列数错误未纳入本版本蓝图。
- 是否存在兼容 / 回滚约束：无兼容窗口；回滚方式为撤回上述 2 个文件的文本修改。
- 当前状态：待修订（内部状态值：`needs-revision`）。

## 下一步需要用户做什么

本 v1 蓝图不再请求批准。请审核修订后的 v2 蓝图。
