"""ISSUE-21 的机械复核: 叙述视角与重复批准规则.

用法: uv run python check-issue21.py <create/SKILL.md> <maintain/SKILL.md>
退出码 0 表示无命中; 1 表示有命中, 命中项逐条打印.

三组检查:
- 视角: 正文出现 "用户" 且不属固定术语时命中 (writing-for-llm 第 7 节 "叙述视角").
  固定术语只有两个: "用户入口" 指产品的使用者入口, "用户调用" 指 BR-009 的调用方式.
  需求方一律写 "我", 执行 agent 写 "你".
- 重复: 同一段正文字符串在两份正文各出现一次时命中 (writing-for-llm "单一真相源").
  阈值 20 字符, 用来跳过 "完成标准:" 这类短标签; frontmatter 与代码块不计入.
- 单一真相源与指针: 共用批准规则的两句在全仓库只出现一次, 另一份文件给出可解析的
  文件指针与节名, 且两份文件都保留自己的资源清单四项.

这不是行为断言工具, 只做写作面机械审计.
"""

import re
import sys
from pathlib import Path

FIXED_TERMS = ("用户入口", "用户调用")
SHARED_RULES = (
    "批准绑定这四样",
    "派工单原样写进批准的范围与授权",
)
SECTION = "共用批准规则"
RESOURCE_LABELS = ("资源与对象:", "操作:", "清理:", "验证办法:")
DUPLICATE_MIN = 20
LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")


def prose_lines(path: Path) -> list[tuple[int, str]]:
    """返回正文行 (行号, 文本), 跳过 frontmatter 与代码块."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0] == "---":
        end = lines.index("---", 1)
        lines = lines[end + 1 :]
    out: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        out.append((number, line))
    return out


def voice_hits(path: Path) -> list[str]:
    hits = []
    for number, line in prose_lines(path):
        rest = line
        for term in FIXED_TERMS:
            rest = rest.replace(term, "")
        if "用户" in rest:
            hits.append(f"{path}:{number}: 第三人称指需求方: {line.strip()}")
    return hits


def shared_prose(create: Path, maintain: Path) -> list[str]:
    hits = []
    create_lines = {line.strip() for _, line in prose_lines(create) if len(line.strip()) >= DUPLICATE_MIN}
    for number, line in prose_lines(maintain):
        text = line.strip()
        if len(text) >= DUPLICATE_MIN and text in create_lines:
            hits.append(f"{maintain}:{number}: 与 create 正文逐字重复: {text}")
    return hits


def single_source(create: Path, maintain: Path) -> list[str]:
    hits = []
    bodies = {create: "\n".join(l for _, l in prose_lines(create)),
              maintain: "\n".join(l for _, l in prose_lines(maintain))}
    for rule in SHARED_RULES:
        owners = [path for path, body in bodies.items() if rule in body]
        if len(owners) != 1:
            names = ", ".join(str(p) for p in owners) or "无"
            hits.append(f"共用规则 {rule!r} 应只在一份正文出现, 实际: {names}")
    if SECTION not in bodies[create]:
        hits.append(f"{create}: 缺少共用规则所在小节标题 {SECTION!r}")
    pointer = None
    for _, line in prose_lines(maintain):
        if SECTION in line:
            pointer = line
            break
    if pointer is None:
        hits.append(f"{maintain}: 没有指向 {SECTION!r} 的指针")
    else:
        links = LINK.findall(pointer)
        resolved = [
            (label, target)
            for label, target in links
            if (maintain.parent / target).resolve() == create.resolve()
        ]
        if not resolved:
            hits.append(f"{maintain}: 指针未解析到 create 的 SKILL.md: {pointer.strip()}")
    for path in (create, maintain):
        body = bodies[path]
        for label in RESOURCE_LABELS:
            if label not in body:
                hits.append(f"{path}: 缺少自己的资源清单项 {label}")
    return hits


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    create, maintain = Path(argv[0]), Path(argv[1])
    hits = voice_hits(create) + voice_hits(maintain)
    hits += shared_prose(create, maintain)
    hits += single_source(create, maintain)
    for hit in hits:
        print(hit)
    print(f"hits={len(hits)}")
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
