#!/usr/bin/env bash
# ISSUE-01 演练夹具准备. 只在 /tmp/orchestra-01 下建临时 Git 项目, 不碰仓库与其他目录.
# 用法: bash setup-drills.sh <仓库工作树根目录>
set -euo pipefail

REPO=${1:?需要仓库工作树根目录}
ROOT=/tmp/orchestra-01
BUILD="$ROOT/build"

reset_fixtures() {
  rm -rf "$ROOT"/a-committed-clean "$ROOT"/c-no-product "$ROOT"/d-dirty "$ROOT"/e-checked-docs "$ROOT"/e-evidence
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
  mkdir -p "$BUILD"

  cat > "$BUILD/PRODUCT.base.md" <<'EOF'
# 问候工具 Product Spec

## 背景

团队需要一个小命令行工具, 按姓名打印问候语, 并能在正式场合切换成全大写输出. 提出方是运维小组, 受益者是每天发版通知的值班同学.

## 目标

- G-001: 值班同学能在本机运行问候命令, 按姓名得到问候语, 并用 `--shout` 切换成全大写输出.

## 非目标

- NG-001: 不做多语言. (理由: 当前只有中文团队使用.)

## 业务规则

- BR-001: 问候语固定以 `Hello` 开头, 后接 `, ` 与姓名, 以 `!` 结尾.
- BR-002: 本工具只依赖 Python 标准库, 不新增第三方依赖. (审计)

## 验收标准

## 决策引用

- 无.
EOF

  cat > "$BUILD/验收草稿.md" <<'EOF'
```gherkin
# language: zh-CN
功能: 问候工具

@AC-001 @normal @G-001 @BR-001
场景: AC-001-1 默认问候
  假定 值班同学已取得 greet.py
  当 值班同学运行 `python3 greet.py --name Ada`
  那么 标准输出为 `Hello, Ada!` 且退出码为 0

@AC-002 @normal @G-001 @BR-001
场景: AC-002-1 大声问候
  假定 值班同学已取得 greet.py
  当 值班同学运行 `python3 greet.py --name Ada --shout`
  那么 标准输出为 `HELLO, ADA!` 且退出码为 0
```
EOF

  cat > "$BUILD/TECHNICAL.md" <<'EOF'
# 问候工具 Technical Spec

## 模块划分

- greet: 命令行入口, 解析参数并打印问候语.

## 模块接口

- 本变更必须把参数解析拆到 `lib/args.py`, 由 `greet.py` 调用; 该内部代码划分是本变更必须完成的事项.

## 接缝与适配器

- CLI 入口 `python3 greet.py`.

## 测试接缝

- 直接运行 CLI 并观察标准输出与退出码.

## 安全策略

- 只读本地参数, 不访问网络.

## 关键流程

1. 解析参数 -> 2. 生成问候语 -> 3. 打印.

## 决策引用

- 无.
EOF

  cat > "$BUILD/EXECUTION.md" <<'EOF'
# 问候工具 Execution Spec

## 允许范围

- 新增 `greet.py`; 新增 `lib/args.py`.

## 禁止范围

- 不引入第三方依赖.

## 完成定义

- 全部任务完成, 检查命令通过.

## 任务图

- TASK-01: 实现 greet.py; 覆盖 AC-001. [x]
- TASK-02: 实现 `--shout` 全大写; 覆盖 AC-002. [x]
- TASK-03: 拆分 `lib/args.py`. [x]

## 验证入口

- `python3 greet.py --name Ada`

## 覆盖矩阵

- AC-001 -> TASK-01. AC-002 -> TASK-02.
EOF
}

write_project() {
  local dir="$1" with_product="$2"
  mkdir -p "$dir/docs/changes/greet-cli"
  printf '.agents/\n' > "$dir/.gitignore"
  cat > "$dir/greet.py" <<'EOF'
#!/usr/bin/env python3
"""按姓名打印问候语, --shout 切换全大写."""
import argparse
import sys


def greet(name: str, shout: bool) -> str:
    return f"Hello, {name}!"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="greet.py")
    parser.add_argument("--name", required=True)
    parser.add_argument("--shout", action="store_true")
    args = parser.parse_args(argv)
    print(greet(args.name, args.shout))
    return 0


if __name__ == "__main__":
    sys.exit(main())
EOF
  cat > "$dir/README.md" <<'EOF'
# greet-cli

最小问候命令行工具.

## 运行

- 默认问候: `python3 greet.py --name Ada`
- 大声问候: `python3 greet.py --name Ada --shout`

## 开发约定

- 只用 Python 标准库, 不引入第三方依赖.
- 语法检查: `python3 -m compileall -q greet.py`.
EOF
  cp "$BUILD/TECHNICAL.md" "$BUILD/EXECUTION.md" "$dir/docs/changes/greet-cli/"
  if [ "$with_product" = "yes" ]; then
    promote_product "$BUILD/PRODUCT.base.md" "$BUILD/验收草稿.md" "$dir/docs/changes/greet-cli/PRODUCT.md"
  fi
}

commit_all() {
  local dir="$1" msg="$2"
  (cd "$dir" && git init -q -b main && git add -A && git -c user.name=drill -c user.email=drill@example.com commit -qm "$msg")
}

main() {
  reset_fixtures
  write_product_inputs

  write_project "$ROOT/a-committed-clean" yes
  commit_all "$ROOT/a-committed-clean" "初始化问候工具与三份 spec"

  write_project "$ROOT/c-no-product" no
  commit_all "$ROOT/c-no-product" "初始化问候工具, 只有技术 spec 与执行计划"

  cp -a "$ROOT/a-committed-clean" "$ROOT/d-dirty"
  python3 - "$ROOT/d-dirty/greet.py" <<'EOF'
import sys
from pathlib import Path
path = Path(sys.argv[1])
path.write_text(path.read_text(encoding="utf-8").replace('f"Hello, {name}!"', 'f"Hi, {name}!"'), encoding="utf-8")
EOF

  write_project "$ROOT/e-checked-docs" yes
  cat > "$ROOT/e-checked-docs/check_changes.py" <<'EOF'
#!/usr/bin/env python3
"""校验每个 docs/changes/<slug>/ 目录只含三份 spec, 多出文件即失败."""
import sys
from pathlib import Path

REQUIRED = {"PRODUCT.md", "TECHNICAL.md", "EXECUTION.md"}


def main() -> int:
    problems = []
    for change in sorted(Path("docs/changes").iterdir()):
        if not change.is_dir():
            continue
        names = {path.name for path in change.iterdir()}
        if missing := REQUIRED - names:
            problems.append(f"{change}: missing {sorted(missing)}")
        if extra := names - REQUIRED:
            problems.append(f"{change}: unexpected {sorted(extra)}")
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
EOF
  python3 - "$ROOT/e-checked-docs/README.md" <<'EOF'
import sys
from pathlib import Path
path = Path(sys.argv[1])
path.write_text(
    path.read_text(encoding="utf-8")
    + "\n## 变更目录检查\n\n- `python3 check_changes.py` 遍历 docs/changes 下每个变更目录, 只允许 PRODUCT.md, TECHNICAL.md, EXECUTION.md, 多出任何文件或目录即失败.\n",
    encoding="utf-8",
)
EOF
  commit_all "$ROOT/e-checked-docs" "初始化问候工具, spec 目录形态检查与三份 spec"

  echo "夹具就绪:"
  for dir in a-committed-clean c-no-product d-dirty e-checked-docs; do
    printf '%s %s %s\n' "$dir" "$(cd "$ROOT/$dir" && git rev-parse HEAD)" "$(cd "$ROOT/$dir" && git status --porcelain | wc -l)"
  done
}

main
