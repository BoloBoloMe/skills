#!/usr/bin/env bash
# ISSUE-03 重型夹具: 3 个可独立验收的场景组, 每组有足量互不共享的批量检查.
# 用于 AC-005-1 的 (3 组, 可派 2 人) 与 (3 组, 可派 3 人) 两个大纲例子.
# 用法: bash setup-heavy-drills.sh <仓库工作树根目录> <实现提交>
set -euo pipefail

REPO=${1:?需要仓库工作树根目录}
CHANGE=${2:?需要真实实现会话的提交}
ROOT=/tmp/orchestra-03/heavy
BUILD="$ROOT/build"
AUTHOR=/tmp/orchestra-03/author
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

promote_product() {
  local base="$1" draft="$2" out="$3" review
  review=$(cd "$REPO" && uv run workflow/to-spec/ac-draft.py preview "$base" "$draft" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["review_id"])')
  (cd "$REPO" && uv run workflow/to-spec/ac-draft.py promote "$base" "$draft" "$out" --review "$review" >/dev/null)
  (cd "$REPO" && uv run workflow/to-spec/check-ac.py "$out" >/dev/null)
}

write_inputs() {
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
- BR-002: 本变更不新增第三方依赖, 依赖清单, 锁文件和构建材料与上一提交逐项一致. (审计)

## 验收标准

## 决策引用

- 无.
EOF

  cat > "$BUILD/draft-heavy.md" <<'EOF'
```gherkin
# language: zh-CN
功能: 工具集

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

@AC-001 @normal @G-001 @BR-001
场景: AC-001-3 批量问候 250 个姓名
  假定 值班同学已有 `data/greet/names.txt`, 共 250 行, 每行一个姓名
  当 值班同学对每一行运行一次 `python3 tool.py greet --name <该行姓名>`
  那么 250 条标准输出都等于 `Hello, <该行姓名>!` 且退出码都是 0

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

@AC-002 @normal @G-002
场景: AC-002-3 批量统计 250 个文件
  假定 值班同学已有 `data/count/docs/` 下 250 个文本文件, 以及 `data/count/expected.tsv` (每行是文件名与词数)
  当 值班同学对每个文件运行一次 `python3 tool.py count --file <该文件>`
  那么 250 条标准输出都与 `expected.tsv` 中对应词数一致且退出码都是 0

@AC-003 @normal @G-003
场景: AC-003-1 JSON 导出
  假定 值班同学已取得 tool.py
  当 值班同学运行 `python3 tool.py export --name Ada`
  那么 标准输出为 `{"name": "Ada", "greeting": "Hello, Ada!"}` 且退出码为 0

@AC-003 @normal @G-003
场景: AC-003-2 批量导出 200 个姓名
  假定 值班同学已有 `data/export/names.txt`, 共 200 行, 每行一个姓名
  当 值班同学对每一行运行一次 `python3 tool.py export --name <该行姓名>`
  那么 200 条标准输出都等于 `{"name": "<该行姓名>", "greeting": "Hello, <该行姓名>!"}` 且退出码都是 0
```
EOF
}

write_project() {
  local dir="$1"
  mkdir -p "$dir/docs/changes/tool-cli" "$dir/tests" "$dir/tools" "$dir/data/greet" \
    "$dir/data/count/docs" "$dir/data/export"
  printf '.agents/\nmaterials/\ndist/\n__pycache__/\n.pytest_cache/\n' > "$dir/.gitignore"

  cat > "$dir/tool.py" <<'EOF'
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

  printf 'alpha beta gamma\n' > "$dir/notes.txt"

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

工具集, 含问候, 统计与 JSON 导出.

## 运行

- 问候: `python3 tool.py greet --name Ada`
- 统计: `python3 tool.py count --file notes.txt`
- 导出: `python3 tool.py export --name Ada`

## 验收数据

- `data/greet/names.txt`: 250 个姓名, 供批量问候检查.
- `data/count/docs/` 与 `data/count/expected.tsv`: 250 个文本文件及其期望词数, 供批量统计检查.
- `data/export/names.txt`: 200 个姓名, 供批量导出检查.
- 三组数据互不共享, 也不被构建脚本或测试引用.

## 检查

- `python3 -m pytest -q`
- `bash build.sh`
EOF

  cat > "$dir/docs/changes/tool-cli/TECHNICAL.md" <<'EOF'
# 工具集 Technical Spec

## 模块接口

- 入口 `python3 tool.py <子命令>`, 子命令为 greet, count, export.

## 测试接缝

- 直接运行 CLI 并观察标准输出, 标准错误与退出码.
- 批量检查逐条运行 CLI, 与 `data/` 下的输入和期望文件对照.

## 验证入口

- `python3 -m pytest -q`
- `bash build.sh`
EOF

  python3 - "$dir" <<'EOF'
import sys
from pathlib import Path

root = Path(sys.argv[1])
names = [f"Person{i:03d}" for i in range(1, 251)]
(root / "data/greet/names.txt").write_text("\n".join(names) + "\n", encoding="utf-8")

docs = root / "data/count/docs"
rows = []
for i in range(1, 251):
    text = " ".join(f"w{i}x{j}" for j in range(1, (i % 9) + 2)) + "\n"
    name = f"doc{i:03d}.txt"
    (docs / name).write_text(text, encoding="utf-8")
    rows.append(f"{name}\t{len(text.split())}")
(root / "data/count/expected.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")

export_names = [f"Guest{i:03d}" for i in range(1, 201)]
(root / "data/export/names.txt").write_text("\n".join(export_names) + "\n", encoding="utf-8")
EOF

  promote_product "$BUILD/PRODUCT.base.md" "$BUILD/draft-heavy.md" "$dir/docs/changes/tool-cli/PRODUCT.md"
}

main() {
  rm -rf "$ROOT"
  mkdir -p "$BUILD"
  write_inputs
  for name in three-groups-2avail three-groups-3avail; do
    write_project "$ROOT/$name"
    (cd "$ROOT/$name" && git init -q -b main && git add -A && git \
      -c user.name=drill -c user.email=drill@example.com commit -qm "初始化工具集与产品标准")
    (cd "$ROOT/$name" && git remote add author "$AUTHOR")
    (cd "$ROOT/$name" && git fetch -q author && git \
      -c user.name=drill -c user.email=drill@example.com cherry-pick "$CHANGE" >/dev/null)
    mkdir -p "$ROOT/$name/.agents/skills/verify-change"
    cp -a "$REPO/workflow/verify-change/." "$ROOT/$name/.agents/skills/verify-change/"
  done
  {
    echo "生成时间: $TS"
    for name in three-groups-2avail three-groups-3avail; do
      printf '%s 目标提交 %s 脏文件 %s 场景数 %s 审计BR数 %s\n' "$name" \
        "$(cd "$ROOT/$name" && git rev-parse HEAD)" \
        "$(cd "$ROOT/$name" && git status --porcelain | wc -l)" \
        "$(grep -c '^场景: ' "$ROOT/$name/docs/changes/tool-cli/PRODUCT.md")" \
        "$(grep -c '(审计)' "$ROOT/$name/docs/changes/tool-cli/PRODUCT.md")"
    done
  } | tee "$BUILD/fixtures.txt"
}

main
