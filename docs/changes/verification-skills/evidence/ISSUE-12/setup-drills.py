#!/usr/bin/env python3
"""准备 ISSUE-12 的临时演练项目: drill-a, drill-b, drill-c.

只生成夹具并做一次初始提交, 不替真实会话决定行为结果.
用法: uv run python setup-drills.py [--root /tmp/orchestra-12]
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

APP = r'''#!/usr/bin/env python3
"""notes-cli: 一个极小的笔记命令行工具."""

import json
import sys
from pathlib import Path

VERSION = "0.3.0"
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "notes.json"
INCLUDE_ARCHIVED_IN_SEARCH = __SEARCH_BUG__


def load():
    if not DATA.exists():
        return []
    return json.loads(DATA.read_text(encoding="utf-8"))


def save(notes):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(notes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def next_id(notes):
    return max((note["id"] for note in notes), default=0) + 1


def main(argv):
    if not argv:
        print("usage: app.py <add|list|search|archive|export|doctor> ...", file=sys.stderr)
        return 2
    command, rest = argv[0], argv[1:]
    notes = load()

    if command == "add":
        if not rest:
            print("缺少笔记正文", file=sys.stderr)
            return 2
        note = {"id": next_id(notes), "text": " ".join(rest), "archived": False}
        notes.append(note)
        save(notes)
        print(f"added {note['id']}: {note['text']}")
        return 0

    if command == "list":
        for note in notes:
            mark = " [archived]" if note["archived"] else ""
            print(f"{note['id']}\t{note['text']}{mark}")
        return 0

    if command == "search":
        if not rest:
            print("缺少关键词", file=sys.stderr)
            return 2
        keyword = rest[0]
        hits = []
        for note in notes:
            if keyword not in note["text"]:
                continue
            if note["archived"] and not INCLUDE_ARCHIVED_IN_SEARCH:
                continue
            hits.append(note)
        for note in hits:
            print(f"{note['id']}\t{note['text']}")
        print(f"matches: {len(hits)}")
        return 0

    if command == "archive":
        if not rest:
            print("缺少笔记编号", file=sys.stderr)
            return 2
        target = int(rest[0])
        for note in notes:
            if note["id"] == target:
                note["archived"] = True
                save(notes)
                print(f"archived {target}")
                return 0
        print(f"note not found: {target}", file=sys.stderr)
        return 1

    if command == "export":
        if not rest:
            print("缺少导出路径", file=sys.stderr)
            return 2
        target = Path(rest[0])
        target.write_text("".join(f"{note['id']}\t{note['text']}\n" for note in notes), encoding="utf-8")
        print(f"exported {len(notes)} notes to {target}")
        return 0

    if command == "doctor":
        print(f"notes-cli {VERSION}")
        print(f"data_path: {DATA}")
        print(f"notes: {len(notes)}")
        return 0

    if command == "--version":
        print(VERSION)
        return 0

    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
'''

PRODUCT_A = """# PRODUCT.md (已确认)

状态: 已确认, 提交时生效.

## 范围

当前产品只包含两个功能: 新建笔记, 搜索笔记. 导出与归档属于历史功能, 不在本次产品范围.

## 功能要求

### 新建笔记

- 执行 `python3 app.py add "<正文>"` 后, 新笔记出现在 `python3 app.py list` 输出中, 正文与输入一致.

### 搜索笔记

- 执行 `python3 app.py search "<关键词>"` 返回正文包含关键词的笔记.
- 已归档笔记不出现在搜索结果中.
"""

PRODUCT_B = """# PRODUCT.md (已确认)

状态: 已确认, 提交时生效.

## 范围

当前产品包含三个功能: 新建笔记, 搜索笔记, 导出笔记. 归档属于历史功能, 不在本次产品范围.

## 功能要求

### 新建笔记

- 执行 `python3 app.py add "<正文>"` 后, 新笔记出现在 `python3 app.py list` 输出中, 正文与输入一致.

### 搜索笔记

- 执行 `python3 app.py search "<关键词>"` 返回正文包含关键词的笔记.
- 已归档笔记不出现在搜索结果中.

### 导出笔记

- 执行 `python3 app.py export <文件路径>` 写出全部笔记, 每行一条.
- 导出文件存在, 行数与 `python3 app.py list` 的输出行数一致.
"""


def shared_skill(*, health: str, health_expect: str) -> str:
    return f"""---
name: verify-notes
description: 项目本地验证配方, 启动 notes-cli 并按功能驱动真实入口.
disable-model-invocation: true
---

# verify-notes

来源项目: notes-cli 的旧配方, 覆盖多个历史功能.

## 启动

```bash
cd <项目根>
python3 app.py --version
```

期望输出 `0.3.0`.

## 健康检查

```bash
{health}
```

期望{health_expect}.

## 驱动

用 `python3 app.py` 的真实子命令. 每步记录命令与输出.

## 取证

命令输出与 `data/notes.json` 片段, 存到本 skill 的 `evidence/` 下.

## 清理

删除本次创建的 `data/` 目录和临时文件, 保留 `evidence/` 供复核, 不删除他人数据.

## 功能入口

- [新建笔记](features/create-note.md)
- [搜索笔记](features/search-notes.md)
"""


CREATE_DRIFT = """# 新建笔记

- 准备: 在项目根启动一次, 确认版本.
- 命令: `python3 app.py add --text "第一条笔记"`
- 验证: `python3 app.py list` 输出含 `1\t第一条笔记`.
"""

SEARCH_DRIFT = """# 搜索笔记

- 准备: 新建两条笔记, 其中一条正文含关键词 `会议`, 再归档另一条含 `会议` 的笔记.
- 命令: `python3 app.py find 会议`
- 验证: 输出只含未归档的匹配项.
"""

EXPORT_OK = """# 导出笔记

- 准备: 新建一条笔记.
- 命令: `python3 app.py export /tmp/notes-export.txt`
- 验证: 文件存在, 行数与 `python3 app.py list` 一致.
"""

ARCHIVE_OK = """# 归档笔记

- 准备: 新建一条笔记.
- 命令: `python3 app.py archive 1`
- 验证: `python3 app.py list` 输出该条带 `[archived]` 标记.
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build(root: Path, name: str, *, search_bug: bool, product: str | None,
          features: dict[str, str], health: str, health_expect: str) -> None:
    project = root / name
    if project.exists():
        shutil.rmtree(project)
    write(project / "app.py", APP.replace("__SEARCH_BUG__", str(search_bug)))
    if product is not None:
        write(project / "docs" / "PRODUCT.md", product)
    skill = project / ".agents" / "skills" / "verify-notes"
    write(skill / "SKILL.md", shared_skill(health=health, health_expect=health_expect))
    for feature, content in features.items():
        write(skill / "features" / f"{feature}.md", content)
    write(project / ".gitignore", "data/\n" + ".agents/skills/verify-notes/evidence/\n")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "add", "-A"], cwd=project, check=True)
    subprocess.run(
        ["git", "-c", "user.name=ISSUE-12 drill", "-c", "user.email=drill@example.invalid",
         "commit", "-q", "-m", "fixture: 初始项目与旧配方"],
        cwd=project, check=True,
    )
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project, check=True,
                          capture_output=True, text=True).stdout.strip()
    print(f"{name}: {project} @ {head}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/tmp/orchestra-12"))
    args = parser.parse_args()
    root: Path = args.root
    root.mkdir(parents=True, exist_ok=True)

    features_a = {
        "create-note": CREATE_DRIFT,
        "search-notes": SEARCH_DRIFT,
        "export-notes": EXPORT_OK,
    }
    build(root, "drill-a", search_bug=True, product=PRODUCT_A,
          features=features_a, health="python3 app.py doctor", health_expect="输出首行为 `notes-cli 0.2.0`")

    features_b = {
        "create-note": CREATE_DRIFT,
        "search-notes": SEARCH_DRIFT,
        "archive-notes": ARCHIVE_OK,
    }
    build(root, "drill-b", search_bug=False, product=PRODUCT_B,
          features=features_b, health="python3 app.py --health", health_expect="输出包含 version 与 data_path")

    build(root, "drill-c", search_bug=True, product=None,
          features=features_a, health="python3 app.py doctor", health_expect="输出首行为 `notes-cli 0.2.0`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
