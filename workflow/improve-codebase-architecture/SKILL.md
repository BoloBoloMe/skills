---
name: improve-codebase-architecture
description: 代码库复杂度, 模块边界, 可测试性, 重构候选的架构审查.
disable-model-invocation: true
---

开始前, 使用 `domain-awareness` skill 只读感知当前工作目录的领域模型.

# 改进代码库架构

发现架构摩擦并提出 **deepening 机会** - 将 shallow module 重构为 deep module 的变更. 目标是可测试性和 AI 可导航性.

本 skill 受项目领域模型启发, 并建立在共享设计词汇之上:

- 使用 `codebase-design` skill 获取架构词汇 (**module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality**) 及其原则 (删除测试, "interface 是测试表面", "一个 adapter = 假想 seam, 两个 = 真实"). 在每个建议中精确使用这些术语 - 不要混用 "component", "service", "API" 或 "boundary".
- `docs/language/UBIQUITOUS_LANGUAGE.md` 中的领域语言为好的 seam 赋名. 多上下文项目先读取 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md`. `docs/adr/` 中的 ADR 记录了本 skill 不应重新审视的决策.

## 流程

### 1. 探索

首先阅读项目的领域术语表: 单上下文项目读取 `docs/language/UBIQUITOUS_LANGUAGE.md`; 多上下文项目先读取 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md`, 再读取相关 `docs/language/contexts/*.md`. 同时阅读你正在触及区域的 ADR.

然后直接探索代码库. 如需分派只读 scout 压缩上下文, 按子代理规则委派. 不遵循死板启发式 - 自然探索, 注意经历摩擦的地方:

- 理解一个概念需要在许多小模块之间跳转?
- 模块是 **shallow** 的 - interface 几乎与 implementation 一样复杂?
- 纯函数仅为可测试性而被提取, 但真正的 bug 藏在它们的调用方式里 (没有 **locality**)?
- 紧密耦合的模块跨它们的 seam 泄漏?
- 代码库哪些部分未经测试, 或难以通过当前 interface 测试?

对你怀疑是 shallow 的任何东西应用 **删除测试**: 删除它会集中复杂性, 还是只是移动它? 回答"是, 集中了"才是你想要的信号.

### 2. 将候选呈现为 HTML 报告

向 OS 临时目录写入一个自包含的 HTML 文件, 这样不会有任何东西落入仓库. 从 `$TMPDIR` 解析临时目录, 回退到 `/tmp` (或 Windows 上的 `%TEMP%`), 写入 `<tmpdir>/architecture-review-<timestamp>.html`, 使每次运行获得一个新文件. 为用户打开它 - Linux 上 `xdg-open <path>`, macOS 上 `open <path>`, Windows 上 `start <path>` - 并告诉他们绝对路径.

报告使用 **Tailwind via CDN** 进行布局和样式, **Mermaid via CDN** 用于图表 (当图/流/序列可靠传达结构时). Mermaid 与手工 CSS/SVG 视觉混合 - 关系是图形的 (调用图, 依赖, 序列) 时用 Mermaid; 想要更编辑性的呈现 (mass diagram, cross-section, collapse animation) 时用手工 div/SVG. 每个候选获得一个 **before/after 可视化**. 强调可视化.

对每个候选渲染一个卡片, 包含:

- **Files** - 涉及哪些文件/模块
- **Problem** - 当前架构为什么产生摩擦
- **Solution** - 用通俗语言描述什么会变化
- **Benefits** - 以 locality 和 leverage 解释, 以及测试会如何改善
- **Before / After diagram** - 并排, 自定义绘制, 展示 shallow 和 deepening
- **Recommendation strength** - `Strong`, `Worth exploring`, `Speculative` 之一, 渲染为徽章

报告末尾以 **Top recommendation** 章节: 你会先处理哪个候选以及原因.

**使用 `docs/language/UBIQUITOUS_LANGUAGE.md` 或相关 `docs/language/contexts/*.md` 词汇指代领域, `codebase-design` skill 词汇指代架构.** 如果词汇表定义了 "Order", 说 "the Order intake module" - 不是 "the FooBarHandler", 也不是 "the Order service".

**ADR 冲突**: 候选与现有 ADR 矛盾时, 仅在摩擦足以值得重新审视该 ADR 时才展示. 在卡片中清楚标记 (例如警告提示: _"与 ADR-0007 矛盾 - 但值得重新打开, 因为..."_). 不要列出 ADR 禁止的每一个理论重构.

见 [HTML-REPORT.md](HTML-REPORT.md) 获取完整的 HTML 脚手架, 图表模式和样式指导.

**不要** 此时提出 interface. 文件写入后, 询问用户: "你想探索哪一个?"

### 3. Grilling 循环

用户选定一个候选后, 使用 `grilling` skill 与他们一起走设计树 - 约束, 依赖, deepened module 的形状, seam 背后是什么, 哪些测试保留.

副作用在决策结晶时内联发生 - 使用 `domain-modeling` skill 保持领域模型随行更新:

- **用不在领域语言文件中的概念命名一个 deepened module?** 使用 `domain-modeling` skill, 将术语添加到 `docs/language/UBIQUITOUS_LANGUAGE.md` 或相关 `docs/language/contexts/*.md`. 文件不存在则惰性创建.
- **在对话中打磨了一个模糊术语?** 使用 `domain-modeling` skill, 在对应领域语言文件中更新.
- **用户以有力理由拒绝了候选?** 提议 ADR, 表述为: _"记为 ADR 吗? 这样未来架构审查不会再建议它."_ 仅当该理由确实需要让未来探索者避免重复建议同一方案时才提议 - 跳过短暂理由 ("目前不值得") 和不言自明的理由.
- **想为 deepened module 探索替代 interface?** 使用 `codebase-design` skill 及其 design-it-twice 并行 sub-agent 模式.
