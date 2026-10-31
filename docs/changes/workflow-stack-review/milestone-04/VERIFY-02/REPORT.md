# milestone-04 独立产品核验报告 - VERIFY-02

## 结论范围

本报告是独立产品核验的证据汇总, 不是正式验收结论. 必验项共 26 项: 通过 22, 失败 1, 未验证 3. 有失败/未验证项, 整体不得报通过. 正式验收仍由仓库主人逐项确认.

## 版本前提与判据

- 目标源提交: `2166d757e5954c39d128d4876ef1f2d0e825b051`, 完整号.
- 调用方指定目标源分支: `refactor-skill-around-verification`; 当前证据提交分支: `verify/m04`.
- 工作目录: `/home/bolo/Workspace/refactor-skill-around-verification.worktrees/verify-m04`.
- 首轮开始时工作区是目标提交的干净检出. VERIFY-01 阻塞记录随后单独提交在 `8bb4134b0d83bb1b1030bb22f76a6e6e877ac831`; 该提交的父提交精确为目标提交, 唯一差异是新增 `VERIFY-01/REPORT.md`. 本轮没有切换版本, 没有用归档快照或其他工作区替代成品, 直接在当前检出上重验文件和运行入口.
- 本轮直接读取的 PRODUCT SHA-256: `2c4f43e644f83a4a516ceec8d0d83776abe42aca937cb5d4cbf217cf9fa9f09e`, 与目标提交一致. 产品源文件、测试、配置与目标提交一致.
- 初始主工作区 `/home/bolo/Workspace/refactor-skill-around-verification` 当时有调用方说明的并行未提交/未跟踪文件, 不作为核验对象. 选择独立检出是为了不混入那些无关改动.
- 唯一产品判据: `docs/changes/workflow-stack-review/milestone-04/PRODUCT.md`, 标记 `<!-- confirmed-flow: v1 -->`. 必验清单为 AC-001..AC-022 加标记 `(审计)` 的 BR-001..BR-004, 共 26 项. BR-005/BR-006 不另加项, 其对应要求已分别列入 AC-011/AC-010.
- `EXECUTION.md`, `TECHNICAL.md`, issues、README 和 pytest.ini 仅用于定位入口/理解操作, 不增加产品判据. 不核验模块设计, 不检查安装后模型行为.

## 两轮关系与证据边界

- `VERIFY-01/REPORT.md` 保留原样, 仅记录当时因缺测试写入授权而停止, 不作为本轮产品观察.
- VERIFY-02 是获得后续授权后新开的核验轮次, 不追认 VERIFY-01. 作者侧 `/tmp/m9-04-*` 材料、issues 内作者证据均未用于本轮判定.
- 静态组最初曾在 `/tmp/m9-04-verify/static/source/` 的副本上检查. 该批结果不作为本报告结论. 同一新验收会话随后在本轮真实检出根目录直接重跑所有分配项, 有逐文件时间/退出码/原始输出, 见 `static/live/RESULT.md` 与其原始材料.
- 所有本轮原始运行材料保留在容器 `/tmp/m9-04-verify/`. 产品入口生成的图、日志和临时服务材料均未塞入产品目录. 主要证据索引见下文和相应组报告.

## 分组、人数与选型

三组按检查方式和资源划分, 共派 3 名本轮新开的非作者验收者. 三组各自承担完整范围, 并行有实际收益: 静态文本/搜索/文档检查可与 CLI 检查并行; pytest 与展示页都争用本地服务/端口, 因而按顺序执行, 不并发争用. 有读图能力的视觉模型专门承接 AC-006/BR-002. 旧实现/修复会话和已有旧会话均未复用.

选型依 `general/llm-select/SKILL.md`, `score.py` 与 review 画像. 三名验收者使用 `cli/gpt-6.1-sol`, thinking `high`: 当前 `pi/models.json` 确认此模型接受图像输入且支持 high; 评分表 review 画像 0.993, vision 1.170, general 0.943. 视觉判读需要图像能力, 失败代价是误报/漏报已确认标准, 因此选高质量档, 没有选择价格最低但图像能力不足或未评分的候选. 每个验收者均点名读取仓库内 `workflow/verification-contract/SKILL.md` 并遵守共同安全底线; 判据仍只来自 PRODUCT.

| 组 | 范围 | 子会话 | 创建时间 UTC | 未参与事实/承接标准 | 执行与原件 |
| --- | --- | --- | --- | --- | --- |
| 静态/文档 | AC-001, AC-004, AC-007..AC-014, AC-016, AC-017, AC-018..AC-022, BR-003, BR-004 | `01a19288-8686-74fc-81a2-36f4da57b245` | `2026-10-31T15:16:23.303Z` | 新建 pi session, 目标提交之后创建; 会话头与首条任务记录无作者上下文; 未参与实现/修复. 最初快照结果作废后, 由同一新会话在当前检出根直接重验 | `/tmp/m9-04-verify/static/live/RESULT.md` 及同目录 `.stdout/.stderr/.meta.json` |
| CLI/回归 | AC-002, AC-003, AC-005, AC-015, BR-001 | `01a19288-86a2-750b-82c1-d0630a308d06` | `2026-10-31T15:16:23.330Z` | 新建 pi session, 首条任务即本轮核验; 目标提交之后创建; 未参与实现/修复 | `/tmp/m9-04-verify/runtime/m04-verify-authorize-2_01a19288-86a2-750b-82c1-d0630a308d06/RESULT.md`, `cli-evaluation.json`, 原始 CLI 流和 `/tmp/m9-04-verify/runtime/pytest-run/` |
| 网页/读图 | AC-006, BR-002 | `01a19288-8686-7104-a34a-793d1e357e7d` | `2026-10-31T15:16:23.312Z` | 新建 pi session, 首条任务即本轮核验; 目标提交之后创建; 未参与实现/修复. 当前模型具备图像输入 | `/tmp/m9-04-verify/visual/RESULT.md`, `AC-006-demo-poc.png`, 细节图/双帧及原始日志 |

三名会话均在目标提交时间 `2026-10-31T05:15:41Z` 之后新建, 首条用户任务是本轮验收任务, 未继承作者或修复对话. 会话创建与首条任务证据见各组原件. 任务与资源执行顺序为: CLI、静态文本初查并行; pytest 在默认服务 `alive:false` 后尝试运行, 越界删除一发生即停止; 随后网页组串行完成 render_checks 和页面截图/读图; 静态组再于当前检出根直接完成有效重验. 没有共享作者观察作为通过依据.

## 逐项核验结果

材料类型说明: “当前观察”是本轮验收者直接读取的成品/命令输出/截图; 静态文本和全仓搜索在类型后注明“静态核对”. “未运行”表示该场景没有取得可判定的完整运行结果. 所有结论只对目标提交与本轮环境成立.

| 编号 | 判据摘要 | 结果 | 材料类型 | 本轮事实与可复核位置 |
| --- | --- | --- | --- | --- |
| AC-001 | demo skill 目录与命名 | 通过 | 当前观察, 静态核对 | 目录含 SKILL.md/LOGIC.md/UI.md, frontmatter `name: demo`, 用途为制作演示材料, `workflow/prototype` 不存在. `static/live/04-direct-texts.stdout`, `00-context.stdout` |
| AC-002 | roadmap 接受 demo 类型 | 通过 | 当前观察, CLI 实跑 | save 退出 0, query 得到 `demo`. `runtime/.../AC-002-save.stdout.json`, `AC-002-query.stdout.json` |
| AC-003 | roadmap 拒绝 prototype 且文件不变 | 通过 | 当前观察, CLI 实跑 | save 退出 1 并报非法 type, 清单精确为六个合法值; 同一夹具前后 SHA-256 相同, `cmp` 退出 0, query 仍为 demo. `runtime/.../AC-003-*`, `AC-003-before.bytes`, `AC-003-after.bytes` |
| AC-004 | demo 文档落位与子形态判定 | 通过 | 当前观察, 静态核对 | A/B/C 判定顺序、文件前缀/路由/目录/分支位置逐条对照符合标准. `static/live/04-direct-texts.stdout` |
| AC-005 | roadmap 接受 poc 类型 | 通过 | 当前观察, CLI 实跑 | save 退出 0, query 得到 `poc`. `runtime/.../AC-005-*` |
| AC-006 | 网页图例与 demo/poc 外观可区分 | 通过 | 当前观察, 服务实跑与读图 | 页面确有 `演示 demo`/`实验 PoC`; demo 有环绕卫星, 棕红裂隙纹; poc 为青绿圆坑纹/双圈, 一眼可分. 主截图 `/tmp/m9-04-verify/visual/AC-006-demo-poc.png`, 细节图/双帧见同目录, 完整记录见 `visual/RESULT.md` |
| AC-007 | poc 为 AFK 并有完成标准 | 通过 | 当前观察, 静态核对 | 明确代理独立驱动、主人无需在场, 完成标准及结论/依据收口. `static/live/04-direct-texts.stdout` |
| AC-008 | demo 可用于演示现成成品 | 通过 | 当前观察, 静态核对 | demo 覆盖需要看清样子/行为/过程, 成品或线上系统演示也归 demo, 不新增交付承诺. 同上 |
| AC-009 | demo 完成标准与关闭摘要 | 通过 | 当前观察, 静态核对 | 写主人看过能判断; 成品演示摘要写内容/版本, 产物可空; 无强制 demos 留档或另补说明文件. 同上 |
| AC-010 | 演示材料/变体分支由主人点名清理 | 失败 | 当前观察, 静态核对 | SKILL.md/LOGIC.md 明确材料可留, 但未明确变体分支本体; UI.md 将点名清理限制在 C, A/B 分支未同样明确. 直接对照 PRODUCT:123-124. `static/live/04-direct-texts.stdout`, `10-cleanup-direct.stdout` |
| AC-011 | poc 流程语并指向共享词条 | 通过 | 当前观察, 静态核对 | 四部分流程及共享 PoC 词条指针存在, 未抄写完整交付定义. `static/live/04-direct-texts.stdout` |
| AC-012 | research 只等待工作目录外事实 | 通过 | 当前观察, 静态核对 | 原实验半句不在, 创建条件为工作目录外事实. 同上 |
| AC-013 | task 承接描述现状的实测结论 | 通过 | 当前观察, 静态核对 | 有现状实测说明及压测/性能基线例子. 同上 |
| AC-014 | ADR 记录 demo 改名与 poc 新增 | 通过 | 当前观察, 静态核对 | ADR 说明旧名处置边界和不做读取兼容. 同上 |
| AC-015 | navigate 测试全绿 | 未验证 | 未运行, 启动后越界中止 | pytest 进程在测试结果出现前因超范围删除被终止, 无 pytest 汇总/退出 0, 不能判产品失败或通过. 详见“写入/删除/端口与越界风险”及 `runtime/pytest-run/RESULT.md` |
| AC-016 | README/模板/navigate 类型术语同步 | 通过 | 当前观察, 静态核对 | README 链接/用途、合法枚举、deliberate 句子逐项符合. `static/live/04-direct-texts.stdout` |
| AC-017 | 两份改过的 skill 通过硬约束检查 | 通过 | 当前观察, 命令实跑 | 从当前检出根重跑两命令, 均退出 0 且输出 OK. `static/live/01-demo-check.*`, `02-navigate-check.*` |
| AC-018 | demo skill 不用于演示成品且正文无 PoC | 通过 | 当前观察, 静态核对与搜索 | 明确直接跑成品; 对当前文件大小写不敏感搜索无 PoC 命中. `static/live/04-direct-texts.stdout`, `09-demo-poc-absence.*` |
| AC-019 | demo 通用规则 1/5/6 | 通过 | 当前观察, 静态核对 | 不进产品/不承诺/可留, 捕获信息完整, 验证止于能演示. `static/live/04-direct-texts.stdout` |
| AC-020 | poc 拆分判据及产品代码归 task | 通过 | 当前观察, 静态核对 | 按独立结论拆、跨会话不拆、规模只作经验、产品代码归 task. 同上 |
| AC-021 | poc 终止处置 | 通过 | 当前观察, 静态核对 | 未证实保持未完成, 主人裁决才关闭, 指定摘要/移除验收依赖/不记歧路. 同上 |
| AC-022 | research 就地查与领域/影响面指派 | 通过 | 当前观察, 静态核对 | 内部事实就地查, blast-radius/domain-awareness 指派, 不合适时说明里程碑划错. 同上 |
| BR-001 (审计) | roadmap 六值枚举、其他值拒绝 | 通过 | 当前观察, CLI 实跑与静态核对 | 六合法值逐项接受, 九种非法值逐项拒绝并报完整合法清单, 拒绝前后文件不变. `runtime/.../BR-001-*`, `10-enum-source-audit.stdout` |
| BR-002 (审计) | 网页 demo/poc 独立元数据/图例/外观 | 通过 | 当前观察, 浏览器实跑与读图 | meta 独立, 标签/颜色 `#e8955c`/`#63c9a3`, 地貌 `cracks`/`craters`, 实际图像不同. `visual/RESULT.md`, `browser-v3/served-index.html`, `readout.json`, 主截图 |
| BR-003 (审计) | 活跃内容无残留 prototype 约定 | 未验证 | 当前观察, 全仓搜索及静态核对 | 从当前根搜索 482 行/169 文件/2549 处, 387 行/160 文件无法严格判定是活跃约定或符合已关闭材料例外. 不把全量分类强判通过/失败. `static/live/03-prototype-all.stdout`, `05-classification.stdout`, `UNCLASSIFIED.tsv` |
| BR-004 (审计) | 不改已安装技能/全局配置, 不同步 | 未验证 | 当前观察, 静态审计; 历史材料未运行 | 核对了安装现况、只读挂载、短时指纹和 Git 差异, 但没有覆盖整个实现/修复期的记录及实现前安装基线, 不能证明期间从未同步/修改. `static/live/06-installed-before.stdout`, `13-installed-after.stdout`, `15-audit-comparison.stdout` |

## 关键真实路径结果

- `roadmap.py` CLI 三项 AC-002/003/005 以及 BR-001 已由 runtime 验收者在公开 CLI 上实跑; 夹具均为本轮新建并保留的 `/tmp` JSON, AC-003 对同一文件做字节比对, 不引用作者测试日志.
- `uv run python -m pytest workflow/navigate/tests` 的完整测试套件没有得到结果. 一次执行触发不在授权路径内的文件删除, 随即被监控器终止. AC-015 必须保持未验证.
- `render_checks` 按指定入口本轮实跑, 退出码 0, 10 项通过/0 失败. 精确自删对象、删除前留存路径、服务 pid/端口及前后状态见 `visual/RESULT.md` 和 `visual/render-checks/`.
- 展示页在隔离测试环境以真实 `web_server.py start` 加原始夹具打开. 浏览器只连 `127.0.0.1`; `0.0.0.0:39271` 是容器内进程监听, 未对外建桥或加端口映射. screenshot 的主图及双帧由有读图能力的验收者本轮实际打开判读, 不以渲染代码或图片文件存在代替.

## 写入/删除/端口与越界风险

### 核准范围内操作

- 测试夹具/原始输出/截图/脚本副本/服务日志保存于 `/tmp/m9-04-verify/`, 未覆盖旧作者材料.
- pytest 运行前设置本轮独立 basetemp `/tmp/pytest-m04-verify`, 并确认原本不存在, 避免触碰既有 `/tmp/pytest-*`; 通过 `PYTHONDONTWRITEBYTECODE=1` 与 `-p no:cacheprovider` 避免仓库 pyc/cache 写入. 这次 pytest 在调用进一步测试之前被停止, basetemp 未形成.
- render_checks 外层临时根 `/tmp/navigate-visual-vfy02-01a19288-round3` 创建并保留. 脚本创建的内层 `/tmp/navigate-visual-vfy02-01a19288-round3/navigate-visual-m5_tdstz` 是唯一由其 `shutil.rmtree` 删除的对象. 在删除前, 夹具 small/chain/big 与 runtime/server.log 已复制到 `/tmp/m9-04-verify/visual/render-checks/before-delete/`; `server.json` 在 stop 清理前也有副本. 原始删除事件/路径不存在性见 `render-filesystem-events.jsonl`, `python-audit.jsonl`.
- 本轮视觉服务操作按序使用容器内 `0.0.0.0:39271`, 每次启动前 status 均 `alive:false`, 浏览器端只访问 `127.0.0.1`; 每轮停止后 status 为 false, `ss` 确认无监听. 完整命令/退出码/时间/ pid/端口见 `visual/render-checks/*.command.json`, stdout/stderr 和服务/文件审计见 `visual/render-checks/`.
- 初始发现端口有由主工作区启动的服务, `web_server.py stop` 因脚本绝对路径与旧进程 argv 不一致而拒停. 两次均先核对 PID/CWD/命令行确认是本仓库展示服务, 再在获准“停止该展示服务”范围内仅对精确 PID 发 SIGTERM, status 随后 `alive:false`; 未使用广域 kill. PID/命令/时间为 85094 (15:15:10Z) 和 106316 (16:59:21Z), 详见本会话命令记录. 此项透明记录为跨工作区环境影响.

### 未授权删除事件

pytest 被执行到正常测试前, 本轮透明 Python 审计在 `2026-10-31T17:08:09.879125+00:00` 记录到 `os.unlink('/tmp/li0fh15u')`, 并在 `17:08:09.879214+00:00` 记录该删除成功. 该路径不在批准的 `/tmp/pytest-*`/`tmp_path` 范围. 检测器约 7.6ms 后于 `17:08:09.886707Z` 终止本轮进程, pytest returncode `-9`; 其余无 bind/服务启动事件. 原始材料: `runtime/audit/events.jsonl`, `runtime/pytest-run/scope-violations.json`, `pytest-run/pytest.meta.json`, `pytest-run/RESULT.md`.

无法确认 `/tmp/li0fh15u` 在本轮前是否存在或归属谁. 没有重建/恢复该对象, 没有继续重跑, 没有清理任何其他路径. 这属于核验执行越权副作用, 不是产品失败, 也不把被终止测试算成通过. 因授权边界未覆盖该路径, 本报告如实记为权限/环境缺口和风险.

### 邮箱身份工具的额外写入

授权2阶段, 为准备独立子会话间的通知, 静态组验收者调用了 mailbox `ensure-session`. 该工具即使返回 `created:false`, 仍重写了 `/home/bolo/.agents/mailbox/sessions/01a19288-8686-74fc-81a2-36f4da57b245/config.json`; 文件 mtime/ctime 为 `2026-10-31T15:20:40.486627065Z`. 过程证据见 `/tmp/m9-04-verify/static/19-mailbox-write-source.stdout` 和静态组旧轮记录. 未读取/输出其中凭据, 未回滚或再次写入. 这不是产品材料或已安装 skill 修改, 但属于验收通信准备产生的额外文件写入; 不将其隐去, 也不计作产品判据结果.

## 三类去向

- 明确实现问题: 1 项, AC-010. 当前文档没有在三个指定文件中逐项明确变体分支本体的保留/点名清理边界, 与 PRODUCT 的字面覆盖要求不符. 交回实现流程处理; 本轮不修文档.
- 尚缺产品规则: 1 项, BR-003. 当前搜索里大量旧词命中不能仅凭文件位置确定为活跃约定或已关闭的一手材料. 需要仓库主人明确范围; 在此之前保持未验证, 不扩大或缩小 PRODUCT 的范围.
- 权限或环境/历史证据缺口: 2 项, AC-015 与 BR-004. AC-015 被授权外删除事件触发安全终止, 无完整测试结果; BR-004 缺少实现期执行历史和实现前安装基线. 两项均为未验证, 不记产品实现失败.
- 额外安全风险: `/tmp/li0fh15u` 的越界删除如上, 已记录, 未恢复. 这是验收执行过程的事故, 不计入 26 条产品判据的失败数.

## 收尾与边界

网页组最后一次服务 `stop` 于 `2026-10-31T17:27:56.312304Z` 至 `17:27:56.426607Z` 成功, 随后 status 为 `alive:false`. 报告整理后于 `2026-10-31T17:43:12.261964281Z` 再查 `uv run python workflow/navigate/scripts/web_server.py status`, 原始输出 `{"success": true, "command": "status", "alive": false}`; `ss -ltnp 'sport = :39271'` 无监听. 当前无活动展示服务. 原始服务数据按授权保留. 当前 Git 工作区除本次证据目录的新增报告外, 没有其他未提交改动.

除本次证据目录的输出外, 产品源码与 Spec 未变. 本报告不修改产品/规格, 不改 `~/.agents` 下真实安装技能, 不运行 `sync-to-pi.py`, 不 push/merge. 邮箱会话配置写入作为核验工具副作用已在上文单列.

仍需仓库主人逐项确认和正式人工验收.
