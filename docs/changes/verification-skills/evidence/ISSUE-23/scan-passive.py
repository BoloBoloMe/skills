#!/usr/bin/env python3
"""scan-passive: 扫 "被" 字残留 (translate-a-skill 第 2 节第 2 刀, 全文禁字).

用法: uv run python scan-passive.py <文件或目录>...
目录按 *.md 递归展开. 命中逐行打印, 退出码 1; 全清退出码 0.
例外只给法律/安全警告句: 同一行含 "警告" 时打印但不算失败, 判定仍靠人读.
"""

from __future__ import annotations

import sys
from pathlib import Path

FORBIDDEN = "被"
WARNING_MARK = "警告"


def targets(args: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in args:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
        elif path.is_file():
            files.append(path)
        else:
            raise SystemExit(f"路径不存在: {raw}")
    return files


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    hits = 0
    files = targets(sys.argv[1:])
    for path in files:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if FORBIDDEN not in line:
                continue
            if WARNING_MARK in line:
                print(f"[例外: 警告句] {path}:{number}: {line.strip()}")
                continue
            hits += 1
            print(f"[命中] {path}:{number}: {line.strip()}")
    print(f"扫描文件数={len(files)} 命中={hits}")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
