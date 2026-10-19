#!/usr/bin/env bash
# ISSUE-04 演练夹具准备. 只写 /tmp/orchestra-04, 不碰仓库与其他目录.
# 用法:
#   bash setup-drills.sh init                              建立夹具, 每个带 T0 初始提交与 T1 目标提交
#   bash setup-drills.sh install-skill <项目> <技能目录>    把待测技能复制进项目 .agents/skills/
#   bash setup-drills.sh status                            打印各夹具 HEAD 与工作区状态
#   bash setup-drills.sh reset-runtime                     停掉夹具实例并清 runtime 目录
set -euo pipefail

REPO=${REPO:-/home/bolo/Workspace/skills/skills-v2.worktrees/ISSUE-04}
ROOT=/tmp/orchestra-04
BUILD="$ROOT/build"
MODE=${1:-init}
PORT_A=18101
PORT_B=18102

stop_instances() {
  pkill -f "app.py serve --port 181" 2>/dev/null || true
  sleep 0.5
  pkill -9 -f "app.py serve --port 181" 2>/dev/null || true
}

reset_runtime() {
  stop_instances
  for d in "$ROOT"/*/; do
    [ -d "$d/runtime" ] && rm -rf "$d/runtime"
  done
  return 0
}

promote_product() {
  local base="$1" draft="$2" out="$3" review
  review=$(cd "$REPO" && uv run workflow/to-spec/ac-draft.py preview "$base" "$draft" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["review_id"])')
  (cd "$REPO" && uv run workflow/to-spec/ac-draft.py promote "$base" "$draft" "$out" --review "$review" >/dev/null)
  (cd "$REPO" && uv run workflow/to-spec/check-ac.py "$out" >/dev/null)
}

write_products() {
  mkdir -p "$BUILD"

  cat > "$BUILD/PRODUCT.parallel.base.md" <<'EOF'
# 记录板 Product Spec

## 背景

值班同学需要一个小的记录板: 可以同时开多个实例, 每个实例有自己的数据目录, 所有实例共用一条记录与一份事件日志.

## 目标

- G-001: 每个实例能显示自身状态页.
- G-002: 每个实例能执行一次耗时任务并回报结果.
- G-003: 实例能向同一条共享记录追加条目.
- G-004: 共享事件日志可按只读方式查看.
- G-005: 状态页与 report 输出给出同一实例, 同一版本, 同一状态.

## 非目标

- NG-001: 不做鉴权与多用户管理. (理由: 只在本地临时实例上使用.)

## 业务规则

- BR-001: 共享记录的序号从 1 开始连续递增且不重复, 每个 value 只出现一次. (审计)
- BR-002: 共享事件日志只增不改, 只读查看前后文件内容不变. (审计)

## 验收标准

## 决策引用

- 无.
EOF

  cat > "$BUILD/PRODUCT.reverify.base.md" <<'EOF'
# 记录板 Product Spec

## 背景

值班同学需要一个小记录板: 每个实例有自己的数据目录, 提供状态页, 耗时任务, report 输出与只读事件日志.

## 目标

- G-001: 实例能显示自身状态页.
- G-002: 实例能执行一次耗时任务并回报结果.
- G-003: 实例能输出 report, 其中的状态反映实例当前状态.
- G-004: 共享事件日志可按只读方式查看.

## 非目标

- NG-001: 不做鉴权与多用户管理. (理由: 只在本地临时实例上使用.)

## 业务规则

- BR-001: 本次变更不新增第三方依赖, `deps.txt` 与上一提交逐项一致. (审计)

## 验收标准

## 决策引用

- 无.
EOF

  cat > "$BUILD/draft.parallel.md" <<'EOF'
```gherkin
# language: zh-CN
功能: 记录板

@AC-001 @normal @G-001
场景: AC-001-1 alpha 状态页与 report
  假定 实例 alpha 正在 127.0.0.1:18101 运行且 health 返回 `ok instance=alpha`
  当 验收者核对 alpha 状态页截图与 `python3 app.py report --port 18101` 的输出
  那么 截图显示 `instance=alpha`, `state=ready` 与 `version=relay-v1`
  而且 report 输出为 `relay-report instance=alpha version=relay-v1 state=ready`

@AC-001 @normal @G-001
场景: AC-001-2 beta 实例状态页
  假定 实例 beta 正在 127.0.0.1:18102 运行且 health 返回 `ok instance=beta`
  当 验收者运行 `python3 app.py status --port 18102`
  那么 输出含 `instance=beta`, `state=ready` 与 `version=relay-v1` 且退出码为 0

@AC-002 @normal @G-002
场景: AC-002-1 alpha 耗时任务
  假定 实例 alpha 正在 127.0.0.1:18101 运行
  当 验收者运行 `python3 app.py job --port 18101 --ms 4000`
  那么 输出为 `job-done instance=alpha elapsed_ms=4000` 且退出码为 0
  而且 命令实际耗时不少于 4 秒

@AC-002 @normal @G-002
场景: AC-002-2 beta 耗时任务
  假定 实例 beta 正在 127.0.0.1:18102 运行
  当 验收者运行 `python3 app.py job --port 18102 --ms 4000`
  那么 输出为 `job-done instance=beta elapsed_ms=4000` 且退出码为 0
  而且 命令实际耗时不少于 4 秒

@AC-003 @normal @G-003
场景: AC-003-1 追加 alpha 条目
  假定 实例 alpha 正在 127.0.0.1:18101 运行且共享记录 `runtime/shared/record.jsonl` 尚不存在
  当 验收者运行 `python3 app.py append --port 18101 --value alpha`
  那么 输出形如 `seq=<n> value=alpha` 且退出码为 0
  而且 记录中 `value=alpha` 的条目恰好一条

@AC-003 @normal @G-003
场景: AC-003-2 追加 beta 条目
  假定 实例 beta 正在 127.0.0.1:18102 运行且共享记录 `runtime/shared/record.jsonl` 已有 alpha 条目
  当 验收者运行 `python3 app.py append --port 18102 --value beta`
  那么 输出形如 `seq=<n> value=beta` 且退出码为 0
  而且 记录中 `value=beta` 的条目恰好一条

@AC-004 @normal @G-004
场景: AC-004-1 只读查看事件日志
  假定 实例 alpha 正在 127.0.0.1:18101 运行且其耗时任务正在执行
  当 验收者运行 `python3 app.py log --port 18101`
  那么 输出含 `instance=alpha` 与 `event=job-start` 且退出码为 0

@AC-005 @normal @G-005
场景: AC-005-1 两个实例的状态材料互相一致
  假定 实例 alpha 与 beta 都在运行, 两侧的状态页截图与 report 输出已由各自负责人产出
  当 验收者核对两侧截图与 report 输出
  那么 每一侧的 instance 与 version 在截图和 report 中相同
  而且 两侧 report 输出都含 `state=ready`
```
EOF

  cat > "$BUILD/draft.reverify.md" <<'EOF'
```gherkin
# language: zh-CN
功能: 记录板

@AC-001 @normal @G-001
场景: AC-001-1 状态页截图
  假定 实例 alpha 正在 127.0.0.1:18101 运行且 health 返回 `ok instance=alpha`
  当 验收者用浏览器渲染 `http://127.0.0.1:18101/status-page` 并截图
  那么 截图显示 `instance=alpha`, `state=ready` 与 `version=relay-v1`

@AC-002 @normal @G-002
场景: AC-002-1 耗时任务
  假定 实例 alpha 正在 127.0.0.1:18101 运行
  当 验收者运行 `python3 app.py job --port 18101 --ms 2500`
  那么 输出为 `job-done instance=alpha elapsed_ms=2500` 且退出码为 0

@AC-003 @normal @G-003
场景: AC-003-1 report 状态
  假定 实例 alpha 正在 127.0.0.1:18101 运行且 health 返回 `ok instance=alpha`
  当 验收者运行 `python3 app.py report --port 18101`
  那么 输出为 `relay-report instance=alpha version=relay-v1 state=ready` 且退出码为 0

@AC-004 @normal @G-004
场景: AC-004-1 只读查看事件日志
  假定 实例 alpha 正在 127.0.0.1:18101 运行且其耗时任务已经执行
  当 验收者运行 `python3 app.py log --port 18101`
  那么 输出含 `instance=alpha` 与 `event=job-end` 且退出码为 0
```
EOF
}

write_app_scaffold() {
  cat > "$1" <<'PYEOF'
#!/usr/bin/env python3
"""记录板: 多实例状态页, 耗时任务与只读事件日志."""
import argparse
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

VERSION = "relay-v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class Board:
    def __init__(self, instance: str, data_dir: str, shared_dir: str) -> None:
        self.instance = instance
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.shared_dir = Path(shared_dir)
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.shared_dir / "events.log"
        self.state = "ready"

    def log_event(self, kind: str, detail: str = "") -> None:
        line = f"{now_iso()} instance={self.instance} event={kind} {detail}".rstrip()
        with self.events_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def status_page(self) -> str:
        return (
            "<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\"><title>relay board</title></head>\n"
            "<body><h1>relay board</h1>\n"
            f"<p>instance={self.instance}</p>\n<p>state={self.state}</p>\n"
            f"<p>version={VERSION}</p></body></html>\n"
        )

    def events(self) -> str:
        if not self.events_path.exists():
            return ""
        return self.events_path.read_text(encoding="utf-8")


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
            if parsed.path == "/job":
                ms = int(query.get("ms", ["1000"])[0])
                board.log_event("job-start", f"ms={ms}")
                time.sleep(ms / 1000.0)
                board.log_event("job-end", f"ms={ms}")
                self._text(f"job-done instance={board.instance} elapsed_ms={ms}\n")
                return
            if parsed.path == "/log":
                self._text(board.events())
                return
            self._text("not found\n", status=404)

    return Handler


def client_get(port: int, path: str) -> int:
    import urllib.request

    url = f"http://127.0.0.1:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            status = resp.status
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
    serve.add_argument("--shared-dir", required=True)

    for name in ("status", "health", "log"):
        sub = commands.add_parser(name)
        sub.add_argument("--port", type=int, required=True)

    job = commands.add_parser("job")
    job.add_argument("--port", type=int, required=True)
    job.add_argument("--ms", type=int, default=1000)

    args = parser.parse_args(argv)

    if args.command == "serve":
        board = Board(args.instance, args.data_dir, args.shared_dir)
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_factory(board))
        print(f"listening on 127.0.0.1:{args.port} instance={board.instance}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        return 0
    if args.command == "status":
        return client_get(args.port, "/status-page")
    if args.command == "health":
        return client_get(args.port, "/health")
    if args.command == "log":
        return client_get(args.port, "/log")
    if args.command == "job":
        return client_get(args.port, f"/job?ms={args.ms}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
PYEOF
}

# full: scaffold 加上 append/record/report; report 状态取实例真实状态.
write_app_full() {
  local out="$1"
  python3 - "$out" <<'PYEOF'
import sys
from pathlib import Path

out = Path(sys.argv[1])
src = Path("/tmp/orchestra-04/build/app_scaffold.py").read_text(encoding="utf-8")

src = src.replace(
    '''        self.events_path = self.shared_dir / "events.log"
        self.state = "ready"''',
    '''        self.events_path = self.shared_dir / "events.log"
        self.record_path = self.shared_dir / "record.jsonl"
        self.state = "ready"''',
)

src = src.replace(
    '''    def events(self) -> str:''',
    '''    def append_record(self, value: str) -> int:
        lines = []
        if self.record_path.exists():
            lines = [line for line in self.record_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        seq = len(lines) + 1
        # 写入窗口: 记录由多个实例共用, 同一时刻只允许一个写入者.
        time.sleep(1.2)
        entry = {"seq": seq, "value": value, "instance": self.instance, "ts": now_iso()}
        with self.record_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\\n")
        self.log_event("append", f"seq={seq} value={value}")
        return seq

    def record(self) -> str:
        if not self.record_path.exists():
            return ""
        return self.record_path.read_text(encoding="utf-8")

    def report(self) -> str:
        return report_line(self.instance, self.state)

    def events(self) -> str:''',
)

src = src.replace(
    '''def handler_factory(board: Board):''',
    '''def report_line(instance: str, state: str) -> str:
    return f"relay-report instance={instance} version={VERSION} state={state}"


def handler_factory(board: Board):''',
)

src = src.replace(
    '''            if parsed.path == "/log":
                self._text(board.events())
                return''',
    '''            if parsed.path == "/log":
                self._text(board.events())
                return
            if parsed.path == "/record":
                self._text(board.record())
                return
            if parsed.path == "/report":
                self._text(board.report() + "\\n")
                return
            if parsed.path == "/append":
                value = query.get("value", [""])[0]
                if not value:
                    self._text("missing value\\n", status=400)
                    return
                seq = board.append_record(value)
                self._text(f"seq={seq} value={value}\\n")
                return''',
)

src = src.replace(
    '''import argparse
import sys''',
    '''import argparse
import json
import sys''',
)

src = src.replace(
    '''    for name in ("status", "health", "log"):''',
    '''    for name in ("status", "health", "log", "record", "report"):''',
)

src = src.replace(
    '''    job = commands.add_parser("job")''',
    '''    append = commands.add_parser("append")
    append.add_argument("--port", type=int, required=True)
    append.add_argument("--value", required=True)

    job = commands.add_parser("job")''',
)

src = src.replace(
    '''    if args.command == "job":
        return client_get(args.port, f"/job?ms={args.ms}")''',
    '''    if args.command == "record":
        return client_get(args.port, "/record")
    if args.command == "report":
        return client_get(args.port, "/report")
    if args.command == "append":
        return client_get(args.port, f"/append?value={args.value}")
    if args.command == "job":
        return client_get(args.port, f"/job?ms={args.ms}")''',
)

out.write_text(src, encoding="utf-8")
PYEOF
}

# defect: full 版, 但 report 的状态写死成 loading (本次变更引入的真实缺陷).
write_app_defect() {
  local out="$1"
  write_app_full "$out"
  python3 - "$out" <<'PYEOF'
import sys
from pathlib import Path

path = Path(sys.argv[1])
src = path.read_text(encoding="utf-8")
old = "        return report_line(self.instance, self.state)"
new = '        return report_line(self.instance, "loading")'
assert old in src, "缺陷注入点未找到"
path.write_text(src.replace(old, new), encoding="utf-8")
PYEOF
}

write_tests() {
  local dir="$1"
  mkdir -p "$dir/tests"
  cat > "$dir/tests/test_app.py" <<'EOF'
from pathlib import Path

import app


def test_status_page_mentions_instance_and_version(tmp_path):
    board = app.Board("alpha", str(tmp_path / "data"), str(tmp_path / "shared"))
    page = board.status_page()
    assert "instance=alpha" in page
    assert f"version={app.VERSION}" in page
    assert "state=ready" in page


def test_log_event_appends_only(tmp_path):
    board = app.Board("alpha", str(tmp_path / "data"), str(tmp_path / "shared"))
    board.log_event("job-start", "ms=1")
    first = Path(board.events_path).read_text(encoding="utf-8")
    board.log_event("job-end", "ms=1")
    second = Path(board.events_path).read_text(encoding="utf-8")
    assert second.startswith(first)
    assert "event=job-end" in second
EOF
}

write_readme() {
  local dir="$1" kind="$2"
  if [ "$kind" = "parallel" ]; then
    cat > "$dir/README.md" <<'EOF'
# 记录板

两个实例共用一个共享目录: 状态页与耗时任务各走自己的端口, 共享记录与事件日志放在 `runtime/shared/`.

## 启动实例

```bash
mkdir -p runtime/alpha runtime/beta runtime/shared
python3 app.py serve --port 18101 --instance alpha --data-dir runtime/alpha --shared-dir runtime/shared &
python3 app.py serve --port 18102 --instance beta --data-dir runtime/beta --shared-dir runtime/shared &
python3 app.py health --port 18101
python3 app.py health --port 18102
```

## 命令

- `python3 app.py status --port 18101`: 打印状态页 HTML.
- `python3 app.py job --port 18101 --ms 4000`: 执行一次耗时任务.
- `python3 app.py append --port 18101 --value alpha`: 向共享记录追加一条.
- `python3 app.py record --port 18101`: 打印共享记录全文.
- `python3 app.py log --port 18101`: 只读打印事件日志.
- `python3 app.py report --port 18101`: 打印 report 单行.

## 状态页截图

```bash
google-chrome --headless --disable-gpu --no-sandbox --window-size=900,400 \
  --screenshot=runtime/alpha-status.png http://127.0.0.1:18101/status-page
```

## 测试

`uv run --no-project --with pytest python -m pytest -q`

`runtime/` 与 `.agents/` 在 `.gitignore` 里.
EOF
  else
    cat > "$dir/README.md" <<'EOF'
# 记录板

单实例: 状态页, 耗时任务, report 输出与只读事件日志共用 `runtime/`.

## 启动实例

```bash
mkdir -p runtime/alpha
python3 app.py serve --port 18101 --instance alpha --data-dir runtime/alpha --shared-dir runtime/shared &
python3 app.py health --port 18101
```

## 命令

- `python3 app.py status --port 18101`: 打印状态页 HTML.
- `python3 app.py job --port 18101 --ms 2500`: 执行一次耗时任务.
- `python3 app.py report --port 18101`: 打印 report 单行.
- `python3 app.py log --port 18101`: 只读打印事件日志.

## 状态页截图

```bash
google-chrome --headless --disable-gpu --no-sandbox --window-size=900,400 \
  --screenshot=runtime/alpha-status.png http://127.0.0.1:18101/status-page
```

## 测试

`uv run --no-project --with pytest python -m pytest -q`

`runtime/` 与 `.agents/` 在 `.gitignore` 里.
EOF
  fi
}

make_project() {
  local dir="$1" kind="$2" variant="$3" product="$4"
  rm -rf "$dir"
  mkdir -p "$dir/docs/changes/relay-board" "$dir/tests"
  printf '.agents/\nruntime/\n__pycache__/\n.pytest_cache/\n' > "$dir/.gitignore"
  printf 'python3 标准库, 无第三方依赖\n' > "$dir/deps.txt"
  write_readme "$dir" "$kind"
  write_tests "$dir"
  write_app_scaffold "$dir/app.py"
  cp "$BUILD/PRODUCT.$product.base.md" "$BUILD/_base.tmp.md"
  cp "$BUILD/draft.$product.md" "$BUILD/_draft.tmp.md"
  promote_product "$BUILD/_base.tmp.md" "$BUILD/_draft.tmp.md" "$dir/docs/changes/relay-board/PRODUCT.md"
  rm -f "$BUILD/_base.tmp.md" "$BUILD/_draft.tmp.md"

  (
    cd "$dir"
    git init -q -b main
    git add -A
    git commit -q -m "初始化记录板骨架与产品标准"
    case "$variant" in
      full) write_app_full app.py ;;
      defect) write_app_defect app.py ;;
      *) echo "未知变体: $variant" >&2; exit 2 ;;
    esac
    git add -A
    if [ "$variant" = "defect" ]; then
      git commit -q -m "feat: 增加共享记录与 report 子命令"
    else
      git commit -q -m "feat: 增加共享记录追加与 report 子命令"
    fi
  )
}

do_init() {
  stop_instances
  rm -rf "$ROOT"
  mkdir -p "$BUILD"
  write_products
  write_app_scaffold "$BUILD/app_scaffold.py"
  make_project "$ROOT/parallel" parallel full parallel
  make_project "$ROOT/reverify" single defect reverify
  git clone -q "$ROOT/parallel" "$ROOT/red-parallel"
  git clone -q "$ROOT/reverify" "$ROOT/red-reverify"
  mkdir -p "$ROOT/author-materials"
  echo "init 完成: $ROOT/parallel $ROOT/reverify $ROOT/red-parallel $ROOT/red-reverify"
}

install_skill() {
  local project="$1" skilldir="$2"
  mkdir -p "$project/.agents/skills"
  rm -rf "$project/.agents/skills/verify-change"
  cp -a "$skilldir" "$project/.agents/skills/verify-change"
  echo "已安装: $project/.agents/skills/verify-change"
}

do_status() {
  for d in "$ROOT"/*/; do
    [ -d "$d/.git" ] || continue
    echo "== $d"
    git -C "$d" log --oneline | sed 's/^/  /'
    git -C "$d" status --short | sed 's/^/  /'
  done
}

do_rebuild_parallel() {
  stop_instances
  mkdir -p "$BUILD"
  write_products
  write_app_scaffold "$BUILD/app_scaffold.py"
  make_project "$ROOT/parallel" parallel full parallel
  rm -rf "$ROOT/red-parallel"
  git clone -q "$ROOT/parallel" "$ROOT/red-parallel"
  echo "rebuild-parallel 完成: $ROOT/parallel $ROOT/red-parallel"
}

main() {
  case "$MODE" in
    init) do_init ;;
    rebuild-parallel) do_rebuild_parallel ;;
    install-skill) install_skill "${2:?项目路径}" "${3:?技能目录}" ;;
    status) do_status ;;
    reset-runtime) reset_runtime ;;
    *) echo "未知模式: $MODE" >&2; exit 2 ;;
  esac
}

main "$@"
