asset_id: hilp-execution-capability-restoration-implementation-blueprint
artifact_name: stage-4-5/implementation-blueprint
version: v2
state: ready-for-approval
state_label: 待审批
owner_skill: hilp-blueprint
created_from: stage-3/design-choice@v2 [state=approved｜中文状态=已批准]
last_event: none
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批

# 实施蓝图阶段：human-in-loop-execution 二次精准补强 v2

## 这个阶段要做什么

把已批准的 v2 补强方案转成确定、唯一、可执行的文件级改动、顺序、约束和验证检查点。

## 已保存资产

- 文件路径：`docs/hilp/补回human-in-loop-execution能力/03-实施蓝图_needs-approval_implementation-blueprint@v2.md`
- asset_ref：`stage-4-5/implementation-blueprint@v2 [state=ready-for-approval｜中文状态=待审批]`
- 蓝图形式：单体蓝图
- 上游设计：`stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`
- 当前状态：待审批（`ready-for-approval`）
- 当前是否需要审批：需审批。批准后才能进入执行交接阶段。

## 改动拓扑

### 改动切片

1. `skill-authoring-depth`：补强 `writing-skills.md` 的 CSO、测试类型、压力测试、反理性化和部署 checklist。
2. `subagent-orchestration-depth`：补强 `subagent-driven-development.md` 的模型选择、失败重派、红旗清单和复杂任务调度校准。
3. `code-examples`：为 TDD、系统化调试、测试反模式补少量原版同类高信号代码示例。

### 依赖顺序

1. 先执行 `skill-authoring-depth`，为后续技能文档改动提供元纪律校准。
2. 再执行 `subagent-orchestration-depth`，补齐执行编排细节。
3. 最后执行 `code-examples`，把示例补入已存在的硬纪律文件。
4. 全部完成后执行结构、关键词、代码块和禁止路径验证。

### 风险检查点

- 不全文翻译 Superpowers 原文。
- 不修改 `superpowers/**`。
- 不新增 `human-in-loop-execution/` 之外的技能入口。
- 不恢复 `brainstorming`、`using-git-worktrees`、`using-superpowers` 独立入口。
- 示例只解释规则，不引入项目专用 API 或蓝图外实现范围。

### 发布检查点

- 发布对象只包含 5 个目标 reference 文件。
- 发布前运行本蓝图列出的验证命令。
- 若验证失败，不得进入执行交接完成声明。

### 验证检查点

- `writing-skills.md` 包含 CSO、技能测试类型、压力场景、部署 checklist。
- `subagent-driven-development.md` 包含模型选择、失败重派、红旗清单。
- TDD / 调试 / 测试反模式三个文件均包含 fenced code block 示例。
- `superpowers/` 无 diff。

### 涉及模块 / 子系统 / 文件范围

允许修改且仅允许修改：

- `human-in-loop-execution/references/writing-skills.md`
- `human-in-loop-execution/references/subagent-driven-development.md`
- `human-in-loop-execution/references/test-driven-development.md`
- `human-in-loop-execution/references/systematic-debugging.md`
- `human-in-loop-execution/references/testing-anti-patterns.md`

本 v2 不修改：

- `human-in-loop-execution/references/root-cause-tracing.md`
- `human-in-loop-execution/references/defense-in-depth.md`
- `human-in-loop-execution/references/condition-based-waiting.md`
- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/README.md`
- `superpowers/**`

## 分层蓝图包 manifest

- 使用条件：无。本次改动只有 5 个 reference 文件，依赖顺序线性，采用单体蓝图。
- 包内资产清单：无。
- 切片索引：无。
- 跨切片依赖图 / 波次：无。
- 覆盖矩阵：无单独资产；覆盖关系写入本蓝图。
- 审批边界：本蓝图 v2 单一资产。

## 实现约束

### 数据形状

所有目标文件必须继续保留以下固定结构：

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

- 不修改任何 frontmatter。
- 不新增文件。
- 不新增独立 skill 入口。
- 不修改 HILP 资产之外的规划协议文件。

### 局部算法骨架

#### `writing-skills.md`

在“执行规则”内补入以下确定内容：

1. CSO / 搜索优化：
   - description 只写触发条件，不写流程摘要。
   - 使用具体触发症状、关键词、错误信号和场景词。
   - 避免用描述字段替代正文流程。
   - 需要引用其他技能时使用技能名和 required marker，不用强制加载大型引用。
2. 技能测试类型：
   - 纪律型：压力场景、反借口、红旗。
   - 技术型：应用场景、边界场景、缺信息场景。
   - 参考型：检索场景、应用场景、缺口测试。
   - pattern 型：识别场景、应用场景、反例场景。
3. 压力测试流程：RED 基线失败、GREEN 最小规则、REFACTOR 补漏洞复测。
4. 反理性化模板：常见借口表与红旗清单。
5. 部署前 checklist：frontmatter、description、压力场景、验证证据、禁止越界项、安装边界。

#### `subagent-driven-development.md`

在“执行规则”内补入以下确定内容：

1. 模型选择：
   - 机械任务用较轻模型。
   - 多文件集成、调试、模式匹配用标准模型。
   - 架构、设计判断、最终审查用最强可用模型。
2. 失败重派：
   - `NEEDS_CONTEXT`：补上下文后重派。
   - `BLOCKED` 且上下文不足：补上下文后重派。
   - `BLOCKED` 且模型能力不足：换更强模型。
   - `BLOCKED` 且任务过大：拆成更小任务。
   - `BLOCKED` 且蓝图错误：停止并回到 HILP 变更重审。
3. 红旗清单：
   - 让 subagent 自己读整份计划。
   - 跳过规格审查或质量审查。
   - 规格审查未通过就做质量审查。
   - 多个实现 subagent 并行编辑同一文件。
   - reviewer 有问题但不复审。
   - 实现者自查替代真正审查。
   - 控制者手工修 subagent 失败以绕过流程。
4. 复杂任务调度：每个任务给完整任务文本、局部上下文、验证命令和停止条件；subagent 可在开始前或过程中提问。

#### `test-driven-development.md`

在“执行规则”内补入两个短示例：

1. 好测试 / 坏测试 TypeScript 风格对照：好例断言真实行为，坏例断言 mock 被调用。
2. 最小 GREEN / 过度实现对照：最小实现只满足当前测试，过度实现展示蓝图外配置或功能扩张。

示例必须使用通用函数名，不绑定具体项目 API。

#### `systematic-debugging.md`

在“执行规则”内补入两个短示例：

1. 多组件边界诊断 bash 示例，包含 workflow、script、external command 三层输入 / 输出 / 环境检查。
2. 单假设验证示例，展示一次只验证一个变量，不堆叠多个修复。

示例不得要求真实执行危险命令。

#### `testing-anti-patterns.md`

在“执行规则”内补入两个 before / after 示例：

1. mock 行为测试 before / after。
2. 测试专用生产方法 before / after。

示例必须说明 after 版本如何验证真实行为或把测试辅助放入测试工具。

### 错误处理要求

- 发现需要修改未列文件时，停止并回到 HILP 变更重审。
- 发现需要复制 Superpowers 原文件大段正文时，停止并裁剪为少量高信号规则或示例。
- 发现示例需要项目专用 API 才能成立时，改为通用伪代码或停止回到蓝图重审。
- 验证命令失败时不得声明完成。

### 测试承诺

执行完成后运行：

```bash
# 六段结构检查。
for f in \
  human-in-loop-execution/references/writing-skills.md \
  human-in-loop-execution/references/subagent-driven-development.md \
  human-in-loop-execution/references/test-driven-development.md \
  human-in-loop-execution/references/systematic-debugging.md \
  human-in-loop-execution/references/testing-anti-patterns.md; do
  grep -q "## 适用时机" "$f" && \
  grep -q "## 输入契约" "$f" && \
  grep -q "## 执行规则" "$f" && \
  grep -q "## 禁止事项" "$f" && \
  grep -q "## 输出契约" "$f" && \
  grep -q "## 检查清单" "$f" || exit 1
done

# 能力关键词检查。
grep -n "CSO\|搜索优化\|description" human-in-loop-execution/references/writing-skills.md
grep -n "压力场景\|RED\|GREEN\|REFACTOR\|部署前" human-in-loop-execution/references/writing-skills.md
grep -n "模型选择\|NEEDS_CONTEXT\|BLOCKED\|红旗" human-in-loop-execution/references/subagent-driven-development.md
grep -n "```" human-in-loop-execution/references/test-driven-development.md
grep -n "```" human-in-loop-execution/references/systematic-debugging.md
grep -n "```" human-in-loop-execution/references/testing-anti-patterns.md

# 禁止路径检查。
git diff --name-only -- superpowers | grep . && exit 1 || true
```

## 确定性检查

- 未确定项：无。
- 模糊表达：无。
- 分支待选方案：无。
- 需要执行者自行裁量的实现决策：无。
- 分层蓝图包成员检查：无，单体蓝图。

## 当前判断

- 当前是否可交接到执行层：否。蓝图状态为待审批，不是已批准。
- 当前阻断项：无阻断项。
- 是否存在兼容 / 回滚约束：无兼容窗口；回滚边界为还原 5 个目标 reference 文件的文档改动。
- 当前状态：待审批（`ready-for-approval`）。

## 下一步需要用户做什么

请明确批准当前 `stage-4-5/implementation-blueprint@v2 [state=ready-for-approval｜中文状态=待审批]`。批准后可进入执行交接阶段。
