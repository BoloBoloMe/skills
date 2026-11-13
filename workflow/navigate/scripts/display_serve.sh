#!/usr/bin/env bash
# navigate 展示服务编排/复原入口 (milestone-17).
#
# 展示实例的固定身份: 运行时目录 /tmp/navigate-display-<uid>, 端口 39300,
# 网段经转发桥 (如 8801 -> 127.0.0.1:39300) 给浏览器长期访问. 桥固定指端口,
# 只要服务复原回 39300, 桥零操作自愈 -- 本脚本就是"服务死了能复原回 39300"
# 的那条可重复命令. socat 桥本身不在本脚本管辖内.
#
# 用法:
#   display_serve.sh ensure    首选入口: 服务活着且端口对则直接复用;
#                              死了则拉起; 端口不对则重建 (详见下).
#   display_serve.sh start     启动 (幂等复用) 并校验端口 == 期望端口.
#   display_serve.sh status    查看状态 (存活, pid, 端口).
#   display_serve.sh stop      停止展示实例 (仅复原/演练时用; 日常收工禁用,
#                              收工不 stop 展示服务).
#
# 行为约定:
#   - ensure 对"活着但端口不对"的实例自动 stop + start 重建: 本运行时目录
#     归展示脚本专属, 里面不该有别的端口的实例.
#   - start/ensure 遇陌生进程占端口: web_server.py 报 port_in_use 且不漂移,
#     本脚本原样报错退出, 不杀占用者, 不换端口.
#   - stdout 只输出最后一行 JSON (web_server.py 的结果), 供调用方解析;
#     诊断信息全部走 stderr. 退出码 0 成功 / 1 失败.
#
# 测试与演练覆盖 (不碰真实展示实例):
#   NAVIGATE_DISPLAY_PORT / NAVIGATE_DISPLAY_RUNTIME_DIR 可覆盖固定端口与
#   固定目录; 另可用 NAVIGATE_DISPLAY_PYTHON 指定解释器.
#
# 自愈巡检: 本脚本不自带常驻巡检守护 (那会引入又一个无主单例, 正是
# milestone-16 根因之一); ensure 幂等, 可按需重复执行或挂 cron.

set -u

HERE=$(cd -- "$(dirname -- "$0")" && pwd)
WEB_SERVER="$HERE/web_server.py"
[ -f "$WEB_SERVER" ] || { echo "display_serve: 找不到 $WEB_SERVER" >&2; exit 1; }

DISPLAY_PORT="${NAVIGATE_DISPLAY_PORT:-39300}"
DISPLAY_RUNTIME_DIR="${NAVIGATE_DISPLAY_RUNTIME_DIR:-/tmp/navigate-display-$(id -u)}"
export NAVIGATE_WEB_PORT="$DISPLAY_PORT"
export NAVIGATE_WEB_RUNTIME_DIR="$DISPLAY_RUNTIME_DIR"

PYTHON="${NAVIGATE_DISPLAY_PYTHON:-python3}"
command -v "$PYTHON" >/dev/null 2>&1 || PYTHON=python
command -v "$PYTHON" >/dev/null 2>&1 || { echo "display_serve: 无可用 python" >&2; exit 1; }

say() { echo "display_serve: $*" >&2; }
die() { echo "display_serve: $*" >&2; exit 1; }

json_field() { # $1=json 文本 $2=键名 -> 输出值 (缺失输出空串)
    printf '%s' "$1" | "$PYTHON" -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    print("")
    raise SystemExit
value = data.get(sys.argv[1])
print("" if value is None else value)
' "$2"
}

cli() { # $1=子命令 -> stdout 存全局 CLI_OUT; 失败时 die
    CLI_OUT=$("$PYTHON" "$WEB_SERVER" "$1") || die "$1 失败: $CLI_OUT"
}

do_start() {
    cli start
    port=$(json_field "$CLI_OUT" port)
    [ "$port" = "$DISPLAY_PORT" ] \
        || die "端口漂移: 期望 $DISPLAY_PORT, 实际 ${port:-未知}; 不自动改道, 请人工检查"
    say "start ok: port=$DISPLAY_PORT pid=$(json_field "$CLI_OUT" pid) runtime=$DISPLAY_RUNTIME_DIR"
    echo "$CLI_OUT"
}

do_ensure() {
    cli status
    alive=$(json_field "$CLI_OUT" alive)
    if [ "$alive" = "True" ]; then
        port=$(json_field "$CLI_OUT" port)
        if [ "$port" = "$DISPLAY_PORT" ]; then
            say "ensure ok: 复用存活实例 port=$DISPLAY_PORT pid=$(json_field "$CLI_OUT" pid)"
            echo "$CLI_OUT"
            return 0
        fi
        say "实例存活但端口为 ${port:-未知} (期望 $DISPLAY_PORT), 重建以复原固定端口"
        cli stop
    fi
    do_start
}

case "${1:-}" in
    start) do_start ;;
    stop)
        cli stop
        say "stop done (日常收工请勿调用本命令)"
        echo "$CLI_OUT"
        ;;
    status)
        cli status
        echo "$CLI_OUT"
        ;;
    ensure) do_ensure ;;
    *) say "用法: display_serve.sh <ensure|start|status|stop>"; exit 1 ;;
esac
