# CodeCharta 前端构建期汉化: 可行性验证报告

任务标识: ccbuild-probe
工作根: /tmp/cc-build (全部产物与脚本都在这里, 未碰 ~/Workspace, 未对上游仓库 commit/push)
上游: MaibornWolff/codecharta, tag `vis-2.9.1`, commit `bd1fe9b40f987cfdc34cf169b7fb220e5ea69466` (提交时间 2026-10-23 09:48:44 +0200)
结论先说: **可行**. 构建期"词表 + 替换"能在 10 秒级构建里落地, 脚本可重放, 3D/依赖视图/对话框都正常; 真正的成本在词表本身 (约 900-1000 条) 和"绑定表达式 + .ts 里的文案"这三类漏网, 以及汉化会打掉 62 个测试文件里的文本断言.

---

## 1. 环境与耗时 (全部实测)

| 项 | 命令/位置 | 结果 | 耗时 |
| --- | --- | --- | --- |
| Node / npm | `node -v` / `npm -v` | v24.21.0 / 11.19.0 (满足 engines `^22.22.3 \|\| ^24.15.0 \|\| >=26`) | - |
| Angular / TypeScript | visualization/package.json | ^22.1.7 / 6.0.3 | - |
| 克隆 | `git clone --depth 1 --branch vis-2.9.1 ...` | 工作树 220M (含 .git 28M) | 4.4s |
| 安装依赖 (暖 npm 缓存) | `npm ci` | 1162 包, node_modules 732M, 53 个漏洞告警 (1 low/40 moderate/9 high/3 critical) | 24.0s |
| 安装依赖 (清空缓存, 真实下载) | `npm ci --cache /tmp/cc-build/npmcache` | 下载入缓存 252M | 22.4s |
| 构建 (冷, 删掉 .angular 与 dist) | `npm run build` | 成功, bundle 生成 9.8s | 10.5s |
| 构建 (增量/暖) | `npm run build` | 成功 | 10.1s |
| 构建 (汉化后) | `npm run build` | 成功, 产物大小与体积不变 | 10.0s / 10.7s / 9.99s (三次) |
| 汉化脚本 (184 模板 + 1093 个 .ts, 三本词表) | `localize.py` + `localize_ts.py` x2 | 替换 29 + 9 + 13 处 | 0.09s |
| 端到端 (clone + npm ci + 汉化 + build, 暖缓存) | `tools/build-zh.sh /tmp/cc-build/e2e` | 成功 | 22.1s |
| 端到端 (冷 npm 缓存) | 分项相加 (1+2+3+4) | 约 37.4s (未单次整段实测) | ~37s |
| 产物 | `dist/bundler/browser` | 6.2M, 初始包 3.42MB (估算传输 804kB), 2 个懒加载 chunk | - |
| 运行镜像 | `visualization/Dockerfile`: `FROM nginx:1.29.5-alpine` + `COPY dist` | 单阶段, 运行镜像体积本项**未实测** (容器内无 docker) | - |

## 2. 构建步骤与失败点

实际命令序列 (全部成功, 无一处需要修):

```bash
git clone --depth 1 --branch vis-2.9.1 https://github.com/MaibornWolff/codecharta /tmp/cc-build/src
cd /tmp/cc-build/src/visualization && npm ci && npm run build
```

`npm run build` 的真实内容是三段: `npm run patch && ng build && cp electron/* package.json dist/bundler/browser`.
其中 `patch-package` 会先应用 `patches/echarts-wordcloud+2.1.0.patch`. 这是升级上游时第一个会见红的地方: 依赖版本变动导致 patch 冲突, 构建在第一步就失败 (本次 2.9.1 上应用正常, 输出 `echarts-wordcloud@2.1.0 ✔`).

本次唯一的构建告警 (都是上游既有的, 与汉化无关, 原文关键行):

```
Application bundle generation complete. [9.777 seconds]
WARNING: bundle initial exceeded maximum budget. Budget 1.00 MB was not met by 2.42 MB with a total of 3.42 MB.
WARNING: 56 rules skipped due to selector errors:   (daisyUI 的 & 嵌套选择器)
```

部署侧实测发现的一个真问题: 产物用 `python3 -m http.server` 只能从 `/` 进入, 直接访问 `/dependency` `/metrics` 返回 **404** (`curl` 实测), 因为这是 HTML5 history 路由, 需要 nginx `try_files $uri /index.html`. 上游 Dockerfile 用的是 nginx 默认配置, 也就是说这个坑上游自己也在, 部署时要么加 rewrite, 要么只从根路径进. 另外 `index.html` 里没有 hash 路由, 页签切换会改路径, 刷新就 404.

## 3. 汉化机制与验证

### 3.1 三个替换通道 (脚本都在 /tmp/cc-build/tools/)

| 通道 | 脚本 | 处理对象 | 本轮替换 |
| --- | --- | --- | --- |
| A 模板静态文案 | `localize.py` | .html 的文本节点 + 8 类用户可见属性 (title/label/aria-label/ariaLabel/tooltip/placeholder/alt/aria-description) | 29 处 / 14 文件 |
| B .ts 整条字面量 | `localize_ts.py` | 按 (文件, 整条字面量) 白名单精确替换 | 9 处 / 3 文件 |
| C 模板绑定内字面量 | `localize_ts.py --allow-any` | `[label]="'...'"` 与 `{{ a ? 'x' : 'y' }}` 里的整条字面量 | 13 处 / 6 文件 |

`localize.py` 的关键规则 (都实现了, 也都是踩过的坑):

- Angular 17+ 控制流块头 `@if (...) {` `@for (...; track ...) {` `@else` `@empty` `@let` 当语法原样保留, 只翻其中的文案; 用括号深度扫描, 不用正则 (正则会在 `@for (x of y; track z)` 上断在 `;`).
- `{{ }}` 整段变成不可变占位符 `{{0}} {{1}}`, 译文可重排位置. 例: `Folders with up to {{0}} files are drawn as a treemap.` -> `最多 {{0}} 个文件的文件夹会按矩形树图绘制.`
- 4 条硬校验: 译文必须含中文; 占位符必须一个不多一个不少; 译文不许有裸 `<` `>` `&` (要写 `&amp;`); 属性值包裹引号里不许出现同种引号. 命中就报错且不改文件.
- 幂等: 再次运行时源文已变中文, 匹配不到就跳过 (实测连跑三次 diff 一致).

### 3.2 可重放性

"restore -> apply 三通道" 连续跑三次, 产出的 `git diff` 逐字节相同:
`sha256 = bfce3aa6404452089f8ae4f50c4f9604d6ba6355ece75fefbea3c002ad9c660e`, 22 文件 47 行 (patch 存于 `/tmp/cc-build/localization.patch`).

### 3.3 截图证据

| 截图 | 场景 | 观察结果 |
| --- | --- | --- |
| `/tmp/cc-build/shot-01-baseline.png` | 未汉化, 指标视图 | 英文原样, 3D 城市渲染正常 (数据 mine2.cc.json) |
| `/tmp/cc-build/shot-08-metrics-final.png` | 汉化后, 指标视图 | 底部条 `布局`/`面积`/`颜色`, 右上 `设置` 变中文; 3D 城市, 侧栏, 图例, 右下 "7 scenarios available" 全部正常, 无排版错位 |
| `/tmp/cc-build/shot-03-layout-popover.png` | 点底部"布局" | 弹层标题 `地图布局` 中文; 弹层内部的选项名与描述仍是英文 (`Squarified TreeMap` 等来自 .ts) |
| `/tmp/cc-build/shot-04-settings.png` / `shot-07-settings-zh.png` | 点右上"设置" | 对话框标题 `全局配置` 与 4 个开关标签 (隐藏被压平的建筑 等) 变中文; 按钮 `Reset global settings` 等仍是英文 (来自 .ts 与绑定字面量, 未在本轮词表内) |
| `/tmp/cc-build/shot-05-deps.png` / `shot-06-deps-zh.png` | 依赖视图 | 依赖图盒子渲染正常; 底部 EDGE STYLE 由 `Combined / By count` 变 `合并 / 按数量` (来自 .ts, 证明通道 B 生效) |

### 3.4 机制层面的坑 (本轮实测踩到或量到)

1. `.ts` 就是文案大户: 顶部页签 `Metric`/`Dependencies`, 布局选项名与描述, 设置项 label 的字符串源, 指标显示名, 全在 .ts. 光翻 .html 只能翻一半界面.
2. **文案藏在绑定表达式里**: 30 处 `[title]/[label]/[aria-label]` 绑定内含字符串字面量, 23 处 `{{ }}` 内有字面量. 静态文本扫描全漏, 必须走通道 C. 例: `{{ count.all === 1 ? 'file' : 'files' }}` (单复数写在插值里), `'Show ' + word + ' again'` (拼接).
3. 同一句英文出现在多个文件: 词表键 `Settings` 命中 14 个模板. 好处是省翻译, 坏处是同词不同语境 (Settings 也可能是别的意思) 只能靠"按文件覆盖"来纠正 (通道 B/C 天然带文件维度).

## 4. 模板文案统计 (方法 + 数字)

统计方法: 用同一套扫描器 (与替换脚本共用代码) 跑全部 184 个 .html; 文本节点先剥掉 Angular 控制流块头, 再要求"含 2 个以上字母的英文单词"且不是纯符号/纯数字/纯插值; 属性则按 8 类白名单取字面量值. 报告 JSON: `/tmp/cc-build/stat-report-pristine.json`.

| 指标 | 数字 |
| --- | --- |
| 模板总数 | 184 |
| 含用户可见字面文案的模板 | **123** (67%), 另 61 个只有结构化标签/纯插值 |
| 文案位点合计 | **437** 处 (其中 231 文本节点 / 206 属性值 / 23 处含 `{{ }}` 插值) |
| 属性分布 | title 65, aria-label 44, label 43, ariaLabel 28, tooltip 14, placeholder 11, alt 1 |
| 去重后英文串 | **359** 条 (437 处里 78 处是重复出现, 高频: close 10, Height 6, Close 5, Color 5, Global Configuration 4, Cancel 4, Show 4) |
| 长度分布 | 单词/短语 (无空格, <=12 字符) **70** 条, 超过 60 字符的长句 **20** 条, 含 HTML 实体 3 条 (`Flatten &amp; decolor`, `These folders&#8217; floors...`) |
| 单文件密度 | 中位数 3 处; 最密 `labelSettingsPanel` 23, `edgeSettingsPopover` 14, `metricRuleEditor`/`saveScenarioDialog`/`edgeTypesSegment` 各 11 |
| 扫描够不到的 | `{{ }}` 内字面量 **23** 处; 可见属性绑定内字面量 **30** 处 |

`.ts` 侧统计 (方法: 去注释后取全部字符串字面量, 黑名单过掉路径/CSS 类/图标/单位/URL/camelCase 标识符, 要求像句子; 排除 629 个 spec/e2e/po/mocks):

| 指标 | 数字 |
| --- | --- |
| .ts 总数 / 视为生产代码被扫 | 1728 / **1093** |
| 疑似用户文案 | **1172 处 / 584 种** |
| 其中落在已知文案属性 (title/label/message/description/hint/placeholder/...) 下 | 108 种 (可信度最高) |
| throw / console 里 (开发向, 一般不翻) | 26 处 |
| 分布热点 | `metricTitles.ts` 20, `scenarioSettings.registry.ts` 32, `scenarios.service.ts` 21, `fileValidationMessages.ts` 17, `edgeStyleChoices.ts` 14, `radialFolderValues.ts` 15 |

翻译预算: 模板 359 条 + .ts 侧人工过滤后约 500-600 条 = **约 900-1000 条**. 术语表必须先定 (70 条单词里大量是复用词: Area/Height/Color/Edges/Labels/Scenario/Folder/Flatten 等).

## 5. .ts 文案怎么安全处理

结论: **能用同一个"字面量白名单"机制处理, 但绝不能做正则或子串替换**. 本轮已验证的实现 (`tools/localize_ts.py`) 的纪律:

1. 键是 (文件相对路径, 英文整条字面量) 二元组, 必须**整条完全相等**才替换; 不做前缀/子串/正则.
2. 每条替换打印 `file:line` 与前后值, 人工可逐条复核.
3. 同一字面量在一个文件里出现多次 -> 报 ERROR 要求人看 (实测 `Cyclomatic Complexity` 出现 2 次就报了).
4. 拒绝改 `*.spec.ts` / `*.e2e.ts` / `*.po.ts` / `mocks/`, 防止把测试夹具当界面文案.
5. 含 `${}` 的模板字面量一律跳过并单独列出 (占位符顺序要人定).
6. 未命中的词条也报出来, 这就是"上游改文案"的探针.

分层建议:

- A 类直接进词表: 枚举显示名 (`SquarifiedTreeMap = "Squarified TreeMap"`), choices 的 `label`/`hint` (`edgeStyleChoices.ts`), `ERROR_MESSAGES`, `metricTitles`, `scenarioSettings.registry` 的字段标题.
- B 类必须人工重写而不是对翻: 拼接字符串 `'Show ' + word + ' again'` -> 中文语序要变, 只能改成参数化写法或接受 `再次显示 ...`; `{{ count.all === 1 ? 'file' : 'files' }}` 这类单复数在中文里合并成 `个文件` (本轮已实测有效, 界面读作 `5 个文件`).
- C 类不进词表: `throw new Error(...)`, `console.*`, URL, CSS 类名, 图标类名, 属性路径.
- 顺序: 先做 A 类 (量大收益高), 再做通道 C (30 处绑定), 最后处理 B 类的拼接/单复数.

## 6. 可行性与纪律清单

可行性: **成立**. 收益是零 fork 维护, 升级只改一个 tag 变量; 成本是词表维护 + 每次升级跑一次 `--check` 看哪条词失效.

必需的纪律 (每条都有对应的实测依据):

1. 只改字面量, 不改表达式: 文本节点/白名单属性/整条字面量三种入口, 其余一律不碰.
2. Angular 控制流块头必须原样保留 (含 `@for (...; track ...)` 里的分号).
3. `{{ }}` 当占位符 `{{n}}`, 校验数量与唯一性, 允许重排 (中文语序).
4. 双引号转义: 属性值用双引号包裹时, 译文里不许出现双引号, 需要时写 `&quot;` 或改单引号包裹; 脚本会报错拦下.
5. HTML 实体: 词表键必须从报告里原样拷贝 (`&amp;`, `&#8217;`), 手打英文会把键打错导致永不命中; 译文里禁止裸 `&` `<` `>`.
6. 空白与换行: 键统一做空白折叠 (多行段落会被压成一行), 替换时保留原节点首尾空白; 实测无跨行拆句的模板 (0 处含换行).
7. 单复数: 上游没用 Angular i18n/plural, 单复数写在模板表达式或 .ts 里, 中文统一成一个量词, 需要按句人工处理.
8. 术语表先行: 70 条单词型文案必须先统一 (Area=面积, Height=高度, Color=颜色, Edges=边, Labels=标签...), 否则同一概念在不同文件翻法不一.
9. 幂等 + 可重放: 每次构建先 `git checkout` 还原, 再 apply; 脚本二次运行必须无副作用 (已实测).
10. 只翻文案, 顺便别碰 `data-testid`/`id`/class/`[attr.*]` 绑定键名 (脚本已跳过).
11. 每次构建后跑一遍冒烟: 起静态服务 + 无头 Chromium 截图看 3D 与依赖视图 (本轮脚本 `tools/shot_click.py` 可直接复用).
12. 部署侧要补 history fallback (nginx `try_files`), 否则刷新/深链 404.

升级上游的代价 (实测路径): 改 `CC_TAG`, 重跑 `tools/build-zh.sh` (~37s 冷缓存 / ~22s 暖缓存), 看两处输出:

- `--check` 的"未使用词条" = 上游删了或改了这句, 需要人工处理 (本轮用真实改动模拟验证过: 把 `title="Change the map layout"` 改成 `Change map layout`, 立刻报 `未使用词条 1 条 - Change the map layout`).
- 报告里的"未命中 343 种" = 还没翻的. 这两个数字一起就是进度条.
- 风险点: `patch-package` 的 patch 冲突 (`echarts-wordcloud`), 会在 `npm run build` 第一步失败.

## 7. 未验证 / 未覆盖

1. **词汇覆盖只有样本**: 目标只选了 5 个模板 (布局页签/面积段/设置按钮/3D 打印/Explore-Compare 页签), 但因共享键扩散, 实际改到 14 个模板; 359 条里只覆盖 16 条 (4.5%). 加 .ts 9 处与绑定 13 处, 全部替换共 51 处. 全量能否无坑, 只验证了机制, 没验证规模.
2. **测试会红**: 629 个 spec/e2e/po 文件里有 62 个用可见文本断言 (`getByText` 224 次, `getByPlaceholderText` 13, `getByTitle` 11, `getByLabelText` 6, 对比 `getByTestId` 458 次). 汉化后这 254 处文本查询大概率失败. 本轮**没有**跑 `npm test`/`npm run e2e` 验证. 要么同步改测试, 要么接受内部构建不跑上游测试.
3. **Electron 打包未验证**: `npm run package` / `npm start` 未执行.
4. **运行镜像体积未实测**: 容器内无 docker, 只能确认 Dockerfile 是 nginx 单阶段 + COPY dist (6.2M).
5. **深度链接未解决**: `/dependency` `/metrics` 直连 404, 需 nginx 配置; 也未验证 Electron 下的路由行为.
6. **超长译文排版未压测**: 已翻的最长句约 30 字符; 按钮/窄栏在超长中文下的溢出未测.
7. **字体**: 本容器 Chromium 有中文字体, 截图无豆腐块; 目标机器字体未验证.
8. **未覆盖的深路径**: 3D 打印导出对话框, 场景保存/应用, 规则编辑器, domain/wordCloud 视图的实际渲染只做了代码级替换, 没逐屏截图.
9. **.ts 侧 584 条候选未逐条人工判定**, 只做了启发式分桶; A/B/C 的最终划分需要人工过一遍.

## 附: 复现清单

```
/tmp/cc-build/tools/build-zh.sh      # 一键: clone -> npm ci -> 三通道汉化 -> build
/tmp/cc-build/tools/localize.py      # 通道 A: 模板静态文案 (+ --report/--check/--restore)
/tmp/cc-build/tools/localize_ts.py   # 通道 B/C: 整条字面量白名单
/tmp/cc-build/tools/ts_strings.py    # .ts 文案统计
/tmp/cc-build/tools/shot.py / shot_click.py  # 无头 Chromium 截图 (CDP)
/tmp/cc-build/i18n/zh.txt            # 模板词表 (16 条样本)
/tmp/cc-build/i18n/zh-ts.txt         # .ts 白名单 (8 条样本)
/tmp/cc-build/i18n/zh-lit.txt        # 绑定表达式白名单 (12 条样本)
/tmp/cc-build/stat-report-pristine.json  # 模板统计原始数据
/tmp/cc-build/ts-report.json             # .ts 统计原始数据
/tmp/cc-build/localization.patch         # 本轮汉化 diff (sha256 bfce3aa6...)
/tmp/cc-build/0*-*.log                   # 各步骤实测日志
```
