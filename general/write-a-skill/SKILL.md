---
name: writing-a-skills
description: 编写和编辑优秀 skills 的参考 - 让 skill 行为可预测的词汇和原则.
disable-model-invocation: true
---

Skill 的作用, 的存在是为了从随机系统中驯服确定性. **Predictability** 是它的根本价值: agent 每次运行时遵循相同的*过程*, 而不是产出相同的结果. 下面的每个杠杆都服务于这一点.

**粗体术语** 在 [`GLOSSARY.md`](GLOSSARY.md) 中定义. 需要完整含义时去那里查.

## 叙述视角

编写 skill 时始终站在我的第一视角. 读取 skill 的 agent 是 "你", 与之相对, 触发和指挥 agent 的人是 "我". 因此写 "我在使用 skill 时可能遇到的问题", 不写 "用户在使用 skill 时可能遇到的问题". 如果需要讨论调用机制, 保留固定术语 `user-invoked`, 但不要把用户写成第三人称.

## 调用方式

调用方式有两种, 代价不同:

- **model-invoked** skill 保留 **description**, 因此 agent 可以自行触发它, 其他 skill 也可以触及它. 我也可以手动输入名称调用. 代价是增加 **context load**: description 每一轮都会留在上下文窗口里. 机制: 省略 `disable-model-invocation`, 写一个面向模型的 description, 并包含足够清晰的触发短语, 例如 "当我想要..." 或 "mentions...".
- **user-invoked** skill 会从 agent 的可达范围中移除 description. 只有我输入它的名称时才能调用它, 其他 skill 不能调用. 它的 context load 为零, 但会增加 **cognitive load**:*我* 必须记得它存在, 并知道何时使用它. 机制: 设置 `disable-model-invocation: true`; 此时 `description` 面向人类, 只写一行摘要, 不写触发词清单.

只有当 agent 必须自动触发某个 skill, 或另一个 skill 必须触及它时, 才选择 model invocation. 如果它只需要被手动触发, 就让它保持 user-invoked, 避免任何 context load.

当 user-invoked skills 多到我记不住时, 累积的 cognitive load 可以用一个 **router skill** 解决: 创建一个 user-invoked skill, 列出其他 skills, 并说明什么时候该触发哪一个.

## 写 description

model-invoked **description** 做两件事: 说明 skill 是什么, 并列出哪些 **branches** 应该触发它. description 中的每个词都会增加 **context load**, 所以它比正文更需要激进剪枝:

- **把leading word放在前面**. description 是 invocation 真正发生的地方.
- **每个 branch 只保留一个触发器.** 给同一个 branch 写同义触发词就是 **duplication**. 例如 "build features using TDD" 和 "asks for test-first development" 是同一个 branch 写了两遍. 把它们折叠起来, 只保留真正不同的 branch.
- **删除正文里已经说明过的身份信息.** description 应该只保留触发器, 以及必要的 "when another skill needs..." 到达条款.

## 信息层级

Skill 由两类内容构成: **steps** 和 **reference**. 它们可以自由混合: 一个 skill 可以全是 steps, 全是 reference, 或两者兼有. 核心决策是: 哪些内容放在何处. 这取决于 **信息层级**, 即按照 agent 对内容需求紧急性排名的梯次:

1. **In-skill step** - `SKILL.md` 中的有序动作, 是主要层级: agent 要做什么, 按什么顺序做. 每一步都以**完成标准**结束, 即告知 agent 这项工作达到什么条件算完成. 完成标准要*可检查* (agent 能区分 done 和 not-done 吗?), 重要处还要*详尽* (例如 "每个修改过的 model 都被说明", 而不是 "产出变更列表"). 模糊的标准会诱发 **premature completion**.
2. **In-skill reference** - `SKILL.md` 中按需查阅的定义, 规则或事实. 它们通常是合法的平级集合, 例如 review skill 中的每条规则都位于同一层级. 这是合理组织, 不是坏味道.*本 skill 就几乎全是 reference.*
3. **External reference** - 将 reference 从 `SKILL.md` 推到单独文件中, 通过 **context pointer** 抵达, 只有 pointer 被触发时才加载. 这既可以是*已披露的* reference, 例如 skill 目录中的 sibling 文件 `GLOSSARY.md`, 仍然属于该 skill; 也可以是完全位于 skill 系统之外, 供任意 skill 指向的 **external reference**.

严格的完成标准会迫使 agent 做足 **legwork**, 也就是执行过程中的挖掘工作. 这与 skill 是否有 steps 无关: "应用每条规则" 对扁平 reference 的约束, 就像 "完成每一步" 对有序步骤的约束.

向下推得太少, 顶层会臃肿. 向下推得太多, 又会隐藏 agent 真正需要的材料. 整个决策都在处理这股张力.

**Progressive Disclosure** 是沿着梯次向下移动内容: 把内容从 `SKILL.md` 移进一个被链接的文件, 让顶层保持可读. 机制: 在 skill 文件夹中放一个链接的 `.md` 文件, 文件名描述其内容. 本 skill 就把完整定义披露到 `GLOSSARY.md`.

有些 skill 有多种用法, 每种用法都是一个 **branch**: 不同运行会沿着 skill 的不同路径前进. Branching 是最干净的披露测试: 每个 branch 都需要的内容内联; 只有部分 branch 会触及的内容, 放到 pointer 后面. 一个 **context pointer** 的*措辞*, 而不是它指向的目标, 决定 agent 何时以及多可靠地抵达那份材料.

梯次决定一块内容放得*多深*. **co-location** 决定 agent 抵达后, 它*旁边放什么*: 把一个概念的定义, 规则和注意事项放在同一个标题下, 而不是散落各处. 这样 agent 读到其中一部分时, 也会顺带读到相邻内容.

## 何时拆分

**Granularity** 指 skill 切分得多细. 每次切分都会付出某种负载, 所以只有当切分能赚回成本时才拆. 切分有两种:

- **按 invocation 拆分** - 当你有一个不同的 **leading word** 应该独立触发它, 或另一个 skill 必须抵达它时, 拆出一个 **model-invoked** skill. 你会为新的常驻 **description** 支付 **context load**, 所以独立可达必须值得.
- **按 sequence 拆分** - 当前 step 后面那些尚未开始的 **steps**, 也就是某个 step 的 **post-completion steps**, 会诱使 agent 跳过当前工作, 提前冲向后续任务, 从而造成 **premature completion** 时, 就拆分这串 **steps**. 把后续步骤移出视野, 能鼓励 agent 在当前任务上做更多 **legwork**.

## 剪枝

让每个意义都只有一个 **单一真相源**: 一个权威位置. 这样改变行为只需要编辑一次.

检查每一行的 **相关性**: 它是否仍然关系到这个 skill 要做什么?

然后逐句寻找 **no-ops**, 不只是逐行检查. 对每个句子单独运行 no-op 测试. 一旦失败, 删除整个句子, 不要只在句子里修修补补. 要激进: 大多数失败的散文都应该删除, 而不是重写.

## leading word

**leading word** 是已经存在于模型预训练中的紧凑概念, agent 运行 skill 时会用它来思考, 例如*lesson*,*fog of war*,*tracer bullets*. leading word在文本中反复出现, 虽然强leading word不一定需要重复很多次. 它会积累分布式定义, 借用模型已有的先验, 用很少的 token 锚定一整片行为.

它从两个方向服务于 Predictability. 在正文中, 它锚定*执行*: agent 每次遇到这个词, 都会触及同一组行为. 在 description 中, 它锚定*invocation*: 当同一个词同时出现在我的 prompt, 文档和代码里, agent 会把这套共享语言连接到 skill, 并更可靠地触发它.

寻找机会用leading word重构 skill. 如果同一个三元组在三个位置反复展开, 那就是 **duplication**. 如果一个 description 要花一句话指向一个想法, 也可能在乞求 **collapse** 成一个 token. 例子:

- "fast, deterministic, low-overhead" ->*tight* - 一个 phase 上反复描述的品质, 可以折叠成单个预训练词, 例如一个 *tight* loop.
- "a loop you believe in" ->*red* - 把模糊 gate 变成二元可观察状态: 循环在 bug 上变*red*, 或者没有变*red*.

这能一箭双雕: 更少的 token, 以及一个更锋利的钩子, 让 agent 能把思考挂在上面. 假设每个 skill 都有一些重复表达可以被 leading word 淘汰. 去找出它们.

## 失败模式

用这些概念诊断我在使用 skill 时可能遇到的问题.

- **Premature completion** - step 在真正完成前就结束, 注意力滑向*已经完成* 的错觉. 防御顺序: 先锐化完成标准, 这是便宜且局部的修复; 只有当标准不可避免地模糊, 且你已经观察到 agent 冲向后续任务时, 才通过拆分隐藏 post-completion steps, 也就是按 sequence 切分.
- **Duplication** - 同一个意义出现在多个地方. 它会增加维护成本和 token 成本, 还会在层级上夸大这个意义的重要性.
- **Sediment** - 过期层沉积下来, 因为添加内容感觉安全, 删除内容感觉有风险. 任何缺少剪枝纪律的 skill, 默认都会走向这里.
- **Sprawl** - 一个 skill 单纯太长, 即使每一行都仍然有效且唯一. 它会损害可读性和可维护性, 并浪费 token. 治法是回到梯次: 把 **reference** 披露到 pointer 后面, 或按 **branch** / sequence 拆分, 让每条路径只携带自己需要的内容.
- **No-op** - 模型默认就会遵守的一行, 所以你花负载说了一句没有改变行为的话. 测试: 它相对默认行为有改变吗? 弱leading word是 no-op, 例如当 agent 已经大致 thorough 时写*be thorough*. 修复方法不是换一种技术性说法, 而是换一个更强的词, 例如*relentless*.
