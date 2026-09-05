# skills 仓库

本仓库沉淀可复用的 AI coding agent skills 与 pi agent 配置. 本词汇表收集跨 skill 讨论中解析清楚的特有术语.

## 语言

**常驻展示服务**:
present skill 在远程 (ssh) 场景下于主机上常驻的 web 服务器 (`web_server.py`), 向用户设备的浏览器交付展示内容. 同主机同用户 (uid) 单例, 多 ssh 会话共用.
_避免_: web 服务器进程, 后台服务 (过泛, 未含单例与用途语义)

**挂载目录 (root)**:
经 start 或 add-dir 登记进**常驻展示服务**、其内容可被 URL 访问的本地目录. roots 的顺序即**遮蔽**优先级.
_避免_: 根目录 (与文件系统根混淆), 资源目录

**扁平并集**:
**常驻展示服务**的 URL 命名空间: 请求路径依次在各**挂载目录**查找, 首个命中返回; 顶层 listing 为各目录条目并集去重. 对立面是被拒绝的"每目录一前缀"方案.
_避免_: 虚拟路径合并, 目录映射

**遮蔽**:
**扁平并集**下多个**挂载目录**含同名文件时, 按挂载先后静默返回先挂载者的规则; 保留命名空间 (`/__control__/*`) 对同路径文件的优先也称遮蔽. 均无提示.
_避免_: 覆盖, 冲突

**控制面**:
**常驻展示服务**上 `/__control__/*` 保留命名空间内的本机专用端点簇 (ping/add-dir), 仅 loopback 来源. 对立面是**内容面**.
_避免_: 管理接口, 内部 API

**内容面**:
**常驻展示服务**上静态内容与目录 listing 的访问面, 绑定开放时对网段可见 (已接受取舍).
_避免_: 公开面, 静态面

**远程模式**:
present skill 检测到 ssh 会话 (`SSH_TTY`/`SSH_CONNECTION` 或用户明示) 时的展示路径: 走**常驻展示服务**交付 URL, 完全替代本地 Chromium, 降级为纯展示 (无页面状态回读).
_避免_: ssh 模式, headless 模式

**sandbox-worktree**:
git worktree + sandbox 容器的绑定对, use-sandbox-worktree skill 管理的生命周期单元: 诞生 (建工作树作**母体** + 拉起容器) → 存续 (用户 ssh 入容器驱动容器内 agent, 产物 push 到母体分支, **推送落地**回流 host) → 终结 (删容器; 母体存删用户自决).
_避免_: 沙盒 (未含 worktree 绑定语义), 容器工作区

**母体**:
**sandbox-worktree** 中 host 上的 git worktree (主仓 linked worktree, use-worktree 所建), 容器代码的克隆源与产物回流落地窗口二合一: 容器诞生时经 **git 守护进程**克隆母体分支, 工作成果 push 直写主仓的母体分支 ref, **推送落地**使母体目录文件即时更新可审阅可运行. 母体存活/删除/复用由用户自决, 与 sandbox-worktree 解耦; 同一主仓同一时刻至多一个活动母体.
_避免_: gate (旧称, 原指独立 clone 中转仓, 该形态已废), 中转仓

**git 守护进程**:
git 自带的无认证 `git://` 协议服务进程 (`git daemon`). **sandbox-worktree** 中每容器一个, 随容器生灭, base-path 仅含主仓, 是容器到达**母体**的唯一 git 通道; 真远端对容器完全不暴露.
_避免_: 后台服务 (过泛, 未含协议与无认证语义)

**推送落地**:
git 配置 `receive.denyCurrentBranch=updateInstead` 的效果: 合规 push 被接收的瞬间, 检出该分支的工作区文件同步更新为 push 内容. **母体**目录因此 push 即落地.
_避免_: 自动同步 (未含 git 语义)

**base 层 / 项目层**:
**sandbox-worktree** 镜像的两层结构: base 层固定且跨项目共享 (OS + pi CLI + skill 库 + bin), 项目层由 host llm 按项目推导依赖件叠加. 门禁类扩展不属于任何一层 — 留 host 不进容器.
_避免_: 基础镜像 (未含跨项目共享与固定语义), 项目镜像

**完美复刻**:
**sandbox-worktree** 容器用户 home 的布局原则: home 路径与 host 字面相同, `~/Workspace/`, `~/.pi/agent` 机械复制, 零适配层. 代码固定 `~/Workspace/<母体目录名>` (规范化目录名, 非原始分支名). 刻意排除 `~/AGENTS.md` 与 `~/docs/` — 它们是 host 环境文档, 容器是独立环境, 注入即误导.
_避免_: 环境同步 (未含字面路径相同语义), 镜像复刻

**交互式编排适配层**:
herdr 在 **sandbox-worktree** 中的定位: host herdr 经 `HERDR_AGENT=pi` wrapper 提示把 ssh 入容器的 pi 识别为一等 agent, host 侧用 委派配方 (查 idle → send-text → 容器键位提交 → wait/read) 驱动容器 agent. 刻意不宣称协议级替代 subagent: 无 task id/退出码/重试幂等.
_避免_: subagent 替代 (被刻意收窄的定位), 远程控制

## 示例对话

开发者: 第二个会话又调用 start, 会起新的**常驻展示服务**吗?
领域专家: 不会, 同 uid 单例, 它复用现有实例并把新目录追加为**挂载目录**.
开发者: 两个**挂载目录**里都有 index.html 怎么办?
领域专家: **扁平并集**规则, 先挂载的**遮蔽**后挂载的, 静默.
开发者: 网段里别人能挂目录吗?
领域专家: 不能, add-dir 在**控制面**, 仅 loopback; 但读已挂载内容走**内容面**, 网段可读, 这是已接受的取舍.
