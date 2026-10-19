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
