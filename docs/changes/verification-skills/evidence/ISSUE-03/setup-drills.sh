#!/usr/bin/env bash
# ISSUE-03 演练夹具准备. 只在 /tmp/orchestra-03 下建临时 Git 项目, 不碰仓库与其他目录.
# 用法: bash setup-drills.sh <仓库工作树根目录> init
#       bash setup-drills.sh <仓库工作树根目录> apply-author-change <实现提交>
# init 只准备初始提交与产品标准; 目标提交由真实实现会话完成后, 再用 apply-author-change 把该提交
# cherry-pick 到各夹具, 保证"本次实现"有真实会话和真实提交可核对.
set -euo pipefail

REPO=${1:?需要仓库工作树根目录}
MODE=${2:-init}
ROOT=/tmp/orchestra-03
BUILD="$ROOT/build"
AUTHOR="$ROOT/author"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

reset_fixtures() {
  rm -rf "$ROOT"/*
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

write_product_base() {
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
}

write_drafts() {
  cat > "$BUILD/draft-three.md" <<'EOF'
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

@AC-003 @normal @G-003
场景: AC-003-1 JSON 导出
  假定 值班同学已取得 tool.py
  当 值班同学运行 `python3 tool.py export --name Ada`
  那么 标准输出为 `{"name": "Ada", "greeting": "Hello, Ada!"}` 且退出码为 0
```
EOF

  cat > "$BUILD/draft-two.md" <<'EOF'
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

@AC-002 @normal @G-002
场景: AC-002-1 统计词数
  假定 值班同学已有文本文件 notes.txt, 内容为 `alpha beta gamma` 加一个换行
  当 值班同学运行 `python3 tool.py count --file notes.txt`
  那么 标准输出为 `3` 且退出码为 0
```
EOF

  cat > "$BUILD/draft-one.md" <<'EOF'
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
```
EOF

  cat > "$BUILD/draft-micro.md" <<'EOF'
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
}

write_project_files() {
  local dir="$1" draft="$2"
  mkdir -p "$dir/docs/changes/tool-cli" "$dir/tests" "$dir/tools"
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

  cat > "$dir/tools/build_manifest.py" <<'EOF'
"""生成构建清单 dist/app.txt, 供构建检查使用."""
import sys
from pathlib import Path

source = Path(__file__).resolve().parent.parent.joinpath("tool.py").read_text(encoding="utf-8")
shout = "yes" if "--shout" in source else "no"
lines = [
    "tool-cli 1",
    "commands=greet,count,export",
    f"greet-shout={shout}",
]
Path("dist").mkdir(exist_ok=True)
Path("dist/app.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("built dist/app.txt")
EOF

  cat > "$dir/prepare.sh" <<'EOF'
#!/usr/bin/env bash
# 构建检查用的产物. dist/ 不进仓库, 每个新会话都要先跑一次.
set -euo pipefail
python3 tools/build_manifest.py
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

## 构建检查

- `bash prepare.sh` 生成 `dist/app.txt` 构建清单; `dist/` 不进仓库, 每个新会话都要先跑一次.

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
- 构建检查先跑 `bash prepare.sh`, 再读 `dist/app.txt`.

## 验证入口

- `python3 -m pytest -q`
- `bash build.sh`
EOF

  promote_product "$BUILD/PRODUCT.base.md" "$BUILD/$draft.md" "$dir/docs/changes/tool-cli/PRODUCT.md"
}

commit_init() {
  local dir="$1"
  (cd "$dir" && git init -q -b main && git add -A && git \
    -c user.name=drill -c user.email=drill@example.com commit -qm "初始化工具集与产品标准")
}

# 把真实实现会话的提交 cherry-pick 到夹具, 保留原作者信息.
apply_author_change() {
  local dir="$1" sha="$2"
  (cd "$dir" && git remote add author "$AUTHOR" 2>/dev/null || true)
  (cd "$dir" && git fetch -q author && git \
    -c user.name=drill -c user.email=drill@example.com cherry-pick "$sha" >/dev/null)
}

write_materials() {
  local dir="$1" kind="$2" author_sha="$3"
  case "$kind" in
    none) return ;;
    blocked)
      mkdir -p "$dir/materials"
      cat > "$dir/materials/session-inventory.md" <<EOF
# 本轮可用会话清单

一次性配额已经用尽, 本轮不能再新开任何会话来验收.

| 会话名 | 参与事实 |
| --- | --- |
| \`i03-author\` | 本次实现由它完成 (提交 \`$author_sha\`), 之后没有单独的修复会话 |

清单外没有其他可用会话.
EOF
      ;;
    *) echo "未知材料类型: $kind" >&2; exit 2 ;;
  esac
}

main() {
  reset_fixtures
  write_product_base
  write_drafts

  for spec in "author:draft-three" "red-delegation:draft-three" \
    "red-plan:draft-micro" "green-non-author:draft-three" \
    "green-two-groups:draft-two" "green-three-groups:draft-three" \
    "green-single-group:draft-one" "green-micro-groups:draft-micro" \
    "green-blocked:draft-three"; do
    local name="${spec%%:*}" draft="${spec##*:}"
    write_project_files "$ROOT/$name" "$draft"
    commit_init "$ROOT/$name"
  done

  {
    echo "生成时间: $TS"
    for name in author red-delegation red-plan green-non-author green-two-groups \
      green-three-groups green-single-group green-micro-groups green-blocked; do
      printf '%s 初始提交 %s 场景数 %s 审计BR数 %s\n' "$name" \
        "$(cd "$ROOT/$name" && git rev-parse HEAD)" \
        "$(grep -c '^场景: ' "$ROOT/$name/docs/changes/tool-cli/PRODUCT.md")" \
        "$(grep -c '(审计)' "$ROOT/$name/docs/changes/tool-cli/PRODUCT.md")"
    done
  } | tee "$BUILD/fixtures.txt"
  echo "下一步: 在 $AUTHOR 开真实实现会话完成本次变更并提交, 再跑 apply-author-change."
}

case "$MODE" in
  apply-author-change)
    sha=${3:?需要实现提交}
    for name in red-delegation red-plan green-non-author green-two-groups \
      green-three-groups green-single-group green-micro-groups green-blocked; do
      apply_author_change "$ROOT/$name" "$sha"
    done
    write_materials "$ROOT/green-blocked" blocked "$sha"
    {
      echo "实现提交: $sha"
      for name in red-delegation red-plan green-non-author green-two-groups \
        green-three-groups green-single-group green-micro-groups green-blocked; do
        printf '%s 目标提交 %s 脏文件 %s\n' "$name" \
          "$(cd "$ROOT/$name" && git rev-parse HEAD)" \
          "$(cd "$ROOT/$name" && git status --porcelain | wc -l)"
      done
    } | tee -a "$BUILD/fixtures.txt"
    ;;
  init)
    main
    ;;
  *)
    echo "未知模式: $MODE (可用: init, apply-author-change)" >&2
    exit 2
    ;;
esac
