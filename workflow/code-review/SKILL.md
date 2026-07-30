---
name: code-review
description: 双轴代码评审流程.
disable-model-invocation: true
---

开始前, 调用 `domain-awareness` skill 只读感知当前工作目录的领域模型.

从我指定的基准点到 `HEAD` 之间的 diff, 沿两条轴 review:

- **Standards**: 代码是否遵循仓库中已记录的编码规范?
- **Spec**: 代码是否完整实现了原始 DECISIONS / spec?

两条轴分开运行, 互不污染上下文, 最后并列展示结果. 不跨轴合并排序.

## 步骤

### 1. 确定基准点

我说的任何可被 Git 解析的引用都可以作为基准点, 包括 commit SHA, 分支名, tag, `main`, `HEAD~5`. 未指定时询问.
一次性记录 diff 命令: `git diff <基准点>...HEAD` (三点语法, 以 merge-base 为比较基准). 同时记录 commit 列表: `git log <基准点>..HEAD --oneline`.
继续之前, 确认基准点可解析 (`git rev-parse <基准点>`) 且 diff 不为空. 引用无效或 diff 为空时在本步骤失败, 不把失败推给后续 reviewer.

完成标准: 基准点已解析, diff 命令已记录, commit 列表已记录, diff 非空.

### 2. 定位 spec 来源

按以下顺序查找原始 spec:

1. 我作为参数传入的路径或内容.
2. commit message 中的 issue 引用.
3. `docs/changes/<feature-slug>/` 下的 `DECISIONS.md`, `PRODUCT.md`, `TECHNICAL.md`, `EXECUTION.md`.
4. 以上均无, 询问我 spec 在哪. 如果我说没有, **Spec** 轴跳过并报告 `no spec available`.

完成标准: spec 状态已归类为路径, 已获取内容, 或 `no spec available`; 每个使用的来源都有路径, URL 或提交证据.

### 3. 确定规范来源

读取仓库中记录编码规范的文档, 如 `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `AGENTS.md`, lint/test 配置说明或项目文档中的开发约定.
除仓库文档外, Standards 轴始终携带 [Fowler 坏味道基线](references/fowler-baseline.md), 即使仓库无任何文档也适用. 两条规则约束:

- **仓库优先**: 仓库记录的规范始终胜出; 如果仓库规范认可了基线本会标记的写法, 抑制该坏味道.
- **始终是判断性发现**: 每个坏味道都是带标签的启发式判断, 如 `可能是 Feature Envy`; 绝不作硬性违规. 与本 skill 中任何规范一样, 跳过工具链已强制检查的内容.

完成标准: 规范来源文件列表已记录; Fowler 坏味道基线已读取; 已明确哪些检查由现有工具链强制覆盖, 没有则记录为无.

### 4. 运行双轴 review

启动 **Standards** 和 **Spec** 两个 reviewer. 若运行时不支持子 agent, 没有可用 reviewer, 或并行启动失败, 父会话按同一输入契约先运行 Standards 再运行 Spec, 最终格式不变.

**Standards reviewer 输入** 包含:

- 完整的 diff 命令和 commit 列表.
- 步骤 3 中找到的规范来源文件列表.
- `references/fowler-baseline.md` 全文. reviewer 没有其他途径获取这份基线.
- 任务简述: `报告按相关文件/hunk 组织. (a) diff 中每个违反已记录规范的位置, 引用规范文件和规则; (b) 你发现的任何基线坏味道, 列出名称并引用 hunk. 区分硬性违规和判断性发现. 违反已记录规范可能是硬性的, 基线坏味道始终是判断性发现, 且仓库已记录规范覆盖基线. 跳过工具链已强制检查的内容. 每个发现必须已读取对应 hunk 所在完整函数/方法及必要调用方; 无上下文支撑的坏味道不得报告. 400 词以内.`

**Spec reviewer 输入** 包含:

- 完整的 diff 命令和 commit 列表.
- spec 的路径或已获取的内容.
- 任务简述: `报告 (a) spec 要求但缺失或不完整的实现; (b) diff 中出现了但 spec 未要求的行为, 即范围蔓延; (c) 看似已实现但实现方式有误的需求. 每条发现引用 spec 原文. 每个发现必须已读取对应 hunk 所在完整函数/方法及必要调用方; 无 spec 证据不得报告. 400 词以内.`

如果 spec 缺失, 跳过 Spec reviewer 并在最终报告中注明.

完成标准: Standards 输出已获得; Spec 输出已获得或已明确跳过; 每个 reviewer 的输入都包含 diff 命令, commit 列表和本轴必需来源.

### 5. 汇总

在 `## Standards` 和 `## Spec` 标题下展示两份报告, 原文或略作清理. **切勿**合并或重排发现, 两条轴刻意分离.
以一行总结收尾: 每条轴的发现总数, 以及每条轴内最严重的问题 (如有). 不跨轴选最严重问题, 因为双轴分离正是为了防止重排.

完成标准: 最终报告包含 `## Standards`, `## Spec`, 每轴发现总数, 每轴内最严重问题或 `无`, 并保留两轴原有边界.

## 为何双轴

一处改动可能通过一条轴而失败于另一条:

- 代码遵循所有规范但实现了错误的功能 -> **Standards 通过, Spec 失败.**
- 代码精确实现了 issue 要求但破坏了项目约定 -> **Spec 通过, Standards 失败.**

分开报告, 防止一条轴掩盖另一条.
