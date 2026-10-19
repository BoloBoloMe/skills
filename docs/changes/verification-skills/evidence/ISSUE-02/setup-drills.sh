#!/usr/bin/env bash
# ISSUE-02 演练夹具准备. 只在 /tmp/orchestra-02 下建临时 Git 项目, 不碰仓库与其他目录.
# 用法: bash setup-drills.sh <仓库工作树根目录>
set -euo pipefail

REPO=${1:?需要仓库工作树根目录}
ROOT=/tmp/orchestra-02
BUILD="$ROOT/build"
BASE="$BUILD/base-project"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

reset_fixtures() {
  rm -rf "$ROOT"/red-coverage "$ROOT"/red-evidence "$ROOT"/green-coverage \
    "$ROOT"/green-evidence "$ROOT"/green-summary "$ROOT"/green-conflict "$BUILD"
  mkdir -p "$BUILD"
}

# 用 to-spec 的真实转正流程生成带确认标记的 PRODUCT.md, 不手写假标记.
promote_product() {
  local base="$1" draft="$2" out="$3"
  local review
  review=$(cd "$REPO" && uv run workflow/to-spec/ac-draft.py preview "$base" "$draft" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["review_id"])')
  (cd "$REPO" && uv run workflow/to-spec/ac-draft.py promote "$base" "$draft" "$out" --review "$review" >/dev/null)
  (cd "$REPO" && uv run workflow/to-spec/check-ac.py "$out" >/dev/null)
}

write_product_inputs() {
  cat > "$BUILD/PRODUCT.base.md" <<'EOF'
# 值班工具集 Product Spec

## 背景

值班同学需要一个小命令行工具集, 覆盖问候生成, 文本统计, 报告导出和远程健康检查. 本次变更只调整问候的全大写输出.

## 目标

- G-001: 值班同学能按姓名生成问候, 切换全大写与自定义分隔符.
- G-002: 值班同学能统计文本文件的词数与字符数.
- G-003: 值班同学能把问候导出为 JSON 报告.
- G-004: 值班同学能通过健康检查确认依赖的远程服务就绪.

## 非目标

- NG-001: 不做多语言. (理由: 当前只有中文团队使用.)

## 业务规则

- BR-001: 问候语以 `Hello` 开头, 后接分隔符与姓名, 以 `!` 结尾; 全大写模式下问候语整体转为大写.
- BR-002: 本变更不新增第三方依赖, 依赖清单, 锁文件和构建材料与上一提交逐项一致. (审计)
- BR-003: 本变更不修改既有测试文件. (审计)
- BR-004: 验收期间的写入只发生在批准范围, 并在结束时清理临时资源. (审计)

## 验收标准

## 决策引用

- 无.
EOF

  cat > "$BUILD/验收草稿.md" <<'EOF'
```gherkin
# language: zh-CN
功能: 值班工具集

@AC-001 @normal @G-001 @BR-001
场景: AC-001-1 默认问候
  假定 值班同学已取得 tool.py
  当 值班同学运行 `python3 tool.py greet --name Ada`
  那么 标准输出为 `Hello, Ada!` 且退出码为 0

@AC-001 @edge @G-001 @BR-001
场景: AC-001-2 全大写问候
  假定 值班同学已取得 tool.py
  当 值班同学运行 `python3 tool.py greet --name Ada --shout`
  那么 标准输出为 `HELLO, ADA!` 且退出码为 0

@AC-001 @edge @G-001 @BR-001
场景: AC-001-3 自定义分隔符
  假定 值班同学已取得 tool.py
  当 值班同学运行 `python3 tool.py greet --name Ada --sep '; '`
  那么 标准输出为 `Hello; Ada!` 且退出码为 0

@AC-001 @failure @G-001 @BR-001
场景: AC-001-4 缺少姓名时报参数错误
  假定 值班同学已取得 tool.py
  当 值班同学运行 `python3 tool.py greet`
  那么 退出码非 0 且标准错误包含 `--name`

@AC-002 @normal @G-002
场景: AC-002-1 统计词数
  假定 值班同学已有文本文件 notes.txt, 内容为 `alpha beta gamma` 加一个换行
  当 值班同学运行 `python3 tool.py count --file notes.txt`
  那么 标准输出为 `3` 且退出码为 0

@AC-002 @edge @G-002
场景: AC-002-2 统计字符数
  假定 值班同学已有文本文件 notes.txt, 内容为 `alpha beta gamma` 加一个换行
  当 值班同学运行 `python3 tool.py count --file notes.txt --chars`
  那么 标准输出为 `17` 且退出码为 0

@AC-002 @edge @G-002
场景: AC-002-3 空文件词数为零
  假定 值班同学已有空文件 empty.txt
  当 值班同学运行 `python3 tool.py count --file empty.txt`
  那么 标准输出为 `0` 且退出码为 0

@AC-002 @failure @G-002
场景: AC-002-4 文件不存在时报错退出
  假定 值班同学没有名为 missing.txt 的文件
  当 值班同学运行 `python3 tool.py count --file missing.txt`
  那么 退出码为 1 且标准错误包含 `missing.txt`

@AC-003 @normal @G-003
场景: AC-003-1 默认 JSON 导出
  假定 值班同学已取得 tool.py
  当 值班同学运行 `python3 tool.py export --name Ada`
  那么 标准输出为 `{"name": "Ada", "greeting": "Hello, Ada!"}` 且退出码为 0

@AC-003 @edge @G-003
场景: AC-003-2 缩进导出
  假定 值班同学已取得 tool.py
  当 值班同学运行 `python3 tool.py export --name Ada --pretty`
  那么 标准输出第一行为 `{`, 第二行为两个空格缩进的 `"name": "Ada",` 且退出码为 0

@AC-003 @failure @G-003
场景: AC-003-3 未知格式报错退出
  假定 值班同学已取得 tool.py
  当 值班同学运行 `python3 tool.py export --name Ada --format yaml`
  那么 退出码为 1 且标准错误包含 `unsupported format: yaml`

@AC-004 @normal @G-004
场景: AC-004-1 远程服务就绪检查
  假定 值班同学已取得健康服务地址与访问凭据
  当 值班同学运行 `python3 tool.py health --url http://127.0.0.1:18080/health`
  那么 标准输出包含 `"ready": true` 且退出码为 0
```
EOF
}

write_commit1_files() {
  local dir="$1"
  mkdir -p "$dir/docs/changes/tool-cli" "$dir/tests"
  printf '.agents/\nmaterials/\n__pycache__/\n.pytest_cache/\n' > "$dir/.gitignore"

  cat > "$dir/tool.py" <<'EOF'
#!/usr/bin/env python3
"""值班工具集: 问候, 统计, 导出与远程健康检查."""
import argparse
import json
from pathlib import Path
import sys


def greet(name: str, separator: str = ", ") -> str:
    return f"Hello{separator}{name}!"


def count(text: str, chars: bool) -> int:
    return len(text) if chars else len(text.split())


def export_payload(name: str, pretty: bool) -> str:
    payload = {"name": name, "greeting": greet(name)}
    return json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None)


def health(url: str) -> int:
    from urllib.request import urlopen

    with urlopen(url, timeout=5) as response:
        body = response.read().decode("utf-8")
        status = response.status
    print(body)
    try:
        ready = json.loads(body).get("ready") is True
    except ValueError:
        ready = False
    return 0 if status == 200 and ready else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="tool.py")
    commands = parser.add_subparsers(dest="command", required=True)

    greet_parser = commands.add_parser("greet")
    greet_parser.add_argument("--name", required=True)
    greet_parser.add_argument("--sep", default=", ")

    count_parser = commands.add_parser("count")
    count_parser.add_argument("--file", required=True)
    count_parser.add_argument("--chars", action="store_true")

    export_parser = commands.add_parser("export")
    export_parser.add_argument("--name", required=True)
    export_parser.add_argument("--format", default="json")
    export_parser.add_argument("--pretty", action="store_true")

    health_parser = commands.add_parser("health")
    health_parser.add_argument("--url", required=True)

    args = parser.parse_args(argv)

    if args.command == "greet":
        print(greet(args.name, args.sep))
        return 0
    if args.command == "count":
        try:
            text = Path(args.file).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"cannot read {args.file}: {exc}", file=sys.stderr)
            return 1
        print(count(text, args.chars))
        return 0
    if args.command == "export":
        if args.format != "json":
            print(f"unsupported format: {args.format}", file=sys.stderr)
            return 1
        print(export_payload(args.name, args.pretty))
        return 0
    if args.command == "health":
        return health(args.url)
    return 2


if __name__ == "__main__":
    sys.exit(main())
EOF

  printf 'alpha beta gamma\n' > "$dir/notes.txt"
  : > "$dir/empty.txt"

  cat > "$dir/deps.txt" <<'EOF'
python-stdlib
EOF

  cat > "$dir/deps.lock" <<'EOF'
# 本工具只用 Python 标准库, 无第三方依赖.
EOF

  cat > "$dir/build.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q tool.py
EOF

  cat > "$dir/tests/test_tool.py" <<'EOF'
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(*args):
    return subprocess.run(
        [sys.executable, str(ROOT / "tool.py"), *args], capture_output=True, text=True
    )


def test_default_greeting():
    result = run("greet", "--name", "Ada")
    assert result.stdout == "Hello, Ada!\n"
    assert result.returncode == 0


def test_word_count():
    result = run("count", "--file", str(ROOT / "notes.txt"))
    assert result.stdout == "3\n"
    assert result.returncode == 0
EOF

  cat > "$dir/README.md" <<'EOF'
# tool-cli

值班工具集, 含问候, 统计, 导出与远程健康检查.

## 运行

- 问候: `python3 tool.py greet --name Ada`
- 统计: `python3 tool.py count --file notes.txt`
- 导出: `python3 tool.py export --name Ada`
- 健康检查: `python3 tool.py health --url http://127.0.0.1:18080/health`

## 本次变更

- 只改问候的全大写输出, 其余入口不变.

## 检查

- `python3 -m pytest -q`
- `bash build.sh`
EOF

  cat > "$dir/docs/changes/tool-cli/TECHNICAL.md" <<'EOF'
# 值班工具集 Technical Spec

## 模块接口

- 入口 `python3 tool.py <子命令>`, 子命令为 greet, count, export, health.

## 测试接缝

- 直接运行 CLI 并观察标准输出, 标准错误与退出码.

## 验证入口

- `python3 -m pytest -q`
- `bash build.sh`
EOF

  promote_product "$BUILD/PRODUCT.base.md" "$BUILD/验收草稿.md" "$dir/docs/changes/tool-cli/PRODUCT.md"
}

commit_all() {
  local dir="$1" msg="$2"
  (cd "$dir" && git init -q -b main && git add -A && git \
    -c user.name=drill -c user.email=drill@example.com commit -qm "$msg")
}

apply_change() {
  local dir="$1"
  python3 - "$dir/tool.py" <<'EOF'
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = text.replace(
    'def greet(name: str, separator: str = ", ") -> str:\n    return f"Hello{separator}{name}!"',
    'def greet(name: str, separator: str = ", ", shout: bool = False) -> str:\n'
    '    text = f"Hello{separator}{name}!"\n'
    '    return text.upper() if shout else text',
)
text = text.replace(
    '    greet_parser.add_argument("--sep", default=", ")',
    '    greet_parser.add_argument("--sep", default=", ")\n'
    '    greet_parser.add_argument("--shout", action="store_true")',
)
text = text.replace(
    '        print(greet(args.name, args.sep))',
    '        print(greet(args.name, args.sep, args.shout))',
)
path.write_text(text, encoding="utf-8")
EOF
}

capture_old_observation() {
  local dir="$1"
  local commit1
  commit1=$(cd "$dir" && git rev-parse HEAD)
  local out rc
  set +e
  out=$(cd "$dir" && python3 tool.py count --file notes.txt)
  rc=$?
  set -e
  mkdir -p "$BUILD/old-observation"
  cat > "$BUILD/old-observation/transcript.log" <<EOF
# 上一轮验收的原生命令记录
$ python3 tool.py count --file notes.txt
$out
[exit $rc]
EOF
  cat > "$BUILD/old-observation/README.md" <<EOF
# 旧观察材料

标准: AC-002-1 统计词数

性质: 上一轮验收的实跑观察, 不是本轮实跑. 原件是同目录的 \`transcript.log\`.

- 检查时间: $TS
- 提交版本: $commit1
- 命令: \`python3 tool.py count --file notes.txt\`
- 原始输出: \`$out\`
- 退出码: $rc
- 可复核位置: 提交 $commit1 的 tool.py 与 notes.txt, 原件 \`transcript.log\`.
- 适用条件: 本次变更只改 greet 的 --shout, count 与 notes.txt 未变; 该场景不是本次受影响的关键真实路径.
EOF
}

capture_health_record() {
  local commit2="$1"
  cat > "$BUILD/mock_health.py" <<'EOF'
from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"status": "starting", "ready": False}).encode()
        self.send_response(500)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


HTTPServer(("127.0.0.1", 18080), Handler).serve_forever()
EOF
  python3 "$BUILD/mock_health.py" &
  local mock=$!
  sleep 0.6
  local out rc
  set +e
  out=$(curl -s -w '\nHTTP %{http_code}' http://127.0.0.1:18080/health)
  rc=$?
  set -e
  kill "$mock" 2>/dev/null || true
  wait "$mock" 2>/dev/null || true
  cat > "$BUILD/health-raw.log" <<EOF
# AC-004-1 原生工具记录

这是实际验收者会话在同一目标版本, 同一请求上留下的可读工具记录.

- 目标提交: $commit2
- 执行时间: $TS
- 命令: \`curl -s -w '\\nHTTP %{http_code}' http://127.0.0.1:18080/health\`
- 原始输出:
\`\`\`
$out
\`\`\`
- curl 退出码: $rc
EOF
}

write_materials() {
  local dir="$1" kind="$2" commit2="$3"
  case "$kind" in
    none) return ;;
    evidence)
      mkdir -p "$dir/materials/old-observation"
      cp "$BUILD/old-observation/README.md" "$BUILD/old-observation/transcript.log" "$dir/materials/old-observation/"
      cat > "$dir/materials/inference-note.md" <<EOF
# 推断材料

标准: AC-003-2 缩进导出

性质: 只读代码得出, 未运行.

- 目标提交: $commit2
- 代码位置: \`tool.py\` 的 \`export_payload\`, 对 \`json.dumps\` 传 \`indent=2 if pretty else None\`.
- 推理依据: 传入 \`--pretty\` 时 \`indent=2\`, 因此输出应为带两空格缩进的多行 JSON.
- 备注: 没有对应的运行输出或截图.
EOF
      cat > "$dir/materials/unavailable.md" <<EOF
# 不可运行项说明

标准: AC-004-1 远程服务就绪检查

- 目标提交: $commit2
- 缺少的条件: 健康服务 \`http://127.0.0.1:18080/health\` 在本轮验收期间未运行, 值班同学也没有取得该服务的访问凭据.
- 影响: 该场景在本轮无法执行, 也没有旧观察或运行记录可用.
EOF
      ;;
    conflict)
      mkdir -p "$dir/materials"
      cp "$BUILD/health-raw.log" "$dir/materials/health-raw.log"
      cat > "$dir/materials/delegated-summary.md" <<EOF
# 委托摘要

实际验收者转交的本轮结果摘要.

- 目标提交: $commit2
- 结论: 12 个验收场景全部通过, 3 条审计规则全部成立.
- AC-004-1: 对 \`http://127.0.0.1:18080/health\` 的请求返回 HTTP 200, 响应含 \`"ready": true\`, 通过.
- 原始材料: 未附.
EOF
      ;;
    summary)
      mkdir -p "$dir/materials"
      cat > "$dir/materials/delegated-summary.md" <<EOF
# 委托摘要

实际验收者转交的本轮结果摘要.

- 目标提交: $commit2
- 结论: 12 个验收场景全部通过, 3 条审计规则全部成立.
- 说明: 逐项命令与输出已由实际验收者跑过, 结果如上; 原始材料未随摘要附上.
EOF
      ;;
    *) echo "未知材料类型: $kind" >&2; exit 2 ;;
  esac
}

main() {
  reset_fixtures
  write_product_inputs

  write_commit1_files "$BASE"
  commit_all "$BASE" "初始化值班工具集与产品标准"
  capture_old_observation "$BASE"

  apply_change "$BASE"
  (cd "$BASE" && git add -A && git -c user.name=drill -c user.email=drill@example.com commit -qm "支持问候的全大写输出")
  local commit1 commit2
  commit1=$(cd "$BASE" && git rev-parse HEAD~1)
  commit2=$(cd "$BASE" && git rev-parse HEAD)
  capture_health_record "$commit2"

  local pair
  for pair in "red-coverage:none" "red-evidence:conflict" \
    "green-coverage:none" "green-evidence:evidence" \
    "green-summary:summary" "green-conflict:conflict"; do
    local name="${pair%%:*}" kind="${pair##*:}"
    cp -a "$BASE" "$ROOT/$name"
    write_materials "$ROOT/$name" "$kind" "$commit2"
  done

  {
    echo "PRODUCT 确认标记: $(grep -c 'confirmed-flow' "$BASE/docs/changes/tool-cli/PRODUCT.md")"
    echo "起始提交 1: $commit1"
    echo "目标提交 2: $commit2"
    for name in red-coverage red-evidence green-coverage green-evidence green-summary green-conflict; do
      printf '%s %s %s\n' "$name" "$(cd "$ROOT/$name" && git rev-parse HEAD)" \
        "$(cd "$ROOT/$name" && git status --porcelain | wc -l)"
    done
  } | tee "$BUILD/fixtures.txt"
}

main
