---
name: grill-with-docs
description: 结合领域文档/ADR 的设计盘问.
disable-model-invocation: true
---

用 `grilling` skill 盘问我. 用 `domain-modeling` skill 在盘问期间维护领域语言文件或 ADR. 需要记录会影响代码, 测试, 外部行为, 边界或后续追溯的决策时, 调用 `decision-ledger` skill, 按其规则维护本 feature 的 `DECISIONS.md`.

固定首问: 要不要懒设计?
我说要 -> 调用 `lazy-design` skill 了解什么是懒设计, 在盘问中若我的回答违背懒设计, 立即否定该回答, 并尝试说服我改变决策.
我说不要 -> 走常规设计.

决策记录边界:

- `DECISIONS.md` 记录本 feature 的产品, 代码, 边界, 测试决策和代码追踪.
- ADR 只记录长期架构决策.
- 领域语言文件只记录领域词汇, 不承载实现决策.
- 新增, 替代, 废弃决策前必须得到我确认.