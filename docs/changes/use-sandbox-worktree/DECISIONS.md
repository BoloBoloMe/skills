# use-sandbox-worktree 决策账本

## 决策

### D001 读通道: 真远端完全不暴露, 容器一切 git 读走 gate 镜像
- 状态: 已替代 (→ D007)
- 约束性: 必须遵守
- 内容: 容器的 clone/fetch 全部指向 gate, 网络白名单只放行 gate 端口; 真远端对容器连只读都不暴露. 理由: T7b 教训下真远端对容器"fetch 通但 push 拒"的半暴露状态徒增攻击面无收益; gate 是真远端完整镜像, 读全分支无损. 代价: 容器看到的"远端"新鲜度受 gate 同步策略限制, 由 D002/D003 对冲.
- 依赖事实: F002, F003
- 预计影响: use-sandbox-worktree skill 诞生步骤 (容器 git remote 配置, 白名单盘点)

### D002 gate 读侧同步时机: 诞生同步 + 明说更新 + 新会话重置顺带 fetch
- 状态: 已废弃 (MILESTONE-02 盘问, 2026-09-03)
- 约束性: 必须遵守
- 内容: gate 从真远端 fetch 的触发点只有三个: (1) sandbox-worktree 诞生时初始同步; (2) 用户明说"更新"时 host llm 手动 fetch; (3) 每新会话重置 sandbox/work 起点时顺带 fetch. 明确不做定时轮询 — 轮询是容器外的隐式变化, 违背"容器之外用户说了算".
- 依赖事实: F002
- 预计影响: 废弃原因: gate 形态从独立 clone 改为主仓 linked worktree (母体, D007), "gate 从真远端 fetch" 概念消亡 — 主分支进度由 host llm 在主仓直接管理; "每新会话重置 sandbox/work 起点" 被用户否定 (未合流提交会被静默抛弃), 由 D009 取代.

### D003 freshness 可观测: gate 每次同步记录 base commit + fetched_at
- 状态: 已废弃 (MILESTONE-02 盘问 Q12, 用户选撤销)
- 约束性: 必须遵守
- 内容: gate 每次从真远端同步后, 记录 base commit 与 fetched_at, 容器内可查 — agent 始终能知道自己基于多旧的快照, 不自知陈旧的静默状态被排除. 不强制 agent 基于最新 main 工作 (用户工作流: 工作树分支推进到可上线程度才合并主分支, 半成品/未完成 QA 的改动不进主分支, 故"最新 main"不是硬要求).
- 依赖事实: F005
- 预计影响: 废弃原因: 新模型下容器只感知母体, 每次诞生克隆的基底即母体当时现状, "运行中基底偷偷变旧" 场景消失, 反方攻击成立前提被消解; 用户判定容器不必也无法观测主分支, 母体侧也不记录 base/fetched_at.

### D004 gate 服务形态: 每 gate 专属 git daemon, 拓扑纪律兜底
- 状态: 已替代 (→ D008)
- 约束性: 必须遵守
- 内容: gate 用 `git daemon --enable=receive-pack` 服务, 不用 git-over-ssh. 附加纪律: 每 sandbox-worktree 一个专属 daemon 进程, base-path 仅含本 gate 仓, 不开 `--export-all`, 端口动态分配, daemon 随容器生灭. 排除 ssh 的理由: 私钥须进容器 = 凭据泄漏面 (与 host↔真远端共用密钥直接判死); ssh 默认可对用户有写权限的任意路径跑 git-receive-pack, 锁路径要 authorized_keys forced command, 复杂度白付. 已认知限制: daemon 无身份认证/审计能力, 威胁模型仅覆盖"单容器单 gate, 本机 netns 白名单, 防容器 agent 绕过钩子"; 未来若要会话级审计或多 gate 互隔需重审 (多 gate 并发在未决迷雾).
- 依赖事实: F002, F003
- 预计影响: 替代说明: daemon 形态, 随容器生灭, 不开 --export-all, 无认证威胁模型全部保留进 D008; 变化处: base-path 从 "独立 gate 仓" 变为主仓本身 (母体模型), 写面收敛手段从 pre-receive 钩子变为主仓 config.

### D005 gate 干净保障: 专用目录纪律 + host 兜底, 不做权限强制
- 状态: 已替代 (→ D007)
- 约束性: 必须遵守
- 内容: gate = host 上独立 clone 的专用目录 (非 git worktree 形态 — 共享 hooks 目录会误伤主仓), 角色钉死为"纯落地窗口": 人工审阅只读/diff/可编译试跑 (实测未跟踪产物不阻塞 push), 禁止编辑跟踪文件, 审阅时不开会自动写文件的工具 (IDE 格式化等). 兜底: host llm 诞生时初始化并校验干净; 运行期 agent push 失败回流 host 会话时, host llm 诊断 `git -C <gate> status` 并修复. 拒绝"接收/审阅目录分离"方案: 它只多防"违反纪律编辑跟踪文件"一种事故, 代价是丢掉 updateInstead "push 即落地可运行"的二合一甜头. 拒绝权限强制 (目录对人只读): 碍审阅试跑.
- 依赖事实: F001, F004
- 预计影响: 替代说明: 用户否决独立 clone, 改拍 gate = 主仓 linked worktree (母体), 共享 hooks 问题的解法是 "不加 hooks" (D008); updateInstead 脏树拒 push 的原生行为在母体上仍然成立 (母体工作区跟踪文件脏 → 容器 push 被拒, 原生报错).

### D006 报错透明化: 所有拒绝路径都要人话
- 状态: 已替代 (→ D008)
- 约束性: 必须遵守
- 内容: pre-receive 钩子 stderr 写人话回传 push 方 (如 "拒: 仅收 refs/heads/sandbox/work 的 ff push"); 透明化须覆盖所有拒绝路径, 不止自定义钩子 — 脏工作树路径由 updateInstead 原生报错 "Working directory has unstaged changes" 兜底 (半可读, 实测), 其余路径 (网络失败/同步失败) 在 MILESTONE-03 实现时逐项核对.
- 依赖事实: F001
- 预计影响: 替代说明: 无 hooks 拓扑 (D008) 下自定义钩子不存在, 拒绝信息退回 git 原生英文 (`deny updating a hidden ref` / `denying non-fast-forward` 等, F007 实测矩阵); 透明化改由 skill 文档附原生报错译解表承担.

### D007 母体模型: gate = 主仓 linked worktree, 容器代码的克隆源与落地窗口二合一
- 状态: 当前有效
- 约束性: 必须遵守
- 替代: D001, D005
- 内容: gate 重定义为**母体**: 主仓的 linked worktree (use-worktree 所建的工作树分支). 诞生时 host llm 调 use-worktree 建工作树分支作母体 (或复用现有母体, 见 D010); 容器诞生时经 git 守护进程 `git clone -b <母体分支>` 克隆母体为代码母体; 容器工作成果 push 直写主仓 `refs/heads/<母体分支>`, 推送落地 (updateInstead) 让母体目录文件即时更新为 agent 成果, host 直接审阅/试跑. 真远端对容器完全不暴露 (D001 此部分保留). 一名贯穿: 母体分支名 = worktree 目录名 = 容器名 = 容器 label 标识 (澄清 2026-09-06: 本条适用单容器缺省名; 多容器情形身份规则由 D031 细化, 母体 id + 容器实例名两层). 理由: 用户判定独立 clone 中转层多余, 砍层; 实测 updateInstead 识别 linked worktree 当前分支并即时更新其工作区 (F007). 代价: 主仓成为 receive 端, 写面收敛全靠主仓 config (D008); 母体工作区跟踪文件脏会拒容器 push (updateInstead 原生行为, F001 同构).
- 依赖事实: F007
- 预计影响: use-sandbox-worktree skill 诞生/存续/终结全部步骤; MILESTONE-03 瘦闭环编排脚本
- 需要调整: 按 D005 旧模型写的 gate 独立 clone 初始化流程 (尚无实现)

### D008 无 hooks 写面收敛: 主仓 config 模板 + 每容器专属守护进程
- 状态: 当前有效
- 约束性: 必须遵守
- 替代: D004, D006
- 内容: 不加任何 git 钩子, 写面收敛由主仓 config 承担 (F007 实测模板):
  ```ini
  [receive]
      denyCurrentBranch = updateInstead
      denyNonFastForwards = true
      denyDeletes = true
      hideRefs = refs/heads
      hideRefs = !refs/heads/<母体分支>
      hideRefs = refs/tags
  [uploadpack]
      hideRefs = refs/heads
      hideRefs = !refs/heads/<母体分支>
      hideRefs = refs/tags
  ```
  收敛结果: 容器写面 = 仅母体分支的 fast-forward push; 读面 ref 广告 = 仅母体分支. 守护进程沿用 D004 保留部分: 每容器一个专属 `git daemon --enable=receive-pack`, base-path 仅含主仓, 不开 `--export-all` (F003 拓扑铁律), 端口动态分配, 随容器生灭, 无认证 (威胁模型沿用: 防容器 agent, host 本地调用者受信). 已接受残余: (1) HEAD 协议广告藏不掉, 容器物理可读 main tip 对象 — 比完整镜像轻, 用户知情接受; (2) 拒绝信息为 git 原生英文, skill 文档附译解表 (D006 降级); (3) config 常驻主仓, 只约束主仓作 receive 端, 用户日常 push 真远端无影响 (F007 实测), 但用户手动 push 进主仓会被拒, 需文档明示; (4) `!` 否定例外语法依赖 git 版本 (2.53 实测过), 部署时须重验. 已排除: per-worktree core.hooksPath (实测不被 daemon receive-pack 采用); REMOTE_ADDR 分流钩子 (本地可注入伪造, 且用户明确不要 hooks).
- 依赖事实: F003, F007
- 预计影响: use-sandbox-worktree skill 诞生步骤 (config 写入/守护进程拉起); 容器镜像内 skill 文档 (译解表)

### D009 容器分支语义: 与母体同名, 跨容器累积, 无 reset
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 容器内工作分支与母体分支同名 (旧约定 `sandbox/work` 废弃). 分支跨容器累积: 容器灭后重建, 从母体本地版本重新克隆继续 (用户原话: 取 host 工作树分支的本地版本作新容器代码母体). 无任何自动 reset/rebase — 旧决策 "每新会话重置起点" 被用户否决 (未合流提交会被静默抛弃). 容器不感知主分支, 无新鲜度观测 (D003 已废弃). 合流主分支, 换基底纯 host 侧操作: 用户/host llm 在主仓管理主分支进度与母体内容, 容器不参与. 多容器共推同一母体时 non-ff 相拒的消化: 容器内 llm fetch 同步 → 解冲突 → 重推 (git 原生 ff 串行化, 无新机制).
- 依赖事实: F005
- 预计影响: use-sandbox-worktree skill 诞生步骤 (克隆/分支检出); 容器镜像内 skill 文档 (冲突消化指引)

### D010 单活动母体不变量与母体复用语义
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: **不变量**: 同一主仓同一时刻至多一个活动母体 (有存活容器/守护进程的母体). 多容器共享同一母体: 允许 (D009 冲突消化). 母体存活/删除/复用与 sandbox-worktree 解耦, 用户自决 — 含已合流主分支的旧母体跨时复用, 含一个母体同时作多个容器的母体. 换活动母体 = host 侧原子操作: 停旧母体全部容器/守护进程 → 校验 ref 与工作区干净 → 改 hideRefs 例外分支 → 拉起新端点. **不支持**同仓两个不同母体同时活跃: 主仓 config 是全局策略, 守护进程无认证, 无法表达 "容器 A→母体 A, 容器 B→母体 B" 的授权映射 (F008 反方攻击成立项, 高置信); 未来真需要须重开 receiver 隔离 (独立 clone 或钩子), 已入未决迷雾.
- 依赖事实: F007, F008
- 预计影响: use-sandbox-worktree skill 诞生步骤 (活动母体检测/切换操作); 迷雾回访时的重审入口

### D011 入口默认行为与 fail-closed 恢复
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: use-sandbox-worktree 被调用时的默认行为: (1) 检查当前是否处于 worktree 目录; (2) 按容器 label 查该目录是否已有容器实例; (3) 有 → 询问用户是否重启, 确认后按 fail-closed 序列重启: 注入 nft 白名单规则 → 拉起守护进程 → 校验 → 最后 start 容器 (规则未就绪前容器工作负载不运行 — `stop/start` 后 netns 重建规则全失, 容器不得抢跑, F008 反方攻击成立项); (4) 无 → 走诞生流程新建. 不用 `--restart=always`, 无 systemd 自启 unit — 恢复时机 = 用户下次调用 skill 并经确认. 端口策略: 宿主端口 create 时动态分配, 跨 stop/start/restart 稳定, 不记录, 用 `podman port` 查; 端口被占时 start 失败 (原生报错透明), 不自动换端口, 须重建容器或释放端口.
- 依赖事实: F006, F008
- 预计影响: use-sandbox-worktree skill 入口流程与恢复序列; MILESTONE-03 编排脚本

### D012 终结流程: 脏检查阻塞 + 母体存删用户自决
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 拆 sandbox-worktree 时先脏检查: ssh 入容器查未 push 工作 (未 commit 改动/未 push commit), 脏 → 阻塞提示, 用户明示才强拆; 干净或确认后 rm 容器 (守护进程随灭). 母体目录不随终结删除, 存续/删除由用户自决. 理由: 容器内未 push 工作 rm 后不可恢复 (容器层消失); 母体是用户的审阅现场与复用资产 (D010).
- 预计影响: use-sandbox-worktree skill 终结步骤

### D013 镜像换版时存活容器处置
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 镜像出新版时不动存活容器生; 诞生时比对镜像 digest (MILESTONE-05 结论: digest 精确版本), 有新版 → 提示用户 "是否终结重建", 决定权在用户, 绝不自动拆在跑的容器.
- 依赖事实: 无 (镜像 digest 版本语义来自 MILESTONE-05 外部产物, 非本账本事实)
- 预计影响: use-sandbox-worktree skill 诞生步骤 (镜像比对提示)

### D014 两层镜像结构与门禁扩展归属
- 状态: 部分修订 (层数 → D039 三层; 扩展名单 → D043 repetition-guard 改判进容器; 其余有效)
- 约束性: 必须遵守
- 内容: 镜像分两层. **base 层**固定且跨项目共享: OS + pi CLI + skill 库全量 (含 access-web) + fd/rg 等 bin; **项目层**由 host llm 读项目信号 (AGENTS.md/README/package.json/pyproject.toml 等) 推导依赖件叠加. 诞生时向用户展示推导清单, 确认后才构建 ("容器之外用户说了算"). 门禁类扩展 (filesystem-operation-gate, git-operation-gate, python-operation-hook, repetition-guard) **留 host 不进容器** — 回归调研 §3 原结论 (2026-09-01-research.md: 容器内 pi 不装门禁类扩展), 反方攻击成立项: gate 弹确认会阻塞 herdr 委派回路, 且容器内硬约束已由 D008 daemon/config 拓扑承担, gate 扩展在容器内只增行为耦合. 排除单层自由推导: base 复用率低. 构建期安装项目依赖的传递依赖/postinstall 风险与日常开发同级 (装依赖即工作流目的), 不入威胁模型, 但清单确认时应提示.
- 预计影响: MILESTONE-07 镜像制备实现; use-sandbox-worktree skill 诞生步骤 (清单确认环节)

### D015 镜像版本语义与清单格式
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 不做语义版本. tag = 构建日期-当日序号 (如 2026.09.05-1), 纯人读索引; digest = 精确版本, 落 image label (MILESTONE-05 结论). 新旧判定不靠 tag, 靠需求清单 vs 内容物清单比对. 清单条目 = 名称 + 版本谓词 (如 node>=20); contents.md = 构建后**实测**版本清单 — 反方攻击成立项: 无版本谓词的名称 subset 判不了运行时版本满足, 且 label 声明不是内容证明, 内容物必须实测.
- 依赖事实: MILESTONE-05 findings (外部产物)
- 预计影响: MILESTONE-07 (清单生成/比对实现)

### D016 记录位置与项目身份规则
- 状态: 已替代 (→ D024, 仅记录位置路径变更; 身份规则不变由 D024 承接)
- 约束性: 必须遵守
- 替代说明: 记录根目录由 `~/.pi/sandbox-worktree/` 改为 `~/.agents/sandbox-worktree/` (用户拍板 2026-09-04). 尚无实现, 无代码需调整. 以下原文保留:
- 内容: 构建输入 (Containerfile) + 需求清单 requirements.md + 实测内容物清单 contents.md 落 `~/.pi/sandbox-worktree/<project-slug>/builds/<build-id>/` (环境信息不落项目 git). label 前缀 `run.sandbox-worktree.*`: image 存 project-id/schema-version/contents-digest/build-id/base-digest; 容器存 identity/worktree-path/image-digest (MILESTONE-05 结论的落地). **身份规则**: project-id = 主仓绝对路径 (唯一主键, 防同名目录碰撞); slug = 目录名规范化, 仅作展示索引与目录名, 冲突时加短 hash; build-id 构建前查重 (防两会话并发同号).
- 预计影响: MILESTONE-07; skill 诞生步骤 (镜像查询/构建记录)

### D025 场景脚本总体形态: 单 module `swt` 五子命令
- 状态: 部分修订 (→ D041: 新增诊断子命令 display-check, 不改资源状态; 五子命令生命周期本体有效)
- 约束性: 必须遵守
- 内容: host 侧生命周期编排收敛为**一个 module** (`workflow/use-sandbox-worktree/scripts/swt.py`), 对外五个子命令: `birth` (诞生: 建/复用母体 + config + daemon + nft + 容器就绪) / `resume` (恢复, 带 DECIDE gate, 见 D030) / `status` (只读盘点, 永不改状态) / `terminate` (按容器终结, D029) / `switch` (换活动母体, 独立危险入口, D028). 五场景共享同一套探测, D008 config 模板, runtime 状态文件与输出协议, 拆成五个独立脚本会把它们复制五份 (locality 崩坏), 故为单 module 五子命令. 形态经 Design It Twice 三分支比较拍板 ([design-min](milestone-11-design-min.md) 2 入口 / [design-flex](milestone-11-design-flex.md) 9 入口 / [design-caller](milestone-11-design-caller.md) 5 子命令), 取 caller 骨架. 与现有脚本的关系: image-prep.py / net-firewall.py 复用不吞并 (各自 interface 已被 M04/M07 测试钉住, 包一层是透传浅 module); login-wall.py 不统辖 (登录墙是存续期可选环节); e2e-smoke.py 下沉缓退役 (D036). 目标定位: 显式 `--repo` 优先, 缺省从 cwd 推导主仓 (`git rev-parse --git-common-dir`), **废弃 M03 的跨命令注册表索引契约** (M03 遗留缺口 (1) 就此消解: 多一份跨命令状态 = 多一类不一致). 命名消歧: 容器内已有 swt-vnc (M09), SKILL.md 首次出现处各写全称.
- 依赖事实: F006, F007, F011
- 预计影响: MILESTONE-12 实现本体; MILESTONE-10 SKILL.md 引用

### D026 用户决策协议: DECIDE + 决策收据 (指纹绑定)
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 脚本非交互 (不读 stdin), 一切用户拍板点表达为 **exit 1 + stdout `DECIDE` 行**, llm 原样转述用户, 用户答后带 flag 重跑同一子命令. 规则四条: (1) **一次列全**: 在首次改变任何资源之前, 列出当前所有可知待决问题, 不挤牙膏; 执行中途新冒出的问题不算 DECIDE, 走 exit 3 PARTIAL 语义. (2) **决策收据**: 每个 DECIDE 生成一次性票据 (decision id) 并绑定资源指纹 — 主仓绝对路径 / 母体分支+ref tip / 容器 Podman ID (非可复用 name) / 镜像 digest / config 指纹 / 网络模式与规则输入 / 脏计数 / 全部受影响容器清单 / (switch 时) 目标分支; 重跑时拿锁 (D034) 后 compare-and-swap 比对指纹并消费票据 (一次性, 不可复用), 任一字段变了 → 重新 DECIDE 或 FAIL, **绝不把旧答案静默套到新状态上** (反方攻击成立项: 无指纹则用户确认拆的是容器 A, 实际可能拆了同名重建的 B). (3) **已答不重问**: 已答决策记入 runtime, 重入重探测仅当其前提字段变化才重问. (4) DECIDE 走 stdout 不是错误, exit code 语义见 D027. 理由: 决策权在用户 + 脚本非交互两条约束的合取; 指纹机制同时覆盖文件锁不跨 DECIDE 空窗的缺口.
- 依赖事实: F011
- 预计影响: MILESTONE-12 (decision 协议实现); SKILL.md (确认话术节)

### D027 exit code 协议与输出契约
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 全子命令统一: **0** 成功 (含幂等 no-op); **1** DECIDE 待用户 (D026); **2** 前置不满足 — 严格限定为**尚未创建/改动任何资源**的预检失败, 状态未变, 调用方别重试同一命令; **3** 中途失败可重入 — 凡是动过状态之后的失败全归此类 (含端口被占: F006 实测 start 失败留下 exited 容器, 已动状态, 不属 exit 2 — 反方攻击成立项), 已完成阶段登记 runtime; 已定义的常规半状态重跑同一命令幂等收敛, 不可自动收敛的半状态由 PARTIAL 文案列出唯一人工恢复路径 (D037), 不空泛承诺 "重跑必收敛"; **4** 环境错误 (podman/git/nft 缺失或版本不支持, 含 D008 `!` 语法重验失败). 输出: stdout 进度行人话 + 末行 `STATE {...}` 单行 json (五子命令共用 schema, 带版本号, 只加字段不改名, 沿用 M09 login-wall up 先例); stderr 首行机器标签 (`FAIL`/`PARTIAL`/`ENV` + 人话), git/podman 原生报错原文透传不吞不译 (译解表归 SKILL.md, D006 降级精神, 防两处漂移).
- 依赖事实: F006, F011
- 预计影响: MILESTONE-12; SKILL.md (exit 表 + 译解表)

### D028 危险操作显式独立
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 换母体 = 独立 `switch` 子命令 (D010 原子序: 停旧全部容器/daemon → 校验 ref 与工作区干净 → 改 hideRefs 例外 → 拉起新端点); 强拆 = `terminate --force` 独立 flag, 先审计登记 (判决快照: 谁/何时/脏概要) 再删. 拒绝把换母体藏进 birth/up 的决策点 (design-min 分支形态): 停全部容器 + 改主仓全局 config 是危险复合操作, interface 应当在敲下命令那一刻就无可误会, 藏进通用入口算设计失败. 危险入口刻意不做 "聪明": 不自动迁移, 不自动确认.
- 依赖事实: F011
- 预计影响: MILESTONE-12; SKILL.md

### D029 terminate 按容器粒度与脏检查口径
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: `terminate --repo <主仓> [--name <容器名>] [--force]`, 按容器粒度 (共享母体 D009 时按母体一次拆光会误伤兄弟容器), `--name` 缺省 = 该母体唯一容器, 多容器时必填. 脏检查口径定稿: 未 push = `git rev-list --count <母体ref>..HEAD`; ahead/behind/diverged 关系用 ancestor 检查区分 (`git merge-base --is-ancestor`): HEAD 是 ref 的祖先 → 纯 behind 不算脏 (落后于母体不丢数据); ref 是 HEAD 的祖先 → 纯 ahead, 算脏; 互为非祖先 → diverged, 算脏; STATE 与 DECIDE 文案分别给出 ahead/behind/diverged 关系与计数; 未提交含未跟踪文件; ssh 不可达或容器已停 → 脏度 unknown **视同脏** 阻塞. TOCTOU 残余 (检查到 rm 之间容器内 agent 可能还在写) 的处理: DECIDE 文案要求用户确认容器内 agent 已停手 + 决策收据含脏计数, 重跑必重查 (D026); 残余窗口知情接受. 成功后: rm 容器, 收该容器 daemon, nft 按 D032 规则, **母体保留** (D012), 主仓 config 不动.
- 依赖事实: F011
- 预计影响: MILESTONE-12; SKILL.md (停手确认话术)

### D030 resume 带 DECIDE gate, D011 确认义务落代码
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: `resume` 有 CLI 级 DECIDE gate: 检测到可恢复对象 (停着的容器/stale daemon/缺规则) 时 exit 1, 决策收据绑定容器 Podman ID + 当前授权母体分支; 用户确认后带 flag 重跑, 按 D011 fail-closed 序列执行, 时序以 M04 实测为准 (F-M04-02: netns 在首个容器 start 前不存在, 落地 = 收 stale daemon → start 容器 → **start 后立即注入 nft 并校验 daemon, 校验通过前不开放 agent 工作负载**; D011 的排序精神 "规则未就绪工作负载不跑" 由此保全, 字面 "先注入后 start" 已被 F-M04-02 修订). 推翻 design-caller 的 "resume 无 gate, 确认由 skill 层承担" — 反方攻击成立: 那正好把 D011 的确认义务退回给 llm 自觉, 是脚本化方向要消灭的漏项; resume 会杀进程, 重建网络规则, 重启工作负载, 绝非无副作用. resume 同时校验 runtime 记录的母体分支仍是当前全局授权分支, 否则拒绝 (防 switch 后旧容器在新授权域下被拉起, 配合 D033).
- 依赖事实: F008, F011
- 预计影响: MILESTONE-12; SKILL.md 恢复节

### D031 多容器两层身份: 母体 id + 容器实例名
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: D009 允许同母体多容器, 与 D007 一名贯穿 (容器名 = 母体 slug) 冲突 (反方攻击成立项: 同母体第二次 birth 撞 podman name). 解法: 身份分两层 — 母体 id (分支名 = worktree 目录名, 不变) + 容器实例名. `birth` 加可选 `--name`, 缺省 `swt-<slug>` (单容器情形一名贯穿保留), 撞名 exit 2 要求显式命名. 容器 label 同时存母体 id 与实例名, runtime 记录同. 拒绝 v1 收窄为单容器 (birth 拒第二容器): D009 是已拍板语义, 且 D032/D033 的修复都以多容器存在为前提, 身份分离是共同地基, 实现增量小.
- 依赖事实: F011
- 预计影响: MILESTONE-12; D024 容器 label (identity 拆两层); SKILL.md

### D032 nft 共享表按容器归属, net-firewall 扩展入 M12 范围
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 反方攻击发现的确定性冲突: 现有 net-firewall.py 的 `clear` 删整张 `inet swt` 表, `apply` 见表中已有其他容器源地址即拒 (APPLY-CONFLICT) — 多容器下同母体兄弟容器的终结/恢复会互删网络保护. 决策: net-firewall.py 扩展**按容器源地址删除规则**的能力 (或锁内按剩余容器全量重渲染), 仅最后一个容器消失才删整表; resume 在共享表场景不得走 clear+apply (窗口内会清掉兄弟规则). 此扩展属 MILESTONE-12 范围 (M04 module 的 interface 演进, 其既有测试保持绿).
- 依赖事实: F011
- 预计影响: MILESTONE-12 (net-firewall.py 接口扩展 + swt 编排)

### D033 switch 后旧容器标记 retired
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: switch 停旧母体全部容器但**不删** (D010 不变), 停下的旧容器在 runtime 标记 **retired**: status 可见 (标 retired), `resume` 拒绝 retired 容器 (防旧容器在新全局授权域下被拉起, 看到/操作错误分支), 唯一出路是 `terminate` (走 D029 正常脏检查). 用户想把旧分支捡回来 → 对旧母体重新 switch 回去或 birth (经 D026 决策协议).
- 依赖事实: F011
- 预计影响: MILESTONE-12; SKILL.md switch 节

### D034 并发: 同主仓文件锁, 第二者 exit 2 不排队
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 同主仓的 swt 变更类调用持文件锁 (M03 fcntl 先例), 拿不到锁 exit 2 直接拒, 不排队 (排队等锁反而让第二会话拿到过时状态). DECIDE 两次调用之间的空窗不由锁保护 (进程退出锁即释放), 由 D026 决策收据的指纹比对覆盖.
- 预计影响: MILESTONE-12

### D035 镜像构建职责: birth 只判不建
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: birth 内部经 image-prep `match` 判镜像 (D017 匹配规则留在 image-prep); verdict=BUILD-NEW 即停出 DECIDE (附推导清单), 用户确认后由 llm 走 D014 流程跑 image-prep `build`, 再带 `--image <ref>` 重跑 birth. birth 不自动构建 — D014 的清单确认本就是会话环节, birth 吞了它会造出两条确认路径并存. 在跑容器镜像有新版只标 `newer-available` (D013), 绝不自动拆.
- 预计影响: MILESTONE-12; SKILL.md 诞生节

### D036 e2e-smoke 下沉但缓退役, 等价矩阵通过才删
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: M12 把 e2e-smoke.py 已实跑验证的阶段函数 (母体建立/config 写入与断言/daemon 拉起/脏检查/兜底清理) 下沉为 swt 的 implementation, 测试在 swt CLI 接口处重写 (替换不叠加精神). **但** e2e-smoke 保留为独立回归基线, 直到 swt 黑盒测试矩阵逐项等价 M03 证据全绿方可删除, 等价矩阵至少含: 拒绝矩阵 (新分支/tag/non-ff/删除), 母体脏树拒收, daemon 不带 --export-all, config 校验先于 daemon 启动, clone 检出母体分支, push 回流落地, D008 多值 config 的既有值/错值/幂等重跑, ssh 不可达与已停容器视同脏, 强拆审计登记, 中途清理与重复 birth, 多容器共享母体时互不影响的 resume/terminate/nft 规则, switch 中途失败与旧容器 retired — 且断言独立外部状态 (`git config --get-all` / `podman ps` / nft 表 / 母体文件落地), 不只信 swt 自己的 STATE. — 反方攻击成立项: 阶段函数下沉不自动继承覆盖, 提前退役会同时失去独立基线与负向断言. 此条写入 MILESTONE-12 完成判据. (对本会话先前提案 "直接退役" 的修正.)
- 依赖事实: F011
- 预计影响: MILESTONE-12 完成判据; e2e-smoke.py 生命周期

### D037 修复原语 (config/daemon 子命令) 不进 v1
- 状态: 当前有效
- 约束性: 可调整
- 内容: design-flex 分支的 `swt config apply|verify|revoke` 与 `swt daemon start|stop|probe` 修复原语不进 v1 interface. resume 已收敛常规残留态; 更深的救场由 llm 敲原生命令 (git config / pgrep / net-firewall show), 包一层是透传浅 module. 若 M12 实现或 M10 演练暴露真实救场需求, 可重开. 代价记录: exit 3 PARTIAL 的文案必须列出每种半状态的唯一人工恢复路径, 不能空泛承诺 "重跑必收敛".
- 依赖事实: F011
- 预计影响: MILESTONE-12 (PARTIAL 文案质量); 迷雾回访入口

### D038 脚本与 skill 文档的职责边界
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: **进脚本** (可执行断言防错): 状态探测, D008 config 模板写入/读回/快照回滚, D011 fail-closed 顺序, D010 单活动母体检查, D012 脏检查阻塞, D013 digest 比对提示, 决策收据协议, 审计登记, 并发锁. **留文档** (需人/agent 判断): 原生报错译解表 (D006 降级), 黑/白模式语义与域名盘点方法论, 多容器冲突消化指引 (D009, 容器内流程), 母体存删自决指引, D019 风险明示, D021 委派配方. 判据: 可执行断言防错的进代码, 需要判断的留文档, 同一知识不两处维护 (反方审查第 3 点). M03 checklist 决策点成熟度: 母体复用/黑白模式/脏放行/镜像换版成熟为 DECIDE+flag; 端口冲突不设决策点 (F006, exit 3 透传); base 更新判断留会话问答 (D020, 低频); 运行期新站点需求留迷雾.
- 预计影响: MILESTONE-12; MILESTONE-10 SKILL.md 结构

### D017 镜像匹配规则
- 状态: 部分修订 (谓词对象 → D039: 项目层硬性条件的比对对象从当前 base 改为当前 display; 规则本体有效)
- 约束性: 必须遵守
- 内容: `podman images --filter label=run.sandbox-worktree.project-id=<主仓路径>` 取候选 → digest 去重 (同镜像多 tag 会去重) → 按 build-id 排序取最新. 判定: 需求逐项**版本满足** (含谓词) + **base-digest = 当前 base** (硬谓词 — 反方攻击成立项: 用户更新 base 后旧项目镜像须自然淘汰, 不能仅靠提示) → 复用. 同名条目版本不满足即不可用; 多余项容忍; 缺任意项 → 推导新清单构建新版; 旧镜像保留不删 (GC 在未决迷雾).
- 预计影响: MILESTONE-07 (候选选择逻辑)

### D018 容器 home 复刻布局与 harness 注入
- 状态: 已替代 (→ D023, 仅 host 环境文档注入部分被推翻; 其余内容保留并由 D023 承接)
- 约束性: 必须遵守
- 替代说明: 原决策中 "~/docs, ~/AGENTS.md 机械复制进容器" 被用户推翻 (D023): 它们是 host 环境文档, 容器是独立环境, 注入即误导. 原决策其余部分 (home 路径字面相同/~/Workspace/<母体目录名>/~/.pi/agent 机械复制/auth.json ro 挂载/skills COPY/浏览器定位) 不变, 由 D023 完整承接. 以下原文保留:
- 内容: 容器用户 home **完美复刻** host 布局 (用户拍板): home 路径与 host 字面相同, `~/docs`, `~/AGENTS.md`, `~/Workspace/`, `~/.pi/agent` (settings/models/keybindings) 全部机械复制 — 根部 AGENTS.md 原样注入即生效, 零适配层. 代码固定 `~/Workspace/<母体目录名>` — use-worktree 所建的规范化目录名, 非原始分支名 (反方攻击成立项: `feature/foo` 分支名含斜杠会造成路径嵌套/非法容器名). skill 库全量 COPY 进 base: access-web 的 139M 大头是浏览器依赖, 容器内浏览器专为 agent 而设, 即容器唯一浏览器, 一份两用. auth.json **只读挂载**不烤进镜像层 (换 key 不重建镜像); sessions 不进容器.
- 预计影响: MILESTONE-07 (base 层 Containerfile, 挂载点); 容器内路径契约

### D019 auth.json 残余风险接受
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 只读挂载防写回 host, 不防读 — 容器内恶意依赖可读 token 并经白名单内的 LLM 域名外传/滥用 (与 D004 拒 ssh 私钥同类的凭据泄漏面, 但容器 agent 工作必需 LLM 凭据, 无法根除). 用户亲口确认接受该风险: 仅要求 skill 文档明示; **不配**独立可撤销 key (用户明确否决); 只读挂载即权衡后的最终选择.
- 预计影响: use-sandbox-worktree skill 文档 (风险明示段落)

### D020 base 层更新语义
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: base 仅在用户明说 "更新 base" 时重建, 无自动检测. 项目层镜像 label 记 base-digest, 诞生比对不一致仅提示不强制 (D013 精神: 不动存活容器, 决定权在用户); 匹配层 base-digest 硬谓词 (D017) 使旧 base 项目镜像自然被淘汰出候选.
- 预计影响: MILESTONE-07; skill 诞生步骤 (base 比对提示)

### D021 herdr 集成: 形态 d (host herdr + wrapper 提示) 与委派配方
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: **容器不装 herdr** — 诞生后 host 侧开 `HERDR_AGENT=pi ssh -p <动态端口> ...` 窗格接入 host herdr, 经进程 env 提示 + 屏幕清单把 ssh 后的 pi 识别为一等 agent (F009 实测). **委派配方**: (1) `agent get` 确认 idle, blocked 态不发 (反方修正: 无就绪 guard 会把键打进错误界面); (2) `pane send-text` 发任务文本; (3) 提交键 = 读容器内 keybindings.json 的 `tui.input.submit` 首键 — 键位即接口, 跟随用户配置 (本机为 `alt+\`), 兜底 alt+enter (pi followUp 排队键, 空闲等效提交); (4) `agent wait`/`agent read` 收结果. **定位收窄为交互式编排适配层** (反方攻击成立项): 无 task id/退出码/重试幂等, 不宣称协议级替代 subagent; 状态/重试/幂等契约入未决迷雾, M10 端到端演练回访. herdr 编排的编排者是 host 侧 (用户/host pi), 容器内 pi 不自治编排; 任务切分配方细节同入迷雾. 排除: host herdr socket 挂入容器 (`pane run` 在 host 执行 = 容器逃逸通道); 容器内自含 herdr (嵌套 multiplexer, 剪贴板/键位降级, 且同键位注入问题); 暂不结合 (用户已明确要集成).
- 依赖事实: F009, F010
- 预计影响: skill 存续步骤 (herdr 接入与委派配方); MILESTONE-10 演练场景

### D022 容器操作不做 provider 抽象层, 仅留文档级扩展点
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 不建 "接口 + 实现类" 式的容器 provider 抽象 (docker/podman 多态). 理由: (1) 同一场景同一时刻只绑一个 provider, 诞生时选定后全程复用, 运行期多态无收益; (2) 硬约束长在 podman rootless 特性上 (netavark/nft 白名单注入, rootless netns, Quadlet), docker 的网络模型不同, 抽象层必漏成抽象漏洞; (3) skill 是 markdown 驱动 llm 敲命令, 抽象层无代码宿主. 扩展点形态: skill 文档把所有容器命令收拢到单独一节, 未来换/加 provider 时只改该节. 动机记录: 留扩展点 + 架构整洁偏好.
- 预计影响: use-sandbox-worktree SKILL.md 结构 (容器命令独立一节)

### D023 容器不注入 host 环境文档 (~/AGENTS.md, ~/docs)
- 状态: 当前有效
- 约束性: 必须遵守
- 替代: D018 (部分)
- 内容: **不打**: `~/AGENTS.md` 与 `~/docs/*` 是记录 host 本身环境的文档 (host 软件指针/ssh/输入法/防火墙等设施说明), 容器是另一个独立环境, 注入即误导, 一律不进容器 (不 COPY 不挂载). 容器内 pi 的约定来源 = 项目仓自身 AGENTS.md (经母体克隆随代码到达) + `~/.pi/agent/AGENTS.md` (pi 用户级指令, 属 harness, 随 ~/.pi/agent 机械复制). 承接 D018 保留部分: 容器 home 布局复刻 host (home 路径字面相同), 代码固定 `~/Workspace/<母体目录名>` (use-worktree 规范化目录名), `~/.pi/agent` (settings/models/keybindings) 机械复制, skill 库全量 COPY 进 base (容器浏览器专为 agent, 即容器唯一浏览器), auth.json 只读挂载不烤镜像层, sessions 不进容器.
- 预计影响: MILESTONE-07 (base 层 Containerfile 与挂载点 — 剔除 ~/docs 与 ~/AGENTS.md); 容器内路径契约

### D024 记录位置修订: 落 ~/.agents/sandbox-worktree/
- 状态: 当前有效
- 约束性: 必须遵守
- 替代: D016
- 内容: 构建输入 (Containerfile) + 需求清单 requirements.md + 实测内容物清单 contents.md 落 `~/.agents/sandbox-worktree/<project-slug>/builds/<build-id>/` (环境信息不落项目 git; 与 skills 库同屋, 区别于 pi 运行时配置 ~/.pi). label 前缀 `run.sandbox-worktree.*`: image 存 project-id/schema-version/contents-digest/build-id/base-digest; 容器存 identity/worktree-path/image-digest. **身份规则** (承接 D016 不变): project-id = 主仓绝对路径 (唯一主键, 防同名目录碰撞); slug = 目录名规范化, 仅作展示索引与目录名, 冲突时加短 hash; build-id 构建前查重 (防两会话并发同号).
- 预计影响: MILESTONE-07; skill 诞生步骤 (镜像查询/构建记录)

### D039 三层镜像: base → display → 项目层
- 状态: 当前有效
- 约束性: 必须遵守
- 替代: ISSUE-04 的 "浏览器栈进项目层" 形态 (项目层不再直接 FROM base); D014 分层结构延伸; D017 谓词对象延伸 (项目层硬性条件从 "基于当前 base" 改为 "基于当前 display")
- 内容: 镜像分三层. **base 层**内容不变 (OS/git/sshd/node/pi CLI/uv/fd/rg/python3/herdr + skill 库 COPY + ~/.pi/agent 复制; 另烘配 sshd_config `SetEnv PATH=.../home/bolo/.local/bin/...` 使 ssh 非交互 shell 可解析 ~/.local/bin, 见 F012 — 实测 sshd 对每个会话重设 PATH 为编译缺省, 镜像 ENV 不生效); 新增 **display 层** FROM 当前 base, 内容 = image/requirements-browser.md 全量 (xvfb/x11vnc/websockify/noVNC/fonts-noto-cjk + playwright chromium + swt-vnc), 记录落 `<records-root>/display/builds/`; **项目层** FROM 当前 display. 匹配谓词链: display 层自身须基于当前 base (base-digest == 当前 base), 项目层须基于当前 display — base 更新后旧 display 自然淘汰 (DISPLAY-STALE), display 更新后旧项目镜像自然淘汰, D017 硬谓词的自然延伸. base 与 display 都只在用户明说时重建 (D020 延伸). 工具面: image-prep 新增 `build-display` 子命令与 `resolve_display`; match 在 display 缺失/过期时软失败 BUILD-NEW + reason (不硬崩), build 时硬报 NO-DISPLAY. 理由: 显示栈是环境不是项目依赖 (任何项目都可能撞登录墙, 处处可得消除独立容器割裂), 但 chromium 上游安全更新与 access-web 登录墙适配是镜像内容里搅动最频繁的部分 — 放进 base 会让最常变的内容住进最不该常变的层 (base 搅动半径 = 全部项目层陪葬, D017), 放进项目层又回到每项目重复安装; 独立中间层同时保住 "环境层处处都有" 与爆炸半径隔离 (display 搅动只淘汰项目层).
- 依赖事实: 反方报告 A4 (最常变内容放最稳定层的两难); M09 实测 (chromium 下载占浏览器栈构建大头; base 自身真实摆动频率高)
- 预计影响: image-prep (build-display/resolve_display/match/build); SKILL.md 镜像管理节; display 层构建记录

### D040 6080 回环发布 + shm-size + 显示栈自动拉起
- 状态: 当前有效
- 约束性: 必须遵守
- 替代: ISSUE-04 login-wall up 的 0.0.0.0 发布 + 临时容器形态
- 内容: swt 容器 create 固定 `-p 127.0.0.1:6080:6080` (只绑宿主回环, 局域网不可达) + `--shm-size=1g` (chromium 必需, A5 欠规格项); 宿主 6080 已被占 (多容器并存, D009) 时回落 `-p 127.0.0.1::6080` 动态回环端口 — 回环约束不动摇, noVNC URL 与隧道命令按实际端口交付 (STATE `vnc-port`). birth 启动后自动 `podman exec <容器> swt-vnc start`; resume 在与防火墙重注入同位置自动重拉. 交付固定附 noVNC URL + 局域网隧道命令. 理由: 反方 A1 — 常开无认证桌面通道对局域网 24/7 暴露不在任何已接受风险清单 (x11vnc -nopw; nft 管出向不纳入向发布), 而回环化修复近乎免费; 局域远程观看由现成 ssh 通道转发 (`ssh -p <宿主端口> -L 6080:127.0.0.1:<vnc宿主端口> bolo@<host-LAN-IP>`), 交付体验几乎不变, 责任面归零.
- 依赖事实: F012 (pasta 映射监听 *, 局域网可达); research §8 (--shm-size=1g); requirements-browser.md (swt-vnc 无认证三动作)
- 注: 多容器并存时的动态回落是对 "固定 6080" 字面与 D009 多容器语义的技术调和 (pasta 端口绑定互斥), 用户拍板的两条硬约束 (只绑回环, chromium shm) 不变.
- 预计影响: swt.py (create 参数/交付打印); SKILL.md 交付节/风险明示

### D041 显示栈 verify 门禁语义: birth 全量 + DECIDE, resume 秒级降级
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: login-wall.py 的通道检查 (noVNC HTTP/ws 握手/RFB banner + 空白基线 + 渲染基线 0.2 + headless 回切) 迁为独立模块 `scripts/swt-display.py`; swt 新增 **display-check** 子命令调用 (诊断用; 0 全过/1 检查未过/2 传输层失败, 非 DECIDE 语义, 不改状态不持锁). 门禁拆两级: **birth** 跑全量 verify (证明的是镜像常量, 人在场 fail-fast 合理), 失败出 DECIDE — 选项 继续只开终端 (`--display-continue`, 显示栈降级) / 重验一次 (`--display-recheck`) / 终结 (terminate); **resume** 只跑 swt-vnc status 级秒级检查 (自动重拉 + 三进程/端口确认), 失败降级 — STATE 标显示栈状态 + 汇报注明一行, 不阻断终端工作. 容器镜像未含 swt-vnc (旧镜像/极简镜像) → 显示栈缺席 (STATE 标 absent), 跳过检查不判失败. 对 D026 的修订: display-verify 是执行完成后的追加 DECIDE (票据绑定容器 podman-id + 镜像 digest), 不受 "首次改资源前一次列全" 约束 — 用户拍板的明示例外. 理由: 反方 A2/A3 — 防火墙规则是状态性的 (stop 后必然全失, 验不过 = 裸奔 = 必须挡), 显示栈能力是镜像性的 (birth 验过一次, 镜像不变则能力恒在); resume 全量渲染轮询重证已证常量, 且把偶发失败 (chrome 冷启动/轮询时序) 放在硬门禁上 = 让便利特性当全部工作负载的人质.
- 依赖事实: 反方报告 A2/A3 (类比不成立 + 门禁语义错位); M09 实测 (verify 六检查 31 用例全绿, 迁家即复用)
- 预计影响: swt-display.py (新模块); swt.py (display-check 子命令/birth 尾部门禁/resume 降级); SKILL.md 显示栈节

### D042 login-wall.py 整删, 测试迁家重写
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: `scripts/login-wall.py` 整删 (up/down/build 编排随独立登录墙容器形态一并废弃; 其 verify 通道检查已迁 swt-display.py, 见 D041). `tests/test_swt_m09.py` 重写适配: RFB/ws 帧纯逻辑测试原样改指 swt-display.py; 浏览器镜像 e2e 改跑 build-display (断言 display 层记录/labels/contents); 容器生命周期测试改用裸 podman run (回环发布 + shm 1g, swt birth 同型) 直驱 swt-vnc; verify e2e 改经 `swt display-check`.
- 依赖事实: 用户拍板 (决策 4)
- 预计影响: scripts/, tests/test_swt_m09.py

### D043 扩展过滤白名单心智
- 状态: 当前有效
- 约束性: 必须遵守
- 修订: D014 (门禁扩展名单: repetition-guard 从 "留 host" 改判 "进容器")
- 内容: image-prep 复制 ~/.pi/agent 时, extensions/ 只排除显式点名名单 — filesystem-operation-gate.ts / git-operation-gate.ts / python-operation-hook.ts (名单落 image-prep.py 注释), 其余扩展 (repetition-guard.ts, herdr-agent-state.ts) 与未来新扩展**默认进容器**, 留 host 才需点名 (白名单心智反向: 名单 = 留 host 名单). 理由: 容器内硬约束已由 daemon/config 拓扑承担 (D014), 门禁类扩展在容器内只增行为耦合, 这一定位不变; 但 repetition-guard/herdr-agent-state 属行为辅助非门禁, 随行走容器内 pi 的日常体验反而需要它们, 因除外面不是包含面.
- 依赖事实: 用户拍板 (决策 5); ~/.pi/agent/extensions 实测清单
- 预计影响: image-prep.py stage_context; SKILL.md 镜像管理节

### D044 auth.json 运行时只读挂载
- 状态: 已作废 (→ D046; F014 证伪: rootless uid_map 下 ro+0600 挂载使容器 bolo 永不可读)
- 约束性: 必须遵守
- 承接: D018/D019 (风险语义不变)
- 内容: swt 容器 create 加 `-v <host>/.pi/agent/auth.json:/home/bolo/.pi/agent/auth.json:ro`; host 缺失时跳过挂载并 stderr 警告 (不阻塞 birth); 镜像复制继续排除 auth.json (不烤镜像层, D018 不变); models-store.json 维持随 ~/.pi/agent 复制. 换 key 无需重建镜像或容器, 下次 create 自动带新值; 运行中容器不热换.
- 依赖事实: 用户拍板 (决策 6)
- 预计影响: swt.py create; SKILL.md 风险明示

### D045 容器不设内存/CPU 上限
- 状态: 当前有效
- 约束性: 默认如此
- 内容: 容器维持现状不设 `--memory`/`--cpus` 限额, 本条仅落簿记. 理由: 沙盒的隔离目标是网络出向与写面拓扑 (nft + daemon/config), 不是资源配额; 容器内是用户自己的 agent 工作负载 (构建/编译/测试), 限额只会制造人工饥饿. 若未来多容器互相挤占成为真问题, 再重开.
- 依赖事实: 用户拍板 (决策 7)
- 预计影响: SKILL.md 容器命令收拢节

## 事实

### F001 updateInstead 阻塞条件实测 (2026-09-01 后盘问会话)
- 状态: 当前有效
- 来源: 本地实测 (git init + receive.denyCurrentBranch=updateInstead, checkout sandbox/work 后 push)
- 内容: gate 检出分支为 sandbox/work 前提下: (1) 仓内存在未跟踪文件 (模拟编译产物) → push 正常接受, 不阻塞; (2) 跟踪文件有未暂存改动 → push 被拒, 原生报错 `Working directory has unstaged changes`; (3) 向非检出分支 push 完全不触发 updateInstead 检查 (第一次实测曾因此误报, 复测已修正).

### F002 门禁机制实测矩阵全过
- 状态: 已变更 (→ F007)
- 来源: docs/changes/use-sandbox-worktree/2026-09-01-research.md §4.2
- 内容: clone 读全 ref / sandbox/work 追加 push 接受 / non-ff 拒 / 新分支拒 / tag 拒 / 删分支拒 / 绕开 gate 直指真远端时协议层拒写. git 钩子只存在于写方向, 读方向天生开放. 变更说明: 该矩阵基于独立 clone + pre-receive 钩子拓扑 (D005 已替代); 新拓扑 (母体直连主仓, 无 hooks) 的等价实测矩阵见 F007.

### F003 T7b 拓扑教训
- 状态: 当前有效
- 来源: docs/changes/use-sandbox-worktree/2026-09-01-research.md §4.2
- 内容: git daemon `--export-all` 共享 base-path 时可经 9418 直接 push 写穿真远端绕过钩子. 门禁由拓扑保证, 不由钩子保证: real 仓绝不落在任何可写服务端点路径内. 新拓扑下的对应纪律: 守护进程 base-path 仅含主仓, 不开 `--export-all`, 真远端永不暴露给容器 (D008).

### F004 updateInstead "push 即落地"
- 状态: 当前有效
- 来源: docs/changes/use-sandbox-worktree/2026-09-01-research.md §4.3
- 内容: 非裸仓设 receive.denyCurrentBranch=updateInstead 后, 合规 push 被接受的瞬间 host 工作树文件自动更新成 agent 成果; 门禁与落地窗口二合一, 回流 = host 人工审阅该目录 → merge → push 真远端. F007 已复测确认该行为对 linked worktree 同样成立.

### F005 用户合并工作流
- 状态: 当前有效
- 来源: 用户陈述 (MILESTONE-01 盘问会话, 2026-09)
- 内容: 工作树分支推进到可以上线的程度才合并主分支; 半成品/未完成 QA 的改动不进主分支.

### F006 动态宿主端口行为实测 (2026-09-03, MILESTONE-02 盘问会话)
- 状态: 当前有效
- 来源: 本机 podman 实测 (alpine 容器, -p 8080 动态分配)
- 内容: (1) 动态宿主端口 create 时分配, stop/start/restart 全程不变 (实测 44869), 仅 rm 重建才变 — "restart 后端口会变" 的旧假设证伪, 端口不构成需记录的身份信息; (2) 启动时端口被占 → start 失败 exit 125, pasta 报 `Address already in use`, 容器停 exited 态, 不自动换端口.

### F007 worktree 拓扑实测矩阵 (2026-09-03, MILESTONE-02 盘问会话)
- 状态: 当前有效
- 来源: docs/changes/use-sandbox-worktree/milestone-02-worktree-topology-findings.md (git 2.53.0, /tmp 实验仓)
- 内容: (承接 F002 的新拓扑实测矩阵) (1) updateInstead 识别 linked worktree 当前分支, push 成功即更新该 worktree 工作区文件; (2) 无 hooks 默认写面 = 整仓 refs (non-ff/新分支/tag/删除普通分支全通, 仅当前分支删除受 denyDeleteCurrent 保护); (3) `receive.hideRefs = refs/heads` + `!refs/heads/<分支>` + `refs/tags` 配 denyNonFastForwards + denyDeletes 可把写面收敛为单分支 ff-only; (4) 正确配置键是 `receive.hideRefs`, `receivepack.hideRefs` 实测无效; (5) `uploadpack.hideRefs` 只控读广告不防 push, 且 HEAD 广告无法隐藏 (clone 默认 detached 在 main 对象, 须 `clone -b <分支>`); (6) per-worktree core.hooksPath 不被 daemon receive-pack 采用; (7) REMOTE_ADDR 可识别 daemon 来源但本地调用者可注入伪造, 不宜作安全凭据; (8) receive.* 配置只约束本仓作 receive 端, 不影响本仓作发送方 push 真远端, 不影响本地建分支.

### F008 MILESTONE-02 反方审查结论 (2026-09-03)
- 状态: 当前有效
- 来源: docs/changes/use-sandbox-worktree/milestone-02-opposing-review.md (opposing-viewpoint 对抗分析)
- 内容: (1) 高置信: 共享主仓 config 无法表达每容器/每守护进程的分支授权映射, 同仓出现两个不同活动母体时每容器单分支约束确定性失效 — 当前拓扑上限是单授权域, 已由 D010 单活动母体不变量采纳修正; (2) 中置信: `--restart=always` 独立抢跑 + 事后重注入 nft 存在 fail-open 网络裸奔窗口, 已由 D011 fail-closed 重启序列 (且废弃自动重启, 改 skill 入口询问式恢复) 采纳修正.

### F009 herdr 检测与委派机制实测 (2026-09-04, MILESTONE-06 盘问会话)
- 状态: 当前有效
- 来源: 本机 herdr 0.8.2 实测 + 官方文档 (herdr.dev/docs/agents) + 源码核查 (github.com/herdrdev/herdr)
- 内容: (1) herdr agent 识别 = host 进程存在性 + 屏幕清单 (TOML 规则匹配终端底部缓冲快照); ssh 后的 agent 默认不可见 (社区 issue #1170 同现象). (2) `HERDR_AGENT=<agent>` 环境提示 (0.7.1+ 内建, 读 wrapper 进程 /proc environ) 使 ssh 后的 pi 被识别为一等 agent — 实测 `HERDR_AGENT=pi ssh localhost` 后窗格识别为 pi/idle. (3) herdr 注入 Enter 为标准 `\r` (字节捕获实测), agent prompt/send-keys/pane run 同理; 提交是否生效取决于目标 pi 的 keybindings.json — 本机 `tui.input.submit=alt+\` 且 enter 被划给 newLine, 致注入的 enter 只插入换行 (用户定位根因, 非 herdr/pi bug). (4) 委派全链路实测成功: `pane send-text` 发任务 + `agent send-keys alt+\` 提交 → working → done → read 读回. (5) herdr agent kind 原生支持 pi; `herdr --remote` 是 attach 远端会话的 thin client 形态, 多容器不共 workspace, 不符合 "host 一个 workspace 总览多容器" 目标.

### F010 pi 非交互模式可作自动化保底 (2026-09-04)
- 状态: 当前有效
- 来源: 本机实测 (`pi -p "<任务>" --model glm-5.3-flash`, exit 0)
- 内容: `pi -p` 非交互模式 (处理 prompt 后退出) 可用; host 经 ssh + herdr `pane run`/`pane wait-output` 编排容器内 pi 批处理任务, 可完全绕开 TUI 键位注入, 是委派回路 (D021) 失效时的保底形态. 代价: 失去交互 TUI, 一轮一进程.

### F011 MILESTONE-11 反方审查结论 (2026-09-06)
- 状态: 当前有效
- 来源: docs/changes/use-sandbox-worktree/milestone-11-opposing-review.md (opposing-viewpoint 对抗分析, gpt-5.6-luna; 产出方为 glm-5.3-flash 三设计分支, 对抗对不同模型)
- 内容: 对五场景方案 (Design It Twice 三分支 + 用户拍板的 caller 骨架混合案) 的反方攻击, 10 项攻击 9 项成立或部分成立, 全部已转为修正: (1)(3) DECIDE 重探测与决策不过期矛盾 + 锁不跨空窗 → D026 决策收据指纹; (2) 一次列全与示例矛盾 → D026 定义收紧 (首次改状态前列全); (4) 端口被占非 exit 2 → D027 exit 2/3 重划; (5) resume 无 gate 违背 D011 → D030; (6) net-firewall clear 删共享整表与多容器冲突 (硬事实) → D032; (7) 多容器身份未落地 → D031; (8) switch 后旧容器 resume 归属丢失 → D033; (9) 脏检查 ahead/behind 与 TOCTOU → D029 (behind 不算脏, 残余窗口知情接受); (10) 下沉不继承覆盖 → D036 缓退役.

### F012 M10 演练 ssh 入口踩坑三连 (2026-09-10, birth 交付后实测)
- 状态: 当前有效
- 来源: M10 全链演练本会话实测 (base 2026.09.09-3, 项目层 skills:2026.09.10-1, blacklist)
- 内容: (1) **pasta 下容器无独立 IP**: STATE `network-ip` 实测 = host 本机 LAN IP (192.168.31.252), birth 交付的 "容器 IP: ssh bolo@<IP>" 直连 22 必撞 host 自身 sshd — 已知 host key 报 "known by other names", ssh-agent 多 key 试满 MaxAuthTries 报 "Too many authentication failures", 密码都轮不到. 修复方向: birth 交付逻辑检测 network-ip == host IP 时改打 "本机 127.0.0.1:<port> / 局域网 <host-LAN-IP>:<port>" 两条带端口入口 (映射端口本就监听 *, 远程机同样走端口); SKILL.md 第四步同步措辞并要求交付前 `podman port` 核对. (2) **容器 ssh 非交互 shell PATH 缺 ~/.local/bin**: herdr remote 自动装远端 binary 到 ~/.local/bin/herdr 后报 "remote shell does not resolve herdr to that path". 修复方向: base 镜像烘配 PATH (下次用户明说重建 base 时带上). (3) **herdr --remote 在已有 herdr 会话内被套娃禁用拦下** ("nested herdr is disabled by default"): SKILL.md herdr remote 节需注明该命令须在非 herdr 终端运行, 已在 herdr 里则走开窗格配方. 另: 本次 birth 前发现主仓 config 残留上一次演练的 uploadpack.hideRefs 旧值 (指向已删旧分支), birth 拒覆盖 exit 2, 手工 `git config --unset-all uploadpack.hideRefs` 后重跑即过 — 修配置归属前的救场路径, 值得在 SKILL.md 救场节补一笔. 修复执行时点: M10 全链跑完后统一改 (演练中途不改被测对象).

### F013 构建期 root 写 bolo home 的属主残留 (2026-09-11, M10 重跑实测)
- 状态: 当前有效
- 来源: M10 全链重跑, herdr --remote 进容器实测暴露
- 内容: display 层 chromium 安装以 root + `HOME=/home/bolo` 跑 `playwright install --with-deps chromium`, 除 `.cache` 外还会在 `/home/bolo/.local/share/pki` 建 nssdb, 在 `/home/bolo/.config` 建 google-chrome-for-testing, 全部 root 属主 700 — bolo 对自身 `~/.local`/`~/.config` 无写权限, 直接炸 herdr remote (装二进制 mkdir `.local` 拒; server status 连 `~/.config/herdr/herdr.sock` EACCES) 及一切写这两个目录的运行时软件. 且这两个目录非必现 (有缓存的重建不产生), 修复不能写无条件 chown. 修复: requirements-browser.md chromium 安装行 `.cache` 无条件 chown + `.local`/`.config` 存在才 chown; display 层 2026.09.11-2 与 skills 项目层 2026.09.11-2 已带修复重建. 教训普适化: 任何以 root 跑且 HOME 指 bolo 的构建步骤, 收尾必须把它可能写的 home 子树全量 chown 回 bolo, 且按 "存在才处理" 写法.

### D046 auth.json 启动后注入 (替代 D044 只读挂载)
- 状态: 当前有效
- 约束性: 必须遵守
- 替代: D044 (ro bind mount) — F014 实测证伪
- 内容: swt 不再在 create 挂 `-v auth.json:ro`; 改为 birth/resume 容器启动后经 `podman exec -i ... sh -c 'install -d -o bolo -g bolo; cat > auth.json; chown bolo:bolo; chmod 600' < host-auth.json` 注入. 语义对照 D044: 不烤镜像层 (仍由 D018 排除) ✓; 防写回 host 更强 (拷贝物理隔离, 容器内随便改都到不了 host) ✓; host 缺失跳过并警告 ✓; 换 key 生效面从 "下次 create" 扩到 "下次 birth/resume" (resume 重注入幂等). 配套: image-prep 生成的 display/项目层 Containerfile 收尾统一 `RUN chown -R bolo:bolo /home/bolo` 兜底 (F013 类问题的镜像级不变量, 不再靠清单逐目录打地鼠). 理由: rootless podman uid_map 是环境常量 (容器 root = host bolo uid 1000, 容器其他 uid 映射 100000+ 假 uid), host 文件 bind mount 进容器必然呈现为 root 属主; 凡是 "容器 bolo 要读写的 host 文件", bind mount 形态在 rootless 下整体不成立, 注入制是唯一无 mapping 魔改的稳态解.
- 依赖事实: F014 (uid_map 实测 + pi EACCES); F013 (构建期 root 残留同类)
- 预计影响: swt.py (inject_auth_json/birth/resume); image-prep.py (normalize RUN); SKILL.md 风险明示/容器命令收拢; m12 断言

### F014 rootless uid_map 下 host bind mount 的属主错配 (2026-09-11, M10 重跑实测)
- 状态: 当前有效
- 来源: M10 全链重跑, 用户 herdr/ssh 进容器跑 pi 报 `EACCES: permission denied, open '/home/bolo/.pi/agent/auth.json'`
- 内容: 实测容器 uid_map: `0→1000 (host bolo), 1..65536→100000+`; 容器内 bolo = uid 1001. 推论: host 上 bolo (uid 1000) 拥有的文件经 bind mount 进容器后属主呈现为 root; D044 的 `-v auth.json:...:ro` 叠加 host 0600 权限 = 容器 bolo 永远读不了, pi 启动即崩. 且该挂载在运行容器内不可拆 (容器内 umount 无权限; host 侧 nsenter -m 亦失败), 只能重建容器. 通用规则: rootless 下任何挂给容器非 root 用户读写的 host 文件, 都必须走注入 (cp/stdin + chown) 而非 bind mount; 或文件属主换成对应 subuid (脆, 不取). 处置: D046 注入制 + m12 断言改写.

### D047 容器主机名必须经 DECIDE 确认
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: `birth` 不带 `--hostname` 时先输出 `DECIDE` 并停止, 不让 Podman 用容器 ID 充当主机名. 用户确认后带 `--hostname <RFC1123 主机名>` 重跑; 非法值在资源创建前 exit 2. 主机名写入 `podman create --hostname`, m12 以 `podman inspect .Config.Hostname` 复核.
- 预计影响: swt.py birth/create; tests/test_swt_m12.py

### D048 目标容器 netns 绑定与全局兜底禁猜
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: nft 目标 netns 全部由目标容器 `podman inspect` 的 `NetworkSettings.SandboxKey` 定位, 覆盖 birth/resume/resume 网络状态检查/terminate/switch 清理. runtime 中记录的旧 netns 只作状态信息, 不作为 stop/start 后的目标定位; `pgrep -af 'pasta --config-net'` 仅保留兼容诊断兜底, 且全机多于一个 pasta 实例时直接报错, 禁止取首个或任意猜测. 多容器时兄弟容器规则只在各自 inspect 得到的 netns 中处理.
- 依赖事实: F015
- 预计影响: swt.py; tests/test_swt_m12.py; SKILL.md 风险说明

### F015 pasta 多实例串台与 SandboxKey 实测 (2026-09-11)
- 状态: 当前有效
- 来源: m12 并存容器回归 `TestTS5Resume.test_birth_and_resume_use_target_netns_with_interference_container` 与原验收现场复现
- 内容: 同时运行干扰容器和目标容器时, `pgrep -af 'pasta --config-net'` 能返回多个实例. 旧实现取首个实例的 `--netns`, 会把目标容器的 nft 规则注入干扰容器 netns, 目标容器反而没有规则; 目标容器 `podman inspect` 的 `NetworkSettings.SandboxKey` 可稳定指向其当前 netns, 但 stop/start 后该路径可能变化. 修复后 birth/resume/terminate/switch 均按目标容器当前 SandboxKey 操作, 多实例全局兜底直接拒绝.

### F016 terminate 成功路径凭证残留 (2026-09-11, M12 凭证卫生回归)
- 状态: 当前有效
- 来源: m12 单容器 terminate 回归实测
- 内容: terminate 成功 rm 容器并收尾 runtime 后, `runtime/<identity>/ssh/<容器名>.ed25519`, 对应 `.pub` 与 `.password` 仍存在; 多容器按名终结也没有按容器清理. 这违反 SKILL.md 终结完成标准, 形成 host 侧凭证残留. 修复要求: 成功路径按目标 runtime 记录删除私钥, 公钥和密码文件, 缺席按幂等成功处理, 兄弟容器凭证保留.
- 承接: F014 (凭证卫生面)
- 预计影响: swt.py terminate; tests/test_swt_m12.py; SKILL.md 终结完成标准

### D049 git 通道 unix socket 双端桥 (替代 pasta 映射直连)
- 状态: 当前有效
- 约束性: 必须遵守
- 替代: 容器 remote 直连 `git://host.containers.internal:<daemon端口>` (pasta map-guest-addr 映射)
- 内容: daemon 只听宿主回环 (127.0.0.1 动态端口); host 侧 socat 把 unix socket (`runtime/<identity>/git-bridge/git.sock`, 挂载进容器 `/run/swt-git/`) 桥到 daemon 当前端口; 容器内 socat 转发器 (`podman exec -d`, root) 监听固定 127.0.0.1:9418 转发到该 socket. 容器 remote 恒定 `git://127.0.0.1:9418/<仓库名>`, birth/resume 都重保桥与转发器; resume 就绪判定新增 git 通道实测 (记录 remote 为固定地址 + 容器 origin 实际指向它 + 经桥 ls-remote 通), 任一不满足判可恢复并重跑收敛 (G 轮中途失败中间态不再卡死). resume 同时检测 pasta --config-net 复制配置与宿主当前网络失配并告警 (不强制重建). 配套: base 镜像 +socat (双端桥) +iproute2 (容器内排障); host 需 socat (start_git_bridge ENV 检查).
- 依赖事实: F017
- 预计影响: swt.py (daemon/birth/resume/terminate/switch/容器 create 挂载); image-prep.py (base); SKILL.md (术语/恢复/风险/命令收拢); tests/test_swt_m12.py

### F017 pasta map-guest-addr 在宿主换网络后失效 (2026-09-11, G 轮 M10 验收获评)
- 状态: 当前有效
- 来源: G 轮 M10 验收, 宿主从 wlp1s0 换到 tun0 (VPN) 后容器 push 超时
- 内容: 容器出网/DNS 正常, 唯独容器到 `host.containers.internal` (169.254.1.2) 的映射通道超时 — 旧 pasta 进程在宿主换网络后不死不重建, 其映射的是创建时接口状态; 同时 resume 重拉 daemon 端口漂移 (40629→45469), 容器内 remote 失配, resume 就绪判定不含 git 通道实测, 把 "daemon 活 + 容器跑" 误判为就绪, 中途失败留下 "新 daemon + 旧 remote" 中间态后重跑卡 "已就绪" 不再修复. 另实测 pasta --config-net 复制的接口名/地址在宿主换网络后与容器内不一致 (容器 tun0 192.168.216.x vs 宿主 wlp1s0 192.168.31.x).

### D050 agent 系统提示词母本制
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 母本在仓库 `agent-prompts/{pi,codex,kimi-code}_AGENTS.md`; birth 拷贝到 `runtime/<identity>/agent-prompts/<容器>/` 留档 (每容器一份, 可追溯版本), 只读单文件挂载进容器: pi → `~/.pi/agent/AGENTS.md`, codex → `~/.codex/AGENTS.md`, kimi-code → `~/.kimi-code/AGENTS.md` (官方文档: 全局指令文件随 KIMI_CODE_HOME, 缺省 `~/.kimi-code/`). 生效语义: 母本更新只对新 birth 的容器生效, 不动运行中容器. base 镜像不再烘 host 的 `~/.pi/agent/AGENTS.md` (image-prep IGNORE_PI_AGENT 加排除). 只读挂载只防写, 容器内可读 — 与镜像内其他配置同级, 无秘密.
- 预计影响: swt.py (stage_agent_prompts/create 挂载); image-prep.py (IGNORE_PI_AGENT); agent-prompts/ (新增); SKILL.md 新节; tests/test_swt_m12.py

### F018 kimi OAuth refresh token 一次性轮换 (2026-09-11, G 轮实测)
- 状态: 当前有效
- 内容: 容器内 kimi 与 host 共用同一份 OAuth 凭证 (复制 `~/.pi/agent/auth.json`) 时, 先用者刷新成功, 另一边报 400 invalid grant. 结论: 容器内 kimi (Kimi Code CLI) 必须独立登录, 禁止复制 host kimi 凭证进容器共用; 已写入 SKILL.md 存续节. 另: Python 版 kimi-cli 官方停维护, 项目层换代为 Node 版 Kimi Code CLI (install.sh, KIMI_VERSION 钉 0.42.0, KIMI_INSTALL_DIR=/usr/local 系统级), 同层清旧 uv 版残留.

### D051 双模显示栈: 本机 wayland 直通 + VNC 保留兜底
- 状态: 当前有效
- 约束性: 必须遵守
- 依据: `容器GUI无感访问技术报告.md` (2026-09-12, 同目录); 本机环境实测: GNOME Wayland 会话在线, 无 SELinux (报告坑 2 不适用), `/dev/dri` 可直挂 (非 NVIDIA, 免 CDI). 机制与 D049 git 桥同族 (host unix socket bind-mount 进容器), 工程手法有现成参照.
- 内容:
  1. **本机直通 (新增)**: 检测到宿主机 `$XDG_RUNTIME_DIR/wayland-0` 存在时, `podman create` 恒挂 — `-v $XDG_RUNTIME_DIR/wayland-0:$XDG_RUNTIME_DIR/wayland-0` + `-e WAYLAND_DISPLAY=wayland-0 -e XDG_RUNTIME_DIR=<宿主机值>` + `--device /dev/dri` (pulse socket 可选, 声音需求出现时再加). 检测是 host 侧静态条件, 与会话从本机还是远程发起无关, 挂了远程也不碍事, 故恒挂不设 DECIDE.
  2. **VNC 栈保留不降级**: noVNC 仍是局域网远程访问的唯一通道, 也是直通失效时的兜底. 6080 发布/隧道命令/交付规格照旧.
  3. **容器内选路**: headed 浏览器等 GUI app 优先走 `WAYLAND_DISPLAY` (`chromium --ozone-platform=wayland`), 不可达回退 `DISPLAY=:99` (Xvfb). 本机在场 = 窗口直接弹在宿主机桌面; 远程 = 照旧 noVNC.
  4. **display-check 加一路**: wayland 直通探测 (容器内连 socket 实测), 与现有 noVNC 检查并列报告, 失败按 D041 降级不阻断终端工作.
  5. **禁挂 X11 socket**: X11 协议允许跨客户端键盘嗅探/按键注入, 直通只走 wayland, 不通就回 noVNC, 永不以挂 X socket 兜底.
- 信任面明示 (用户已拍板接受, 2026-09-12): 挂 wayland socket 后容器内任意进程可在宿主机桌面开窗口/读剪贴板, 接近 distrobox 信任级别; 网络白名单语义零变化 (socket 非网络通道). 收益: 登录墙原生窗口 + GPU 渲染 + fcitx 中文输入 + 剪贴板互通, noVNC 窗口套窗口/软渲染/无法输中文三个短板全消.
- 预计影响: swt.py (create 参数组/display-check); SKILL.md (显示栈节/容器命令收拢/风险明示/交付汇报); display 层镜像基本不动 (chromium 自带 wayland 后端); tests. 范围外: waypipe 远程直通 (noVNC 够用前不引入).

### F019 socat 中继对 wayland 无效 (SCM_RIGHTS fd 传递被截断) (2026-09-12, M13 实测)
- 状态: 当前有效
- 内容: wayland 客户端与合成器靠 unix socket  ancillary data (SCM_RIGHTS) 传共享显存 fd; socat 这类字节流中继不传 fd, chromium 经中继连接必崩 (`Fatal Wayland communication error: Invalid argument`). 结论: wayland 直通只能直挂 socket 本体, 权限问题在属主权上解 (chmod 0777, 见 D051 实现修订), 禁用中继. 另: `--screenshot` 会强制 headless 模式, 不能用作 wayland 通路的验证手段; 验证 = headed 进程存活 + 无 fatal (直挂方案实测: bolo 身份 chromium `--ozone-platform=wayland` 存活 25s+ 零 fatal, 窗口落宿主机桌面).

### D051 实现修订 (M13, 2026-09-12)
- 状态: 当前有效
- 内容: D051 第 1 条落地参数定为 `-v <宿主socket>:/run/swt-wayland/wayland-0 -e XDG_RUNTIME_DIR=/run/swt-wayland -e WAYLAND_DISPLAY=wayland-0 [--device /dev/dri]`. 权限解法: rootless uid_map 下直挂 socket 在容器内属主映射为 root, 0755 属主权下 bolo 连不上 → host 侧 `chmod 0777` 该 socket (birth/resume 都重保, GNOME 登录会话重启重置权限); 父目录 `/run/user/<uid>` 为 0700, 其他用户够不着路径, 宿主暴露面≈零. 不采用容器内 socat 中继 (F019). GPU 补充: 非 NVIDIA 宿主 `/dev/dri` 直挂即可, 但 render 节点属主权同样受限, chromium 不可用时自动回软渲染, 不阻断.
