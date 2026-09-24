# 拉窗 (swt.pull-window) 收信侧配方

容器把 GUI 窗口拉到设备侧显示的 exec 指令. 服务端内置动态绑定 (不落静态 whitelist 行, 安全语义见 mailbox.md 指令集现状节); 设备侧取信脚本内置机械门禁 (waypipe 在场 + 同容器 300s 限频, 限频键 = 容器标识). 三态选路 (宿主直通 wayland / 设备侧 waypipe 直飞 / noVNC 兜底) 与容器侧编排见 use-sandbox-worktree skill 的 `reference/pull-window.md`.

## 信形状

type = `exec`, body 为 JSON dict, 恰含下列键 (多余键一律降级):

- `tool`: 固定 `swt.pull-window`.
- `container`: 投信方 session id **或其容器名**, 二者皆命中直批 (E1). 容器 session 形态 = `<容器名>-<8hex 随机尾>` (D010), 服务端按剥尾匹配容器名; 填他人 session/容器名一律降级 request, 走设备侧权限流程. 限频键同样归一到容器标识 — 同一容器换写法 (填 session id 或容器名) 不重置 300s 窗.
- `url` (可选): 设备侧按信中 url 拉起页面, 不猜端口 (E2). 缺省沿用前置编排补全的页面地址 (容器内 `127.0.0.1:<web端口>` 形态).

## 设备侧拉起模板 (E4)

前提: 设备 Linux Wayland 桌面会话 + waypipe 客户端. 拉起前先做幂等探测 (`ssh <容器> pgrep -x waypipe`, 已有活跃会话不再拉).

标准写法 (带音频):

```bash
nohup waypipe ssh -p <宿主ssh端口> -R /tmp/swt/pulse-b.sock:/run/user/$(id -u)/pulse/native bolo@<host-LAN-IP> /home/bolo/.local/bin/swt-headed-browser.sh --user-data-dir=/tmp/pullwin-<标记> --disable-gpu --disable-gpu-compositing --no-first-run --no-default-browser-check --start-maximized <url> >/dev/null 2>&1 &
```

退化写法 (无音频): 容器无 `/run/user` 时音频 socket 转发建不出, 省去整个 `-R /tmp/swt/pulse-b.sock:/run/user/$(id -u)/pulse/native` 段, 其余参数不变 — 仅损失声音, 拉窗不受影响:

```bash
nohup waypipe ssh -p <宿主ssh端口> bolo@<host-LAN-IP> /home/bolo/.local/bin/swt-headed-browser.sh --user-data-dir=/tmp/pullwin-<标记> --disable-gpu --disable-gpu-compositing --no-first-run --no-default-browser-check --start-maximized <url> >/dev/null 2>&1 &
```

- `--user-data-dir` 强制: chromium 单例坑 — 默认 profile 被占时新调用被单例转发后秒退 (实测两次), 必须独立数据目录. `<标记>` 用容器名或来信 id 区分多窗.
- 软件渲染参数 (`--disable-gpu --disable-gpu-compositing`) 必带: GPU 路径经部分 waypipe 版本只出隐形窗口 (任务栏有图标无画面).
- waypipe 会话须长存, nohup 后台, 不占 LLM 前台.
- `<url>` 位即信中 `url` 参数 (有则用之, 不猜端口).
