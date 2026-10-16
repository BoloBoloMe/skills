---
name: deliberate
description: 盘问我以敲定决策, 然后将决策落盘.
disable-model-invocation: true
---

调用 `domain-awareness` skill 只读感知当前工作目录的领域模型. 调用 `grilling` skill 盘问我.
我确认结束盘问后: 使用 `domain-modeling` 维护领域语言文件或 ADR; 调用 `decision-ledger` 维护决策账本, 账本是后续独立会话的唯一输入, 因此必须完整记录会话中明确的所有事实和决策, 禁止写成摘要.
要落盘的产物都落盘之后自检: 落盘内容所包含的信息是否完整? 逻辑是否自洽?