---
name: use-sandbox-worktree
description: 管理 sandbox-worktree (host worktree 母体 + sandbox 容器绑定对) 的生命周期与配套镜像/网络/显示栈.
disable-model-invocation: true
---

# use-sandbox-worktree

**术语**:
- **sandbox-worktree**: 一个 host 上的 git worktree (**母体**) + 一个 sandbox 容器的绑定对, 本 skill 管理的生命周期单元. **开放写单位 = 母体工作树** (不是主仓): 每个母体工作树各自配容器, 多对并存互不干扰. 一母体同一时刻至多一个活跃容器 (活跃 = 非 retired, 含停止未终结): birth 拒绝同母体已有活跃容器, 想换容器须先 terminate; 一台 host 可有多个母体 (多个主仓各自多对, 同一主仓也可多对并存); 改动前已存在的容器不追溯处置.
- **母体**: 主仓在 host 上的一个 worktree 目录 (与主仓同级的兄弟目录, 目录名 = 母体分支名), 身兼两职: 容器诞生时从它克隆代码; 容器 push 的成果直接落进它, 打开就能审阅/试跑.
- **推送落地**: 容器 `git push` 被接受的瞬间, 母体目录里的文件自动更新成 push 内容, 不用手动 pull; 有秒级短延迟 (push 返回后文件稍后可读).
- **git 守护进程 (daemon)**: 每对一个临时起的 `git daemon` 进程 (服务各自的母体目录, 对级 hideRefs 随母体 config.worktree 生效), 只听宿主回环 (127.0.0.1 动态端口), 容器碰到代码的唯一通道, 无认证. 该母体最后一个容器 terminate 时收掉.
- **git 桥**: 容器访问 daemon 的固定通道; 容器 remote 恒定 `git://127.0.0.1:9418/<母体目录名>`, daemon 端口漂移/host 换网络都不再失配 (机制见 reference/ops.md).
- **交付包**: birth/resume 收尾必须齐发的一组交付, 逐项规格与缺发规则见 birth 第四步.

元规则: 本文件机制细节与环境现实冲突时, 以环境硬约束 (git 配置/防火墙/拓扑) 为准并报告我.
**命名消歧**: `swt` = host 编排脚本 `scripts/swt.py`; `swt-vnc` = 容器内 VNC 栈 helper (见显示栈节), 两者无关.

## 角色边界

- 你 (host 侧 agent) 只管理生命周期, 不进容器干活.
- 一切需我拍板的点由脚本以 DECIDE 行表达 (见决策协议节): 逐字转述给我, 我答后带 flag 重跑同一命令, 替我作答即违规.
- 真远端 (github 等) 对容器完全不暴露; 授权配置常驻两层: 主仓 config (deny 三键 + worktreeConfig 扩展开关, 跨母体共享) + 各母体 config.worktree (hideRefs 与 git-daemon-export-ok, 每对一份, 只放行本对分支) (残余影响见 reference/risks.md). 改造前旧版主仓级 hideRefs 残留会被 birth/resume 自动迁入各母体 config.worktree (含 daemon 重摆与容器 remote 改指), 运行中容器无感, 不需手工处理.

## 环境前置

- rootless podman (pasta 网络), nftables, git (须支持配置里 "隐藏所有分支, 只放行一个" 的 `hideRefs` 写法与 `extensions.worktreeConfig` 扩展; birth 每次会建一次性小仓库实测确认, 不支持则 exit 4).
- `uv run python` 运行全部脚本; 脚本路径相对本 skill 目录引用.
- 记录根缺省 `~/.agents/sandbox-worktree/` (运行状态/决策收据/审计/镜像构建记录同屋), 全部脚本支持 `--records-root` 覆盖.
- host skill 库 `~/.agents/skills/` 全树全局可读 (容器 bolo 经 rootless uid 映射只靠 other 位读它); 带依赖的 skill 项目须携带已部署的 uv.lock.

## 入口: status 先行

```text
uv run python scripts/swt.py status [--repo <主仓>]
```

`--repo` 缺省从 cwd 推导主仓. status 只读, 聚合盘点本主仓全部对 (STATE 顶层兼容字段 = 主对, `mothers[]` 逐对列 branch/dir/daemon/containers). 读末行 `STATE {...}` 分流: 有停着的容器/残留的 daemon/缺防火墙规则 → resume; 无任何记录 → birth; 多对时用 `--branch`/容器名消歧; 有 retired 容器 → 唯一出路 terminate (resume 拒绝).
完成标准: 已据 STATE 判定走 birth / resume / terminate 之一.

## 诞生 (birth)

**第零步: 先用 `use-worktree` skill 为项目创建工作树分支**
母体不是本 skill 自创的命名, 必须走 use-worktree 的建树流程产出: 分支名 = 目标分支名原文, 目录名 = 它的 slug 规则 (<项目>-<来源分支>-<目标分支>). 后续 birth 的 `--branch` 传目标分支名原文, 脚本按分支名定位对: 母体已存在即复用, 不存在即按 `--base`/缺省分支新建 (机械事实, 不再出母体选择 DECIDE). 未建树先 birth 会卡住, 别绕. `--branch` 也是新对的钥匙: 已有对在世时对另一个分支 birth 直接并存开新对, 无需先收拾旧对.

**第一步: 网络模式与白名单盘点**
创建容器前必须与我确认网络模式, 运行期不切换:
- **whitelist** (默认拒, 推荐): 只放行 容器实际解析器 (自动读容器 resolv.conf, 仅 udp/tcp 53) + 网关 DNS + `--allow` 条目 + 已建立连接的返程流量 (output 链只放回程方向: 保住 host 发起的 ssh, 策略收紧即断既有容器主动连接), 过滤覆盖 forward/input/output 三链 (output 管容器主动出站), 其余容器流出全断. git 走 unix socket 桥, 不占网络白名单; 网关与解析器自动放行的残余暴露见 reference/risks.md.
- **blacklist** (默认放行): 只断 `--deny` 条目, 护 host 侧特定服务 (数据库/redis 等) 场景.
盘点方法论: 与我一起列出容器工作所需站点, **域名须解析为具体 IP/CIDR 后传入** (防火墙规则只认 IP, 脚本拒收域名); 条目是 IP 级, 放行即全端口. 站点换 IP 失效时重新盘点. 运行期新站点需求的处理形态未定, 发生时带回本会话问我.

**第二步: 镜像判定与制备**
birth 内部自动跑 image-prep `match`, 需求清单取 `<records-root>/<项目slug>/requirements.md` (或 `--requirements` 指定):
- **清单文件不存在 → birth exit 2, 这是首次为项目建镜像的入口**: 你读项目信号 (AGENTS.md/README/package.json/pyproject.toml 等) 推导依赖件写成需求清单 (格式与推导规则见镜像管理节), **展示清单与我确认后才落盘** — 装依赖会运行其安装脚本, 风险与日常装包同级, 确认时向我明示; 落盘后重跑 birth.
- REUSE → 直接用.
- BUILD-NEW → birth 停出 DECIDE 并附清单; 我确认后由你跑 `image-prep build`, birth 不吞构建环节, 构建完成带 `--image <ref>` 重跑 birth. display 缺失/过期时的构建链与重建纪律见镜像管理节.
在跑容器镜像有新版只在 STATE 标 `newer-available`, 不动存活容器.

**第三步: 执行 birth**
```text
uv run python scripts/swt.py birth [--repo <主仓>] --branch <母体分支名原文>
    [--base <源 ref>] [--name <容器名>]
    [--mode whitelist --allow <CIDR>]... | [--mode blacklist [--deny <CIDR>]...]
    [--image <ref>] [--requirements <file>] [--new-mother | --reuse-mother] [--lan-ip <ipv4>]
```
容器缺省名 `swt-<分支名>`, `--name` 只用于自定义名 — 同母体活跃容器唯一 (见术语), 它不是放行第二个容器的开关. 首次执行通常出 DECIDE (网络模式, 容器主机名, 局域网地址, 镜像), 按决策协议节应答.

**第四步: 交付包**
逐项向我报告, 缺发只允许以一种形式发生 — 显式打原因, 不静默丢失:
- ssh 入口 (两条带端口, 总是同时交付; pasta 下容器无独立 IP — STATE 的 `network-ip` = host 本机 IP, 直连形式已废除):
  - 本机: `ssh -p <宿主端口> bolo@127.0.0.1` — 跨 stop/start 稳定, 端口用 `podman port <容器名>` 或 STATE 的 `ssh-port` 发现, 不记录端口 (rm 重建才变).
  - 局域网: `ssh -p <宿主端口> bolo@<host-LAN-IP>` — `<host-LAN-IP>` 一律取已确认值, 不猜首个网卡: 确认值持久化在 records_root 根级, 首次 birth 无确认值时出 DECIDE 问 (现算候选只作提示, 不当可达交付), 我答后带 `--lan-ip <ipv4>` 重跑即确认; 换网络环境后用同一 flag 覆盖.
- noVNC URL (本机浏览器直接开): `http://127.0.0.1:<vnc宿主端口>/vnc.html?resize=scale` — 实际端口看 STATE 的 `vnc-port`.
- web 双 URL (容器有 web-port 才发): 本机 `http://127.0.0.1:<web-port>` / 局域网 `http://<已确认地址>:<web-port>`; 只列当前母体自身容器, 不汇总其他母体; 无已确认局域网地址时打 "未附发" 提示行, 不猜地址; birth 只交付入口, 不因容器出生自动打开页面. 分享出去的 URL 不保证跨容器重建稳定 (容器 rm 重建后宿主端口会变, 须重新取新 URL).
- 本机直通状态: STATE 容器记录 `host-display=ok` 时交付注明 — 登录墙等 headed 窗口直接弹宿主机桌面, 本机可不开 noVNC; `degraded` 注明已回退 noVNC; `absent` 打一行常态说明 (远程/纯服务器宿主).
- 局域网隧道命令: `ssh -p <宿主端口> -L 6080:127.0.0.1:<vnc宿主端口> bolo@<host-LAN-IP>` — 我在远程机开这条隧道后, 浏览器开 `http://127.0.0.1:6080/vnc.html?resize=scale`; noVNC 无密码, 隧道 (即容器 ssh 凭据) 就是门槛.
- 登录凭证 (两种, 都随 terminate 清除, 落 `<records-root>/runtime/<identity>/ssh/`, 0600; identity 为对级目录 = `<项目slug>-<sha1(母体目录路径)前8位>`, 每对一套):
  - 密码: 固定 `sandbox` (用户拍板, 风险见 reference/risks.md), `<容器名>.password` 留档; 人登录用.
  - 密钥: `<容器名>.ed25519` (`ssh -i <私钥> ...`), 脚本/herdr 的 BatchMode 走它.
- herdr remote (走 ssh, 容器无需预启 server, remote attach 按需拉起): 两条完整命令 — 本机 `herdr --remote ssh://bolo@127.0.0.1:<宿主端口>`, 局域网远程机 `herdr --remote ssh://bolo@<host-LAN-IP>:<宿主端口>`; 我会在本机和远程机之间来回切换, 远程机私钥需先从 host 拷贝 (路径见上) 或直接用密码. 该命令须在非 herdr 终端运行 (herdr 会话内被套娃禁用拦截); 已在 herdr 里则走开窗格配方 (存续节).
- 远程直飞命令模板 (容器带 headed 启动脚本才发): 见 reference/pull-window.md 设备侧拉起第 4 步, 变量照 STATE 与交付包实际值代换.
- 容器内路径契约: 用户 `bolo` (home 与 host 字面相同), 代码固定克隆在 `/home/bolo/Workspace/<分支名>` (当前分支 = 母体分支); skill 库在 `~/.agents/skills/` (运行期从 host 同路径只读挂载, 实时跟随 host 版本; 项目 `.venv` 是镜像播种的可写匿名卷), pi 配置在 `~/.pi/agent/`.
- 风险声明: 连同 reference/risks.md 的风险项一起声明.
完成标准: STATE `stage=born`, 容器内检出分支 = 母体分支, 交付包齐发 (显示栈降级/缺席时相应项改为降级/常态说明, 其余照发).

## 存续

**ssh 入容器**: 经交付包 ssh 入口进容器驱动 pi 干活. 产物回流 = 容器内 `git push` (只允许历史只增不改的快进推送), 推送落地使母体目录文件即时更新, host 直接审阅/试跑.

**herdr 接入与委派配方**: herdr 在 base 层 (容器内可直接用); 要从 host herdr 工作区总览容器内 pi, 就在 host 侧开窗格 `HERDR_AGENT=pi ssh -p <端口> -i <私钥> bolo@127.0.0.1`, host herdr 经 env 提示把容器内 pi 识别为一等 agent. 委派配方:
1. `herdr agent get` 确认 idle — blocked/working 态不发 (无 guard 会把键打进错误界面).
2. `herdr pane send-text` 发任务文本.
3. 提交键 = 读容器内 `~/.pi/agent/keybindings.json` 的 `tui.input.submit` 首键 (跟随我的键位配置), 兜底 alt+enter.
4. `herdr agent wait` / `agent read` 收结果.
这层编排没有任务 id/退出码/重试保证; 需要这些保证时用保底形态 `pi -p "<任务>"` 批处理 (绕开 TUI 键位注入, 一轮一进程).

**展示链**: 容器内展示由 `present` skill 的容器分支全权负责 (判定/bind/端口/url 语义见其 "容器内分支" 节). host 侧事实: 容器对外 web 端口固定 8800, birth 把它发布到宿主 0.0.0.0 动态端口 (直达局域网, 无认证), 映射登记 STATE 容器记录 `web-port`; present 容器分支钉 `start 8800 <root> --bind 0.0.0.0 --fixed-port`, 多张展示页经 add-dir 复用同一实例. birth/resume 交付包与 status 输出对 running 容器直接附 web 双 URL, 组装转交给我即可; 容器停止时 status 不附 URL 行, 走 STATE 或 `podman port <容器名> 8800` 查.

**显示栈 (内置)**: 每个工作容器内置 VNC 显示栈 (Xvfb + x11vnc + websockify/noVNC + 中文字体 + playwright chromium + swt-vnc helper, 来自 display 层镜像), 6080 只发布到宿主回环 (127.0.0.1, 多容器并存时动态回落) — 对照: web 8800 发布到 0.0.0.0 直达局域网, 与 6080 回环-only 不同. birth/resume 自动 `podman exec <容器> swt-vnc start` 拉起; 手动开关: `podman exec <容器名> swt-vnc start|stop|status`. headed 浏览器过登录墙: 容器内约定 `BROWSER_HEADED=true` + 选路环境变量 (直通在场用 wayland, 缺席用 `DISPLAY=:99`, 见窗口直飞节), 登录弹窗由你经弹出的窗口/noVNC 或 ssh 人工操作; 登录态 profile 落容器内 /tmp, 容器存续期内跨 ssh 会话复用, rm 即失. 通道体检: `uv run python scripts/swt.py display-check [--name <容器>]` (noVNC HTTP/ws/RFB banner/空白基线/渲染基线 0.2/headless 回切 + wayland 直通探测, PPM 证据落 evidence 目录; 退出码语义见决策协议节例外, 诊断语义非 DECIDE). 门禁语义: birth 跑全量检查, 失败出 DECIDE (继续只开终端 --display-continue / 重验 --display-recheck / terminate 终结); resume 只做 swt-vnc status 级秒级检查, 失败降级不阻断终端工作, STATE 标显示栈状态 + 汇报注明. 容器镜像未含 swt-vnc (旧镜像/极简镜像) → 显示栈缺席 (STATE 标 absent), 跳过不判失败.

**本机直通**: 宿主机存在 wayland socket (本机桌面会话) 时, birth 恒挂进容器并烘 wayland 环境变量 (+ GPU 设备, 缺席不挂; 命令字面见 reference/ops.md). 直挂 socket 属主经 rootless uid_map 映射为容器 root, 0755 属主权下 bolo 连不上 — 解法是 **host 侧 `chmod 0777` 宿主机 socket** (birth/resume 都重保, 登录会话重启会重置); 父目录 `/run/user/<uid>` 为 0700, 其他用户够不着路径, 暴露面≈零. **禁用 socat 中继**: wayland 靠 SCM_RIGHTS 传 fd, 中继截断 fd 传递, chromium 必报 Fatal Wayland communication error. **直通只走 wayland, 禁挂 X11 socket** (X11 协议允许跨客户端键盘嗅探/注入). headed 浏览器优先 `--ozone-platform=wayland` 走宿主机桌面 (原生窗口/GPU/fcitx 中文输入/剪贴板互通), 实测不过回退 `DISPLAY=:99` noVNC. 状态值 ok/degraded/absent 落 STATE 容器记录 `host-display`; 无 socket 环境 (纯服务器宿主) 恒 absent, 行为 = 旧形态.

**窗口直飞 (三态选路)**: 容器内 AI 开 headed 浏览器时的三态 — 宿主直通 wayland / 设备侧 waypipe 直飞 / noVNC 兜底. 执行入口 = 容器固定路径 `/home/bolo/.local/bin/swt-headed-browser.sh` (母本经 birth 换入 chromium 精确路径后只读挂载), 内置 preflight, 本机直通缺席时 exit 86. 完整协议 (容器侧编排/设备侧拉起/远程直飞命令模板/残尸纪律) 见 reference/pull-window.md; 投信走信箱 (reference/mailbox.md). 容器无 headed 脚本 (chromium 路径解析失败) 时交付包打 reason 行, 该容器仅终端 + noVNC, 无直飞.

**多对并存**: 同一主仓可同时有多对 (每个母体分支一对, 各自母体目录 + daemon + 容器), 每对互不可见对方分支: 容器读面只见本对分支, 写面只准快进推本对母体分支. 多个容器同推同一母体 (历史残留或未来放开): 容器只准快进推送, 后推的那个会被 git 以历史分叉为由拒绝 — 容器内 `git fetch` → 解冲突 → 重推 (git 原生串行化, 无新机制).

**kimi 凭证**: 容器内 kimi (Kimi Code CLI) 必须独立登录 (容器内 `kimi` → `/login` 走 OAuth), 禁止把 host 的 kimi 凭证复制进容器两处共用: OAuth refresh token 一次性轮换, 同一份两处用时先刷新者生效, 另一边报 400 invalid grant. swt 注入的 host `~/.pi/agent/auth.json` 若含 kimi OAuth 条目同理 — 容器内要用 kimi 就独立登录, 别复用注入文件里的 kimi 条目.

**母体使用纪律 (转述给我)**: 母体目录是审阅现场: 只读/diff/试跑随意, **禁止编辑跟踪文件** — 母体工作区脏会拒容器 push (推送落地机制自带行为); 未跟踪文件 (编译产物等) 不阻塞. 审阅时不开会自动写文件的工具.

## 恢复 (resume)

```text
uv run python scripts/swt.py resume [--repo <主仓>] [--branch <母体分支名原文>] [--name <容器名>] [--confirm]
```

`--branch`/`--name` 定位对, 都缺省 = 本主仓唯一记录对, 多对时点名消歧. 有 CLI 级 DECIDE gate: 检测到可恢复对象先 exit 1, 我确认后带 `--confirm` 重跑. 序列: 收本对残留 daemon + 旧 git 桥 → 旧形态配置自愈迁移 (见角色边界) → start 容器 → 重拉本对 daemon 并重建桥 → **start 后立即重注入防火墙规则** (合并式 `--merge`, 不做整表清空重建) → 同位置自动重拉显示栈 (幂等 `swt-vnc start` + 秒级检查, 失败降级不阻断) → 重保容器内 git 转发器 → 经桥 git 校验 (固定 remote ls-remote + fetch), 校验通过前不开放工作负载. 就绪判定含 git 通道实测: daemon/桥活但容器 remote 失配 (中途失败或旧形态中间态) 会判为可恢复并重跑收敛, 不卡死. retired 容器 resume 直接 exit 2. pasta 复制配置与宿主当前网络失配 (宿主换过网络) 时打印告警提示重建, 不强制. 交付包与 birth 同规格齐发.
完成标准: 容器 running, 防火墙规则已重注入, git 桥校验通过, 显示栈状态已标注, STATE 反映本对母体分支.

## 终结 (terminate)

```text
uv run python scripts/swt.py terminate [--repo <主仓>] [--branch <母体分支名原文>] [--name <容器名>] [--force]
```

按容器粒度, 候选跨对聚合; `--name` 缺省 = 全部候选唯一时免填, 多个候选必须 `--name` 指定 (可先用 `--branch` 缩小到单对; 旧版 switch 往返留下的 retired 残留也在此列, 但新流程不再产生 retired). **脏检查口径**: 未提交改动 (含未跟踪文件) 算脏; 容器里有而母体没有的提交 (领先或分叉) 算脏, 只是落后于母体不算脏; 查不了 (ssh 不通/容器已停) 一律按脏处理. 脏 → DECIDE 出示脏概要, 文案含 "确认容器内 agent 已停手"; 我确认带 `--force` 重跑, 先写 `audit.jsonl` 审计登记再删. 成功后: 删防火墙规则 → rm 容器 → 本对最后一个容器终结才收本对 daemon (其他对的 daemon 不动). **母体目录与 config 不动**; 母体存删我自决 (删母体走 use-worktree 流程).
完成标准: 目标容器与 (本对最后一个容器时) 本对 daemon 已灭, 母体目录与 config 原样留存, 运行记录与 ssh 私钥已清除.

## 镜像管理 (image-prep)

```text
uv run python scripts/image-prep.py build-base    [--requirements <file>]   # base 层
uv run python scripts/image-prep.py build-display [--requirements <file>]   # display 层 (缺省 image/requirements-browser.md)
uv run python scripts/image-prep.py match      --repo <主仓> [--requirements <file>]
uv run python scripts/image-prep.py build      --repo <主仓> [--requirements <file>]
```

- 三层结构: **base 层** (OS + git + sshd + node + pi CLI + uv + herdr + socat (git 桥双端) + 容器内排障件 + skill 库全量 COPY (运行期被 host 只读挂载遮蔽, 退化为兜底快照) + `~/.pi/agent` 复制) 固定且跨项目共享; **display 层** FROM 当前 base (VNC 栈 + chromium + waypipe, 清单缺省 `image/requirements-browser.md`); **项目层** FROM 当前 display, 由你读项目信号推导依赖件叠加, 清单与我确认后才构建.
- 匹配谓词链: display 须基于当前 base, 项目层须基于当前 display — base 更新后旧 display 自然淘汰, display 更新后旧项目镜像自然淘汰. **base 与 display 都只在我明说时重建**, 无自动检测; display 缺失/过期时项目构建报 `NO-DISPLAY`/`DISPLAY-STALE`, 先 build-display 再 build. skill 纯内容变更不需重建 base (挂载实时生效); pyproject/uv.lock 依赖变更需重建, 否则容器内 venv 种子与 lock 失配且无网重装.
- 需求清单格式, 推导规则 (含 codex env_key 静态配置条目), 匹配规则细节, 版本语义 (tag/digest/contents.md), 记录落点, base 层复制过滤 → reference/image-prep.md.
- image-prep 直用时 match/build 的 `--requirements` 为必填 (birth 内部自动代填缺省路径 `<records-root>/<项目slug>/requirements.md`, 只有绕开 birth 手敲时才需显式给). 旧镜像保留不删.

## 母本与分发

- **agent 提示词母本制**: 母本在仓库内 `agent-prompts/{pi,codex,kimi-code}_AGENTS.md` — 改它 = 改容器内 agent 的行为基线. birth 时拷贝到 `<records-root>/runtime/<identity>/agent-prompts/<容器>/` 留档 (可追溯每容器用了哪版), 再只读单文件挂载进容器: pi → `/home/bolo/.pi/agent/AGENTS.md`, codex → `/home/bolo/.codex/AGENTS.md`, kimi-code → `/home/bolo/.kimi-code/AGENTS.md` (官方文档: 全局指令文件随 KIMI_CODE_HOME, 缺省 `~/.kimi-code/`). 母本更新只对新 birth 的容器生效, 不动运行中容器. 维护纪律: 三母本的通用核逐字相同, 改通用核必须三份同步; 容器契约各行与存续节 (显示栈/窗口直飞) 呼应, 改动两边同步.
- **分发**: 仓库里的改动到达使用现场有两条路, 别混淆 — swt.py / swt-mailbox.py / 本 SKILL.md 与 reference/ (host 侧 agent 读): 仓库根 `uv run python sync-to-pi.py` 同步到 host skills 目录即生效; 设备侧现场是各自的副本, 更新后取信会话重跑脚本即生效 (无扩展, 无后台常驻). `present` skill (容器内): 它是 base 镜像构建期 COPY 进镜像的, 只改仓库文件容器拿不到 — sync-to-pi 后还须重建 base (`image-prep build-base`, 按镜像管理节级联 display/项目层), 之后 birth 的新容器才拿到新版; 现有容器不受影响也不补.

## 环境变量继承 (env.conf)

容器要继承的 host 环境变量列在清单文件里, birth 创建容器时烘入 (`podman create -e`), **改清单须重建容器才生效**:
- 全局: `<records-root>/env.conf`; 项目级: `<records-root>/<项目slug>/env.conf` (同名覆盖全局).
- 每行一条: `NAME` = 值取 host 当前环境 (**文件不存秘密值**); `NAME=value` = 固定值 (仅限非秘密). `#` 开头为注释.
- `NAME` 在 host 未设置: stderr 警告并跳过, 不阻塞 birth.

## 基础服务 (信箱 mesh + LLM 中转)

单文件服务 `scripts/swt-mailbox.py` (纯 stdlib): **信箱** (session 间传信, 设备/容器/本机身份统一为 session, 信件类型 notify/open_url/exec/request) + **LLM 中转** (OpenAI 兼容, sk- key 认证), mesh 架构 — 每台机器一个实例, 邻居间共享密钥互认洪泛路由. birth 自动注册容器 session 并烘入凭证 env, terminate 注销; 信箱缺席只告警不阻断. 网络面 whitelist 已自动放行宿主网关, 无额外 `--allow`.
serve 启动, 设备侧取信配置, 容器侧投信, 展示页网址沟通与代开协议, 指令集 (swt.pull-window) 安全语义, admin 口速查 → reference/mailbox.md. 协议细节 (HMAC 签名/时间窗/防重放/租约重投) 以 `swt-mailbox.py` docstring 与 `docs/changes/swt-mailbox-mesh/TECHNICAL.md` 为准.

## 网络控制 / 容器命令 / 救场

手救场 (防火墙/daemon/config), 换/加容器 provider, 或需要容器操作原生命令时 → reference/ops.md; 脚本原生报错看不懂时 → reference/errors.md (译解表).

## 决策协议 (DECIDE + 收据)

swt 生命周期四子命令 (birth/resume/status/terminate; 旧 switch 已删 — 开新对直接 birth, 不再换母体) 非交互, 一切拍板点:
1. **exit 1 + stdout DECIDE 行**: `DECIDE <id> <kind> <问题人话> 选项: <flag 形态>`; 首次改任何资源前一次列全.
2. 逐字转述给我; 我答后带对应 flag **重跑同一命令**.
3. **决策收据**: DECIDE 开出的一次性票据, 绑定当时的资源状态; 我答后重跑时先比对资源状态, 变了就废票重新问 — 旧答案绝不套到新状态上.
4. 执行中途新冒出的问题不是 DECIDE, 走 exit 3 PARTIAL.

exit code 全子命令统一:

| code | 含义 |
| --- | --- |
| 0 | 成功 (含幂等 no-op) |
| 1 | DECIDE 待我 |
| 2 | 前置不满足 (未动任何资源, 别重试同一命令) |
| 3 | 中途失败可重入 (PARTIAL 文案列唯一人工恢复路径) |
| 4 | 环境错误 (podman/git/nft 缺失或版本不支持) |

stdout 末行 `STATE {...}` 单行 json (只加字段不改名); stderr 首行 `FAIL|PARTIAL|ENV <人话>`, 原生报错原文透传.
例外: 诊断子命令 `display-check` 不参与本表 — 0 全过/1 检查未过/2 传输失败, 无 DECIDE, 无 STATE 行 (见显示栈节).
