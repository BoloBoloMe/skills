# HILE Strict Runbook（人类审核版）

strict 执行生成 `agent/03-runbook.yaml.md` 时，必须同时生成一份完整的人类审核版 Runbook。默认路径为 `execution/human/02-strict-runbook.md`。这不是简报，也不是摘要；它是 agent Runbook 的人类可读重组版，必须覆盖 agent Runbook 的全部执行信息。

## 生成原则

- 面向人类审核员组织语言、标题和阅读顺序，避免要求审核员直接理解 YAML。
- 不丢失 agent Runbook 的 contract 信息；每个 execution unit、每个 planned file、每个 repo observation、每个 implementation step、每个源码级修改意图、每个 verification plan、每个 risk check 和 stop condition 都必须出现。
- 源码级修改意图必须出现在对应 execution unit 的“分单元详细 Runbook”小节内，并紧跟该单元的计划步骤；不要生成独立的全局“源码级修改意图”章节。
- 保留可点击链接到 agent Runbook、planned-files、review-pack、manifest 和 source HILP 资产。
- 允许把机器字段翻译为中文说明，但关键字段名应在首次出现时保留括注，例如 `allowed_files`、`prohibited_files`、`pre_modify_gate`。
- 如果 agent Runbook 包含并行组、共享状态、回滚、ledger 或 unit-summary 义务，人类版也必须单独说明。

## 推荐结构

````markdown
# HILE Strict Runbook：变更名称

## 0. 审核结论入口

说明当前 Runbook 版本、来源 HILP handoff、执行分级、repo context、planned-files gate 结果、当前是否可确认执行，以及唯一固定确认命令。

## 1. 执行上下文

| 项目 | 内容 |
|---|---|
| runbook asset | hile/runbook@vN |
| source handoff | phase-05/execution-handoff@vK |
| source blueprint | phase-03/implementation-blueprint@vM |
| workspace / branch / commit | repo_context |
| execution units | EU 列表 |

## 2. 本次会做什么 / 不会做什么

### 会做什么

从 execution unit objective 汇总。

### 不会做什么

从 prohibited_files、global stop conditions、handoff prohibited scope 和 human review notes 汇总。

## 3. 受影响范围

| 执行单元 | planned files | allowed_files 来源 | prohibited_files |
|---|---|---|---|

## 4. 实施策略

说明整体落地顺序、依赖关系、串行/并行安排、共享状态和为何安全。

## 5. 执行步骤总览

| 步骤 | 所属执行单元 | 名称 / action | 目标文件 | 依赖 | 预期结果 |
|---|---|---|---|---|---|

## 6. 分单元详细 Runbook

### EU-001：单元目标

**允许修改文件（allowed_files）**：列出完整范围。  
**禁止修改文件（prohibited_files）**：列出完整范围。  
**依赖**：列出依赖单元。  
**Repo 观察结果**：逐条列出 file、status、anchors、observation。  
**计划步骤**：逐条列出 step_id、action、files、anchors、expected_result。  

**源码级修改意图（source_level_change_intent）**：必须放在当前执行单元内，紧跟该单元的计划步骤之后，作为该执行单元的执行前代码审查入口；不得作为全局独立章节集中展示。它来自 agent Runbook 的 `source_level_change_intent`，不是执行后的 diff，也不得编造最终 patch。

| 文件 | 符号 / 位置 | 修改类型 | 计划源码操作 | 审核重点 | 对应步骤 |
|---|---|---|---|---|---|
| `src/example.ts` | `mergeRuntimeConfig` | 修改函数 | 调整覆盖顺序；保留 fallback 行为 | 是否只影响批准路径；缺省值是否仍可用 | P2 |

如果无法定位具体符号，应写明原因，并改用稳定 anchor，例如配置键、路由、接口名、测试名、模板 ID 或日志事件名。不能只写“修改该文件”。

**验证计划**：列出 commands、expected_results、evidence_to_collect。  
**风险检查**：列出 risk_checks。  
**停止条件**：列出 stop_conditions。

## 7. 执行前门禁

写明 planned-files allowed-file gate 命令、结果、out-of-scope files、Runbook validator 结果和阻塞项。

## 8. 验证与完成标准

汇总全局 verification gate、每个 unit 的 verification plan、完成前必须收集的 evidence、actual changed-files gate 和 completion review 要求。

## 9. 确认命令

只给出当前 Runbook 对应的唯一固定命令，路径必须指向 canonical agent Runbook 文件。

```text
确认执行：确认执行 Runbook docs/changes/change_slug/execution/agent/03-runbook.yaml.md
```
````

## 完整性检查

生成人类版 Strict Runbook 后，逐项确认：

| 检查项 | 要求 |
|---|---|
| source refs | design、blueprint、handoff、execution units 均已呈现；agent Runbook 缺少某项时说明来源不可得 |
| repo context | workspace、branch、commit 或 unknown 原因已呈现 |
| unit coverage | agent Runbook 中每个 execution unit 都有对应章节 |
| file scope | planned_files、allowed_files、prohibited_files 均已呈现 |
| repo observations | 每条 file/status/anchor/observation 均已呈现 |
| implementation steps | 每条 step_id/action/files/anchors/expected_result 均已呈现 |
| source-level intent | 每个 execution unit 内部均包含源码级修改意图；每条 file/symbol/change_type/intended_operations/review_focus/related steps 均已呈现；没有独立全局章节 |
| verification | commands、expected_results、evidence_to_collect 均已呈现 |
| risks and stops | risk_checks、stop_conditions、global_stop_conditions 均已呈现 |
| gate | pre_modify_gate 命令、结果、out-of-scope files 均已呈现 |
| confirmation | 固定确认命令存在，且路径指向 agent Runbook |
