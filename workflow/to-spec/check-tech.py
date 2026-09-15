# /// script
# requires-python = ">=3.10"
# ///
"""TECHNICAL.md 节名机检脚本.

用法: uv run check-tech.py <TECHNICAL.md 路径>

校验三项, 规则与同目录 SKILL.md 的 TECHNICAL.md 模板对齐:
1. 节名封闭集: `## ` 标题只允许模板固定节名, 逐字一致; "(条件保留)" 是模板
   标注, 落盘标题不得携带; 不重复出现同一节.
2. 必备节齐全: 架构与组件/接口契约/数据模型与状态/边界与异常处理/
   依赖与风险/决策引用 必须全部出现; 条件节 (安全策略/非功能要求/关键流程/
   测试接缝) 不满足保留条件时整节省略.
3. 节序合法: 全部 `## ` 节的先后顺序必须是模板序的子序列.
"""

from __future__ import annotations

import re
import sys

# (节名, 是否必备), 顺序即模板序
SECTIONS: tuple[tuple[str, bool], ...] = (
    ("架构与组件", True),
    ("接口契约", True),
    ("数据模型与状态", True),
    ("边界与异常处理", True),
    ("依赖与风险", True),
    ("安全策略", False),
    ("非功能要求", False),
    ("关键流程", False),
    ("测试接缝", False),
    ("决策引用", True),
)

HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.M)
FENCE_RE = re.compile(r"^```[^\n]*\n.*?^```", re.S | re.M)


def fail_input(detail: str) -> None:
    print(f"[输入] {detail}", file=sys.stderr)
    sys.exit(2)


def main() -> int:
    if len(sys.argv) != 2:
        fail_input("用法: uv run check-tech.py <TECHNICAL.md 路径>")
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            markdown = f.read()
    except OSError as e:
        fail_input(f"无法读取 {sys.argv[1]}: {e}")

    names = [name for name, _ in SECTIONS]
    allowed = set(names)
    required = [name for name, req in SECTIONS if req]
    order = {name: i for i, name in enumerate(names)}

    # 代码块替换为等价空行, 防止块内 `## ` 被当成标题且保持行号对齐
    stripped = FENCE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), markdown)

    violations: list[str] = []
    found: list[tuple[str, int]] = []
    for m in HEADING_RE.finditer(stripped):
        name = m.group(1)
        line = stripped[: m.start()].count("\n") + 1
        if name not in allowed:
            violations.append(
                f"[节名封闭集] 行 {line}: 非法节名 {name!r} (封闭集: "
                f"{'/'.join(names)}; `(条件保留)` 为模板标注, 落盘标题不得携带)"
            )
        else:
            found.append((name, line))

    seen: set[str] = set()
    for name, line in found:
        if name in seen:
            violations.append(f"[节名封闭集] 行 {line}: 节 {name!r} 重复出现")
        seen.add(name)

    for name in required:
        if name not in seen:
            violations.append(f"[必备节] 缺少必备节 `## {name}`")

    seq = [order[name] for name, _ in found]
    if seq != sorted(seq):
        violations.append(
            f"[节序] 节顺序与模板不一致: {' -> '.join(name for name, _ in found)}"
        )

    if violations:
        for item in violations:
            print(item, file=sys.stderr)
        return 1
    print(f"check-tech: 通过 - {len(found)} 节")
    return 0


if __name__ == "__main__":
    sys.exit(main())
