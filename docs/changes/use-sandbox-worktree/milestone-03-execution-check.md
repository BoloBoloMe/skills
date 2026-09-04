# MILESTONE-03 执行规约审查

审查对象:
- `docs/changes/use-sandbox-worktree/EXECUTION.md`
- `docs/changes/use-sandbox-worktree/issues/ISSUE-01-fixture-mother-config.md`
- `docs/changes/use-sandbox-worktree/issues/ISSUE-02-daemon-write-surface.md`
- `docs/changes/use-sandbox-worktree/issues/ISSUE-03-container-birth-read-face.md`
- `docs/changes/use-sandbox-worktree/issues/ISSUE-04-push-landing.md`
- `docs/changes/use-sandbox-worktree/issues/ISSUE-05-teardown-rerun-artifacts.md`
- 附带复核: `PRODUCT.md`, `TECHNICAL.md`

基准:
- `DECISIONS.md`
- `roadmap/MILESTONE-03.md`
- `milestone-02-worktree-topology-findings.md`
- `milestone-02-scripting-opposing-review.md`
- `workflow/use-worktree/SKILL.md` 及 `scripts/slug.py`, `scripts/status.py`
- `/home/bolo/.agents/skills/to-execution/SKILL.md`
- `pytest.ini` 及现有 `tests/` 布局

结论: **不通过**. ID 覆盖表面完整, 但执行路径存在会使规约无法按当前约束完成的错误. 本报告只写入本审查产物, 未修改被审对象.

证据等级:
- A: 被审文档与权威文档的直接矛盾或直接缺失.
- B: 权威实测事实直接支持的可执行性问题.
- C: 基于接口未定义或测试布局的高概率风险, 需要在规约中补契约.

## 已核对通过

1. `EXECUTION.md` 任务图中的 5 个 issue 路径真实存在, 编号连续.
2. `AC-001..006`, `TG-001..004`, `NFR-001..002`, `NB-001..004` 均进入覆盖矩阵.
3. `TC-001..007` 均有覆盖, 且矩阵中各 TC 只有一个声称 issue: TC-001/002 -> ISSUE-01, TC-003 -> ISSUE-03, TC-004/006 -> ISSUE-04, TC-005 -> ISSUE-02, TC-007 -> ISSUE-05.
4. issue 中列出的 D/F ID 在 `DECISIONS.md` 中存在. D008/F007 的 config, hideRefs, ff-only, `clone -b`, `HEAD` 行为引用方向基本相符. `ISSUE-05` 对 D012 的解释除下述冲突外, ID 本身存在.
5. blockers 图 `ISSUE-01 -> ISSUE-02 -> ISSUE-03 -> ISSUE-04 -> ISSUE-05` 无环. 但其线性结构违反下述垂直切片要求.

## 错误

### E-01 issue 是水平分层, 不满足垂直切片纪律

位置:
- `EXECUTION.md:35,39-43`
- `ISSUE-01:13,31,74-76`
- `ISSUE-02:9,28,69-74`
- `ISSUE-03:9,78-80`
- `ISSUE-04:9,73-75`
- `ISSUE-05:9,67-76`

理由:
`to-execution/SKILL.md:20-27,43` 要求每个 issue 都是可独立演示或验证的窄而完整端到端路径, 只有无法保持边界和验证时才允许预重构 issue. 当前拆分是同一个脚本按实现层次切开:

- ISSUE-01 只做母体和 config, 明确禁止 daemon/container.
- ISSUE-02 再补 daemon 和 host 侧写面矩阵, 明确禁止容器.
- ISSUE-03 再补容器 birth/读面.
- ISSUE-04 再补 smoke 回流.
- ISSUE-05 才补 cleanup/重跑.

因此 ISSUE-01 到 ISSUE-04 单独完成时都不能演示 M03 的任何完整闭环, 也不能在真实边界上独立验证其声称的最终行为. 这不是必要的共享 API 宽重构, 而是把单个 E2E 流程按层分期, 与 `to-execution` 明确要求的 tracer bullet 相反. 现有 blockers 只是让这种水平拆分可串行实现, 不能使其变成垂直切片.

证据等级: A.

### E-02 TC-002 没有可行的故障注入路径

位置:
- `PRODUCT.md:54-59`
- `TECHNICAL.md:58-59,96-104`
- `ISSUE-01:13,48-54`

理由:
TC-002 要求“主仓配置被故意写错一个键”, 然后执行同一个 `birth`, 期待配置校验失败且 daemon 未拉起. 但 birth 流程明确是先建母体, 再写入 D008 config, 再逐键校验 (`TECHNICAL.md:58-59`). 若脚本在校验前无条件写 D008, 测试预置的错误值会被覆盖, 测不到失败分支; 若脚本保留错误值并拒绝覆盖, 又没有任何 CLI 参数或 fixture 接口定义该行为.

`ISSUE-01:51-52` 只描述预置错误和校验, 未定义如何阻止 config 写入覆盖错误值, 也未定义 fault injection 开关. `TECHNICAL.md:27-29` 的公开 CLI 没有测试模式或故障注入参数. 因此执行 agent 无法同时满足“birth 写 config”和“预置错误后 birth 必须失败”.

建议至少在执行规约中明确: 错误配置是由测试夹具在 birth 的哪个阶段注入, 或增加仅测试用的受控注入入口, 并明确 daemon 启动前的检查对象.

证据等级: A.

### E-03 TC-005 的测试主体不是容器, 无法覆盖 AC-003

位置:
- `PRODUCT.md:74-85`
- `TECHNICAL.md:123-131`
- `ISSUE-02:9,37-43`
- `EXECUTION.md:40,49`

理由:
AC-003 明确要求“容器内 agent”执行新分支、新 tag、non-ff 强推和删除分支, 并将其作为容器写面约束. 但 ISSUE-02 明确把实现写成“host 侧客户端经 daemon URL clone -b ...”, 其 TS-001 也是“birth 后经 daemon URL执行四类越界 push”. 这只验证服务端 receive config 对某个 host 客户端的行为, 没有验证容器的 git 通道, 容器内 remote, 容器到 daemon 的网络路径或容器主体上的越界操作.

ISSUE-03 只覆盖容器 clone/read face, 没有承接 TC-005. 所以矩阵虽把 AC-003/TC-005 指向 ISSUE-02, 实际验证主体与产品验收主体不一致, 且 AC-003 的 BR-001 隔离语义没有被这条测试覆盖.

证据等级: A.

### E-04 daemon loopback 与容器访问路径互相冲突

位置:
- `TECHNICAL.md:16,59,76`
- `ISSUE-02:9,71`
- `ISSUE-03:9,32,60,68`
- 权威实测: `docs/changes/use-sandbox-worktree/2026-09-01-research.md:170-171`

理由:
规约固定 daemon 为 `--listen=127.0.0.1`, 同时要求容器内执行 clone. 权威实测明确记录: rootless Podman 容器通过 pasta 网关访问 host 服务可达, 但 host 的 `127.0.0.1` 监听服务容器到不了, 必须全地址监听. 因此 ISSUE-03:60 所说“容器经 `host.containers.internal` 或网关地址访问 host loopback”不是已成立的接口: 改用网关地址仍无法连接只绑定 loopback 的 daemon.

规约还说如果需要非 loopback 监听, 只记录事实并“不得擅自改决策”. 但 D008/`TECHNICAL.md:76` 已把 loopback 作为安全约束, 容器 clone 又是 birth 的硬步骤. 这不是可由执行 agent 自行选择的实现细节, 而是必须先解决的决策冲突: 要么定义一个已验证的 host-side forwarding/namespace 方案, 要么重新确认最小监听范围与安全边界. 当前文本无法完成 AC-001/AC-004 的容器 clone.

证据等级: B.

### E-05 无 `--export-all` 时遗漏 daemon 导出标记

位置:
- `TECHNICAL.md:16,59,75`
- `ISSUE-02:9,28,71`
- `ISSUE-03:9,32`
- 权威实测: `milestone-02-worktree-topology-findings.md:17-28`
- 权威实测总结: `2026-09-01-research.md:100,186`

理由:
D008/F003 要求不使用 `--export-all`, 且 daemon base-path 只服务主仓. 在权威拓扑实测中,启动 daemon 前显式执行了 `touch main/.git/git-daemon-export-ok` (`findings:25`), 并且研究结论明确写出生产方案需要目录白名单加显式 `export-ok` (`research:100,186`).

当前 birth 流程只描述建 fixture/worktree, 写 config, 启 daemon, 没有创建或验证 `.git/git-daemon-export-ok`. 在不带 `--export-all` 的前提下, 新建 fixture 很可能不会被 git daemon 导出, 随后的 clone 会失败. `base-path` 仅含主仓的审计也没有替代 export marker 的创建. 这是完成 birth 所需的遗漏步骤, 不是可选 checklist.

证据等级: B.

### E-06 cleanup 后 birth 的重复探测规则与母体复用规则矛盾

位置:
- `TECHNICAL.md:33-34,70-71`
- `TECHNICAL.md:141-149`
- `ISSUE-05:9,38-42,51-57,69-72`
- `DECISIONS.md:85-90`

理由:
`TECHNICAL.md:70` 规定 birth 前发现同名母体/ref 就“中止并提示先 cleanup, 不自动强拆”. `TC-007` 又要求 cleanup 后母体和 ref 留存, 随后再次 birth 成功. ISSUE-05:57 改为发现既有母体且干净时“复用而非报错”, 并称其符合 D010.

这两个 birth 状态转移规则互相冲突: cleanup 按 BR-003 保留母体和 ref 时, 第二次 birth 必然命中前一规则; 要满足 TC-007 必须引入 D010 的复用状态机, 但 `TECHNICAL.md` 没有定义复用时如何重新校验 config, 重建 daemon, 重建容器, 更新运行时 JSON, 以及如何区分 stale JSON/同名但不同母体. `TECHNICAL.md:33` 还规定 JSON 是 smoke/cleanup 的唯一状态载体, 未说明 cleanup 后 JSON 是否删除或标记, 这会进一步影响第二次 birth.

证据等级: A.

### E-07 cleanup 明确违背当前有效的 D012

位置:
- `ISSUE-05:16-18,26-28`
- `TECHNICAL.md:63,141-149`
- 权威决策: `DECISIONS.md:99-103`

理由:
D012 当前有效且无“延期到 M11/12”的状态标记. 它要求终结前通过 ssh 检查容器内未 commit 改动和未 push commit, dirty 时阻塞, 只有用户明示才强拆. ISSUE-05 在相关决策中却写成“终结脏检查属 M11/12”, 并在禁止范围明确“不实现脏检查交互”. `TECHNICAL.md:63` 也把 cleanup 固定为 `podman rm -f` 后 kill daemon.

M03 可以选择不实现完整用户交互, 但这需要明确的决策变更或把本阶段标成受限实验清理, 同时不能把 D012 作为支持该行为的相关决策. 当前规约既宣称 cleanup 的端到端完成, 又在 cleanup 中直接删除可能含未 push 工作的容器, 与权威安全语义矛盾. 另外 ISSUE-04:46 的 dirty-tree 测试恢复母体文件, 但没有恢复容器中已创建而未 push 的 commit, 这使 D012 的保护缺口在实际链路中可复现.

证据等级: A.

## 存疑

### S-01 slug.py 的实际调用协议未固化

位置:
- `TECHNICAL.md:15,53`
- `ISSUE-01:13,33-37`
- `TECHNICAL.md:27-29`
- `workflow/use-worktree/scripts/slug.py:18-24,74-95`

事实:
`slug.py` 不是输出一个裸 slug 的通用命令. 它支持 `slug.py <branch>` 或 `slug.py <project> <source-branch> <target-branch>`, 输出多行 `key=value`; 一参数模式的目标字段是 `slug=...`. 当前公开 CLI 却只有 `--name <slug>`, 没有说明 `<name>` 是原始 branch 还是已生成 slug, 没有说明调用哪一种 positional 形式, 也没有说明解析 `slug=` 还是直接使用参数.

这不一定导致实现错误, 但“注意其输入参数”不足以构成稳定执行契约. 应明确一条命令和输出字段, 并说明母体目录名与母体 branch 如何从该结果派生. `status.py` 被列入只读复用范围, 但所有 issue 没有说明它在哪个状态检查中使用, 也未定义其 nonstandard/missing-origin 输出如何处理.

证据等级: C.

### S-02 issue-05 的 roadmap 引用按 issue 文件相对路径不可解析

位置:
- `ISSUE-05:32`
- 实际文件: `docs/changes/use-sandbox-worktree/roadmap/MILESTONE-03.md`

理由:
同一 issue 的 Product/Technical 引用使用 `../PRODUCT.md` 和 `../TECHNICAL.md`, 但 checklist 来源写成 `roadmap/MILESTONE-03.md`. 若按 issue 文件位置解析, 它指向不存在的 `docs/changes/use-sandbox-worktree/issues/roadmap/MILESTONE-03.md`; 实际相对路径应为 `../roadmap/MILESTONE-03.md`, 或使用仓库根路径. 任务图自身的 issue 路径没有此问题, 但该代码定位引用不满足“引用路径按实际位置解析”的执行标准.

证据等级: A.

### S-03 pytest 验证入口没有落到仓库现有约定

位置:
- `pytest.ini:1-4`
- `tests/test_sync_to_pi.py:1-17,27-104`
- 各 issue 的验证入口, 例如 `ISSUE-01:56-58`, `ISSUE-02:52-54`

事实:
`pytest.ini` 只声明 `tests` 和 `general/present/tests` 为 testpaths, 没有定义 `swt_m03` marker, 文件名或测试发现约定. 当前 Python 测试主要采用 `unittest.TestCase`, 且仓库中没有 `swt_m03` 测试文件或测试名. 规约给出的测试名如 `test_birth_writes_mother_and_config` 也不含 `swt_m03`.

pytest 的 `-k swt_m03` 可以在执行者额外创建名为 `test_swt_m03.py` 的模块时工作, 但规约没有要求这个文件名, 也没有提供真实测试目标路径. 在全新上下文中照现有示例添加测试并运行该命令, 可能出现无匹配测试. 建议明确新增测试文件路径, 说明是 pytest 函数还是 unittest 类, 并在命令中使用具体文件或 marker.

证据等级: A.

### S-04 Containerfile 与 ssh/pi 依赖仍不足以支持 AFK 声明

位置:
- `TECHNICAL.md:12,159-161,169-176`
- `ISSUE-03:9,33,47-48,56-68`

理由:
TECHNICAL 明确说 pi 首次运行和 sshd 配置尚未实测, 依赖可能需要补齐; ISSUE-03 又称“适合 AFK”并只给出参考 `pi/` 和 `sync-to-pi.py`. 规约没有指定 Containerfile 的 build context, pi CLI 的安装/复制方式, ssh 用户, authorized key 注入方式, 容器工作目录, 或容器访问 daemon 的最终地址.

这些可以作为 M03 实验中待发现事实, 但不能同时宣称 issue 可在无待决架构问题下 AFK. 至少应把容器到 daemon 地址和 ssh/pi 最小运行契约列为明确 HITL/环境前置, 或给出已验证的命令接口.

证据等级: C.

## 建议

### R-01 重新按可演示闭环拆分 issue

把单一 `birth -> smoke -> cleanup -> birth` 作为一个可独立领取的 integration/HITL issue, 或让每个 issue 都包含一个可运行的端到端最小路径并保留已有路径. 如果共享 `e2e-smoke.py` 的增量实现确实不可避免, 应按照 `to-execution/SKILL.md:33-41` 标成 integration 特例, 写明共享分支, 每步局部证据和最终整体绿色承诺, 不把它们标作五个独立可执行代码切片.

### R-02 先闭合 birth 的服务端契约

在执行规约中明确:
- fixture 创建 `git-daemon-export-ok` 的位置和审计断言.
- daemon 的实际 bind 地址与容器访问地址, 以及不改变 D008 的可行方案.
- `--port=0` 的可靠发现命令/日志协议, 失败时是否允许固定端口.
- 容器内 remote URL 的 host 字段, 不能把 host loopback 当作容器可达地址.

### R-03 明确故障注入和状态机

为 TC-002 定义错误 config 的注入时点和入口. 为 cleanup/rebirth 定义状态表: runtime JSON 的生命周期, 母体复用条件, config 重校验, stale daemon/container 处理, 以及与 `TECHNICAL.md:70` 重复 birth 拒绝规则的优先级.

### R-04 修正 cleanup 的决策边界

在 D012 仍为当前有效时, cleanup 必须先检查未 commit/未 push 工作; 若 M03 只做实验资源回收, 应明确这是受限演练而不是完整终结语义, 不引用 D012 支撑相反行为, 并在完成定义中记录该限制及容器数据风险.

### R-05 让 AC-003 真正走容器路径

TC-005 的四类 push 应由容器内 clone 执行, 通过 ssh/podman exec 采集原生输出. Host 侧 client 可作为补充 receiver 矩阵, 但不能替代 Product 中“容器内 agent”的验收主体.

### R-06 固化测试文件与路径

建议指定 `tests/test_swt_m03.py` 或等价真实路径, 明确测试函数/类命名和环境依赖. 对需要 Podman、rootless pasta、可用基础镜像网络的测试, 写出缺环境时的跳过或失败标准, 避免 `pytest tests/ -k swt_m03` 以零测试通过或无法诊断.

## 总结

ID 和覆盖矩阵的静态完整性基本通过, 决策 ID 也大多存在且语义相符. 但规约当前不能作为可执行的 M03 交付说明: 水平分层违反垂直切片标准, birth 的网络/导出前置条件未闭合, 失败注入和重跑状态机互相冲突. 
## 复审 (2026-09-03)

范围: 重审修订后的 `TECHNICAL.md`, `EXECUTION.md`, `ISSUE-01-host-loop-tracer.md`, `ISSUE-02-container-client-loop.md`, 并对照未改的 `PRODUCT.md`, `DECISIONS.md`, `roadmap/MILESTONE-03.md` 及 M02 实测. 本节只追加审核结论, 未改被审规约.

### 原 7 项错误

| ID | 结论 | 证据 |
| --- | --- | --- |
| E-01 水平分层 | 消解 | `EXECUTION.md:64` 将 ISSUE-01 定义为可独立演示的 host 端完整闭环, ISSUE-02 在其上接入容器并完成全部 AC. `ISSUE-01-host-loop-tracer.md:13,57-77` 含 birth/smoke/cleanup/rebirth, 不是原先仅建 fixture/config 的层切分. `ISSUE-02-container-client-loop.md:13,44-78` 是容器真实客户端的完整验收闭环. 两片均有可观察结果和无环阻塞边. |
| E-02 故障注入缺失 | 消解 | `TECHNICAL.md:54` 明定预写错误 config 为注入入口, 且不覆盖错误值. `TECHNICAL.md:106-114` 和 `ISSUE-01-host-loop-tracer.md:50-56` 规定 TC-002 的退出码, stderr, 无 daemon 和错误值留存断言. 下文 C-01 是独立的多值写入缺陷. |
| E-03 TC-005 主体非容器 | 消解 | `TECHNICAL.md:133-141` 明定四类操作均在容器内执行. `ISSUE-02-container-client-loop.md:58-64` 的 TS-003 也明确禁止以 host 重验替代. |
| E-04 daemon loopback 冲突 | 消解 | `TECHNICAL.md:84` 承认 loopback 不可达, 改为 pasta 网关地址优先和 `0.0.0.0` 兜底, 并要求记录 LAN 暴露中间态. 该兜底与实测 `2026-09-01-research.md:170-173` 的"容器走 169.254.1.2, host 服务须全地址监听"一致, 且 D008 未规定必须 loopback. |
| E-05 缺 git-daemon-export-ok | 消解 | `TECHNICAL.md:16,65` 要求在 daemon 前创建 export marker, TC-001 也断言其存在 (`TECHNICAL.md:97-105`). |
| E-06 重入规则矛盾 | 消解 | `TECHNICAL.md:35-36,57-61` 定义 JSON 生命周期, 干净母体复用, 脏母体拒绝和存活资源拒绝. `TECHNICAL.md:151-159` 将 cleanup 删 JSON 后复用母体的重跑固化为 TC-007, 与 D010 一致. |
| E-07 违背 D012 | 部分消解 | 修订明确 cleanup 是仅针对 /tmp 夹具的受限实验清理并记录容器状态 (`TECHNICAL.md:70,165`), 不再把它伪称完整终结. 但仍无条件 `podman rm -f`, 而当前有效 D012 要求未 commit/未 push 工作必须阻塞直至用户明示 (`DECISIONS.md:99-103`). M03 roadmap 也要求把"脏放行"登记为 checklist 决策点 (`roadmap/MILESTONE-03.md:18`), 规约未定义该项的字段或执行前置. TC-005 的被拒 push 可留下未 push 本地提交, 之后全链 cleanup 会自动丢弃它. |

### 原 4 项存疑

| ID | 结论 | 证据 |
| --- | --- | --- |
| S-01 slug 契约 | 未消解, 升级为严重问题 | `TECHNICAL.md:15` 和 `ISSUE-01-host-loop-tracer.md:37` 规定三参数调用后解析 `slug=`. 实际 `slug.py` 的三参数分支只输出 `target_slug=` 和 `dir=` (`workflow/use-worktree/scripts/slug.py:74-84`); `slug=` 只在一参数分支输出 (`:68-72`). 规定的解析必然失败, 也未说明怎样使 branch, 目录和容器身份满足 D007 的一名贯穿. |
| S-02 相对路径 | 消解 | ISSUE-02 已从错误的 `roadmap/...` 改为 `../roadmap/MILESTONE-03.md` (`ISSUE-02-container-client-loop.md:40`), 路径存在. ISSUE parent/Product/Technical/Decisions 的 `../` 路径均可解析, 两个 ADR 也存在于仓库根 `docs/adr/`. |
| S-03 pytest 落点 | 消解 | `TECHNICAL.md:95` 和 `EXECUTION.md:28,36` 固定 `tests/test_swt_m03.py`, `unittest.TestCase` 和精确 pytest 命令. 该目录已在 `pytest.ini:2-4` 的 `testpaths` 中. |
| S-04 AFK 依据不足 | 部分消解 | ISSUE-02 已将 ssh, daemon 地址和 pi 运行列为风险/停止条件 (`ISSUE-02-container-client-loop.md:84-97`), 不再静默假定成功. 但 Containerfile 的 build context, pi CLI 的实际取得方式, ssh 用户和 key 注入协议仍未固化; 当前仓库 `pi/` 只有 extensions/config, 不是 pi CLI 分发物. 因此该 issue 可以作 HITL 实验, 但"适合 AFK"尚无充分依据. |

### 修订引入的问题

#### 严重 C-01 config 写入语义无法构造 D008 模板

位置: `TECHNICAL.md:40-54`, `milestone-02-worktree-topology-findings.md:172-177,189-196`.

D008 的 `receive.hideRefs` 和 `uploadpack.hideRefs` 都是三个值的多值键. 规约却规定"键不存在则写入, 键已存在且值不符则失败". 按该规则写入第一个 `hideRefs` 后, 写第二个同键不同值即必须失败, TC-001 无法得到模板. M02 实测明确以 `git config --add` 写入三项. 必须按标量键和多值键分别定义完整集合的比较及写入规则, 包括初始空集合时一次加入全部三值, 已有集合何时允许和何时 `ASSERT-FAIL config`.

#### 严重 C-02 公开 --repo 与仅 /tmp 夹具边界冲突

位置: `TECHNICAL.md:24-35,85`, `EXECUTION.md:18-23`, `roadmap/MILESTONE-03.md:13-18`.

CLI 把任意 `<主仓路径>`作为唯一公开接口的 `--repo`, 后续流程会创建 export marker, 写 D008 config 和 cleanup. 同一规约又禁止触碰用户真实仓库, 限定 config 只写 /tmp 夹具仓. 没有路径白名单, 夹具标识或拒绝非夹具仓的 TC, 执行者无法判断传入仓是否允许写入. 这会直接违反执行范围, 并可能把 M03 实验的常驻 receive config 写入真实仓库.

#### 警告 C-03 daemon base-path 未被收敛到唯一主仓

位置: `TECHNICAL.md:16,18,101`, `PRODUCT.md:28,49`, `DECISIONS.md:74`.

规约实际传 `--base-path=<主仓父目录>`, 但 Product 和 D008 都要求 base-path 仅含主仓. 夹具父目录还承载全部运行时产物, 并且同一流程要建立母体 worktree 和 host 客户端目录. 文本没有隔离服务根目录或断言枚举出的服务路径只有主仓, 故 TC-001 的"base-path 仅含主仓"没有可实施口径. 应固定一个仅放主仓的 daemon 根目录, 或规定并验证父目录没有任何其他可服务 Git 仓.

### 一致性和覆盖复核

- Product 的 AC-001 至 AC-006, Technical 的 TC-001 至 TC-007/TG-001 至 TG-004/NFR-001 至 NFR-002, 以及 NB-001 至 NB-004 均在 `EXECUTION.md:40-53` 有承接. TC-005 已正确落 ISSUE-02 的容器路径. 静态覆盖矩阵完整.
- 两个 issue 的任务图引用真实存在且 blocker 为 `ISSUE-01 -> ISSUE-02`, 无环. ISSUE-01 是完整 host tracer, ISSUE-02 是完整容器验收, 符合垂直切片要求, 不需要 integration 特例.
- 修订的相对引用可解析. `ISSUE-02-container-client-loop.md:40` 的 roadmap 引用已修正; `docs/adr/0007-gate-daemon-not-ssh.md` 和 `docs/adr/0008-mother-worktree-direct-receive-no-hooks.md` 存在. 
- 除 C-01/C-02/C-03 和 E-07/S-04 外, 内容与 PRODUCT, D007-D010 和 roadmap 的 M03 瘦编排器边界一致. C-01 还会阻断 roadmap 要求的"config 就绪后才拉 daemon" (`roadmap/MILESTONE-03.md:15,22`).

### 复审结论

**不通过**.

原 E-01 至 E-06 和 S-02/S-03 已消解, 网络和容器主体修订方向正确. 但三参数 slug 解析错误, 多值 config 写入不可执行, 以及 `--repo` 允许越界写真实仓仍是阻塞问题. 受限 cleanup 还必须把 D012 的脏放行作为明确的夹具前置或 checklist 决策, 才能避免其自动删除未 push 工作.

## 三审 (2026-09-03)

范围: 本轮修订后的 `TECHNICAL.md`, `PRODUCT.md`, `EXECUTION.md`, 两个 issue, 对照 `DECISIONS.md`, M03 roadmap/ROADMAP, M02 实测及 `workflow/use-worktree/scripts/slug.py`. 本节只追加审核产物, 未修改被审源码/配置.

### 已消解项

- slug 阻塞已消解. 实际执行 `uv run python workflow/use-worktree/scripts/slug.py demo main 'feature/test'` 输出 `dir=demo-main-feature-test`, 三参数分支确实没有 `slug=`; 与 `TECHNICAL.md:15`, `issues/ISSUE-01-host-loop-tracer.md:37` 一致.
- 多值 `hideRefs` 写入缺口已消解. `TECHNICAL.md:56-59` 已定义空集合按序三次 `--add`, 集合相等跳过, 不相等不覆盖并失败; 与 D008/F007 一致. 重复值边界见 W-03.
- `--repo` 越界边界已补齐. `TECHNICAL.md:34-35`, `EXECUTION.md:18-24`, `PRODUCT.md:61-66` 要求 `.git/swt-m03-fixture`, 非夹具退出码 2 且零写; TC-008 已接入 `EXECUTION.md:41,46` 和 ISSUE-01 TS-006.
- C-03 已消解. `TECHNICAL.md:16,19,71` 固定 `srv/<reponame>`/`base-path=<夹具>/srv`, TC-001 断言 srv 根只有一个 git 仓, 与 D008/F003 一致.
- E-01 至 E-06 的本轮对应项, S-02/S-03 均有当前文本承接. 两个 issue 的路径和主要 `../` 引用可解析, 测试落点固定为 `tests/test_swt_m03.py`; TC-008 也已进入覆盖矩阵. M03/M04/M11 的 roadmap 阻塞关系一致.
- E-07 原“缺脏放行登记”已补齐为产物/checklist 字段要求: `TECHNICAL.md:75`, `issues/ISSUE-02-container-client-loop.md:13,105`. 但该登记不能替代 D012 的阻塞语义, 见 W-02.
- S-04 的镜像静态字段已补齐到 `TECHNICAL.md:17`, 但 sshd/容器入口仍不完整, 见 E-02.

### 发现

#### 严重 E-01: birth 中途失败时 cleanup 无法定位资源

证据:

- `TECHNICAL.md:37` 规定 runtime JSON 记录资源, `TECHNICAL.md:71` 却把写 JSON 放在容器 clone/断言后的第 13 步.
- `TECHNICAL.md:62-66` 的重入检测只检查 JSON 和同名存活容器, 没有检查存活 daemon.
- `TECHNICAL.md:75` 的 cleanup 依赖 JSON 中的 PID/容器信息, `TECHNICAL.md:83` 对“中途失败 JSON 留存”的表述无法覆盖 JSON 尚未写入的阶段.

daemon 已在第 7 步启动, 但镜像 build、容器 start、ssh 或 clone 在第 8-12 步失败时, 第 13 步尚未执行, 因而可能留下 daemon/容器而无 JSON. 下一次 birth 看不到该 daemon, cleanup 也无确定 PID/容器名, 违反部分诞生幂等清理和 D010 单活动母体不变量. 应在每个资源创建后持久化状态, 或定义无 JSON 时基于 fixture/label/PID 的可验证发现与回收, 并测试 daemon 已起而容器未起的路径.

#### 严重 E-02: Containerfile 和 `podman create` 未定义容器存活及 sshd 启动

证据:

- `TECHNICAL.md:17` 只写“sshd 就位”, 未定义 `CMD`/`ENTRYPOINT`, sshd 配置、host key/runtime 目录或启动命令.
- `TECHNICAL.md:18,71` 的 create 命令只含 `-p 22` 和镜像, 未定义前台 sshd 或长驻进程.
- `issues/ISSUE-02-container-client-loop.md:47-50,101` 已将容器运行/BatchMode ssh 列为验收条件, 但没有补齐运行入口.

安装 `openssh-server` 本身不会使 sshd 成为容器主进程. 当前契约不能保证 `podman start` 后容器持续运行, 也不能推导 sshd 何时启动及公钥注入何时生效, 因而 S-04 尚未完全消解. 应固化入口命令、`/run/sshd`/host key 初始化、公钥注入时点和 agent 登录用户.

#### 警告 W-01: 缺省 `--repo` 的跨命令状态定位未定义

`TECHNICAL.md:28-37` 允许 birth 随机自建 `/tmp` 夹具, runtime JSON 写在未知 repo 下; 但 `issues/ISSUE-01-host-loop-tracer.md:88` 只给出 `birth --name demo` 后直接执行 smoke/cleanup. 后两命令无法仅凭 name 找到该随机 repo. 应统一要求三阶段显式传 repo, 或定义不会串用夹具的状态索引/环境传递机制.

#### 警告 W-02: 脏放行登记已补, 但无阶段性授权仍违反 D012

`DECISIONS.md:99-103` 要求未 commit/未 push 时阻塞 cleanup, 用户明示后才 rm; `TECHNICAL.md:75` 和 `issues/ISSUE-02-container-client-loop.md:13,69` 却规定只记录、不阻塞并无条件 `podman rm -f`. `EXECUTION.md:24` 还禁止实现该交互, 而 `roadmap/MILESTONE-03.md:18` 只要求登记决策点. 若 M03 要保留 `/tmp` 破坏性实验例外, 应在权威范围/决策处明确批准, 并规定 checklist 的状态值、夹具路径、时间、确认依据和放行结论; 否则“登记即可放行”与当前 D012 不一致.

#### 警告 W-03: set 比较会放过重复的 hideRefs 值

`TECHNICAL.md:58` 说不计顺序的集合相等即可跳过, 但 `TECHNICAL.md:106,115` 和 `PRODUCT.md:48` 要求逐项与模板一致. 模板三值加重复值会被当作相等并跳过, 实际 `git config --get-all` 却多出一项. 应比较多重集合/长度, 并补重复值测试.

#### 警告 W-04: TC-003 未放宽已知的 HEAD 广告

`TECHNICAL.md:124` 要求 `ls-remote` 仅含母体分支 ref, 但 F007 实测 `milestone-02-worktree-topology-findings.md:180-187,277` 明确仍有 `HEAD` 行, 且 HEAD 对应 main 对象无法隐藏. `TECHNICAL.md:81` 已承认该事实, TC-003 却未声明允许 HEAD. 应改为“除 HEAD 行外 refs 仅含母体分支”, 并断言 remote-tracking refs 只有母体分支.

#### 警告 W-05: daemon `--port=0` 的发现仍未固化为可执行协议

`TECHNICAL.md:16,71,199-201` 只要求动态端口、写 JSON、记录发现手段; `issues/ISSUE-01-host-loop-tracer.md:13,92` 只给出“端口发现”及高端口退化. 未定义 PID/socket 匹配、竞态、发现失败时的清理和固定端口占用探测, 但容器 clone 在第 12 步已必须使用该端口. 应补具体命令和失败状态测试.

### 总结

原三项表面阻塞和 C-03 已按文本补齐, slug 实际行为与新契约一致, 覆盖矩阵和主要引用可解析. 但中途失败资源不可回收, 容器启动/sshd 契约仍不足, D012 放行语义也未获明确的阶段性授权. **结论: 不通过.**


## 四审 (2026-09-03)

### 三审 2 项严重与 5 项警告

| ID | 结论 | 证据 |
| --- | --- | --- |
| E-01 birth 中途失败资源不可回收 | 基本消解, 但有状态机残留见下文 E-01 | `TECHNICAL.md:37` 改为母体/daemon/容器每创建一项即增量落盘, 并在 JSON 缺失或缺段时以容器 label 和 `pgrep` 按 srv 根兜底发现. `TECHNICAL.md:84` 也明确中途失败后由 cleanup 回收. 这覆盖了 daemon 已起、容器未创建以及末尾 JSON 尚未写入的主要窗口. 但 birth 重入检测仍只写“存在 JSON 或同名存活容器” (`TECHNICAL.md:63-67`), 没有把存活 daemon 纳入检测, 见下文. |
| E-02 容器 sshd 启动契约缺失 | 消解 | `TECHNICAL.md:17` 固化了 `ssh-keygen -A`, `/run/sshd`, `CMD ["/usr/sbin/sshd", "-D", "-e"]`, agent 用户及 start 后 `authorized_keys` 注入/0600/BatchMode 断言. `TECHNICAL.md:72` 固化注入时点, 足以定义容器长驻和登录入口. |
| W-01 缺省 `--repo` 跨命令定位 | 部分消解, 索引边界见下文 W-01 | `TECHNICAL.md:38` 增加 `/tmp/swt-m03-index.json` 的 name -> repo 索引, 并规定 birth 注册、stdout 打印、cleanup 注销. 这使缺省 repo 的基本跨命令路径可执行, 但未定义冲突/失效/并发和原子更新处理. |
| W-02 脏放行与 D012 不一致 | 未消解 | `TECHNICAL.md:76` 和 `EXECUTION.md:24` 已采用 D012 的阻塞 + `--i-am-sure` 形态, 但 `issues/ISSUE-02-container-client-loop.md:13,23` 仍明确写“不阻塞”且称 D012 用户交互归 M11/12. 这是同一交付任务内的直接冲突. 其 `:33,69` 虽写有“须阻塞或 --i-am-sure”, 不能消除前述旧语义. |
| W-03 多值键重复值放过 | 消解 | `TECHNICAL.md:59` 已要求长度 + 各值计数的多重集比较, 明确重复值不得放过, 与 D008 模板逐项校验一致. |
| W-04 TC-003 未放宽 HEAD 行 | 消解 | `TECHNICAL.md:125` 已写明除 HEAD 行外 refs 仅含母体分支, 并另断言 remote-tracking refs 仅有母体分支, 与 F007 一致. |
| W-05 daemon 端口发现协议未固化 | 消解 | `TECHNICAL.md:16,72` 固化 socket bind 0 预选、daemon 拉起后探测、失败重选至多 3 次, 并不使用 daemon 自身 `--port=0`. 这已定义 clone 前的端口可用性和失败上限. |

### 本轮新增或仍阻塞的问题

#### 严重 E-01: birth 仍可能绕过存活 daemon 的重入检测

证据:

- `DECISIONS.md:85-90` 的 D010 不变量把“有存活容器/守护进程的母体”定义为活动母体, 同一主仓不能出现两个不同活动母体.
- `TECHNICAL.md:63-67` 的 birth 状态机只检查 JSON、同名母体和同名存活容器, 没有检查存活 daemon.
- `TECHNICAL.md:37` 虽规定 cleanup 用 `pgrep -f 'git daemon.*<srv 根>'` 兜底发现, 该发现只出现在 cleanup 语义, 没有成为 birth 开始阶段的活动资源检查.

若 daemon 已成功启动且随后 JSON 丢失, 进程仍在时再次 birth 可能落入“无 JSON, 存在同名母体且干净 -> 复用”分支 (`TECHNICAL.md:65`), 再拉起另一个 daemon. 这既不满足“存活 daemon 应阻止重入”的状态模型, 也会使后续 cleanup 按同一 srv 根无法区分本次与上次 daemon. 应在 birth 重入检测中按相同 srv 根检查存活 daemon, 明确发现后的退出/cleanup 指引, 并补 daemon-only 残留测试.

#### 严重 E-02: D012 规则与 ISSUE-02 及 TC-007 全链入口仍不能同时成立

证据:

- 当前有效 D012 要求脏时阻塞、用户明示后才强拆 (`DECISIONS.md:99-103`). 技术规约已正确写为无 `--i-am-sure` 不删除、显式 flag 才放行 (`TECHNICAL.md:76`), 全局规则也如此 (`EXECUTION.md:24`).
- 但 `issues/ISSUE-02-container-client-loop.md:13` 仍规定 cleanup 记录状态“**不阻塞**”, `:23` 仍声称 D012 用户交互不实现; 这会指导执行者无条件删除脏容器, 直接违背 D012.
- 更进一步, `TECHNICAL.md:139-156` 的 TC-005/TC-006 都在容器内创建用于被拒 push 的新提交, 但未规定断言后删除/回退这些本地未 push commit. `TECHNICAL.md:157-165` 的 TC-007 却把 cleanup 后再 birth + smoke 写成全链成功, `issues/ISSUE-02-container-client-loop.md:82` 也给出不带 `--i-am-sure` 的 `birth -> smoke -> cleanup` 入口.

因此按当前 D012 检查, TC-005 的 non-ff 本地分叉和 TC-006 的新提交至少可能被判为未 push, 默认 cleanup 必须阻塞; 按旧 ISSUE-02 文字则会不安全地删除. 必须统一 ISSUE-02, 明确负向用例的本地状态复原策略, 并在 TC-007/验证入口中显式规定干净 cleanup 或 `cleanup --i-am-sure` 及其登记断言. 在此之前 M03 完成定义不可稳定满足.

#### 警告 W-01: 增量 JSON 的写入/回收契约仍缺原子性和未知状态语义

证据:

- `TECHNICAL.md:37` 要求每创建一资源即增量更新 JSON, 但未定义 JSON 的具体字段、写入失败/进程崩溃时的原子替换规则, 也未规定“资源已创建但状态文件只写了一半”如何判定.
- `TECHNICAL.md:72` 把最终 JSON 写入放在容器 clone 和断言之后, 与前面的增量要求方向一致, 但没有说明 clone 客户端目录是否纳入资源登记或 cleanup 生命周期.
- cleanup 兜底仅规定发现并回收 (`TECHNICAL.md:37,76`), 未定义 JSON 与 label/pgrep 结果不一致时以哪一方为准, 也未定义 PID 已复用或 pgrep 匹配到多个 daemon 时的拒绝条件.

这使“增量 JSON + 兜底发现”可表达但不可严格审计, 尤其 cleanup 可能依据过期 JSON 处理错误进程. 至少应固定 JSON schema/阶段状态, 使用原子写入, 对身份不一致 fail-closed, 并明确客户端目录是否删除或留存.

#### 警告 W-02: `/tmp/swt-m03-index.json` 的生命周期和唯一性不足

证据:

- `TECHNICAL.md:38` 只有 name -> repo 单值映射, 未规定 name 冲突时拒绝、覆盖或多值历史, 也未规定索引文件不存在、损坏、路径已删除时的退出码.
- `TECHNICAL.md:38` 要求 birth 注册、cleanup 注销, 但没有定义注册发生在夹具创建前后、注册写失败时是否继续, 也没有原子写/并发锁语义.
- `DECISIONS.md:85-90` 允许同一母体下多容器共享, 而单值索引只按 name 定位 repo, 没有说明多个活动实例或同名不同夹具的身份选择规则.

当前索引足以支持单进程、单夹具、顺序执行, 但不足以保证跨命令定位不串仓. 建议用绝对路径 + fixture 标识复核, 对冲突和 stale entry fail-closed, 并规定注册/注销的原子更新及异常恢复.

#### 警告 W-03: `--i-am-sure` 未进入公开 CLI 契约且脏检查失败态未定义

证据:

- `TECHNICAL.md:25-31` 的“唯一公开接口”代码块只列 `cleanup --repo --name`, 没有 `--i-am-sure`.
- `TECHNICAL.md:36` 只定义 0/1/2 三类退出码, 未指定脏阻塞、无法 SSH、容器已退出或状态不可判定时的退出码和登记行为.
- `TECHNICAL.md:76` 要求先 ssh 入容器查状态, 但对 SSH 不可达时是否视为未知脏状态、是否必须 flag 没有规定. 这直接影响 birth 中途失败后的 cleanup 兜底场景.

这是执行接口缺口, 也使 D012 的 fail-closed 语义无法覆盖容器启动失败/sshd 未就绪等部分资源状态. 应将 flag 和阻塞/未知状态的退出码、保留资源、重试方式写入公开契约.

### 一致性抽查

- `PRODUCT.md` 的 AC-001 至 AC-006 与 `TECHNICAL.md:103-174` 的 TC-001 至 TC-008 仍有覆盖, TC-003 已保留 HEAD 例外, TC-005 明确走容器路径.
- `DECISIONS.md` 的 D007/D008/D009/D010 与母体、无 hooks、单分支 ff-only、复用母体方向一致; D012 仅在 TECHNICAL/EXECUTION 中得到正确承接, ISSUE-02 仍相冲.
- `roadmap/MILESTONE-03.md:13-18` 仍要求可观测/可清理/可重跑编排器, 并把脏放行和失败清理列为 checklist 决策点. 当前规约虽有登记字段 (`TECHNICAL.md:76`), 但没有把字段的状态值、路径、时间、依据落实为可测试的 checklist schema, 也没有解决默认全链与脏状态的冲突.
- 仓库当前尚未出现 `workflow/use-sandbox-worktree/` 或 `tests/test_swt_m03.py` 实现文件; 本轮是规约终审, 因而未执行 E2E. 现有 `tests/` 只有 `tests/test_sync_to_pi.py` 等既有测试, 不构成 M03 实现已验证的证据.

### 结论

原 E-02 和 W-03/W-04/W-05 已消解, 原 E-01 的资源记录/cleanup 主要缺口已补, 原 W-01 具备基本索引方案. 但 D010 的存活 daemon 重入检测缺失, D012 在 ISSUE-02 与全链用例中仍冲突, `--i-am-sure` 未进入公开接口且未知状态未定义. **结论: 不通过.**

## 五审 (2026-09-03)

范围: 复核四审遗留的 E-01/E-02/W-01/W-02/W-03, 检查本轮修订引入的问题, 并对照 `PRODUCT.md`, `DECISIONS.md` D007-D012, `roadmap/MILESTONE-03.md` 及既有 M02 实测. 本节只追加审核产物, 未修改被审规约/源码.

### 四审项核对

- E-01 存活 daemon 绕过 birth 重入: 消解. `TECHNICAL.md:68-73` 已把按 srv 根 `pgrep` 发现存活 daemon 纳入 birth 状态机, 明确中止并提示先 cleanup, 不得重复拉起.
- E-02 D012/ISSUE-02 旧语义及负向用例残留: 核心路径已修订, 但仍有同文件旧声明冲突, 见严重 F-01. `TECHNICAL.md:80,82`, `EXECUTION.md:24`, `ISSUE-02-container-client-loop.md:13,68-69,82` 已规定负向用例复原, 脏则退出码 3 阻塞, `--i-am-sure` 放行并登记.
- W-01 JSON 状态不完整: 基本消解. `TECHNICAL.md:39-42` 固化了资源创建后的增量状态, 完整 schema, 临时文件 + `os.replace`, JSON/label/pgrep 身份不一致时 fail-closed, 以及克隆目录不登记不删.
- W-02 索引契约: 基本消解, 但跨 cleanup/rebirth 的默认入口仍有阻塞矛盾, 见严重 F-02. `TECHNICAL.md:43` 已覆盖原子注册/注销, 同名冲突拒绝, 缺失/损坏/失效路径退出码 2.
- W-03 `--i-am-sure` 与未知状态: 消解. `TECHNICAL.md:30,33,38,82` 和 `EXECUTION.md:24` 已进入公开接口并规定脏阻塞, 资源保留, SSH 不可达/容器已退出按未知脏状态 fail-closed.

### 发现

#### 严重 F-01: TECHNICAL 保留相互矛盾的 D012 边界声明

证据:

- 新语义: `TECHNICAL.md:82` 要求 cleanup 先查容器状态, 脏则中止且不删除, 通过显式 `--i-am-sure` 重跑才放行并登记; 同一语义还在 `TECHNICAL.md:30,33,38`, `EXECUTION.md:24` 和 `ISSUE-02-container-client-loop.md:13,68-69,82`.
- 旧语义: `TECHNICAL.md:186` 仍写"**不实现 D012 的脏检查用户交互**", 并称容器状态"只记录入产物". 这与当前已经实现的 D012 非交互形态直接相反, 不是措辞差异.
- 权威基准: `DECISIONS.md:99-103` 要求脏时阻塞, 用户明示后才强拆.

影响: 执行者无法判断 cleanup 是仅记录后删除, 还是默认阻塞并要求显式 flag. 旧声明若被按字面执行, 会重新引入四审 E-02 所指出的无条件删除未 push 工作问题, 并违背当前 D012. 需删除/改写 `TECHNICAL.md:186`, 同时明确 roadmap 的 checklist 是记录要求, 不替代 `--i-am-sure` 的放行条件.

证据等级: A.

#### 严重 F-02: 默认 `--repo` 的重跑入口不能验证母体复用

证据:

- `TECHNICAL.md:36` 规定省略 `--repo` 时 birth 自建 `/tmp` 夹具; `TECHNICAL.md:43` 规定自建夹具成功注册索引, 但 cleanup 成功时原子注销索引.
- `TECHNICAL.md:167` 对 TC-007 的要求却是 cleanup 后第二次 birth “走复用母体路径”.
- `ISSUE-01-host-loop-tracer.md:88` 和 `ISSUE-02-container-client-loop.md:82` 的手动验证入口均使用 `birth --name demo` / 再 `birth` 而未保留或传入 `--repo`.

按当前契约, 第一次省略 `--repo` 的 birth 会得到随机夹具并登记; cleanup 又注销该索引; 第二次省略 `--repo` 的 birth 没有旧夹具定位信息, 只能新建另一个夹具, 不会命中原母体复用分支. 因此验证入口可以得到"新夹具再次成功", 但不能满足 TC-007/D010 所宣称的"母体留存后复用", 也使 W-02 的跨命令定位修复未闭合重跑场景.

需二选一并在所有入口统一: 保留 cleanup 前打印的绝对 `repo` 路径并让第二次 birth 显式传 `--repo`, 或重新定义 birth 省略 `--repo` 时按 name 找到可复用的历史夹具且规定其冲突/失效处理. 后者不能与当前 cleanup 成功注销索引的契约并存而不补新的定位机制.

证据等级: A.

#### 警告 W-01: 增量 JSON 与 birth 步骤的“写 JSON”表述仍有歧义

`TECHNICAL.md:39` 要求每创建一个资源即增量落盘, 但 `TECHNICAL.md:78` 又把"写运行时 JSON"列为 clone 完成后的第 13 步. 若第 13 步被理解为首次写入, 中途失败时仍会无状态文件, 重新打开四审 E-01; 若它只是最终补写, 应明确写成"最终更新 JSON". 这是可局部澄清的契约歧义, 不改变本轮已固化的 schema/原子写方向.

证据等级: C.

### 一致性抽查

- Product 的 AC-001 至 AC-006 与 Technical 的 TC-001 至 TC-008 仍有覆盖, 容器主体/读面/回流/拒绝矩阵位于 `ISSUE-02`, 与 `PRODUCT.md:54-133` 的容器内验收主体一致.
- D007-D010 与当前母体、专属 daemon、单活动母体和复用方向一致; `TECHNICAL.md:68-73` 也已承接 D010 的存活 daemon 不变量.
- D012 的行为主体已正确进入 `EXECUTION.md` 和 ISSUE-02, 但 `TECHNICAL.md:186` 的旧边界声明仍造成直接不一致, 并非权威决策已改变.
- M03 roadmap 仍要求可观测/可清理/可重跑, 并要求脏放行等决策入 checklist (`roadmap/MILESTONE-03.md:13-18`). 当前技术规约有登记字段, 但应把 checklist 的记录职责与 D012 flag 的放行职责明确区分.
- 未发现本轮对 D008 hideRefs 多值写入, export marker, HEAD 广告例外, daemon 地址兜底或真实仓保护引入新的规格级矛盾. 本轮仍是规约终审, 仓库尚无 `workflow/use-sandbox-worktree/` 实现和 `tests/test_swt_m03.py`, 未执行 E2E.

### 结论

四审的存活 daemon 漏检, JSON schema/原子写与身份 fail-closed, 索引基本契约, 以及 cleanup CLI/退出码主体均已补齐. 但 `TECHNICAL.md` 内 D012 新旧边界声明冲突, 且默认 `--repo` 的验证入口无法实现 TC-007 的母体复用, 两项都会使执行规约在关键路径上产生不同结果. **不通过.**

## 六审 (2026-09-03)

范围: 只复核五审遗留 F-01/F-02/W-01, 检查本轮落盘修订的规格级一致性. 对照 `TECHNICAL.md`, `ISSUE-01-host-loop-tracer.md`, `ISSUE-02-container-client-loop.md`, `EXECUTION.md`, `DECISIONS.md` D012 与 M03 roadmap. 本节只追加审核产物, 未修改被审规约/源码.

### 五审项核对

| ID | 结论 | 证据 |
| --- | --- | --- |
| F-01 D012 旧边界声明 | 消解 | `TECHNICAL.md:187` 现明确 cleanup 实现 D012 非交互形态: 脏则阻塞并返回退出码 3, 仅 `--i-am-sure` 放行且登记. 同句明确 checklist 只承担记录, 不替代放行条件. 该语义与 `TECHNICAL.md:33,38,83`, `EXECUTION.md:24`, `ISSUE-02-container-client-loop.md:13,23,33,68-69` 及 `DECISIONS.md:99-103` 一致. |
| F-02 母体复用的验证入口 | 未完全消解, 见 E-01 | `TECHNICAL.md:45` 已正确规定第二轮 birth 传同一 `--repo`, `ISSUE-01-host-loop-tracer.md:88` 也从首个 birth stdout 获取 `<R>` 并向 smoke/cleanup/第二轮 birth 显式传递. `ISSUE-02` 仍有遗漏. |
| W-01 JSON 收尾歧义 | 消解 | `TECHNICAL.md:39-40` 固定每创建资源即增量原子落盘, `:79` 第 13 步现明确仅将 `stage` 更新为 `born`, 不再能合理解释为首次写 JSON. |

### 发现

#### 严重 E-01: ISSUE-02 的第二轮 smoke 和脏放行重试仍丢失 `<R>`/`--name`

证据:

- `TECHNICAL.md:43` 规定 cleanup 成功会注销 name 到 repo 的索引. `:45` 因此要求验证母体复用时, 后续命令显式传同一 `--repo`.
- `ISSUE-02-container-client-loop.md:82` 的全链入口已为首轮 smoke/cleanup 和第二轮 birth 写入 `--repo <R> --name demo`, 但第二轮 birth 后只写 `+ smoke`, 未给 `--repo <R> --name demo`. 索引已经由第一轮 cleanup 注销, 而第二轮 birth 使用显式 repo 不会触发"自建夹具成功后"的注册 (`TECHNICAL.md:43`), 故缺省 smoke 无法按 name 定位 `<R>`, 应退出码 2, 不能满足该行宣称的退出码全 0.
- 同行的脏放行重试写作 `cleanup --i-am-sure`, 同样遗漏 `--repo <R> --name demo`. `--name` 是唯一公开接口中的必要身份参数 (`TECHNICAL.md:28-30,35`), 此命令不构成可执行验证入口.

影响: F-02 的核心状态定位规则虽已进入 TECHNICAL 和 ISSUE-01, ISSUE-02 作为全链验收的手动路径仍不能执行完 TC-007, 也不能可靠执行 D012 放行验证. 应将该行的两处缩写分别展开为 `smoke --repo <R> --name demo` 和 `cleanup --repo <R> --name demo --i-am-sure`.

证据等级: A.

### 本轮修订的其余一致性检查

- 未发现 F-01 的新旧 D012 语义残留. TECHNICAL, EXECUTION 和 ISSUE-02 对默认阻塞, 显式放行, 登记责任的表述一致.
- F-03 未改变资源登记时机. `stage=born` 收尾与增量 JSON/schema/中途失败保留状态的契约相容.
- 除 E-01 外, 本轮变更未发现新的规格级矛盾. 容器网络的实际探测, sshd/pi 运行结果及端口运行细节均已标为实现时验证事实, 不作为本轮规格阻塞项.

### 结论

F-01 和 F-03 已消解, F-02 已在主规约及 ISSUE-01 消解, 但 ISSUE-02 的两条手动验证命令仍违反其刚固化的 `<R>` 传递契约. **结论: 不通过.**

