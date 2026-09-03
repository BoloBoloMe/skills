# use-sandbox-worktree 决策账本

## 决策

### D001 读通道: 真远端完全不暴露, 容器一切 git 读走 gate 镜像
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 容器的 clone/fetch 全部指向 gate, 网络白名单只放行 gate 端口; 真远端对容器连只读都不暴露. 理由: T7b 教训下真远端对容器"fetch 通但 push 拒"的半暴露状态徒增攻击面无收益; gate 是真远端完整镜像, 读全分支无损. 代价: 容器看到的"远端"新鲜度受 gate 同步策略限制, 由 D002/D003 对冲.
- 依赖事实: F002, F003
- 预计影响: use-sandbox-worktree skill 诞生步骤 (容器 git remote 配置, 白名单盘点)

### D002 gate 读侧同步时机: 诞生同步 + 明说更新 + 新会话重置顺带 fetch
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: gate 从真远端 fetch 的触发点只有三个: (1) sandbox-worktree 诞生时初始同步; (2) 用户明说"更新"时 host llm 手动 fetch; (3) 每新会话重置 sandbox/work 起点时顺带 fetch. 明确不做定时轮询 — 轮询是容器外的隐式变化, 违背"容器之外用户说了算".
- 依赖事实: F002
- 预计影响: skill 诞生步骤与会话起点流程 (分支生命周期细节属 MILESTONE-02)

### D003 freshness 可观测: gate 每次同步记录 base commit + fetched_at
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: gate 每次从真远端同步后, 记录 base commit 与 fetched_at, 容器内可查 — agent 始终能知道自己基于多旧的快照, 不自知陈旧的静默状态被排除. 不强制 agent 基于最新 main 工作 (用户工作流: 工作树分支推进到可上线程度才合并主分支, 半成品/未完成 QA 的改动不进主分支, 故"最新 main"不是硬要求).
- 依赖事实: F005
- 预计影响: gate 同步脚本 (写元数据), 容器内查询方式 (MILESTONE-03 待定形式)

### D004 gate 服务形态: 每 gate 专属 git daemon, 拓扑纪律兜底
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: gate 用 `git daemon --enable=receive-pack` 服务, 不用 git-over-ssh. 附加纪律: 每 sandbox-worktree 一个专属 daemon 进程, base-path 仅含本 gate 仓, 不开 `--export-all`, 端口动态分配, daemon 随容器生灭. 排除 ssh 的理由: 私钥须进容器 = 凭据泄漏面 (与 host↔真远端共用密钥直接判死); ssh 默认可对用户有写权限的任意路径跑 git-receive-pack, 锁路径要 authorized_keys forced command, 复杂度白付. 已认知限制: daemon 无身份认证/审计能力, 威胁模型仅覆盖"单容器单 gate, 本机 netns 白名单, 防容器 agent 绕过钩子"; 未来若要会话级审计或多 gate 互隔需重审 (多 gate 并发在未决迷雾).
- 依赖事实: F002, F003
- 预计影响: skill 诞生/终结步骤 (daemon 进程编排), 网络白名单注入

### D005 gate 干净保障: 专用目录纪律 + host 兜底, 不做权限强制
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: gate = host 上独立 clone 的专用目录 (非 git worktree 形态 — 共享 hooks 目录会误伤主仓), 角色钉死为"纯落地窗口": 人工审阅只读/diff/可编译试跑 (实测未跟踪产物不阻塞 push), 禁止编辑跟踪文件, 审阅时不开会自动写文件的工具 (IDE 格式化等). 兜底: host llm 诞生时初始化并校验干净; 运行期 agent push 失败回流 host 会话时, host llm 诊断 `git -C <gate> status` 并修复. 拒绝"接收/审阅目录分离"方案: 它只多防"违反纪律编辑跟踪文件"一种事故, 代价是丢掉 updateInstead "push 即落地可运行"的二合一甜头. 拒绝权限强制 (目录对人只读): 碍审阅试跑.
- 依赖事实: F001, F004
- 预计影响: skill 诞生步骤 (gate 目录初始化), 容器内 skill 文档 (试跑规则)

### D006 报错透明化: 所有拒绝路径都要人话
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: pre-receive 钩子 stderr 写人话回传 push 方 (如 "拒: 仅收 refs/heads/sandbox/work 的 ff push"); 透明化须覆盖所有拒绝路径, 不止自定义钩子 — 脏工作树路径由 updateInstead 原生报错 "Working directory has unstaged changes" 兜底 (半可读, 实测), 其余路径 (网络失败/同步失败) 在 MILESTONE-03 实现时逐项核对.
- 依赖事实: F001
- 预计影响: MILESTONE-03 瘦闭环实现的 pre-receive 钩子脚本

## 事实

### F001 updateInstead 阻塞条件实测 (2026-09-01 后盘问会话)
- 状态: 当前有效
- 来源: 本地实测 (git init + receive.denyCurrentBranch=updateInstead, checkout sandbox/work 后 push)
- 内容: gate 检出分支为 sandbox/work 前提下: (1) 仓内存在未跟踪文件 (模拟编译产物) → push 正常接受, 不阻塞; (2) 跟踪文件有未暂存改动 → push 被拒, 原生报错 `Working directory has unstaged changes`; (3) 向非检出分支 push 完全不触发 updateInstead 检查 (第一次实测曾因此误报, 复测已修正).

### F002 门禁机制实测矩阵全过
- 状态: 当前有效
- 来源: docs/changes/use-sandbox-worktree/2026-09-01-research.md §4.2
- 内容: clone 读全 ref / sandbox/work 追加 push 接受 / non-ff 拒 / 新分支拒 / tag 拒 / 删分支拒 / 绕开 gate 直指真远端时协议层拒写. git 钩子只存在于写方向, 读方向天生开放.

### F003 T7b 拓扑教训
- 状态: 当前有效
- 来源: docs/changes/use-sandbox-worktree/2026-09-01-research.md §4.2
- 内容: git daemon `--export-all` 共享 base-path 时可经 9418 直接 push 写穿真远端绕过钩子. 门禁由拓扑保证, 不由钩子保证: real 仓绝不落在任何可写服务端点路径内.

### F004 updateInstead "push 即落地"
- 状态: 当前有效
- 来源: docs/changes/use-sandbox-worktree/2026-09-01-research.md §4.3
- 内容: 非裸仓设 receive.denyCurrentBranch=updateInstead 后, 合规 push 被接受的瞬间 host 工作树文件自动更新成 agent 成果; 门禁与落地窗口二合一, 回流 = host 人工审阅该目录 → merge → push 真远端.

### F005 用户合并工作流
- 状态: 当前有效
- 来源: 用户陈述 (MILESTONE-01 盘问会话, 2026-09)
- 内容: 工作树分支推进到可以上线的程度才合并主分支; 半成品/未完成 QA 的改动不进主分支.
