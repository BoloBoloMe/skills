# milestone-12 代码库结构可视化侦查

- 任务标识: m12-research
- 性质: 事实侦查与方案对比, 不实现工具, 不改任何 skill, 不改本仓库其他文件
- 目标: 为计划中的 "代码库结构可视化" skill 打底, 要求读任意目标代码库, 把分层和模块关系画成网页, 观感像城市地图 (模块是建筑/街区, 分层是高度或区域, 依赖是道路), 既可被 `workflow/to-spec` 在技术规格盘问时调用, 也可手动点名看一眼
- 环境以 2026-10-31 为准 (本容器 `date` 显示 2026 年)

## 0 结论速览

1. 想直接拿到 "城市" 观感, 现成方案里只有 CodeCharta 一家能做到, 而且它的分析端 (ccsh) 要 Node 22.19 以上加 Java 22 以上, 与本仓库纯 python + uv 的栈冲突.
2. 但实测发现一条绕开分析端的路: CodeCharta 官方发布物里有一个 3.5MB 的 `web.zip`, 解压后就是完整的静态前端 (46 个文件, 6.2MB), 不联网, 不需要 Java/Node, 只要一个本地 http 服务就能打开; 它吃的 `.cc.json` 是公开的交换格式, 文档明确写着 "可以从你自己的工具生成". 我用 40 行 python 手写了一个 cc.json, 3D 城市视图和分层依赖视图都正常显示, 自定义的 `layer` 属性还能被选成建筑高度. 这是本次最实用的发现.
3. 只要二维关系图不追求城市观感的话, cytoscape.js 单个 435KB 文件内联进 HTML, `file://` 直接打开就能画出分层布局 (实测通过). 这是零外部资产的备用路线.
4. 不能用的: ccsh (Java 22 + Node 22.19), Gource (要 OpenGL 硬件加速, 而且画的是 git 历史不是模块结构), mermaid-cli (要 Chromium), graphviz 系 (要系统库 dot, 本容器没有), Sourcetrail / SoftVis3D / DependaCharta (全部归档, 停止维护), git-truck (没有依赖关系, 只有 git 活跃度).
5. 分层这件事本身是分析问题, 不是渲染问题: 要算模块的层号 (levelization), 要标出环和 "向上依赖". 现成工具里只有 CodeCharta 的 dependencyparser 直接把层号算进产物; dependency-cruiser / madge / pydeps 只出图, 层号得我们自己算 (最长路径分层加环检测, 代码量很小).

## 1 侦查方法与证据边界

做法: 先用 GitHub API 和 GitLab API 取仓库元数据 (star, 许可, 最后 push 时间, 是否归档), 再逐个读官网/文档/README 取能力描述, 关键结论在本容器内实跑验证 (下载 web.zip 起服务截图, 内联 cytoscape.js 打开截图, 跑 pydeps 看报错). 没核实到的直接标 "未核实", 不凭记忆下结论.

本容器实测环境 (与 "引进依赖的成本" 有关):

| 项 | 状态 |
| --- | --- |
| 系统 | Debian 12 (bookworm), 16 核, 30GB 内存 |
| python | 3.11.2, uv 0.13.1 |
| node / npm | v24.21.0 / 11.19.0 (镜像自带, 本仓库自身不用) |
| java | 缺席 |
| graphviz `dot` | 缺席 |
| docker | 缺席 |
| 仓库自身 | 无任何 `package.json`, 纯 python + uv (只有 access-web 的 venv 里带了依赖的 node 包) |

所以结论里凡涉及 "要 node / 要 java / 要 dot / 要 docker" 的, 引进到本仓库都是新增一条工具链, 不是顺手就有.

## 2 候选方案逐个档案

### 2.1 CodeCharta

结论: 唯一开箱给出 "3D 城市 + 分层依赖图" 的方案, 多语言支持最广, 但分析端技术栈与本仓库不合; 前端可以单独拿来用.

| 项 | 事实 | 来源 |
| --- | --- | --- |
| 许可 | BSD 3-Clause | GitHub API `MaibornWolff/codecharta` |
| 维护 | 活跃, 最后 push 2026-10-30; 分析端发布 ana-2.3.0 (2026-10-28), 前端发布 vis-2.9.1 (2026-10-23) | GitHub API releases |
| star | 563 (相对小众) | GitHub API |
| 实现语言 | Kotlin (分析端) / TypeScript (前端) | GitHub API |

能力:

- 语言覆盖 (源码度量 parser, 基于 tree-sitter, 20 种): JavaScript, TypeScript, TSX, Java, Kotlin, C#, C/C++, Objective-C, Python, Go, PHP, Ruby, Swift, Bash, Vue, Delphi, Rust, Angular 模板 (`.html`), SQL.
- 依赖 parser (实验性, 移植自已归档的 DependaCharta): Java, Kotlin, C#, C/C++, Go, Python, PHP, TypeScript, JavaScript, Vue, Delphi, Rust, Angular 模板, SQL; 按每种语言自己的 import 解析规则处理, 还认 tsconfig/jsconfig 路径别名, webpack/vite/vue.config 别名, Go 的 `go.mod`.
- 分层能力 (关键): 依赖 parser 直接输出层号 `level` (0 表示不依赖任何东西), 边缘标 `isCyclic` (在环里) 和 `isPointingUpwards` (逆着层级流向, 即架构违规), 还有声明级 (类/函数) 的 `leaves` / `namespaces` / `leafEdges` 和用法分类 (`usage`, `inheritance`, `implementation`, `instantiation` 等).
- 视图: 三个, Metric (3D 城市, 面积/高度/颜色可绑任意指标), Domain (词云), Dependencies (按层堆叠的 2D 图, 默认只显示环和向上依赖).
- 交互: 强. 缩放旋转, 搜索过滤, 点击看详情, 多场景 (scenario), 两个版本对比, 3D 打印导出.
- 分层是不是 "高度": 默认不是. 默认面积=代码行, 高度=复杂度. 但指标可以在界面里重新绑, 而 cc.json 里的属性表是开放的, 所以自己算好 `layer` 属性写进去就能把高度设成层号 (见 5.2 实测).

产物与依赖成本:

| 路径 | 需要的运行时 | 是否离线 | 备注 |
| --- | --- | --- | --- |
| `npm i -g codecharta-analysis` 出 cc.json | Node 22.19+ 和 Java 22+ | 装完可离线跑 | 文档明写 "You need Node 22.19 or newer and Java 22 or newer" |
| Docker 分析镜像 `codecharta/codecharta-analysis` | docker | 离线 | 镜像里带 git/tokei/code-maat/sonar-scanner |
| 桌面端 (Electron) | 无 | 离线 | 单个平台包 126-400MB, 太重 |
| `web.zip` 静态前端 | 只要一个静态 http 服务 | 完全离线 | 3.5MB, 解压 46 个文件 6.2MB, 实测可用 |

一句话: 分析端贵, 前端便宜.

### 2.2 dependency-cruiser

结论: JavaScript/TypeScript 依赖图的成熟方案, 输出格式最多, 还能直接吐 d2 和 mermaid; 但它只懂 JS 系, 且自身不算分层 (靠 dot 布局和目录汇总).

- 许可 MIT, star 7355, 最后 push 2026-10-30, 很活跃.
- 语言: JavaScript, TypeScript, CoffeeScript; ES6/CommonJS/AMD 模块系统. `.vue`/`.svelte` 是否支持未核实.
- 运行要求: `engines.node` 为 `^22||^24||>=26`, 直接依赖 18 个 (npm 上最新版 18.7.0).
- 输出 (`--output-type`): `err`, `err-long`, `err-html`, `dot`, `ddot` (汇总到目录层), `archi`/`cdot` (按自己指定的模式折叠, 官方说适合高层总览), `flat`/`fdot`, `dot-webpage` (把 dot 渲染结果包进带悬停高亮的 html), `mermaid`, `d2`, `markdown`, `html` (依赖矩阵表, 不是图), `csv`, `json`, `anon`, `text`, `teamcity`, `azure-devops`, `metrics`.
- 是否分层: 没有 levelization. 有的是 `--metrics` 算出的 instability 指标 (稳定依赖原则), 以及用规则文件禁止 "从 A 层指向 B 层", 违规在报告里列出来. 图长什么样交给 Graphviz dot 决定.
- 2D. 交互程度: `dot-webpage` 有悬停高亮和点击跳源码, 其余是静态文件.
- 要出图 (不只出文本) 必须有 graphviz 的 `dot` 二进制, 文档明说 "This assumes the GraphViz dot command is available".

### 2.3 madge

结论: 轻量 JS 依赖图, 装起来最简单, 但能力比 dependency-cruiser 少, 只出静态图.

- 许可 MIT, star 10178, 最后 push 2026-01-21 (三者里最慢但仍活跃), npm 最新 8.0.0, `engines.node >= 18`.
- 语言: JavaScript (AMD/CommonJS/ES6), 外加 CSS 预处理器 (Sass/Stylus/Less). TypeScript 要通过 `tsConfig` 选项配置解析, 混用 JS 和 TS 时要同时给 `webpackConfig` 和 `tsConfig`, README 有专门章节讲这个坑.
- 输出: DOT 文本, 图片 (svg/png, 格式由扩展名决定), JSON. 有 `circularOnly` 只画环.
- 是否分层: 没有. 只有循环依赖检测和目录聚类 (Graphviz 的 cluster).
- 2D, 静态, 基本无交互 (输出的 svg 本身可在浏览器里缩放).
- Graphviz 被文档标为 "optional", 只有生成图片时才需要.

### 2.4 skott (本次新发现)

结论: JS/TS 生态里少见的 "自带交互式网页" 的分析器, 但只懂 JS 系.

- 许可 MIT, star 877, 最后 push 2026-09-11.
- 语言: JavaScript, TypeScript (JSX/TSX), Node.js.
- 自带 webapp 视图, 本地起服务看 (要 Node), 2D.
- 与本仓库栈不合; 若目标库恰好是 JS/TS 且允许用 node, 它的 JSON 输出可以考虑, 但不如 dependency-cruiser 的输出格式丰富.

### 2.5 pydeps

结论: Python 专用的依赖图工具, 用法最省事, 但只出静态图片, 且强依赖系统 graphviz.

- 许可 BSD-2-Clause, star 2121, 最后 push 2026-10-30, 活跃; PyPI 3.0.9, 纯 python 包 (实测 `uv run --with pydeps` 只装 2 个包).
- 语言: 只有 Python.
- 输出: svg 或 png (靠 graphviz 的 `dot`), 也可以只输出 dot 文本 (`--dot-output`). 没有 HTML, 没有交互.
- 是否分层: 没有显式层号. 有的是 `--max-bacon` (按跳数裁深度), `--cluster` (把外部依赖聚成簇), `--rankdir` (布局方向).
- 文档明写要装 Graphviz 才能出图.
- 实测坑: 在本仓库根目录跑 `pydeps sync-to-pi.py` 直接失败, 它要求目录名/文件名能当合法的 python 标识符 (本仓库目录名 `refactor-skill-around-verification` 带 `-`), 报错提示改名或用可导入的包名去指. 换句话说它对 "任意目标库" 不友好, 只能对合法的 python 包运行.

### 2.6 importlab

结论: 只是库, 不是给人用的工具, 而且已经归档.

- 许可 Apache-2.0, star 179, 最后 push 2024-05-03, **已归档 (archived)**; PyPI 0.8.1.
- 只做 Python 导入依赖推断, 是 pytype 的内部依赖. 无渲染, 无 CLI 面向用户.
- 现在没有维护, 不建议引进.

### 2.7 grimp

结论: 纯 python 侧的 python 导入图库, 适合我们自建方案的 "分析" 那一半.

- 许可 BSD-2-Clause, PyPI 3.18, 无运行时依赖, 有各平台预编译轮子 (`requires_dist` 为空).
- 只懂 Python, 不做渲染, 提供可查询的图 (谁 import 谁, 是否形成环).
- 相比自己写 `ast` 遍历 + 路径解析, 它把 "模块名到文件" 的解析坑处理掉了, 成本低.

### 2.8 code2flow / pyan (补充)

- code2flow: 许可 MIT, star 4619, 最后 push 2025-07-27. 画的是**调用图**不是模块依赖图, 支持 Python/JS/Ruby/PHP; 除 Python 外都要另装对应语言的解析器 (acorn / parser / php-parser), 并且要 graphviz.
- pyan3: 许可 GPL-2.0 (注意 copyleft), 最后 push 2026-10-26, Python 静态调用图, 要 graphviz.
- 这两个的定位是 "函数谁调谁", 与本次要的 "模块分层" 不是一回事, 只在需要看函数级细节时才有用.

### 2.9 d2 (渲染器)

结论: 目前质量最好的文本转图渲染器, 单二进制无运行时依赖, 但它只负责 "画", 图得别人给.

- 许可 MPL-2.0, star 25770, 最后 push 2026-10-11, 活跃; Go 写的, 官方提供预编译二进制和安装脚本.
- 布局: dagre (默认), ELK, TALA (官方自研, 专为软件架构图设计).
- 导出: SVG (默认), PNG, PDF, PPTX, GIF, ASCII. 文档明确说 "PNG exports have no external dependencies. D2 renders them directly, unlike Mermaid, which uses a headless browser like Chromium".
- 2D. 交互: 输出是静态 SVG, 只有链接和动画这类静态交互, 没有缩放探索, 没有 "点开某个模块".
- 结论: 适合把一张结构图放进文档, 不适合 "给我一张能点着看的网页".

### 2.10 mermaid (渲染器)

结论: 生态最大, 但渲染要么靠浏览器要么靠 Chromium, 且只出静态图.

- 主库许可 MIT, star 90941, 最后 push 2026-10-31.
- CLI (`@mermaid-js/mermaid-cli`, 也 MIT) 把 mermaid 定义转 svg/png/pdf; 它把 `puppeteer ^25` 作为 peer 依赖, 也就是要一个 Chromium. 另有 Docker 镜像 `minlag/mermaid-cli`.
- 2D, 静态, 无探索式交互.
- 本仓库已有先例: `general/present/vendor/mermaid.min.js` (3.5MB) 被内联进单页 HTML 由浏览器渲染, 说明 "把渲染库塞进仓库" 这条路本仓库已经走过.

### 2.11 graphviz (渲染器)

结论: 布局算法的老祖宗, 但它是系统库而不是 python 包, 本仓库引进要装二进制.

- 许可 EPL-2.0 (主仓 `LICENSE` 文件实测内容为 Eclipse Public License v 2.0).
- 主仓在 GitLab: `gitlab.com/graphviz/graphviz`, GitLab star 1475, 最后提交 2026-10-30, 活跃. GitHub 上的 `graphviz/graphviz` 已不是开发主仓 (GitHub API 显示 archived, 无 push 记录, 5 star), 查维护状态别查错地方.
- 用法: 吃 dot 文本, 出 svg/png 等. 2D, 静态, 无交互.
- 本容器没有 `dot`; python 的 `graphviz` 包只是拼 dot 文本, 调用二进制, 装 pip 包不等于能出图.

### 2.12 Gource (补充对比)

结论: 最像 "城市" 的开源可视化, 但画的是 git 提交历史, 而且强依赖 OpenGL 硬件加速.

- 许可 GPL-3.0 (copyleft), star 13182, 最后 push 2026-03-06.
- README 明确写: "Gource's display is rendered using OpenGL and requires a 3D accelerated video card to run".
- 它按提交时间把文件和目录长成一座城, 但没有 "模块 A 依赖模块 B" 的边, 也没有层号.
- 容器里没有 GPU, 这个方案基本不可行 (要视频输出还得 ffmpeg).

### 2.13 已归档或不合适的

| 方案 | 状态 | 为什么不合适 |
| --- | --- | --- |
| Sourcetrail | GPL-3.0, 16464 star, **归档**, 最后 push 2021-12-13 | 交互式源码浏览器 (引用/调用图) 曾经最好用, 但 2021 年停更, 不会再支持新语言和编译器 |
| DependaCharta | BSD-3-Clause, 18 star, **归档** | 它的能力已经被移植进 CodeCharta 的 dependencyparser (文档里写明是 port), 直接看 CodeCharta 即可 |
| SoftVis3D | LGPL-3.0, 64 star, **归档**, 最后 push 2023-09-18 | SonarQube 的 3D 城市插件, 停更, 且要先有 SonarQube |
| git-truck | MIT, 782 star, 最后 push 2026-10-12 | 交互式 git 仓库可视化, 要 Node + git, 本地起服务; 它把文件大小/提交数/作者映射到方块, **没有依赖关系**, 不能表达分层 |
| Understand / Structure101 / Lattix (商业) | 未核实 | 本次没有访问其官网, 不下结论; 仅记录 "商业闭源, 不在本仓库可引进范围" 这一点 |

## 3 输出产物形态与安装成本

| 方案 | 产物 | 必须起服务? | 能否完全离线 | 安装成本 |
| --- | --- | --- | --- | --- |
| CodeCharta ccsh | `.cc.json` | 否 (生成阶段) | 是 (装完以后) | 重: Node 22.19+ 和 Java 22+ |
| CodeCharta web.zip 前端 | 静态站点 + cc.json | 是 (一个静态 http 服务; `file://` 实测失败) | 是 | 轻: 3.5MB 静态文件, 零运行时 |
| dependency-cruiser | dot / mermaid / d2 / html / json 等 | 否 | 是 | 中: Node 22+, 要出图还要 graphviz dot |
| madge | dot / svg / png / json | 否 | 是 | 中: Node 18+, 出图要 graphviz dot |
| skott | 本地 webapp + json | 是 (它自己起服务) | 是 | 中: Node |
| pydeps | svg / png / dot | 否 | 是 | 中: python 包 + 系统 graphviz |
| d2 | svg / png / pdf / pptx / gif | 否 | 是 | 轻: 单二进制 |
| mermaid-cli | svg / png / pdf | 否 | 是 | 重: Node + Chromium |
| graphviz | svg / png | 否 | 是 | 中: 系统包 (`dot`) |
| Gource | 窗口动画 / 视频 | 否 | 是 | 重: OpenGL 硬件加速 + ffmpeg |
| 自建 python + 单页 HTML (cytoscape.js) | 单个 .html | 否 (`file://` 实测可开) | 是 | 轻: 一个 435KB 的 JS 文件 |

`file://` 那一条值得强调: CodeCharta 静态前端从 `file://` 打开会白屏, 原因是它用 ES 模块分块加载, `file://` 下 `origin` 是 `null`, 控制台报 "blocked by CORS policy / net::ERR_FAILED"; 换成本地 http 服务后同一个目录立刻正常 (两种情形都实测过, 有截图). 这不是 CodeCharta 的 bug, 是现代打包产物的通病, 自建方案如果也想 `file://` 直开, 就必须用单文件 UMD 打包 (cytoscape.js 那种).

## 4 维护状态与许可汇总

数据取自 2026-10-31 的 GitHub API / GitLab API 与包注册表, 不是记忆.

| 方案 | star | 最后 push / 提交 | 许可 | 归档 | 适合作为本仓库依赖? |
| --- | --- | --- | --- | --- | --- |
| CodeCharta (分析端 ccsh) | 563 | 2026-10-30 | BSD-3-Clause | 否 | 不适合 (要 Java 22 + Node 22.19) |
| CodeCharta (web.zip 前端) | 同上 | vis-2.9.1, 2026-10-23 | BSD-3-Clause | 否 | 可以, 作为 vendored 静态资产, 需保留版权声明 |
| dependency-cruiser | 7355 | 2026-10-30 | MIT | 否 | 视需求, 需 Node ^22 (直接依赖 18 个) |
| madge | 10178 | 2026-01-21 | MIT | 否 | 视需求, 需 Node 18+ 与 graphviz |
| skott | 877 | 2026-09-11 | MIT | 否 | 视需求, 需 Node |
| pydeps | 2121 | 2026-10-30 | BSD-2-Clause | 否 | 可以 pip, 但只能 python 且要系统 graphviz |
| importlab | 179 | 2024-05-03 | Apache-2.0 | **是** | 不适合 (停更) |
| grimp | 未核实 (未查 star) | PyPI 3.18 | BSD-2-Clause | 否 | 可以, 纯 python 依赖图 |
| code2flow | 4619 | 2025-07-27 | MIT | 否 | 只能出调用图, 且要 graphviz |
| d2 | 25770 | 2026-10-11 | MPL-2.0 | 否 | 可以 (单二进制), 但只解决渲染 |
| mermaid | 90941 | 2026-10-31 | MIT | 否 | 可以, 本仓库已有 vendor 先例 |
| graphviz | GitLab 1475 | 2026-10-30 | EPL-2.0 | 否 | 要装系统库, 本容器没有 |
| Gource | 13182 | 2026-03-06 | GPL-3.0 | 否 | 不适合 (要 GPU, 且不是结构图) |
| Sourcetrail | 16464 | 2021-12-13 | GPL-3.0 | **是** | 不适合 |
| DependaCharta | 18 | 2026-10-20 | BSD-3-Clause | **是** | 不适合 (能力已并入 CodeCharta) |
| SoftVis3D | 64 | 2023-09-18 | LGPL-3.0 | **是** | 不适合 |
| git-truck | 782 | 2026-10-12 | MIT | 否 | 不适合 (没有依赖关系) |
| cytoscape.js | 11258 | 2026-10-30 | MIT | 否 | 可以 (单文件内联) |
| d3 | 113829 | 2026-10-21 | ISC | 否 | 可以, 但底层, 要自己写布局和交互 |
| 3d-force-graph | 6516 | 2026-09-29 | MIT | 否 | 可以 (有 UMD 构建), 3D 场景要自己搭 |
| sigma.js | 12210 | 2026-10-27 | MIT | 否 | 可以, 面向大图 |
| vis-network | 3635 | 2026-10-29 | Apache-2.0 | 否 | 可以 |
| tree-sitter (python 绑定) | 27341 | 2026-10-31 | MIT | 否 | 可以, 有预编译轮子 |
| tree-sitter-language-pack | 未核实 (未查 star) | PyPI 1.22.1 | MIT | 否 | 可以, 372 种语法一次装齐 |

判断口径: 本仓库产出以 markdown 和 python 为主, 所以 "能 pip 装, 无系统依赖, 无外部运行时" 是硬指标; 需要 Java/GPU/系统的库一律算高成本, 需要 Node 的算中等成本且要让 skill 明确降级路径.

## 5 若现成工具都不合适: 自建最小方案的代价

### 5.1 先分清三件事

1. 抽图 (谁依赖谁): 这是分析问题, 各语言各写一套 import 解析规则.
2. 分层 (谁在第几层, 有没有环, 有没有反着指): 这是图算法问题, 与语言无关.
3. 画图 (城市/道路/高度): 这是前端问题, 可以直接借现成的前端.

现成工具大多只解决第 1 和第 3, 第 2 只有 CodeCharta 的 dependencyparser 直接给了. 所以自建方案的重点是 "自己算第 2 步", 第 3 步能借就借.

### 5.2 路线 A (推荐): 纯 python 出 cc.json + 内置 CodeCharta 静态前端

结论: 成本最低, 观感最好, 已实测可行. 用现成的城市前端, 自己只写分析.

实测过程 (在本容器完成, 证据可复现):

1. 下载 `https://github.com/MaibornWolff/codecharta/releases/download/vis-2.9.1/web.zip` (3.5MB), 解压得 `dist/bundler/browser/` 46 个文件 6.2MB.
2. 用 40 行 python 手写一个 5 个文件 3 个目录的 `mine.cc.json` (节点 id 用 `md5(路径)[:16]`, 依赖边 6 条, 层号 0/1/2, 指标 rloc).
3. `python3 -m http.server` 起服务后打开 `index.html?file=mine.cc.json`, 3D 城市正常渲染, 每个目录一座 "街区", 每个文件一栋楼, 依赖边显示为连线.
4. 点 Dependencies 标签, 按层 0/1/2 堆叠的二维依赖图正常显示.
5. 再往 cc.json 的指标表里加一个自定义属性 `layer`, 界面里它出现在可选指标列表 (可作为面积/高度/颜色), 也就是说 "分层 = 建筑高度" 这个需求不需要改前端, 只需要我们把层号当指标写进去.

要写的东西:

| 部件 | 工作量 | 说明 |
| --- | --- | --- |
| 文件树扫描 | 小 | `pathlib` 递归, 按 .gitignore 排除; 生成 cc.json 的 `files` 树和稳定 id |
| 依赖抽取 (按语言) | 中, 每种语言一份 | 见 5.4 |
| 分层计算 | 小 | 在有向图上做最长路径 levelization, 用 Tarjan 找强连通分量标记环, 边反向且目标层不低就标 "向上依赖". 200 行以内 |
| 指标 | 小 | 代码行, 文件大小, 变更次数等, 想放就放 |
| cc.json 组装 | 小 | 是公开格式, 官网页有最小样例; 需遵守其 id/checksum 规则 |
| 起服务 | 小 | 本仓库 `general/present/scripts/web_server.py` 已经有起临时静态服务的实现, 可复用同一套做法 |
| 内置前端 | 一次性 | 3.5MB 资产入库, 与 `general/present/vendor/mermaid.min.js` (同样 3.5MB) 的先例一致; 升级时要重新下载替换 |

风险与代价:

- 前端是第三方二进制资产, 我们无法修改它的行为, 只能喂数据; 它的界面语言是英文.
- 版本升级要人工重新 vendored, 但 cc.json 格式 2.1 是稳定的交换格式, 升级风险可控.
- BSD-3 允许再分发, 需要保留版权与许可声明, 这一点要在 skill 里写明.
- 必须起一个本地 http 服务 (`file://` 不行, 实测), 这会给 skill 增加一条 "端口/清理" 的运行纪律; 好在 `present` skill 已经有同类处理.

### 5.3 路线 B (备用): 纯自建单页 HTML

结论: 零外部资产, `file://` 直接双击打开, 但只有二维关系图, 城市观感要自己造.

实测过程: 下载 `cytoscape.min.js` (435KB, UMD), 写一个 20 行的 HTML 内联脚本, 塞 6 个节点 5 条边, 用 `breadthfirst` (有向分层) 布局, 从 `file://` 打开截图正常, 控制台无报错.

- 优点: 单文件, 无服务, 无第三方资产升级问题, 2D 布局算法 (分层, 力导向, 环形) 都是库自带.
- 缺点: 要 "城市" 观感就得自己算每个模块的方块位置和大小 (树图/街区块布局), 再画道路; 3D 要自己搭 three.js 场景, 工作量从 "小" 变成 "中偏大".
- 我另外试了 `3d-force-graph` 的 UMD 包 (1.4MB): 从 `file://` 能加载并启动 (页面底部出现操作提示), 但我的 30 行试验里直接用了 `THREE` 全局变量来建方块, 那个 UMD 包不暴露 `THREE`, 所以画面是空的. 也就是说 "3D 单文件可行" 这个前提成立, 但 "几分钟拼出城市观感" 不成立, 要正式做需要按它的 API 文档写自定义几何体. 这一点是我的实测局限, 标为未完成验证.

### 5.4 各语言适配成本差异

| 目标语言 | 抽依赖的做法 | 成本 | 坑 |
| --- | --- | --- | --- |
| Python | 标准库 `ast` 遍历 `Import`/`ImportFrom`, 或用 `grimp` (BSD-2, 无运行时依赖) 直接拿图 | 低 | 要处理包根/相对导入/`sys.path`; pydeps 实测在本仓库目录 (名字带 `-`) 直接失败, 说明路径解析是真坑, 用 grimp 能省这块 |
| JavaScript / TypeScript | 自己写很难 (node_modules 解析, tsconfig 别名, 打包器别名, 动态 import); 走捷径: 调 dependency-cruiser 的 `--output-type json` 或 skott 的 json, 再喂给自己的渲染 | 高 (自写) / 中 (借工具) | 借工具就要 Node, 与本仓库栈冲突; 自写基本不划算 |
| Java / Kotlin / C# / Go / Rust / C / C++ | 用 tree-sitter 抽 import/include/use 语句, 按包路径或模块路径解析到文件 | 中 | 每种语言的解析规则各写一套; 不追类型解析, 只做文件级依赖就够用 |
| 任意语言统一 | `tree-sitter` (MIT) + `tree-sitter-language-pack` (MIT, 372 种语法, 有 abi3 预编译轮子) | 中 | 语法全, 但 "import 字符串到文件" 的解析仍然要按语言写规则; 好处是不需要目标库能编译 |
| 只想要函数级细节 | code2flow / pyan | 中 | 这两个要 graphviz; pyan 是 GPL-2.0, 传染性许可要避开 |

经验判断: 如果这个 skill 只需要 "看结构", 抽到文件或目录级依赖就够, 不要碰类型解析和动态派发; 那部分成本会翻好几倍, 收益对 "城市观感" 没有帮助.

## 6 明确推荐与不推荐

推荐:

1. **首选路线 A**: 自建 python 分析器 (抽图 + 算层 + 出 cc.json), 内置 CodeCharta 的 3.5MB 静态前端, 由 skill 起一个本地 http 服务把页面交给我. 理由: 城市观感和分层视图都是现成的 (实测), 我们要写的只有分析和组装; 许可 BSD-3 可再分发; 完全不碰 Java 和 Node.
2. **首选路线的降级**: 目标库过大或前端资产缺失时, 退到路线 B (cytoscape.js 单文件 2D 分层图), 一个 HTML 文件交付, 不依赖服务.
3. **目标库是 JS/TS 且允许 Node 时的加速**: 用 dependency-cruiser 的 `--output-type json` 拿准确的 import 图, 再交给 A 或 B 渲染. 这一条只作为可选加速, 不作为默认路径, 因为它给仓库引进 Node 工具链.
4. **只在需要静态插图时**才考虑 d2 或 mermaid (本仓库已有 mermaid vendor 先例), 它们适合放进 markdown 文档, 不适合当 "可以点着看" 的交互产物.

不推荐:

| 方案 | 理由 |
| --- | --- |
| CodeCharta ccsh 分析端 | 要 Node 22.19+ 与 Java 22+, 本仓库与容器都没有 Java; 而它的前端我们已经能单独用 |
| Gource | 要 OpenGL 硬件加速 (文档明写), 容器无 GPU; 且画的是 git 历史, 不表达模块依赖与分层 |
| mermaid-cli / 桌面端 Electron | 要 Chromium 或 126-400MB 的安装包, 只换来静态图 |
| graphviz 系 (madge 出图, pydeps 出图, code2flow) | 需要系统 `dot` 二进制, 本容器没有; 且输出是静态图, 没有探索交互 |
| pydeps 作为主力 | 只能 python, 只能静态图, 还要求目标是合法可导入的包 (实测本仓库这种带 `-` 的目录名直接报错) |
| Sourcetrail / DependaCharta / SoftVis3D / importlab | 已归档, 不再维护 |
| git-truck | 没有依赖关系, 只能看 git 活跃度 |

不可行 (已经验证过的不行):

1. CodeCharta 静态前端从 `file://` 直接打开: ES 模块分块被 CORS 拦, 白屏. 必须起 http 服务.
2. Gource 在没有 3D 加速的容器里跑: 文档要求硬件加速, 本容器无 GPU.
3. 用 ccsh 在本容器直接跑: 没有 Java 22, 装 JDK 是额外工具链, 超出 "纯 python + uv" 的范围.
4. 用 `pydeps` 对任意目录直接跑: 目录名/文件名必须是合法 python 标识符, 否则直接报错.

## 7 结论边界

已查证 (有官方文档或实测支撑):

- 各方案的许可, star 量级, 最后 push 时间, 是否归档 (GitHub/GitLab API, 2026-10-31).
- CodeCharta 的语言覆盖, 依赖 parser 的层号/环/向上依赖语义, ccsh 对 Node 22.19+ 与 Java 22+ 的要求, web.zip 的存在与体积 (官网文档 + release 资产列表).
- CodeCharta 静态前端离线可跑 (本地 http 服务), 接受自造 cc.json, 自定义 `layer` 指标可选为高度/面积 (本容器实测, 有截图).
- CodeCharta 前端 `file://` 打开失败的原因 (控制台 CORS 报错, 实测).
- cytoscape.js 435KB 单文件内联后 `file://` 可开并画分层图 (实测).
- pydeps 需要 graphviz, 且在本仓库目录直接报错 (文档 + 实测).
- Gource 需要 OpenGL 硬件加速 (README 原文).
- graphviz 主仓在 GitLab, 许可 EPL-2.0 (GitLab 仓库文件实测), GitHub 那个是归档壳.
- mermaid-cli 把 puppeteer 作为 peer 依赖 (npm 包元数据).
- dependency-cruiser 的 `engines.node` 与输出格式清单 (仓库 package.json 与 doc/cli.md).

推断 (有依据但没逐一实测, 用前要验):

- 用 cc.json 承载 "层号 = 建筑高度" 的整体观感是否好看. 我只验证了属性可选, 没验证大面积真实代码库 (几千文件) 下的可读性与帧率. 大库性能需要实测.
- 3D 单文件 (3d-force-graph) 做出街区观感的实际工作量. 我的试验没跑通渲染, 只确认库能从 `file://` 加载.
- tree-sitter 抽各语言 import 的准确率. tree-sitter 本身成熟, 但 "import 字符串到文件路径" 的解析规则要按语言写, 准确率取决于规则质量, 没有实测.
- "dependency-cruiser 的 json 可以作为通用中间格式" 这一点没实测, 只是从它输出 json 这个事实推断可行.

未核实 (不要当结论用):

- `.vue` / `.svelte` 在 dependency-cruiser 和 madge 里的支持程度.
- grimp 与 tree-sitter-language-pack 的 star 数与最后提交时间 (只查了 PyPI 元数据: 3.18 / 1.22.1, 许可 BSD-2 / MIT).
- 商业工具 (Understand, Structure101, Lattix) 的能力与价格, 本次完全没有访问.
- CodeCharta 在 windows/macos 之外的可移植性细节, 以及 cc.json 的 checksum 具体算法 (文档只说要遵守规范, 我手写时随便填了一个 checksum, 前端没有拒绝, 但正式产出应该按规范算).
- CodeCharta 前端资产是否允许以 `web.zip` 内文件的形式再分发到第三方仓库 (BSD-3 通常允许, 但要保留声明; 具体仓库里是否有单独的资产许可, 未逐文件核对).
