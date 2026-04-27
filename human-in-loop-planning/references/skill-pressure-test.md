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
2. 写出预期路由。
3. 写出预期阻断点。
4. 写出预期资产状态变化。
5. 审查当前内部模块包在此场景下的表现。
6. 对比实际与预期。
7. 输出偏差与修订建议。

路由矩阵见 `references/routing-matrix.md`。
交接契约见 `references/handoff-contracts.md`。
事件动作规则见 `references/event-action-rules.md`。

## 推荐测试场景

至少覆盖：
- lean 单点缺陷修复
- standard 行为保持型重构
- strict 兼容性过渡
- 新事实推翻旧批准
- `human_decision_required` 是否阻断绑定性推进
- `human_decision_recommended` 下默认路径是否足够保守
- 治理升级 / 降级是否正确影响资产生命周期
- 主原型升格后是否正确重算下一跳

## 触发器互斥测试矩阵

至少覆盖以下互斥场景：
- router 与 reapproval：含“重新看 / 之前方案 / 新发现”的模糊输入必须优先进入 `hilp-reapproval`。
- requirements-facts 与 design-approval：事实部分缺失但用户要求直接给方案时，必须优先补 `hilp-requirements-facts`。
- design-approval 与 reapproval：首次在当前阶段发现 必须人工裁决的决策 由当前阶段处理；既有资产被 必须人工裁决的决策 推翻或阻断时进入 `hilp-reapproval`。
- blueprint 与 design-approval：用户说“方案定了”但没有 `stage-3/design-choice@vN [state=approved]` 与 `last_decision` 时，不得进入 `hilp-blueprint`。
- execution-handoff 与 reapproval：执行中发现上游假设错误时，必须进入 `hilp-reapproval`，不得继续交接。

## 输出模板

# 压力测试报告

## 测试场景
- 名称：
- 输入：
- 预期目的：

## 预期行为
- 预期路由：
- 预期治理模式：
- 预期阻断点：
- 预期资产状态变化：

## 实际行为
- 实际路由：
- 实际治理模式：
- 实际阻断点：
- 实际资产状态变化：

## 偏差分析
- 偏差 1：
- 偏差 2：
- 根因：

## 修订建议
- 建议修改的内部模块：
- 建议补充或删减的规则：
- 建议新增的测试样例：

## 硬约束

- 不能把测试结果写成业务规划结论。
- 不能忽略资产状态变化。
- 不能只测轻量任务，不测升级与失效路径。
- 不能跳过 必须人工裁决的决策相关测试。
- 不能把压力测试写成泛泛的 review。
