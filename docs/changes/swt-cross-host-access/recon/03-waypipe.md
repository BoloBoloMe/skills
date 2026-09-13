# 方向侦查 03: waypipe 远程直通固化的剩余事实缺口

日期: 2026-09-14
性质: 纯调研 (文献 + 源码级), 不含实施, 不含决策
前序: [跨机GUI无感访问可行性调研报告](../../use-sandbox-worktree/跨机GUI无感访问可行性调研报告.md) (实测底座), 同目录其他方向侦查并行

## 资料来源与版本对应

waypipe 官方仓库 gitlab.freedesktop.org/mstoeckl/waypipe 被反爬 (Anubis) 挡住, 本报告经 GitHub 镜像 (bcornec/waypipe, rogkne/waypipe 带 tag) + man.archlinux.org + 上游源码交叉取得:

| 版本 | 性质 | 与本任务的关系 | 来源 |
|---|---|---|---|
| 0.8.2 | C 版 | Debian 12 (bookworm) 仓库版本 = swt 容器 apt 装到的版本 | v0.8.2 tag 源码 + man; manpages.debian.org/bookworm/waypipe 确认 recon 存在 |
| 0.9.2 | C 版 | 部分发行版 (trixie/Arch 早期/Fedora) 版本 | v0.9.2 tag man |
| 0.10+/0.11.2 | Rust 重写 | 新发行版将迁到的版本; 行为有删改 | Arch man (0.11.2) + master README |

容器内实际 Debian 修订号 (0.8.2-1 之类) 留实施时 `apt policy waypipe` 一步确认.

---

## 0. 结论先行

1. waypipe **没有** "容器内起 server 监听等设备侧来连" 的反向模式: 所有传输方式下 server (应用侧) 都是拨出方, client (合成器侧) 都是监听方. "容器等待设备" 只能靠设备侧预先挂一条常驻 ssh 反向隧道来等价实现.
2. `waypipe ssh` 模式下, 容器内的会话痕迹 (socket 名, 环境变量组合) 是确定性的, 足够容器内 LLM 做 "远程会话在场" 判定; 但该痕迹只对 waypipe 自己拉起的子进程自动可见, 容器内 LLM 自行启动的窗口不会受益 — 这就是题目所说的核心不对称, 三条触发链路围绕它展开.
3. ssh 断线后 `waypipe ssh` 形态是全清场 (两端 waypipe + 应用全退); 重连 (recon) 能力只存在于 C 版 (0.8.x/0.9.x, `--control` 管道), Rust 版 (0.10+) 已删. C 版重连示例的隧道方向是应用侧拨出, 与 swt 白名单立场冲突.
4. Debian 12 的 waypipe 0.8.2 默认压缩是 **none** 不是 lz4; 局域网可接受, 但固化命令若要写 `-c lz4` 应写在设备侧 (wrapper 会透传给远端).
5. 音频 `ssh -R` 反带 pulse unix socket: 文献层面可行且坑位明确 (sshd `StreamLocalBindUnlink` 缺省 no 会留死 socket 挡重建; `StreamLocalBindMask` 缺省 0177 落成 0600 仅属主), 且源码证实 `waypipe ssh` 会逐字透传用户自带的 `-R` 参数, 可与音频转发同条 ssh. 全部属未实测, 必测点已列.
6. 启动脚本模板归 birth 生成比镜像内置更有事实支撑: chromium 路径随镜像重建漂移且可能多版本并存 (glob 有歧义), 脚本微调不应触发 D017 级联重建; swt 已有两个现成交付先例 (AGENTS.md 只读挂载 / auth.json exec 写入).
7. 运行期三态判定只能依赖容器内文件/socket/进程事实, 不能依赖环境变量被改写 — env 烘配只发生在 podman create 时, resume 无法变更.

---

## 1. 远程会话判定与触发链路 (核心)

### 1.1 server/client 角色与 ssh 方向的绑定 (事实)

- `waypipe client` = 合成器侧: bind 一个 unix socket 监听 (缺省 `/tmp/waypipe-client.sock`, 非单连接时 backlog 128), 并连本地合成器. `waypipe server` = 应用侧: 造一个假合成器 socket 给应用连, 自己**主动 connect** 到 client 的 socket. man 原文: server "try to connect to its matching waypipe client socket".
- 方向绑定在所有传输下一致: ssh 模式 (wrapper 自动 `ssh -R` 把 client socket 反向带进应用侧, server 连它), ncat/socat 手工接力 (仍是 server 拨出), vsock (man 明言 "CID is only used in the server mode", 还是 server 连 client). **不存在 client 拨向 server 的模式**, 即不存在原生反向.
- vsock 模式仅面向虚拟机 (VMADDR), podman rootless pasta 容器无 vsock 设备, 不适用.

### 1.2 `waypipe ssh` 模式的内部构造 (0.8.2 源码, 判定依据的根据)

`waypipe [opts] ssh <ssh args> <dest> <cmd>` 在本机生成 8 位随机 token, 然后:

- 本机 (设备 B) 起 client, socket = `<prefix>-client-<token>.sock` (prefix 缺省 `/tmp/waypipe`);
- 构造 ssh 命令: `ssh -R <prefix>-server-<token>.sock:<prefix>-client-<token>.sock <用户的全部 ssh 参数...> waypipe server ... <cmd>`;
- 远端 (容器) sshd 经登录 shell 拉起 waypipe server, server 连进 `-R` 造出的 socket; 应用假合成器名 = `wayland-<token>` (随机);
- 用户的 ssh 参数 (`-p`, 用户自带的 `-R` 等) 被逐字复制进 arglist, 与 waypipe 自己的 `-R` 并存 (源码 arglist 构造段). 这是音频同条 ssh 转发的直接依据.

推论:
- **每次 `waypipe ssh` 的 socket 名都不同 (随机 token)**: 设备 B 同时对多个容器开多条会话互不冲突, 多容器并存隔离在源码层坐实 (0.11 man 的 "randomized suffix" 同义).
- 容器内会话痕迹: `/tmp/waypipe-server-<token>.sock` 存在期间 = 远程会话在场 (ssh 掉线即消失); `pgrep -x waypipe` 同理. 二者都是容器内可探测的文件/进程事实.

### 1.3 三条触发链路

**关键不对称重述**: 设备侧发起的窗口, 环境由 waypipe server 自动喂好 (`WAYLAND_DISPLAY=wayland-<rand>` 只设给它的子进程, man ENVIRONMENT 节), 天然落地 B; 容器内 LLM 在普通 ssh 会话里自己启动的 headed 进程没有这些变量, 沿现有两态判定落 noVNC. 差距全在 "谁拉起应用".

| 链路 | 发起方 | 通道构成 | 新增暴露 | 容器内判定依据 | 评注 |
|---|---|---|---|---|---|
| (a) 设备侧手工直发起 (现状交付形态) | B 的人 | `waypipe ssh ... <启动脚本>`, 纯入向 | 零 (复用 sshd 端口) | 会话 socket 存在 / pgrep waypipe (只能 "看见", 不能利用) | LLM 自启窗口不受益; 两套窗口可能各落各屏, 体验割裂 |
| (b) 容器内发起, 经传话通道 | 容器内 LLM 写请求 | 并行侦查方向: 容器内队列 + 设备侧常驻 pi 会话, 由它执行 `waypipe ssh` | 零 (动作仍在 B 侧) | 同 (a) | waypipe 侧唯一要求 = "设备侧某个时刻能执行一条 shell 命令", 对传话机制无额外约束; 窗口延迟含传话往返 |
| (c1) waypipe 原生反向 | - | 不存在 | - | - | 排除 |
| (c2) 应用侧拨出常驻隧道 (C 版 man 重连示例形态) | 容器侧 | 容器 `ssh -fN -L ...` 拨出连 B + 常驻 `waypipe server --control` | **容器出向流量, 白名单须放行 B 的 IP**, B IP 漂移即失效 | 隧道 socket 存在 | 与 swt whitelist 立场直接冲突; 唯一优势是原生断线重连 |
| (c3) 设备侧入向常驻隧道 + 容器内按需起 server | B 预挂隧道, LLM 按需用 | B: `waypipe -s /tmp/swt/wp-b.sock client &` + `ssh -fN -R /tmp/swt/wp-c.sock:/tmp/swt/wp-b.sock -p <port> bolo@<A>` (可再挂一条 `-R` 带音频); 容器: `waypipe -s /tmp/swt/wp-c.sock server -- <脚本>` | 零 (纯入向) | `test -S /tmp/swt/wp-c.sock` | 唯一 "LLM 能直接发起且零白名单改动" 的形态; 代价是 B 侧多一条常驻命令, 隧道死后 socket 残留 (见 3.2) |

(c3) 细节事实:
- 容器侧 server 按需起, 只拨出不监听, 无清理负担; 应用关 = server 退, **隧道存活**, 下个应用即起即用.
- (c3) 下应用死 = server 死 = 窗口消失, 无重连 (重连需常驻 server + `--control`, 那是 (c2) 的形态); 对 "登录墙/网页浏览" 场景足够, 断线后重跑命令即可.
- `/tmp/swt/` 目录属 entrypoint 保障项, 与固化清单第 1 条 (`/tmp/xdg-1000` 保证) 同一处实现.
- 隧道断了再挂: `StreamLocalBindUnlink` 缺省 no 会让旧 socket 挡新转发 (见 3.2), 解法三选一: base sshd_config 加 `StreamLocalBindUnlink yes` (又一处 base 层改动, 触发 D017 级联), entrypoint 起动时清残留, 或 B 侧 autossh/ServerAlive 保活少断.

### 1.4 判定依据事实清单 (供考察点 5 使用)

容器内进程视角, 三态可用环境变量组合直接区分, 无歧义:

| 态 | WAYLAND_DISPLAY | XDG_RUNTIME_DIR | 来源 |
|---|---|---|---|
| 宿主直通 (D051) | `wayland-0` (烘死) | `/run/swt-wayland` (烘死) | ops.md D051 命令字面 |
| 远程 waypipe 会话 (子进程) | `wayland-<8位随机>` | 继承 ssh 登录环境 = `/tmp/xdg-1000` (base SetEnv) | 源码 display_path 构造 + 坑 2 解法 |
| 都不在场 | 未设 | `/tmp/xdg-1000` | - |

跨进程判定 (LLM 的 shell 里): 会话 socket (`/tmp/waypipe-server-*.sock`) 或隧道 socket (`/tmp/swt/wp-c.sock`) 存在性, `pgrep waypipe`. 均为文件/进程事实, 不依赖被烘死的 env.

host 侧 (swt/STATE) 视角: 远程会话是入向 ssh, swt 生命周期完全不经手, **STATE 无法自动感知**; 可行路径是 resume/display-check 时 `podman exec` 探测上述容器内事实, 把点时快照写进 STATE (见 5.3).

---

## 2. waypipe 能力边界

### 2.1 多窗口并发

- 缺省非 oneshot: client 与 server 的通道 socket backlog 均为 128 (源码 `oneshot ? 1 : 128`); 一个 server 多路复用一个假合成器 socket, 多应用多窗口并发无数量级障碍. `--oneshot` (单连接, 关即退) 反而是要刻意避开的选项.

### 2.2 剪贴板

- man SECURITY 节将 copy-paste 数据与窗口表面内容并列为 fd 传输内容; 实测报告确认双向剪贴板. 无新缺口.

### 2.3 ssh 断线后行为

- `waypipe ssh` 形态: man 重连节明言 wrapper "will automatically close both the waypipe client and the waypipe server when the connection fails" — 全清场, 应用随之退出; 实测 (窗口关闭/会话退出, 容器无转储) 一致. 登录态 profile 落 /tmp 不受影响.
- 重连能力**版本绑定**: C 版 (0.8.x/0.9.x) 有 `waypipe recon <控制管道> <新socket>` + `--control`; master README 明言 Rust 版 "includes some features (like reconnection support) dropped in later versions", 0.11.2 man 无此二者. 即: **若未来 base 换到带 Rust 版 waypipe 的发行版, 重连形态直接消失**, 这是版本升级的一个隐蔽约束.
- C 版重连的标准形态 (man 示例): 两端分离起 client/server, server 带 `--control` 管道常驻 (`-- sleep inf`), 传输断了在新转发 socket 上 `waypipe recon` 重接. 注意示例的转发是应用侧拨出 `ssh -fN -L` — 容器出向, 即 1.3 (c2).

### 2.4 多容器并存隔离

- 各 waypipe 对独立无共享; ssh 模式随机 socket 名保证同 B 多会话无冲突 (2.3/1.2). 实测报告 "天然隔离" 结论在源码层成立.

### 2.5 容器内 socket 权限面

会话期容器内共三类 socket:
1. 假合成器 socket `$XDG_RUNTIME_DIR/wayland-<rand>`: 位于 `/tmp/xdg-1000` (0700 bolo), 仅 bolo 可达.
2. `ssh -R` 转发 socket `/tmp/waypipe-server-<rand>.sock`: sshd 建, 权限 = 0666 & StreamLocalBindMask(缺省 0177) = 0600, 属主 = 会话用户 bolo (sshd_config(5) 原文: "readable and writable only by the owner"). 仅 bolo 可连.
3. (c3) 隧道 socket: 同上 0600 bolo.
即容器内 socket 权限面收敛于工作用户本身, 与 swt 单用户 (bolo) 模型吻合, 无新增暴露主体. 另 man SECURITY 提醒两点供风险声明复用: waypipe 不过滤合成器放出的协议 (B 桌面若给所有 client 截屏/锁屏协议, 被代理的容器应用同样拿得到); 流量时序/包长可侧信道窥探行为 (内容有 ssh 加密).

### 2.6 视频/dmabuf

README Technical Limitations 与实测结论互证:
- 共享内存 buffer 用镜像副本做**增量区域传输**, 静态 UI 高效, 动画类应用有延迟尖峰; ssh `ObscureKeystrokeTiming` 可能额外引入输入延迟.
- dmabuf (GPU 零拷贝) 需两端格式/驱动兼容, 跨机异构 GPU 下不成立, 走压缩路径 — **确认实测报告 "恒走压缩" 的说法**.
- 视频编码 (--video h264/vp9/av1) 是按 buffer 的独立视频流, 窗口在少数几个 buffer 间轮转时会闪 (各流压缩瑕疵不同); 硬件编解码 "somewhat experimental". 结论: 视频场景本就是体验下限, 固化时不必指望 --video 救.
- `--no-gpu` 强制软件渲染 + shm buffer, 是排查 GPU 相关故障的官方推荐开关, 可写进救场条目.

### 2.7 版本矩阵 (选型约束)

| 项 | 0.8.2 (容器现状) | 0.9.2 | 0.10+/0.11 (Rust) |
|---|---|---|---|
| 默认压缩 | **none** (man 脚注: 未来才改 lz4; 源码注释同) | lz4 | lz4 |
| recon/--control 重连 | 有 | 有 | **无** |
| --secctx / --vsock | 无 | 有 | 有 |
| --ssh-bin / --remote-socket / --xwls | 无 | 无 | 有 |
| ssh 模式 socket 名 | prefix-client/server-<rand>.sock | 同 | prefix + 随机后缀 (同义) |

设备 B (Bazzite) 侧版本由用户自管 (distrobox 安装), 不受 swt 控制; 两端跨版本 (0.8.2 对 0.9.x/0.10.x) 的线协议兼容性官方未给承诺, 列入必测. 若做 (c3) 隧道形态, 两端命令字面还依赖各自版本支持的手工模式参数, 差异不大但需按 B 实际版本核对.

---

## 3. 音频 ssh -R 形态预研 (文献层面, 全部未实测)

### 3.1 形态

```bash
# B 侧, 与画面同条 ssh (waypipe 透传用户 -R, 源码证实):
waypipe ssh -R /tmp/swt/pulse-b.sock:/run/user/1000/pulse/native \
  -p <宿主端口> bolo@<host-LAN-IP> /home/bolo/.local/bin/swt-headed-browser.sh
# 容器内启动脚本:
PULSE_SERVER=unix:/tmp/swt/pulse-b.sock exec <chromium ...>
```
方向: 容器内应用连 `/tmp/swt/pulse-b.sock` (sshd 建) → ssh 隧道 → B 侧 ssh 客户端连 `/run/user/1000/pulse/native` (B 的 PipeWire pulse 兼容 socket). 容器全程无出向流量, 替代实测过的 TCP 直连形态, 零白名单改动.

### 3.2 sshd 侧三个事实 (sshd_config(5), Arch 版核对)

- **StreamLocalBindMask 缺省 0177**: 转发 socket 落成 0600 仅属主 (= 会话用户 bolo) 可读写. 容器内 pulse 客户端以 bolo 运行, 权限吻合. 精确值可在容器 `sshd -T` 一步核对.
- **StreamLocalBindUnlink 缺省 no**: 原文 "If the socket file already exists and StreamLocalBindUnlink is not enabled, sshd will be unable to forward the port to the Unix-domain socket file". 即 ssh 不干净断开后残留死 socket, 同路径重连直接失败. 对策: base sshd_config 加 `StreamLocalBindUnlink yes` (与 SetEnv 是不同 directive, 无坑 3 的单行问题; 但属 base 层改动, D017 级联成本要摆上桌), 或 entrypoint/resume 清 `/tmp/swt/` 残留.
- PermitListen 只管 TCP 转发, unix socket 反向转发无对应白名单 directive, sshd 缺省放行, 无需改.
- unix socket 路径 108 字节上限: `/tmp/swt/...` 足够短.

### 3.3 容器内 pulse 客户端侧

- `PULSE_SERVER=unix:<path>` 是 libpulse 标准写法; libpulse0 已在固化清单 (坑 8 dlopen 问题随之解决).
- 认证: B 侧连 pulse socket 的进程是 B 上的 ssh 客户端 (uid bolo), pulse/PipeWire 对同 uid unix socket 连接缺省放行, 无需 cookie/TCP 匿名模块 — 比 TCP 形态 (auth-anonymous=1, 同网段任何人都可用 B 声卡) 的安全面显著更小.
- 脚本健壮性: 隧道不在场时该 socket 不存在, chromium 起得来但无声 (libpulse 连不上不致命). 是否需要脚本内探测并告警, 留设计.

### 3.4 必测点 (实施阶段)

1. 端到端: 上述形态下 chromium 真出声 (unix 形态; TCP 形态已实测).
2. B 侧 PipeWire 对同 uid unix 连接的认证行为 (预期放行).
3. sshd 转发 socket 容器内实测权限/属主 (预期 0600 bolo; rootless uid_map 映射后的呈现).
4. `StreamLocalBindUnlink` 缺省行为实测 (制造断线, 验证残留 socket 挡重建) + 加 directive 后生效.
5. `waypipe ssh` 与用户 `-R` 并存的端到端 (源码层透传已证实, 组合未跑过).
6. 0.8.2 (容器) 与 B 实际版本的跨版本兼容.
7. LAN 下 pulse native 过 ssh 隧道的延迟/抗抖动主观评价.

---

## 4. 启动脚本模板归属

事实约束:
- **chromium 路径不稳定**: playwright 目录 `~/.cache/ms-playwright/chromium-<rev>/chrome-linux[64]/chrome`, rev 随 display 镜像构建变; 镜像升级后旧 rev 目录并存时, `chromium-*` glob 取哪个有歧义. birth 时 exec 解析出**精确字面路径**烘进脚本, 比镜像内置脚本运行时 glob 更稳.
- **参数化需求分两类**: 音频走 `ssh -R` 隧道形态则 socket 路径是常量 (镜像内置不失格); 一旦回头用 TCP 形态, B 的 IP 是每实例参数, 只能 birth 时注入. 通用浏览器参数 (no-sandbox/ozone 等) 与镜像版本演进绑定.
- **演进成本不对称**: 脚本内容属于 "经验性调参" (flag 增删, 音频切换), 高频; 镜像重建是 D017 级联 (base/display/全部项目镜像), 低频重操作. 脚本进镜像 = 每次调参都触发级联.
- **swt 已有两个交付先例** (同一机制的两种写法): agent-prompts 母本制 = 仓库模板 → birth 拷贝留档 → 只读单文件挂载进容器, 可追溯每容器用的哪版; auth.json = birth 后 exec 写入. 脚本模板完全可套母本制: 模板放 skill 仓库, birth 生成实例脚本落 `<records-root>/runtime/<identity>/`, 挂载或 exec 写入容器内固定路径 (如 `/home/bolo/.local/bin/swt-headed-browser.sh`), B 侧命令引用该路径.
- 脚本路径的稳定性只要求 "容器存续期内不变": B 拿到的命令在 birth/resume 交付包里, rm 重建容器后脚本随新 birth 重生成, 口径自洽.

两案对比 (陈述事实, 不替设计拍板):

| 维度 | 镜像内置 (display 层) | birth 生成 (模板在 skill 仓库) |
|---|---|---|
| chromium 精确路径 | 需运行时 glob, 多 rev 有歧义 | birth 时 exec 解析, 字面烘入 |
| 每实例参数 (B IP/音频形态) | 进不去, 只能环境变量接力 | 直接生成时注入 |
| 脚本调参 | 触发 D017 级联重建 | 改模板, 下个 birth 生效, 零重建 |
| 版本追溯 | 随镜像 contents.md | 母本制留档, 每容器可查 |
| 旧容器 resume | 脚本随镜像原地存在 | 依赖挂载/文件随容器存续 (birth 产物, resume 不动) |

---

## 5. 三态选路语义草案 (选项陈述, 非定稿)

### 5.1 谁在何时判定

三层各管一段, 现有机制已覆盖前两层的一半:
1. **birth/resume (host)**: 判定 D051 有无 (现状, 烘 env + STATE `host-display`); 对远程态只能探测, 不能预知 (入向会话).
2. **容器内 LLM (每次 headed 启动时)**: 按事实序判定, 是三态化唯一必须新增的判定点.
3. **B 的人 (每工作会话一次)**: 选通道形态 — (a) 逐应用命令, 或 (c3) 挂一条常驻隧道. 这层在交付包里以命令模板表达.

### 5.2 容器内判定顺序草案

```text
1. WAYLAND_DISPLAY 已设 且 socket 可连 → 直接用
   (XDG_RUNTIME_DIR 值可区分 D051 / waypipe 会话, 见 1.4 表)
2. 未设 且 远程通道标志在场 (c3: test -S /tmp/swt/wp-c.sock; a: /tmp/waypipe-server-*.sock 存在)
   → 用 waypipe server 包装启动 (c3) 或提示用户走 B 侧命令 (a); 启动失败 → 落 3
3. DISPLAY=:99 → noVNC 兜底
```
要点: 环境变量继承 (`BROWSER_HEADED=true` 约定) 不动; 新增的只有第 2 步的探测与包装. **判定依据必须落在文件/socket/进程, 不能是 env** — env.conf 烘配只在 podman create 时发生, resume 改不了运行中容器的环境 (SKILL 环境变量继承节明言改清单须重建).

### 5.3 STATE 落形态选项

STATE 单行 json 只加字段不改名. 三个选项:
- **A 不动 STATE**: 容器内文件事实是唯一事实源, host 需要时 exec 探测; 交付包按 birth 参数生成远程直通项. 最小改动.
- **B 加探测快照字段**: resume/display-check 时 exec 探测 (会话 socket/隧道 socket), 写 `remote-display: seen-tunnel|seen-session|absent`, 语义 = 点时快照非持续状态, 文档须写明.
- **C 出生声明**: birth 加 flag 声明 "本容器预期远程使用", 只影响交付包内容, 不参与运行期判定. 与 A/B 可叠加.
注意 B/C 都解决不了 "会话中途建立/断开" 的实时性 — 实时判定只在容器内 (5.2) 成立, 这是由触发链路的方向性决定的, 不是实现缺陷.

---

## 6. 遗留疑问 / 必测清单汇总

1. 3.4 节音频 7 项 (unix 形态端到端, PipeWire 认证, socket 权限, Unlink 行为, -R 并存, 跨版本兼容, 延迟体验).
2. (c3) 隧道形态端到端未实测: 常驻 -R 隧道 + 容器内按需 server, 含隧道断后 socket 残留的实际表现.
3. B 侧实际 waypipe 版本与 0.8.2 的兼容 (决定 B 侧命令字面与 (c3) 可行性).
4. 容器内 Debian 修订号确认 (`apt policy waypipe`, 一分钟).
5. 设计阶段待盘问: 触发链路选 (a)+(b) 还是加 (c3); 音频形态终选; STATE 选项 A/B/C; 脚本挂载 vs exec 写入; `StreamLocalBindUnlink yes` 是否接受 base 层级联成本.
6. 本方向未覆盖: 容器内队列 + 设备侧常驻 pi 会话的传话机制细节 (并行侦查文档); web 服务场景形态 (用户明确挂起).
