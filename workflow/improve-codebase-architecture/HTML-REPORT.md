# HTML 报告格式

架构审查报告由 `adaptive-presentation` skill 生成与展示: 自包含 HTML, 临时目录, 视觉风格, 浏览器展示均遵循其规则. 本文件只携带架构报告的内容结构与图表模式增量.

## 头部

仓库名称, 日期, 和简洁图例: 实线框 = module, 虚线 = seam, 红色箭头 = 泄漏, 粗深框 = deep module. 不写介绍段落 - 直奔候选.

## 候选卡片

图表承担重量. 文字稀少, 通俗, 使用术语表术语 (来自 `codebase-design` skill) 而不做任何仪式.

每个候选是一个 `<article>`:

- **Title** - 短, 命名 deepening (例如 "Collapse the Order intake pipeline").
- **Badge row** - recommendation strength (`Strong` / `Worth exploring` / `Speculative`), 加上依赖类别标签 (`in-process`, `local-substitutable`, `ports & adapters`, `mock`).
- **Files** - 等宽字体列表.
- **Before / After diagram** - 核心内容. 两列, 并排. 见下方模式.
- **Problem** - 一句话. 什么痛苦.
- **Solution** - 一句话. 什么改变.
- **Wins** - 条目, 每条 <= 10 个汉字或短语. 例如 "测试命中一个 interface", "Pricing 不再泄漏", "删除 4 个 shallow wrapper".
- **ADR callout** (如适用) - 警告色提示框中的一行.

没有解释段落. 如果一个图表需要一段文字才能理解, 重画图表.

## 图表模式

全部用 inline SVG 和 HTML+CSS 手工绘制. 混合使用. 不要让每个图表看起来一样 - 多样性是部分目的.

### 流程与依赖图 (主力)

当要点是 "X 调用 Y 调用 Z, 看这一团糟" 时, 用手工 boxes-and-arrows: 模块作为带边框和标签的 `<div>` 或 SVG `<rect>`, 箭头作为 relative 容器内 absolute 定位的 inline SVG `<line>`/`<path>`. 虚线描边表示 seam, 红色边表示泄漏, 深色实心框表示 deep module. 往返次数标注在边上 ("之前: 6 次往返; 之后: 1 次").

### Cross-section (适合分层 shallow)

堆叠水平条带来展示一次调用穿过的层. Before: 6 个薄层每个什么都不做. After: 1 个厚条带标注着合并的责任.

### Mass diagram (适合 "interface 与 implementation 一样宽")

每个模块两个矩形 - 一个表示 interface 表面面积, 一个表示 implementation. Before: interface 矩形几乎与 implementation 矩形一样高 (shallow). After: interface 矩形短, implementation 矩形高 (deep).

### 调用图折叠

Before: 一棵函数调用树渲染为嵌套框. After: 同一棵树坍缩为一个框, 现在内部的调用在其内部以淡色显示.

## 增量样式

视觉风格遵循 `adaptive-presentation`; 报告只追加:

- Before/after 图并排, 高度约 320px, 不需滚动即可同屏对比.
- 图表内模块标签用小号大写字母加宽字距, 读作示意图, 不是 UI.
- 颜色纪律: 红 = 泄漏, 警告色 = ADR 冲突, 一个强调色渲染 recommendation strength 徽章; 其余用低饱和自然色.

## Top recommendation 部分

一个更大的卡片. 候选名称, 一句话说为什么, anchor 链接到其卡片. 就这样.

## 语气

朴素中文, 简洁 - 但架构名词和动词直接来自 `codebase-design` skill. 简洁不是漂移的借口.

**精确使用:** module, interface, implementation, depth, deep, shallow, seam, adapter, leverage, locality.

**绝不替换:** component, service, unit (指 module) * API, signature (指 interface) * boundary (指 seam) * layer, wrapper (指 module, 当你意指 module).

**符合风格的表述:**

- "Order intake module 是 shallow 的 - interface 几乎与 implementation 匹配."
- "Pricing 在 seam 上泄漏."
- "Deepen: 一个 interface, 一个测试的地方."
- "两个 adapter 证明 seam: 生产中 HTTP, 测试中内存."

**Wins 条目** 用术语表术语命名收益: *"locality: bug 集中在一个 module 中"*, *"leverage: 一个 interface, N 个调用点"*, *"interface 缩小; implementation 吸收 wrapper"*. 不写 *"更容易维护"* 或 *"更干净的代码"* - 这些术语不在术语表中, 没有挣到它们的位置.

不做 hedging, 不做 throat-clearing, 不写 "值得注意的是...". 如果一句话可以成为条目, 让它成为条目. 如果一个条目可以削减, 削减它. 如果一个术语不在 `codebase-design` skill 术语表中, 在发明新术语之前寻找一个已存在的.
