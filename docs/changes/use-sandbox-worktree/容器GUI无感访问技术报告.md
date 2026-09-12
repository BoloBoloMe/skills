# 在宿主机上无感运行容器内 GUI 程序: 技术实现报告

日期: 2026-09-12
环境: Bazzite (Fedora Atomic 44, KDE Plasma 6, Wayland, NVIDIA RTX 3060 Ti), podman 5.8.2
演示对象: Fedora 容器内的 Chromium, 窗口直接出现在宿主 KDE 桌面

---

## 1. 原理: 为什么容器里的程序能 "无感" 显示在宿主桌面

### 1.1 核心事实: 容器不隔离显示

Linux 图形栈是 C/S 架构. 应用 (客户端) 不直接画屏幕, 而是向显示服务端发送结构化消息:

- Wayland: 应用连接 unix socket `/run/user/<uid>/wayland-0`, 发送 "创建窗口", "提交缓冲区" 等请求. 合成器 (KWin) 收到像素缓冲区后负责最终合成上屏.
- X11: 应用连接 X server 的 socket (DISPLAY=:0), 同理.

关键点: 这套通信的载体只是一个 unix socket 文件. 容器的隔离边界是 mount namespace, PID namespace 等, 但只要把 socket 文件 bind-mount 进容器, 容器内进程就能和宿主合成器正常对话. 窗口由宿主的 KWin 绘制, 因此拖动, 缩放, 主题, 多显示器行为与原生窗口完全一致.

容器内程序只承担 "计算要画什么" 的部分, 最终显示权在宿主. 这就是无感体验的根源.

### 1.2 完整体验还需要的其他通道

| 通道 | 宿主资源 | 接法 |
|---|---|---|
| 显示 | `/run/user/1000/wayland-0` | bind-mount socket, 设 `WAYLAND_DISPLAY`, `XDG_RUNTIME_DIR` |
| GPU 加速 | `/dev/dri` (DRM 设备) | `--device /dev/dri`; NVIDIA 需额外注入用户态驱动 (CDI) |
| 声音 | `/run/user/1000/pulse` (PulseAudio/PipeWire socket) | bind-mount 整个目录 |
| 文件 | `$HOME` 或子目录 | bind-mount |
| dbus (可选) | `/run/user/1000/bus` | 会话总线, 影响托盘/文件对话框等集成 |
| 网络 | 宿主网络栈 | `--network=host` 最简单, 也让容器能访问仅监听 127.0.0.1 的宿主服务 |

### 1.3 Flatpak 为什么天然无感

Flatpak 就是 "按桌面应用需求预配置好的沙盒": 上述通道全部自动接线, 外加 portal 标准通道处理文件选择器, 摄像头, 通知等. 底层隔离技术与 podman 同源 (bubblewap/namespaces). 所以 Flatpak 应用的无感是设计使然, 不是巧合.

---

## 2. 实操记录: podman + Fedora 容器跑 Chromium

### 2.1 最终可用的启动命令

```bash
podman run -dit --name chromium-box \
  --userns=keep-id \
  --network=host \
  --security-opt label=disable \
  -e WAYLAND_DISPLAY=wayland-0 \
  -e XDG_RUNTIME_DIR=/run/user/1000 \
  -v /run/user/1000/wayland-0:/run/user/1000/wayland-0 \
  --device /dev/dri \
  -v /run/user/1000/pulse:/run/user/1000/pulse \
  -v /home/bolo:/home/bolo \
  registry.fedoraproject.org/fedora:latest sleep infinity

podman exec -u root chromium-box dnf -y install chromium

podman exec -d chromium-box bash -c \
  'HOME=/home/bolo /usr/lib64/chromium-browser/chromium-browser \
   --no-sandbox --disable-crashpad --disable-dev-shm-usage \
   --ozone-platform=wayland'
```

窗口直接出现在宿主 KDE 桌面, 与原生窗口混排, 无任何额外配置.

### 2.2 各参数的作用

- `--userns=keep-id`: 容器内用户 UID 映射为宿主的 1000, 家目录文件属主一致, 避免权限错乱.
- `--network=host`: 共享宿主网络栈. 一石二鸟: 出网走宿主路由, 且能访问监听 127.0.0.1 的宿主代理 (127.0.0.1:7897). 若不用 host 网络, 容器内的 127.0.0.1 指容器自身, 访问宿主需改用 `host.containers.internal`, 且要求宿主服务监听在非 loopback 地址上.
- `--security-opt label=disable`: 关闭 SELinux 标签隔离. 见 2.3 坑 2.
- `-e WAYLAND_DISPLAY + -v wayland-0`: 显示通道, 最核心的两个接线.
- `--device /dev/dri`: GPU 硬件加速. NVIDIA 专有驱动场景还需 CDI 注入用户态驱动库 (Bazzite 的 `ublue-nvctk-cdi.service` 自动生成 CDI 配置, 可用 `--cdi=nvidia.com/gpu=all`), 本例 Chromium 用软件路径也能工作, 未强制要求.

### 2.3 踩过的三个坑 (按发现顺序)

**坑 1: 容器内无法访问宿主代理**

现象: `dnf install` 连不上任何源, 直连也不通.
原因: 代理只监听宿主 `127.0.0.1:7897`; 容器默认网络命名空间里 127.0.0.1 是自己.
解法: `--network=host`. 容器内 127.0.0.1 即宿主, 代理直接可用.

**坑 2: SELinux 拒绝容器写家目录 (最隐蔽)**

现象: 容器内 `touch /home/bolo/xxx` 报 Permission denied, 但 `ls -ld` 显示属主/权限完全正确 (bolo:bolo, 700), 容器内身份也是 uid 1000.
原因: SELinux. 宿主家目录文件标签是 `user_home_t`, 容器进程标签是 `container_file_t` 域, 默认策略不允许容器进程写用户家目录. 传统 DAC 权限 (属主/rwx) 检查通过, 但 LSM 层拒绝. `ls -l` 看不出来, 需要看 `/proc/mounts` 的 context 或用 `ausearch -m avc` 排查.
解法: `--security-opt label=disable` 让容器进程不带容器标签运行. distrobox 默认即此行为, 这就是 distrobox "开箱即用" 的原因之一.
备注: 这是安全性换便利的取舍, 对受信任的自用开发容器可接受.

**坑 3: podman 默认共享内存过小, Chromium 图形模式必崩**

现象: Chromium 前台启动数秒后 core dump (exit 133), 只留下 `[chromium-browse]` 僵尸进程; headless 模式却正常.
原因: podman 默认给容器挂 64MB 的 tmpfs 作 `/dev/shm`, Chromium 多进程架构通过 shm 共享 GPU 命令缓冲等数据, 轻易超限, 触发崩溃. headless 不走这条路所以没事.
解法 (二选一):
- 启动参数加 `--disable-dev-shm-usage` (改用临时文件, 本例采用);
- 或容器加 `--shm-size=1g` 从根上解决 (更推荐, 更接近原生行为).

### 2.4 其他细节

- Fedora 的 Chromium 二进制名是 `chromium-browser` (deb 系才是 `chromium`), 实际脚本 `/usr/lib64/chromium-browser/chromium-browser.sh` 会 exec 真二进制.
- `--ozone-platform-hint=auto` 在容器内探测失败会回退 X11 并报 `Missing X server or $DISPLAY`; 显式 `--ozone-platform=wayland` 更稳.
- dbus 报错 (`Failed to connect to the bus`) 是非致命警告, 不影响窗口出现; 若需完整桌面集成 (托盘图标, xdg-open), 再挂 `/run/user/1000/bus` 并设 `DBUS_SESSION_BUS_ADDRESS`.
- 容器内 `dnf` 以 root 跑: `podman exec -u root`, 或建容器时指定 root 用户.

---

## 3. 通用化: 这套方案的工程化路径

### 3.1 手动方案的模板

任何 GUI 程序都适用同一模板:

```
必需: wayland socket 挂载 + WAYLAND_DISPLAY/XDG_RUNTIME_DIR 环境变量
推荐: /dev/dri, pulse socket, 家目录挂载, --network=host (按需)
NVIDIA: --cdi=nvidia.com/gpu=all (需 CDI 配置, Bazzite 已自动生成)
SELinux 启用系统: --security-opt label=disable
```

### 3.2 distrobox: 把接线自动化

distrobox 是上述模板的封装器, 底层就是 podman:

```bash
distrobox create --name dev --image registry.fedoraproject.org/fedora:latest
distrobox enter dev        # 进入后像正常 shell, 可 dnf install 任意东西
distrobox-export --app chromium-browser   # 生成桌面图标到宿主应用列表
```

它默认就做了: keep-id, label=disable, 挂载 home/wayland/pulse/dbus/GPU, 还额外生成 `.desktop` 文件让应用出现在宿主启动器里. 本次演示手写的每个参数, distrobox 都已内置. "无感体验" 的工业标准答案就是它.

### 3.3 与 Flatpak 的定位区分

| | Flatpak | distrobox/podman |
|---|---|---|
| 定位 | 面向最终用户的桌面应用分发 | 面向开发/任意软件的通用容器 |
| 接线 | 全自动 + portal 权限管理 | distrobox 自动, 裸 podman 手动 |
| 系统侵入性 | 沙盒内自带依赖 | 容器内是完整发行版, 可 dnf/apt |
| 典型用途 | 装浏览器/聊天/媒体软件 | 装开发工具链, 跑老版本依赖 |

### 3.4 跨平台适用性

- **Linux 宿主**: 完全复刻, 如上.
- **Windows**: podman 跑在 WSL2 内, WSLg 提供 Wayland/X 直通, 窗口可出现在 Windows 桌面, 体验良好但归功于 WSL 而非 podman.
- **macOS**: podman 跑在虚拟机内, 无原生 Wayland/X11, 需 XQuartz 转发, 延迟与保真度明显劣化, 不推荐.

---

## 4. 清理记录

演示产物已全部清除, 系统还原到演示前状态:

- 容器 `chromium-box`: `podman rm -f` 已删
- 镜像 `registry.fedoraproject.org/fedora:latest`: `podman rmi` 已删
- Chromium 配置目录 `/home/bolo/.config/chromium`: 已删
- podman 存储目录残留仅 168K 空目录结构, 属正常

验证: `podman ps -a` 与 `podman images` 均为空.

---

## 5. 结论

容器内 GUI 程序在宿主桌面上无感运行, 靠的不是什么虚拟显示或远程桌面, 而是: 显示权本来就归宿主合成器, 容器只需拿到那个 unix socket. 显卡/声音/文件同理, 都是挂载接线问题. 真正的坑在 SELinux 标签和共享内存这类默认安全/资源限制上. 裸 podman 可行但每步手动; 生产实践中用 distrobox 封装, 一次接线, 长期无感.
