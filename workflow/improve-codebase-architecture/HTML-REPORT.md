# HTML 报告格式

架构审查渲染为 OS 临时目录中的单一自包含 HTML 文件. Tailwind 和 Mermaid 都来自 CDN. Mermaid 在图形状的图表上可靠; 手工 div 和 inline SVG 处理更编辑性的视觉 (mass diagram, cross-section). 两者混合 - 不要对所有东西都依赖 Mermaid, 它会开始看起来千篇一律.

## 脚手架

```html
<!doctype html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8" />
    <title>架构评审 - {{repo name}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script type="module">
        import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
        mermaid.initialize({ startOnLoad: true, theme: "neutral", securityLevel: "loose" });
    </script>
    <style>
        /* Tailwind 无法干净覆盖的小型自定义层:
           虚线接缝线,手绘感箭头等. */
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

## 头部

仓库名称, 日期, 和简洁图例: 实线框 = module, dashed 线 = seam, 红色箭头 = 泄漏, 粗深框 = deep module. 不写介绍段落 - 直奔候选.

## 候选卡片

图表承担重量. 文字稀少, 通俗, 使用术语表术语 (来自 `/codebase-design` 技能) 而不做任何仪式.

每个候选是一个 `<article>`:

- **Title** - 短, 命名 deepening (例如 "Collapse the Order intake pipeline").
- **Badge row** - recommendation strength (`Strong` = emerald, `Worth exploring` = amber, `Speculative` = slate), 加上依赖类别标签 (`in-process`, `local-substitutable`, `ports & adapters`, `mock`).
- **Files** - monospaced 列表, `font-mono text-sm`.
- **Before / After diagram** - 核心内容. 两列, 并排. 见下方模式.
- **Problem** - 一句话. 什么痛苦.
- **Solution** - 一句话. 什么改变.
- **Wins** - 条目, 每条 <= 10 个汉字或短语. 例如 "测试命中一个 interface", "Pricing 不再泄漏", "删除 4 个 shallow wrapper".
- **ADR callout** (如适用) - amber 浅色提示框中的一行.

没有解释段落. 如果一个图表需要一段文字才能理解, 重画图表.

## 图表模式

选择适合候选的模式. 混合使用. 不要让每个图表看起来一样 - 多样性是部分目的.

### Mermaid graph (依赖/调用流的主力)

当要点是 "X 调用 Y 调用 Z, 看这一团糟" 时使用 Mermaid `flowchart` 或 `graph`. 用 Tailwind 样式卡片包裹它, 不要让它看起来是临时空降的. 用 classDef 将泄漏边标红, deep module 标暗色. Sequence diagram 适合 "之前: 6 次往返; 之后: 1 次."

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

### 手工 boxes-and-arrows (当 Mermaid 的布局与你对抗时)

模块作为带边框和标签的 `<div>`. 箭头作为在 relative 容器上 absolute 定位的 inline SVG `<line>` 或 `<path>` 元素. 当你想让 "after" 图表感觉像一个粗边框 deep module, 内部灰掉 - Mermaid 不会以正确的重量渲染它.

### Cross-section (适合分层 shallow)

堆叠水平条带 (`h-12 border-l-4`) 来展示一次调用穿过的层. Before: 6 个薄层每个什么都不做. After: 1 个厚条带标注着合并的责任.

### Mass diagram (适合 "interface 与 implementation 一样宽")

每个模块两个矩形 - 一个表示 interface 表面面积, 一个表示 implementation. Before: interface 矩形几乎与 implementation 矩形一样高 (shallow). After: interface 矩形短, implementation 矩形高 (deep).

### 调用图折叠

Before: 一棵函数调用树渲染为嵌套框. After: 同一棵树坍缩为一个框, 现在内部的调用在其内部以淡色显示.

## 样式指导

- 倾向编辑性, 不是企业仪表盘. 充裕的留白. Serif 可选用于标题 (`font-serif` 与 stone/slate 配合良好).
- 谨慎用色: 一个强调色 (emerald 或 indigo) 加红色用于泄漏, amber 用于警告.
- 保持图表 ~320px 高, 使 before/after 并排时不需滚动.
- 在图表内部使用 `text-xs uppercase tracking-wider` 标注模块标签 - 它们应读作示意图, 不是 UI.
- 唯一的脚本是 Tailwind CDN 和 Mermaid ESM import. 报告其余部分是静态的 - 无应用代码, 无交互性 (除 Mermaid 自身的渲染).

## Top recommendation 部分

一个更大的卡片. 候选名称, 一句话说为什么, anchor 链接到其卡片. 就这样.

## 语气

朴素中文, 简洁 - 但架构名词和动词直接来自 `/codebase-design` 技能. 简洁不是漂移的借口.

**精确使用:** module, interface, implementation, depth, deep, shallow, seam, adapter, leverage, locality.

**绝不替换:** component, service, unit (指 module) * API, signature (指 interface) * boundary (指 seam) * layer, wrapper (指 module, 当你意指 module).

**符合风格的表述:**

- "Order intake module 是 shallow 的 - interface 几乎与 implementation 匹配."
- "Pricing 在 seam 上泄漏."
- "Deepen: 一个 interface, 一个测试的地方."
- "两个 adapter 证明 seam: 生产中 HTTP, 测试中内存."

**Wins 条目** 用术语表术语命名收益: *"locality: bug 集中在一个 module 中"*, *"leverage: 一个 interface, N 个调用点"*, *"interface 缩小; implementation 吸收 wrapper"*. 不写 *"更容易维护"* 或 *"更干净的代码"* - 这些术语不在术语表中, 没有挣到它们的位置.

不做 hedging, 不做 throat-clearing, 不写 "值得注意的是...". 如果一句话可以成为条目, 让它成为条目. 如果一个条目可以削减, 削减它. 如果一个术语不在 `/codebase-design` 术语表中, 在发明新术语之前寻找一个已存在的.
