# Chromium 的显示环境

Herdr 窗格内 Chromium 启动失败时读取. 这是 Linux Wayland 桌面的实测问题, 与 agent kind 无关.

实测 Herdr shell 未继承桌面环境变量, DISPLAY/WAYLAND_DISPLAY 为空时, present/access-web 启动 Chromium 会因 ozone 误选 X11 崩溃, 报 `CDP port not reachable`.
确认目标机器实际使用的显示环境, 把有效环境传给原启动命令. Wayland 使用桌面会话的实际显示名, 并显式选择后端:

```bash
WAYLAND_DISPLAY="<实际显示名>" BROWSER_EXTRA_ARGS=--ozone-platform=wayland <原启动命令>
```

显示名由目标环境决定, 不固定为某个 socket 名. XWayland 还依赖 XAUTHORITY, 此问题优先修正已有的 Wayland 环境. 目标没有可用桌面会话时报告环境缺失.
