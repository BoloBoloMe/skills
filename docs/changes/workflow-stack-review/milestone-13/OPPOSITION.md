# milestone-13 决策账本: 独立反方报告

- 任务: 对 `milestone-13/DECISIONS.md` (D001-D020, F001-F010) 做对抗性攻击
- 立场: 未参与盘问与落盘, 只站在反方; 不改账本, 不改其他文件, 不提交 git
- 方法: 按 opposing-viewpoint skill 四步; 证据分四级 — 实测 (本容器实跑) / 源码 (上游 vis-2.9.1 源码与构建产物) / 文本 (只依据仓库文档) / 未知
- 上游源码检查点: `/tmp/cc-build/src` 为 milestone-13 构建探针留下的克隆, `git log` 确认 `bd1fe9b40f987cfdc34cf169b7fb220e5ea69466`, `tag: vis-2.9.1`, 与 BUILD-PROBE.md 记录一致

## 0 一句话结论

账本里最承重的一条技术理由 (CodeCharta 前端是 HTML5 history 路由, 必须自建带深链回退的服务) 被上游源码与构建产物证伪: vis-2.9.1 用的是 hash 路由, 服务端根本收不到 `/dependency` 这种路径, 现有静态服务与上游 nginx 默认配置都够用. 这不是文字瑕疵, 它把 D006 的立项理由清空, 同时使 m21 已被判"待改写"的 nginx 方案反而是对的. 另外整条分析端 (ccsh 的 level/isCyclic) 在本仓库零次执行, 却已被写成"必须遵守", 而工具的全部价值都押在它身上.

## 1 检索范围与证据等级

已读: 本目录 `DECISIONS.md` `PLAN.md` `BUILD-PROBE.md`; `milestone-12/FINDINGS.md`; `RESEARCH-design-visualization.md`; `workflow-stack-review/ACCEPTANCE.md` (grep, 无可视化条目); `milestone-14/DECISIONS.md` (D001-D010); roadmap 节点原文 `milestone-13/14/15/16/17/18/19/20/21` 与 `notes`; `general/present/REMOTE.md`; `general/present/scripts/web_server.py` (静态查找/控制面/端口/状态段); `workflow/navigate/scripts/display_serve.sh`; `docs/adr/0025`; `docs/language/UBIQUITOUS_LANGUAGE.md`; `tests/test_skills_codex_metadata.py`.

已实测 (本容器):

| 项 | 做法 | 结果 |
| --- | --- | --- |
| present 静态服务能否服务"指向挂载根外的软链" | `PI_PRESENT_WEB_RUNTIME_DIR=/tmp/symtest/rt web_server.py start 45321 /tmp/symtest/root --bind 127.0.0.1`, 根内放 `link.cc.json -> /tmp/symtest/out/data.cc.json` | `/` 200, `/link.cc.json` **404** (事后已 `stop`) |
| 构建产物在"哑静态服务"下是否真需要回退 | `python3 -m http.server` 服务 `dist/bundler/browser`, 分别 curl | `/` 200, `/mine2.cc.json` 200, `/#/dependencies` **200**, `/dependency` 404 |
| 前端路由策略 | 读 `app/app.config.ts`, `app/codeCharta/routing/queryPreservingHashLocation.strategy.ts`, 并在 `dist/.../main-6GBGBDS5.js` 中确认 `prepareExternalUrl` 与 `.hash=` 进产物 | hash 路由, 与 BUILD-PROBE 的"HTML5 history"判断相反 |

已读上游源码 (vis-2.9.1, 与本账本若干前提直接相关):

| 文件 | 事实 |
| --- | --- |
| `app/app.config.ts:39` | `locationStrategyProvider = { provide: LocationStrategy, useClass: QueryPreservingHashLocationStrategy }` |
| `app/codeCharta/routing/queryPreservingHashLocation.strategy.ts` | 继承 `HashLocationStrategy`, 视图切换只改 `url.hash`, 查询串保留 |
| `app/dist/bundler/browser/index.html` | `<base href="./">`; CSP `default-src 'self'` (含 connect-src 回落 'self') |
| `.../stores/fileStore/loaders/ccJson/util/urlExtractor.ts` | `httpClient.get(fileName)` — `?file=` 的值被当 URL 取, 受同源与 CSP 'self' 双重约束 |
| `app/codeCharta/util/queryParameter/queryParameter.ts` | URL 参数含 `file` `mode` `area` `height` `color` `edge`, `file` 支持 `getAll` (多个库) |
| `app/codeCharta/features/navBar/services/uploadFiles.service.ts` | 有 "Load cc.json files" 本地选文件按钮 |
| `app/codeCharta/load/loadFiles.useCase.ts:57` | 无 `?file=` 时从 IndexedDB 恢复上次状态 |

评审期间观察到 (非我所改, 只作事实记录): 工作区出现另一会话正在写的 `docs/adr/0026-codebase-map-host-resident-service.md` (未跟踪), 以及 `milestone-13/PLAN.md` 与 `docs/language/UBIQUITOUS_LANGUAGE.md` 的改动. 这三处都在把账本 D006 的口径外扩, 其中"深链回退"这条错误事实已经扩散进去 (见 4.A), 所以下面的引用按评审当时的实际内容计.

检索不到的 (写入第 8 节缺口): 宿主实际环境 (Node 版本, Chromium, podman, 能否拉 docker.io); ccsh 源码与产物 (本容器无 Java, 12 号侦查与 13 号探针都未执行过分析端); CodeCharta 官方文档原页 (只经 12 号文档转述).

## 2 正方还原 (steelman)

### 2.1 定义

一个纯手动调用, 只在宿主运行, 无认证的常驻网页工具: 用 CodeCharta 官方分析镜像把某个目标代码库分析成 `.cc.json` (层号/环/向上依赖由 ccsh 给), 用构建期汉化的 CodeCharta 前端把它渲染成 3D 城市与依赖视图, 由自建的 python 常驻单例服务在局域网地址上交付, 多库靠 `?file=` 区分, 数据与状态不落在本仓库而落在目标库与 `~/.agents/codebase-map/`.

### 2.2 前提假设

| 编号 | 前提 | 账本依据 | 状态 |
| --- | --- | --- | --- |
| P1 | 用户只要自己手动看, 不进任何自动流程 | D001, F007 | 用户陈述, 稳 |
| P2 | 只在宿主跑, 页面给局域网别的机器看 | D003, D008 | 用户陈述, 稳 |
| P3 | ccsh 的 `level`/`isCyclic`/`isPointingUpwards` 语义可靠且对 Java 目标库能算出有意义的值 | D005, D019, F002 | **仅厂商文档转述, 零次执行** |
| P4 | 分析端用官方镜像就够了, 不必自建分析器, 宿主为 podman 可用 | D002, D003, F001 | 宿主 podman 有旁证 (swt 脚本), 镜像可用性未验 |
| P5 | 前端必须自己做构建期汉化, 因此宿主必须有 Node >= 22.22.3 与无头浏览器 | D013, D014, F009 | F009 证据全部来自容器 |
| P6 | CodeCharta 前端是 HTML5 history 路由, 直接静态托管会在深链/刷新时 404, 所以必须自建服务 (或有 try_files) | F004, F005, D006 | **被证伪** (第 4.A 节) |
| P7 | `?file=` 只能取同源相对路径, 所以要把数据软链进服务目录 | D011 | 前提成立 (源码证实), 推论"必须软链"不唯一 |
| P8 | 单例服务 + 一个端口 + `?file=` 能满足多库, 端口可顺延 | D007 | 语义满足用户要求, 顺延机制有事故史 |
| P9 | 状态文件足以让服务被找到与复原 | D012 | 缺探活与复原入口 |
| P10 | cc.json 放目标库 `.codebase-map/` 是正确落点 | D010 | 与 D017 默认排除冲突 (第 4.H 节) |
| P11 | 大库 (>5000 文件) 自动按目录聚合能保住可读性 | D018, F010 | 未实测, 且与 D005 "不自算" 冲突 |
| P12 | 汉化收益大于"宿主多一条 Node/Chromium 工具链 + 每次升级重翻"的代价 | D013-D016 | 用户早先确认过目标, 但从未与本轮 5 条需求对比过优先级 |

### 2.3 论据

里程碑 12 的全景对比 (只有 CodeCharta 给城市观感, 只有它的 dependencyparser 直接出层号); 里程碑 13 的构建探针 (三通道替换可行, 22-37 秒可重放, sha256 一致, 截图正常); 用户对 5 条运行要求的明确陈述; 仓库"只维护 python"的栈约束; 仓库已有 present 常驻服务的先例.

### 2.4 推理链

用户要"看代码库分层结构" -> 需要层号与依赖 -> 只有 ccsh 现成给 -> ccsh 要 Java 22/Node 22.19, 所以用官方镜像 -> 前端要中文所以要构建期汉化, 所以宿主要有 Node -> 前端是 SPA 所以要自建服务加回退 -> 交付局域网 URL, 单例加 `?file=` 满足多库 -> 数据跟库走, 状态进 `~/.agents/codebase-map/`.

## 3 主战场

**P3 与 P6 两条"承重事实"未经本仓库执行或核实就升格成"必须遵守"的决策.** 选它作主战场, 因为:

1. P6 是 D006 唯一的立项理由. 它错, 整个"自建服务 (含深链回退)"的存在依据消失, 连带 D006 的"m21 需改写 nginx"实际是撤销一个正确方案, 而 D014 的冒烟与 D009 的三子命令边界都要重新划.
2. P3 是 D005 + D019 的唯一依据. 它错或退化, 工具存在的理由 ("看分层有没有被破坏") 直接失效, 而 D004 的"未解析要显式标出"只覆盖"语言不支持", 不覆盖"语言支持但结果退化".
3. 两者共同的结构性缺陷是同一个: 账本把"在本容器验证过的前端机制"与"只在厂商文档里读到的分析语义"一起写成"必须遵守", 却没有一个"在目标运行环境 (宿主) 上先跑一次再固化"的门. ADR 0025 要求"环境不可得时报未验证缺口, 不用弱证据充抵", 账本把 P3 记成 F002 事实, 恰好是用弱证据充抵.

## 4 反方反驳

### 4.A 决定性一击: "前端是 HTML5 history 路由, 所以必须自己写带回退的服务"不成立

F005 的证据是 `python3 -m http.server` 下 `/dependency` `/metrics` 返回 404, 结论写成"因为这是 HTML5 history 路由, 需要 nginx try_files", 并在 BUILD-PROBE 补一句"index.html 里没有 hash 路由".

上游源码与产物同时否掉这个判断:

- `app.config.ts:39` 用 `QueryPreservingHashLocationStrategy`, 该类 `extends HashLocationStrategy`, 视图切换只写 `url.hash`; 路由表 `routePaths` 是 `""/domain/dependencies`. 也就是说真实地址是 `http://host:port/?file=x.cc.json#/dependencies`, 服务端看到的永远是 `/`.
- 生产产物 `dist/bundler/browser/main-6GBGBDS5.js` 里能直接看到 `prepareExternalUrl(t){let i=new URL(this.platformLocation.href) ... prepareExternalUrl(t),i.toString()}` 与 `.hash=`, 说明不是开发模式假象.
- 实测: 同一产物用 `python3 -m http.server` 服务, `/` 200, `/#/dependencies` 200, `/mine2.cc.json` 200, 只有 `/dependency` 404 — 而 `/dependency` 是应用永远不会生成的 URL 形状. 所以 BUILD-PROBE 的 curl 测的是一个不存在的路径, 404 是任何静态服务的正常行为, 不是路由缺陷.
- F005 第二句"上游 Dockerfile 用 nginx 默认配置, 同样有这个坑"随之失效: 在 hash 路由下, 上游 nginx 默认配置 (无 try_files) 本来就是正确的, 坑只存在于"路径式深链"这个被误认的形态里.

后果 (按 D006 自己的理由逐条):

1. "含 HTML5 history 深链回退, 否则 `/dependency` 之类刷新 404" — 需求本身是假的, 应整条删除. D006 与 BUILD-PROBE 里凡出现"深链回退/try_files"的表述都应作废, m21 (3) 的"必须交 try_files 配置"也应撤回, 而不是改写.
2. "用自建 python 服务替代 nginx" — 现有证据下, 静态托管这一半用 `python3 -m http.server`, 上游 nginx 默认配置, present 的 `web_server.py` 都成立. 自建服务若仍要做, 理由只能换成用户要求 3/4 的生命周期语义 (常驻单例, 端口记录不落仓库, `stop` 入口), 这是**另一条**论证, 账本没有写.
3. 这条误判有可追溯的代价: BUILD-PROBE 把"部署侧要补 history fallback"写进纪律清单第 12 条, PLAN 第 3 节据此写了 nginx.conf 配方, m21 把"交付含 try_files 的配置"列为验收项, D006 又据此否掉 nginx. 一条错误事实在三个节点上各放大一次.

**误判已经扩散到四处, 且在我评审期间还在继续扩散**:

| 落点 | 原话 |
| --- | --- |
| 账本 D006 | "把前端构建产物作为静态站点提供 (含 HTML5 history 深链回退, 否则 `/dependency` 之类刷新 404)" |
| PLAN.md 改稿 (另一会话) | "页面由自建 python 常驻服务提供 (含 HTML5 history 深链回退)" |
| ADR 0026 (另一会话, 未跟踪) | "托管构建产物 (含 HTML5 history 深链回退)"; 后果段又写"深链回退, 端口, 单例, 状态文件都由我们负责, 没有第三方配置兜底" |
| UBIQUITOUS_LANGUAGE "结构地图服务" | "托管前端产物 (含深链回退)" |

也就是说, 一个来源只有一次 curl 误读的事实, 已经变成四条记录里的"设计约束". 这不是修辞问题: 它会让实现者去写一段无人需要的回退逻辑, 让 m21 撤回一个本来正确的 nginx 交付方式, 并给"为什么不用 nginx"留下一个假理由.

置信度: 高 (源码 + 产物 + 实测三重).

### 4.B 其他关键前提的薄弱处与替代主张

| 编号 | 账本主张 | 反方反驳 | 替代主张 | 置信度 |
| --- | --- | --- | --- | --- |
| P3/D005 | 层号环与向上依赖 "沿用 ccsh 输出, 不自算", 理由"自算只有在要与 ccsh 不同时才有意义" | 理由把"要不要自算"当成口味问题, 真实问题是"ccsh 在这个目标库上算出来的东西是否可信". 全仓库零次执行 ccsh (12 号侦查结论里 ccsh 明列"不可行, 未跑"; 13 号探针只跑前端). 一旦 Java 侧退化, 页面会给出**看起来正常但错**的分层图, 比画错更危险 | 在宿主上先跑一次"分析端先导探针": 对用户真实 Java 库产 cc.json, 记录边数/层号分布/未解析比例, 再固化 D005+D019 | 高 |
| P7/D011 | `?file=` 只能同源相对路径, 所以必须软链 | 前提成立 (`urlExtractor.ts` 用 `httpClient.get(fileName)`, 且 `index.html` 的 CSP 是 `default-src 'self'`), 但"必须软链"不唯一: 前端自带 "Load cc.json files" 本地选文件按钮, 且无 `?file=` 时会从 IndexedDB 恢复上次数据 (`loadFiles.useCase.ts:57`). 软链换来的是**可书签/可复现的 URL**, 不是"能看到图" | 保留软链, 但把决策理由改成"为了可书签与可交付 URL", 并删掉"否则看不了"的隐含前提; 同时把"用户可在浏览器里手选文件"写成崩溃场景的备用通道 | 高 (前提已被源码证实, 推论需要改口径) |
| P5/D013-D014 | 汉化是 v1 的必须遵守项, 于是宿主必须 Node + 无头浏览器 | 本轮用户 5 条需求里没有一条要求中文界面; 汉化是早先 PLAN 的目标, 且实现在 m21, 与本节点是并行节点 (roadmap 里 m21 `blocked_by: []`). 把它写成 v1 前置, 等于让"第一次看到城市图"必须等 900-1000 条词表 + 一条 Node 工具链. 这与 ADR 0025 "先做出能跑的可验证版本, 垂直切片端到端交付"相反 | v1 切片拆成两层: 第一片 `web.zip` (3.5MB, 已有实测) + ccsh -> 页面, 宿主零 Node; 第二片再加汉化构建链. 两片共用同一服务与同一 cc.json 数据模型, 不返工 | 中 |
| P9/D012 | `state.json` 记端口/pid/启动时间/软链清单 | 只记不验, 就是下一个 navigate. m16 已确诊: 端口静默漂移 + 固定桥不知情 = 页面变哑; 无主单例被别的会话按收工定义 stop. m17 的定案是"显式端口 + 陌生占用报错不漂移 + `display_serve.sh ensure` 一条复原命令", D007/D012 反而选择了"顺延取空闲端口"和"只写状态文件" | D007 改为: 首选 8090, 被陌生程序占用时报错并让用户裁决, **不静默顺延**; 状态文件之外补一条 `serve --status/ensure` 型复原入口, 读记录后必须真实探活 (pid + 端口 + 首次可达校验) | 高 |
| P10/D010 | cc.json 落在目标库 `.codebase-map/cc.json` | 用户需求 5 明确要求这样, 方向没错; 但与 D017 的默认排除表冲突 (第 4.H 节): 目标库里多了这份文件后, 下一次 build 会把它当源码扫进去, 也可能把它当"未排除的产物"计入文件数阈值 | D017 默认排除补 `.codebase-map` (与 `node_modules/.git/dist/build/target/vendor` 并列), 并在 ccsh 侧确认是否已跳过隐藏目录 | 高 (逻辑必然) / 未证实 (ccsh 是否跳隐藏目录) |
| P11/D018 | 超 5000 文件自动按目录聚合 | 聚合层号需要定义"文件夹的层号" (最大? 平均?), 这本身就是 D005 明令不自算的算法; 页面顶部加提示需要改上游模板, 与 D013 "只做整条字面量替换, 不做正则或子串" 的纪律相冲; 阈值来自 F010 的"未实测" | 把 D018 降为"未决", 或改成只用前端已有能力: 用 `?height=level` 只显示层号非零的节点 (前端有搜索/过滤), 不自造聚合 | 中高 |

### 4.C 受影响却未入账的旧行为

1. **m21 的 nginx 残留不是残留, 是被误撤的正确方案.** m21 (3) 要求"交付一份含 `try_files $uri /index.html` 的配置, 用官方 nginx 镜像挂载产物与该配置, 不构建自有镜像"; D006 判定"m21 已按 PLAN 写了 nginx 配置与手册的部分需改写". 按 4.A, hash 路由下连 `try_files` 都不需要, m21 的"官方 nginx 镜像 + 挂载"成立, 需要改的只是删掉 try_files 那句. 账本的改写方向搞反了.
2. **m21 的问题描述整体过期, 但它仍是"实施输入".** m21 写"按 `milestone-13/PLAN.md` 落地, 方案已与用户敲定, 不再改方案本身", 并写"数据交付方式 (`?file=` 或浏览器选文件)" (两者都可用, 见 4.B), "手册里的 skill 名字与入口命令先用占位, 待 milestone-13 定名后替换". 而本轮账本把 PLAN 的分析端运行前提, 交付方式, 入口, 产物去向全部改写了. m21 必须整段重写, 否则实施者会照 PLAN 的 nginx + docker 配方做, 与 D002 (podman) 和 D010 (`.codebase-map/`) 直接冲突. 这条不在 D001-D020 任何一条的"预计影响"里.
3. **to-spec 入口的残留命中为零, 但残留假设仍有.** 全仓 grep `codebase-map` 只在 milestone-13 目录内命中, 没有任何活跃 skill 引用 (已查 `workflow/*/SKILL.md`, `general/*/SKILL.md`, `README.md`). 残留只在两处历史文本: `milestone-12/FINDINGS.md` 开头"既可被 workflow/to-spec 在技术规格盘问时调用", 和 m12 的路线图问题原文. 这两处按惯例保留历史不改, 但 m13 的 roadmap `artifacts` 仍为空, 账本尚未登记为产物, 存在"后续会话读不到账本"的实际风险.
4. **与 milestone-14 的三处潜在冲突, 账本一处也没记.**
   - 端口约定: m13 D007 是"首选 8090 + 顺延", m14 D005 是"宿主在 49152-65534 由代理选, 被占换端口最多 10 次", m17 定案是 navigate 固定 39300 不漂移. 宿主上将有三种端口哲学, 无一条仲裁规则.
   - 地址来源: m13 D008 说"实际取址与多页规则在 milestone-14 统一时再对齐, 本节点只要求局域网可达", 而 m14 D003 已经定死"缺值不降级, 不猜地址, 不回落 loopback, 探测结果未核实不得当可用链接交付". m13 D008 把它写成"以后再对齐", 等于把一个已裁决的硬规则留在未决态.
   - 服务身份: m14 D004 定"present 与 navigate 是不同服务, 不共用实例/状态文件". codebase-map 将成为宿主上第三个单例无认证服务, 各自一个状态文件. 术语上, 账本本身没有登记第二个服务的词条 (与 m14 D009 的"领域文档同步"惯例不一致); 评审期间另一会话已往 `docs/language/UBIQUITOUS_LANGUAGE.md` 补了"结构地图""结构地图服务"两条, 术语缺口算是被补上, 但"结构地图服务"的定义里写进了"含深链回退"这条错误约束 (见 4.A).
5. **D001 的"预计影响"漏了仓库强制项.** 本仓库 `tests/test_skills_codex_metadata.py` 要求"用户调用型 skill" (frontmatter `disable-model-invocation: true`) 必须有 `agents/openai.yaml` 且 `policy.allow_implicit_invocation: false`. D001 只说建 `workflow/codebase-map/SKILL.md` 与改 README 表, 漏了 frontmatter 标志与 codex 元数据文件 — 不补这条, 新 skill 一落地就会让仓库测试变红, 且与"只由用户手动调用"这一条本意直接对应.

### 4.D 单例 + 端口 + 状态文件的并发/崩溃/重启退化

账本给的是"状态文件 + 顺延端口", 没有锁, 没有探活, 没有复原入口, 而同样的结构在 navigate 上已经失败过一次 (m16/m17). 逐场景:

| 场景 | 现账本下的行为 | 应有规则 (账本缺) |
| --- | --- | --- |
| 两个会话同时 `serve` | 两者都读到无状态或旧状态, 都想绑 8090, 后者按 D007 "顺延取空闲端口" -> 出现两个实例, 违反 D007 的"同一时刻只有一个实例"; 状态文件被后者覆盖, 前者成为局域网上的幽灵服务 (端口暴露无认证) | 起服务前取文件锁 + 探活; 已有存活实例就复用 (present 的 `_ping_control` 已有实现), 绝不靠顺延解决并发 |
| build 与服务并发 | 若软链是 `ln -sf` 替换, 存在极短的链接缺失窗口, 期间任何刷新都取不到 data | 先建临时名再 `mv` 原子替换 |
| `kill -9` / 崩溃 | `state.json` 残留, 声称端口在监听 | 读取后必须用 pid + 端口实际探活, 残留 JSON 不算存活 (m14 D004 已定这条, m13 没定) |
| 宿主重启 | `~/.agents/codebase-map/state.json` 不是临时目录, 会跨重启存活下来; pid 可能被别的进程复用, 8090 可能被别的程序占 | 记录 `started_at` 与 cwd/命令行, 复用前三重校验; 或干脆按"宿主重启后一律需要 `serve` 重建"写清 |
| 8089/8090 后来被别的程序占 | 下次 `serve` 顺延 -> 用户书签里的旧 URL 静默失效, 但账本没有任何"地址变了要告知"的规则 | 与 m17 同口径: 报错让人裁决, 或者在输出里显式对比旧地址 |
| 用户手动删掉 `~/.agents/codebase-map/` | 服务还在跑, 状态没了, 端口不知道, 页面的 `?file=` 也无法再解析 | 明确"删状态目录等于放弃这个实例", 并在文档里给出"从 8090 逐个试/杀进程"的复原步骤 |

### 4.E 软链方案在目标库移动/删除/重命名后的行为

账本只说"同名库重跑覆盖同一条软链", 没有定义任何生命周期:

1. **库被删除**: `.codebase-map/cc.json` 与软链目标一起消失, 指向它的链接悬空; 页面 fetch 失败, 前端会报加载错误 (源码里 `getFileDataFromFile` 抛 `Could not load file`), 状态文件里"当前软链的库清单"变成一堆死名字, 无清理规则. D010 选"数据跟库走"的原始理由是"能复查", 而库一删数据即不可恢复, 这条理由只在库长期存在时成立, 账本没写这个前提.
2. **库被移动**: 软链断, cc.json 还在新位置; 用户看到的是"报错"而不是"数据在别处", 必须重跑 build.
3. **库被重命名**: 会新增一条以新名为键的软链, 旧名那条悬空留着, 服务照旧对外提供 (并对外暴露旧库名, 属信息泄露的边角).
4. **两个不同库同名** (如 `~/a/common` 与 `~/b/common`): 键是 `<库名>.cc.json`, 第二库 build 会静默覆盖第一条软链, 于是 A 库打开的页面在刷新后显示 B 库的结构, **没有任何提示**. 这是"多库"这一核心用法上最危险的一条, 账本完全没有处理 (D011 只说"同名库重跑覆盖", 假定同名等于同库).
5. **服务根目录的物理布局没定义**: 前端 `<base href="./">` + CSP `default-src 'self'` + `httpClient.get(fileName)`, 决定了数据文件的请求路径是 `http://host:port/<file 参数>`, 即数据必须与 `index.html` 在同一 URL 目录下. 而 D012 把前端产物放 `cache/`, 软链放 `data/`, D011 又写"服务只服务该目录". 三者凑不出一个能工作的根目录: 要么把 `data/` 链进构建产物目录 (该目录每次重建会被 `git checkout` + rebuild 清掉), 要么服务做虚拟根 (与"只服务该目录"矛盾), 要么把 `index.html` 也软链到 `data/` 根 (可行但账本没写). 这一条在账本里是空白, 且直接影响 D011/D012 的实现.
6. 顺带: 若实现时"复用 present 的静态服务代码", 会撞上我实测的那个 404 — present 的 `_serve_static` 先 `resolve()` 再 `relative_to(root)` 做包含性检查, 指向根外的软链一律 404. 也就是说 D011 "不复制副本, 只用软链" 与 present 已验证的安全检查互斥; 同时"服务只服务该目录"这句承诺在"跟随根外软链"的实现下技术上不成立 (服务实际能读到该用户有权限的任意路径).

### 4.F Java 优先 + 沿用 ccsh 的 level/isCyclic: 反例风险

没有任何一条证据来自一次真实运行, 以下是必须被证伪的反例清单:

1. **外部依赖不计入 -> 大面积 level 0**: 若 ccsh 只解析项目内 import (Spring 应用的类大量只 import 框架类型), 一堆文件会是"不依赖项目内任何模块"= level 0. D019 又把高度绑成层号, level 0 的建筑在 3D 里是最矮/最平的一片, 用户看到的是"一片平地 + 几根柱子", 而不是分层. 这不是渲染 bug, 但会被当成工具坏掉.
2. **多模块 Maven/Gradle 的源根识别**: 跨模块 import 需要 `src/main/java` 源根映射. ccsh 的文档摘要里点明它认 tsconfig/webpack/go.mod 别名, 对 Java 源根**没有同等说明** (12 号文档未记录). 若源根识别不准, 模块间依赖全丢, level 退化成单模块内部层.
3. **生成代码与框架**: Lombok/注解处理器生成类, DI 容器字符串注入, 反射 (`Class.forName`), JSP/XML 配置装配, 这些都不在 import 图里. 于是"架构违规为零"可能只是"看不见".
4. **`isPointingUpwards` 的参考系**: 它按 ccsh 自己的层号定义. D005 把层号, 环, 向上依赖三者一起"沿用", 等于把三个语义打包接受; 一旦发现层号口径不合用户直觉, 三者要一起换, 账本没有留第二条口径.
5. **D004 的门只挡"语言不支持"**: 它要求"该语言未解析时页面显式标出". 真正会发生的失败是"语言被支持但解析结果严重不全", 账本没有对应的护栏. 需要的是一条数值门禁: 边数为 0, 层号全同, 未解析比例过高, 超过某阈值就不许交付, 并明确说明缺什么.
6. **D019 的"颜色 = 违规标记"没有落点**: 前端的 color 是数值指标 + 阈值 (D019 依赖事实 F003 也只验证了自定义属性可选为高度/面积). 布尔 "isCyclic or isPointingUpwards" 要变成颜色, 必须先在 cc.json 里造一个数值指标 — 这已经是"自算", 与 D005 的字面口径不一致; 且把环与向上依赖合并成同一种红, 用户无法区分两类违规.

### 4.G 首次构建链路: 失败点与可重复性

P5 的链条 (宿主: podman pull -> 挂载目标库跑 ccsh -> clone 上游 -> npm ci -> 三通道替换 -> npm run build -> 无头浏览器冒烟) 在宿主上从未跑过. 可预见的失败点, 按"会不会挡住第一次使用"排序:

| 失败点 | 依据 | 后果 |
| --- | --- | --- |
| 宿主 Node 版本不满足 `^22.22.3 || ^24.15.0 || >=26` | BUILD-PROBE 记录的是**容器**的 Node v24.21; F009 自己也标"容器内实跑" | 汉化构建直接失败; 账本把 D003 "环境不足一律报错停下" 用在这里, 用户第一次用就卡住 |
| 宿主没有可用的无头 Chromium | D014 的冒烟依赖它; 探针用的是容器里的 Chromium | 冒烟失败即构建失败 (D014 明文), 于是"分析成功但没有浏览器"也判定失败 |
| `docker.io` 拉不到 `codecharta/codecharta-analysis:ana-2.3.0` | F006 只确认 github 与 npm registry 可达, 没有测 registry | 分析端根本起不来 |
| ccsh 在容器里以 root 写输出 | 通用容器行为, 账本未记录 | 目标库里出现 root 拥有的 `.codebase-map/`, 用户自己的 git/编辑器操作受阻; 二次 build 可能因权限失败 |
| SELinux 重打标签 (`:z`) / 用户名映射 (`--userns=keep-id`) | 宿主发行版未知 | 挂载目录不可写, ccsh 报无权限 |
| 磁盘占用 | clone 220M + node_modules 732M + npm cache 252M, 都在 D012 的 `cache/` 下 | 超过 1GB 且无回收规则, 每次升 tag 再叠一层 |
| 可重复性 | 镜像只钉 tag 不钉 digest; npm 53 个漏洞告警含 3 critical | 同一个 tag 拉到的镜像可能明天不同; 供应链无验证 |
| `patch-package` 与 `echarts-wordcloud` | BUILD-PROBE 已列为升级第一处见红点 | 升级即断, 属已知代价而非新风险 |

此外 D009 的三子命令有一处没有归属: `build` 只"做分析并产出 cc.json", `serve` "起或复用常驻服务", 但"前端产物不存在时谁负责第一次 clone + npm ci + build" 两个子命令的契约里都没写. 若放进 `serve`, 第一次 `serve` 会静默做 40 秒以上的网络构建; 若放进 `build`, 就违反了"build 只做分析"的划分. 这是首次使用体验上最直接的一处空白.

### 4.H 账本内部矛盾与未定义项 (汇总)

| 项 | 矛盾/空白 | 触发条件 |
| --- | --- | --- |
| D011 vs D012 | 数据软链在 `data/`, 前端产物在 `cache/`, 而 `?file=` 必须同目录解析; 服务根目录无定义 | 第一次实现 |
| D011 vs F004/实现 | "不复制副本" + "只服务该目录" 与 present 已验证的根外软链 404 互斥 | 第一次实现 |
| D010 vs D017 | 默认排除不含 `.codebase-map`, 二次 build 会把上一轮的 cc.json 当源码扫入 | 第二次 build |
| D005 vs D018 | 聚合出图必须自算文件夹层号 | 超过阈值的大库 |
| D013 vs D018 | "只做整条字面量替换" 与"页面顶部加提示"互斥 | 超过阈值的大库 |
| D006 vs D007 | D006 要求服务"提供停止入口", D007 规定单例无"只停某个库", 而 D012 的 `stop` 影响面 (会不会连带 present 的实例) 未写 | `stop` 时 |
| D008 | 没写 bind 地址. 用户要求 2 (局域网别的机器访问) 隐含 `0.0.0.0`, 但账本只写"局域网 IP + 端口"的 URL 形状 | 第一次 serve |
| D019 | 布尔违规 -> 数值颜色指标, 无转换定义 | 组装 cc.json 时 |
| D020 | "页面刷新即看到新数据" 未规定 cc.json 的缓存头; 浏览器/前端缓存可能给出旧图 | 重跑 build 后 |

## 5 反方立论 (替代主张)

立场: 需求与主体方向对, 但**固化顺序错了**, 且有两处事实必须推翻重写.

1. **删掉"深链回退"这条需求.** F004/F005 的结论作废, D006 的理由改写成"用户要求常驻单例 + 端口与状态不落仓库, 所以需要一个带生命周期的服务进程"; 静态托管本身是已解决问题. m21 (3) 撤回 try_files 要求, 保留"官方 nginx 镜像 + 挂载"作为可选交付, 与自建服务并列而不是被否定.
2. **在宿主上先做一次"分析端先导探针", 再固化 D004/D005/D019.** 对象是用户真实 Java 库, 产出 `level` 直方图, 边密度, 未解析 import 比例, 以及至少一屏截图. 门槛: 若 `level` 取值少于 3 种或 level 0 文件占比超过某阈值, D005 的"沿用"结论不成立, 退回 12 号侦查 5.2 的自算方案 (最长路径分层 + Tarjan 环检测, 200 行内) 或退回二维 cytoscape 路线. 这条探针的产物应当像 BUILD-PROBE 一样落盘, 它比"1000 条词表"更能决定这个工具是否有价值.
3. **把 v1 切成两个垂直切片.** 切片一: `web.zip` + ccsh + 静态服务 + 局域网 URL, 宿主不需要 Node/Chromium (ADR 0025 的最短路径). 切片二: 构建期汉化 + 冒烟. 两片共用同一 `.cc.json` 模型与同一服务, 切片二不改变切片一的任何外部行为; 用户能比现在早一轮看到真图.
4. **服务侧继承 m14/m17 已裁决的纪律, 而不是重新发明.** 显式 `--bind 0.0.0.0`; 首选端口被陌生程序占用时报错让人裁决, 不静默顺延; 状态文件只作线索, 复用前必须探活; 提供一条幂等的 `ensure` 复原入口 (m17 的 `display_serve.sh` 就是现成范本). 状态文件放 `~/.agents/codebase-map/` 是用户要求, 保留, 但记录内容要加 `started_at` 与可执行路径以便校验 pid 复用.
5. **`?file=` 的键改成"路径指纹"而不是"库名".** 例如 `<basename>-<8 位路径哈希>.cc.json`, 并在状态文件里保留 名字 -> 绝对路径 的可读映射. 这样同名库不再互相覆盖, 重命名产生新键而旧键可被识别为悬空并在 `serve` 启动时清理.
6. **把 D018 降级.** 前端已有搜索/过滤与 `?height=` `?color=` 参数, 大库可读性先用"只看层号非零/只看违规"这类前端能力解决, 聚合留到实测后; 若仍要聚合, 必须在账本里写清文件夹层号的定义, 并承认这一次是自算.
7. **补三条账本缺的护栏.** 解析退化门禁 (边数/层数/未解析比例); 软链悬空与同名冲突的显式报错 (不许静默给错数据); 首次初始化 (clone + npm ci) 归属到 `build` 并明说它是慢操作.
8. **交付 URL 用上前端已有能力.** `?file=x.cc.json&height=level&area=rloc&color=<违规指标>#/dependencies` — 指标绑定与视图都能写进 URL (`queryParameter.ts` 实测含 `area/height/color/edge/mode`, 路由是 hash). 这样做的好处: cc.json 可以保持 ccsh 原样输出, D019 从"组装期改数据"变成"交付期拼 URL", 与 D005 的"不自算"更相容, 且用户书签能记住看的是哪个视图.

## 6 幸存与比较

正方仍成立且不应被推翻的部分:

- D001 (纯手动, 不被任何 skill 调用) — 与用户需求 1 完全对应, 且全仓无残留引用, 反方无异议.
- D003 (只在宿主, 不降级, 环境不足报错) — 方向正确, 反方只是要求把"环境"清单补全 (Node/浏览器/registry) 并接受它可能挡住第一次使用.
- D010 (cc.json 跟库走) 与 D016 (仓库不放上游源码与产物) — 对应需求 5 与仓库卫生, 只需补 D017 的排除项.
- D013 的**机制** (三通道整条字面量替换, 幂等可重放, sha256 一致) — 探针实测扎实, 反方不质疑机制本身, 只质疑它在 v1 关键路径上的位置.
- D017 的排除思路, D020 的幂等覆盖 — 合理, 需要小补.
- D002 选官方镜像而非自建分析器 — 在"宿主已有 Java 22/Node 22 吗"未知的前提下, 这个选择是正确的成本判断; 反方反对的是"选完就算验证过了".

比较 (影响范围 x 发生概率 x 不可逆性):

| 争点 | 影响范围 | 概率 | 不可逆性 | 判定 |
| --- | --- | --- | --- | --- |
| 深链回退事实错误 | D006 的理由, m21 的验收项, 部署手册 | 已确定发生 (源码 + 产物 + 实测) | 若照账本实施, 会写一份不必要的回退, 并撤掉一个正确方案; 可改但会留下"为什么当初要自建服务"的错误理由 | 反方占优 |
| ccsh 分析语义未验 | 工具的全部价值 | 中 (Java 外部依赖占比高, 退化常见) | 高: 固化后 1000 条词表与 D019 指标都建在它上面; 若后期才发现 level 无意义, 数据模型与文档要重写 | 反方占优 |
| 单例/端口/状态缺探活与复原 | 每次宿主重启或端口冲突后的可用性 | 高 (m16 已实证同类结构会坏) | 中: 可补, 但事故已经发生过一次 | 反方占优 (要求改 D007/D012 细则) |
| 汉化在 v1 关键路径 | 首次可用时间, 宿主工具链负担 | 高 | 低-中: 顺序调整不需返工设计 | 反方占优 (仅顺序, 不否定目标) |
| 软链同名冲突/根目录布局 | 多库这一核心用法 | 中 (同名库常见: 两个 checkout 的 common) | 中: 会静默给出错误的库结构 | 反方占优 |
| D001/D003/D010/D016 | 范围与卫生 | — | — | 正方成立 |

即使接受正方最强的幸存论点 — "自建一个带生命周期的服务本来就要写点代码, 顺手加个回退不亏" — 反方仍占优: 这条辩护只说明"写了也不致命", 不说明"F004/F005 的判断是对的", 而错误的理由已经进入 m21 的验收项和一个部署纪律. 反方要的不是删服务, 是删伪需求并补真门禁.

## 7 置信度

| 结论 | 置信度 | 依据 |
| --- | --- | --- |
| 前端是 hash 路由, 深链回退不需要 | 高 | 源码 `app.config.ts:39` + 策略类 + 产物 bundle + 实测 |
| F004/F005 的结论不适用于 vis-2.9.1 | 高 | 同上; F004 的事实 (present 无回退) 为真, 推论不适用 |
| `?file=` 受同源与 CSP 'self' 约束 (D011 前提成立) | 高 | `urlExtractor.ts` + `index.html` CSP |
| 服务根目录布局在账本里无解 (D011 vs D012) | 高 | 三者文本 + `<base href="./">` |
| 同名库静默覆盖, 无冲突处理 | 高 | D011/D020 文本推理, 必然发生 |
| 二次 build 会把 `.codebase-map/cc.json` 扫进目标树 | 中高 | 逻辑必然; ccsh 是否跳隐藏目录 未证实 |
| present 静态服务不能服务根外软链 | 高 | 本容器实测 404 |
| D007 顺延端口会造成静默失联 | 高 | m16 H1 实证同类; m17 已定"不漂移" |
| ccsh 在真实 Java 库上的 level 会退化 | 中 | 反例推理, 缺实测; 外部依赖与源根识别均未核 |
| 宿主 Node/Chromium/registry 不满足 | 未知 | 容器外无法检查; 但 F009 证据确实只覆盖容器 |
| D018 与 D005/D013 冲突 | 中高 | 文本推理, 不需外部事实 |
| D013 应从 v1 关键路径移出 | 中 | 价值判断, 依赖"先看到图"的优先级 |
| m21 需整段重写 (nginx + PLAN 引用) | 高 | m21 原文与 D002/D006/D010 直接冲突 |

## 8 缺口 (反方也无法核实的部分, 不应被当作已解决)

1. 宿主实际环境: Node/npm 版本, 是否有可用 Chromium 或无头浏览器, podman 版本与 SELinux/用户命名空间配置, 能否拉 `docker.io`. 全部只能由宿主会话确认; 本报告所有关于"宿主会失败"的论点都标为中或未知, 不是已证事实.
2. ccsh 行为: 本仓库从未执行分析端 (12 号已判"不可行, 未跑"), 源码不在本容器 (只有 `visualization/` 与 `analysis/` 的部分文件, 未读 Kotlin 实现). 因此"文件夹是否有 level" "Java 源根是否识别" "外部依赖是否计入" "隐藏目录是否跳过" 全部未证实, 只是必须被测的反例.
3. cc.json 的 checksum 规范: 12 号文档自己标"未核实"; D019 要求组装指标, 而组装是否要重算 checksum 属未决.
4. `?file=` 跨源可行性: 源码显示用 `httpClient.get`, 但 CSP 与 CORS 叠加后的实际行为只做了静态推断, 没在浏览器里试过跨源 URL. 本报告的结论 (必须同源) 在 CSP 存在时成立, 若上游改 CSP 则失效.
5. 大库观感与帧率 (F010), 超长中文排版, 中文字体在用户设备上是否存在, Electron 打包: 与账本一致地保持未验证.
6. 本轮未读: `general/present/tests/` 全量 (只用了实测替代), navigate 的 `web_server.py` (只读 `display_serve.sh` 与 roadmap notes), 以及 `docs/changes/workflow-stack-review/milestone-02..11` 的账本正文 (只读 ACCEPTANCE grep 结果与路线图摘要), 因此"其他节点是否还有可视化前提残留"只能保证在 `codebase-map` / `codecharta` / `nginx` / `to-spec` 四个关键词的 grep 范围内.
