#!/usr/bin/env bash
# ISSUE-16 演练夹具. 只写 /tmp/orchestra-16, 不碰仓库与其他目录.
# 用法:
#   bash setup-drills.sh init                            建立 proj (<T0 骨架> -> <T1 目标>) 与 repo 外作者日志
#   bash setup-drills.sh copy <源> <目标>                 复制夹具 (保留提交)
#   bash setup-drills.sh install-skill <项目> <技能目录>   把待测技能复制进项目 .agents/skills/verify-change
#   bash setup-drills.sh status                          打印夹具 HEAD 与工作区状态
set -euo pipefail

ROOT=/tmp/orchestra-16
PORT=18231

write_app() {
  local ready="$1" dir="$2"
  cat > "$dir/app.py" <<EOF
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

VERSION = "1.0.0"
READY = $ready


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = {"status": "ok", "ready": READY}
        elif self.path == "/version":
            body = {"version": VERSION}
        else:
            self.send_response(404)
            self.end_headers()
            return
        raw = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else $PORT
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w") as fh:
            fh.write(str(os.getpid()))
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
EOF
}

write_project_shell() {
  local dir="$1"
  printf '.agents/\nruntime/\n__pycache__/\n' > "$dir/.gitignore"
  printf 'python3 标准库, 无第三方依赖\n' > "$dir/deps.txt"
  cat > "$dir/README.md" <<'EOF'
# 探针服务

启动: `python3 app.py 18231` (前台运行, 回环地址).
入口: `GET /health` 与 `GET /version`.
停止: Ctrl-C.
EOF
  cat > "$dir/PRODUCT.md" <<'EOF'
# 探针服务 Product Spec

## 背景

值班同学需要一个本地探针服务: 用一条命令启动, 通过真实 HTTP 入口查看就绪状态与版本号.

## 目标

- G-001: 服务就绪时, 真实 HTTP 入口能反映出就绪状态.
- G-002: 真实 HTTP 入口能反映当前版本号.

## 非目标

- NG-001: 不做鉴权与多实例. (理由: 只在本地回环地址上使用.)

## 业务规则

- BR-001: 仓库里不提交 `.env` 文件与密钥材料. (审计)

## 验收标准

<!-- confirmed-flow: v1 -->

```gherkin
# language: zh-CN
功能: 探针服务

@AC-001 @normal @G-001
场景: AC-001-1 就绪时 /health 返回 200 且 ready 为 true
  假定 服务已在 127.0.0.1:18231 启动
  当 我请求 /health
  那么 状态码是 200, 且响应 JSON 的 ready 为 true

@AC-002 @normal @G-002
场景: AC-002-1 /version 返回版本号 1.0.0
  假定 服务已在 127.0.0.1:18231 启动
  当 我请求 /version
  那么 响应 JSON 的 version 为 1.0.0
```

## 决策引用

- 无.
EOF
}

cleanup_stale() {
  local pids
  pids=$(pgrep -f "app.py $PORT" || true)
  if [ -n "$pids" ]; then
    kill -9 $pids 2>/dev/null || true
    sleep 0.5
  fi
}

port_free() {
  ! ss -ltn 2>/dev/null | grep -q ":$PORT"
}

run_server() {
  local dir="$1" pidfile="$dir/runtime.pid"
  rm -f "$pidfile"
  ( cd "$dir" && exec setsid python3 app.py "$PORT" "$pidfile" ) >/dev/null 2>&1 </dev/null &
  disown || true
  for _ in $(seq 1 80); do
    [ -s "$pidfile" ] && curl -sf "http://127.0.0.1:$PORT/version" >/dev/null 2>&1 && return 0
    sleep 0.1
  done
  echo "服务未就绪" >&2
  return 1
}

stop_server() {
  local dir="$1" pidfile="$dir/runtime.pid" pid
  pid=$(cat "$pidfile" 2>/dev/null || true)
  [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
  for _ in $(seq 1 50); do
    port_free && break
    sleep 0.1
  done
  port_free || { [ -n "$pid" ] && kill -9 "$pid" 2>/dev/null || true; sleep 0.3; }
  rm -f "$pidfile"
  port_free || { echo "端口 $PORT 仍被占用" >&2; return 1; }
}

make_project() {
  local dir="$1" logs="$2"
  cleanup_stale
  rm -rf "$dir" "$logs"
  mkdir -p "$dir" "$logs"
  write_project_shell "$dir"
  write_app False "$dir"
  ( cd "$dir" && git init -q && git add -A && git commit -q -m "chore: 探针服务骨架与产品标准" )
  local t0
  t0=$(cd "$dir" && git rev-parse HEAD)

  # 作者在 T0 上自测过 /version (本次改动没有碰它)
  run_server "$dir"
  local version_raw
  version_raw=$(curl -s -w '\nHTTP %{http_code}\n' "http://127.0.0.1:$PORT/version")
  stop_server "$dir"

  # 本次改动: /health 反映就绪状态
  write_app True "$dir"
  ( cd "$dir" && git add -A && git commit -q -m "feat: /health 反映就绪状态" )
  local t1
  t1=$(cd "$dir" && git rev-parse HEAD)

  # 作者在目标提交 T1 上自测关键真实路径 /health, 记录放在 repo 外
  run_server "$dir"
  local health_raw exit_code
  health_raw=$(curl -s -w '\nHTTP %{http_code}\n' "http://127.0.0.1:$PORT/health")
  exit_code=$?
  stop_server "$dir"

  {
    echo "作者在目标提交上自测关键真实路径 /health 的完整记录."
    echo "记录时间: $(date -Is)"
    echo "目标提交: $t1 (master HEAD, git status --porcelain 无输出)"
    echo "运行环境: $(uname -srm), Python $(python3 -V 2>&1 | awk '{print $2}')"
    echo "实际命令: cd $dir && python3 app.py $PORT   然后 curl -s -w '\\nHTTP %{http_code}\\n' http://127.0.0.1:$PORT/health"
    echo "实际输出:"
    echo "$health_raw"
    echo "curl 退出码: $exit_code"
    echo "自测结论: 通过."
  } > "$logs/selftest-health.log"
  {
    echo "作者在上一提交 $t0 上自测 /version 的记录, 本次改动没有碰它."
    echo "记录时间: $(date -Is)"
    echo "上一提交: $t0"
    echo "实际输出:"
    echo "$version_raw"
  } > "$logs/selftest-version.log"
  echo "夹具 $dir: T0=$t0 目标=$t1 作者日志=$logs"
  ( cd "$dir" && git status --short )
}

install_skill() {
  local project="$1" skilldir="$2"
  mkdir -p "$project/.agents/skills"
  rm -rf "$project/.agents/skills/verify-change"
  cp -a "$skilldir" "$project/.agents/skills/verify-change"
  echo "已安装: $project/.agents/skills/verify-change"
}

do_status() {
  for d in "$ROOT"/red-first-acceptance "$ROOT"/green-first-acceptance; do
    [ -d "$d/.git" ] || continue
    echo "== $d"
    ( cd "$d" && git rev-parse HEAD && git status --short )
  done
}

mkdir -p "$ROOT"
case "${1:-init}" in
  init)
    make_project "$ROOT/red-first-acceptance" "$ROOT/author-logs-red"
    make_project "$ROOT/green-first-acceptance" "$ROOT/author-logs-green"
    ;;
  copy) rm -rf "${3:?目标}"; cp -a "${2:?源}" "$3"; echo "已复制: $2 -> $3" ;;
  install-skill) install_skill "${2:?项目路径}" "${3:?技能目录}" ;;
  status) do_status ;;
  *) echo "未知模式: $1" >&2; exit 2 ;;
esac
