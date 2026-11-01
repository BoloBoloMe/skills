# 代码库结构可视化: 已定方案 (milestone-13 决策输入)

- 性质: 已与用户逐条敲定的方案记录, 供后续实施里程碑直接使用
- 依据: milestone-12 侦查 (FINDINGS.md), 传统设计期可视化侦查 (RESEARCH-design-visualization.md), 构建期汉化实测 (milestone-13/BUILD-PROBE.md)
- **本轮定稿见同目录 `DECISIONS.md` (D001-D020), 与本文件冲突时以账本为准.** 账本相对本文件改写的地方: 分析端跑在宿主的 podman 上 (非 docker); 交付不用 nginx, 改自建 python 常驻服务 (D006); 不被任何 skill 调用, to-spec 入口整项作废 (D001); cc.json 落被分析库的 `.codebase-map/` (D010); 运行状态与构建缓存放宿主 `~/.agents/codebase-map/` (D012).
- 尚未定的部分单列在最后一节, 不影响实施主体

## 1 路线

用 CodeCharta. 分析端与前端都跑在宿主的 podman 里, 上游源码不入本仓库.

- 分析端: 官方镜像 `codecharta/codecharta-analysis`, 挂载目标仓库与输出目录, 产出 `.cc.json`.
- 前端: 上游 Angular 前端 `MaibornWolff/codecharta`, 构建时汉化, 产物由官方 `nginx:alpine` 镜像挂载提供页面.
- 本仓库里只放: 构建脚本, 三本词表, nginx 配置, 操作手册. 不含上游源码, 不含 6.2MB 产物, 不含第三方二进制.

## 2 汉化方式 (已实测)

构建期替换, 零 fork 维护:

1. `git clone --depth 1 --branch <vis tag> https://github.com/MaibornWolff/codecharta`.
2. `npm ci` (Node `^22.22.3 || ^24.15.0 || >=26`) 加 `npm run build` (含 `patch-package`, Angular 22 + esbuild).
3. 构建前用三通道词表替换文案:

| 通道 | 脚本 | 对象 | 已测结果 |
| --- | --- | --- | --- |
| A 模板静态文案 | `tools/localize.py` | `.html` 文本节点 + 8 类用户可见属性 | 123/184 个模板有字面文案, 437 处 / 359 条去重 |
| B `.ts` 整条字面量 | `tools/localize_ts.py` | 按 (文件, 整条字面量) 白名单 | 584 种候选, 人工过滤后约 500 条 |
| C 绑定内字面量 | `tools/localize_ts.py --allow-any` | `[label]="'...'"` 与 `{{ a ? 'x' : 'y' }}` | 30 处绑定 + 23 处插值 |

实测耗时: clone 4.4s, `npm ci` 24s, build 10s, 端到端 22s (暖缓存) / 约 37s (冷缓存). 连跑三次 diff 逐字节一致.

## 3 交付方式 (由 DECISIONS.md D006/D007/D008/D009 定稿, 本节的 nginx 配方不再采用)

1. 构建产物落在宿主 `~/.agents/codebase-map/cache/` 下.
2. 页面由自建 python 常驻服务提供, 单例一个端口, 交付局域网 IP 拼成的 URL, 多库靠 `?file=`.
3. 数据: `build` 在 `~/.agents/codebase-map/data/` 建软链指向目标库里的 `.codebase-map/cc.json`.
4. 命令三段: `build` / `serve` / `stop`.
5. 原 nginx 方案与 `try_files` 需求作废: 上游是 hash 路由 (F011), 服务端只会看到 `/`, 不存在路径深链 404; 保留自建服务的理由是常驻单例与状态记录.

## 4 测试策略 (用户选定)

不跑上游单测. 上游 629 个测试文件里有 62 个用可见文本断言 (getByText 224 次), 汉化后约 254 处会失败, 同步改测试成本高且与上游更新冲突.

改为自建渲染冒烟: 对构建产物起临时静态服务, 无头 Chromium 截图并断言关键元素 (页签, 底栏指标条, canvas 里出现建筑, 依赖视图有方块). 冒烟脚本已有原型 `tools/shot_click.py`.

## 5 术语表 (用户已认可)

Area=面积, Height=高度, Color=颜色, Edges=边, Labels=标签, Scenario=场景, Folder=文件夹, Flatten=压平, Metric=指标, Dependencies=依赖.

扩展规则: 高频单词型文案 (70 条) 必须先统一定义, 再开始批量翻译; 同一英文默认只有一个译法, 语境确实不同才按文件覆盖.

## 6 汉化纪律 (每条都有实测依据)

1. 只改字面量, 不改表达式; Angular 控制流块头 (`@if` / `@for (...; track ...)` / `@else` / `@empty` / `@let`) 原样保留.
2. `{{ }}` 整段变占位符, 校验数量一致并允许重排 (中文语序).
3. 译文必须含中文; 不许裸 `<` `>` `&`; 属性值包裹引号内不许出现同种引号.
4. 词表键从统计报告原样拷贝 (`&amp;`, `&#8217;`), 手打会永不命中.
5. `.ts` 白名单只做整条完全相等替换, 拒绝子串/正则; 同一字面量在同文件多次出现时报错要人看.
6. 跳过 `*.spec.ts` / `*.e2e.ts` / `*.po.ts` / `mocks/`; 跳过 `throw` / `console.*` / URL / CSS 类名.
7. 单复数在模板表达式里, 中文合并量词 (例: `5 个文件`).
8. 幂等: 每次构建先还原再 apply; 脚本二次运行不得有副作用.
9. 每次构建后跑冒烟截图, 有英文残留或排版溢出就补.

## 7 升级上游的成本

改 tag 变量重跑构建, 看两处输出: `--check` 报的"未使用词条" (上游改了或删了那句), 以及统计报告里的"未命中"数量 (还没翻的). 风险点是 `patch-package` 的 `echarts-wordcloud` 补丁可能冲突, 会在 build 第一步失败.

## 8 已定 (原"仍未定", 现由 DECISIONS.md 定稿)

1. skill 名字与放置位置: `workflow/codebase-map/` (D001).
2. 调用方式: 只手动调用, 无 skill 调用它, 无 to-spec 入口 (D001, F007).
3. 产物落盘: 目标库 `.codebase-map/cc.json` (D010); 运行状态与缓存 `~/.agents/codebase-map/` (D012).
4. 第一版语言范围: Java (D004); 未解析语言显式标注, 不静默画空图.
5. 其余口径 (单例/端口/命令/指标/排除/聚合): D007, D009, D017, D018, D019.

## 9 现成资产

- `docs/changes/workflow-stack-review/milestone-13/tools/`: `build-zh.sh`, `localize.py`, `localize_ts.py`, `ts_strings.py`, `shot_click.py`.
- `docs/changes/workflow-stack-review/milestone-13/i18n/`: `zh.txt` (模板 16 条样本), `zh-ts.txt` (8 条), `zh-lit.txt` (12 条).
- `docs/changes/workflow-stack-review/milestone-13/BUILD-PROBE.md`: 构建期汉化实测报告 (含耗时表, 坑, 统计方法, 未验证项).
- 实测现场已不在 `/tmp/cc-build/` (临时目录会随容器/宿主清理丢失): 长期保留部分移到宿主 `~/.agents/codebase-map/` (D012), 需要复现时按 `tools/build-zh.sh` 重跑.
