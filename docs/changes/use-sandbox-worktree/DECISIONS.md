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
- 状态: 当前有效
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
- 状态: 当前有效
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
- 状态: 当前有效
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
