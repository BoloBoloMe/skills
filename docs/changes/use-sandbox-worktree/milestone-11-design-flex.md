# 设计: swt 场景脚本模块的 interface (灵活分支)

分支约束: 最大化灵活性, 细粒度可组合入口, 每个入口自身成立, 为多母体并发与新 provider 留扩展位. 用语沿用 codebase-design 词汇 (module/interface/implementation/seam/adapter/depth/leverage/locality) 与 UBIQUITOUS_LANGUAGE 领域词 (sandbox-worktree/母体/git 守护进程/推送落地).

## 0. 一句话结论

一个 module (`swt` 单命令), 其 interface = 1 个只读探测入口 + 2 个数据保护入口 + 4 个生命周期入口 + 2 个修复原语入口; 硬约束 (D008 模板/D011 顺序/D010 不变量/D012 保护/D013 换版提示) 全部钉在 implementation 里, 用户决策点全部以 exit 3 + 提示文案表达, 非交互.

## 1. interface

### 1.1 module 定位与 seam

- module: `swt`, host 侧 Python CLI, 位于 `workflow/use-sandbox-worktree/scripts/swt.py`, seam = 命令行 argv 进 / exit code + stdout(stdout 可选 `--json`) 出.
- 调用方: host llm (按 SKILL.md 指引敲命令) 与集成测试 (同一道 seam). 用户不直接敲; 用户的决策经 llm 转达为显式 flag.
- 外部 seam 只此一个; implementation 内部另有 internal seam (纯函数层, 供测试, 不进 interface, 见 DEEPENING.md "内部接缝不进接口").

### 1.2 命令面

统一约定: 所有入口支持 `--json`; 目标定位一律 显式 flag 优先, 缺省时从当前目录探测主仓 (`git rev-parse --git-common-dir`); 不设 M03 的跨命令注册表索引 (该索引契约是 M03 遗留缺口, 本设计以"显式目标必填 + cwd 探测"直接消解它). 所有入口非交互, 禁止 stdin 问答.

**探测 (只读):**

| 入口 | 作用 |
|---|---|
| `swt state [--repo <主仓>] [--only <段>]` | 输出主仓的完整 world 模型: 各母体 (目录/分支/工作区干净度), 各容器 (名字/状态/动态端口/镜像 digest), git 守护进程 (pid/地址/端口), config 是否已应用. 不 ssh 进容器, 快路径. |
| `swt dirty --container <名>` | ssh 评估单容器的脏度: 未 commit 数/未 push 数, 参照 ref = 主仓 `refs/heads/<母体分支>`; ssh 不可达时输出 `unknown` 并给 exit 3. |

**数据保护与终结:**

| 入口 | 作用 |
|---|---|
| `swt terminate --container <名> [--i-am-sure]` | 拆单个容器. 脏或 unknown → exit 3; `--i-am-sure` 强拆并把判决快照先写审计再删 (M03 record_dirty_release 先例). 该母体最后一个容器被拆时一并收 git 守护进程; 母体目录永不删. |
| `swt switch --mother <母体目录> [--i-am-sure]` | 换活动母体 (D010 原子序): 评估旧母体全部容器脏度 → 停旧容器与守护进程 → 校验 ref 与工作区干净 → 改 hideRefs 例外分支 → 拉新守护进程. 旧容器只停不删 (容器层保留). |

**生命周期:**

| 入口 | 作用 |
|---|---|
| `swt birth --repo <主仓> (--branch <分支> | --mother <目录>) --mode whitelist|blacklist [--allow IP/CIDR]... [--deny IP/CIDR]... [--requirements <文件>] [--image <ref>] [--allow-stale-image]` | 诞生: 建/复用母体 → 应用 D008 config → 起 git 守护进程 → 镜像匹配 (D013 digest 比对) → 建容器 → 注入 nft 规则 → readiness 校验 → 最后 start 容器 (D011 fail-closed 序). 每 secret 每步骤先落 runtime 状态再执行. |
| `swt recover [--repo <主仓>]` | 恢复 (D011): 接受任意残留态 (母体无容器/容器停/stale 守护进程/中途夭折的 birth), 逐层校验收敛: 收割 stale 守护进程 → 重注 nft 规则 → 拉/校验守护进程 → start 容器. 已健康 = 幂等 no-op exit 0. 母体工作区脏不自动修, 报 `MOTHER-DIRTY` 指人工. |

**修复原语 (绕过编排入口手动修复/扩展/测试用, 各自带前置守卫):**

| 入口 | 作用 |
|---|---|
| `swt config apply|verify|revoke --repo <主仓> --branch <分支>` | apply = 应用 D008 模板 (外来冲突键存在时拒 `CONFIG-FOREIGN`, 不覆写; 写前快照, 校验失败自动回滚); verify = 幂等校验含 git 版本对 `!` 否定语法的重验 (D008 部署重验); revoke = 移除 swt 拥有的键. 默认策略: config 常驻主仓 (D008 残余 3), revoke 仅显式终结时用. |
| `swt daemon start|stop|probe --repo <主仓>` | start 前置守卫: `config verify` 不过即拒. 端口预留 + pasta 地址优先/0.0.0.0 兜底 + 僵尸收割 (M03 start_daemon 语义). |

net-firewall.py 不设 swt 子命令 — 它已是独立 module 且 interface 成立, `birth`/`recover` 的 implementation 直接经其 CLI 调用.

**每个入口的四件事 (M11 待盘问项的正面回答):**

| 入口 | 状态前置 | 成功后状态 | 失败清理责任 | 禁止操作 |
|---|---|---|---|---|
| birth | 无其他活动母体 (I1); 母体存在则工作区干净; config 无外来冲突; 镜像决策已定 (否则 gate) | born: 母体+config+守护进程+容器 running+readiness 过, ssh 要素可从 state 取 | 每步先写 runtime 再动; 失败删自建容器与守护进程, config 回滚快照; 母体保留 | 不动他母体容器; 不删母体; 端口占用不自动换 (F006); 不碰真远端 |
| recover | 无 (任意残留态可入) | converged: running + readiness 过 | 只收割/对齐, 不新造资源 | 不 rm 容器; 不改分支; 母体脏不自动修 |
| state / dirty | 无 | 只读 | 无 | 任何写操作 (含 runtime 记录) |
| terminate | 容器存在 | 容器已删, 末容器时守护进程收, 母体保留 | 脏/unknown 时不删; 强拆先审计后删 | 不删母体; 不动 ref; 默认不拆未知脏 |
| switch | 目标母体存在且干净; 旧母体容器无未 push (有则 gate) | 例外分支已换, 新端点就绪, 旧容器 stopped 保留 | 中途失败尽力恢复旧例外分支与旧端点并报残态 | 不删任何容器; 不产生同仓双活跃母体 |
| config / daemon | 见各自守卫 | 单层就绪 | apply 失败回滚快照 | 不覆写外来键; 无 config 不起守护进程 |

### 1.3 exit code 与错误模式

| code | 含义 | stderr 首行标签族 |
|---|---|---|
| 0 | 成功, 含幂等 no-op | — (stdout 键值行或 `--json`) |
| 1 | 断言/校验失败, 环境异常需诊断 | `ASSERT-FAIL <名>`, `COMMAND-FAIL <命令>` (附原生 stderr 原文, 不翻译) |
| 2 | 前置条件/参数/环境错误 | `STATE`, `NOT-A-REPO`, `INVARIANT-ACTIVE-MOTHER`, `CONFIG-FOREIGN`, `MOTHER-DIRTY`, `PRECONDITION-*` |
| 3 | 用户确认门: 提示文案在 stderr, 人话, llm 原样转述用户; 用户拍板后加显式 flag 重跑 | `CONFIRM-DIRTY`, `CONFIRM-UNKNOWN-DIRTY`, `CONFIRM-IMAGE-NEWER`, `CONFIRM-SWITCH-DIRTY` |

exit 3 是本 interface 的核心机制: 脚本非交互, 确认点 = "停在一个可重入状态 + exit 3 + 文案 + 指明重跑 flag". 每个门对应的 flag: 脏强拆/脏换母体 → `--i-am-sure`; 镜像新版 → `--image <新ref>` 或 `--allow-stale-image`. `--i-am-sure` 必触发审计登记 (先登记后执行, 删失败也留痕).

### 1.4 state 输出契约 (--json)

```json
{"schema": "swt.state/v1",
 "repo": "<主仓绝对路径>",
 "mothers": [{"dir": "...", "branch": "...", "worktree_clean": true,
   "config_applied": true,
   "daemon": {"pid": 1, "addr": "0.0.0.0", "port": 44651, "fallback": true},
   "containers": [{"name": "swt-...", "state": "running|exited|absent",
                    "ssh_port": 42329, "ssh_key_path": "...",
                    "image_digest": "...", "dirty": null}]}],
 "active_mothers": 1}
```

- `dirty` 恒为 null (state 不 ssh); 要脏度就调 `swt dirty`.
- `ssh_key_path` 指向 runtime 目录下的 per 容器私钥 (用户 ssh 入容器的凭据, llm 拿它拼 ssh 命令给用户).
- schema 带版本号, 只加字段不改字段; 消费方须容忍未知字段. 这是版本演进的扩展位.

### 1.5 不变量 (interface 级承诺)

- I1 单活动母体 (D010): 任一 mutating 入口在同主仓已有别的活动母体 (有存活容器或守护进程) 时拒绝, `INVARIANT-ACTIVE-MOTHER`. 注意: 这是运行时检查而非语法限制 — state 的 mothers 本就是列表, 未来 receiver 隔离重开 (D010 未决迷雾) 时只放宽检查, 命令面不动.
- I2 fail-closed 序 (D011): 任何容器工作负载 start 晚于 nft 规则注入与守护进程 readiness 校验. 编排入口内部保证; 原语入口靠各自前置守卫使手工错序 fail-closed (无 config 不起守护进程, 无守护进程端点不建容器).
- I3 写面收敛 (D008): 容器写面 = 仅母体分支 fast-forward push, 由 config 模板保证, `config verify` 是它的可检查形态.
- I4 数据保护 (D012): 任何删除容器层的行为前必须有脏度判决: clean → 行, dirty/unknown → 门 (exit 3) 或显式 `--i-am-sure` + 审计.
- I5 真远端不暴露: 所有入口的实现只经 git 守护进程 (base-path 仅主仓, 不开 --export-all) 与主仓本身, 无任何入口产生通向真远端的容器侧通道.
- I6 一名贯穿 (D007): 母体分支名 = worktree 目录名 = 容器名 (`swt-<分支>`) = label 标识, 全命令面一致.

### 1.6 顺序约束 (调用方须遵守)

- O1 协议顺序: 任何动作前先 `state` (llm 的读-判-动循环以此为准).
- O2 birth 遇残留态拒绝 (`exit 2` 指向 recover); recover 是唯一重入收敛入口.
- O3 switch 不要求先 terminate (只停不删), 但自带旧母体全容器脏评估.
- O4 terminate 只在拆最后一个容器时收守护进程; 非末容器不动守护进程与 config.
- O5 手工修复时原语顺序: `config verify` → `daemon start` → net-firewall apply → 容器 start; 编排入口内部已按此序.

### 1.7 MILESTONE-11 考察点覆盖表

| 考察点 | interface 落点 |
|---|---|
| 母体身份与复用 | `--branch`(新建)/`--mother`(复用) 双锚; birth 自动判复用 (干净即复用并报 `mother_reused`); cwd 探测 worktree 身份; I1 检查 |
| 恢复状态机 | `recover` 收敛任意残留态; stale 守护进程收割; readiness 校验; O2 使重入路径唯一 |
| 终结数据保护 | `dirty` 独立入口; 参照 ref = 主仓母体分支 ref; ssh 不可达 = unknown = 门; `--i-am-sure` + 先审计 |
| 共享母体 | state 列出母体下全部容器 (label 过滤, 不只看单容器); terminate 按容器名; 末容器判定决定守护进程收否; switch 评估旧母体全部容器 |
| 全局 config | `config apply/verify/revoke`; 外来键拒覆写; 失败回滚快照; git 版本重验入 verify |
| 镜像版本 | birth 内 digest 比对 → `CONFIRM-IMAGE-NEWER` (exit 3) → `--image`/`--allow-stale-image`; 存活容器绝不动 (D013) |

### 1.8 脚本与 skill 文档的职责切分 (M11 待盘问项)

- 进脚本: 状态探测, 顺序, 模板, 门, 审计, 参照 ref 语义, readiness 校验.
- 留文档: 原生报错译解表 (D008 残余 2, 脚本只透传原文 + 机器标签); 黑/白模式语义与域名解析盘点方法论; 容器内冲突消化指引 (D009 fetch/解冲突/重推, 容器内流程完全不归 swt); 母体存删自决指引; D019 风险明示.
- M03 checklist 决策点成熟度: 黑/白模式 → birth `--mode` 必选 (llm 会话内先问用户); 脏放行 → `CONFIRM-DIRTY` + `--i-am-sure`; 镜像换版 → `CONFIRM-IMAGE-NEWER`; 恢复确认 → 会话内确认, recover 免 flag (幂等安全); 母体复用 → 自动判 + 报告, 不设门; 端口冲突 → 不设门 (无用户决策空间, exit 1 原文 + 译解表指路).

## 2. 使用示例 (调用方视角: host llm + 用户确认回路)

### 2.1 主链: 诞生 → 干活回流 → 终结

```
$ swt state --repo ~/Workspace/demo          → exit 0, 空世界 (mothers: [])
  llm 问用户: 分支名? 黑/白模式? 白名单盘点哪些域名?
$ swt birth --repo ~/Workspace/demo --branch feature/pi-report \
    --mode whitelist --allow 203.0.113.7      → exit 0
  (implementation 内部: 建母体 → config → 守护进程 → 镜像匹配 → 容器 → 规则 → start)
$ swt state --repo ~/Workspace/demo --json   → 母体/容器 running, ssh_port/ssh_key_path 就绪
  llm 把 ssh 命令交给用户; 用户 ssh 入容器驱动 pi 干活, push, 推送落地回母体目录
$ swt dirty --container swt-feature-pi-report → exit 0, unpushed=0
$ swt terminate --container swt-feature-pi-report → exit 0
$ swt state                                   → 容器 absent, 母体保留, 守护进程已收
```

### 2.2 失败路径 A: 终结撞上未 push 工作 (D012 门)

```
$ swt dirty --container swt-feature-pi-report → exit 0, unpushed=2
$ swt terminate --container swt-feature-pi-report
  stderr: CONFIRM-DIRTY 容器内有 2 个未 push 提交, 强拆后不可恢复; 确认请加 --i-am-sure 重跑
  → exit 3. llm 原样转述用户. 用户答"先留着" → 什么都不做, 状态未变 (可重入).
  用户后改主意"拆":
$ swt terminate --container swt-feature-pi-report --i-am-sure → exit 0 (审计先行登记)
```

### 2.3 失败路径 B: host 重启后的恢复 (D011 状态机)

```
$ swt state --json   → 容器 exited, daemon null (stale 进程被收割前呈现为残留)
$ swt recover        → exit 0
  (implementation: 收割 stale 守护进程 → 重注 nft 规则 → 起并校验守护进程 → 最后 start 容器)
$ swt recover        → exit 0 (幂等 no-op, 容器已 running)
```

### 2.4 失败路径 C: 不变量与换母体 (D010)

```
$ swt birth --repo ~/Workspace/demo --branch other-thing ... 
  stderr: INVARIANT-ACTIVE-MOTHER 主仓已有活动母体 feature-pi-report
  → exit 2. llm 转述; 用户说"换到新母体":
$ swt switch --mother ~/Workspace/demo-mother-other --i-am-sure → exit 0
  (旧容器无未 push 时可省 --i-am-sure; 有则先出 CONFIRM-SWITCH-DIRTY)
  旧容器 stopped 保留, 例外分支已换, 新守护进程就绪; state 的 active_mothers 仍为 1
```

## 3. seam 背后藏了什么

implementation 组成 (单文件起步, 内部按层切, 不外露):

- **发现层**: label 过滤 `podman ps -a`, 按命令行 pattern 找守护进程 pid (M03 pgrep 先例), git config/worktree 读, 输出解析 → state 模型. 五个编排入口共享同一发现层 — locality 的主要来源.
- **config 引擎**: D008 模板展开, 外来键检测, 写前快照/失败回滚, verify 含 git 版本对 `!` 语法的重验.
- **守护进程监督**: 端口预留, pasta 地址优先/0.0.0.0 兜底, 探测, 僵尸收割 (M03 已知限制的兜底落点).
- **容器操作**: create/start/rm, 动态端口发现 (F006: 不记录, `podman port` 现查), per 容器 ssh keypair 生成与 authorized_keys 注入.
- **脏度评估**: ssh `git status --porcelain` + `rev-list --count <主仓母体分支 ref>..HEAD`, 不可达 → unknown.
- **审计**: runtime 目录 append-only jsonl, 强拆/未知脏判决快照先行登记.
- **编排器**: birth/recover/terminate/switch 四序列, 把 D008/D010/D011/D012/D013 的顺序与门钉死在代码里 — 这正是脚本封装方向已确认的动机 (防 llm 即兴漏项/乱序).

与现有四个脚本的关系:

- `image-prep.py` (M07) 与 `net-firewall.py` (M04): **复用, 不吸收**. 它们各自 interface 已成立且被各自 milestone 测试覆盖; swt 的 implementation 经其 CLI 调用. 给它们再包一层 swt 子命令只会造透传浅 module.
- `login-wall.py` (M09): **不统辖**. 登录墙是存续期可选环节 (用户要登录外部站点时), 由 skill 文档按需指路, 与生命周期编排无顺序耦合.
- `e2e-smoke.py` (M03): **被替代, 退役为测试夹具**. 它的 birth/smoke/cleanup 是本设计三入口的实证先例; 其断言模式 (clone 必须检出母体分支/push 落地母体文件变化/拒绝矩阵/脏阻塞/审计登记/母体留存) 平移为 swt 的 interface 测试, 编排职责归 swt.

为何值得藏: config 的 `!` 例外语法与版本敏感性, fail-closed 顺序, pasta 兜底, 脏参照 ref 语义, 审计先行 — 每一项都是 llm 即兴组合时漏项率高, 且改一处须处处同步的知识. 藏进 implementation 后, llm 每学一单位命令面 (9 个入口 + 2 个门 flag) 触发整条生命周期的行为, depth 高; 一次修复处处生效, locality 高.

## 4. 依赖与测试策略

按 DEEPENING.md 依赖类别:

- **类别 1 进程内**: 输出解析 → state 模型, config 模板展开, 门决策表, slug 推导. 纯函数, direct unit 测试, 属 internal seam, 不进 interface.
- **类别 2 本地可替代**: 文件系统 runtime/审计记录, git 仓 (M03 fixture 仓先例 = 本地替身), temp 目录. 测试用真 git + 临时目录.
- **类别 3/4**: 无跨网络自有服务, 无外部 SaaS. podman/nft/ssh/git 守护进程 = 本机系统命令, 无轻量替身, 且测试策略明确不许假设 mock 框架 → 按 M03 先例真跑集成: fixture 主仓 + 一次性容器, 覆盖每入口的正/负/门分支. nft 与 nftables 真实内核表在测试机上真注入真清除 (M04 先例已此做法).

测试打在 interface 上 (interface 即测试面):

- 经 argv 进, 断言 exit code + stdout `--json` + 可观察外部事实 (`podman ps`, `git show-ref`, 母体文件落地, 审计文件行), 不 import 内部函数, 不读内部状态.
- 必备用例组: 拒绝矩阵 (新分支/tag/non-ff/删除); `CONFIRM-DIRTY` → `--i-am-sure` → 审计行存在; 杀掉中途 birth → `recover` 收敛; 双母体 → `INVARIANT-ACTIVE-MOTHER`; 外来 config 键 → `CONFIG-FOREIGN` 且不覆写; 守护进程 kill -9 残留 → recover 收割; `--json` schema 版本前向兼容 (未知字段容忍).
- 替换不叠加: e2e-smoke 的阶段断言迁入 swt interface 测试后, 原脚本级用例退役 (DEEPENING.md "删除测试").

## 5. 权衡

- **leverage 高处**: llm 的学习面 = 1 个 state 契约 + 4 个动作 + 2 个门 flag, 即可驱动全生命周期并守住全部硬约束; SKILL.md 从"步骤清单"瘦身为"入口 + 门协议 + 译解表", 文档不再承载顺序记忆. state 的快/慢分离 (不 ssh) 使读-判-动循环便宜.
- **locality 高处**: 发现层单份, 五入口共享; 顺序/模板/参照语义变更只进 implementation. 对照反方案 (五脚本各自实现): 脏语义要写五遍, D008 改一处动五处.
- **seam 位置的代价**: (1) config/daemon 原语扩了可误用面 — 对冲是各入口自带前置守卫使错序 fail-closed, 但诊断负担落在 llm 读 exit 2 标签; (2) 大 interface 有 shallow 化风险 — 对冲是每入口背后是完整发现+序列而非透传, depth 仍高, 学习成本由 SKILL.md 门协议消化; (3) state schema 一旦被依赖, 淘汰字段有兼容成本 — 对冲是版本号 + 只加不改; (4) e2e-smoke → swt 迁移期双轨, M12 实现时一次性收拢; (5) 遵守 D022 (不做 provider 抽象) 与"给新 provider 留扩展位"的张力: 扩展位收在 implementation 内部 — podman 调用收拢为一处 + SKILL.md 容器命令独立一节, 换 provider 是改代码 + 改文档节, 不是换 adapter; 这是 D022 已拍板接受的代价. (6) 放弃 M03 注册表索引换显式目标: 少一份跨命令状态 (少一类不一致), 代价是每条命令多敲 `--repo` — 对 llm 调用方近乎零成本.
- **与对照方案的差异**: 较"严格五脚本"方案多出 config/daemon 原语, dirty 独立入口与 switch 的 `--i-am-sure` — 多出的面积各有明确服务对象 (手工修复/ expensive ssh/数据保护), 非为对称而对称; 较"单一 do 巨命令"方案, 拆分换来测试可分入口打点与 llm 的最小权限式调用.
