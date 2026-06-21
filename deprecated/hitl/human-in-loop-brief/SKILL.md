---
name: human-in-loop-brief
description: 根据 human-in-the-loop / HITL 0.0.1 资产包生成完整中文方案评审简报. 当用户提供 HITL manifest, planning/checks/execution agent assets, human-view 审核入口或验证/收尾资产, 并要求生成最终方案评审简报, 评审备忘录, 方案简报或决策就绪总结时使用. 该 skill 通读资产包, 保留事实和来源可追溯性, 缺失证据明确标记, 最终仅输出简报内容.
---

# 中文方案评审简报生成器

## 目标

把用户提供的 human-in-the-loop / HITL 0.0.1 资产包整理成一份中文《方案评审简报》. 输出必须是一份包含最终简报内容的 Markdown 文档, 不输出过程记录, 工作计划或解释性前言.

## 角色边界

本 skill 只做资产解读和简报生成, 不启动新的 HITL 流程, 不创建或修改 manifest, planning/checks/execution agent assets, approval decision, confirmation decision, Plan, Runbook 或 verification record.

如需解释资产结构, 读取 `human-in-the-loop` skill 的 `SKILL.md` 及其 references. 只使用 HITL 语义理解资产结构, 状态, 审批/确认语义, 版本语义, 边界, 门禁和验证证据; 不要把本任务升级为规划或执行协议.

## 输入

用户输入通常是一个 HITL 资产包、`manifest.md`、文件夹、压缩包、链接或粘贴内容。优先读取：

- 根 `manifest.md`：协议、tier、workflow、current_pointers、asset_registry、decision_log。
- `planning/agent/*.yaml`：facts、design、blueprint、implementation-package、reassessment。
- `checks/agent/*.yaml`：asset-check 或文件范围检查记录。
- `execution/agent/*.yaml`：Plan、Runbook、ledger、unit-summary、verification、close。
- `human-view.html` 仅作为人类审核入口证据；正式事实仍以 manifest 和 agent assets 为准。
- 任何补充材料，例如背景说明、设计讨论、测试记录、日志、变更列表和人工备注。

只读取 agent 视图资产作为正式协议输入。旧资产可作为补充材料，但不得作为正式 HITL 协议输入或批准事实来源。

## 工作流

1. 盘点资产包，建立资料索引：文件名、资产类型、版本、生命周期状态、是否当前版本、与方案的关系。
2. 按 HITL planning 语义读取目标、事实、范围、非范围、方案选择、蓝图、执行契约和批准范围。
3. 按 HITL checks/execution 语义读取 asset-check、Plan/Runbook、受影响文件、执行单元、范围门禁、验证证据、失败/阻塞/完成状态。
4. 交叉核对规划与执行：确认执行计划是否仍匹配已批准设计、蓝图和 implementation-package；标出新增事实、边界变化、验证口径变化和阻塞项。
5. 将证据映射到简报模板。每个章节都要填写；每个主章节开头先写一句梗概性总结；缺失信息写成“未在资产包中找到明确依据”，并说明影响。
6. 输出最终中文简报。不要输出分析过程、不要请求用户继续确认、不要在简报前后添加额外说明。

## 信息抽取规则

- “关键事实”来自 facts、manifest decision_log、asset-check 和 verification。
- “范围内”和“不改的内容”优先来自 blueprint.execution_contract、allowed_files、prohibited_files、prohibited_scope、stop_conditions。
- “当前方案与关键取舍”优先来自 design 和 implementation-package。
- “实施计划”优先来自 blueprint、Plan/Runbook、execution units 和 unit-summary。
- “风险与争议点”综合 risks、stop_conditions、reassessment、verification 未运行项和 residual risks。
- “验收方式”优先来自 execution_contract.verification_contract、Plan/Runbook verification_plan、verification 和 close。

## 来源与不确定性规则

每个重要结论都要能回溯到资料来源。若当前环境支持文件引用或链接，在正文或附录中保留来源；若不支持，使用稳定文件路径、文档标题、章节名或资产版本号。

不要编造链接、版本、日期、状态或验证结果。缺失信息必须显式标出。不要把“应该通过”写成已验证事实；只有资产中有验证命令、执行时间、结果或等价证据时，才写为已验证。

## 输出格式

始终使用 `references/brief-template.md` 的完整结构。允许根据资产内容增加行数，但不要删除主章节。不要保留尖括号占位符。最终输出必须从标题开始：

`# 方案评审简报：方案名称`

如果资产中没有明确方案名称，用最具体的 change_slug、manifest 主题或资产包目录名替代；仍不明确时使用“未命名方案”。
