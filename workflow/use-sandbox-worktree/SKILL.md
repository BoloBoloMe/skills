---
name: use-sandbox-worktree
description: 管理 sandbox-worktree (host worktree 母体 + sandbox 容器绑定对) 的生命周期与配套镜像/网络/显示栈.
disable-model-invocation: true
---

# use-sandbox-worktree

**术语**:
- **sandbox-worktree**: 一个 host 上的 git worktree (**母体**) + 一个 sandbox 容器的绑定对, 本 skill 管理的生命周期单元. 一母体同一时刻至多一个活跃容器 (活跃 = 非 retired, 含停止未终结): birth 拒绝同母体已有活跃容器, 想换容器须先 terminate; 一台 host 可有多个母体, 各自独立; 改动前已存在的容器不追溯处置.
- **母体**: 主仓在 host 上的一个 worktree 目录 (与主仓同级的兄弟目录, 目录名 = 母体分支名), 身兼两职: 容器诞生时从它克隆代码; 容器 push 的成果直接落进它, 打开就能审阅/试跑.
- **推送落地**: 容器 `git push` 被接受的瞬间, 母体目录里的文件自动更新成 push 内容, 不用手动 pull.
- **git 守护进程 (daemon)**: 随容器生灭临时起的 `git daemon` 进程, 只听宿主回环 (127.0.0.1 动态端口), 容器碰到代码的唯一通道, 无认证.
- **git 桥**: 容器访问 daemon 的固定通道; 容器 remote 恒定 `git://127.0.0.1:9418/<仓库名>`, daemon 端口漂移/host 换网络都不再失配 (机制见 reference/ops.md).
- **交付包**: birth/resume 收尾必须齐发的一组交付 — ssh 双入口 + noVNC URL + web 双 URL + 局域网隧道命令 + herdr remote 双命令 + 本机直通状态 + 远程直飞命令模板 (容器带 headed 启动脚本时; 见存续节 窗口直飞) + 登录凭证 + 容器内路径契约 + 风险声明 (reference/risks.md). web 双 URL = 本机 `http://127.0.0.1:<web-port>` 与局域网 `http://<已确认地址>:<web-port>`, 只列当前母体自身容器, 不汇总其他母体; 分享出去的 URL 不保证跨容器重建稳定 (容器 rm 重建后宿主端口会变, 须重新取新 URL). 各项形态见 birth 第四步.

元规则: 本文件机制细节与环境现实冲突时, 以环境硬约束 (git 配置/防火墙/拓扑) 为准并报告我.
**命名消歧**: `swt` = host 编排脚本 `scripts/swt.py`; `swt-vnc` = 容器内 VNC 栈 helper (见显示栈节), 两者无关.

## 角色边界

- 你 (host 侧 agent) 只管理生命周期, 不进容器干活.
- 一切需我拍板的点由脚本以 DECIDE 行表达 (见决策协议节): 逐字转述给我, 我答后带 flag 重跑同一命令, 替我作答即违规.
- 真远端 (github 等) 对容器完全不暴露; 主仓 config 常驻 (残余影响见 reference/risks.md).

## 环境前置

- rootless podman (pasta 网络), nftables, git (须支持配置里 "隐藏所有分支、只放行一个" 的 `hideRefs` 写法; birth 每次会建一次性小仓库实测确认, 不支持则 exit 4).
- `uv run python` 运行全部脚本; 脚本路径相对本 skill 目录引用.
- 记录根缺省 `~/.agents/sandbox-worktree/` (运行状态/决策收据/审计/镜像构建记录同屋), 全部脚本支持 `--records-root` 覆盖.
- host skill 库 `~/.agents/skills/` 全树全局可读 (容器 bolo 经 rootless uid 映射只靠 other 位读它); 带依赖的 skill 项目须携带已部署的 uv.lock.

## 入口: status 先行

```text
uv run python scripts/swt.py status [--repo <主仓>]
```

`--repo` 缺省从 cwd 推导主仓. status 只读, 读末行 `STATE {...}` 分流: 有停着的容器/残留的 daemon/缺防火墙规则 → resume; 无任何记录 → birth; 有 retired 容器 → 唯一出路 terminate (resume 拒绝).
完成标准: 已据 STATE 判定走 birth / resume / terminate 之一.

## 诞生 (birth)

**第零步: 先用 `use-worktree` skill 为项目创建工作树分支**
母体不是本 skill 自创的命名, 必须走 use-worktree 的建树流程产出: 分支名 = 目标分支名原文, 目录名 = 它的 slug 规则 (<项目>-<来源分支>-<目标分支>). 后续 birth 的 `--branch` 传目标分支名原文, 脚本按分支名识别已有母体并走 reuse 决策. 未建树先 birth 会在 DECIDE/断言处卡住, 别绕.

**第一步: 网络模式与白名单盘点**
创建容器前必须与我确认网络模式, 运行期不切换:
- **whitelist** (默认拒, 推荐): 只放行 网关 DNS + `--allow` 条目 + 已建立连接的返程流量 (保住 host 发起的 ssh), 其余容器流出全断. git 走 unix socket 桥, 不占网络白名单; 网关自动放行的残余暴露见 reference/risks.md.
- **blacklist** (默认放行): 只断 `--deny` 条目, 护 host 侧特定服务 (数据库/redis 等) 场景.
盘点方法论: 与我一起列出容器工作所需站点, **域名须解析为具体 IP/CIDR 后传入** (防火墙规则只认 IP, 脚本拒收域名); 条目是 IP 级, 放行即全端口. 站点换 IP 失效时重新盘点. 运行期新站点需求的处理形态未定, 发生时带回本会话问我.

**第二步: 镜像判定与制备**
birth 内部自动跑 image-prep `match`, 需求清单取 `<records-root>/<项目slug>/requirements.md` (或 `--requirements` 指定):
- **清单文件不存在 → birth exit 2, 这是首次为项目建镜像的入口**: 你读项目信号 (AGENTS.md/README/package.json/pyproject.toml 等) 推导依赖件写成需求清单 (格式见镜像管理节), **展示清单与我确认后才落盘** — 装依赖会运行其安装脚本, 风险与日常装包同级, 确认时向我明示; 落盘后重跑 birth.
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
母体分支名 = use-worktree 目标分支名原文, 母体目录名 = 它的 slug 规则生成; 容器缺省名 `swt-<分支名>`, `--name` 只用于自定义名 — 同母体活跃容器唯一 (见术语), 它不再是放行第二个容器的开关. 首次执行通常出 DECIDE (母体新建/复用, 网络模式, 镜像), 按决策协议节应答.

**第四步: 交付包**
交付包逐项向我报告 (缺发只允许以一种形式发生: 显式打原因; 不静默丢失):
- ssh 入口 (两条带端口, 总是同时交付; pasta 下容器无独立 IP — STATE 的 `network-ip` = host 本机 IP, 直连形式已废除):
  - 本机: `ssh -p <宿主端口> bolo@127.0.0.1` — 跨 stop/start 稳定, 用 `podman port <容器名>` 或 STATE 的 `ssh-port` 发现, 不记录端口 (rm 重建才变).
  - 局域网: `ssh -p <宿主端口> bolo@<host-LAN-IP>` — 远程机走同一条带端口命令. `<host-LAN-IP>` 一律取已确认值, 不猜首个网卡: 确认值持久化在 records_root 根级, 首次 birth 无确认值时出 DECIDE 问 (现算候选只作提示, 不当可达交付), 我答后带 `--lan-ip <ipv4>` 重跑即确认; 换网络环境后用同一 flag 覆盖.
- noVNC URL (本机浏览器直接开): `http://127.0.0.1:<vnc宿主端口>/vnc.html?resize=scale` — 容器内显示栈已自动拉起并经 birth 全量检查; 实际端口看 STATE 的 `vnc-port`.
- web 双 URL (容器对外展示入口, 容器有 web-port 才发): 本机 `http://127.0.0.1:<web-port>` / 局域网 `http://<已确认地址>:<web-port>` — web-port 看 STATE 容器记录; 只列本容器; 无已确认局域网地址时打 "未附发" 提示行, 不猜地址; birth 只交付入口, 不因容器出生自动打开页面.
- 本机直通状态: STATE 容器记录 `host-display=ok` 时交付注明 — 登录墙等 headed 窗口直接弹宿主机桌面, 本机可不开 noVNC; `degraded` 注明已回退 noVNC; `absent` 打一行常态说明 (远程/纯服务器宿主).
- 局域网隧道命令: `ssh -p <宿主端口> -L 6080:127.0.0.1:<vnc宿主端口> bolo@<host-LAN-IP>` — 我在远程机开这条隧道后, 浏览器开 `http://127.0.0.1:6080/vnc.html?resize=scale`; noVNC 无密码, 隧道 (即容器 ssh 凭据) 就是门槛.
- 登录凭证 (两种, 都随 terminate 清除, 落 `<records-root>/runtime/<identity>/ssh/`, 0600):
  - 密码: 固定 `sandbox` (用户拍板, 风险见 reference/risks.md), `<容器名>.password` 留档; 人登录用.
  - 密钥: `<容器名>.ed25519` (`ssh -i <私钥> ...`), 脚本/herdr 的 BatchMode 走它.
- herdr remote (走 ssh, 容器无需预启 server, remote attach 按需拉起): 两条完整可直接复制的命令 — 我在本机用 `herdr --remote ssh://bolo@127.0.0.1:<宿主端口>`, 我在局域网远程机上用 `herdr --remote ssh://bolo@<host-LAN-IP>:<宿主端口>`. 我会在本机和远程机之间来回切换; 远程机上 ssh 用的私钥需先从 host 拷贝 (路径见上), 或直接用密码. 该命令须在非 herdr 终端运行 (herdr 会话内被套娃禁用拦截); 已在 herdr 里则走开窗格配方 (存续节).
- 容器内路径契约: 用户 `bolo` (home 与 host 字面相同), 代码固定克隆在 `/home/bolo/Workspace/<分支名>` (当前分支 = 母体分支); skill 库在 `~/.agents/skills/` (运行期从 host 同路径只读挂载, 实时跟随 host 版本; 项目 `.venv` 是镜像播种的可写匿名卷), pi 配置在 `~/.pi/agent/`.
- 风险声明: 连同 reference/risks.md 的风险项一起声明.
完成标准: STATE `stage=born`, 容器内检出分支 = 母体分支, 交付包齐发 (显示栈降级/缺席时相应项改为降级/常态说明, 其余照发).

## 存续

**ssh 入容器**: 经上方入口进容器驱动 pi 干活. 产物回流 = 容器内 `git push` (只允许历史只增不改的快进推送), **推送落地**使母体目录文件即时更新, host 直接审阅/试跑. 推送落地有秒级短延迟 (push 返回后文件稍后可读).

**herdr 接入与委派配方**: herdr 在 base 层 (容器内可直接用); 要从 host herdr 工作区总览容器内 pi, 就在 host 侧开窗格 `HERDR_AGENT=pi ssh -p <端口> -i <私钥> bolo@127.0.0.1`, host herdr 经 env 提示把容器内 pi 识别为一等 agent. 委派配方:
1. `herdr agent get` 确认 idle — blocked/working 态不发 (无 guard 会把键打进错误界面).
2. `herdr pane send-text` 发任务文本.
3. 提交键 = 读容器内 `~/.pi/agent/keybindings.json` 的 `tui.input.submit` 首键 (跟随我的键位配置; 本机为 `alt+\`), 兜底 alt+enter.
4. `herdr agent wait` / `agent read` 收结果.
这套做法只是一层交互式编排的适配: 没有任务 id/退出码/重试保证; 需要这些保证时用保底形态 `pi -p "<任务>"` 批处理 (绕开 TUI 键位注入, 一轮一进程).

**展示链**: 容器内展示由 `present` skill 的容器分支全权负责 (判定/bind/端口/url 语义见其 "容器内分支" 节): 容器对外 web 端口固定 8800, birth 把它发布到宿主 0.0.0.0 动态端口 (直达局域网, 映射登记 STATE 容器记录 `web-port`), present 容器分支钉 `start 8800 <root> --bind 0.0.0.0 --fixed-port` (锁定不换端口, 多张展示页经 add-dir 复用同一实例). 你侧不再只靠 `podman port` 发现 — birth/resume 交付包与 status 输出对有 web-port 的容器直接附 web 双 URL (本机 + 局域网已确认地址), 组装转交给我即可; 容器停止时 status 不附 URL 行, 走 STATE/`podman port <容器名> 8800` 查.

**显示栈 (内置)**: 每个工作容器内置 VNC 显示栈 (Xvfb + x11vnc + websockify/noVNC + 中文字体 + playwright chromium + swt-vnc helper, 来自 display 层镜像), 6080 只发布到宿主回环 (127.0.0.1, 多容器并存时动态回落). 对照: web 8800 发布到宿主 0.0.0.0 动态端口, 直达局域网 (无认证, 已接受对同网段开放, 见展示链节), 与 6080 回环-only 不同. birth/resume 自动 `podman exec <容器> swt-vnc start` 拉起; 手动开关: `podman exec <容器名> swt-vnc start|stop|status`. headed 浏览器过登录墙: 容器内约定 `BROWSER_HEADED=true` + 选路环境变量 (直通在场用 wayland, 缺席用 `DISPLAY=:99`, 见下段), 登录弹窗由你经弹出的窗口/noVNC 或 ssh 人工操作; 登录态 profile 落容器内 /tmp, 容器存续期内跨 ssh 会话复用, rm 即失. 通道体检: `uv run python scripts/swt.py display-check [--name <容器>]` (noVNC HTTP/ws/RFB banner/空白基线/渲染基线 0.2/headless 回切 + wayland 直通探测, PPM 证据落 evidence 目录; 退出码语义见决策协议节例外, 诊断语义非 DECIDE). 门禁语义: birth 跑全量检查, 失败出 DECIDE (继续只开终端 --display-continue / 重验 --display-recheck / terminate 终结); resume 只做 swt-vnc status 级秒级检查, 失败降级不阻断终端工作, STATE 标显示栈状态 + 汇报注明. 容器镜像未含 swt-vnc (旧镜像/极简镜像) → 显示栈缺席 (STATE 标 absent), 跳过不判失败.

**本机直通**: 宿主机存在 wayland socket (本机桌面会话) 时, birth 恒挂进容器并烘 wayland 环境变量 (+ GPU 设备, 缺席不挂; 命令字面见 reference/ops.md). 直挂 socket 属主经 rootless uid_map 映射为容器 root, 0755 属主权下 bolo 连不上 — 解法是 **host 侧 `chmod 0777` 宿主机 socket** (birth/resume 都重保, 登录会话重启会重置); 父目录 `/run/user/<uid>` 为 0700, 其他用户够不着路径, 暴露面≈零. **禁用 socat 中继**: wayland 靠 SCM_RIGHTS 传 fd, 中继截断 fd 传递, chromium 必报 Fatal Wayland communication error. headed 浏览器优先 `--ozone-platform=wayland` 走宿主机桌面 (原生窗口/GPU/fcitx 中文输入/剪贴板互通), 实测不过回退 `DISPLAY=:99` noVNC. **直通只走 wayland, 禁挂 X11 socket** (X11 协议允许跨客户端键盘嗅探/注入). 状态值 ok/degraded/absent 落 STATE 容器记录 `host-display`; 无 socket 环境 (纯服务器宿主) 恒 absent, 行为 = 旧形态.

**窗口直飞 (三态选路)**: 容器内 AI 开 headed 浏览器时的三态 — 宿主直通 wayland / 设备侧 waypipe 直飞 / noVNC 兜底 (D007 判定拆分: 机械判定在代码, 编排在本节). 执行入口 = 容器固定路径 `/home/bolo/.local/bin/swt-headed-browser.sh` (母本 `headed-browser/swt-headed-browser.sh` 经 birth 换入 chromium 精确路径后只读挂载, UD-06): 内部先 preflight — `WAYLAND_DISPLAY` 与 `XDG_RUNTIME_DIR` 在场且 `$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY` 可连才启动 chromium; 不满足 **exit 86**, 容器 AI 见 86 即投信, 不重试脚本 (UD-11). 脚本内部条件导出 `PULSE_SERVER=unix:/tmp/swt/pulse-b.sock` (socket 在场才导, 宿主直通模式硬导会断本地音频, UD-08) 后 `exec chromium --no-sandbox --ozone-platform=wayland`; env 由脚本内部设置, 命令行禁止 `VAR=...` 赋值前缀 (N1: waypipe 把前缀当程序名, Spawn failure).

容器侧编排 (preflight 退出 86 后):
1. **投信前记基线**: `ls /tmp/waypipe-server-*.sock 2>/dev/null` 记现有 token 集 — 异常死亡的会话会留 socket 尸体 (N2), 判活只看新 token 差集.
2. **投信**: exec 类型信, `to` 显式填当前设备 (定设备纪律见基础服务节 展示页网址沟通与代开), body 为 JSON: `{"tool": "swt.pull-window", "container": "<SWT_CONTAINER_NAME>"}`. 服务端形状校验 + container 动态绑定投信容器自身 (UD-05), 命中直批不问人 (指令能力极窄且无参数注入面, D008).
3. **等 ack 后轮询**: ack 只证明信被设备取走, 不证明窗口拉起 — 轮询容器内 `/tmp/waypipe-server-*.sock` 出现基线之外的新 token (F005), 超时 **120s** (UD-02). 新 token 出现 = 窗口已落在设备屏, 后续经 playwright/CDP 自己导航.
4. **超时落兜底**: 120s 未出新 token → 落 noVNC (`DISPLAY=:99`), 并在回复中明确告知用户落了兜底.

设备侧 (取信会话收到 swt.pull-window 信; 扩展代码先做机械门禁 (UD-07 分层: 代码管机械判定, 本配方管编排): waypipe 缺席 → 设备本地 notify 安装提示 + 立即 ack `skipped:waypipe-missing`; 同容器 300s 窗内重复 → ack `skipped:rate-limited`; 两种都不转化为 LLM 轮 (UD-10)):
1. **前提**: 设备 Linux Wayland 桌面会话 + waypipe 客户端; Atomic 系发行版 (Bazzite 等) 经 distrobox 安装 (D006).
2. **密钥**: 设备→容器 ssh 免密经 host 上 `uv run python scripts/swt.py enroll-device-key <容器名>` 一次性发放 (N4: 密码登录无法自动化代执行).
3. **幂等探测**: `ssh <容器> pgrep -x waypipe` — 已有活跃会话直接回报不再拉起 (D008 幂等; N2 修正: 不用 socket 存在判活, 尸体会残留).
4. **后台拉起** (即交付包远程直飞模板, 变量照交付包实际值代换): `nohup waypipe ssh -p <宿主端口> -R /tmp/swt/pulse-b.sock:/run/user/$(id -u)/pulse/native bolo@<host-LAN-IP> /home/bolo/.local/bin/swt-headed-browser.sh >/dev/null 2>&1 &` — `-R` 同一条会话建音频 socket (D002; 远端路径由设备 shell 展开实际 uid, 不写死 1000, UD-09); waypipe 会话须长存, 不能占 LLM 前台, 故 nohup 后台.
5. **回报**: 拉起后经 herdr notification 通知设备用户窗口已送达.

残尸纪律: 容器侧不做 waypipe 残尸清理 (UD-12), 旧 token 不挡差集判定; `pulse-b.sock` 残渣由 base 层 sshd `StreamLocalBindUnlink yes` 治理. ssh 会话的 `XDG_RUNTIME_DIR=/tmp/xdg-1001` 由 base 镜像 sshd_config SetEnv 烘配 (UD-03, 固定常量 uid), waypipe server 才有落 display socket 的位置. 容器无 headed 脚本 (chromium 路径解析失败, UD-06) 时交付包打 reason 行, 该容器仅终端 + noVNC, 无直飞.

**同母体多容器**: 新规则下同母体活跃容器唯一 (见术语), 常态不再出现多容器共推同一母体; 改动前已存在的容器不追溯处置, 历史残留仍可能多容器并存. 若真有两个容器同推一母体: 容器只准快进推送, 后推的那个会被 git 以历史分叉为由拒绝: 容器内 `git fetch` → 解冲突 → 重推 (git 原生串行化, 无新机制).

**kimi 凭证**: 容器内 kimi (Kimi Code CLI) 必须独立登录 (容器内 `kimi` → `/login` 走 OAuth), 禁止把 host 的 kimi 凭证复制进容器两处共用: OAuth refresh token 一次性轮换, 同一份两处用时先刷新者生效, 另一边报 400 invalid grant. swt 注入的 host `~/.pi/agent/auth.json` 若含 kimi OAuth 条目同理 — 容器内要用 kimi 就独立登录, 别复用注入文件里的 kimi 条目.

**母体使用纪律 (转述给我)**: 母体目录是审阅现场: 只读/diff/试跑随意, **禁止编辑跟踪文件** — 母体工作区脏会拒容器 push (推送落地机制自带行为); 未跟踪文件 (编译产物等) 不阻塞. 审阅时不开会自动写文件的工具.

## 恢复 (resume)

```text
uv run python scripts/swt.py resume [--repo <主仓>] [--name <容器名>] [--confirm]
```

有 CLI 级 DECIDE gate: 检测到可恢复对象先 exit 1, 我确认后带 `--confirm` 重跑. 序列: 收残留 daemon + 旧 git 桥 → start 容器 → 重拉 daemon 并重建桥 → **start 后立即重注入防火墙规则** (合并式 `--merge`, 不做整表清空重建) → **同位置自动重拉显示栈** (幂等 `swt-vnc start` + status 级秒级检查, 失败降级不阻断) → 重保容器内 git 转发器 → 经桥 git 校验 (固定 remote ls-remote + fetch), 校验通过前不开放工作负载. 就绪判定含 git 通道实测, daemon/桥活但容器 remote 失配 (中途失败留下的中间态) 会判为可恢复并重跑收敛, 不卡死. retired 容器 resume 直接 exit 2; 运行记录里的母体分支 ≠ 当前放行分支也 exit 2. pasta 复制配置与宿主当前网络失配 (宿主换过网络) 时打印告警提示重建, 不强制. 交付包与 birth 同规格齐发.
完成标准: 容器 running, 防火墙规则已重注入, git 桥校验通过, 显示栈状态已标注, STATE 反映当前放行的母体分支.

## 换母体 (switch, 危险独立入口)

```text
uv run python scripts/swt.py switch [--repo <主仓>] --to <目标分支名原文> [--force]
```

同一主仓同一时刻只有一个分支对容器开放写. 换母体 = 停旧母体容器 (常态唯一, 历史残留可能多个) +daemon → 删防火墙规则 → 校验目标 → 改主仓 config 里放行的分支名. 旧容器**不删**, 标 **retired**: status 可见, resume 拒绝, 唯一出路 terminate (走正常脏检查). 想捡回旧分支 → switch 回去或重新 birth. 旧母体容器先脏检查, 脏 → DECIDE + `--force`. 目标母体分支不存在: 允许 (写面对象暂缺, 随后 birth 再建); 分支存在但母体工作区脏 / 无对应 worktree → exit 2.
完成标准: 旧容器全停并标 retired, config 里放行的分支已指向新目标, status 显示新母体.

## 终结 (terminate)

```text
uv run python scripts/swt.py terminate [--repo <主仓>] [--name <容器名>] [--force]
```

按容器粒度; `--name` 缺省 = 该母体只有一个候选容器时免填, 多个候选 (含 switch 往返留下的 retired 残留 + 新活跃容器) 必须 `--name` 指定 (`--name` 兼容保留, 但多容器不再是常态). **脏检查口径**: 未提交改动 (含未跟踪文件) 算脏; 容器里有而母体没有的提交 (领先或分叉) 算脏, 只是落后于母体不算脏; 查不了 (ssh 不通/容器已停) 一律按脏处理. 脏 → DECIDE 出示脏概要, 文案含 "确认容器内 agent 已停手"; 我确认带 `--force` 重跑, 先写 `audit.jsonl` 审计登记再删. 成功后: 删防火墙规则 → rm 容器 → 最后一个容器终结才收 daemon. **母体目录与主仓 config 不动**; 母体存删我自决 (删母体走 use-worktree 流程).
完成标准: 目标容器与 (最后一个容器时) daemon 已灭, 母体目录与主仓 config 原样留存, 运行记录与 ssh 私钥已清除.

## 镜像管理 (image-prep)

```text
uv run python scripts/image-prep.py build-base    [--requirements <file>]   # base 层
uv run python scripts/image-prep.py build-display [--requirements <file>]   # display 层 (缺省 image/requirements-browser.md)
uv run python scripts/image-prep.py match      --repo <主仓> [--requirements <file>]
uv run python scripts/image-prep.py build      --repo <主仓> [--requirements <file>]
```

- 三层结构: **base 层** (OS+git+sshd+node+pi CLI+uv+fd+rg+python3+herdr+socat (git 桥双端)+iproute2 (容器内排障) + skill 库全量 COPY (运行期被 host 只读挂载遮蔽, 退化为兜底快照) + `~/.pi/agent` 复制 (排除 auth.json/sessions/AGENTS.md — AGENTS.md 走母本制, 见下节), sshd_config SetEnv 烘配非交互 PATH 含 `~/.local/bin`) 固定且跨项目共享; **display 层** FROM 当前 base (VNC 栈 + chromium + swt-vnc, 清单缺省 `image/requirements-browser.md`), 记录落 `<records-root>/display/builds/`; **项目层** FROM 当前 display, 由你读项目信号推导依赖件叠加, 清单与我确认后才构建.
- 匹配谓词链: display 层自身须基于当前 base, 项目层须基于当前 display — base 更新后旧 display 自然淘汰, display 更新后旧项目镜像自然淘汰.
- **base 与 display 都只在我明说时重建**, 无自动检测; display 缺失/过期时项目构建报 `NO-DISPLAY`/`DISPLAY-STALE`, 先 build-display 再 build. skill 纯内容变更不需重建 base (挂载实时生效); pyproject/uv.lock 依赖变更需重建, 否则容器内 venv 种子与 lock 失配且无网重装.
- 需求清单条目 = 名称 + 版本要求 (`>= <= > < ==` 或裸名称), 指令 `install=`/`probe=` (探测缺省 `<name> --version`); apt 条目必须写 `install=` (只写 probe 不装包).
- image-prep 直用时 match/build 的 `--requirements` 为必填 (birth 内部会自动代填缺省路径 `<records-root>/<项目slug>/requirements.md`, 只有绕开 birth 手敲 image-prep 时才需显式给).
- **推导规则: 项目层清单含 codex (或其他支持 env_key 的 llm CLI) 时, 必须附静态配置条目** — 以 codex 为例: `codex-config install="mkdir -p /home/bolo/.codex && echo <config.toml 的 base64> | base64 -d > /home/bolo/.codex/config.toml && chown -R bolo:bolo /home/bolo/.codex" probe="grep -c . /home/bolo/.codex/config.toml"`; 配置文件零秘密, 密钥走 `env_key` 指向 env.conf 继承的环境变量, 禁止把密钥写进清单/镜像/文件. 参照实现: `<records-root>/skills/requirements.md`.
- 匹配规则: 按镜像 label 找候选取最新构建 → 需求逐项版本满足 + 硬性条件 "基于当前 display 构建" → REUSE, 否则 BUILD-NEW (display 缺失时报 BUILD-NEW + reason, 不硬崩). 旧镜像保留不删.
- 版本语义: tag = 日期-序号 (人读索引), digest = 镜像内容哈希即精确版本; contents.md = 构建后**实测**清单.
- 记录落 `<records-root>/<slug>/builds/<build-id>/` (Containerfile/requirements.md/contents.md/build.json), 不落项目 git.
- 扩展过滤 (白名单心智): 复制 `~/.pi/agent` 时 extensions/ 只排除显式点名的门禁类扩展 (filesystem-operation-gate / git-operation-gate / python-operation-hook, 名单落 image-prep.py 注释), 其余扩展 (含 repetition-guard/herdr-agent-state) 与未来新扩展默认进容器; host 环境文档 (`~/AGENTS.md`/`~/docs/`) 不进容器.

## agent 系统提示词母本制

- 母本在仓库内 `agent-prompts/{pi,codex,kimi-code}_AGENTS.md` — 改它 = 改容器内 agent 的行为基线.
- birth 时拷贝到 `<records-root>/runtime/<identity>/agent-prompts/<容器>/` 留档 (可追溯每容器用了哪版), 再只读单文件挂载进容器: pi → `/home/bolo/.pi/agent/AGENTS.md`, codex → `/home/bolo/.codex/AGENTS.md`, kimi-code → `/home/bolo/.kimi-code/AGENTS.md` (官方文档: 全局指令文件随 KIMI_CODE_HOME, 缺省 `~/.kimi-code/`).
- 生效语义: 母本更新只对新 birth 的容器生效, 不动运行中容器 (每容器一份留档副本, 互不影响).
- 维护纪律: 三母本的通用核逐字相同, 改通用核必须三份同步; 容器契约各行与存续节 (显示栈/登录墙) 呼应, 改动两边同步.

## 环境变量继承 (env.conf)

容器要继承的 host 环境变量列在清单文件里, birth 创建容器时烘入 (`podman create -e`), **改清单须重建容器才生效**:
- 全局: `<records-root>/env.conf`; 项目级: `<records-root>/<项目slug>/env.conf` (同名覆盖全局).
- 每行一条: `NAME` = 值取 host 当前环境 (**文件不存秘密值**); `NAME=value` = 固定值 (仅限非秘密). `#` 开头为注释.
- `NAME` 在 host 未设置: stderr 警告并跳过, 不阻塞 birth.

## 基础服务 (信箱 + LLM 中转)

**是什么**: host 常驻单体 web 服务 `scripts/swt-base-server.py` (纯 stdlib, 零第三方依赖), 二合一: **信箱** (容器→设备单向传话, 无回程队列 — 设备回话走既有 ssh/herdr 通道) + LLM 中转 (OpenAI 兼容 `/v1/chat/completions` 与 `/v1/models`, sk- key 认证, 模型白名单/quota/用量/过期/吊销, 响应上游不透 stream). 消息/设备/容器 key/已见 id/指令集全落 host SQLite (`~/.local/state/swt-base-server/server.db`), 重启完整恢复; 已处理消息 7 天滚动删除. 端口: 服务口区间 38417-38426 启动绑首个空闲, 无认证 `GET /__identity__` 供探测身份; admin 口默认 38416 (`SWT_ADMIN_PORT` 可配) 硬绑 127.0.0.1 (header `X-Admin-Token`, 容器够不着). 实际端口与 admin token 写状态文件 `~/.local/state/swt-base-server/state.json` (0600), 同机组件读文件免扫描. 上游配置走 env `SWT_UPSTREAM_BASE`/`SWT_UPSTREAM_KEY`.

**怎么起**: systemd user unit 常驻, 单元文件 `scripts/swt-base-server.service`, 部署命令见文件头注释 (cp 到 `~/.config/systemd/user/` + `systemctl --user` + linger). 手动起 (调试): `uv run python scripts/swt-base-server.py`.

**容器侧怎么投信**: birth 自动接线, 零手工 — 探测服务 (读状态文件, 缺席扫区间 `__identity__`; 状态文件命中也先做一次 `__identity__` 验活, 失活则弃文件退扫描 — 重启换 admin token, 旧文件凭证不可信) → 经 admin 口申领容器 key (作用域 = 全 4 类型 + 全目标) → env 烘入容器 (`SWT_BASE_URL`/`SWT_MAILBOX_KEY`/`SWT_CONTAINER_NAME`, podman -e + ssh 面 `~/.ssh/environment` 双通道). 服务缺席或 admin 凭证不可得 → stderr 告警 + runtime 记 skipped, 不阻断 birth; 重入不重复申领 (容器已存在则 env 不重烘). 网络面 whitelist 已自动放行宿主网关, 无额外 `--allow`. 投信 = `POST $SWT_BASE_URL/mailbox/post`, 4 类型 `notify`/`open_url`/`exec`/`request`; 签名式 `sig = HMAC(SWT_MAILBOX_KEY, sig_ts\nid\nbody)`, 响应用同 key 签名可验. 最小示例 (容器内 stdlib):

```python
import hashlib, hmac, json, os, time, urllib.request, uuid
base, key = os.environ["SWT_BASE_URL"], os.environ["SWT_MAILBOX_KEY"]
envelope = {"id": uuid.uuid4().hex, "ts": time.time(),
            "from": os.environ["SWT_CONTAINER_NAME"], "to": "",  # 空 = 最近活跃设备
            "type": "notify", "body": "任务完成, 请过目"}
sig_ts = str(time.time())
sig = hmac.new(key.encode(), f"{sig_ts}\n{envelope['id']}\n{envelope['body']}".encode(),
               hashlib.sha256).hexdigest()
req = urllib.request.Request(base + "/mailbox/post",
    data=json.dumps({"key": key, "envelope": envelope, "sig_ts": sig_ts, "sig": sig}).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
print(json.load(urllib.request.urlopen(req)))
```

协议细节 (错误响应也签名/时间窗 ±5min/防重放) 以 `swt-base-server.py` docstring 与 `tests/test_swt_base_server.py` e2e 为准.

**设备侧怎么收取信会话**: 组件 = pi 扩展 `swt-mailbox-relay.ts` + 阻塞取信脚本 `swt-mailbox-fetch.mjs` (同目录, 经仓库根 `sync-to-pi.py` 同步到 pi 扩展目录). 先经 admin 口发设备凭证 (三元组手工复制一次):

```bash
TOKEN=$(jq -r .admin_token ~/.local/state/swt-base-server/state.json)
curl -s -H "X-Admin-Token: $TOKEN" -H "Content-Type: application/json" \
  -X POST http://127.0.0.1:38416/admin/devices -d '{"name":"<设备名>"}'
# 应答: {device, signing_key, response_key}
```

配置落设备 `~/.config/swt/mailbox.json` (env `SWT_MAILBOX_CONFIG` 覆盖路径):

```json
{
  "server": "http://127.0.0.1:38417",
  "device": "<设备名>",
  "signing_key": "<发放值>",
  "response_key": "<发放值>"
}
```

跨机取信推荐 `ssh -L 38417:127.0.0.1:<host端口> bolo@<host-LAN-IP>` 本地转发 (全程加密), 配置 server 指本地端口; 裸连局域网+签名是降级路径. **取信会话**全部手动首启, 不开机自启: host 上开在当前会话 tab 的窗格, 其他设备开固定命名 tab `S-swt-relay-1`; 扩展 session_start 自动后台拉起脚本长轮询 (空转零 token), 来信经 triggerTurn 唤醒 LLM 处理, 该轮收尾后自动 ack 回报服务端.

**admin 口速查** (127.0.0.1:38416, header `X-Admin-Token`, token 读状态文件):
- 发凭证: `POST /admin/devices {name}` / `POST /admin/container-keys {container, allow_types, allow_targets}` / `POST /admin/relay-keys {models, quota?, ttl_seconds?}`
- 吊销: `POST /admin/{devices,container-keys,relay-keys}/revoke` (体 `{name}` 或 `{key}`)
- 查询: `GET /admin/stats`, `/admin/devices`, `/admin/container-keys`, `/admin/relay-keys`, `/admin/messages[?status=queued|delivered|processed]`
- **指令集**注册: `POST /admin/whitelist {instruction}` (instruction = 含 `tool` 的结构化指令对象)

**指令集现状**: 首成员已落地 — `swt.pull-window` (零参数拉窗, D008): 不落静态 whitelist 行, 服务端内置形状校验 (dict 恰含 `tool`/`container` 两键) + `container` 动态绑定投信容器自身 (UD-05; 裸 tool/多余键/他人容器名一律降级 request 走设备侧 pi 权限流程); admin whitelist 注册机制保留, 供未来无动态绑定的成员使用. 设备侧执行器机械门禁: waypipe 在场检查 + 同容器 300s 限频 (UD-07/UD-10). 成员变动即安全策略变动, 必过 e2e 门禁 (`uv run pytest tests/test_swt_base_server.py`).

**展示页网址沟通与代开 (容器与设备 agent 行为指引)**: 容器内展示页就绪后要到我当前用的电脑上打开一次, 网址容器自己查不到 (host 才知道映射), 靠信箱问设备侧取信会话代查代开. 本节全部是指引, 不新增任何接口.

容器侧 (投信方) 检查清单:
1. **先定当前设备**: 每次开始工作时确定本次使用的电脑 — 会话已有信息或我明示的优先, 不能确定才问我一次并记住; 我换电脑时更新.
2. **展示相关信件 `to` 显式填该设备名, 禁止留空**: 缺省路由 = 最近轮询的设备, 最近取信不等于我坐在那台设备前 (两台设备同时取信时落在哪台纯看轮询时序). 其它与设备无关的信件仍按原协议, `to` 留空走缺省.
3. **body 必带四样**: (a) 容器名; (b) 宿主定位 — 目的是让设备 agent 能在 host 上定位到该容器: 容器报自己可见的主仓路径与容器名作线索 (容器内 home 与 host 字面相同, 但 records_root 是 host 侧路径且可被 `--records-root` 覆盖, 容器只能按默认值推断, 设备侧不把容器报的路径当必然可解析, 查不到时用容器名 + podman/STATE 兜底); (c) 原会话标识 — 使回话能回到发起会话; (d) 请求动作 — 查网址 / 就绪代开.
4. 完整示例信 (request 类型, 签名与发送代码同上文 notify 最小示例, 只换 envelope):

```python
envelope = {"id": uuid.uuid4().hex, "ts": time.time(),
            "from": os.environ["SWT_CONTAINER_NAME"], "to": "<当前设备名>",
            "type": "request",
            "body": ("container=<容器名>\n"
                     "host-repo=<主仓在 host 的路径>\n"
                     "records=<records_root 路径>\n"
                     "session=<原会话标识, 回话时引用>\n"
                     "action=查该容器 web 入口双 URL 并回告本会话; 页面就绪后在本设备打开一次")}
```

设备侧 (取信会话) 检查清单:
1. **来信不是网址**: 收到容器名不等于能查到状态, 必须实际去 host 查, 不把信里任何字段当现成 URL.
2. **查网址**: 经既有 ssh/herdr 通道到 host, 依次可用 — `uv run python scripts/swt.py status --repo <主仓>` 输出的 web 双 URL 行 / STATE 容器记录的 `web-port` / `podman port <容器名> 8800`; 注意 status 只对 running 容器附双 URL 行, 容器停止时走 STATE/podman port. 局域网用址取已确认值 (status 局域网行 / `<records_root>/lan-address`), 不用现算猜测.
3. **回话**: 经既有 ssh/herdr 回话通道回到 body 里 session 指明的原会话, 告知双 URL.
4. **代开**: 页面就绪后在本设备 `xdg-open <URL>` 一次; 开不了就把可点击链接交给我, 不说成已打开.

**已知 URL 时直接投 `open_url`**: body 就是 URL 本身, 取信会话收到直接在本设备打开, 省掉查询回话一轮. 与 request 的区别: request = "帮我查并办" (网址未知), open_url = "网址在这, 直接开" (网址已知, 如回话已拿到). `to` 同样显式填当前设备. 示例 (发送代码同上, 只换 envelope):

```python
envelope = {"id": uuid.uuid4().hex, "ts": time.time(),
            "from": os.environ["SWT_CONTAINER_NAME"], "to": "<当前设备名>",
            "type": "open_url", "body": "http://<已确认地址>:<web-port>/<页面路径>"}
```

**降级路径**: 信箱未运行时没有自动沟通与代开, 我仍可点 host 交付包里的 web 双 URL (本机 + 局域网) 访问已就绪页面; 交付与汇报只写 "可点击链接", 不写成已自动打开. birth 只交付入口, 不因容器出生自动打开页面.

**本节不新增的东西**: 无 URL 查询端点, 无给容器挂载的 URL 文件, 无回程队列 (回话走既有 ssh/herdr); 双设备同时取信 + 换电脑的真机验证归 M09.

## 分发与生效

仓库里的改动到达使用现场有两条路, 别混淆:

- **swt.py 与本 SKILL.md** (host 侧): 仓库根 `uv run python sync-to-pi.py` 同步到 host 的 skills 目录即生效 — 脚本由 host 侧 agent 直接跑, 本文档由 host 侧 agent 直接读, 无其他环节.
- **present skill** (容器内): 它是 base 镜像构建期 COPY 进镜像的, 只改仓库文件容器拿不到. 流程: sync-to-pi 同步到 host skills 目录 → 重建 base (`image-prep build-base`, 按镜像管理节级联 display/项目层) → 之后 birth 的新容器才拿到新版规则. 现有容器不受影响也不补 (不追溯); 真机验证归 M09.

**M08 落地物分流提醒**: swt.py / swt-mailbox-relay.ts / headed 脚本母本 / 本 SKILL.md 经 sync-to-pi 到位 (relay 同步到 pi 扩展目录, 设备侧重启取信会话生效). **base 与 display 层本次都改了** (base: sshd SetEnv 合并 `XDG_RUNTIME_DIR=/tmp/xdg-1001` + `StreamLocalBindUnlink yes` + entrypoint 建目录; display: 加 waypipe/libpulse0 两个 apt 条目) — 须 `image-prep build-base` → `build-display` 按 D017 级联重建 (base 更新后旧 display 自然淘汰, display 更新后旧项目镜像自然淘汰), 之后 birth 的新容器才拿到, 既有容器不追溯. 窗口直飞全链 (真窗口拉起/跨机音频/限频表现) 真机验收归 M09.

## 网络控制 / 容器命令 / 救场

手救场 (防火墙/daemon/config), 换/加容器 provider, 或需要容器操作原生命令时 → reference/ops.md; 脚本原生报错看不懂时 → reference/errors.md (译解表).

## 决策协议 (DECIDE + 收据)

swt 生命周期五子命令 (birth/resume/status/terminate/switch) 非交互, 一切拍板点:
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
