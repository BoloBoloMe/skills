---
name: deliberate
description: 审议并关闭产品与技术决策.
disable-model-invocation: true
---

调用 `domain-awareness` skill 只读感知当前工作目录的领域模型. 调用 `grilling` skill 盘问我.

我确认结束盘问后: 使用 `domain-modeling` 维护领域语言文件或 ADR; 调用 `decision-ledger` 维护决策账本, 必须完整记录会话中所有确认过的决策和事实, 禁止写成摘要.
我拒绝结束并补充问题: 不写文件, 返回盘问继续.

`DECISIONS.md` 写入产物根目录, 默认 `docs/changes/<feature-slug>/`, 调用方可指定其他根目录; 领域语言文件与 ADR 由 `domain-modeling` 写入其约定位置.
已有同 slug 产物时直接修订, 无则新建.

要落盘的产物都落盘之后, 启动一名子代理校验它们的内容是否正确且一致. 如果发现有问题先向我汇报, 在得到我的答复前禁止采取任何行动.
