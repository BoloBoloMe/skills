---
asset_id: fix-hilp-execution-handoff-intake-ambiguity-implementation-blueprint
artifact_name: stage-4-5/implementation-blueprint
version: v2
state: approved
state_label: 已批准
owner_skill: hilp-blueprint
created_from: stage-reapproval/reapproval-decision@v1 [state=archived｜中文状态=已归档]
last_event: human-approval-granted
last_decision: human-approval-2026-04-29-approve-blueprint-v2
approval_marker: approved
approval_marker_label: 已批准
asset_path: D:/Workspace/skills/docs/changes/修正HILP执行交接入口歧义/planning/assets/03-实施蓝图_implementation-blueprint@v2.md
asset_link: [03-实施蓝图_implementation-blueprint@v2.md](./03-实施蓝图_implementation-blueprint@v2.md)
---

# 实施蓝图阶段

## 这个阶段要做什么

把已批准的入口歧义修正方案和新发现的 Markdown 表格渲染问题，转成可执行的文件级改动、资产修复边界和验证检查点。

## 已保存资产

- 文件链接：[03-实施蓝图_implementation-blueprint@v2.md](./03-实施蓝图_implementation-blueprint@v2.md)
- asset_ref：`stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]`
- 蓝图形式：单体蓝图
- 上游设计：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
- 重审记录：`stage-reapproval/reapproval-decision@v1 [state=archived｜中文状态=已归档]`；文件链接：[04-变更重审_reapproval@v1.md](./04-变更重审_reapproval@v1.md)
- 当前状态：已批准（内部状态值：`approved`）
- 当前是否需要审批：已批准；审核包 [03-implementation-blueprint@v2-review.md](../review-pack/03-implementation-blueprint@v2-review.md) 已关闭。

## 改动拓扑

### 改动切片

1. `skill-entry-description`：修正 [human-in-loop-execution/SKILL.md](../../../../../human-in-loop-execution/SKILL.md) 的 frontmatter description、入口前提和 HILP 绑定纪律。
2. `handoff-intake-contract`：修正 [human-in-loop-execution/references/hilp-handoff-intake.md](../../../../../human-in-loop-execution/references/hilp-handoff-intake.md) 的输入契约、执行规则、禁止事项和检查清单。
3. `hilp-asset-table-rendering`：修复本变更目录中已生成 review-pack 的表格分隔行列数，并把 Markdown 表格列数一致性纳入本轮验证。

### 依赖顺序

1. 先处理 `hilp-asset-table-rendering`：确认并修复本变更目录下 review-pack 表格列数错误，防止待审入口继续不可读。
2. 再改 `human-in-loop-execution/SKILL.md`，统一技能触发语义和顶层入口门槛。
3. 再改 `human-in-loop-execution/references/hilp-handoff-intake.md`，把顶层语义落到接收检查规则。
4. 最后运行验证命令，确认旧误导短语已移除、新关键语义已出现、规划侧源文件未被修改、当前 HILP 资产表格列数一致。

### 风险检查点

- 不修改 `human-in-loop-planning/**` 源文件。
- 不修改除本蓝图列明的 2 个 execution skill 文件之外的 skill 源文件。
- 当前 HILP 资产修复仅限本变更目录下 review-pack 表格语法，不改变已批准设计语义。
- 不改变设计资产和蓝图资产必须 `approved｜中文状态=已批准` 的硬门槛。
- 不把执行交接资产改成批准资产；只定义有效性检查。
- 不放宽执行范围、禁止越界项、停止并回退条件的必填要求。

### 发布检查点

- 发布对象包含 2 个 execution skill Markdown 文件，以及本变更目录内 HILP 资产表格语法修复记录。
- 发布前必须运行本蓝图列出的 5 条验证命令。
- 任一验证命令失败时，不得声明完成；按失败信息修正，若需要扩大源文件范围则停止并回到 HILP 变更重审。

### 验证检查点

- `SKILL.md` 不再出现 `handoff has been approved`。
- `SKILL.md` 明确出现“执行交接资产自身不要求已批准”。
- `hilp-handoff-intake.md` 明确出现 `owner_skill=hilp-execution-handoff` 和“执行交接资产自身不要求已批准”。
- `git diff -- human-in-loop-planning` 无输出。
- 本变更目录下所有 Markdown 表格的表头行、分隔行和数据行列数一致。

### 涉及模块 / 子系统 / 文件范围

允许修改且仅允许修改：

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/hilp-handoff-intake.md`
- `docs/changes/修正HILP执行交接入口歧义/planning/review-pack/02-design-choice@v1-review.md` 的表格分隔行
- `docs/changes/修正HILP执行交接入口歧义/planning/review-pack/03-implementation-blueprint@v1-review.md` 的审核关闭记录与表格分隔行
- 本 v2 蓝图、v2 审核包、manifest 和 `_current/` 入口

禁止修改：

- `human-in-loop-planning/**`
- `human-in-loop-execution/references/execution-routing.md`
- `human-in-loop-execution/references/writing-plans.md`
- 其他 `docs/hilp/**` 历史变更目录
- `docs/changes/<变更概述>/review/**`

## 分层蓝图包 manifest

- 使用条件：无。本次改动虽包含资产修复检查，但源文件修改只有 2 个文档文件，依赖顺序线性，采用单体蓝图。
- 包内资产清单：无。
- 切片索引：无。
- 跨切片依赖图 / 波次：无。
- 覆盖矩阵：无单独资产；覆盖关系写入本蓝图。
- 审批边界：本蓝图 v2 单一资产。

## 实现约束

### 数据形状

两个目标 execution 文件继续保持现有 Markdown 层级结构，不新增 frontmatter 字段，不新增 skill 文件。当前变更目录中的 review-pack 表格必须满足：表头列数、分隔行列数和每个数据行列数相同。

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

#### 本变更目录 HILP 资产

1. [02-design-choice@v1-review.md](../review-pack/02-design-choice@v1-review.md) 的 review-pack 表格必须为 12 列表头、12 列分隔行、12 列数据行。
2. [03-implementation-blueprint@v1-review.md](../review-pack/03-implementation-blueprint@v1-review.md) 的 review-pack 表格必须为 12 列表头、12 列分隔行、12 列数据行，并记录 v1 因新事实关闭为待修订。
3. [03-implementation-blueprint@v2-review.md](../review-pack/03-implementation-blueprint@v2-review.md) 的 review-pack 表格必须为 12 列表头、12 列分隔行、12 列数据行。

### 局部算法骨架

1. 修正当前变更目录中已知异常 review-pack 的分隔行列数。
2. 定位 execution skill 目标字符串。
3. 对 2 个 execution 文件做最小文本替换，不调整无关章节顺序。
4. 检查两个目标 execution 文件中：设计/蓝图 approved 门槛仍保留。
5. 检查两个目标 execution 文件中：执行交接自身不要求 approved 的说明已出现。
6. 检查当前变更目录下 Markdown 表格列数一致。
7. 检查 `human-in-loop-planning/**` 没有 diff。

### 错误处理要求

- 若目标字符串不存在，停止并回到实施蓝图阶段修订蓝图，不得自由改写相邻语义。
- 若发现必须修改 `execution-routing.md` 才能消除冲突，停止并回到 HILP 变更重审阶段。
- 若验证显示 `human-in-loop-planning/**` 有 diff，撤回规划侧源文件改动并重新验证。
- 若表格列数校验失败，修复当前变更目录内对应 Markdown 表格；若失败发生在其他历史变更目录，不纳入本轮执行，另行重审。

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

```bash
node - <<'JS'
const fs = require('fs');
const path = require('path');
const root = 'docs/hilp/修正HILP执行交接入口歧义';
const files = [];
function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(p);
    else if (entry.isFile() && p.endsWith('.md')) files.push(p);
  }
}
function cols(line) { return line.slice(1, -1).split('|').length; }
let bad = [];
walk(root);
for (const file of files) {
  const lines = fs.readFileSync(file, 'utf8').split(/\r?\n/);
  for (let i = 0; i < lines.length - 1; i++) {
    if (lines[i].startsWith('|') && lines[i + 1].startsWith('|---')) {
      const expected = cols(lines[i]);
      for (let j = i + 1; j < lines.length && lines[j].startsWith('|'); j++) {
        const actual = cols(lines[j]);
        if (actual !== expected) bad.push(`${file}:${j + 1}: expected ${expected}, got ${actual}`);
      }
    }
  }
}
if (bad.length) {
  console.error(bad.join('\n'));
  process.exit(1);
}
console.log('markdown table columns ok');
JS
```

预期输出：

- 第一条命令退出码为 0，且无匹配输出导致 `! grep` 成功。
- 第二条命令至少输出 2 行，分别覆盖两个目标 execution 文件。
- 第三条命令至少输出 2 行，分别覆盖两个目标 execution 文件。
- 第四条命令无输出。
- 第五条命令退出码为 0，输出 `markdown table columns ok`。

## 确定性检查

- 未确定项：无。
- 模糊表达：无。
- 分支待选方案：无。
- 需要执行者自行裁量的实现决策：无。
- 分层蓝图包成员检查：无。

## 当前判断

- 当前是否可交接到执行层：待补执行交接入口变量后判断；本蓝图已批准，但执行模式尚未在蓝图中绑定。
- 当前阻断项：执行交接阶段有阻断项；缺少已确定的执行模式。
- 是否存在兼容 / 回滚约束：无兼容窗口；回滚方式为撤回上述 2 个 execution 文件的文本修改，并恢复当前变更目录 review-pack 表格语法修复前版本。
- 当前状态：已批准（内部状态值：`approved`）。

## 下一步需要用户做什么

当前蓝图已批准。进入执行交接阶段前，需要用户明确执行模式：人类开发者 / 单代理 / 多代理 / 暂不执行。
