#!/usr/bin/env python3
"""准备 ISSUE-17 的临时演练项目: proj-create, proj-maintain.

只生成夹具, 复制待测技能源目录并做一次初始提交, 不替真实会话决定行为结果.
用法: uv run python setup-drills.py --skill create-verification-skill
      uv run python setup-drills.py --skill maintain-verification-skill
可选: --root /tmp/orchestra-17 --worktree <skills 仓库工作树>
"""

import argparse
import shutil
import subprocess
from pathlib import Path

NOTES_SH = r'''#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
DATA=${NOTES_DATA:-$ROOT/data/items.txt}
cmd=${1:-}
case $cmd in
  add)
    text=${2:-}
    if [ -z "$text" ]; then echo "usage: notes.sh add <text>" >&2; exit 2; fi
    mkdir -p "$(dirname "$DATA")"
    printf '%s\n' "$text" >> "$DATA"
    echo "added: $text"
    ;;
  show)
    if [ ! -s "$DATA" ]; then echo "(empty)"; exit 0; fi
    i=0
    while IFS= read -r line; do
      i=$((i + 1))
      printf '%s\t%s\n' "$i" "$line"
    done < "$DATA"
    ;;
  status)
    echo "notes-cli 0.2.0"
    echo "data_path: $DATA"
    ;;
  export)
    out=${2:-}
    if [ -z "$out" ]; then echo "usage: notes.sh export <path>" >&2; exit 2; fi
    mkdir -p "$(dirname "$out")"
    cp "$DATA" "$out" 2>/dev/null || : > "$out"
    echo "exported to $out"
    ;;
  *)
    echo "usage: notes.sh <add|show|status|export>" >&2
    exit 2
    ;;
esac
'''

PRODUCT = r'''# notes-cli 产品说明

状态: 已确认 (2026-10-20, 产品负责人确认). 本文件是本轮唯一通过判据来源.

## 功能: 记录笔记

- 入口: `./notes.sh add <正文>`
- 通过: 退出码 0; 输出 `added: <正文>`; 之后 `show` 能在列表末尾看到这条正文.

## 功能: 查看笔记

- 入口: `./notes.sh show`
- 通过: 每行输出 `<序号>\t<正文>`, 序号从 1 连续递增, 顺序与实际记录一致; 没有记录时输出 `(empty)` 且退出码 0.

## 非目标

- 导出 (`export`) 不在本轮覆盖范围.
'''

README = r'''# notes-cli

极简笔记工具, 数据默认落在 `data/items.txt` (可用 NOTES_DATA 覆盖).

- `./notes.sh add <正文>`
- `./notes.sh show`
- `./notes.sh status`
- `./notes.sh export <path>` (本轮非目标)
'''

RECIPE_SHARED = r'''---
name: verify-fixture
description: 按已确认 PRODUCT.md 实跑 notes-cli 的记录与查看入口.
disable-model-invocation: true
---

# notes-cli 验证配方

本项目本地配方让陌生 agent 按 `docs/PRODUCT.md` 实跑记录与查看两个入口.

## 共用规则

- 健康检查: `./notes.sh doctor`, 应输出 `notes-cli 0.2.0` 与数据路径.
- 数据目录: `data/notes.txt`.
- 取证: 每次运行输出存到 `evidence/<时间>-<功能>.txt`.
- 清理: `rm -rf data/`.

## 功能入口

- 记录笔记: [features/add.md](features/add.md)
- 查看笔记: [features/show.md](features/show.md)
- 导出笔记: [features/export.md](features/export.md)
'''

RECIPE_ADD = r'''# 记录笔记

1. 前置: 数据目录 `data/` 不存在时先 `mkdir -p data/`.
2. 操作: `./notes.sh add --text "第一条笔记"`.
3. 期望: 退出码 0, 输出 `added: 第一条笔记`.
4. 取证: `./notes.sh show > evidence/<时间>-add.txt`.
'''

RECIPE_SHOW = r'''# 查看笔记

1. 前置: 数据目录 `data/` 不存在时先 `mkdir -p data/`.
2. 操作: `./notes.sh show`.
3. 期望: 空数据输出 `(empty)`; 有数据时每行 `<序号>\t<正文>`.
4. 取证: `./notes.sh show > evidence/<时间>-show.txt`.
'''

RECIPE_EXPORT = r'''# 导出笔记 (历史功能, 当前 PRODUCT.md 未覆盖)

1. 操作: `./notes.sh export /tmp/notes-export.txt`.
2. 期望: 输出 `exported to /tmp/notes-export.txt`.
3. 取证: 拷贝导出文件到 `evidence/`.
'''


def run(*args, cwd=None):
    subprocess.run(args, cwd=cwd, check=True)


def write(path: Path, text: str, mode=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if mode is not None:
        path.chmod(mode)


def build_project(project: Path, skill_source: Path, maintain: bool):
    if project.exists():
        shutil.rmtree(project)
    project.mkdir(parents=True)
    write(project / "notes.sh", NOTES_SH, 0o755)
    write(project / "README.md", README)
    write(project / "docs" / "PRODUCT.md", PRODUCT)
    if maintain:
        recipe = project / ".agents" / "skills" / "verify-fixture"
        write(recipe / "SKILL.md", RECIPE_SHARED)
        write(recipe / "features" / "add.md", RECIPE_ADD)
        write(recipe / "features" / "show.md", RECIPE_SHOW)
        write(recipe / "features" / "export.md", RECIPE_EXPORT)
    target = project / ".agents" / "skills" / skill_source.name
    shutil.copytree(skill_source, target)
    run("git", "init", "-q", "-b", "main", cwd=project)
    run("git", "config", "user.name", "orchestra", cwd=project)
    run("git", "config", "user.email", "orchestra@example.invalid", cwd=project)
    run("git", "add", "-A", cwd=project)
    commit = subprocess.run(
        ["git", "commit", "-q", "-m", "fixture: notes-cli 与待测技能"],
        cwd=project, check=True, capture_output=True, text=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project, check=True, capture_output=True, text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=project, check=True, capture_output=True, text=True,
    ).stdout
    print(f"project: {project}")
    print(f"skill:   {target}")
    print(f"commit:  {head}")
    print(f"status:  {status!r}")
    assert not status, "夹具工作区应干净"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", required=True, choices=[
        "create-verification-skill", "maintain-verification-skill",
    ])
    parser.add_argument("--root", default="/tmp/orchestra-17")
    parser.add_argument(
        "--worktree",
        default=str(Path(__file__).resolve().parents[5]),
    )
    args = parser.parse_args()
    worktree = Path(args.worktree)
    skill_source = worktree / "workflow" / args.skill
    assert (skill_source / "SKILL.md").is_file(), skill_source
    name = "proj-maintain" if args.skill == "maintain-verification-skill" else "proj-create"
    build_project(Path(args.root) / name, skill_source, maintain=name == "proj-maintain")


if __name__ == "__main__":
    main()
