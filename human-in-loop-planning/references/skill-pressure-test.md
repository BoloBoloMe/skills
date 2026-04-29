# Skill 包压力测试模块

## 模块元信息
- internal_module: `hilp-skill-pressure-test`
- 原触发描述：用于测试“人在回路”子 skill 包本身是否按预期运行。适用于上线前验收、版本迭代、回归检查，或怀疑某个子 skill 会跳阶段、绕过 gate、错分治理模式或沿用失效资产的场景。它不参与正常业务规划链，只服务于 skill 设计迭代。

# 概览

你不服务业务任务。
你服务的是整个“人在回路”skill 包的质量。

你的职责是：
- 构造压力场景
- 预测协议应如何反应
- 对比实际与预期
- 找出触发、输出、交接规则中的漏洞

你不负责：
- 不替代业务规划
- 不产出业务蓝图
- 不把测试结果伪装成真实任务结论

## 极简工作流

1. 选择压力场景。
2. 写出测试模式：`static-rule-inference`（静态规则推演）、`interactive-dry-run`（交互干跑）或 `regression-replay`（回归重放）。
3. 写出预期路由。
4. 写出预期阻断点。
5. 写出预期资产状态变化，必须同时包含内部状态值和中文状态名。
6. 审查当前阶段规则包在此场景下的表现。
7. 对比实际与预期。
8. 输出偏差与修订建议。

路由矩阵见 `references/routing-matrix.md`。
交接契约见 `references/handoff-contracts.md`。
事件动作规则见 `references/event-action-rules.md`。

## 推荐测试场景

至少覆盖：
- lean 单点缺陷修复
- standard 行为保持型重构
- strict 兼容性过渡
- 新事实推翻旧批准
- `human_decision_required`（必须人工裁决）是否阻断绑定性推进
- `human_decision_recommended`（建议人工裁决）下默认路径是否足够保守
- 治理升级 / 降级是否正确影响资产生命周期
- 主原型升格后是否正确重算下一跳
- 执行交接成功后是否自动生成规划资产归档索引
- 归档失败是否只报告失败且不阻断执行交接
- 手动重新归档是否要求有效执行交接资产

## 触发器互斥测试矩阵

至少覆盖以下互斥场景：
- router 与 reapproval：含“重新看 / 之前方案 / 新发现”的模糊输入必须优先进入 `hilp-reapproval`。
- requirements-facts 与 design-approval：事实部分缺失但用户要求直接给方案时，必须优先补 `hilp-requirements-facts`。
- design-approval 与 reapproval：首次在当前阶段发现 必须人工裁决的决策 由当前阶段处理；既有资产被 必须人工裁决的决策 推翻或阻断时进入 `hilp-reapproval`。
- blueprint 与 design-approval：用户说“方案定了”但没有 `stage-3/design-choice@vN [state=approved｜中文状态=已批准]` 与 `last_decision` 时，不得进入 `hilp-blueprint`。
- execution-handoff 与 reapproval：执行中发现上游假设错误时，必须进入 `hilp-reapproval`，不得继续交接。
- execution-handoff 与 archive：执行交接成功落盘且入口检查为“无阻断项”后，必须自动尝试进入 `hilp-archive`；归档失败不得反向推翻执行交接。
- archive 与 reapproval：用户要求重新归档但同时提供新事实、失效、回滚或必须人工裁决阻断时，必须优先进入 `hilp-reapproval`，不得生成归档 manifest。
- archive 多候选链路：存在多个候选执行交接资产且无法唯一确定最终链时，必须归档失败并报告原因，不得猜测最终入口。

## 输出模板

# 协议压力测试阶段

## 这个阶段要做什么
- 用一句话说明：验证本规划协议是否会正确分流、阻断、审批、重审和保存资产。

## 已保存资产
- 文件链接：[90-协议压力测试_pressure-test@vN.md](相对路径到assets/90-协议压力测试_pressure-test@vN.md)
- asset_ref：`stage-test/skill-pressure-test@vN [state=<state>｜中文状态=<state_label>]`
- 当前状态：必须写中文状态名，必要时附内部状态值。
- 当前是否需要审批：通常不需要，应写“无需审批”；若测试结论要驱动规则修改，应另建方案设计资产进入“待审批”。
- 若当前状态为 `ready-for-approval｜中文状态=待审批`：同时列出审核包链接 [90-pressure-test@vN-review.md](相对路径到review-pack/90-pressure-test@vN-review.md) 和当前待审入口 [当前待审.md](相对路径到_current/当前待审.md)。

## 测试场景
- 名称：
- 测试模式：静态规则推演 / 交互干跑 / 回归重放。
- 输入：
- 预期目的：

## 预期行为
- 预期阶段：
- 预期治理模式：
- 预期阻断点：写“无阻断项 / 有阻断项”。
- 预期资产状态变化：必须同时写内部状态值和中文状态名。

## 实际行为
- 取证方式：静态规则推演 / 交互干跑 / 回归重放。
- 实际阶段：
- 实际治理模式：
- 实际阻断点：写“无阻断项 / 有阻断项”。
- 实际资产状态变化：必须同时写内部状态值和中文状态名。

## 偏差分析
- 偏差 1：
- 偏差 2：
- 根因：

## 修订建议
- 建议修改的位置：
- 建议补充或删减的规则：
- 建议新增的测试样例：

## 硬约束

- 不能把测试结果写成业务规划结论。
- 不能忽略资产状态变化，也不能只写内部状态值而不写中文状态名。
- 不能只测轻量任务，不测升级与失效路径。
- 不能跳过 必须人工裁决的决策相关测试。
- 不能把压力测试写成泛泛的 review。
