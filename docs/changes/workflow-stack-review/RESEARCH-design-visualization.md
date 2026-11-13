# 传统设计期的代码库可视化: 事实侦查与归类

- 目的: 支撑后续决策, 我们要做的 "代码库结构可视化 skill" 该借鉴哪些成熟做法.
- 侦查日期: 2026-10-31 (UTC). 仓库数据取 GitHub REST API / GitLab API 当日快照; 许可取仓库 LICENSE 文件; 价格与产品能力取官网当日页面 (JS 页面用浏览器渲染后取正文).
- 纪律: 只做研究. 未改 skill, 未改其他文件, 未提交.
- 阅读顺序: 第 0 节给结论, 第 1-4 节给事实, 第 5 节给可借鉴项, 第 6 节划清已查证/推断/未核实.

## 0 结论速览

1. 传统设计期可视化可归五类: 结构类, 行为类, 数据类, 依赖与度量类, 协作讨论类. 五类回答的问题不同, 不能互相替代, 但对我们最有用的只有结构类 (分层语义) 与依赖度量类 (从代码抽真实关系).
2. 真正在解决 "设计图过期" 的只有三种机制: 模型即代码 (Structurizr DSL, C4-PlantUML, D2, Mermaid, PlantUML), 从代码抽依赖 (Lattix, CodeCharta, SonarQube, jQAssistant), 把架构写成可执行断言 (ArchUnit, Lattix 规则, jQAssistant constraints). 三者都不做 "意图与实际的自动映射", 那一步仍然靠人.
3. 没有任何一个成熟工具同时满足 "读任意代码库 + 画分层与模块关系 + 与设计意图对照". 结构图工具 (C4 系, UML 系) 需要人先建模; 代码侧工具 (DSM, 度量, 图查询) 只给 "实际" 不给 "意图". 这个空位就是我们的机会.
4. "城市地图" 这个隐喻已有成熟先行者: CodeCharta 把代码库画成 3D 城市 (文件是楼, 面积/高度/颜色编码度量), 并且支持两版本对比. 直接借, 不必自创隐喻.
5. 最该借的五条: C4 的四层抽象与 "少量精选视图", 视图即代码 (进版本库, CI 渲染), DSM 二维矩阵补位邻接图, 度量着色加基线对比, 只报差异 (violations) 不做全景重画.

## 1 五类划分

先给一张对照表, 下面逐类展开.

| 类别 | 回答什么问题 | 代表图型 | 代表工具 |
| --- | --- | --- | --- |
| 结构类 | 系统由哪些部分组成, 谁包含谁, 谁部署在哪 | UML 类图/包图/组件图/部署图, C4 的 context/container/component, ArchiMate 分层视图 | PlantUML, Mermaid, D2, Structurizr, IcePanel, Archi, StarUML, Enterprise Architect, Visual Paradigm, draw.io |
| 行为类 | 一次请求经过谁, 状态怎么变, 业务流程怎么走 | 时序图, 状态机, 活动图, BPMN, C4 dynamic 图 | PlantUML, Mermaid, StarUML, Enterprise Architect, Visual Paradigm, draw.io |
| 数据类 | 有哪些实体, 表怎么连, 数据从哪来到哪去 | ER 图, 数据库 schema 图, 数据流图 | dbdiagram/DBML, draw.io, StarUML, Enterprise Architect, PlantUML, Mermaid |
| 依赖与度量类 | 谁依赖谁, 有没有环, 哪里复杂度高/改动频繁, 改一处会波及什么 | DSM (依赖结构矩阵), 模块依赖图, 复杂度热图/3D 城市, 质量看板 | Lattix, Structure101 (已被收购), SonarQube, CodeCharta, jQAssistant, Graphviz, ArchUnit |
| 协作讨论类 | 团队对领域的共同理解是什么, 边界在哪, 争议点是什么 | 事件风暴便签墙 (事件/命令/聚合/限界上下文等便签), 白板草图 | 物理便签, Excalidraw, draw.io, Miro/Mural (商业白板) |

### 1.1 结构类: 回答 "有哪些部分, 怎么分层"
- 这是传统设计期的主战场. UML 提供正式语义 (类/包/组件/部署节点), C4 提供面向人的四层抽象 (system, container, component, code), ArchiMate 提供企业架构级分层 (业务/应用/技术).
- 关键差别在 "给谁看": UML 给设计和实现看, C4 给开发和运维看, ArchiMate 给企业架构师和合规看. 同一系统可以同时有这三套图, 但读者不同.
- 这类图最大的毛病是画完就冻结: 一旦代码演进, 除非有人回去改, 图必然过期 (第 3 节讲谁在补).

### 1.2 行为类: 回答 "运行时怎么走"
- 时序图/活动图/状态机/BPMN 描述动态过程, 与结构图互补. 设计期常用来校验 "这个分层是否真的按预期调用".
- 成熟做法是用同一个模型生成结构视图和动态视图 (Structurizr 的 dynamic 视图, UML 工具的同模型多图), 避免两套图各说各话.
- 对我们价值有限: 我们的目标是静态结构地图, 至多借 "同一个模型出多张视图" 这个思想.

### 1.3 数据类: 回答 "数据长什么样"
- ER 图与 schema 图是设计期最容易被代码反向证伪的一类图 (数据库是唯一事实源).
- 现在的主流做法是 schema 即代码 (DBML), 图由文本生成, 并且能双向导入导出 SQL (dbdiagram 官网: SQL import & export, export to PDF/PNG/SVG).
- 借鉴点: "用一份文本定义, 生成图, 并且能和真实系统互导" 是可复用模式.

### 1.4 依赖与度量类: 回答 "真实关系与风险在哪"
- 这一类不画 "设计应该怎样", 只画 "代码实际怎样", 因此天然不过期, 因为它每次重新算.
- DSM (依赖结构矩阵) 是二维矩阵视图: 行列都是模块, 格子表示依赖. 它比邻接图抗 "毛线球" 问题, 还能通过排序把循环依赖暴露成块 (Lattix 文档原话: DSM 是 Lattix Architect 里可视化项目的主要方式之一, 以矩阵形式展示系统组织).
- 度量类 (复杂度热图, 3D 城市) 回答 "哪里最烂/最该先动", 常与依赖图叠加使用.
- 这是与我们目标最接近的一类, 因为它承认 "代码是事实源", 图是派生物.

### 1.5 协作讨论类: 回答 "我们对领域有没有共识"
- 事件风暴是工作坊形式 (eventstorming.com 自述: 用于协作探索复杂业务域的灵活工作坊), 产物是便签墙而不是图文件.
- 工具只是白板替代品 (Excalidraw 手绘风, draw.io, Miro/Mural). 特点是快, 随意, 不追求语法正确, 因此也不承担 "与代码一致" 的责任.
- 我们能借的是它的 "低门槛表达" 与 "讨论产物", 不能借它的准确性.

## 2 工具与产物: 事实表

### 2.1 文本即图 (diagram-as-code)

| 工具 | 产物形态 | 谁先动手 | 双向能力 | 许可 | 价格 | 2026 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| PlantUML | 文本 -> PNG/SVG/EPS/PDF/LaTeX 等; 有在线服务器和 IDE 插件 | 人先写文本 | 单向 (文本 -> 图); 不生成代码 | GPL-3.0 (仓库 LICENSE 文件与 plantuml.com/license 一致; GitHub 元数据标 LGPL-3.0, 与实际文件不符, 以文件为准) | 软件免费; 去广告的 Professional 版需向作者申请 key, 价格未标, 未核实 | 活跃. 13.4k 星, 最后提交 2026-10-31, 最新 v1.2026.9 (2026-10-17) |
| Mermaid | 文本 -> 图; 浏览器/编辑器内联渲染, 有 live editor | 人先写文本 | 单向 | MIT | 免费 | 活跃. 90.9k 星, 最后提交 2026-10-31, 最新 mermaid@12.2.0 (2026-10-13) |
| D2 | 文本 -> SVG/PNG/GIF/PDF/PPTX; 有 playground 和 watch 模式 | 人先写文本 | 单向 | MPL-2.0 | 免费 (Terrastruct 另有商业产品, 未核实) | 活跃. 25.8k 星, 最新 v0.9.0 (2026-09-07); 仓库已从 terrastruct/d2 改名为 d2lang/d2 |
| Graphviz | DOT 文本 -> 多种图片格式; 常被其他工具调用来做布局 | 人写 DOT, 但多数时候是别的工具在调它 | 单向 | EPL-2.0 (GitLab 仓库 LICENSE) | 免费 | 活跃. GitLab 1.5k 星, 最新 tag 16.1.0 (2026-09-04), 最后活动 2026-10-31 |
| C4-PlantUML | PlantUML 宏库, 输出 C4 风格图 | 人先写 | 单向 | MIT | 免费 | 活跃. 7.4k 星, 最新 v2.14.0 (2026-08-26) |
| DBML / dbdiagram | 文本 schema -> ER 图; 可导出 SQL/PDF/PNG/SVG; 可从数据库导入 schema | 人先写 schema | 双向 (SQL 导入与导出, 但是 schema 级, 不是代码级) | DBML 解析器 Apache-2.0 (holistics/dbml); 在线服务另有条款 | Free 计划; Personal Pro $8/月; Team $75/月 (含 3 编辑者), 加编辑者 $5/月; 企业版报价 | 活跃. 3.7k 星, DBML v11.0.0 (2026-10-26) |
| Structurizr DSL | 一份 DSL -> 多张 C4 视图 (context/container/component/dynamic/deployment), 可交互, 可导出 PlantUML/Mermaid/静态 HTML | 人先写 DSL | 单向 (模型 -> 视图), 不从代码反向生成 | Apache-2.0 | 开源; 企业版服务器二进制需授权, 价格未核实 | 活跃但刚整合. 主仓 510 星, 最新 v2026.10.26; 旧 cli/lite/java/ui/on-premises 仓库已归档 (最后提交集中在 2026-01 到 2026-03) |

### 2.2 交互建模与桌面工具

| 工具 | 产物形态 | 谁先动手 | 双向能力 | 许可 | 价格 | 2026 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| Structurizr local/server | 本地/自托管 Web 应用, 交互式图, 支持手动拖版式 | 人先写 DSL, 工具渲染 | 单向 | Apache-2.0 (核心); 企业二进制商业 | 开源免费; 企业版授权价格未核实 | 同上, 2026 年把 lite 与 on-premises 合并进单仓 |
| IcePanel | SaaS, 交互式架构模型与图, 有 API | 人先建模 | 未核实是否有代码导入 | 商业闭源 | Free $0 (1 编辑者, 100 个对象); Growth $40/编辑者/月 (按年计); Scale $80/编辑者/月 (按年计) | 活跃商业产品, 官网 2026-10-31 可访问; 客户含 NVIDIA (厂商宣传) |
| Archi | 桌面应用 (Eclipse RCP), ArchiMate 3.2 模型与视图 | 人先建模 | 单向 (模型 -> 视图) | MIT | 免费 (接受捐赠) | 活跃. 1.3k 星, 最后提交 2026-10-30, 最新 tag release_5.10.0 (2026-09-03) |
| StarUML | 桌面建模器, UML/ERD/C4/SysML/BPMN 等多语言; 数据存 JSON | 人先建模 | 双向 (代码生成与反向工程都靠扩展; 扩展页明确列出 "Java code generation and reverse engineering") | 商业闭源 | V7 Standard $129/设备, Professional $199/设备, 一次买断; 教育 7 折 | 活跃商业产品, 官网标 v7.1.1 |
| Enterprise Architect (Sparx) | 桌面 + 仓库型模型库, 支持代码生成 | 人先建模 | 代码生成已确认; 反向工程未核实 | 商业闭源 | 官网欧洲站: Professional 225 欧, Corporate 289 欧, Unified 489 欧 (Named User, 未税); 美国站被 Cloudflare 拦, 未核实 | 活跃商业产品 |
| Visual Paradigm | 桌面 + 在线, UML/BPMN/ERD/ArchiMate 等 | 人先建模 | 未核实 | 商业闭源 | 永久授权每用户: Modeler $99, Standard $349, Professional $799, Enterprise $1999 | 活跃商业产品 |
| draw.io / diagrams.net | Web + 桌面; 文件是 XML, 可存本地/云盘; 导出 PNG/SVG/PDF/HTML | 人先画 | 单向 (可导入部分格式, 不做代码生成) | Apache-2.0 (源码) | Web 与桌面 "Free forever" (官网原话); Confluence/Jira 应用在 Atlassian Marketplace 单独授权, 价格未核实 | 活跃. 9.1k 星, 最新 v32.6.9 (2026-10-30) |
| Excalidraw | Web 白板, 手绘风; 文件 JSON, 导出 PNG/SVG | 人先画 | 单向 | MIT | 编辑器免费; Excalidraw+ $6/用户/月 (年付省 14%) | 活跃. 13.5 万星, 最后提交 2026-10-31, 最新 v0.18.1 (2026-04-21) |

### 2.3 从代码生成 / 校验的一类

| 工具 | 产物形态 | 谁先动手 | 双向能力 | 许可 | 价格 | 2026 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| Lattix | 桌面应用, DSM 矩阵 + 概念架构图 (CAD) + 热图, 可定义并执行架构规则, 有 CLI | 代码先, 工具抽依赖生成矩阵 | 单向 (代码 -> 矩阵); 规则是额外输入 | 商业闭源 | 未核实 (官网被 Cloudflare 拦, 文档站可访问) | 文档站 2026-10-31 在线, 含 DSM/CAD/热图/规则/许可管理章节; 公司维护状态未核实 |
| Structure101 | 结构分析类工具 (依赖控制, DSM 相关能力) | 代码先 | 未核实 | 商业闭源 (历史) | 已停售. 官网 FAQ 明确 "Will Structure101 products still be available for sale? No" | 已被 Sonar 收购 (sonarsource.com/structure101 有收购说明与新闻聚合), 能力并入 Sonar 产品线 |
| SonarQube | 服务端 + IDE 插件 + 看板; 问题/复杂度/质量指标 | 代码先 | 单向 (代码 -> 指标) | 核心开源 LGPL-3.0 | 云端免费到 5 万行; Team 计划起价 $34/月 (10 万行); 企业版询价 | 活跃. 11.1k 星, 最后提交 2026-10-30; 厂商称 700 万开发者/75% 财富 100 强在用 |
| CodeCharta | 交互式 3D 城市: 度量视图/领域词云/依赖视图, 可对比两个版本, 可导出 3MF/STL 打印 | 代码先 | 单向 (代码 -> 地图) | BSD-3-Clause | 免费开源 | 活跃. 566 星, 最后提交 2026-10-31, 最新 ana-2.3.0 (2026-10-28) |
| jQAssistant | 把源码/字节码/构建文件扫描进 Neo4j 图库, 用 Cypher 查询, 用 concept/constraint 校验, 可输出 PlantUML 报告 | 代码先 | 单向 (代码 -> 图库 -> 报告) | GPL-3.0 | 免费开源 | 活跃. 301 星, 最新 2.9.1 (2026-02-17) |
| ArchUnit | JUnit 测试里的架构断言 (分层/切片/包依赖/环) | 人写规则, 代码是被测对象 | 单向 (代码 -> 规则判定) | Apache-2.0 | 免费开源 | 活跃. 3.9k 星, 最新 v1.5.1 (2026-09-25) |

## 3 设计意图 vs 代码实际: 谁在解决 "图过期"

结论: 有五种机制在补, 都是半自动; 没有一种能自动把 "人脑子里的设计" 对到代码上. 这正好是我们能切入的位置.

1. 模型即代码 (model as code). 图不再手画, 而是由一份进版本库的 DSL 渲染. 图与文本同源, 文本随代码提交一起演进, 渲染进 CI.
   - Structurizr 是这条路的代表作, 官网自述 "you write Structurizr DSL to create multiple software architecture diagrams from a single model", 并称自己是 C4 的参考实现.
   - C4-PlantUML 用 PlantUML 宏把同一套语义固定下来, 降低画图的自由发挥空间.
   - 局限: 模型仍然是人写的, 代码改了模型不一定改; 只解决 "图与模型不一致", 不解决 "模型与代码不一致".
2. 从代码抽依赖. 图不存盘, 每次从代码重算, 因此不会过期, 但它只知道 "实际", 不知道 "意图".
   - Lattix 从代码/数据库/文件抽依赖生成 DSM, 再让人定义规则去约束.
   - CodeCharta 每次分析都重新生成 3D 地图, 还能加载两个版本对比 (官网: 绿色表示变大, 红色表示变小).
   - SonarQube 每次分析重算指标.
3. 把架构写成可执行断言. 这是唯一能自动判定 "违反设计" 的机制.
   - ArchUnit 在单元测试里断言分层/切片/依赖方向/无环, 失败就红. 官网自述分析字节码, 可检查包与类之间的依赖, 层与切片, 循环依赖.
   - Lattix 的规则引擎, jQAssistant 的 constraint 同理, 只是表达方式不同.
   - 局限: 规则本身是人写的意图, 覆盖率取决于人写了多少条.
4. 把代码导进图库再查询. jQAssistant 把源码/字节码/XML/构建信息扫进 Neo4j, 用 concept 补充语义, 用 constraint 校验, 还能出 PlantUML 报告, 并有 C4 等插件. 这解决 "任意问题都要预先建模" 的痛点, 允许临时提问.
5. 差异对比. CodeCharta 的两版本地图对比, Structurizr 的模型 diff (未核实具体形态), 都在回答 "这次改动让结构变好还是变坏".

一句话总结: 业界共识是 "代码是事实源, 图是派生物, 意图要显式写成规则或模型". 我们的 skill 若能把 "声明式分层" 与 "抽取出的真实依赖" 自动对齐, 只报冲突并给出证据路径, 就同时踩中了 2 和 3 两条成熟路线, 且有差异化.

## 4 2026 年现状与主流度

数据口径: 星数/最后提交/归档状态取 2026-10-31 的 GitHub 或 GitLab API; 版本号取各自 release 或 tag.

| 项目 | 星数 | 许可 | 最后提交 | 最新版本 (日期) | 归档 |
| --- | --- | --- | --- | --- | --- |
| Excalidraw | 134925 | MIT | 2026-10-31 | v0.18.1 (2026-04-21) | 否 |
| Mermaid | 90947 | MIT | 2026-10-31 | 12.2.0 (2026-10-13) | 否 |
| D2 | 25771 | MPL-2.0 | 2026-10-11 | v0.9.0 (2026-09-07) | 否 |
| PlantUML | 13390 | GPL-3.0 | 2026-10-31 | v1.2026.9 (2026-10-17) | 否 |
| SonarQube | 11133 | LGPL-3.0 | 2026-10-30 | 未取 (仓库持续发版) | 否 |
| draw.io | 9101 | Apache-2.0 | 2026-10-30 | v32.6.9 (2026-10-30) | 否 |
| C4-PlantUML | 7449 | MIT | 2026-10-13 | v2.14.0 (2026-08-26) | 否 |
| ArchUnit | 3885 | Apache-2.0 | 2026-10-27 | v1.5.1 (2026-09-25) | 否 |
| DBML | 3723 | Apache-2.0 | 2026-10-30 | v11.0.0 (2026-10-26) | 否 |
| Graphviz | 1475 (GitLab) | EPL-2.0 | 2026-10-31 | 16.1.0 (2026-09-04) | 否 |
| Archi | 1297 | MIT | 2026-10-30 | release_5.10.0 (2026-09-03) | 否 |
| CodeCharta | 566 | BSD-3-Clause | 2026-10-31 | ana-2.3.0 (2026-10-28) | 否 |
| Structurizr | 510 | Apache-2.0 | 2026-10-31 | v2026.10.26 (2026-10-26) | 否 |
| jQAssistant | 301 | GPL-3.0 | 2026-10-30 | 2.9.1 (2026-02-17) | 否 |
| Structurizr lite / cli / java / ui / on-premises | 383 / 564 / 1136 / 64 / 222 | MIT 或 Apache-2.0 | 2026-02 到 2026-03 | - | 是, 全部已归档 |

值得注意的变化:
- Structurizr 在 2026 年完成收编: lite, cli, java, ui, on-premises 五个仓库全部归档, 功能并入 structurizr/structurizr 单仓, 官方站已改为 local/server/export 三种用法. 找资料时不要再看旧仓库的 README.
- Structure101 已停止销售, 被 Sonar 收购, 能力折进 Sonar 产品. DSM 商业工具的实际存活者只剩 Lattix 这类.
- D2 仓库改名 terrastruct/d2 -> d2lang/d2, 旧链接 301.
- PlantUML 的 GitHub 许可元数据 (LGPL-3.0) 与仓库 LICENSE 文件 (GPL-3.0) 不一致, 以文件与官网 license 页为准, 写材料时别照抄元数据.
- Mermaid 已进入 12.x (2026-09 发 12.0.0), 不再是多年不变的 10/11.
- 主流度排序 (按星数与行业迹象): 白板/绘图 (Excalidraw, draw.io) > 文本图 (Mermaid, PlantUML, D2) > 代码质量 (SonarQube) > 建模 (Archi, Structurizr) > 代码结构分析 (CodeCharta, jQAssistant, ArchUnit). 注意星数只反映开源社区热度, 不代表企业采购量; 企业建模市场由 StarUML/EA/VP 这类商业工具占据, 它们没有星数.

## 5 可直接借的做法 (针对 "读任意代码库, 画分层与模块关系, 像城市地图")

1. 借 C4 的分层语义与 "视图白名单".
   - 做法: 默认只出三张图 (系统上下文, 容器/模块, 组件/包), 每张图有明确的读者与问题; 命名用 C4 词汇 (system, container, component), 不混用 "模块/服务/子系统" 这类含糊叫法.
   - 依据: C4 官网自述是 "分层抽象 + 分层图" 的模型, 且 notation independent / tooling independent; Structurizr 一份 DSL 出多张视图就是这个模式.
   - 我们怎么落地: skill 输出固定三档粒度, 每档给一句 "这张图回答什么问题", 默认不生成全景大图.
2. 借 "视图即代码", 让图能被 diff 和进 CI.
   - 做法: 图先落成文本中间表示 (自定 JSON/YAML 或 DSL), 再渲染 SVG/HTML; 文本进 git, 渲染进 CI, 图与提交同源.
   - 依据: Structurizr DSL, D2, PlantUML, DBML 都是这条路; 生成成本低才敢频繁重画, 这是抗过期的根.
   - 风险: 中间表示一旦变成第二份需要人维护的真相, 就退化成另一种过期图纸. 我们的文本必须是生成的, 不是手写的.
3. 借 DSM 的二维矩阵作为第二视图.
   - 做法: 邻接图在边多时会成毛线球, 同一份依赖数据再出一张矩阵视图, 行列按目录/包排序, 非对角块就是循环依赖, 上三角就是反向依赖.
   - 依据: Lattix 文档把 DSM 列为主要可视化方式, 矩阵形式展示系统组织; 它天生适合发现 "分层被破坏".
   - 我们怎么落地: 图 + 矩阵双视图, 矩阵可点击定位到文件和行.
4. 借 "城市地图" 的视觉编码与版本对比.
   - 做法: 面积 = 文件规模, 高度 = 复杂度, 颜色 = 变更频率或负责人; 再给 "本次 vs 上次" 的对比着色.
   - 依据: CodeCharta 官网原话是 "a 3D city of your code metrics", 三个视图 (度量/领域词云/依赖), 并且支持两版本对比, 还能 3D 打印.
   - 注意: 我们做的是 2D 地图时, 保留 "面积/颜色/高度" 三通道编码即可, 不必上 3D; 3D 的阅读成本高.
5. 借 "只报差异" 的输出形态 (violations-only).
   - 做法: 让用户或仓库声明分层规则 (允许的依赖方向), skill 从代码抽真实依赖, 只输出违反项: 违反的规则, 证据边, 文件路径, 行号; 不重画整张全景.
   - 依据: ArchUnit 的断言, Lattix 的规则引擎, jQAssistant 的 constraint 都是这个思路; 它们证明 "规则 + 抽取" 是可自动化的.
   - 这是最能形成差异的一条: 现有开源工具要么只画 (Structurizr 系), 要么只查 (ArchUnit 系), 很少有工具把 "读任意仓库 + 出图 + 报差异" 串起来.
6. 借交互式 HTML 与图例, 别只给 PNG.
   - 做法: 输出可缩放/可点击的 HTML, 带自动生成的图例, 点击节点能跳到目录或文件.
   - 依据: Structurizr 官网强调图是可交互, 可动画, 可嵌入, 并自动生成图例; CodeCharta 也是交互式.
   - 理由: 结构图的信息密度高, 静态图必然要牺牲细节; 交互能在 "总览" 与 "下钻" 之间切换.

## 6 结论边界

### 已查证 (有当日来源)
- 归类划分本身是分析框架 (我的组织方式), 但每类里的图型与工具归属有官方文档支撑: C4 官网的分层抽象与图型列表, Archi 官网的 ArchiMate 3.2 与视图/视点, eventstorming.com 的工作坊定义, dbdiagram 的 SQL 导入导出, Lattix 文档的 DSM/CAD/热图/规则章节.
- 所有星数, 最后提交时间, 归档状态, 版本号与日期: GitHub REST API (repos, releases, tags, commits) 与 GitLab API 在 2026-10-31 的快照, 见第 4 节表.
- 许可: 逐个读仓库 LICENSE 文件 (PlantUML GPL-3.0, Graphviz EPL-2.0, D2 MPL-2.0, Excalidraw MIT, draw.io Apache-2.0, Archi MIT, DBML Apache-2.0, CodeCharta BSD-3, ArchUnit Apache-2.0, jQAssistant GPL-3.0, Structurizr Apache-2.0, C4-PlantUML MIT, SonarQube LGPL-3.0).
- 价格: Excalidraw+ $6/用户/月; IcePanel Free/Growth $40/Scale $80; dbdiagram Free/Pro $8/Team $75/加编辑者 $5; SonarQube 免费 5 万行/Team 起 $34; StarUML $129/$199; Visual Paradigm $99/$349/$799/$1999; Enterprise Architect 225/289/489 欧 (sparxsystems.eu).
- Structure101 已被 Sonar 收购且不再销售: sonarsource.com/structure101 的收购说明与 FAQ 原文 "No".
- Structurizr 旧仓库归档与单仓整合: structurizr 组织仓库列表与各自 archived 字段, 新仓 v2026.10.26 与官网的 local/server/export 说明.
- PlantUML Professional 版存在且需要申请 key: plantuml.com/professional 页面原文; 具体价格页面未给出.

### 推断 (基于已查证事实的判断, 不是官方结论)
- "设计图过期问题没有完整解决方案": 依据是五种机制各自只覆盖一半 (模型侧或代码侧), 未见任何工具宣称能从代码自动恢复设计意图.
- "DSM 比邻接图更抗毛线球": 依据是矩阵的固有性质与 Lattix 的产品定位, 未做实测对比.
- "生成式图比手画图更可持续": 依据是 CodeCharta/Sonar 每次重算的设计, 未做团队使用效果测量.
- "企业建模市场由商业工具占据": 依据是 StarUML/EA/VP 均为闭源付费且无星数, 未见市场份额数据.
- 星数不等于使用量: 属于方法学判断.

### 未核实
- PlantUML Professional 版的具体价格 (页面只说申请 key, 未标价).
- draw.io 的 Confluence/Jira 应用在 Marketplace 的具体价格 (Cloudflare 与 JS 页面未取到; 官网只说单独授权).
- Lattix 的价格, 版本号, 公司当前维护状态 (lattix.com 被 Cloudflare 拦截, 只验证了 docs.lattix.com 在线).
- Enterprise Architect 的反向工程能力与最新版本号 (Sparx 美国站 403; 欧洲站只确认了 "Automatic code generation" 与价格).
- Visual Paradigm 的代码生成/反向工程能力 (定价页未提, 产品文档未查).
- IcePanel 是否能从代码或仓库导入模型 (官网只提集成, 未逐项核实).
- Excalidraw 是否内置 Mermaid 导入 (有第三方 mermaid-to-excalidraw 项目, 本次未核实其官方状态).
- Structurizr 企业版服务器的授权价格.
- SonarQube 收购 Structure101 后具体把哪些结构分析能力并入了哪个产品版本.
- Miro/Mural 的价格, 以及事件风暴工具链的具体产品形态.
- 各工具在真实团队中的采用率, 学习成本与产出质量的对比 (无公开可核对数据).
