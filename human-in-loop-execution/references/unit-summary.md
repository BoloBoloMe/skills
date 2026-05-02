# Unit Summary

## 适用时机

每个 `execution_unit` 完成、阻断或进入重审前，必须写入 unit summary。summary 是 execution ledger 的证据来源，不替代蓝图或执行交接；缺少 summary 时不得把 ledger 状态标为 `completed` 或 `blocked`。

## 输入契约

- HILP design asset_ref，且为已批准设计资产。
- HILP blueprint asset_ref，且为已批准蓝图资产。
- HILP execution handoff asset_ref，且为当前有效执行交接。
- `unit_id`、标题、依赖和允许修改文件。
- execution_unit 的 `context_packet`、`must_haves`、验证命令、停止条件和前序 summary。
- execution ledger 路径与本 summary 目标路径。

## 共同字段

完成类和阻断类 summary 都必须包含：

- HILP asset_ref：design、blueprint、execution handoff 三类引用。
- `unit_id` 与标题。
- 文件变更：允许修改文件、实际修改文件、越界结论。
- 验证：命令、退出码、输出摘要、覆盖的 `must_haves`。
- 偏差：新事实、未覆盖风险、停止条件命中情况。
- 重审结论：`no-reapproval-needed` 或 `requires-reapproval`，并写明依据。

## 完成类模板

```markdown
# <unit_id> Unit Summary：<标题>

## 绑定资产

- HILP design asset_ref: `<stage-3/design-choice@vN [state=approved｜中文状态=已批准]>`
- HILP blueprint asset_ref: `<stage-4-5/implementation-blueprint@vN [state=approved｜中文状态=已批准]>`
- HILP execution handoff asset_ref: `<stage-6/execution-handoff@vN>`
- 执行计划：<path>
- execution ledger：<path>

## context_packet 核验

- approved_design_ref：
- approved_blueprint_ref：
- handoff_ref：
- required_sections：
- relevant_decisions：
- prior_summaries：
- explicitly_ignore：

## 文件变更

- 允许修改文件：
- 实际修改文件：
- 越界结论：无越界 / 已阻断。

## must_haves 结果

| must_have_id | Truths | Artifacts | Key Links | 验证层级 | 结果 | 未覆盖风险 |
|---|---|---|---|---|---|---|
| MH-001 |  |  |  | 静态检查 / 命令执行 / 行为测试 / 人工检查 | pass / fail / blocked |  |

## 验证命令

| 命令 | 退出码 | 输出摘要 | 覆盖的 must_haves |
|---|---:|---|---|
| `<command>` | 0 |  |  |

## 偏差与风险

- 新事实或偏差：无 / <说明>。
- 未覆盖风险：无 / <说明>。
- 停止条件命中情况：无 / <说明>。

## 重审结论

- 结论：`no-reapproval-needed` / `requires-reapproval`。
- 依据：

## ledger 更新

- 状态：`completed`。
- Summary 路径：<path>。
- 重审标记：`no-reapproval-needed` / `requires-reapproval`。
```

## 阻断类模板

```markdown
# <unit_id> Unit Summary：<标题>（blocked）

## 绑定资产

- HILP design asset_ref: `<stage-3/design-choice@vN [state=approved｜中文状态=已批准]>`
- HILP blueprint asset_ref: `<stage-4-5/implementation-blueprint@vN [state=approved｜中文状态=已批准]>`
- HILP execution handoff asset_ref: `<stage-6/execution-handoff@vN>`
- 执行计划：<path>
- execution ledger：<path>

## 阻断事实

- unit_id：`<unit_id>`
- 命中的停止条件：
- 证据：
- 已执行的验证命令、退出码和输出摘要：

## 文件变更

- 允许修改文件：
- 实际修改文件：
- 越界结论：无越界 / 已阻断。

## must_haves 影响

- 已覆盖：
- 未覆盖：
- 失败或阻断的 Key Links：

## 偏差与风险

- 新事实或偏差：无 / <说明>。
- 未覆盖风险：
- 影响范围：

## 重审结论

- 结论：`requires-reapproval` / `no-reapproval-needed`。
- 依据：

## ledger 更新

- 状态：`blocked`。
- Summary 路径：<path>。
- 重审标记：`requires-reapproval` / `no-reapproval-needed`。

## 下一步

- 停止执行并回退到指定治理入口；不得在执行阶段临场定义验收口径或继续扩展修复范围。
```

## 检查清单

- [ ] HILP asset_ref、`unit_id`、允许文件和实际文件完整。
- [ ] `must_haves` 逐项记录 Truths / Artifacts / Key Links。
- [ ] 验证命令、退出码和输出摘要完整。
- [ ] 偏差、未覆盖风险和停止条件命中情况已记录。
- [ ] 重审结论明确，且不是 `unchecked`。
- [ ] summary 路径、状态和重审标记已写回 execution ledger。
