---
name: human-in-loop-brief
description: 根据“人在回路规划（human-in-loop-planning）”和“人在回路执行（human-in-loop-execution）”的资产包，生成一份完整的中文方案评审简报。当用户提供了 HILP 或 HILE 相关的规划、执行、交接、清单、评审包、手册、验证、审计等资产，并要求生成最终方案评审简报、评审备忘录、会议简报或决策就绪总结时使用。该技能会通读整个资产包，保留事实和来源可追溯性，填写中文评审模板的每一个章节，对缺失的证据会明确标记，最终仅输出简报内容
---

# 中文方案评审简报生成器

## 目标

把用户提供的 `human-in-loop-planning` 和 `human-in-loop-execution`
资产包，整理成一份完整、可直接用于会议的中文《方案评审简报》。输出必须是最终简报正文，不输出过程记录、工作计划或解释性前言。

## 角色边界

本技能只做资产解读和简报生成，不启动新的 HILP/HILE 正式流程，不创建或修改规划资产、执行资产、manifest、approval
record、handoff record、runbook、plan 或 verification record。

需要借助 `human-in-loop-planning` 和 `human-in-loop-execution` 的语义来理解资产时，先阅读对应技能的 `SKILL.md`
，再按其目录规则读取必要参考资料。只使用这些技能来解释资产结构、状态、审批/确认语义、版本语义、边界、门禁和验证证据；不要把本任务升级为新的规划或执行协议。

## 输入

用户输入通常是一个或多个 HILP/HILE 资产包、文件夹、压缩包、链接或粘贴内容。尽量识别并读取以下资产：

- HILP planning manifest、phase-01 requirements/facts、phase-02 design-choice、phase-03 implementation-blueprint、phase-04
  reapproval、phase-05 execution-handoff、review-pack、audit trail、archive index。
- HILE execution manifest、handoff intake、runbook、plan、execution unit、allowed files、ledger、unit summary、verification
  record、completion review、failure forensics review。
- 任何补充材料，例如背景说明、设计讨论、需求、决策记录、测试记录、日志、变更列表和人工备注。

如果资产很多，优先读取 manifest/current 指针、review-pack、已批准的设计与蓝图、当前 execution handoff、执行
plan/runbook、验证记录和 completion/failure review。不要只依赖文件名或元数据；必须用正文内容确认事实、版本和状态。

## 工作流

1. 盘点资产包，建立资料索引：文件名、资产类型、版本、生命周期状态、是否当前版本、与方案的关系。
2. 按 HILP 语义读取规划资产：背景、目标、事实、假设、范围、非范围、方案选择、备选方案、实施蓝图、依赖、重审条件。
3. 按 HILE 语义读取执行资产：执行分级、runbook/plan、受影响文件或模块、执行单元、allowed-files 边界、验证证据、失败/阻塞/完成状态。
4. 交叉核对规划与执行：确认执行计划是否仍匹配已批准的设计和蓝图；标出新增事实、边界变化、验证口径变化、阻塞项和需要重新评审的触发条件。
5. 将证据映射到简报模板。每个章节都要填写；缺失信息写成“未在资产包中找到明确依据”，并说明影响，而不是保留占位符。
6. 输出最终中文简报。不要输出分析过程、不要请求用户继续确认、不要在简报前后添加额外说明。

## 信息抽取规则

- “关键事实”只写有来源支撑、会影响方案选择或执行边界的事实。
- “当前假设”只写尚未被资产证明、但方案依赖它成立的前提。
- “范围内”和“不改的内容”优先来自 HILP blueprint、handoff、allowed-files、prohibited/stop conditions 和 review-pack。
- “当前方案与关键取舍”优先来自 design-choice、implementation-blueprint、reapproval record 和 review-pack。
- “实施计划”优先来自 implementation-blueprint、execution handoff、runbook、plan 和 execution units。
- “验收方式”优先来自 verification contract、verification record、completion review、测试/日志/对比验证材料。
- “风险、争议点与重新评审触发条件”同时综合 HILP 风险、HILE failure forensics、stop conditions、未验证项、残余风险和阻塞项。
- “会议结论”如果资产已经证明可推进，可以勾选相应结论；如果证据不足，勾选“暂缓推进”或“需要重新评审”，并给出原因。

## 来源与不确定性规则

每个重要结论都要能回溯到资料来源。若当前环境支持文件引用或链接，在正文或附录中保留可点击来源；若不支持，使用稳定的文件路径、文档标题、章节名或资产版本号。

不要编造链接、版本、负责人、日期、状态或验证结果。缺失信息必须显式标出。不要把“应该通过”“看起来可行”写成已验证事实；只有资产中有验证命令、执行时间、结果或等价证据时，才写为已验证。

## 输出格式

始终使用 `references/brief-template.md` 的完整结构。允许根据资产内容增加行数，但不要删除主章节。不要保留尖括号占位符。最终输出必须从标题开始：

`# 方案评审简报：方案名称`

如果资产中没有明确方案名称，用最具体的变更名、handoff 名、manifest slug 或主题替代；仍不明确时使用“未命名方案”。

## 输出契约

在生成审核简报时，agent 必须严格按照提供的文档模板编写审核文档。

强制规则：

1. 审核文档必须遵循模板中定义的结构、标题、顺序和格式规范。
2. 审核文档的语言必须与模板所使用的语言保持一致。
3. 如果原始材料、用户需求或补充说明的语言与模板语言不同，必须先将内容翻译或总结为模板语言，再写入审核文档。
4. 除非模板本身明确包含多语言章节，否则不得在审核文档中混用多种语言。
5. 除非用户明确要求修改模板，否则不得新增章节、重命名标题、删除必填章节或改变模板结构。
6. 如果某些必需信息缺失，必须保留对应模板章节，并使用与模板语言一致的简洁占位说明，例如 `待补充`、`未提供`、`TBD` 等。
7. 所有假设、风险、待确认问题和建议也必须使用与模板一致的语言编写。

## 输出前检查

在生成最终审核简报之前，agent 必须：

1. 识别需要使用的文档模板。
2. 判断模板所使用的语言。
3. 确认最终输出遵循模板结构。
4. 确认最终输出语言与模板语言一致。