# 设计: swt — sandbox-worktree 生命周期 module (为最常见调用方优化)

Design It Twice 分支产物. 只读设计, 未改仓库任何文件.
词汇沿用 codebase-design: module / interface / implementation / seam / adapter / depth / leverage / locality.

最常见调用方 = host llm 按 SKILL.md 敲 CLI, 用户在场, 最终决策权在用户. 因此本设计的两条主轴:

- 默认主链 (诞生→干活回流→终结) 平凡到近乎无脑: 探测, 顺序, 模板, 脏检查全部藏进 implementation, 调用方只读 exit code 和末行 STATE.
- 危险操作显式独立: 强拆 (terminate --force) 与换母体 (switch) 是独立子命令/独立 flag, 藏进通用入口算设计失败.

## 1. interface

### 1.1 module 定位与 seam

一个 module: `swt.py`, host 侧 CLI, seam 就是它的命令行. 五个子命令对应五个场景:

```
swt birth     诞生   建/复用母体 + 起容器, 全就绪交付
swt resume    恢复   把登记过的 sandbox-worktree 拉回全就绪 (fail-closed)
swt status    查询   只读盘点, 永不改动任何状态
swt terminate 终结   删容器与随生灭资源, 母体保留, 脏则阻塞
swt switch    换母体 原子换绑主仓的全局单授权域 (独立危险入口)
```

选"一 module 五子命令"而非五个独立脚本: 五个场景共享同一套探测, config 模板, runtime 状态文件和输出协议, 拆成五个脚本会把它们复制五份 (locality 崩坏); 合并入口粒度的取舍见 1.7.

### 1.2 exit code 协议 (全入口统一, 调用方背这一张表)

| exit | 含义 | 调用方动作 |
|------|------|-----------|
| 0 | 场景完成 | 读末行 STATE, 转述用户 |
| 1 | 等用户决定 | stdout 有 `DECIDE <问题> <选项flag>` 行; llm 原样转述用户, 用户答后带 flag 重跑同一子命令 |
| 2 | 前置不满足/不变量违反 | stderr 首行 `FAIL <人话>`; 状态未变; 不要重试同一命令, 读原因改判断 |
| 3 | 中途失败可重入 | stderr 首行 `PARTIAL <阶段> <人话>`; 已完成阶段已登记, 重跑同一子命令即幂等收敛 |
| 4 | 环境错误 | `ENV <人话>`; podman/git/nft 缺失或版本不支持, 报告用户修环境 |

exit 1 是本设计的核心机制: 脚本非交互 (不读 stdin), 所有用户确认点都表达为"exit 1 + DECIDE 行 + 重跑带 flag". 确认的对话由 llm 承担, 决策落在 flag 上留进命令历史.

### 1.3 输出协议

- stdout 进度行: 人话, 供用户直读.
- stdout 末行: `STATE {...}` 单行 json, 机器读, 五个子命令共用同一 schema (沿用 M09 login-wall up 的单行 json 先例):

```json
{"schema":1, "repo":"<主仓绝对路径>",
 "mother":{"branch":"...","dir":"...","exists":true,"worktree-dirty":false},
 "config":{"swt-form":true},
 "daemon":{"addr":"0.0.0.0","port":44651,"orphan":false},
 "containers":[{"name":"swt-<slug>","state":"running","ssh-port":42329,
                "dirty":{"uncommitted":0,"unpushed":0,"reachable":true}}],
 "image":{"ref":"...","digest":"...","verdict":"REUSE","newer-available":false},
 "network":{"mode":"whitelist","table-present":true}}
```

- status 在"什么都没有"时也 exit 0, 对应字段填空值 — "没有"是查询的合法答案.

### 1.4 各入口的四件事 (前置 / 成功后 / 失败清理 / 禁止)

**birth** `swt birth --repo <主仓> --branch <源分支> [--mode whitelist|blacklist --allow CIDR]... [--image <ref>] [--reuse-mother]`

- 前置: --repo 是 git 仓; git 版本下限满足且 `!` 否定语法行为级重验过 (D008); 该主仓无其他分支的活动母体 (D010, 违反则 exit 2 并指引走 switch); podman 可用.
- 决定点 (逐个 DECIDE, 一次 invocation 把所有待决问题一次列全, 不挤牙膏): 黑/白模式与放行清单 (绘制会话拍板的固定环节); 母体新建或复用 (复用前校验母体工作区干净, 脏则 exit 2); 镜像 verdict=BUILD-NEW 时停 (D014: 推导清单经用户确认后由 llm 走 image-prep build, 再持 --image 重跑; birth 不自动构建).
- 成功后: 母体 worktree 就位; 主仓 config 钉成 D008 形态 (幂等, 重跑不重复加键); net-firewall apply 注入; daemon 拉起并 probe 通过; 容器 create+start; ssh 通; 容器内 clone 检出母体分支并断言读面只广告母体分支. STATE 全就绪.
- 失败清理: 分阶段写 runtime 状态文件 (`~/.agents/sandbox-worktree/runtime/<identity>.json`), PARTIAL 时列已完成/未完成阶段; config 写入失败用写前快照回滚, 不留半套 config.
- 禁止: 不删任何已存在容器/母体; 不动真远端; 端口被占不自动换 (F006/D011, exit 2 透传原生报错); 存活容器镜像有新版绝不自动拆 (D013, STATE 只标 newer-available).

**resume** `swt resume --repo <主仓> [--name <容器名>]`

- 前置: runtime 状态存在 (没诞生过就没有恢复对象, exit 2); 共享母体多容器时用 --name 挑, 缺省唯一容器.
- 成功后: fail-closed 序列钉死在 implementation: 清 stale daemon (孤儿进程先杀并记录) → nft 重注入 (stop/start 后 netns 重建规则全失, 规则未就绪容器负载不得抢跑) → daemon 重拉 → probe → start 容器 → ssh 校验. STATE 全就绪.
- 用户确认: 无 DECIDE gate. resume 无破坏性, D011 的"经确认"由 skill 层承担 — llm 问用户"要恢复吗", 用户答了 llm 才跑. 脚本保持无脑.
- 失败清理: 无破坏动作; 任何一步失败留可重入状态, exit 3.
- 禁止: 不重建容器; 不动母体 ref; 端口被占 exit 2 透传.

**status** `swt status --repo <主仓>`

- 前置: 无 (只读).
- 成功后: exit 0 + STATE. 覆盖 D009 纪律 — 列该主仓下活动母体与其**全部**容器 (不只 cwd 单容器), 每容器脏度 (uncommitted/unpushed/可达性), 孤儿 daemon 检测, config 形态, 镜像 digest 新旧提示.
- 失败清理: 无 (不改任何状态).
- 禁止: 永远无副作用, 永不阻塞.

**terminate** `swt terminate --repo <主仓> [--name <容器名>] [--force]`

- 前置: 容器存在. 脏检查: ssh 可达 → 容器内 `git status --porcelain` (含未跟踪) + 容器 HEAD 对比参照 ref; 不可达或容器已停 → 脏度 unknown, **视同脏** (考察点: 容器已停时的脏检查路径, 宁阻塞勿误删).
- "未 push" 的参照 ref = 主仓 `refs/heads/<母体分支>`: 容器 origin 即经 daemon 指向主仓该 ref, daemon 死了 ref 仍在主仓, host 侧直读, 两个通道等价.
- 脏 → exit 1, DECIDE 行列出脏什么 (N 个未提交文件 / N 个未 push commit), 需 `--force`. --force 是显式独立 flag, 不藏在任何别的入口.
- 成功后: 容器 rm, 该容器 daemon kill, nft 表 clear, runtime 记录清除; **母体保留** (D012), STATE 注明母体路径; 主仓 config 不动 (常驻幂等, D008 已接受残余).
- 共享母体: 多容器各终结各的, 母体级资源 (config, 母体目录) 只随"最后一个容器终结"进入闲置, 不删 (D009/D010).
- 禁止: 绝不删母体; 无 --force 绝不碰脏容器.

**switch** `swt switch --repo <主仓> --to <目标分支|母体目录名> [--force]`

- 前置: 主仓存在; 目标母体不是当前活动母体.
- 步骤 (D010 原子序): 对旧母体**全部**容器逐个跑脏检查 (同 terminate 标准) → 有脏则 exit 1 列明细, 需 `--force` → 停旧母体全部容器与其 daemon, 清 nft → 校验目标母体 ref 存在且工作区干净 → 改 hideRefs 例外分支 → get-all 断言 → STATE.
- 成功后: 单授权域换绑完成. 新母体的容器不由此入口建 — 用户对新区走 birth (复用母体), 职责不混.
- 失败清理: 停旧之后改例外之前失败 → exit 3, runtime 记录"授权域空窗", 重跑 switch 或对旧母体 birth 收敛; --force 的强停决策已由用户给出, 重跑不再问.
- 禁止: 不删旧母体 (存删用户自决); 不建容器; 不在脏检查未过时动任何容器.

### 1.5 不变量 (所有入口共同维护, 调用方可信靠)

1. 单活动母体: 同一主仓同一时刻至多一个有存活容器/daemon 的母体 (D010). birth/switch 是仅有的两个会改变它的入口, 且都显式.
2. 一名贯穿: 母体分支名 = worktree 目录名 = 容器名主体 (swt-<slug>), 经 use-worktree slug.py 规范化.
3. 母体不因 terminate/switch 消失, 存删永远用户自决 (D012).
4. 幂等: birth/resume/switch 重跑收敛到同一终态; config 重写不重复加键.
5. 危险扩散最小: 任何删容器动作必经 terminate (或 switch 的前置强停), 且必经脏检查或 --force.

### 1.6 顺序约束与错误模式

- 调用方无顺序负担: 任何时刻可直接调 status; birth 前不需要先跑别的; 忘了状态就先 status.
- 错误模式三类, 前缀即分类: `FAIL` (前置, 状态未动, 别重试), `PARTIAL` (中途, 状态已登记, 重跑收敛), `ENV` (环境, 找用户). `DECIDE` 走 stdout 不是错误.
- 原生报错 (git/podman 英文) 原文透传在 stderr 后续行, 不翻译不吞 — 译解表归 skill 文档 (D008 残余), 避免两处漂移 (反方审查 #3 的教训).

### 1.7 考察点覆盖映射 (MILESTONE-11 六项全覆盖)

| 考察点 | 落点 |
|---|---|
| 母体身份与复用 (D010) | birth 探测序列 + 复用 DECIDE + 不变量违反 exit 2 指引 switch |
| 恢复状态机 (D011) | resume fail-closed 序列钉死; stale daemon 清理; runtime 状态文件使 PARTIAL 可重入 |
| 终结数据保护 (D012) | terminate 脏检查 (含未跟踪) + 参照 ref = 主仓母体分支 ref + 停/不可达视同脏 + --force 独立 |
| 共享母体 (D009) | status 列全部容器; terminate 按容器隔离; 全局资源只经 switch 且逐容器脏检查 |
| 全局 config (D008) | birth 幂等写入 + `!` 语法行为级重验 + 快照回滚 + 非本模块形态的既有值 exit 2 人工 |
| 镜像版本 (D013/D017/D020) | birth 组合 image-prep match, BUILD-NEW 停给 DECIDE, newer-available 只标不拆, base-digest 硬谓词由 match 承担 |

checklist 决策点成熟度: 母体复用/黑白模式/脏放行三点成熟为 DECIDE+flag; 端口冲突钉死不解决 (F006); daemon 残留降为 resume 自清 + STATE 标注.

## 2. 使用示例 (调用方视角)

### 2.1 主链: 诞生 → 干活回流 → 终结

```
llm: swt birth --repo ~/Workspace/proj --branch main/feat-login
     exit 1, DECIDE 网络模式? --mode whitelist --allow <LLM域名IP> / --mode blacklist
用户: 白名单, 放行 LLM 那两个段.
llm: swt birth --repo ... --branch main/feat-login --mode whitelist --allow 1.2.3.4/32 ...
     exit 1, DECIDE 母体不存在, 新建? / 镜像 verdict=BUILD-NEW (附推导清单)
用户: 新建; 清单确认, 去构建.
llm: image-prep build ... (D014 流程) → swt birth ... --image localhost/sandbox-worktree/proj:2026.09.12-1
     exit 0, STATE: 容器 running, ssh-port 42329.
用户 ssh 入容器干活, 容器内 pi push → 推送落地, 母体目录即时可审阅.
llm: swt terminate --repo ~/Workspace/proj
     exit 1, DECIDE 容器有 3 个未 push commit, 强拆? --force
用户: 等下, 让它先 push. (容器内 push 后)
llm: swt terminate --repo ~/Workspace/proj
     exit 0, STATE: 母体保留在 .../proj-feat-login
```

全程 llm 只做了: 敲命令, 读 exit code, 转述 DECIDE, 把答案变 flag.

### 2.2 失败路径 A: 中途崩了, resume 重入

```
birth 执行到 daemon 拉起后宿主机断电. 重启后 llm:
swt status --repo ...
     exit 0, STATE: config 就绪, daemon orphan=true, 容器 exited.
swt resume --repo ...
     exit 0 (孤儿 daemon 先杀, nft 重注入, daemon 重拉, 容器 start, ssh 校验过), STATE 全就绪.
```

重入不重问: 已确认过的决策记录在 runtime 状态里, resume 不再 DECIDE.

### 2.3 失败路径 B: 违反单活动母体不变量

```
当前活动母体是 feat-login, 用户要起新分支:
swt birth --repo ... --branch main/feat-search
     exit 2, FAIL: 主仓已有活动母体 feat-login (容器 swt-feat-login running), 换母体走 switch.
llm 向用户说明, 用户确认换:
swt switch --repo ... --to feat-search
     exit 1, DECIDE: 旧母体容器 swt-feat-login 有未提交改动 2 文件, 强停? --force
用户: 先让它 push. → 容器内 push → swt switch ... (脏检查过) exit 0.
llm: swt birth --repo ... --branch main/feat-search --reuse-mother? 不 — feat-search 无母体, 正常 birth 流程.
```

switch 换绑授权域后, 旧母体目录原地保留, 用户日后自决存删.

## 3. seam 背后藏了什么

implementation 组成 (M12 实现时的下沉来源):

- **e2e-smoke.py 的阶段函数是直接前身**: 母体建立, D008 config 写入与断言, daemon 拉起/probe, 容器 create/ssh key 注入/克隆验证, 脏检查, 兜底清理 — M03 已实跑验证过这些序列, M12 把它们从"测试编排器"下沉为 swt 的 implementation. 下沉完成后 e2e-smoke 退役, 其测试在 swt interface 处重写 (替换, 不叠加).
- **net-firewall.py / image-prep.py 按现有 interface 组合**: birth/resume 经 `apply/show` 注入规则, 经 `match` 判镜像. 不改这两个 module, 它们自己的 seam 已被 M04/M07 测试钉住.
- **login-wall.py 不进 implementation**: 登录墙是镜像内 swt-vnc 自启能力, swt 只消费镜像契约.
- **新增的藏起来的部分**: runtime 状态文件与重入状态机, 参照 ref 计算, 脏度汇总, DECIDE/STATE 协议, config 快照回滚, 孤儿 daemon 判定.

为何值得藏: D011 的 fail-closed 顺序, D008 的模板与版本重验, D010 的不变量检查, D012 的脏检查语义, 都是"llm 即兴操作时最易漏项/乱序"的硬约束. 钉进代码后, 一次修正处处生效 (locality); llm 每次只学一张 exit code 表 (depth = interface 一单位撬动整个生命周期, leverage 高). 留在 skill 文档的只剩: 确认话术, 报错译解表, herdr 委派配方 (D021, 存续期非生命周期), 冲突消化指引 (D009, 容器内流程), 风险明示 (D019).

## 4. 依赖与测试策略

按 DEEPENING.md 依赖类别:

- **进程内**: 状态机判定 (探测结果 → 允许动作/DECIDE), config 模板渲染, STATE 组装, slug 规范化 (子进程调 slug.py, 纯计算). 可深化, 直接测.
- **本地可替代**: podman/git/nft/ssh 这类无现成替身的依赖不强行造替身. 它们是本机系统命令, 快, 无网络, 副作用可用临时目录圈住 — M03 已证明 fixture 仓 + 真跑是有效测试形态. 不为 mock 引入第二道 seam: "一个 adapter 意味着假想的 seam", 这里注入 mock adapter 只会产生测不出真问题的假测试.
- **远程但自有 / 真正外部**: 无. 本设计没有网络服务依赖; 真远端对容器不可达是拓扑保证的 (F003), 测试反而要断言它不可达.

测试全打在 interface (CLI seam) 上, 断言 exit code + STATE json + 文件系统终态, 不 peek implementation:

- 主链: birth (答完 DECIDE) → status 全就绪 → 容器内 push → 母体文件变化 → terminate 干净 → 母体仍在.
- 负向: 有活动母体时 birth 别分支 exit 2; 脏容器 terminate exit 1, --force 后容器灭母体在; 已停容器 terminate 视同脏; switch 脏 exit 1; config 幂等 (重跑 birth 键不重复); 端口占用 exit 2 且容器不被改建; `!` 语法重验失败 exit 4.
- 顺序的可观察证据: resume 后断言 "容器 running 且 nft 表存在" (fail-closed 的结果态), 顺序本身由 implementation 钉死, 测试不踩时钟.
- 沿用 M03 形态: `uv run --with pytest` + fixture 主仓, 不假设 mock 框架.

## 5. 权衡

- **leverage 高处**: exit code + DECIDE + STATE 三件套协议. llm 学一次, 驱动五个场景; 用户确认从散文变成机器可判定位, 命令历史里还留下决策痕迹.
- **locality 高处**: 四条硬决策 (D008/D010/D011/D012) 各只有一处实现. 反方审查担心的"错误假设固化进五个入口"被消解: 状态语义只有一份.
- **seam 位置的代价**: (1) CLI seam 意味跨调用状态走 runtime 文件而非进程内存, 多一份格式兼容面 (schema 字段钉死 + 版本号兜底); (2) 主仓 config 是全局状态, 测试需每例独立 fixture 主仓, 不能并行共享; (3) 与 image-prep 的组合是子进程 key=value 文本协议, 字段改名会漂移, 靠 match 输出契约的稳定性承担.
- **一处刻意的浅**: 危险入口 (switch, --force) 刻意不做"聪明" — 不自动迁移, 不自动确认, 不合并进 birth. depth 原则让位于误触率: 危险操作的 interface 应当在敲下命令的那一刻就无可误会. 这是设计约束 (藏进通用入口算失败) 的直接体现, 不是疏忽.
- **被拒绝的替代**: 五个独立脚本 (复制五份探测/协议); 查询并入 birth (status 是唯一无副作用入口, 独立才好测好用); birth 内藏换母体 (危险平庸化); provider 抽象层 (D022 已否).
