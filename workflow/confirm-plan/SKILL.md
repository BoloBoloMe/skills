---
name: confirm-plan
description: PLAN.md 变更项风险确认与计划改写流程.
disable-model-invocation: true
---

阅读 PLAN.md 中的 issues 执行计划, 按顺序对每个 issue 执行下述操作.
阅读其变更列表, 结合代码库提炼出 **源码级变更细项**, 检查其中是否存在这些变更项:
- 变更后影响超出 issue 范围, 或不完全符合 issue 预期.
- 对结果有决定性影响或有风险的变更 (如: 涉及资金/发货/不可逆操作/法律/安全/模块边界处的修改/...).
- 隐含的 **生产代码** 变更, 在 PRD 和 issue 中都未明确提及, 也未得到我的确认.

若存在上述变更项, 用 `grill-with-docs` skill 逐项和我确认, 每确认一项即据结果改写 PLAN.md.
若不存在, 不改写 PLAN.md, 输出 `无需要确认的高风险或越界变更`, 并列出已检查的 issue 数和文件数.
完成标准: 每个 issue 都被检查, PLAN.md 只在存在已确认调整时写回, 最终回复说明改写路径或无改写原因.
