#!/usr/bin/env python3
"""check-provenance-artifacts: 静态核对两个复刻包的许可与来源差异材料 (TS-001, TC-102).

只做机械审计: 文件是否存在, 许可段落是否完整, 固定 SHA 与差异表字段是否可读,
translate-a-skill 第 7 节校验命令与其结果是否记在包内. 不判断译文忠实性.

用法: uv run python check-provenance-artifacts.py [--repo-root <路径>]
退出码 0 表示全部通过, 1 表示有缺失项.
"""

from __future__ import annotations

import argparse
from pathlib import Path

FIXED_SHA = "4382e687a50b8d2c5ce4d141d001186589cff8d5"
PACKAGES = ("workflow/blast-radius", "workflow/benchmark-checklist")
PROVENANCE_NAMES = ("reference/PROVENANCE.md", "reference/source-record.md")

MIT_SEGMENTS = (
    "MIT License",
    "Copyright (c) 2026 Lauren Tan",
    "Permission is hereby granted, free of charge, to any person obtaining a copy",
    "furnished to do so, subject to the following conditions:",
    "The above copyright notice and this permission notice shall be included in all",
    'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR',
    "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,",
    "PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE",
    "IN NO EVENT SHALL THE",
    "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,",
    "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE",
)

DIFF_HEADER_CELLS = ("源版位置", "目标版位置", "影响", "处理决定")

PROVENANCE_NEEDS = {
    "固定 SHA": FIXED_SHA,
    "不追浮动 main": "不追浮动",
    "上游获取命令 (raw.githubusercontent.com 带固定 SHA)": f"raw.githubusercontent.com/cursor/plugins/{FIXED_SHA}/pstack",
    "translate-a-skill 第 7 节全角标点命令": "\\x{ff0c}",
    "标点检查结果": "无命中",
    "标题结构命令": '^(',
    "证据目录": "evidence/ISSUE-13/",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=None)
    args = parser.parse_args()
    root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[5]

    failures: list[str] = []
    checks = 0

    for package in PACKAGES:
        pkg = root / package
        checks += 1
        if not pkg.is_dir():
            failures.append(f"[{package}] 包目录不存在: {pkg}")
            continue

        license_path = pkg / "LICENSE"
        checks += 1
        if not license_path.is_file():
            failures.append(f"[{package}] 缺少 LICENSE")
        else:
            text = read(license_path)
            for segment in MIT_SEGMENTS:
                checks += 1
                if segment not in text:
                    failures.append(f"[{package}/LICENSE] 缺少 MIT 片段: {segment}")

        provenance = None
        for name in PROVENANCE_NAMES:
            candidate = pkg / name
            checks += 1
            if candidate.is_file():
                provenance = candidate
                break
        if provenance is None:
            failures.append(f"[{package}] 缺少来源差异记录: {' 或 '.join(PROVENANCE_NAMES)}")
            continue

        text = read(provenance)
        label = f"{package}/{provenance.name}"
        for name, needle in PROVENANCE_NEEDS.items():
            checks += 1
            if needle not in text:
                failures.append(f"[{label}] 缺少{name}")
        for cell in DIFF_HEADER_CELLS:
            checks += 1
            if cell not in text:
                failures.append(f"[{label}] 差异表缺少字段: {cell}")

    print(f"checks={checks} failures={len(failures)}")
    for item in failures:
        print(f"FAIL {item}")
    if failures:
        return 1
    print("OK 两个复刻包的许可, 固定来源与逐项差异记录可读")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
