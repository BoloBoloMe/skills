# pi agent 注意事项

从 herdr 驱动 pi 时的本机实测注意点.

提交键是 `alt+\`, 不是 `enter`; `agent prompt` 默认发的 enter 只把文本留在输入框. 提交用两步:

```bash
herdr pane send-text <pane-id> '<任务文本>' && herdr agent send-keys <短名> "alt+\\"
```

行尾双反斜杠经 shell 转义, Herdr 收到的键名是 `alt+\`.

`--wait` / `wait` 会误报 `agent_prompt_stalled` (pi 干完很快回 idle, 或快照滞后), 不等于文本没送达; 重发前先 `agent read` 看屏幕, 免得任务提交两遍. 真实进度以最新 read 和仓库文件变化为准, 不以状态字段为准.

herdr 会话的 shell 可能没继承桌面环境变量 (DISPLAY/WAYLAND_DISPLAY 为空): present/access-web 启动 Chromium 会因 ozone 误选 X11 崩溃 (报 CDP port not reachable). 解法: 显式给环境再启动 — `WAYLAND_DISPLAY=wayland-0 BROWSER_EXTRA_ARGS=--ozone-platform=wayland` (XWayland 路线要 XAUTHORITY, 不必试).
