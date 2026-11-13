# milestone-23 分析端探针报告 (PROBE)

任务: workflow-stack-review/milestone-23. 执行: 独立研究代理 (pi 会话 01a19547-6809-72d1-a809-de31ee5170c1), 宿主 Ubuntu-Workstation.
时间: 主体探针 2026-11-01 12:07-12:41; 按父会话复核意见修订补查 12:44 起 (同日). 所有产物在本目录; 大体积原始证据在外部 /tmp/m23-evidence/ 与 /tmp/m23-out/ (哈希见 10 节), 不入任何仓库. git 提交归父会话, 本节点未 commit.

标注规则: [实测] = 本机真实执行有日志有哈希; [文档] = 官方资料/registry API 转述, 未在本机执行; [未验证] = 没做或做不成, 缺口如实列出.

## 0. 结论速览

- 探针总体: 分析链路在用户真实 Java 库 cz_sdk-master 上端到端跑通, 产出非零且多层: 依赖边 8820 条, 文件 level 8 种 (0-7), 目录 level 7 种 (0-6), 环与向上依赖均有非零计数. 前端 vis-2.9.1 原版可吃该数据并真实渲染, console 0 错误.
- 但 "未解析 import/名字解析率" 门禁项无法按工具口径验证 [未验证]: 工具不输出名字解析统计, 日志无 warning 只证明语法/读取层零失败, 不等于名字都解析到了项目声明 (详见 6.4/6.5). 故不写 "门禁全过/分层可信" 的启发式结论, 该门禁项连同整体上线判断交用户裁决.
- 镜像 tag 事实: D002 写的 `ana-2.3.0` 在 docker.io 不存在 (manifest unknown); 纯数字 tag `2.3.0` 存在且与 GitHub release ana-2.3.0 同日同版本. 用户指定目标库 cz_sdk-master; 改拉 2.3.0 由父会话明示 (同版本命名纠正), 见 2.3/2.4.
- 官方 "管道合并指标" 在本环境实测损坏; 用官方 `ccsh merge` 替代成功 (6.3).
- D026 的 height=level: 实测 URL 显式请求 `height=level` 被前端静默改写为 `height=complexity`, 加载后页面无 level 候选痕迹; 数据层事实是 level 在 dependency lens 不在 metrics lens. 说法按证据收窄, 见 8.2.
- rootless podman 必须 `--userns=keep-id` 才能写宿主目录 (6.1, uid 映射已用 /proc/uid_map 实证).

## 1. 目标库认定

### 1.1 候选清单 [实测]

扫描 ~/Workspace 全部 .java (find 全深度) (2026-11-01 12:06):

| 路径 (~/Workspace/ 下) | 分支 | HEAD 提交 | 提交时间 | .java 数 | 脏文件 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| ChangZhi/cz_sdk/cz_sdk-master | master | 2f452a91cf3589dfbc693849beae5fcaeb927c01 | 2026-10-30 20:12 | 3312 | 0 | 394M |
| ChangZhi/cz_risk_discern/cz_risk_discern-master | master | 6e20a5468044aaccd55bf5f596006f7d87ffd1e5 | 2026-09-10 11:24 | 558 | 0 | 17M |
| ChangZhi/cz_risk_discern/cz_risk_discern-master-feature-export | feature/export | 2f9bf92aeec8f7e7ac8eae891cd6d999ed400586 | 2026-11-01 11:56 | 594 | 0 | 当时用户正在开发 |
| ChangZhi/cz_sdk/cz_sdk-master-fix-20261103-payment-center-bug-fix | fix/20261103-payment-center-bug-fix | 785e5d432564d982e0f7484d04edee373916cbc5 | 2026-11-01 02:08 | 3309 | 0 | fix 工作树 |
| ChangZhi/cz_sdk/ 其余 4 个工作树 | release/feat 各分支 | (见候选 request 信件) | - | 3106-3272 | 0-1 | 同类 |
| ChangZhi/cz_sdk/cz_sdk-test | 非 git 仓库 | - | - | 3458 | - | 目录拷贝 |
| ChangZhi/cz_sdk/stripe-java34-shaded | 裸仓库 | - | - | 0 | - | 无工作树 |

其余目录 (skills/, requests/, my-editer/, slim-subagent/, cliproxyapi/, DataGripProjects/) 无 .java [实测].

### 1.2 认定过程与用户裁决

存在多个同等级候选, 无法单义辨明. 已发 request 列候选 (信件 9d308d70752a4d29ba2a607a1264f79f). 用户裁决: 指定 cz_sdk-master (父会话信件 59676bda2f9a424b8820e2362df41e1f 与 20d3bdc3098d4490abb2a869367cad10 转述一致).

### 1.3 实跑前复核 [实测]

logs/target-recheck.log (12:30:39): 分支 master, HEAD=2f452a91cf3589dfbc693849beae5fcaeb927c01 ("doc: 新增 bug 报告", 2026-10-30 20:12 +0800), 脏文件 0. 规模: .java 共 3312 (src/main 2850, src/test 457, 其他 5). 多模块 Maven, 12 个顶层目录.

### 1.4 完好性回查 [实测]

主体分析后 (12:41) git status --porcelain = 0 行, HEAD 未变, `.codebase-map` 未创建, 目标库零改动. 全程只读挂载 (:ro).

## 2. 镜像拉取 (步骤 1)

### 2.1 钉定 tag 实测 [实测]

`podman pull docker.io/codecharta/codecharta-analysis:ana-2.3.0` 失败: `manifest unknown` (原始日志与 2.4 成功拉取记录同在 /tmp/m23-evidence/raw-logs/ 及 logs/podman-pull.log 摘录). 未擅自换 tag.

### 2.2 只读诊断 [实测, registry API]

- 仓库 docker.io/codecharta/codecharta-analysis 存在且 active.
- 版本 tag 纯数字: latest, 2.3.0, 2.2.1, 2.2.0, 2.1.0, 2.0.2, 2.0.1, 2.0.0, staging-*. 无 ana- 前缀; 可视化仓库 codecharta-visualization 同风格 (2.9.1). logs/dockerhub-diagnose.log.
- tag 2.3.0: linux/amd64, manifest digest sha256:6402a87f6823c8123de6c8706ffc7b68ae75ce2c2c58aa8b3fcab59e97d1f7a4, 镜像 532445458 字节 (压缩), 推送 2026-10-28 09:52 UTC. logs/dockerhub-tag23.log.

### 2.3 命名混淆溯源 [实测, GitHub API]

GitHub release tag `ana-2.3.0` ("Analysis release 2.3.0", 2026-10-28) 与 `vis-2.9.1` ("Visualization release 2.9.1", 2026-10-23, assets 含 web.zip 3537671 字节) 存在. 判断: D002 的 `ana-2.3.0` 是 GitHub release tag 命名; docker hub tag 是纯数字 `2.3.0`, 二者指向同一分析版本 (发布同日). logs/github-releases.log. 是否修 D002 账本由父会话/用户定.

### 2.4 实际拉取 [实测]

- 用户指定目标库 cz_sdk-master; tag 2.3.0 由父会话明示 "按官方正确名称下载原定 2.3.0 继续试跑" (同版本命名纠正, 非升级非上线). 本节点未把该纠正伪记成用户逐项确认.
- 12:30:47 `podman pull docker.io/codecharta/codecharta-analysis:2.3.0` 成功, 耗时 60s:
  - Image Id: sha256:b10fce5f615e44c65b24d5aadbb86b6cea635999536109029edcaaffb2743fae
  - RepoDigest: docker.io/codecharta/codecharta-analysis@sha256:6402a87f... (与 2.2 registry 声明一致)
  - 平台 linux/amd64, 本地解压后 1268480310 字节 (1.27 GB), Created 2026-10-28 09:52 UTC, User=ubuntu, CMD=["ccsh"], 无 entrypoint.
- 版本不一致记录 [实测]: 镜像 tag 2.3.0, `ccsh --version` 自报 `version "2.2.1"` (logs/ccsh-version.log). 二者不一致的原因未查明 (未做源码核实), 本报告不推断谁对谁错; 日后版本核对建议以镜像 digest 为准 (D030 已要求记 digest), ccsh --version 仅作参考.

## 3. 宿主事实 (步骤 4) [实测]

logs/host-facts.log (12:07):

- podman 5.7.0, rootless=true, uid=1000(bolo), subuid/subgid bolo:100000:65536.
- SELinux 不存在 (/sys/fs/selinux 无, getenforce 无此命令; Ubuntu 走 AppArmor). 探针遇到的写盘权限问题与 SELinux 无关, 是 rootless uid 映射 (6.1).
- 宿主 RAM 30Gi (可用 19Gi), 磁盘 / 剩 362G, 16 核.
- Node v24.19.0, fnm 管理. 满足 ccsh 要求 `^24.15.0` — 本探针按 D002 用镜像, 未依赖宿主 Node.
- 无头浏览器: playwright chromium-1234 (151.0.7922.34) 实测 launch 成功; 系统另有 /usr/bin/google-chrome, /usr/bin/firefox.
- 在跑容器: gitea, guacamole 三件, cliproxyapi, 两个 sandbox-worktree — 全程未碰.
- 端口: 8802/8803/8804/18199 被其他会话临时服务占用, 未动; 本任务用 18923 (仅 127.0.0.1), 已停.

F015 逐项关闭: Node 版本已核实; 无头浏览器已核实可用; docker.io 可达 (tag 拼写是唯一失败原因, 2.3.0 成功); SELinux 不存在; userns rootless 默认 + subuid 65536.

## 4. 分析端真实命令 (步骤 2 前半) [实测 help + 文档]

镜像内 `ccsh dependencyparser --help` (logs/ccsh-dependencyparser-help.log) 与 ana-2.3.0 官方 README (/tmp/m23-evidence/ 外部文档日志) 一致:

- 形状: `ccsh dependencyparser FILE_or_FOLDER [-o out.cc.json] [-nc]`; 官方合并指标示例为管道 `ccsh unifiedparser <proj> -nc | ccsh dependencyparser <proj> - -o out.cc.json` (本环境实测损坏, 见 6.3).
- 关键参数: --include-tests (默认排除测试), -ibf 含 build 目录 (默认排除), --bypass-gitignore, -e 排除正则, -fe 扩展名, --max-file-size, --file-timeout, --omit-graph-analysis, --commit=<ref>.
- 输出: cc.json 2.x, dependency lens (nodes{level}, edges{dependencies,isCyclic?,isPointingUpwards?}) + metrics lens (outgoing/incoming_dependencies) + 逻辑层 namespaces/leaves/leafEdges [文档, 本机产出与之一致].
- level 语义 [文档]: 每个文件/目录在其父内的层化深度, 0=不依赖任何东西; 物理目录树与逻辑命名空间树各层化一次, 两套 level 允许不同.
- isCyclic [文档]: 声明级环 (Tarjan SCC + 有界 DFS, 环长按分量边数封顶 10/8/6/4), 文件边=任一背后声明边成环. 统计对象是边.
- isPointingUpwards [文档]: 逆层化流向, 目标 level >= 源 level 即算 (同级也算, 官方自认已知弱点); 文件层与命名空间层各一次. 统计对象是边.
- Java 名字解析 [文档]: 按 JLS 作用域/影子/导入规则 + JDK 标准库过滤器; 不支持 module-info 边界等 (清单见外部文档日志). 解析不中的名字静默不产生边, 无计数输出 (6.4).

## 5. 前端 vis-2.9.1 与渲染管线 (步骤 3 前半) [实测]

- web.zip 下载自官方 vis-2.9.1 release (3537671 字节, sha256 18b6377f...), 解压 43 文件 6.2M. 按父会话指示, 资产已整体移至 /tmp/m23-evidence/frontend/vis-2.9.1/ (web.zip + unpacked/ + serve/), 仓库内无前端资产与 sample*.cc.json (D016 纪律), 哈希见 logs/evidence-hashes.log.
- index.html 带 `<base href="./">` + CSP `default-src 'self'` (与 F014 一致); 自带 sample 即 apiVersion 2.0; 前端 bundle 含 isPointingUpwards/isCyclic/leafEdges/namespaces 关键字 — vis-2.9.1 原生支持 dependency lens.
- 冒烟 (sample1.cc.json): HTTP 200, WebGL canvas 中央像素 (162,17,17,255), console 0 错误, 截图 /tmp/m23-evidence/frontend/ 下与 work/smoke-sample1.png. 管线可用.
- 临时静态服务: 127.0.0.1:18923 (uv run python -m http.server), 非产品实现, 用完即停, 未碰其他会话服务.

## 6. 真实库分析 (步骤 2 后半)

### 6.1 运行方式与 uid 映射实证 [实测]

成功配方 (work/run-analysis.sh, 已改写为实测成功复跑版):

```
podman run --rm --network=none --userns=keep-id \
  -v /home/bolo/Workspace/ChangZhi/cz_sdk/cz_sdk-master:/proj:ro \
  -v /tmp/m23-out:/out \
  docker.io/codecharta/codecharta-analysis:2.3.0 \
  ccsh dependencyparser /proj -o /out/deps-only.cc.json -nc
```

首跑 (无 --userns=keep-id) 分析本体完成但写盘 Permission denied. 根因用 /proc/self/uid_map 实证 (logs/uid-map-verify.log):

- 默认映射实测: `0→1000 (1 行), 1→100000 (65536 行)` — 即容器 uid 0 = 宿主 1000, 容器 uid N>=1 = 宿主 100000+(N-1). 容器内 ubuntu 是 uid 1000, 映到宿主 100000+999=**100999** (与父会话按 subuid 推算一致; 此前报告写 "映成 2000" 是错的, 以本实测为准). 宿主无 uid 100999, 对 bolo 拥有的 /tmp/m23-out (775) 只有 other 的 r-x, 无写权 → Permission denied.
- keep-id 实测: uid_map 使容器内 uid 1000 对齐宿主调用者 uid 1000 (经父用户命名空间 0 转达), 写盘以 bolo 身份成功, 宿主文件属主 bolo.
- 与 SELinux 无关 (本机无 SELinux). 源码只读 (:ro), 无网络 (--network=none), --rm 用完即删, 未提权, 未碰现有容器.

### 6.2 Run A: 纯依赖图 [实测] (12:32:44 成功, 约 26 秒)

- 产物 /tmp/m23-out/deps-only.cc.json, 5027105 字节, sha256 0f7f3305...(全哈希见 10 节).
- 摘录见 logs/run-a-deps.trimmed.log (原始完整日志在 /tmp/m23-evidence/raw-logs/run-a-deps.log, sha256 3b8dab2e..., 其中进度条流内嵌全部被解析文件名枚举, 按父会话指示原件外置不入仓库, 仓库只留剔进度条摘录).
- 运行日志关键行: Resolving dependencies 218ms; Analyzing cycles: Found 20 strongly connected components, Found a total of 52 cycles (1110ms); Leveling folder tree 237ms; Leveling namespace tree 735ms; Created Project with 3014 leaves.
- 全程无任何 WARN/ERROR 行 (原始日志已逐行核查).

### 6.3 指标合并: 官方管道损坏, 官方 merge 替代成功 [实测]

- 官方管道 `ccsh unifiedparser /proj -nc | ccsh dependencyparser /proj - -o full.cc.json` 失败: `MalformedJsonException: Unterminated string at line 1 column 114642` → "The piped input is not a valid project... Skipping piped project..." (摘录 logs/run-b-merged.trimmed.log, 原件外置). 产物 full.cc.json 与 deps-only 逐字节相同 (sha256 同) — 指标未合入. 根因未深挖, 如实记录.
- 替代 (同为官方工具): (a) `ccsh unifiedparser /proj -nc -o /out/metrics.cc.json` 成功 (2846674 字节; "511 Files ... ignored as they are currently not supported" 列出 .xml/.yml/.json 等非源码扩展; "14 files were excluded by .gitignore rules"); (b) `ccsh merge metrics.cc.json deps-only.cc.json -o merged.cc.json -nc` 成功: "3697 nodes were processed, 0 were added and 3697 were merged". merged.cc.json 7458943 字节, 边 8820 保留, 指标齐 (rloc/loc/complexity 等 24 种, 覆盖 3637 文件含测试; 依赖 lens 覆盖 3014 文件).

### 6.4 门禁统计与分母 [实测] (logs/stats-deps-only.log, 统计脚本 work/stats.py)

分母构成 (磁盘 3312 .java → 依赖树 3014 文件) [实测, logs/file-filter-diff.log]:

- src/main 2850 → 入图 2846. 差 4 个: (a) 2 个 *TestMapper.java (位于 src/main) — 实测文件本体 rloc=0 (86 行全为注释的停用代码, metrics.cc.json 交叉验证), parser 读得但无可分析声明, 依赖树整体不含此类文件 [实测, 单文件复现 logs/single-file-test.log: WARN "No analyzable declarations were found..."]; (b) 2 个 package-info.java (28 字节, 只有包声明, 无类型) — 同机制不入依赖树. 两者均未被 .gitignore 命中, 排除发生在 "零声明文件不入依赖树" 这一工具行为, 非测试/忽略规则.
- src/test 457 → 入图 0 (工具默认排除测试; 识别规则源码 TestFileDetector: 目录 test/tests/__tests__/spec/specs 或 Java 名以 Test/Tests 结尾).
- 其他位置 5 个 .java 全在 target/generated-sources/ (注解处理与 groovy stub 生成物) → 被 build 目录默认排除.
- 非 .java 入图: 122 .js + 22 .html + 21 .sql + 3 .py (多语言顺带解析, 第一版验收范围外的语言). 树含 Folder 683.

统计结果:

- 依赖边总数: 8820. 边权 dependencies: 1 次 8519 条, 最大 25. 文件端点覆盖 2718/3014 (90%); 零内依赖文件 296 (9%) — 这是"库内无依赖", 不等同未解析.
- level 分布 (dependency lens, 3696 项 = 3014 文件 + 682 目录, root 无 level 属预期):
  - 文件 (8 种): {0: 2414, 1: 394, 2: 105, 3: 71, 4: 20, 5: 6, 6: 2, 7: 2}
  - 目录 (7 种): {0: 471, 1: 101, 2: 59, 3: 32, 4: 11, 5: 6, 6: 2}
- 逻辑层: 541 namespace (level 0-9 共 10 种), 声明 7547, 声明级边 17979.
- isCyclic=true: 10 边; isPointingUpwards=true: 191 边; both: 4; regular: 8623. 含义见 4 节 [文档], 统计对象都是边.
- apiVersion "2.1" (2.0 演进版, 前端实测可吃).

### 6.5 "未解析 import/名字解析率" 口径核查 — 门禁该项 [未验证]

- 语义区分 [实测+源码]: "语法解析失败" (文件读不了/解析出错/超时) 与 "名字未解析" (import/名字解析不到项目声明) 是两回事. 日志无 warning + 3014 文件全进 lens, 只证明前者为 0.
- 工具输出口径 [源码核查, logs/unresolved-source-check.log]: ExtractionPipeline 唯一告警通道是 FailedFile (解析/超时/读取失败), `FailureReport.warnAbout` 按原因汇总; ProcessingPipeline/DependencyResolverService/FileReport 无任何未解析计数或告警; 官方名字解析文档明写解析不中的名字 "draws no edge" (静默无边). 结论: 工具不提供 "未解析 import 比例" 的精确定义与分母, 也无输出可推.
- 机制性事实 [实测]: 零声明文件 (如上述 4 个) 整体不进依赖树; 有声明但 import 指向 JDK/第三方的, 按官方设计被标准库过滤器排除, 不产生边, 工具语义使然; 哪些名字解析失败无法从输出得知.
- 处置: D029 的 "未解析文件比例过半" 门禁在本工具上无法按字面执行 (无口径), 该项记 [未验证] 而非 "通过". 可靠的替代事实: 语法解析失败 0/3014; 零声明剔除 4 个 (已逐一定性); 边 8820 非 0; level 多种. 是否算 "门禁通过" 交用户裁决, 本节点不下启发式结论.

### 6.6 门禁核对 (D028/D029) — 修正版

| 门禁项 | 阈值 | 实测 | 结论 |
| --- | --- | --- | --- |
| level 种数 (文件) | >= 3 种 (D028 口径) | 8 种 [实测] | 该项达标 |
| 依赖边数 | > 0 | 8820 [实测] | 该项达标 |
| 未解析文件比例 | 不得过半 | 工具无口径 [未验证]; 语法失败 0/3014, 零声明剔除 4 个已定性 | 该项无法验证, 交用户裁决 |
| 明显退化 | 无 | 层化金字塔正常, 环/向上依赖非零 [实测] | 无退化迹象 |

综合: "分析链路跑通且非零多层" 成立; "门禁三项全过/分层可信" 的说法已撤回. 上线与否由用户按 6.5/9 节缺口裁决.

## 7. 真实数据吃进前端 (步骤 3) [实测]

- serve 根 = /tmp/m23-evidence/frontend/vis-2.9.1/serve/ (解包前端 + cz-sdk-master.cc.json 同目录, F014 满足), 临时服务 127.0.0.1:18923, 已停.
- 3D 城市图: playwright headless chromium 1920x1080 加载 `/?file=cz-sdk-master.cc.json`, HTTP 200, console 0 错误 0 pageerror 0 请求失败 (仅 4 条 GPU 性能 warning), 截图 work/shot-cz-sdk-master-map.png (223KB). 页面标题 cz-sdk-master. 前端自动补全 URL: `?file=...&area=rloc&height=complexity&color=complexity&edge=dependencies`.
- 依赖视图: 点导航 Dependencies → URL `...#/dependencies` (hash 路由, 印证 F011). 该视图是 ECharts/zrender 2D 画布 (非 WebGL), 面板显示 "EDGES SHOWN: In a cycle, Points upward, Points upward and closes a cycle / EDGE STYLE: Combined|By count / EDGE METRIC: dependencies / HIERARCHY: Folders", 页脚 v2.9.1. 截图 work/shot-cz-sdk-master-depview.png.
- 边渲染像素取证 (work/shot-pixel.py, logs/pixel-cz-sdk-deps.json): 依赖视图 canvas 1920x994, 非空像素 899372, 红色 #dc2626 容差扫描命中 1343 像素 — 向上依赖边真实画出. 蓝色 (cyclic 非 upward) 0 像素: 默认过滤组下环边可能落在未展开层级, 未逐层展开验证 — 记为未验证细节.
- height=level 最小补查 (修订新增, work/height-level-check.py, logs/height-level-check.json): 显式加载 `?file=cz-sdk-master.cc.json&height=level&area=rloc&color=complexity` [实测] → 前端静默改写为 `height=complexity` (落地 URL 实测), 全页文本无 "level" 候选痕迹; 指标选择器为自定义组件 (非原生 select), 完整下拉候选未枚举 — 记为该补查的剩余小缺口. 截图 /tmp/m23-evidence/frontend/shot-height-level-request.png.

## 8. 与既定决策的冲突与事实记录 (不自改决策)

### 8.1 D002 tag 命名冲突

D002 钉 `ana-2.3.0`; 实测 docker.io 无此 tag, 纯数字 `2.3.0` 与 GitHub release ana-2.3.0 同日同版本 (2.3 节). 改拉 2.3.0 系父会话明示的同版本命名纠正. 账本修正归属父会话/用户.

### 8.2 D026 指标绑定假设 — 按实测收窄

- 数据事实 [实测]: cc.json 2.1 里 level 在 `lenses.dependency.nodes`, 不在 metrics lens.
- URL 行为 [实测]: 显式请求 `height=level` 被前端静默改写为 `height=complexity`; 加载后页面无 level 候选痕迹; 默认拼 `height=complexity&area=rloc&color=complexity`.
- 未做: 指标选择器为自定义组件, 其完整候选清单未枚举. 故不写 "永远无法绑定" 的绝对断言; 就本探针证据而言: 按 D026 现方案 (URL 参数绑定 level) 实测不可行; 若实施要 "高度=层号", 需在 build 后处理把 level 拷进 metrics lens, 或以官方依赖视图为主界面 — 归实施节点/用户裁决, 本节点未实施未重算.
- 依赖视图 (#/dependencies) 自带层化与边过滤, "EDGES SHOWN" 默认即环与向上依赖 — D025 说的前端能力存在 [实测].

### 8.3 镜像 tag 与 CLI 版本串不一致 [实测, 原因未查明]

tag 2.3.0 vs ccsh --version "2.2.1". 未做源码核实, 不推断原因. 版本核对以 digest 为准 (D030).

## 9. 缺口与未验证清单

1. 未解析 import/名字解析率: 工具无定义无输出, 门禁该项 [未验证], 交用户裁决 (6.5). 附带机制缺口: 零声明文件整体离开依赖树, 分母口径需在实施时明示.
2. 蓝色 cyclic 边像素未逐层展开验证 (红色向上边已证渲染).
3. 官方管道合并失败根因未深挖 (有完整错误摘录与外置原件), 已给官方 merge 替代.
4. 指标选择器自定义组件的下拉候选未穷尽枚举 (height=level 补查的剩余小缺口).
5. 大库观感/帧率: headless 截图正常, 人工交互流畅度未测 (F010 仍开放).
6. cc.json 落点: 原始产物在 /tmp/m23-out/ (临时), 目标库 .codebase-map/cc.json 最终写入归后续实施, 本节点未写.
7. 汉化 (m21): 不在本探针范围, 前端为官方英文原版.

## 10. 证据清单

仓库内 (本目录):

- 报告: PROBE.md (本文件)
- 截图 (work/, 已去重): smoke-sample1.png (管线冒烟), shot-cz-sdk-master-map.png (真实数据 3D), shot-cz-sdk-master-depview.png (依赖视图含红边), shot-cz-sdk-master-edge.png (选中态), deps/edge 两对重复图已删 (哈希核对过)
- 一次性脚本 (work/): run-analysis.sh (实际成功配方, 入库前自动剔进度条), stats.py, shot.py, shot-deps.py, shot-pixel.py, shot-edge.py, height-level-check.py
- 日志 (logs/): host-facts, podman-pull, dockerhub-diagnose, dockerhub-tag23, github-releases, ccsh-version, ccsh-help, ccsh-dependencyparser-help, dependencyparser-docs/tree (官方文档取证), name-resolution-java, DependencyParser.kt-head, analysis-Dockerfile, target-recheck, uid-map-verify, run-a-deps.trimmed / run-b-merged.trimmed / run-b2-merge.trimmed (裁剪摘录, 头部注明), stats-deps-only, stats-merged-check, stats-file-composition, file-filter-diff, test-rule-source, unresolved-source-check, single-file-test, serve-smoke/serve2, smoke-sample1-console, console-cz-sdk-master/-deps (页面文本摘录已脱私有文件名), pixel-cz-sdk-deps/-edge (同样脱敏), height-level-check, evidence-hashes
- 注: 三份超大原始 run 日志 (进度条流含全部私有文件名枚举) 已移出仓库, 见下.

仓库外 (原始证据, 不入 git):

- /tmp/m23-out/: deps-only.cc.json (5027105B, sha256 0f7f33050d48a001aa544f7a18f538f06d1f764ce9f121711da2378f182beecb), merged.cc.json (7458943B, b586dd2501cfb925b2ab45d7cdfdc6fdb5cfd1bf64016a0755a497dbeeb33c43), metrics.cc.json (2846674B, cfd9def649121830f0a2260dd0b85bf7ba7df270b518f3ee07b389f1378cc9dd), full.cc.json (= deps-only, 管道失败产物)
- /tmp/m23-evidence/raw-logs/: run-a-deps.log (sha256 3b8dab2e0ca99b1f8d1ebf32b4f318aeba37cac5037eaa22c8437a8ab1acef15), run-b-merged.log (e1d7bcc947946ff0df8ea570da593548c1c87a40aa07e9dc98043b8414392dc7), run-b2-merge.log (db0a083e8964811194905fbc44678514bf471f0a214d29a926e54615fa0d4c7f) — 含失败证据, 未删除
- /tmp/m23-evidence/frontend/vis-2.9.1/: web.zip (sha256 18b6377f9f482c3e34dd9a3ab8a716d6a7171ad68fa2d6670a516761b0be3682) + unpacked/ + serve/ (含 height-level 补查截图 shot-height-level-request.png) — 上游资产与官方 sample, 按 D016 不入仓库
- 以上哈希登记: logs/evidence-hashes.log

## 11. 对父会话的交接摘要

分析链路端到端跑通, 产出非零多层 (边 8820, 文件 level 8 种), 前端原版可渲染真实数据; "未解析 import" 门禁项因工具无口径记未验证, 上线判断交用户. 实施节点需要的差异事实: 镜像 tag 用 2.3.0; rootless 需 --userns=keep-id (uid_map 实证); 指标合并走 unifiedparser 出文件 + ccsh merge; level 不在 metrics lens, URL 绑 level 实测被静默改写, D026 需按 8.2 收窄或改设计; 零声明文件会离开依赖树, 分母要在交付文案里说清; ccsh --version 与 tag 不一致原因未查明, 核对以 digest 为准.
