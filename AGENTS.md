# 全局约束

## 回复约束
- 保持高信息密度,减少礼貌语/重复总结/无意义过渡语等冗余.
- 禁止原样复述文档中已经有的内容,可以给出内容概述并补充文档引用: `path/filename:start~end`.
- 涉及需求澄清/架构设计/复杂取舍/风险分析时,不得因压缩回复而省略关键推理/边界条件/决策依据.
- 执行阶段/测试反馈/代码审查/小范围修复/批量机械任务中,使用 `/telegraphic-style`。

## 工具说明
- python: 必须以 `uv run python` 执行

## 工作流 Skill 使用说明

### 入口判断

- 目标项目缺少 `docs/agents/*`、`docs/changes/`、`docs/language/` 等 workflow 约定,且当前任务需要 PRD/issues/triage/领域语言/ADR 时,先用 `/setup-workspace`。
- 多个 workflow skill 同时匹配时,优先级:高风险 HITL > `/diagnose` > `/zoom-out` > `/grill-with-docs` > `/prototype` > `/tdd` > `/to-prd`/`/to-issues`/`/triage`。
- 小范围机械修改、格式调整、低风险单文件改动,不强制走 PRD/issues 链路。

### 触发规则

- 新功能/新流程/新接口/新业务规则/需求边界不清:先 `/grill-with-docs`;确认后按需 `/to-prd` → `/to-issues` → `/tdd`。
- bug/异常/报错/测试失败/性能回退:先 `/diagnose`;确认根因后用 `/tdd` 加回归测试并修复。
- 陌生模块/跨包调用链/历史代码/影响范围不清:先 `/zoom-out`,再决定进入诊断、需求澄清或实现。
- 架构优化/降低复杂度/模块边界/可测试性改善:用 `/improve-codebase-architecture`;默认只给报告和建议,不直接大重构。
- 状态机/数据模型/UI 方案需要先试:用 `/prototype`。
- 已明确要实现/修复且有可验证行为:用 `/tdd`。
- 要沉淀 PRD:用 `/to-prd`。
- 要拆执行工单/垂直切片:用 `/to-issues`。
- 要分类、推进、审查 issue:用 `/triage`。
- 只想压力测试想法、不需要项目文档:用 `/grill-me`;需要领域语言/ADR/代码对照时改用 `/grill-with-docs`。

## 高风险任务
涉及以下内容时,默认需要人工确认,建议用户使用 `human-in-the-loop`:
- 支付状态流转
- 退款/扣款/补单/关单
- 风控判断
- 金额/币种/汇率/定价
- 幂等/重试/补偿
- 数据库结构变更
- 权限/认证/密钥/签名
- 生产配置/部署脚本/`CI/CD`