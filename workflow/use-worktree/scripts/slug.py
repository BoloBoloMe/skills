"""Generate portable worktree directory slugs."""
from __future__ import annotations

import hashlib
import re
import sys

if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", newline="\n")

MAX_LEN = 60
HASH_LEN = 7
PREFIX_LEN = MAX_LEN - HASH_LEN - 1

USAGE = """用法:
  slug.py <branch>
  slug.py <project> <source-branch> <target-branch>

规则:
  Windows 非法路径字符和控制字符 -> -
  空格 -> _
  保留中文 / Unicode
  slug 最长 60 字符; 超长时使用前 52 字符 + '-' + sha1 前 7 位

说明:
  正常输出中的 key=value 字段保持英文, 便于脚本和 agent 解析.
"""

INVALID_RE = re.compile(r'[\\/:*?"<>|\x00-\x1f\x7f]+')
HYPHEN_RE = re.compile(r"-+")


def sanitize(raw: str) -> str:
    clean = raw.strip(" .")
    clean = INVALID_RE.sub("-", clean)
    clean = clean.replace(" ", "_")
    clean = HYPHEN_RE.sub("-", clean)
    clean = re.sub(r"_-|-_|--", "-", clean)
    clean = HYPHEN_RE.sub("-", clean)
    clean = clean.strip(".-")
    return clean


def hash7(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:HASH_LEN]


def slug_one(branch: str) -> str:
    clean = sanitize(branch) or "branch"
    if len(clean) > MAX_LEN:
        h = hash7(branch)
        prefix = sanitize(clean[:PREFIX_LEN]).rstrip("-")
        clean = h if not prefix else f"{prefix}-{h}"
    return clean


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(USAGE, end="")
        return 0

    if len(argv) == 1:
        branch = argv[0]
        slug = slug_one(branch)
        print(f"branch={branch}")
        print(f"slug={slug}")
        print(f"length={len(slug)}")
        return 0

    if len(argv) == 3:
        project, source_branch, target_branch = argv
        source_slug = slug_one(source_branch)
        target_slug = slug_one(target_branch)
        print(f"project={project}")
        print(f"source_branch={source_branch}")
        print(f"source_slug={source_slug}")
        print(f"target_branch={target_branch}")
        print(f"target_slug={target_slug}")
        print(f"dir={sanitize(f'{project}-{source_slug}-{target_slug}')}")
        return 0

    print(USAGE, end="", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
