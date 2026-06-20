# 术语表 - 构建优秀 skills

让 skill 变好的领域模型. Skill 的作用, 是从随机系统中逼出确定性. 下面每个术语, 都是实现这个目标的一个杠杆. 本文件是 [`writing-great-skills`](SKILL.md) 的 disclosed reference.

任何定义中的 **粗体术语** 也都在本术语表中定义. 通过对应标题查找即可.

## 术语

### Predictability

Skill 让 agent 每次运行都以相同_方式_行动的程度: 相同过程, 不是相同输出. 一个头脑风暴 skill 应该_可预测地_发散: token 会变, 行为模式不变. 这是所有其他术语服务的根本价值. 成本和可维护性是它的症状, 不是它的对手.

_避免_: consistency, reliability, robustness, output-determinism

### Model-Invoked

保留 **description** 字段的 skill. Agent 能看到它, 因此可以自行触发它. 人类仍然可以输入名称调用它, 所以 model-invocation 总是_包含_用户可达. 不存在 only-model 的状态: description 只会_增加_ agent 发现能力, 不会移除人类调用能力.

代价是每一轮都支付永久 **context load**, 换取可发现性. 它也能被其他 skill 抵达, 因为让它对 agent 可发现的 description, 也让它可被调用.

一个内容全是 **reference** 的 model-invoked skill, 也可以作为共享 reference 的家. 另一个 skill 可以调用它, 所以多个 skill 都需要的 reference 可以只放在一个地方.

只有当 agent 必须自行抵达某个 skill 时, 才选择 model-invocation. 如果它只会被手动触发, 就删除 description, 支付零 context load.

_避免_: ability, tool, capability

### User-Invoked

**description** 被剥离的 skill. 它对 agent 不可见, 只能由人类输入名称抵达. 也就是 user-only. 相比之下, **model-invoked** 是 user-and-agent.

它用 agent 可发现性交换零 **context load**. 因为它没有 description, 除了人类之外没有任何东西可以抵达它: 其他 skill 不能触发它.

_避免_: procedure, workflow, command

### Description

Skill 的机器可读触发器, 也是 **model-invoked** skill 被迫始终加载的那个 **context pointer**. 它是否存在, 就是 invocation 轴本身: 保留它, skill 就是 model-invoked, 并且可被其他 skill 抵达; 删除它, skill 就是 **user-invoked**, 只能由人类抵达.

Description 是 model-invoked skill **context load** 的来源.

_避免_: frontmatter, summary

### Context Pointer

存在于 agent 上下文中的引用. 它命名某份上下文外材料, 并编码何时应该抵达那份材料. **description** 是顶层 context pointer, 从上下文窗口指向 skill. 指向披露文件的 pointer, 是下一层的同类对象.

决定 agent _何时_抵达材料, 以及_多可靠地_抵达材料的, 是 pointer 的措辞, 不是它的目标. 如果必达材料藏在一个措辞很弱的 pointer 后面, 那就是方差 bug. 先修 pointer 措辞, 只有当锐化措辞失败时, 才把材料拉回内联.

_避免_: link, reference, import

### Context Load

**model-invoked** skill 加在 agent 上下文窗口上的成本: 它的 **description** 始终加载, 同时消耗 token 和注意力. 这是 **user-invoked** skill 因为没有 description 而避免的成本, 也是拆出更多 model-invoked skills 时的制动器.

_避免_: token cost, context bloat

### Cognitive Load

**user-invoked** skill 加在人类身上的成本: 人类必须在脑中记住哪些 skills 存在, 以及什么时候该触发哪一个. 换言之, 人类成了索引.

**model-invocation** 通过 agent 可发现性移除这项成本. Cognitive load 是拆出更多 user-invoked skills 时的制动器. 它不是必须最小化的成本: 它是人类能动性的代价, 也是某些 skill 应该保持 user-invoked 的原因. 在人类判断重要的地方花费它; 在不重要的地方移除它.

_避免_: human index, burden, overhead

### Granularity

你把 skills 切得多细. 更细的切分会消耗两种负载之一: 更多 **model-invoked** skills 会消耗 **context load**, 因为更多 description 会挤进上下文窗口并争夺注意力; 更多 **user-invoked** skills 会消耗 **cognitive load**, 因为人类要记住和触发更多东西.

有两种切分方式:

- 按 **invocation** 切分: 当你有一个不同的 **leading word** 应该触发它, 也就是一个你确实会在 prompt 中使用的触发词时, 拆出 model-invoked skill.
- 按 **sequence** 切分: 当某个 step 的 **post-completion steps** 需要被隐藏时, 拆分 **steps**. 把后续步骤隔离到自己的上下文里, 可以清除它们对当前步骤的牵引.

反向操作也要小心: 合并 sequence 会把每个 step 的 post-completion steps 暴露给前面的步骤, 从而邀请 premature completion.

_避免_: chunking, modularity

### Router Skill

一种 **user-invoked** skill, 工作是指向你的其他 user-invoked skills: 命名每一个, 并说明何时使用它. 这样人类只需要记住一个 skill, 而不是许多个.

它只能建议, 不能触发那些 skills. User-invoked skills 没有 **description**, 所以除了人类以外没有任何东西可以抵达它们. 当 user-invoked skills 数量增长时, router skill 是 **cognitive load** 的解法.

_避免_: dispatcher, menu, registry, index, router procedure

### Information Hierarchy

按 agent 紧迫需要程度排列的 skill 内容. 这是单一梯子, 由两种切分共同形成: 内容在文件中还是在 pointer 后面, 内容是 step 还是 reference. 梯子如下:

- **Steps** - 在文件中, 主要层级
- **Reference**, 在文件中 - 次要层级
- **Reference**, 已披露 - 在 **context pointer** 后面

没有 **steps** 的 skill 只使用后两个层级. 这通常是合法的平级集合, 例如 review skill 中每条规则都在同一层级. 这是良好组织, 不是坏味道.

层级独立于 invocation: 一个 skill 可以是 model-invoked 或 user-invoked, 无论它全是 steps, 全是 reference, 还是两者都有.

当 skill 有 steps 时, 本该披露出去的文件内 reference 会掩埋 steps, 让 agent 是否注意到 steps 变成抛硬币. 这不只是可读性杠杆, 也是方差杠杆. 保持梯子顶部可读. 能向下推的内容, 尽量向下推.

_避免_: structure, organization, layout

### Co-location

把 agent 一次需要的材料放在同一个地方: 一个概念的定义, 规则和注意事项放在同一个标题下, 而不是散落在文件各处. 这样 agent 读到其中一部分时, 会顺带读到相邻内容.

它是 **Information Hierarchy** 在文件内部的搭档: 层级决定一块内容放得_多深_; co-location 决定 agent 抵达后, _旁边放什么_.

没有一种公式能保证 **reference** 格式正确. 测试标准是: 这个 skill 是否读起来像给 agent 写的文档. 聚在一起的材料通常像; 散落的材料通常不像.

它不同于 **Duplication**. Duplication 是一个意义重复出现在两个地方. 散落则是把同一个意义碎成很多片, 分散在许多地方.

_避免_: grouping, clustering, cohesion

### Branch

Skill 可以被调用的不同方式, 也就是 skill 处理的不同 case. 不同运行会走不同路径. 有许多 steps 的 skill 可能携带许多 branches. 线性 skill 没有 branch.

_避免_: path, case, fork

### Progressive Disclosure

把 **reference** 移下梯子: 从 `SKILL.md` 移到 **context pointer** 后面, 让顶层保持可读. 它主要不是 token 优化, 而是保护 **information hierarchy** 的方式.

Progressive disclosure 由 **branching** 许可: 只有部分 branch 需要的内容可以披露出去; 每条路径都需要的内容保留内联. 如果 pointer 没有稳定触发必达材料, 先锐化 pointer 措辞. 只有失败时, 才把材料拉回内联.

_避免_: lazy loading, chunking

### Steps

Agent 执行的有序动作. 当 skill 有 steps 时, steps 是主要内容层级, 值得留在 `SKILL.md` 中.

不是每个 skill 都有 steps. Skill 可以全是 steps, 例如 `tdd`; 可以全是 **reference**, 例如 review skill; 也可以两者都有. 这与 invocation 方式无关.

每个 step 都应以一个 **completion criterion** 结束. 这个标准可能清晰, 也可能模糊.

_避免_: workflow, instructions, choreography

### Completion Criterion

告诉 agent 一个工作单元何时完成的条件, 也就是它用来判断的目标. 它有两个属性, 使它不只是质量要求, 而是控制行为的杠杆.

第一个属性是 **clarity**: agent 能区分 done 和 not-done 吗? 它抵抗 **premature completion**. 模糊边界, 例如 "达到理解", 会让 agent 宣告完成并滑到下一步. 这个轴需要 *steps* 才能发挥作用, 因为 premature completion 是 steps 之间的失败.

第二个属性是 **demand**: 它要求多少工作. "每个修改过的 model 都被说明" 会强制彻底工作, 而 "产出变更列表" 不会. 这个轴不绑定 step: 它也可以约束一团平铺的 reference. 这就是没有 steps 的 skill 仍能携带详尽性标准的方式, 例如 "应用每条规则".

最强的完成标准既可检查, 又有足够 demand.

_避免_: done condition, exit condition, stopping rule

### Post-Completion Steps

跟在当前 step 后面的 **steps**. 当它们可见时, 会把 agent 拉向 **premature completion**. Agent 看得越多, 拉力越强. 防御方法是把 steps 序列拆成两段, 从而隐藏后续步骤.

_避免_: horizon, fog of war, lookahead

### Legwork

Agent 在单个 step 内部幕后完成的工作: 读取文件, 探索代码库, 修改代码, 自己挖出需要的信息, 而不是把工作转嫁给用户.

Legwork 位于 step 结构之下: 不要把它写成自己的 step. 它藏在措辞里, 由 agent 执行, 而不是由 skill 逐条控制. 它是 **post-completion steps** 跨 step 牵引力在 step 内部的对应物.

可以通过 **leading word** 提高 legwork, 例如 _comprehensive_, _thorough_; 也可以通过要求详尽工作的 **completion criterion** 提高, 包括作用于平铺 reference 的 demand 轴. 这就是驱动纯 reference skill 覆盖所有规则的东西.

当 demand 缺失, 或 **premature completion** 切断 step 时, legwork 会变薄.

_避免_: scope, effort, diligence, coverage

### Reference

Agent 按需参考的材料: 定义, 事实, 参数, 示例, 条件指令. 当 skill 有 **steps** 时, reference 次于 steps. 当 skill 没有 steps 时, reference 就是全部内容. 它也可以完全生活在任何 skill 之外, 见 **External Reference**.

Reference 可以通过 **context pointer** 抵达, 是 **progressive disclosure** 的首要候选.

_避免_: supporting material, docs, background

### External Reference

生活在 skill 系统之外的 **reference**: 一个普通文件, 没有 **description**, 没有 **steps**, 不可调用, 但任何 skill 都可以指向它.

它是不需要自行触发的共享 reference 的家. 它也是两个 **user-invoked** skills 共享材料的唯一方式, 因为两者都没有 description, 也就不能触发对方.

_避免_: doc, resource, knowledge base

### Leading Word

一个紧凑概念, 也叫 *Leitwort*. 它已经存在于模型预训练中, agent 运行 skill 时会用它思考. 它借用模型已有先验, 用尽可能少的 token 编码行为原则, 例如 _lesson_, _proximal zone of development_, _fog of war_, _tracer bullets_.

它作为 token 重复, 而不是作为句子重复. 它会在 skill 中积累分布式定义, 并锚定一整片行为. 自造词在定义清楚时也能工作, 但它不会招募预训练先验. 你需要支付定义 token, 才能得到已有词免费给你的东西. 先找已有词.

引导词两次服务于 **predictability**. 在正文中, 它锚定 **execution**: agent 每次遇到这个概念, 都会触及同一组行为. 在平铺 reference 中, 它会聚焦 agent 对某类对象的注意力, 每次运行都招募正确的检查.

在 **description** 中, 它锚定 **invocation**. 这不只发生在 skill 内部: 当同一个词存在于你的 prompt, 文档和代码库中, agent 会把这套共享语言连接到 skill, 并更可靠地触发它. 用你真正希望触发该 skill 时会使用的 leading word 来写 description.

_避免_: keyword, term, motif

### Single Source of Truth

每个意义都只生活在一个权威位置的理想状态. 这样改变 skill 行为时, 只需要修改一个地方. **Duplication** 是对它的破坏.

_避免_: home, canonical location

### Relevance

一行内容是否仍然关系到 skill 要做什么. 这是决定保留什么的镜头.

一行失去 relevance, 可能因为它从未真正关系到任务, 例如纯叙述, 或者本应披露到某个 **branch** 后面; 也可能因为它已经过期, 随着它描述的行为或世界改变而漂移.

更短的 skill 更容易保持 relevant, 因为每一行都更便宜检查. Relevance 不同于 **no-op**: relevance 问一行是否关系到任务; no-op 问它是否改变行为.

_避免_: load-bearing, staleness, freshness

## 失败模式

### Premature Completion

当前 step 在真正完成之前就结束, 因为 agent 的注意力滑向了完成感, 而不是继续工作.

这是 steps 之间的失败: 它需要 **steps** 才会发生. 一个没有 steps 的 skill 如果太早退出, 不是 premature completion, 而是 demand 不足导致 **legwork** 变薄.

它是两股力量的拉扯: 可见的 **post-completion steps** 向前拉; **completion criterion** 的 clarity 提供阻力. 锐利, 可检查的 bar 能撑住; 模糊 bar 会让步. 模糊性是必要条件: 如果边界足够锐利, 无论后面有多少 steps 可见, 它都能抵抗拉力. 所以, 一个从不向前冲的 step 不需要防御.

有两个杠杆可以撑住会前冲的 step, 但要按顺序使用:

1. **先锐化边界**. 这是局部且便宜的修复.
2. 只有当标准不可避免地模糊, 且你确实观察到 agent 冲向后续步骤时, 才**隐藏后续 steps**.

隐藏只有在真实上下文边界上才有效, 例如 user-invoked hand-off 或 subagent dispatch. 内联 model-invoked 调用不会清除上下文, 后续 steps 仍然留在那里.

Premature completion 是 legwork 变薄的一个原因, 但两者不同: 即使 step 跑到完成, legwork 也可能很薄.

_避免_: premature closure, the rush, rushing, shortcutting

### Duplication

同一个意义拥有多个 **single source of truth**. 它会增加维护成本, 因为改一处就必须改其他地方; 增加 token 成本; 还会夸大重要性, 因为重复的意义在层级中获得了超过真实排名的权重.

它有点像 **leading word** 的反面. Leading word 是有意重复 token 来提高注意力; duplication 是无意重复意义, 导致维护和权重问题.

_避免_: repetition, redundancy

### Sediment

Skill 中从未清除的旧内容层沉积下来. 添加内容感觉安全, 删除内容感觉有风险, 所以过期和无关的行会不断累积. 你必须从这些沉积物里钻过去, 才能找到仍然活着的内容.

这是任何缺少剪枝纪律的 skill 的默认命运. 它是 **relevance** 的缓慢侵蚀, 不同于 **duplication** 所说的意义重复.

_避免_: accretion, bloat, cruft, rot

### Sprawl

Skill 单纯太长: `SKILL.md` 中行数太多, 与这些行是否过期或重复无关. 即使一个 skill 每一行都有效且唯一, 也可能 sprawl.

它消耗可读性, 因为 agent 在行动前必须涉过更多内容, 注意力在过量材料中变薄. 它消耗可维护性, 因为每多一行, 就多一行需要保持 **relevant**. 它也消耗 token.

治法是回到 **information hierarchy**: 把 **reference** 推到 **context pointer** 后面, 或按 **branch** / sequence 拆分, 让每条路径只携带自己需要的内容.

Sprawl 不同于 **sediment** 和 **duplication**. Sediment 是过时内容造成的长度. Duplication 是重复意义造成的长度. Sprawl 是长度本身, 无论原因是什么.

_避免_: bloat, length, size, verbosity

### No-Op

一条不改变任何行为的指令, 因为模型默认就会这么做. 你支付负载, 告诉 agent 它本来就会做的事.

测试方法: 这一行相对默认行为有改变吗? 一行可以完全 **relevant**, 但仍然是 no-op. 让 **leading word** 免费发挥作用的同一套先验, 也让 no-op 没有价值.

Leading word 是一种_技术_. No-op 是对某一行的_裁决_. 它们会交叉: 一个太弱, 不足以击败默认行为的 leading word, 就是 no-op. 例如当 agent 已经大致 thorough-ish 时, 写 _be thorough_ 就没有价值. 修复不是换一种技术性说法, 而是换一个能通过裁决的更强词, 例如 _relentless_.

因此, No-Op 测试, 也就是 "它相对默认行为有改变吗?", 同时也是你判断 leading word 是否值得重复的方式. 这是相对模型的判断, 不是相对读者的判断. 如果两个人对一行是否 no-op 有分歧, 真正的分歧在于他们对模型默认行为的判断不同. 通过运行 skill 解决, 不要靠辩论解决.

_避免_: redundant instruction, restating the obvious, belaboring
