---
name: grill-with-docs
description: 结合领域文档/ADR 的设计盘问.
disable-model-invocation: true
---

用 `grilling` skill 盘问我. 用 `domain-modeling` skill 在盘问期间维护领域语言文件或 ADR. 首个决策固定为: `要不要懒设计?`
要懒设计吗? 是 -> 调用 `lazy-design` skill 了解什么是懒设计, 在盘问中若我的回答违背懒设计, 立即否定该回答, 并尝试说服我改变决策.
要懒设计吗? 不 -> 走常规设计.