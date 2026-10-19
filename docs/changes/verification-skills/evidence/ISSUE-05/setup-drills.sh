#!/usr/bin/env bash
# ISSUE-05 演练夹具准备. 只写 /tmp/orchestra-05, 不碰仓库与其他目录.
# 用法:
#   bash setup-drills.sh init                       建立夹具 (board / norecipe / stalerecipe 与两个红演练克隆)
#   bash setup-drills.sh install-skill <项目> <技能目录>  把待测 verify-change 复制进项目 .agents/skills/
#   bash setup-drills.sh install-recipe <项目>      写入一份过时的项目级验证配方 (只写 .agents/)
#   bash setup-drills.sh start-relay | stop-relay   外部 relay 依赖服务 (只在造旧证据时开)
#   bash setup-drills.sh remove-relay              删掉部署方 relay 文件, 使后续演练真的缺这个依赖服务
#   bash setup-drills.sh stop-instances             停掉夹具实例
#   bash setup-drills.sh status                     打印各夹具 HEAD 与工作区状态
#   bash setup-drills.sh add-ac004 <项目>            给 PRODUCT.md 追加 AC-004 并转正 (AC-009-4 演练用)
set -euo pipefail

REPO=${REPO:-/home/bolo/Workspace/skills/skills-v2.worktrees/ISSUE-05}
ROOT=/tmp/orchestra-05
BUILD="$ROOT/build"
MODE=${1:-init}
PORT=18201
RELAY_PORT=18290

stop_instances() {
  pkill -f "app.py serve --port 182" 2>/dev/null || true
  sleep 0.4
  pkill -9 -f "app.py serve --port 182" 2>/dev/null || true
}

stop_relay() {
  pkill -f "relay/relay.py" 2>/dev/null || true
  sleep 0.3
  pkill -9 -f "relay/relay.py" 2>/dev/null || true
}

start_relay() {
  mkdir -p "$ROOT/relay"
  nohup python3 "$ROOT/relay/relay.py" --port "$RELAY_PORT" >> "$ROOT/relay/relay.log" 2>&1 &
  for _ in $(seq 1 40); do
    if curl -sf "http://127.0.0.1:$RELAY_PORT/health" >/dev/null 2>&1; then
      echo "relay 就绪: 127.0.0.1:$RELAY_PORT"
      return 0
    fi
    sleep 0.2
  done
  echo "relay 未就绪" >&2
  return 1
}

write_relay() {
  mkdir -p "$ROOT/relay"
  cat > "$ROOT/relay/relay.py" <<'PYEOF'
#!/usr/bin/env python3
"""临时 relay 服务: 只接收 /ingest, 把收到的条目追加到同目录 ingest.jsonl."""
import argparse
import json
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

STORE = Path(__file__).resolve().parent / "ingest.jsonl"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _text(self, body: str, status: int = 200) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/health"):
            count = len(STORE.read_text(encoding="utf-8").splitlines()) if STORE.exists() else 0
            self._text(f"ok relay records={count}\n")
            return
        self._text("not found\n", status=404)

    def do_POST(self):
        if not self.path.startswith("/ingest"):
            self._text("not found\n", status=404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        entry = json.loads(raw)
        entry["received_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        with STORE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        count = len(STORE.read_text(encoding="utf-8").splitlines())
        self._text(f"relay=ok records={count}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"relay listening on 127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
PYEOF
}

write_app() {
  cat > "$1" <<'PYEOF'
#!/usr/bin/env python3
"""记录板: 状态页, report 单行与向外部 relay 服务同步一次事件."""
import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
from relaylib import VERSION as DEP_VERSION  # noqa: E402

VERSION = "relay-v2"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class Board:
    def __init__(self, instance: str, data_dir: str) -> None:
        self.instance = instance
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state = "ready"

    def status_page(self) -> str:
        return (
            "<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\"><title>relay board</title></head>\n"
            "<body><h1>relay board</h1>\n"
            f"<p>instance={self.instance}</p>\n<p>state={self.state}</p>\n"
            f"<p>version={VERSION}</p></body></html>\n"
        )

    def report_line(self) -> str:
        return f"relay-report instance={self.instance} version={VERSION} dep={DEP_VERSION}"

    def sync(self, relay_port: int) -> str:
        payload = json.dumps(
            {"instance": self.instance, "dep": DEP_VERSION, "ts": now_iso()}
        ).encode("utf-8")
        request = urllib.request.Request(
            f"http://127.0.0.1:{relay_port}/ingest",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8").strip()
        return f"sync-ok instance={self.instance} dep={DEP_VERSION} {body}"


def handler_factory(board: Board):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _text(self, body: str, status: int = 200, ctype: str = "text/plain; charset=utf-8") -> None:
            data = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            if parsed.path == "/health":
                self._text(f"ok instance={board.instance}\n")
                return
            if parsed.path == "/status-page":
                self._text(board.status_page(), ctype="text/html; charset=utf-8")
                return
            if parsed.path == "/report":
                self._text(board.report_line() + "\n")
                return
            if parsed.path == "/sync":
                port = int(query.get("relay", ["0"])[0])
                try:
                    body = board.sync(port)
                except OSError as exc:
                    self._text(f"relay-unreachable: {exc}\n", status=503)
                    return
                self._text(body + "\n")
                return
            self._text("not found\n", status=404)

    return Handler


def client_get(port: int, path: str) -> int:
    url = f"http://127.0.0.1:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            body = response.read().decode("utf-8")
            status = response.status
    except OSError as exc:
        print(f"request failed: {exc}", file=sys.stderr)
        return 1
    if status != 200:
        print(f"status {status}: {body}", file=sys.stderr)
        return 1
    sys.stdout.write(body)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="app.py")
    commands = parser.add_subparsers(dest="command", required=True)

    serve = commands.add_parser("serve")
    serve.add_argument("--port", type=int, required=True)
    serve.add_argument("--instance", required=True)
    serve.add_argument("--data-dir", required=True)

    for name in ("health", "status", "report"):
        sub = commands.add_parser(name)
        sub.add_argument("--port", type=int, required=True)

    sync = commands.add_parser("sync")
    sync.add_argument("--port", type=int, required=True)
    sync.add_argument("--relay-port", type=int, required=True)

    args = parser.parse_args(argv)

    if args.command == "serve":
        board = Board(args.instance, args.data_dir)
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_factory(board))
        print(f"listening on 127.0.0.1:{args.port} instance={board.instance}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        return 0
    if args.command == "health":
        return client_get(args.port, "/health")
    if args.command == "status":
        return client_get(args.port, "/status-page")
    if args.command == "report":
        return client_get(args.port, "/report")
    if args.command == "sync":
        return client_get(args.port, f"/sync?relay={args.relay_port}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
PYEOF
}

write_products() {
  mkdir -p "$BUILD"

  cat > "$BUILD/PRODUCT.board.base.md" <<'EOF'
# 记录板 Product Spec

## 背景

值班同学需要一个本地记录板: 实例提供状态页与 report 单行, 并能把一次事件同步到部署方提供的 relay 服务.

## 目标

- G-001: 实例显示自身状态页.
- G-002: 实例输出 report 单行.
- G-003: 实例把一次事件同步到 relay 服务并回报结果.

## 非目标

- NG-001: 不做鉴权与多用户管理. (理由: 只在本地临时实例上使用.)

## 业务规则

- BR-001: status 与 report 的 version 字段只取自实例自身, relay 服务不可用时也不改变. (审计)

## 验收标准

## 决策引用

- 无.
EOF

  cat > "$BUILD/draft.board.v1.md" <<'EOF'
```gherkin
# language: zh-CN
功能: 记录板

@AC-001 @normal @G-001
场景: AC-001-1 状态页
  假定 实例 board 正在 127.0.0.1:18201 运行且 health 返回 `ok instance=board`
  当 验收者运行 `python3 app.py status --port 18201`
  那么 输出含 `instance=board`, `state=ready` 与 `version=relay-v2` 且退出码为 0

@AC-002 @normal @G-002
场景: AC-002-1 report 单行
  假定 实例 board 正在 127.0.0.1:18201 运行
  当 验收者运行 `python3 app.py report --port 18201`
  那么 输出形如 `relay-report instance=board version=relay-v2 dep=<n>` 且退出码为 0
  而且 其中的 dep 值与 `deps.txt` 记录的依赖版本一致

@AC-003 @normal @G-003
场景: AC-003-1 同步到 relay 服务
  假定 部署方提供的 relay 服务正在 127.0.0.1:18290 监听且实例 board 正在 127.0.0.1:18201 运行
  当 验收者运行 `python3 app.py sync --port 18201 --relay-port 18290`
  那么 输出含 `sync-ok instance=board` 与 `relay=ok` 且退出码为 0
```
EOF

  cat > "$BUILD/draft.board.v2.md" <<'EOF'
```gherkin
# language: zh-CN
功能: 记录板

@AC-001 @normal @G-001
场景: AC-001-1 状态页
  假定 实例 board 正在 127.0.0.1:18201 运行且 health 返回 `ok instance=board`
  当 验收者运行 `python3 app.py status --port 18201`
  那么 输出含 `instance=board`, `state=ready` 与 `version=relay-v2` 且退出码为 0

@AC-002 @normal @G-002
场景: AC-002-1 report 单行
  假定 实例 board 正在 127.0.0.1:18201 运行
  当 验收者运行 `python3 app.py report --port 18201`
  那么 输出形如 `relay-report instance=board version=relay-v2 dep=<n>` 且退出码为 0
  而且 其中的 dep 值与 `deps.txt` 记录的依赖版本一致

@AC-003 @normal @G-003
场景: AC-003-1 同步到 relay 服务
  假定 部署方提供的 relay 服务正在 127.0.0.1:18290 监听且实例 board 正在 127.0.0.1:18201 运行
  当 验收者运行 `python3 app.py sync --port 18201 --relay-port 18290`
  那么 输出含 `sync-ok instance=board` 与 `relay=ok` 且退出码为 0

@AC-004 @normal @G-002
场景: AC-004-1 端口未监听时报错
  假定 127.0.0.1:18299 上没有实例在运行
  当 验收者运行 `python3 app.py report --port 18299`
  那么 退出码非 0 且 stderr 含 `request failed`
```
EOF

  cat > "$BUILD/draft.min.v1.md" <<'EOF'
```gherkin
# language: zh-CN
功能: 记录板

@AC-001 @normal @G-001
场景: AC-001-1 状态页
  假定 实例 board 正在 127.0.0.1:18201 运行且 health 返回 `ok instance=board`
  当 验收者运行 `python3 app.py status --port 18201`
  那么 输出含 `instance=board`, `state=ready` 与 `version=relay-v2` 且退出码为 0

@AC-002 @normal @G-002
场景: AC-002-1 report 单行
  假定 实例 board 正在 127.0.0.1:18201 运行
  当 验收者运行 `python3 app.py report --port 18201`
  那么 输出形如 `relay-report instance=board version=relay-v2 dep=<n>` 且退出码为 0
  而且 其中的 dep 值与 `deps.txt` 记录的依赖版本一致
```
EOF
}

promote_product() {
  local base="$1" draft="$2" out="$3" review
  review=$(cd "$REPO" && uv run workflow/to-spec/ac-draft.py preview "$base" "$draft" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["review_id"])')
  (cd "$REPO" && uv run workflow/to-spec/ac-draft.py promote "$base" "$draft" "$out" --review "$review" >/dev/null)
  (cd "$REPO" && uv run workflow/to-spec/check-ac.py "$out" >/dev/null)
}

write_readme() {
  cat > "$1/README.md" <<'EOF'
# 记录板

单实例本地记录板: 状态页, report 单行, 以及向部署方提供的 relay 服务同步一次事件.

## 启动实例

```bash
mkdir -p runtime/board
python3 app.py serve --port PORT_PLACEHOLDER --instance board --data-dir runtime/board &
python3 app.py health --port PORT_PLACEHOLDER
```

## 命令

- `python3 app.py status --port PORT_PLACEHOLDER`: 打印状态页 HTML.
- `python3 app.py report --port PORT_PLACEHOLDER`: 打印 report 单行.
- `python3 app.py sync --port PORT_PLACEHOLDER --relay-port 18290`: 同步一次事件到 relay 服务.

sync 需要部署方提供的 relay 服务在 127.0.0.1:18290 监听; 该服务不在本仓库内, 本项目也不提供它的替身.

## 依赖

`vendor/relaylib.py` 是随项目提交的依赖副本, 版本记录在 `deps.txt`.

## 测试

仓库没有自动化测试, 用上面的命令自查.

`runtime/` 与 `.agents/` 在 `.gitignore` 里.
EOF
}

write_stale_recipe() {
  local project="$1"
  mkdir -p "$project/.agents/skills/verify-board"
  cat > "$project/.agents/skills/verify-board/SKILL.md" <<'EOF'
---
name: verify-board
description: 记录板项目本地验证配方: 启动实例后核对状态页与 report.
disable-model-invocation: true
---

# 记录板验证配方

## 启动实例

```bash
mkdir -p runtime/board
python3 app.py serve --port 18001 --data-root runtime/board &
python3 app.py health --port 18001
```

`/health` 返回 `ok instance=board` 表示实例可用.

## 核对状态页

```bash
python3 app.py status --port 18001
```

输出含 `instance=board` 与 `version=relay-v1` 即通过.

## 核对 report

```bash
python3 app.py report --port 18001
```

输出形如 `relay-report instance=board version=relay-v1` 即通过.

## 取证

把命令输出存到 `runtime/` 下. 结束时 `kill` 掉实例进程.
EOF
}

# 造旧运行记录: 真的启动实例与 relay 服务, 跑一遍并保存原始输出.
collect_old_evidence() {
  local project="$1" evid="$1/docs/changes/board/evidence/board-dep-1.2-run"
  mkdir -p "$evid" "$project/runtime/board"
  start_relay >/dev/null
  ( cd "$project" && nohup python3 app.py serve --port "$PORT" --instance board --data-dir runtime/board \
      > "$evid/server.stdout.log" 2>&1 & )
  for _ in $(seq 1 40); do
    curl -sf "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && break
    sleep 0.2
  done
  (
    cd "$project"
    set +e
    python3 app.py health --port "$PORT" > "$evid/01-health.txt" 2>&1; echo "exit=$?" >> "$evid/01-health.txt"
    python3 app.py status --port "$PORT" > "$evid/02-status.html" 2>&1; echo "exit=$?" >> "$evid/02-status.html"
    python3 app.py report --port "$PORT" > "$evid/03-report.txt" 2>&1; echo "exit=$?" >> "$evid/03-report.txt"
    python3 app.py sync --port "$PORT" --relay-port "$RELAY_PORT" > "$evid/04-sync.txt" 2>&1; echo "exit=$?" >> "$evid/04-sync.txt"
    set -e
  )
  stop_instances
  stop_relay
  cat > "$evid/RUN.md" <<EOF
# board 依赖 1.2 的那轮运行记录

- 运行时间: $(date -u +%Y-%m-%dT%H:%M:%SZ) (UTC)
- 运行版本: 产品提交 $(git -C "$project" rev-parse HEAD) (tag 前的那次提交, 依赖版本 1.2)
- 依赖: \`vendor/relaylib.py\` VERSION=1.2, \`deps.txt\` 记 relaylib 1.2
- 环境: 本机 127.0.0.1:18201 实例 board, 部署方 relay 服务 127.0.0.1:18290 当时在监听
- 原始输出: \`01-health.txt\`, \`02-status.html\`, \`03-report.txt\`, \`04-sync.txt\`, \`server.stdout.log\`
- 各命令退出码见文件末尾的 \`exit=\` 行, 全部为 0
- 说明: 这是旧观察, 只对上面的版本与依赖/环境条件成立; 本轮验收引用前须核对条件是否仍适用
EOF
}

make_board() {
  local dir="$1"
  rm -rf "$dir"
  mkdir -p "$dir/docs/changes/board" "$dir/vendor"
  printf '.agents/\nruntime/\n__pycache__/\n.pytest_cache/\n' > "$dir/.gitignore"
  write_app "$dir/app.py"
  write_readme "$dir"
  printf 'VERSION = "1.2"\n' > "$dir/vendor/relaylib.py"
  printf 'relaylib (vendor) 1.2\n' > "$dir/deps.txt"
  printf '# 值班记录\n\n第一批交接说明.\n' > "$dir/docs/notes.md"
  cp "$BUILD/PRODUCT.board.base.md" "$BUILD/_base.tmp.md"
  cp "$BUILD/draft.board.v1.md" "$BUILD/_draft.tmp.md"
  promote_product "$BUILD/_base.tmp.md" "$BUILD/_draft.tmp.md" "$dir/docs/changes/board/PRODUCT.md"
  rm -f "$BUILD/_base.tmp.md" "$BUILD/_draft.tmp.md"

  (
    cd "$dir"
    git init -q -b main
    git add -A
    git commit -q -m "初始化记录板骨架与产品标准"
  )
  collect_old_evidence "$dir"
  (
    cd "$dir"
    git add -A
    git commit -q -m "docs: 记录依赖 1.2 的首轮运行输出"
    # T1: 只改不参与构建运行的说明材料, 代码/依赖/配置/环境都不动.
    printf '# 值班记录\n\n第一批交接说明.\n\n第二批: 补充交接口径, 不涉及启动与入口.\n' > docs/notes.md
    git add -A
    git commit -q -m "docs: 补充交接说明"
    # T2: 把依赖副本升级到 1.3, 影响 report 的 dep 字段.
    printf 'VERSION = "1.3"\n' > vendor/relaylib.py
    printf 'relaylib (vendor) 1.3\n' > deps.txt
    git add -A
    git commit -q -m "feat: 依赖升级到 1.3"
  )
}

do_rebuild_board() {
  stop_instances
  mkdir -p "$BUILD"
  write_relay
  write_products
  make_board "$ROOT/board"
  rm -rf "$ROOT/red-board2"
  git clone -q "$ROOT/board" "$ROOT/red-board2"
  ( cd "$ROOT/red-board2" && git reset -q --hard HEAD~1 )
  echo "rebuild-board 完成: $ROOT/board (T1=docs only, T2=dep 1.3), $ROOT/red-board2 (停在 T1)"
}

make_min() {
  local dir="$1" port="${2:-18201}"
  rm -rf "$dir"
  mkdir -p "$dir/docs/changes/board" "$dir/vendor"
  printf '.agents/\nruntime/\n__pycache__/\n.pytest_cache/\n' > "$dir/.gitignore"
  write_app "$dir/app.py"
  write_readme "$dir" "$port"
  sed -i "s/PORT_PLACEHOLDER/$port/g" "$dir/README.md"
  printf 'VERSION = "1.3"\n' > "$dir/vendor/relaylib.py"
  printf 'relaylib (vendor) 1.3\n' > "$dir/deps.txt"
  cp "$BUILD/PRODUCT.board.base.md" "$BUILD/_base.tmp.md"
  sed "s/18201/$port/g" "$BUILD/draft.min.v1.md" > "$BUILD/_draft.tmp.md"
  promote_product "$BUILD/_base.tmp.md" "$BUILD/_draft.tmp.md" "$dir/docs/changes/board/PRODUCT.md"
  rm -f "$BUILD/_base.tmp.md" "$BUILD/_draft.tmp.md"
  (
    cd "$dir"
    git init -q -b main
    git add -A
    git commit -q -m "初始化记录板骨架与产品标准"
  )
}

do_init() {
  stop_instances
  stop_relay
  rm -rf "$ROOT"
  mkdir -p "$BUILD"
  write_relay
  write_products
  make_board "$ROOT/board"
  make_min "$ROOT/norecipe"
  cp -a "$ROOT/norecipe" "$ROOT/stalerecipe"
  write_stale_recipe "$ROOT/stalerecipe"
  git clone -q "$ROOT/board" "$ROOT/red-board"
  cp -a "$ROOT/norecipe" "$ROOT/red-stalerecipe"
  write_stale_recipe "$ROOT/red-stalerecipe"
  echo "init 完成: $ROOT/{board,norecipe,stalerecipe,red-board,red-stalerecipe}"
}

install_skill() {
  local project="$1" skilldir="$2"
  mkdir -p "$project/.agents/skills"
  rm -rf "$project/.agents/skills/verify-change"
  cp -a "$skilldir" "$project/.agents/skills/verify-change"
  echo "已安装: $project/.agents/skills/verify-change"
}

add_ac004() {
  local project="$1"
  cp "$BUILD/PRODUCT.board.base.md" "$project/.tmp-base.md"
  cp "$BUILD/draft.board.v2.md" "$project/.tmp-draft.md"
  promote_product "$project/.tmp-base.md" "$project/.tmp-draft.md" "$project/docs/changes/board/PRODUCT.md"
  rm -f "$project/.tmp-base.md" "$project/.tmp-draft.md"
  ( cd "$project" && git add -A && git commit -q -m "docs: 产品标准新增 AC-004 并确认" && git rev-parse HEAD )
}

do_status() {
  for d in "$ROOT"/*/; do
    [ -d "$d/.git" ] || continue
    echo "== $d"
    git -C "$d" log --oneline | sed 's/^/  /'
    git -C "$d" status --short | sed 's/^/  /'
  done
}

main() {
  case "$MODE" in
    init) do_init ;;
    install-skill) install_skill "${2:?项目路径}" "${3:?技能目录}" ;;
    new-min) mkdir -p "$BUILD"; write_products; make_min "${2:?项目路径}" "${3:?端口}"; echo "new-min 完成: $2" ;;
    install-recipe) write_stale_recipe "${2:?项目路径}" ;;
    start-relay) start_relay ;;
    stop-relay) stop_relay ;;
    remove-relay) stop_relay; rm -rf "$ROOT/relay"; echo "已删除部署方 relay 文件: $ROOT/relay" ;;
    stop-instances) stop_instances ;;
    add-ac004) add_ac004 "${2:?项目路径}" ;;
    status) do_status ;;
    rebuild-board) do_rebuild_board ;;
    *) echo "未知模式: $MODE" >&2; exit 2 ;;
  esac
}

main "$@"
