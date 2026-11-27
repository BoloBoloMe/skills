"""ISSUE-04 run1 取证: 坏格式/坏编号 promote 保护, 以及确认标记文案对照.

全部经真实公开 CLI 进程 (ac-draft.py / check-ac.py), 真实隔离文件, 不含 mock.
运行: uv run --with gherkin-official python probe04.py
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = Path("/home/bolo/Workspace/improve.worktrees/ISSUE-04")
SKILL = REPO / "workflow/to-spec"
NEW_CHECK = SKILL / "check-ac.py"
BASE_CHECK = HERE / "baseline/check-ac.py"
DRAFT_CLI = SKILL / "ac-draft.py"
LOGS = HERE / "logs"
FILES = HERE / "files"

BASE = """# 测试变更 Product Spec

## 背景

保留这段中文背景.

## 目标

- 目标1: 读者能看到已确认的内容.

## 非目标

- 非目标1: 不修改其他文档.

## 业务规则

- 规则1: 内容以当前版本为准.
- 规则2: 不新增第三方依赖. (审计)

## 验收标准

待确认, 此处暂不写入正式用例.

## 决策引用

- DECISIONS.md: 决策1.
"""
DRAFT = """```gherkin
# language: zh-CN
功能: 测试变更

背景:
假定 读者已打开当前文档

@AC-001 @normal @G-001 @BR-001
场景: 阅读内容
假定 文档包含 1 条验收标准
当 读者查看验收标准
那么 读者看到已确认的原文
```
"""
MARKER = "<!-- confirmed-flow: v1 -->"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=30)


def save(name: str, argv: list[str], done: subprocess.CompletedProcess) -> None:
    (LOGS / f"{name}.cmd").write_text(json.dumps(argv, ensure_ascii=False) + "\n", encoding="utf-8")
    (LOGS / f"{name}.stdout").write_text(done.stdout, encoding="utf-8")
    (LOGS / f"{name}.stderr").write_text(done.stderr, encoding="utf-8")
    (LOGS / f"{name}.exit").write_text(f"{done.returncode}\n", encoding="utf-8")


def marker_cases() -> list[dict]:
    """标记文案与行为对照: 同一输入分别喂基线 check-ac.py 与目标 check-ac.py."""
    section = "待确认, 此处暂不写入正式用例."
    cases = {
        "missing-marker": BASE.replace(section, DRAFT),
        "marker-after-fence": BASE.replace(section, DRAFT + MARKER),
        "v2-marker-accepted": BASE.replace(section, "<!-- confirmed-flow: v2 -->\n" + DRAFT),
        "v1-marker-accepted": BASE.replace(section, MARKER + "\n" + DRAFT),
    }
    rows = []
    for label, text in cases.items():
        case_dir = FILES / "marker" / label
        case_dir.mkdir(parents=True, exist_ok=True)
        product = case_dir / "PRODUCT.md"
        product.write_text(text, encoding="utf-8")
        row = {"case": label, "input": str(product), "input_sha256": sha256(product)}
        for flavor, checker in (("baseline", BASE_CHECK), ("target", NEW_CHECK)):
            argv = [sys.executable, str(checker), str(product)]
            done = run(argv, case_dir)
            save(f"marker-{label}-{flavor}", argv, done)
            row[flavor] = {"exit": done.returncode, "stdout": done.stdout.strip(),
                           "stderr": done.stderr.strip()}
        rows.append(row)
    return rows


def bad_input_cases() -> list[dict]:
    """坏格式/坏编号输入: 真实隔离正式稿已存在, 断言非零退出且字节不变."""
    base, draft = BASE.encode(), DRAFT.encode()
    duplicate_goal = base.replace(
        "- 目标1: 读者能看到已确认的内容.".encode(),
        "- 目标1: 读者能看到已确认的内容.\n- 目标1: 另一条目标.".encode(),
    )
    cases = {
        "variant-keyword": (base, draft.replace("假定".encode(), "假设".encode()), 1, "白名单"),
        "synonym-keyword": (base, draft.replace("那么".encode(), "并且".encode()), 1, "白名单"),
        "missing-feature-line": (base, draft.replace("功能: 测试变更\n".encode(), b""), 1, "解析"),
        "feature-level-tag": (base, draft.replace("功能:".encode(), "@G-001\n功能:".encode()), 1, "tag-position"),
        "draft-with-marker": (base, MARKER.encode() + b"\n" + draft, 2, "草稿不携带确认标记"),
        "prose-outside-fence": (base, draft + "## 决策引用\n改写正文\n".encode(), 2, "草稿只能包含"),
        "unknown-goal": (base, draft.replace(b"@G-001", b"@G-999"), 1, "不存在"),
        "unknown-rule": (base, draft.replace(b"@BR-001", b"@BR-999"), 1, "不存在"),
        "audit-rule": (base, draft.replace(b"@BR-001", b"@BR-002"), 1, "审计"),
        "two-ac-one-scenario": (base, draft.replace(b"@AC-001", b"@AC-001 @AC-002"), 1, "@AC"),
        "duplicate-goal-entry": (duplicate_goal, draft, 2, "重复"),
    }
    rows = []
    for label, (new_base, new_draft, expected, needle) in cases.items():
        case_dir = FILES / "bad" / label
        case_dir.mkdir(parents=True, exist_ok=True)
        product = case_dir / "PRODUCT.base.md"
        review = case_dir / "review"
        review.mkdir(exist_ok=True)
        acceptance = review / "acceptance.md"
        output = case_dir / "formal" / "PRODUCT.md"
        product.write_bytes(BASE.encode())
        acceptance.write_bytes(DRAFT.encode())
        setup = run([sys.executable, str(DRAFT_CLI), "promote", str(product), str(acceptance), str(output)], case_dir)
        save(f"bad-{label}-setup", [str(DRAFT_CLI), "promote", str(product), str(acceptance), str(output)], setup)
        assert setup.returncode == 0, setup.stdout + setup.stderr
        before = output.read_bytes()
        before_sha = sha256(output)
        product.write_bytes(new_base)
        acceptance.write_bytes(new_draft)
        (case_dir / "formal-before.md").write_bytes(before)
        argv = [sys.executable, str(DRAFT_CLI), "promote", str(product), str(acceptance), str(output)]
        done = run(argv, case_dir)
        save(f"bad-{label}", argv, done)
        after = output.read_bytes()
        listing = sorted(p.name for p in output.parent.iterdir())
        rows.append({
            "case": label,
            "expected_exit": expected,
            "exit": done.returncode,
            "nonzero": done.returncode != 0,
            "error_matches": needle in done.stdout,
            "stdout": done.stdout.strip(),
            "stderr": done.stderr.strip(),
            "output_sha256_before": before_sha,
            "output_sha256_after": sha256(output),
            "output_bytes_unchanged": after == before,
            "output_dir_entries": listing,
        })
    return rows


def main() -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    FILES.mkdir(parents=True, exist_ok=True)
    result = {
        "python": sys.version.split()[0],
        "check_ac_target_sha256": sha256(NEW_CHECK),
        "check_ac_baseline_sha256": sha256(BASE_CHECK),
        "marker": marker_cases(),
        "bad_input": bad_input_cases(),
    }
    (HERE / "probe04.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ok = all(row["nonzero"] and row["exit"] == row["expected_exit"] and row["error_matches"]
             and row["output_bytes_unchanged"] and row["output_dir_entries"] == ["PRODUCT.md"]
             for row in result["bad_input"])
    print(f"marker cases: {len(result['marker'])}, bad-input cases: {len(result['bad_input'])}, all_expected={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())