# milestone-21 实施与验证报告: 代码库结构可视化汉化构建与交付

- 任务: 按 m13 DECISIONS D013-D016/D021/D023/D024/D027/D030 与 m24 U002/U003 落地汉化构建链, 是 v1 之后的技术切第二片, 不改 v1 外部行为.
- 执行环境: sandbox 容器 (bolo), Node v24.21.0 / npm 11.19.0, playwright chromium-1234 二进制; 缓存与 serve-root 落 `~/.agents/codebase-map/` (容器 home 与宿主同路径).
- 标注规则: [实测] = 本会话真实执行有日志有哈希; [未验证] = 没做或做不成, 如实列出.
- 依据材料: m13 DECISIONS.md (D013-D016, D021, D023, D024, D027, D030), m24 DECISIONS.md (U001-U003, F001-F006), m23 PROBE.md; 不再引用 PLAN.md 第 3 节 (nginx/try_files 配方已按 F011/D021 作废).

## 1. 交付清单

`workflow/codebase-map/` (D016: 只放代码/词表/手册, 不入上游源码与产物):

| 文件 | 说明 |
| --- | --- |
| `SKILL.md` | 手动调用入口, frontmatter `disable-model-invocation: true` (D001) |
| `agents/openai.yaml` | codex 元数据 `policy.allow_implicit_invocation: false` (D001/守卫测试要求) |
| `README.md` | 操作手册: 构建/铺设/分析端/升级/已知坑, 逐节挂决策编号 |
| `tools/build-zh.sh` | 构建流水线: 克隆钉死 tag -> npm ci -> 还原 -> 三通道替换 -> build -> 渲染冒烟 |
| `tools/localize.py` | 通道 A: 模板静态文案 (m13 原型原样收编) |
| `tools/localize_ts.py` | 通道 B/C: 整条字面量白名单 (m13 原型 + 受控扩展, 见 4.3) |
| `tools/ts_strings.py` | .ts 文案统计 (m13 原型原样收编) |
| `tools/scan-candidates.py` | 升级时重新发现 B/C 通道候选 (含噪音过滤) |
| `tools/smoke.py` | 渲染冒烟: 临时静态服务 + 无头浏览器 + D014 关键元素断言, 内置合成 cc.json 样例 |
| `tools/stage.py` | serve-root 铺设: 前端产物 + 数据副本键名 `<库名>-<8位路径哈希>.cc.json` (D023) |
| `i18n/zh.txt` | 通道 A 词表 355 条 |
| `i18n/zh-ts.txt` | 通道 B 词表 346 条 |
| `i18n/zh-lit.txt` | 通道 C 词表 44 条 |

`docs/changes/workflow-stack-review/milestone-21/`: 本报告 + `shots/` (3 张冒烟截图) + `reports/` (运行报告 JSON 与界面全文转储).

## 2. 词表规模与渠道漏斗 [实测]

目标原估约 900-1000 条; 实际按"人工过滤后的真实界面文案"落定 745 条 / 837 处替换:

| 通道 | 词表条数 | 替换处数 | 未命中 | 未使用 | 未翻词条 |
| --- | --- | --- | --- | --- | --- |
| A 模板静态文案 | 355 | 430 | 4 种/7 次 (见 4.1) | 0 | 4 |
| B .ts 整条字面量 | 346 | 359 | 0 | 0 | 见 4.2 |
| C 绑定/插值内字面量 | 44 | 48 | 0 | 0 | 见 4.2 |
| 合计 | 745 | 837 | - | - | - |

通道 B 的"约 500"原估与实际的差: 启发式原始候选 1172 处/584 种 [实测, m13 同口径], 过滤 CSS/路径/XML/图标/枚举值/mocks 后 380 条, 人工逐条判定后可译的界面文案 346 条; 其余为非文案 (清单见 4.2). 漏斗工具 `tools/scan-candidates.py` 随 skill 交付, 升级时同法复算.

术语单一译法 (D015): 术语表 14 词统一 (面积/高度/颜色/边/标签/场景/文件夹/压平/指标/依赖/检查器/徽标/节点/建筑), 抽查模板与 .ts 无同词异译; 复合词均由单一译法组词 (反转面积/高度指标等) [实测: 对 built 树 grep, 模板中独立术语英文残留为 0].

## 3. 端到端构建 [实测]

- 命令: `CC_SMOKE_PYTHON="uv run --with websockets python" bash workflow/codebase-map/tools/build-zh.sh`
- 流程全程无人工干预跑通: 克隆 vis-2.9.1 (缓存命中时跳过) -> npm ci (node_modules 在即跳过) -> 还原 -> 三通道替换 -> `npm run build` (9.7s, `echarts-wordcloud@2.1.0 ✔` patch 应用正常) -> 冒烟 PASS.
- 产物: `dist/bundler/browser` 6.2M, 初始包 3.43MB (估算传输 806kB), 懒加载 chunk 2 个 (dependencyView/domainView).
- 耗时: 暖缓存端到端 23s (两次), 其中构建 10s, 冒烟约 12s; 冷 npm ci 未单独计时, 参考值 m13 实测 22-24s.
- 幂等: 连跑两次, 产物全树 sha256 逐字节一致 (`b4297fae84e5f42d...`, 对 12 个产物文件聚合哈希); 源码树 diff 恒为汉化补丁 208 文件 778+/784-.
- 上游既有告警 (与汉化无关): initial bundle 超预算 1MB->3.43MB, daisyUI 选择器告警 56 条.

## 4. 界面残留英文清单 (逐条给原因)

冒烟样例加载后, 指标视图/依赖视图/设置对话框的界面全文转储在 `reports/ui-text-*.txt` [实测]. 英文残留全部属以下几类:

1. **数据与标识符, 不属界面文案**: 指标名 `rloc`/`complexity`/`dependencies`, 扩展名 `java`, 文件名/项目名 (来自 cc.json 数据本身).
2. **状态字段驱动的标题**: 检查器"指标映射"的行头 `AREA`/`HEIGHT`/`COLOR` 来自组件状态 `block().kind` 的值, 模板里是 `{{ block().kind }}` 插值, 译它必须改表达式, 违反"只改字面量"纪律 (D013), 保留.
3. **品牌与版本**: CodeCharta (3 处), MaibornWolff, Github, `v2.9.1`.
4. **术语与排版占位**: `TF-IDF` (通用术语), `&nbsp;` (纯空白文本节点).
5. **与枚举值同字面量的标签**: 比较符 `between` (`{ value: "between", label: "between" }`), 替换会破坏操作符逻辑, 保留; 同文件其余比较符 (大于/至少/小于/至多/等于) 已译.
6. **3D 打印物理模型刻字与设备名**: `backBelowLogoTextMesh` 的厂商文案, 打印机型号 (Prusa MK3S 等) — 属模型内容/商品名, 非界面.
7. **throw/console 消息** (D013 C 类纪律): jsonBytes JSON 解析错 (4 条), urlExtractor 深链加载失败 (2 条), scenarios IndexedDB 失败 (3 条) 等 — 面向开发者的异常路径, 不进词表.
8. **词表明确不翻的其余跳过物**: CSS 类/Tailwind/图标类/路径/常量名/mock 数据.

## 5. 渲染冒烟 [实测, D014]

- 断言与结果 (driver cdp-websockets, chrome headless + swiftshader, 1400x900):
  - PASS 3D 画布挂载 (canvas x2), PASS 页签 指标/依赖, PASS 底栏 面积/高度/颜色;
  - PASS 3D canvas 渲染出建筑 (webgl readPixels 非主导色不透明像素 234,926 >= 800);
  - PASS 点击页签[依赖] -> URL 进入 hash 路由 `#/dependencies` (F011 佐证: 无深链回退需求);
  - PASS 依赖视图文本含 依赖/边, 2D 画布渲染出方块 (非主导色像素 120,724 >= 500);
  - PASS pageerror 0, console error 0.
  - 预期行为 note x2: 领域页签与依赖视图"层级"段分别依赖 domain lens / packages 数据, 合成样例没有, 冒烟按条件断言.
- 截图: `shots/shot-01-map.png` (指标视图, 中文底栏+3D), `shots/shot-02-dependencies.png` (依赖视图), `shots/shot-03-settings.png` (全局配置对话框全中文).
- 冒烟样例为脚本内置合成 cc.json 2.x (metrics rloc/complexity + dependency lens level/环/向上依赖, 确定性字节), 开发中曾靠它抓出两个真实 schema 错 (边端点字段 fromId/toId; files 树节点不允许 attributes 字段) — 校验错误信息本身以中文显示 ("加载的文件有问题/...must NOT have additional properties"), 词表生效的旁证.

## 6. serve-root 铺设 [实测, D023/D024]

- `stage.py frontend`: 前端产物铺到 `~/.agents/codebase-map/serve-root/` (index.html 顶层), 6.2M.
- `stage.py data`: 样例副本键名 `smoke-sample-d36f864c.cc.json` (sha256(realpath) 前 8 位), 与产物同目录.
- 端到端验证: 对 serve-root 起临时静态服务, 加载 `/?file=smoke-sample-d36f864c.cc.json` HTTP 200, 页面正常渲染中文界面 [实测].
- state.json/logs 未创建 (v1 服务归属, milestone-26); 本片铺设的目录即 D023 定义的服务根形状, v1 直接托管.

## 7. localize_ts.py 受控扩展 (相对 m13 原型)

按 m13 "占位符顺序要人定"的纪律落地为机制, 其余纪律不变 (只改整条字面量, 拒绝子串/正则, 拒改 spec/mocks, 幂等先还原):
1. 模板字面量 (反引号串): 键里 `${...}` 写成 `⟦n⟧`, 译文必须恰好各含一次可重排, 表达式本体原样保留; 换行以 `\n` 转义对齐; 含 `` \` `` 转义的跳过并报 SKIP. 覆盖了 m13 只能跳过的几十条界面文案 (如 `Level ${n}`, `7 scenarios available` 拼句).
2. 译文 `(空)` 标记: 仅用于拼接句尾段 (`'Show ' + word + ' again'` -> `再次显示 ` + word).
3. 两轮替换: 先普通字面量 (含模板内层), 后模板外层 (从当前文本提取表达式重建), 外层保留内层译文; 同轮嵌套命中外层优先, 内层放弃并告警.
4. `.html` 绑定内混合表达式的内层字面量扫描 (通道 C 依赖此能力).

## 8. 多命中复核记录 (词表纪律要求人看的 8+4 条)

全部为同义多现场, 逐条核过源码, 批准统一译法: `Cyclomatic Complexity`x2 (metricTitles: complexity 与 sonar_complexity 同标题), `⟦0⟧ to ⟦1⟧`x5 (mapColorLabel 全部是区间格式), `⟦0⟧ Found: ⟦1⟧`x4 与 `⟦0⟧ and ⟦1⟧`x2 (fixedFolderValidator 校验详情), `⟦0⟧ Found duplicate of...`x2 (fileValidator 两处查重), `package ⟦0⟧`x2 (inspectorBadges 包徽标两处), `Change/Switch and continue`x2 (按钮+对话框消息引用), 通道 C `Copied!`/`Copy path`x2 (同按钮 title+aria-label), `Show `/` again`x2 (两处拼接按钮), `Remove folder color`x2 (静态 title 通道 A + 绑定通道 C 各一处).

## 9. 未验证 / 缺口

1. [未验证] 宿主上的实跑: 本片全部在容器实测; 宿主 Node v24.19.0 与 playwright chromium 已由 m23 证实可用, 但 `python3 + playwright` 路径的 smoke.py 在宿主未跑过; `uv run --with websockets` 回退路径在容器实测, 宿主是否装 uv 未核实. v1 实施时首跑即验证点.
2. [未验证] 冷缓存端到端耗时未单独计时 (npm 缓存暖), 参考值引自 m13 BUILD-PROBE.
3. [未验证] 真实大库观感: 冒烟用 7 文件合成样例; 真实 Java 库 (cz_sdk, 3312 文件) 的渲染帧率与可读性未测 (F010 仍开放, D025 的过滤手段未在真库上演练).
4. [未验证] 深路径界面: 3D 打印导出, 场景保存/应用, 规则编辑器, 词云视图只做了代码级替换, 未逐屏截图; 右键菜单/弹层的中文未入冒烟断言.
5. [未验证] 超长译文的排版溢出未压测 (m13 遗留项).
6. [未验证] Electron 打包路径未触碰 (不在交付范围).
7. 依赖文档 [文档]: 分析端命令与 level/环语义引自 m23 PROBE 的镜像内实测与官方文档, 本会话未起分析端 (边界: 不碰分析端).
