# Execution Ledger

## 适用时机

每个 HILP 执行计划进入实现前创建 execution ledger；每个 `execution_unit` 开始、完成、阻断、转入重审或回退时更新。ledger 是执行状态索引，不替代 unit summary、蓝图或执行交接。

## 输入契约

- HILP design asset_ref，且状态必须为 `approved｜中文状态=已批准`。
- HILP blueprint asset_ref，且状态必须为 `approved｜中文状态=已批准`。
- 当前有效的 HILP execution handoff asset_ref。
- 执行计划路径。
- 每个 `execution_unit` 的 `unit_id`、标题、依赖、允许修改文件、验证命令和停止条件。
- 对应 unit summary 路径。

## 状态定义

| 状态 | 含义 | 可声明内容 |
|---|---|---|
| `not-started` | 已列入计划但尚未开始执行。 | 只能声明待执行。 |
| `in-progress` | 当前单元已开始，尚未完成验证或记录。 | 不得声明完成。 |
| `completed` | 单元已按计划完成，验证命令退出码符合预期，unit summary 已写入。 | 可声明该单元完成。 |
| `blocked` | 命中停止条件、缺少输入、验证失败且无法在范围内处理，或需要 HILP 重审。 | 只能声明阻断事实与下一步回退入口。 |
| `rolled-back` | 已按执行计划或 HILP 指令回退本单元改动。 | 可声明回退状态和剩余风险。 |
| `superseded` | 后续已批准计划替代本单元记录。 | 只保留历史，不作为当前执行依据。 |

## 字段

ledger 至少包含以下字段：

| 字段 | 要求 |
|---|---|
| `Unit` | `unit_id`，与执行计划和 unit summary 一致。 |
| `状态` | 使用状态定义中的固定值。 |
| `执行方式` | inline、subagent-worker 或执行交接指定的方式；不得据此绕过计划确认门。 |
| `Summary` | unit summary 相对路径；阻断时也必须填写阻断类 summary 路径。 |
| `验证命令` | 本单元完成或阻断前实际运行的关键命令；无命令时写明人工检查依据。 |
| `退出码` | 实际退出码；未运行命令时写 `n/a` 并说明原因。 |
| `重审标记` | `no-reapproval-needed`、`requires-reapproval` 或 `unchecked`。 |

## 更新时机

1. 初始化执行记录时写入绑定资产、禁止越界项摘要和所有单元的 `not-started` 行。
2. 单元开始执行时可追加事件记录，或将状态改为 `in-progress`；不得提前写 `completed`。
3. 单元完成后，先写完成类 unit summary，再把状态更新为 `completed`，填写 summary 路径、验证命令、退出码和重审标记。
4. 单元阻断后，先写阻断类 unit summary，再把状态更新为 `blocked`，填写阻断证据、失败命令或人工检查依据以及重审标记。
5. 回退、替代或进入 HILP 重审时追加事件记录，保留原始完成或阻断证据。

## 阻断记录

阻断行必须满足：

- `状态` 为 `blocked`。
- `Summary` 指向阻断类 unit summary。
- `验证命令` 记录失败命令、停止条件检查或 `n/a` 的原因。
- `退出码` 记录实际非零退出码；若未运行命令，写 `n/a`。
- `重审标记` 必须明确为 `requires-reapproval` 或 `no-reapproval-needed`，不得保留 `unchecked`。
- 事件记录中写明命中的停止条件、证据路径和回退入口。

## 重审标记

| 标记 | 使用条件 |
|---|---|
| `no-reapproval-needed` | 未改变接口、数据形状、验证口径、发布顺序或禁止越界项，且未发现推翻已批准资产的新事实。 |
| `requires-reapproval` | 发现新事实、蓝图缺口、越界文件需求、接口或验证口径变化、发布顺序变化，或命中执行计划列出的 HILP 重审条件。 |
| `unchecked` | 仅允许用于 `not-started` 或尚未写完 summary 的临时状态；不得用于 `completed` 或 `blocked`。 |

## 禁止改写历史

- 不得删除已发生的事件记录、失败命令或阻断事实。
- 不得把失败记录改写为从未发生；后续修复只能追加新事件并更新当前状态。
- 不得在未写 unit summary 前把状态标为 `completed` 或 `blocked`。
- 不得用待审批、草稿、待修订或已归档的设计 / 蓝图资产覆盖绑定资产。
- 不得用 execution ledger 替代 HILP 审批、蓝图判断或 failure forensics。

## 检查清单

- [ ] 每个 execution_unit 都有一行 ledger 状态。
- [ ] `completed` 或 `blocked` 行均指向已落盘 unit summary。
- [ ] 验证命令、退出码和输出摘要可在 summary 中追溯。
- [ ] 重审标记不是 `unchecked`。
- [ ] 事件记录保留历史，没有删除失败或阻断证据。
