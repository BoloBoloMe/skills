---
name: codebase-design
description: Codebase design 词汇和 interface 设计. 当我需要设计 module interface, seam, deep module 或可测试性 interface 时使用.
---

# 代码库设计

设计 **deep module**: 大量行为隐藏在小接口背后, 位于清晰的 seam, 可通过该接口测试. 在任何代码被设计或重构的地方使用这套语言和原则. 目标是: 对调用者的 leverage, 对维护者的 locality, 对所有人的可测试性.

## 术语表

请务必使用这些术语-不要用 component/service/API/boundary 等词语代替, 语言一致性至关重要.

**Module** - 任何包含 interface 和 implementation 的实体. 刻意保持规模无关性: 可以是函数/类/包/跨层切片. _避免_: unit, component, service.

**Interface** - 调用者正确使用模块所需了解的一切: 类型签名, 以及不变量, 顺序约束, 错误模式, 必需配置和性能特征. _避免_: API, signature (过于狭窄-它们仅指类型层面).

**Implementation** - 指 module 内部的代码主体. 与 **Adapter** 不同: 一个事物可以是 implementation 很大但 adapter 很小 (例如 Postgres 仓库), 也可以是 implementation 很小但 adapter 很大 (例如内存 fake). 当讨论重点在 seam 处的替换角色时, 使用 **Adapter**; 否则使用 **Implementation**.

**Depth** - interface 的杠杆效应: 调用者或测试者每学习一单位 interface 所能触发的行为量. 当大量行为隐藏在较小的 interface 背后时, 该 module 就被称为 **deep module**; 当 interface 的复杂度几乎与 implementation 的复杂度相当时, 该 module 就被称为 **shallow module**.

**Seam** _(Michael Feathers)_ 一个无需直接编辑代码即可改变行为的地方;模块接口所在的位置. Seam 的位置本身就是一个设计决策,与它背后的内容无关.避免使用: boundary (与 DDD 的限界上下文冲突).

**Adapter** - 在 seam 处满足 interface 的具体事物. 它描述的是 *角色*(它填补的空缺), 而不是实质 (它内部的东西).

**Leverage** - 调用者从 depth 获得的收益: 他们学习的每单位 interface 功能都更加强大. 一个 implementation 即可在 N 个调用点和 M 个测试中产生效益.

**Locality** - 维护者从 depth 中获益: 变更, bug, 知识和验证集中在一个地方, 而不是散布在调用者中. 一次修复, 处处有效.

## 深模块 vs 浅模块

**Deep module** = 小 interface + 大量 implementation:

```
+-----------------------+
|   Small Interface     |  <- 少量方法, 简单参数
+-----------------------+
|                       |
|  Deep Implementation  |  <- 复杂逻辑被隐藏
|                       |
+-----------------------+
```

**Shallow module** = 大 interface + 少量 implementation (避免):

```
+-----------------------------------+
|       Large Interface             |  <- 许多方法, 复杂参数
+-----------------------------------+
|  Thin Implementation              |  <- 只是透传
+-----------------------------------+
```

设计 interface 时, 问自己:

- 我能减少方法数量吗?
- 我能简化参数吗?
- 我能把更多复杂性藏在内部吗?

## 原则

- **Depth 是 interface 的属性, 不是 implementation 的.** 一个 deep module 内部可以由小的, 可 mock 的, 可替换的部分组成 - 这些部分并不属于接口. 一个模块可以有 **internal seam** (由 implementation 私有, 供其自己的测试使用), 以及在其 interface 处的 **external seam**.
- **删除测试.** 想象一下删除该模块. 如果复杂度消失, 它是透传层. 如果复杂度在 N 个调用者中重现, 说明它是有价值的.
- **Interface 是测试界面.** 调用者和测试者都经过同一道 seam. 如果你想测试 Interface 之外的内容, 那么这个模块的结构可能就不合适.
- **一个 adapter 意味着假想的 seam. 两个 adapter 意味着真实的 seam.** 除非 seam 两侧确实存在差异, 否则不要引入 seam.

## 为可测试性而设计

好的 interface 让测试变得自然而然:

1. **接受依赖, 不创建依赖.**

   ```typescript
   // 可测试
   function processOrder(order, paymentGateway) {}

   // 难测试
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **返回结果, 不产生副作用.**

   ```typescript
   // 可测试
   function calculateDiscount(cart): Discount {}

   // 难测试
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **小表面面积.** 方法少 = 需要的测试也少. 参数少 = 测试设置更简单.

## 关系

- 一个 **Module** 有恰好一个 **Interface** (它向调用者和测试呈现的界面).
- **Depth** 是 **Module** 的属性, 以其 **Interface** 衡量.
- 一个 **Seam** 是 **Module** 的 **Interface** 所在的位置.
- 一个 **Adapter** 位于 **Seam** 并满足 **Interface**.
- **Depth** 为调用者产生 **Leverage**, 为维护者产生 **Locality**.

## 被拒绝的表述

- **Depth 作为 implementation 行数与 interface 行数之比** (Ousterhout): 嘉奖给 implementation 填充行数. 我们使用 depth-as-leverage.
- **"Interface" 作为 `interface` 关键字或类的公共方法**: 太狭窄了-这里的 interface 包含了调用者必须知道的所有事实.
- **"Boundary"**: 与 DDD 的 bounded context 重复. 说 **seam** 或 **interface**.

## 深入阅读

- **加深集群的依赖关系** - 见 [DEEPENING.md](DEEPENING.md): 依赖类别, seam 纪律, 和 replace-don't-layer 测试.
- **探索替代 interface** - 见 [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md): 启动并行 sub-agent 用几种截然不同的方式设计 interface, 然后按 depth, locality 和 seam 位置比较.
