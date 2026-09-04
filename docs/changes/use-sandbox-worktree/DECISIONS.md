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
- 内容: gate 重定义为**母体**: 主仓的 linked worktree (use-worktree 所建的工作树分支). 诞生时 host llm 调 use-worktree 建工作树分支作母体 (或复用现有母体, 见 D010); 容器诞生时经 git 守护进程 `git clone -b <母体分支>` 克隆母体为代码母体; 容器工作成果 push 直写主仓 `refs/heads/<母体分支>`, 推送落地 (updateInstead) 让母体目录文件即时更新为 agent 成果, host 直接审阅/试跑. 真远端对容器完全不暴露 (D001 此部分保留). 一名贯穿: 母体分支名 = worktree 目录名 = 容器名 = 容器 label 标识. 理由: 用户判定独立 clone 中转层多余, 砍层; 实测 updateInstead 识别 linked worktree 当前分支并即时更新其工作区 (F007). 代价: 主仓成为 receive 端, 写面收敛全靠主仓 config (D008); 母体工作区跟踪文件脏会拒容器 push (updateInstead 原生行为, F001 同构).
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

### D007 容器操作不做 provider 抽象层, 仅留文档级扩展点
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 不建 "接口 + 实现类" 式的容器 provider 抽象 (docker/podman 多态). 理由: (1) 同一场景同一时刻只绑一个 provider, 诞生时选定后全程复用, 运行期多态无收益; (2) 硬约束长在 podman rootless 特性上 (netavark/nft 白名单注入, rootless netns, Quadlet), docker 的网络模型不同, 抽象层必漏成抽象漏洞; (3) skill 是 markdown 驱动 llm 敲命令, 抽象层无代码宿主. 扩展点形态: skill 文档把所有容器命令收拢到单独一节, 未来换/加 provider 时只改该节. 动机记录: 留扩展点 + 架构整洁偏好.
- 预计影响: use-sandbox-worktree SKILL.md 结构 (容器命令独立一节)

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
