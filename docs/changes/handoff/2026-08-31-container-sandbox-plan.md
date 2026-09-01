# 交接: 容器化工作试验场方案定型 (sandcastle 调研 → use-sandbox 形态)

日期: 2026-08-31. 来源会话: slim-subagent 工作目录, 全程只读模式, **零代码落地, 仅完成方案设计**.

## 背景与最终结论

起点是调研 https://github.com/mattpocock/sandcastle (已 clone 到 /tmp/sandcastle, 只读研究用). 经过方向修正, 最终定型的是一个**与 sandcastle 无关的纯 podman 方案**: 给我 (LLM) 一个 "容器内 clone 仓库 → 容器里干活 → 产物经 git 回流" 的隔离试验场, 通过 ssh 进入, 形态是新 skill (暂名 use-sandbox). sandcastle 最终不进依赖.

## 路线图 (真实意图脉络)

1. **起点**: 想给 pi 的 subagent 工具集成容器能力 — 子代理跑在 podman 容器里, 使用者无感. 调研结论: sandcastle 是 TS 库 (AgentProvider/SandboxProvider 两抽象, 内置 pi provider + podman provider), 可以直接驱动 pi, 但与 pi 无原生集成; slim-subagent 集成有两条路 (B1 薄层 argv 包裹 / B2 借库), 均未采纳.
2. **方向修正 (用户)**: "子代理工具结合 sandcastle 不科学", 转向给 use-worktree skill 加 "是否在容器中创建" 选项. 拆出两条路线: A = host 建 worktree + 容器 bind-mount 执行; B = 真·容器内 clone (isolated).
3. **用户选 B** ("更干净"), 依次解决三个疑问: chromium 每次下载 (→ 进镜像), JDK/Maven/git 打包 (→ fat 镜像 + ~/.m2 挂载), 仓库不重拉 (→ host 仓库只读挂载后本地 clone / git bundle).
4. **补齐使用形态**: 用户经 ssh 登录容器干活 → 全 skill 库 (29 个) 兼容性审查 → 纯方法论 ~20 个零障碍, 工具类需镜像预装, **展示链是唯一真缺口**.
5. **缺口逐个闭环**: present 自带 `scripts/web_server.py` (未接线) → HTTP 服务 + 端口映射解决展示链; 登录墙 → Xvfb + noVNC 虚拟屏幕方案. 方案闭环, 落地 0%.

## 定型方案全貌

**fat 镜像** (build 一次, 秒级启动): ubuntu base + git + jdk + maven + uv/python + node + pi CLI + playwright/chromium (--with-deps) + openssh-server + authorized_keys + Xvfb/x11vnc/novnc/websockify + fonts-noto-cjk. 分层原则: 稳定的在前 (jdk/maven), 常变的在后.

**运行时**:
```bash
podman run -d --shm-size=1g \
  -p 2222:22 \                    # ssh (rootless 高位端口, host 约定已存在)
  -p 8800:8800 \                  # HTML 展示 (present web_server)
  -p 6080:6080 \                  # noVNC (人工操作容器浏览器)
  -v ~/.m2:/home/agent/.m2 \      # Maven 缓存复用 (同策略: ~/.gradle 等)
  -v <host-repo>:/mnt/repo:ro \   # 仓库只读挂载 → 容器内 git clone /mnt/repo (秒级) → remote set-url 回真 remote
  -v ~/.pi/agent:~/.pi/agent:ro \ # pi auth/settings
  -v sandbox-profile:/tmp/access-web \  # 浏览器 profile 持久化 (登录态跨容器)
  <image>
```

**关键工作流**:
- 仓库: 只读挂载 + 本地 clone (备选 git bundle, 仅强隔离需求时)
- 展示链: present 的 web_server.py `start <port> <root> --bind 0.0.0.0` + add-dir 动态挂目录 → host 浏览器开 `http://localhost:8800`; probe 的 "重画覆盖同名 + 原地刷新" 语义在 HTTP 下免费保留. 需给 present SKILL.md 加容器分支 (web_server.py 已齐备但未接入流程)
- 登录墙: `Xvfb :99 & x11vnc -display :99 & websockify 6080 localhost:5900` + `DISPLAY=:99 BROWSER_HEADED=true` → host 浏览器开 :6080 人工操作 (密码/MFA/扫码), 登录态落 profile volume, 之后回 headless. access-web 代码零改动
- 展示链覆盖: present / explain-diff / probe / improve-codebase-architecture / teach 全部跟随 present 的容器分支

**已知的 "留 host" 清单**: access-web headed 人工登录若不采用 VNC 方案时; diagnosing-bugs HITL "人来点" (或被测服务端口映射后在 host 点); use-worktree (容器内 clone 非标准 worktree 布局, 场景不适用 — 容器本身就是隔离单位).

## 技术细节备忘 (易踩)

- build vs run: RUN/COPY 仅 build 时执行, 容器启动零安装 — 用户曾误解, 已澄清
- 容器内 HTTP 服务必须 bind 0.0.0.0, 否则端口映射进不来
- chromium 需 `--shm-size=1g` (podman 默认 64MB /dev/shm 会崩); 中文需 fonts-noto-cjk
- skills 同步进容器: sync-to-pi.py 本就 ignore .venv/tests, 容器内重新 uv sync; host .venv 不可复用 (python 路径硬编码)
- ~/AGENTS.md 引用的 ~/docs/, ~/Workspace/ 约定在容器内不存在 — 挂载或降级
- 本地 podman: Ubuntu 26.04, rootless, subuid 已配, 存储 ~/.local/share/containers (见必读推荐)

## 已否定的方向 (勿重提)

- subagent 工具集成 sandcastle / 容器化子代理 (B1 可行但用户判定不科学; B2 与 line-protocol/projection 职责重叠)
- sandcastle 全家桶 createWorktree/createSandbox: 其 worktree 约定 `<repo>/.sandcastle/worktrees/` 与 use-worktree 标准布局冲突
- pi 自带 containerization.md 路线 (gondolin/whole-process-docker/OpenShell): 隔离对象是整个 pi 进程, 与本需求形态不同

## 必读推荐

- `~/.agents/skills/access-web/browse/browse.md` — browse 会话机制全文: session-key 派生, BROWSER_HEADED 开关, profile/cookies 生命周期, 产物路径. 本文档只摘要了衔接点, 落地登录方案前必读.
- `~/.agents/skills/present/SKILL.md` + `present/scripts/web_server.py` — 现有展示流程 (browser_session.py open 路径) 与 web_server CLI 的确切接口 (start/status/stop/add-dir, daemonize 实现). 加容器分支前必读.
- `~/docs/podman.md` — 本机 podman 约定: rootless, 高位端口, Quadlet, 存储位置.
- `/tmp/sandcastle/src/` — 仅当仍需参考: `sandboxes/podman.ts` (rootless/SELinux/mount 参数), `syncIn.ts` (git bundle 机制), `AgentProvider.ts` (pi provider), `AgentProvider.ts` 的 `makePiSessionStorage` (session 跨边界). /tmp 可能已被清理.
- `~/.agents/skills/use-worktree/SKILL.md` — 标准 worktree 布局与硬规则, 理解 "容器内为何不适用" 的对照面.

## 路线图评估

用户真实意图: 一个干净的, ssh 可入的容器化试验场, 让我的全套工作流 (含浏览器与 HTML 展示) 在容器里无障碍运转, 且 host 不落盘, 无重复下载. 设计侧已 100% 闭环 (上文全貌); 落地侧 0%: Containerfile 未写, 镜像未 build, use-sandbox skill 未起草, present 容器分支未动, 端到端 (ssh 入容器 → clone → 干活 → HTML 展示 → 登录墙演练) 未验证.
