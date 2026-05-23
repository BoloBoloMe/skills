# HTML 报告格式

架构评审会渲染为操作系统临时目录中的单个自包含 HTML 文件。Tailwind 和 Mermaid 都来自 CDN。Mermaid 能可靠处理图形结构的图；手写 div 和内联 SVG 用于更偏编辑表达的视觉图（质量图、剖面图）。两者混用——不要什么都依赖 Mermaid，否则看起来会很通用。

## 脚手架

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>架构评审 — {{repo name}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script type="module">
      import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
      mermaid.initialize({ startOnLoad: true, theme: "neutral", securityLevel: "loose" });
    </script>
    <style>
      /* Tailwind 无法干净覆盖的小型自定义层：
         虚线接缝线、手绘感箭头等。 */
      .seam { stroke-dasharray: 4 4; }
      .leak { stroke: #dc2626; }
      .deep { background: linear-gradient(135deg, #0f172a, #1e293b); }
    </style>
  </head>
  <body class="bg-stone-50 text-slate-900 font-sans">
    <main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
      <header>...</header>
      <section id="candidates" class="space-y-10">...</section>
      <section id="top-recommendation">...</section>
    </main>
  </body>
</html>
```

## 页眉

仓库名称、日期，以及紧凑图例：实线框 = 模块，虚线 = 接缝，红色箭头 = 泄漏，粗深色框 = 深模块。不要介绍段落——直接进入候选项。

## 候选卡片

图承担主要信息量。文字要稀疏、直白，并自然使用词汇表术语（[LANGUAGE.md](LANGUAGE.md)）。

每个候选项是一个 `<article>`：

- **标题**——简短，说明深化内容（例如“折叠 Order 接收流水线”）。
- **徽章行**——推荐强度（`强烈推荐` = emerald，`值得探索` = amber，`推测性` = slate），再加一个依赖类别标签（`进程内`、`可本地替代`、`端口与适配器`、`mock`）。
- **文件**——等宽列表，`font-mono text-sm`。
- **前 / 后图**——核心展示。两列并排。见下方模式。
- **问题**——一句话。哪里令人痛苦。
- **方案**——一句话。会改变什么。
- **收益**——项目符号，每条 ≤6 个词。例如“测试命中一个接口”、“定价逻辑停止泄漏”、“删除 4 个浅包装”。
- **ADR 提示**（如适用）——琥珀色提示框中的一行。

不要写解释性段落。如果图需要一段话才能被理解，就重画这张图。

## 图表模式

选择适合该候选项的模式。混合使用。不要让每张图看起来都一样——变化本身也是重点。

### Mermaid 图（依赖 / 调用流的主力）

当重点是“X 调用 Y 调用 Z，看这里多混乱”时，使用 Mermaid `flowchart` 或 `graph`。用 Tailwind 风格卡片包裹它，避免它像空降进来的。用 classDef 将泄漏边染红，将深模块染成深色。序列图很适合表达“之前：6 次往返；之后：1 次”。

```html
<div class="rounded-lg border border-slate-200 bg-white p-4">
  <pre class="mermaid">
    flowchart LR
      A[OrderHandler] --> B[OrderValidator]
      B --> C[OrderRepo]
      C -.leak.-> D[PricingClient]
      classDef leak stroke:#dc2626,stroke-width:2px;
      class C,D leak
  </pre>
</div>
```

### 手写方框和箭头（当 Mermaid 布局与你作对时）

模块用带边框和标签的 `<div>` 表示。箭头使用内联 SVG `<line>` 或 `<path>`，绝对定位在相对容器上。当你希望“之后”的图看起来像一个粗边框深模块、内部结构灰显时，就用这种方式——Mermaid 无法渲染出正确的重量感。

### 剖面图（适合分层浅薄）

堆叠水平带（`h-12 border-l-4`），展示一次调用穿过的层。之前：6 个几乎什么都不做的薄层。之后：1 个粗带，标注合并后的职责。

### 质量图（适合“接口和实现一样宽”）

每个模块两个矩形——一个表示接口表面积，一个表示实现。之前：接口矩形几乎和实现矩形一样高（浅）。之后：接口矩形很短，实现矩形很高（深）。

### 调用图折叠

之前：函数调用树渲染为嵌套框。之后：同一棵树折叠进一个框，已成为内部调用的部分在框内淡化显示。

## 样式指南

- 偏编辑风格，不要像企业仪表板。留白充足。标题可选衬线字体（`font-serif` 与 stone/slate 搭配很好）。
- 谨慎用色：一个强调色（emerald 或 indigo）加红色表示泄漏、琥珀色表示警告。
- 图保持约 320px 高，这样前/后并排时无需滚动也舒服。
- 在图中的模块标签使用 `text-xs uppercase tracking-wider`——它们应读起来像示意图，而不是 UI。
- 唯一脚本是 Tailwind CDN 和 Mermaid ESM import。除此之外报告是静态的——没有应用代码，除了 Mermaid 自身渲染外没有交互。

## 首要推荐章节

一个更大的卡片。候选项名称、一句说明为什么、指向其卡片的锚点链接。就这样。

## 语气

朴素中文，简洁——但架构名词和动词直接来自 [LANGUAGE.md](LANGUAGE.md)。简洁不是漂移的借口。

**必须精确使用：** 模块、接口、实现、深度、深、浅、接缝、适配器、杠杆效应、局部性。

**绝不替换为：** 组件、服务、单元（当你指模块时）· API、签名（当你指接口时）· 边界（当你指接缝时）· 层、包装器（当你指模块时）。

**符合这种风格的措辞：**

- “Order 接收模块很浅——接口几乎等同于实现。”
- “Pricing 跨接缝泄漏。”
- “深化：一个接口，一个测试位置。”
- “两个适配器证明接缝合理：生产用 HTTP，测试用内存。”

**收益项目符号**用词汇表术语命名收益：*“局部性：错误集中在一个模块”*、*“杠杆效应：一个接口，N 个调用点”*、*“接口收缩；实现吸收包装器”*。不要写*“更容易维护”*或*“更干净的代码”*——这些术语不在词汇表中，也没有赢得它们的位置。

不要犹豫，不要清嗓子，不要说“值得注意的是……”。如果一个句子可以成为项目符号，就把它做成项目符号。如果一个项目符号可以删，就删掉。如果某个术语不在 [LANGUAGE.md](LANGUAGE.md) 中，在发明新术语前先找一个已有术语。
