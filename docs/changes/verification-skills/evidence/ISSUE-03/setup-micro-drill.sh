#!/usr/bin/env bash
# ISSUE-03 微检查组夹具 (v2): 3 个微小只读检查, 全部读同一份构建产物 dist/app.txt,
# 该产物由约 25 秒的 bash prepare.sh 生成, 且 dist/ 不进仓库, 每个新会话都要重跑.
# 产品标准只有这 3 个场景, 没有审计 BR, 用于 AC-005-3 的单一决策依据.
# 用法: bash setup-micro-drill.sh <仓库工作树根目录> <实现提交>
set -euo pipefail

REPO=${1:?需要仓库工作树根目录}
CHANGE=${2:?需要真实实现会话的提交}
ROOT=/tmp/orchestra-03/micro2
BUILD="$ROOT/build"
AUTHOR=/tmp/orchestra-03/author

promote_product() {
  local base="$1" draft="$2" out="$3" review
  review=$(cd "$REPO" && uv run workflow/to-spec/ac-draft.py preview "$base" "$draft" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["review_id"])')
  (cd "$REPO" && uv run workflow/to-spec/ac-draft.py promote "$base" "$draft" "$out" --review "$review" >/dev/null)
  (cd "$REPO" && uv run workflow/to-spec/check-ac.py "$out" >/dev/null)
}

mkdir -p "$BUILD"
cat > "$BUILD/PRODUCT.base.md" <<'EOF'
# 工具集 Product Spec

## 背景

值班同学需要一个小的命令行工具集, 覆盖问候生成, 文本统计与报告导出. 本次变更只给问候增加全大写开关.

## 目标

- G-001: 值班同学能按姓名生成问候, 并可切换全大写输出.
- G-002: 值班同学能统计文本文件的词数与字符数.
- G-003: 值班同学能把问候导出为 JSON 报告.

## 非目标

- NG-001: 不做多语言. (理由: 当前只有中文团队使用.)

## 业务规则

- BR-001: 问候语以 `Hello` 开头, 后接分隔符与姓名, 以 `!` 结尾; 全大写模式下整体转为大写.

## 验收标准

## 决策引用

- 无.
EOF

cat > "$BUILD/draft-micro2.md" <<'EOF'
```gherkin
# language: zh-CN
功能: 工具集

@AC-001 @normal @G-001 @BR-001
场景: AC-001-1 构建清单第一行
  假定 值班同学已运行 `bash prepare.sh` 生成 `dist/app.txt`
  当 值班同学读取 `dist/app.txt` 的第一行
  那么 内容为 `tool-cli 1`

@AC-002 @normal @G-002
场景: AC-002-1 构建清单第二行
  假定 值班同学已运行 `bash prepare.sh` 生成 `dist/app.txt`
  当 值班同学读取 `dist/app.txt` 的第二行
  那么 内容为 `commands=greet,count,export`

@AC-003 @normal @G-003 @BR-001
场景: AC-003-1 构建清单第三行
  假定 值班同学已运行 `bash prepare.sh` 生成 `dist/app.txt`
  当 值班同学读取 `dist/app.txt` 的第三行
  那么 内容为 `greet-shout=yes`
```
EOF

DIR="$ROOT/micro-groups"
rm -rf "$ROOT/micro-groups"
mkdir -p "$DIR/docs/changes/tool-cli" "$DIR/tests" "$DIR/tools" "$DIR/data/greet"
printf '.agents/\nmaterials/\ndist/\n__pycache__/\n.pytest_cache/\n' > "$DIR/.gitignore"

cat > "$DIR/tool.py" <<'EOF'
#!/usr/bin/env python3
"""工具集: 问候, 统计与 JSON 导出."""
import argparse
import json
from pathlib import Path
import sys


def greet(name: str, separator: str = ", ") -> str:
    return f"Hello{separator}{name}!"


def count(text: str, chars: bool) -> int:
    return len(text) if chars else len(text.split())


def export_payload(name: str) -> str:
    return json.dumps({"name": name, "greeting": greet(name)}, ensure_ascii=False)


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
        print(export_payload(args.name))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
EOF

printf 'alpha beta gamma\n' > "$DIR/notes.txt"
cat > "$DIR/tools/build_manifest.py" <<'EOF'
"""生成构建清单 dist/app.txt.

按生产方式逐条跑 CLI 收集 250 条问候输出再算出清单校验行, 因此单次准备约 25 秒.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
names = root.joinpath("data/greet/names.txt").read_text(encoding="utf-8").split()
digest = hashlib.sha256()
for _round in range(3):
    for name in names[:250]:
        out = subprocess.run(
            [sys.executable, str(root / "tool.py"), "greet", "--name", name],
            capture_output=True, text=True, check=True,
        ).stdout
        digest.update(out.encode("utf-8"))
source = root.joinpath("tool.py").read_text(encoding="utf-8")
shout = "yes" if "--shout" in source else "no"
lines = [
    "tool-cli 1",
    "commands=greet,count,export",
    f"greet-shout={shout}",
    f"greet-digest={digest.hexdigest()[:16]}",
]
Path("dist").mkdir(exist_ok=True)
Path("dist/app.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("built dist/app.txt")
EOF

cat > "$DIR/prepare.sh" <<'EOF'
#!/usr/bin/env bash
# 构建检查用的产物. dist/ 不进仓库, 每个新会话都要先跑一次 (约 25 秒).
set -euo pipefail
python3 tools/build_manifest.py
EOF

cat > "$DIR/deps.txt" <<'EOF'
python-stdlib
EOF
cat > "$DIR/deps.lock" <<'EOF'
# 本工具只用 Python 标准库, 无第三方依赖.
EOF
cat > "$DIR/build.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q tool.py
EOF

cat > "$DIR/tests/test_tool.py" <<'EOF'
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

cat > "$DIR/README.md" <<'EOF'
# tool-cli

工具集, 含问候, 统计与 JSON 导出.

## 构建检查

- `bash prepare.sh` 生成 `dist/app.txt` 构建清单, 单次约 25 秒.
- `dist/` 不进仓库, 每个新会话都要先跑一次 `bash prepare.sh`.
- 构建清单检查都是只读: 读 `dist/app.txt` 的对应行.

## 检查

- `python3 -m pytest -q`
- `bash build.sh`
EOF

cat > "$DIR/docs/changes/tool-cli/TECHNICAL.md" <<'EOF'
# 工具集 Technical Spec

## 模块接口

- 入口 `python3 tool.py <子命令>`, 子命令为 greet, count, export.

## 测试接缝

- 构建检查先跑 `bash prepare.sh`, 再读 `dist/app.txt`.

## 验证入口

- `python3 -m pytest -q`
- `bash build.sh`
EOF

python3 - "$DIR" <<'EOF'
import sys
from pathlib import Path
root = Path(sys.argv[1])
names = [f"Person{i:03d}" for i in range(1, 251)]
(root / "data/greet/names.txt").write_text("\n".join(names) + "\n", encoding="utf-8")
EOF

promote_product "$BUILD/PRODUCT.base.md" "$BUILD/draft-micro2.md" "$DIR/docs/changes/tool-cli/PRODUCT.md"
(cd "$DIR" && git init -q -b main && git add -A && git \
  -c user.name=drill -c user.email=drill@example.com commit -qm "初始化工具集与产品标准")
(cd "$DIR" && git remote add author "$AUTHOR" && git fetch -q author && git \
  -c user.name=drill -c user.email=drill@example.com cherry-pick "$CHANGE" >/dev/null)
mkdir -p "$DIR/.agents/skills/verify-change"
cp -a "$REPO/workflow/verify-change/." "$DIR/.agents/skills/verify-change/"
{
  printf 'micro-groups 目标提交 %s 脏文件 %s 场景数 %s 审计BR数 %s\n' \
    "$(cd "$DIR" && git rev-parse HEAD)" \
    "$(cd "$DIR" && git status --porcelain | wc -l)" \
    "$(grep -c '^场景: ' "$DIR/docs/changes/tool-cli/PRODUCT.md")" \
    "$(grep -c '(审计)' "$DIR/docs/changes/tool-cli/PRODUCT.md")"
} | tee "$BUILD/fixtures.txt"
(cd "$DIR" && time bash prepare.sh && head -3 dist/app.txt && rm -rf dist) 2>&1 | tail -8
