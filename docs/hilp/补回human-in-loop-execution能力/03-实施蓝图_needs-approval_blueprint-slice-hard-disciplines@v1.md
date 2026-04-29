asset_id: hilp-execution-capability-restoration-slice-hard-disciplines
artifact_name: stage-4-5/blueprint-slice-hard-disciplines
version: v1
state: ready-for-approval
state_label: 待审批
owner_skill: human-in-loop-planning
created_from: stage-3/design-choice@v1 [state=approved｜中文状态=已批准]
last_event: none
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批

# 子蓝图：hard-disciplines

## 适用范围

本切片补强 TDD、完成前验证、系统化调试、测试反模式、根因追踪、防御式验证和条件式等待。

## 所属主蓝图

- `stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`

## 文件范围

- 修改：`human-in-loop-execution/references/test-driven-development.md`
- 修改：`human-in-loop-execution/references/verification-before-completion.md`
- 修改：`human-in-loop-execution/references/systematic-debugging.md`
- 修改：`human-in-loop-execution/references/testing-anti-patterns.md`
- 修改：`human-in-loop-execution/references/root-cause-tracing.md`
- 修改：`human-in-loop-execution/references/defense-in-depth.md`
- 修改：`human-in-loop-execution/references/condition-based-waiting.md`

## 职责边界

- 只补强执行纪律。
- 不新增业务需求、设计方案、接口形态或数据形状。
- 所有调试修复若触发蓝图外变化，必须停止并回到 HILP 变更重审。

## 具体改动约束

### `test-driven-development.md`

必须补入：

- 铁律：没有先失败的测试，不写生产代码。
- 违规处理：先写生产代码时删除并从测试重来，不保留为参考。
- RED 验证：失败原因必须是目标行为缺失。
- GREEN 验证：最小实现，不加入蓝图外能力。
- REFACTOR 验证：测试保持通过时才清理。
- 一个好测试 / 坏测试对照，坏例体现测试 mock 行为。
- 常见借口表：太简单、稍后补测试、手工测过、赶时间、测试难写。
- 输出契约包含 RED 命令、失败摘要、GREEN 命令、通过摘要、回归命令和未覆盖项。

### `verification-before-completion.md`

必须补入：

- Gate function：识别声明、运行完整命令、读取退出码、核对输出、再声明。
- 声明与证据矩阵：测试通过、构建通过、bug fixed、agent 完成、需求满足。
- 禁止措辞：应该、看起来、大概、agent 说完成。
- agent 委派后的独立验证要求。

### `systematic-debugging.md`

必须补入：

- 铁律：未完成根因调查前不得提出修复。
- 四阶段展开：根因调查、模式分析、单假设验证、实现修复。
- 多组件诊断：边界输入、输出、环境、配置传播。
- 一次一个假设。
- 三次修复失败后停止并质疑架构或蓝图。
- 红旗和常见借口表。

### `testing-anti-patterns.md`

必须补入五类反模式：

1. 测试 mock 行为。
2. 向生产类加入测试专用方法。
3. 不理解依赖就 mock。
4. 不完整 mock。
5. 把集成测试当附加事项。

每类包含违规信号、错误原因、修复方式和 gate function。

### `root-cause-tracing.md`

必须补入：症状点、直接失败点、调用者、参数来源、最早触发点、源头修复、栈追踪诊断格式。

### `defense-in-depth.md`

必须补入四层验证模型：入口边界、业务逻辑、危险环境守卫、诊断记录。每层要求测试或命令证据。

### `condition-based-waiting.md`

必须补入：waitFor 伪代码、事件 / 状态 / 数量 / 文件 / 复杂条件场景表、允许固定等待的条件、常见错误。

## 局部风险检查点

- 不得把“无法写测试”作为默认路径；必须要求用户许可或执行交接允许的替代验证。
- 不得允许猜测修复。
- 不得允许随意 sleep 修 flaky。

## 局部验证命令

```bash
grep -n "删除并从测试重来" human-in-loop-execution/references/test-driven-development.md
grep -n "常见借口\|红旗" human-in-loop-execution/references/test-driven-development.md
grep -n "退出码" human-in-loop-execution/references/verification-before-completion.md
grep -n "三次\|3 次" human-in-loop-execution/references/systematic-debugging.md
grep -n "mock" human-in-loop-execution/references/testing-anti-patterns.md
grep -n "最早触发点" human-in-loop-execution/references/root-cause-tracing.md
grep -n "入口边界\|业务逻辑\|环境" human-in-loop-execution/references/defense-in-depth.md
grep -n "waitFor\|真实条件" human-in-loop-execution/references/condition-based-waiting.md
```

## 确定性检查

- 未确定项：无。
- 模糊表达：无。
- 需要执行者自行裁量的规划判断：无。
- 禁止越界项：不触碰 `superpowers/`。
