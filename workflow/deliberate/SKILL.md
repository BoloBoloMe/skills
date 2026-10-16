---
name: deliberate
description: 盘问我以敲定决策, 然后将决策落盘.
disable-model-invocation: true
---

调用 `domain-awareness` skill 只读感知当前工作目录的领域模型. 调用 `grilling` skill 盘问我.

我确认结束盘问后: 使用 `domain-modeling` 维护领域语言文件或 ADR; 调用 `decision-ledger` 维护决策账本, 必须完整记录会话中所有确认过的决策和事实, 禁止写成摘要.
我拒绝结束并补充问题: 不写文件, 返回盘问继续.

要落盘的产物都落盘之后, 启动一名子代理做以下两项, 发现有问题先向我汇报, 在得到我的答复前禁止采取任何行动:
1. 逻辑自洽: 充分理解产物内容, 校验它们的内容是否能形成逻辑闭环, 彼此的内容是否不多/不漏/不矛盾.
2. 反方攻击: 站在反方的立场攻击当前决策. 让子代理调用 `opposing-viewpoint` skill 来完成, 你不要自己调用这个 skill 或者是读取其中的内容, 也不必检查它是否存在, 让子代理调用它就好. 
