#!/bin/sh
# swt-headed-browser.sh — 容器内 headed chromium 启动脚本母本 (M08 D003).
# 本文件是母本: __CHROMIUM__ 占位符由 swt birth 用 throwaway 容器解析出的
# chromium 精确字面路径替换 (UD-06), 实例落 <records_root>/runtime/<identity>/
# 后只读挂载进容器固定路径 /home/bolo/.local/bin/swt-headed-browser.sh.
#
# preflight (D007(1)/UD-11): WAYLAND_DISPLAY 与 XDG_RUNTIME_DIR 在场, 且
# $XDG_RUNTIME_DIR/$WAYLAND_DISPLAY 可 AF_UNIX connect 才启动 — 覆盖宿主
# 直通烘死的变量在宿主桌面注销后变死 socket 的翻车点. 不满足 exit 86:
# 容器 AI 见 86 即按三态编排走信箱投信请设备侧拉窗, 不重试本脚本.
if [ -z "$WAYLAND_DISPLAY" ] || [ -z "$XDG_RUNTIME_DIR" ]; then
    exit 86
fi
if ! python3 -c 'import socket, sys
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.settimeout(2)
sock.connect(sys.argv[1])
sock.close()' "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" 2>/dev/null; then
    exit 86
fi
# 音频 (D002/UD-08): 设备侧 -R 建立的 pulse socket 在场才导出; 宿主直通模式
# 下该 socket 不存在, 硬导出会断 chromium 本地音频.
if [ -S /tmp/swt/pulse-b.sock ]; then
    export PULSE_SERVER=unix:/tmp/swt/pulse-b.sock
fi
# N1: env 由本脚本内部设置, exec 命令行禁止 VAR=... 赋值前缀 (waypipe 会把
# 前缀当程序名, Spawn failure).
exec '__CHROMIUM__' --no-sandbox --ozone-platform=wayland "$@"
