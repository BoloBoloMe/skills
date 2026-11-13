# milestone-23 父会话核对

核对者: pi 会话 `01a19544-5dab-75af-bb9d-b8556cadef7c`. 研究执行者: `01a19547-6809-72d1-a809-de31ee5170c1`.
本文件是研究材料复核, 不是终点验收, 也不是重新运行分析器的独立实测.

## 已核对的证据

- 已读 `PROBE.md`, `logs/stats-deps-only.log`, `logs/stats-file-composition.log`, `logs/target-recheck.log`, `logs/host-facts.log`, 镜像失败/registry 日志和前端 console 记录.
- 已查看 `work/shot-cz-sdk-master-map.png` 和 `work/shot-cz-sdk-master-depview.png`: 前者显示真实库的 3D 建筑, 后者显示模块分层与红色依赖边. 3D 图当时的高度/颜色为 complexity, 不是已经实现的层号/违规映射.
- 统计记录支持: 文件层号 0-7 共 8 种, 文件依赖边 8820 条, `isCyclic=true` 的边 10 条, `isPointingUpwards=true` 的边 191 条, 两标志兼有 4 条. 通知中的 19 条是笔误, 不采信.
- 父会话另只读核对目标库: HEAD 仍为 `2f452a91cf3589dfbc693849beae5fcaeb927c01`, `git status --short` 无输出, `.codebase-map` 不存在. 这只证明核对时的状态, 不宣称连续审计.

## 初次核对提出的修正

已用信件 `20d3bdc3098d4490abb2a869367cad10` 退回研究执行者修正:

1. 没有语法解析失败告警, 不等于依赖名字全部解析成功. 未取得未解析文件比例时, 不得写第三项门禁通过或整体分层可信. 节点齐全/层号存在也不证明依赖抽取完整. 应明确覆盖分母, 以及磁盘 Java 文件和入图 Java 文件的差额.
2. rootless 的宿主 uid=2000 说法缺依据, 需补实际映射或删除具体数值; `--userns=keep-id` 的成功不能反推默认映射数值.
3. 用户原话是 `拿 cz_sdk-master`. 正确镜像标签由父会话公开说明后用于探针, 不得改写成用户逐项确认标签. 镜像 tag 和 CLI 自报版本不一致的原因未证实, 不得断言只是上游忘改版本串.
4. 未显式请求 `height=level` 时的默认 URL 不能单独证明显式参数失败. 区分数据字段位置, 默认显示行为, 实际参数试验.
5. 一次性脚本应对应成功运行配方, 包含只读/无网络/keep-id/文件合并, 或清楚标为历史失败脚本.
6. 修正晚于完成通知的预计完成时间, 记录实际时段.
7. 不把上游 web.zip/展开资产/sample 数据或嵌有完整私有图数据的日志提交进 skills 仓库. 原始记录外置保留并记录哈希, 仓库只收明确标识的命令/错误/结果摘录, 不删掉失败事实.

## 收口条件

研究报告如实列明已知与未证实的事实, 不用能出图代替依赖完整性证明. 无法回答的门禁和已暴露的规格冲突应接入后续 HITL 里程碑, 而非由研究代理放行或改产品决定.

## 修订后的复核 (2026-11-01 12:55 前后)

七项已逐项核对, 抽查的原始记录与报告一致:

- `logs/uid-map-verify.log`: 默认 uid_map 为 `0→1000`, `1→100000(65536)`, 因此容器 uid 1000 映到宿主 100999; keep-id 下 `1000→0`. 报告已改对, 原 2000 说法撤除.
- `logs/file-filter-diff.log`: 磁盘 src/main 2850, 入图 2846; 4 个差额逐条列出 (2 个全注释 `*TestMapper`, 2 个 `package-info`); 另 5 个在 `target/generated-sources` 被默认排除. 与报告 6.4 一致.
- `logs/unresolved-source-check.log`: 源码取证显示告警通道只有解析/超时/读取失败, 没有名字解析失败计数; 官方文档写明解析不中的名字不产边. 因此该门禁项记未验证是正确处置, 不是漏做.
- `logs/height-level-check.json`: 请求 `height=level` 后落地 URL 已被改写为 `height=complexity`, 页面无 level 痕迹; 报告已把断言收窄到"按现方案 URL 绑定实测不可行", 并声明下拉候选未穷举.
- `work/run-analysis.sh`: 已改为实际成功配方 (`keep-id` + `-nc` + unifiedparser 出文件 + `ccsh merge`), 头部注明历史失败配方与外置失败证据位置.
- 仓库内 `work/` 无 `.cc.json` 与 `.zip`, 上游前端资产与官方 sample 已移到 `/tmp/m23-evidence/frontend/`, 三份超大原始日志移到 `/tmp/m23-evidence/raw-logs/` 并登记哈希, 仓库只留带裁剪说明的摘录. 抽查摘录后无私有文件枚举残留.
- 通知里的 `isPointingUpwards 19` 为笔误, 统计与报告均为 191, 以报告为准.

## 仍未解决, 需用户裁决

1. 未解析名字比例无工具口径, 该门禁项永久不可按字面验证; 是否接受"边 8820, 层号 8 种, 语法失败 0"作为继续实施的依据, 属用户判断.
2. `D002` 镜像 tag 写错 (`ana-2.3.0` 实际是 GitHub release 名), 账本需更正.
3. `D026` 的高度绑层号在官方前端实测不可行, 需重新裁决 (build 后把 level 拷进 metrics, 或改用官方依赖视图).
4. 报告与截图含私有项目模块名和文件路径 (`czsdk-*`, `com/changzhi/...`). 若本仓库公开可见, 提交前需脱敏或改为外部引用.

以上均未由研究代理自行处置, 也没有因此改动任何决策或产品代码.
