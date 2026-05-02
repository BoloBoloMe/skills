# Context Packet

## 适用时机

规划层为每个 `execution_unit` 生成执行交接包时使用。Context Packet 只承载当前单元进入实现所需的最小上下文，防止执行阶段重读全部历史规划资产或被旧方案、待审批材料污染。

## 字段契约

每个 `context_packet` 必须包含以下字段：

```text
context_packet:
  approved_design_ref: stage-3/design-choice@vN [state=approved｜中文状态=已批准]
  approved_blueprint_ref: stage-4-5/implementation-blueprint@vM [state=approved｜中文状态=已批准]
  handoff_ref: stage-6/execution-handoff@vK [state=<effective_state>｜中文状态=<state_label>]
  required_sections:
    - <当前 execution_unit 必读章节或标题>
  relevant_decisions:
    - <当前 execution_unit 必须遵守的已批准决策>
  prior_summaries:
    - <当前 execution_unit 依赖的前序 unit summary 路径或标识；无则写 none>
  explicitly_ignore:
    - <不得作为执行依据的资产、旧方案或材料类别>
```

## 字段说明

- `approved_design_ref`：绑定当前单元所依赖的 Stage 3 设计资产；必须为 `approved｜中文状态=已批准`，不得使用草稿、待审批、待修订、已归档或已废弃设计资产。
- `approved_blueprint_ref`：绑定当前单元所依赖的 Stage 4-5 实施蓝图资产；必须为 `approved｜中文状态=已批准`，不得使用草稿、待审批、待修订、已归档或已废弃蓝图资产。
- `handoff_ref`：绑定当前执行入口的 Stage 6 执行交接资产；必须是已成功落盘、owner_skill 为 `hilp-execution-handoff`、入口检查无阻断项的有效执行交接。执行交接资产可作为归档后的执行出口记录，但不得替代已批准设计或蓝图。
- `required_sections`：列出当前单元必须读取的章节、执行范围、禁止越界项、单元标题或验收段落；不得要求执行者重读全部历史规划资产。
- `relevant_decisions`：列出当前单元必须遵守的已批准决策和约束；只摘录与当前单元实现、验证、停止条件直接相关的内容。
- `prior_summaries`：列出当前单元依赖的前序执行摘要；无依赖时写 `none` 或空列表，并说明当前单元无前序摘要输入。
- `explicitly_ignore`：列出执行阶段必须忽略的材料类别或具体资产，例如待审批资产、待修订资产、草稿资产、已废弃方案、旧方案分支和未绑定参考材料。

## 校验规则

1. `approved_design_ref` 与 `approved_blueprint_ref` 必须同时存在，且状态均为 `approved｜中文状态=已批准`；任一缺失、版本不一致或状态失效时停止交接或执行。
2. `handoff_ref` 必须与当前执行入口一致，并通过 owner、落盘证据、执行范围、禁止越界项和无阻断项检查；若 handoff 失效或不一致，停止当前单元并回到 HILP 变更重审或执行计划修正入口。
3. `required_sections` 必须足以定位当前 `execution_unit` 的执行范围、允许文件、验证命令和停止条件；若缺少必要章节，不得由执行层自行搜索未绑定资产补齐。
4. `relevant_decisions` 只能引用已批准设计、已批准蓝图和有效执行交接中的决策；不得引用待审批、待修订、草稿、已废弃或未绑定材料。
5. `prior_summaries` 中列出的路径或标识必须存在且符合依赖顺序；缺失时停止当前单元，不得跳过前序结果继续执行。
6. `explicitly_ignore` 必须覆盖已知的待审批资产、待修订资产和已废弃方案；执行者发现此类材料时只记录并忽略，不得作为实现依据。
7. Context Packet 只允许收窄执行阅读面，不得扩大 `allowed_files`、改变接口、数据形状、验证口径、发布顺序或禁止越界项。

## 输出检查清单

- [ ] `approved_design_ref` 为已批准设计资产。
- [ ] `approved_blueprint_ref` 为已批准蓝图资产。
- [ ] `handoff_ref` 为当前有效执行交接。
- [ ] `required_sections` 只覆盖当前单元必读内容。
- [ ] `relevant_decisions` 均来自已批准或有效交接资产。
- [ ] `prior_summaries` 已列出且可读取，或明确为 `none`。
- [ ] `explicitly_ignore` 明确排除待审批资产、待修订资产、已废弃方案和未绑定材料。
