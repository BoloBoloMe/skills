# 跨机 GUI 无感访问可行性调研报告

日期: 2026-09-13
性质: 可行性调研 (实测验证), 不含实施; 固化实施另行开展
关联文档: [容器GUI无感访问技术报告](./容器GUI无感访问技术报告.md) (同机直通篇)

## 环境

| 角色 | 机器 | 系统 | 桌面 | 局域网 IP |
|---|---|---|---|---|
| 主机 A (容器宿主) | bolo-Yoga | Ubuntu 26.04 | 无 (纯 tty, 无桌面会话) | 192.168.31.252 |
| 设备 B (人面前) | (Bazzite 机) | Fedora Atomic, Bazzite | KDE Plasma, Wayland, NVIDIA | 192.168.31.11 |

实验容器: `waypipe-lab`, 由 `localhost/sandbox-worktree/skills:2026.09.12-1` (Debian 12 项目层镜像, 自带 sshd + playwright chromium) 手工起, 未走 swt 生命周期, 试毕已 `podman rm -f`.

---

## 1. 调研问题

swt 容器内工作时, GUI 需求两类: 容器起 web 服务; 容器开真浏览器窗口 (登录墙等). 现有两条显示通道都有缺口:

- noVNC: 整个 Xvfb 虚拟桌面塞进浏览器网页, 能用但隔两层.
- 本机直通 (D051): wayland socket 挂进容器, 窗口只落在**宿主自己**的桌面; 人经 ssh 在另一台设备 B 前干活时用不上.

问题: 容器内的 GUI 窗口能否**逐窗口**出现在局域网内另一台设备 B 的桌面上, 体验等同本地应用?

## 2. 原理与选型

Linux 图形栈 C/S: 应用往 wayland unix socket 发结构化消息, 谁持有 socket 另一端 (合成器), 窗口就出现在谁的屏幕上. 同机直通是把宿主的 socket 递进容器; 跨机的唯一增量是把消息流**接力过网络**.

- Wayland 协议刻意只支持本机 socket (依赖 SCM_RIGHTS 传 fd), 不能裸过 TCP, 也不能用 socat 中继 (F019 同源原因).
- **waypipe**: 在应用侧造一个本地 wayland socket 收消息, 序列化/压缩后经 ssh 送到对端, 对端再喂给本地合成器. 逐窗口, 双向剪贴板, 不管声音.
- 备选: ssh -X (X11 原生支持网络, 但协议啰嗦) 与 xpra (h264 编码, 视频场景强). 本轮选 waypipe, 与 swt 的 wayland-only 安全立场一致 (不碰 D051 的 X11 禁令).

链路: `容器 chromium → waypipe server (容器内) → ssh (复用容器 sshd 入口) → waypipe client (B) → B 合成器 → B 桌面`. 宿主 A 的显示栈完全不参与.

## 3. 实测过程

### 3.1 容器准备 (宿主 A 上执行)

```bash
podman run -d --name waypipe-lab --shm-size=1g -p 0.0.0.0::22 \
  localhost/sandbox-worktree/skills:2026.09.12-1     # entrypoint 自动起 sshd
podman port waypipe-lab 22                            # 得 0.0.0.0:44429
podman exec -u root waypipe-lab apt-get install -y waypipe libpulse0
podman exec -u root waypipe-lab sh -c 'echo bolo:sandbox | chpasswd'
```

要点: `--shm-size=1g` (报告篇坑 3 的同源预防); ssh 密码 `sandbox` 沿用 swt 惯例; 端口随机发布在宿主所有网卡, B 经 LAN 直连.

### 3.2 B 端准备

B 是 Fedora Atomic, `dnf` 被禁. 正解: 进 distrobox (`distrobox enter`), 盒内 `sudo dnf install waypipe`. distrobox 自动接通 B 的 wayland, waypipe client 在盒内跑, 窗口照样落 B 桌面. (备选: brew; 兜底: rpm-ostree 需重启, 不值.)

### 3.3 拉起命令 (B 上执行)

```bash
waypipe ssh -p 44429 bolo@192.168.31.252 /home/bolo/lab-chrome.sh
```

其中 `lab-chrome.sh` 是容器内启动脚本 (必要性见坑 5):

```sh
#!/bin/sh
export PULSE_SERVER=tcp:192.168.31.11:4713   # 音频通道, 见第 5 节
exec /home/bolo/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome \
  --no-sandbox --disable-crashpad --ozone-platform=wayland
```

### 3.4 实测结果

- 画面: chromium 窗口出现在 B 的 KDE 桌面, 与本地窗口混排, 拖动/缩放/焦点行为原生.
- 交互: 可正常点按, 浏览网页.
- 声音: 开有声页面验证通过 (pulse over TCP, 见第 5 节).
- 窗口关闭后 ssh 会话随之退出, 容器侧无崩溃转储, 生命周期干净.

**结论: 方案可行, 体验达到 "仿佛在本地应用".**

## 4. 踩坑记录 (全部为固化原料)

**坑 1: Debian 官方源在宿主网络下近乎不可用.**
`deb.debian.org` 下载速度归零级, IPv4/IPv6 皆然; 清华源 bookworm-security 返 403; 换 USTC 源 (`mirrors.ustc.edu.cn`, 含 debian-security 路径) 后秒装. 注意实验容器是绕开 swt 防火墙手工起的才有这问题; 正式镜像构建在构建期装包, 不受影响 — 但若构建也变慢, 同样换源.

**坑 2: 容器 ssh 会话没有 XDG_RUNTIME_DIR, waypipe 直接瘫痪 (最核心).**
现象: 命令 4 秒无声退出, B 上什么都看不到, 仅一行 `Env. var XDG_RUNTIME_DIR not available, cannot place display socket`.
排查: 容器内 `waypipe server env` 对照实验证实 — 无此变量时 waypipe server 放不出 socket, **子进程根本拿不到 WAYLAND_DISPLAY**, chromium 无显示可连即退; 设上后子进程正常获得 `WAYLAND_DISPLAY=wayland-xxx`.
根因: 容器内无 systemd 登录会话, 没人设 XDG_RUNTIME_DIR.
解法: sshd_config 的 SetEnv 烘入 `XDG_RUNTIME_DIR=/tmp/xdg-1000`, 并保证该目录存在且属 bolo, 0700.

**坑 3: sshd 的 SetEnv 只认第一行.**
在已有 `SetEnv PATH=...` 后追加 `SetEnv XDG_RUNTIME_DIR=...` 不生效 (`sshd -T` 只见第一行). 必须**合并成单行**: `SetEnv XDG_RUNTIME_DIR=/tmp/xdg-1000 PATH=...`.

**坑 4: 对 pid 1 的 sshd 发 HUP 不重读配置.**
容器内 sshd 即 pid 1, `kill -HUP 1` 后新配置不生效 (对照实验: 加标记 SetEnv, HUP, ssh 登录验证拿不到). 只能 `podman restart` (端口映射不变, /tmp 不丢).

**坑 5: waypipe 启动远程程序不经过 shell.**
远程命令写 `PULSE_SERVER=... chrome ...` 会报 `Spawn failure for 'PULSE_SERVER=...': No such file or directory` — 赋值前缀被当成程序名. 环境变量必须包进容器内启动脚本, 远程命令只写脚本路径. 附带好处: B 侧命令无引号, 免疫终端折行 (本次一次失败即因带引号长命令粘贴时被折行拆散).

**坑 6: B 端 Atomic 装不了 dnf 包.** 见 3.2, distrobox 是正解.

**坑 7: 密码张冠李戴.** 容器 sshd 的账号体系独立于宿主, 输宿主密码必然 permission denied.

**坑 8: chromium 的 pulse 支持是 dlopen 运行时装载.**
`ldd` 看不见 libpulse; 容器内须显式 `apt install libpulse0`, 否则静音.

## 5. 音频通道

waypipe 只搬画面与剪贴板, 声音另走 pulse 协议. 本轮实测形态: B 侧 `pactl load-module module-native-protocol-tcp listen=0.0.0.0 auth-anonymous=1` 开 TCP 4713, 容器侧 `PULSE_SERVER=tcp:<B-IP>:4713` 指过去, 局域网未压缩 PCM 带宽可忽略, 音画同步无感. 安全注意: 开着期间同网段任何主体可用 B 的声卡, 测完 `pactl unload-module module-native-protocol-tcp`.

**固化时应改形态**: TCP 直连是容器**主动外连** B, swt 白名单模式下须为 B 的 IP 加放行, 不雅且 B IP 会漂移. 更干净: `ssh -R /tmp/pulse-remote.sock:/run/user/1000/pulse/native` 把 B 的 pulse socket 反向带进容器, 音视频同走既有 ssh 通道, 零新增暴露, 不占白名单. 此形态本轮未实测, 实施阶段验证.

## 6. 与 swt 安全模型的兼容性

- 纯 wayland 协议, 客户端间天然隔离, 不触碰 D051 "禁挂 X11 socket" 的禁令 (X11 跨客户端嗅探问题不存在).
- waypipe 的 ssh 连接由 B 发起, 对容器是**入向**, 不占 whitelist 出站条目; pasta 下复用既有 sshd 端口发布, 无新网络面.
- 音频若沿用 TCP 直连则是出向, 见上节改进.
- 登录凭证沿用 swt 既有双轨 (密码 `sandbox` / 密钥), 无新增风险项.

## 7. 固化改动清单 (已获用户批准, 实施另起会话)

1. **base 层**: sshd_config 的 SetEnv 单行追加 `XDG_RUNTIME_DIR=/tmp/xdg-1000`; 容器启动路径保证 `/tmp/xdg-1000` 存在 (bolo:bolo, 0700) — 放 entrypoint 或 swt-vnc 同类 helper.
2. **display 层**: 清单加 `waypipe` 与 `libpulse0` 两个 apt 包.
3. **SKILL.md 显示栈节**: headed 选路两态改三态 — 宿主 wayland 在场 → 直通 (现状); 远程会话 → waypipe 远程直通; 都没有 → `DISPLAY=:99` noVNC 兜底. 补坑 2/3/5 的机制说明.
4. **birth/resume 交付包**: 新增 "远程直通命令" 项, 与 noVNC URL 并列; 形态为 `waypipe ssh -p <宿主端口> bolo@<host-LAN-IP> <容器内启动脚本>`, 启动脚本模板随镜像提供 (内含 headed 浏览器全套参数与 PULSE_SERVER).
5. **级联提醒**: base 层变更按 D017 匹配谓词使 display 层与全部项目镜像失效, 须依序重建.
6. **B 端前提写入文档**: B 须 Linux + Wayland 桌面 + waypipe (Atomic 走 distrobox); macOS/Windows 不支持, 继续 noVNC.

## 8. 限制与已知边界

- B 必须是 Linux Wayland 桌面; 其他平台无合成器可接, noVNC 兜底.
- 视频播放是体验下限: 像素压缩过网, 会糊会卡; 登录墙/网页浏览/终端类无感. dmabuf 零拷贝跨机不成立 (两端 GPU/驱动异构), 恒走压缩路径.
- 声音走网络 pulse 有固定小延迟, 局域网内对音乐/提示音无影响.
- 多容器并存时 waypipe 各自独立, 无共享状态, 天然隔离.

## 9. 遗留议题

- **web 服务场景的推荐形态** (端口直达 vs 其他): 用户明确后续单独讨论, 本报告不下结论.
- 音频 ssh -R 形态待实施阶段实测.
- 远程直通与 herdr remote 的交付整合细节 (命令模板中的端口/地址发现自动化) 待实施阶段定稿.

## 10. 实验产物清理记录

- 容器 `waypipe-lab`: 已 `podman rm -f` (账号密码随之消失)
- 宿主临时文件 `/tmp/askpass.sh` (验证 ssh 环境用): 已删
- 镜像 `localhost/sandbox-worktree/skills:2026.09.12-1` 保留 (本就是项目镜像)
- B 端 distrobox 内 waypipe 包与 B 侧 `module-native-protocol-tcp`: 由用户自行处置 (后者重启即消)
