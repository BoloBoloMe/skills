# Failure Forensics

## 适用时机

Failure Forensics 用于 HILE 执行中已经不能安全继续实现或调试的失败状态。触发后必须停止执行，只做取证、分类和回退，不继续修复。

## 触发条件

出现任一条件即进入 Failure Forensics：

- 第二次同类失败：同一命令、同一验证点、同一接口边界或同一根因假设在修复后再次失败。
- 需要修改当前 execution_unit 的 `allowed_files` 之外文件。
- 需要改变接口、数据形状、验证口径、发布顺序或禁止越界项。
- 越界需求要求新增 CLI、runtime、auto loop、dashboard、provider routing、Git worktree 自动化，或要求 HILE 自动连续执行全部 execution_units。
- 出现新事实推翻已批准设计、已批准蓝图或有效执行交接的前提。
- 执行者需要在 HILE 执行阶段补做 HILP 蓝图判断。
- failure forensics 被要求继续修复、自动恢复或绕过确认门。

## 执行规则

铁律：触发后立即停止执行；Failure Forensics 只负责取证、分类和回退，不负责继续修复。

1. 冻结现场：停止新增实现、调试和验证口径调整；不得扩大文件范围。
2. 记录 Failure Note：用下方模板记录触发条件、证据、已改文件、失败命令和影响范围。
3. 分类失败：只做归类，不提出或实施新修复方案。
4. 回退或交接：按 HILP 回退出口返回执行交接、蓝图重审或方案设计阶段。
5. 留痕：将 Failure Note 摘要写入 unit summary；execution ledger 状态使用 `blocked`，重审标记按证据写为 `requires-reapproval` 或 `no-reapproval-needed`。

## 证据字段

Failure Note 必须包含以下证据字段：

- `unit_id`：当前 execution_unit。
- `trigger`：命中的触发条件。
- `failure_signature`：失败命令、退出码、关键错误行、同类失败判定依据。
- `attempt_history`：本轮与上一轮同类失败的最小时间线。
- `changed_files`：已修改文件及是否均在 `allowed_files` 内。
- `boundary_impact`：是否涉及接口、数据形状、验证口径、发布顺序或禁止越界项。
- `asset_impact`：是否推翻已批准设计、已批准蓝图或有效执行交接。
- `rollback_state`：可保留证据、需回退文件、不可继续原因。
- `recommended_hilp_exit`：建议回到的 HILP 阶段。

## Failure Note 模板

```markdown
# Failure Note：<unit_id>

## 触发条件

- trigger：<第二次同类失败 / allowed_files 越界 / 接口或验证口径变化 / 新事实推翻资产 / 其他>
- 停止位置：<命令、文件或步骤>
- 停止执行结论：已停止执行，未继续修复。

## 证据

- failure_signature：<命令、退出码、关键输出>
- attempt_history：<第一次失败、修复或诊断、第二次同类失败>
- changed_files：<已改文件，标记是否在 allowed_files 内>
- boundary_impact：<接口、数据形状、验证口径、发布顺序、禁止越界项影响>
- asset_impact：<已批准设计、已批准蓝图、执行交接影响>
- rollback_state：<可回退范围、需保留证据、当前风险>

## 分类

- failure_class：<implementation-defect / verification-contract-gap / blueprint-mismatch / scope-boundary-breach / asset-invalidated / environment-blocker>
- 分类依据：<仅基于证据，不提出修复方案>

## HILP 回退出口

- recommended_hilp_exit：<execution-handoff / implementation-blueprint / design-choice / change-reapproval>
- 需要审批的问题：<需要人工决策的变更点>
```

## 分类

| failure_class | 含义 | HILP 回退出口 |
|---|---|---|
| `implementation-defect` | 实现与批准蓝图一致，但第二次同类失败表明继续调试风险过高。 | 回到执行交接或变更重审，重新确认执行策略。 |
| `verification-contract-gap` | 验证命令、预期输出或完成口径不足以证明 must_haves。 | 回到实施蓝图或执行交接补齐验证契约。 |
| `blueprint-mismatch` | 已批准蓝图与实际代码结构、接口或依赖不匹配。 | 回到实施蓝图重审。 |
| `scope-boundary-breach` | 继续执行需要越过 `allowed_files`、禁止越界项或发布顺序。 | 回到执行交接或变更重审。 |
| `asset-invalidated` | 新事实推翻已批准设计、已批准蓝图或有效执行交接。 | 回到方案设计或实施蓝图重审。 |
| `environment-blocker` | 环境、权限或外部依赖阻断验证，且不能在当前执行单元内解决。 | 回到执行交接确认执行条件。 |

## 禁止事项

- 不得在 Failure Forensics 中继续修复、补写功能、改变接口或重定义验证口径。
- 不得把 failure forensics 当作自动 stuck detection runtime、自动 crash recovery runtime 或自动恢复机制。
- 不得绕过 HILE 执行计划确认门。
- 不得用待审批、草稿、待修订或已归档资产作为绑定性设计或蓝图输入。
- 不得只记录“失败”而不记录证据字段、分类和 HILP 回退出口。

## 输出契约

输出 Failure Note、失败分类、证据摘要、是否需要回退已改文件、推荐 HILP 回退出口和不得继续执行的结论。若需要记录执行单元状态，unit summary 与 execution ledger 必须标记阻断或需要重审，不得声明完成。

## 检查清单

- [ ] 已停止执行，未继续修复。
- [ ] Failure Note 已包含触发条件和证据字段。
- [ ] 已分类失败且未提出未批准修复路线。
- [ ] 已标明 HILP 回退出口。
- [ ] unit summary 与 execution ledger 的阻断或重审状态一致。
