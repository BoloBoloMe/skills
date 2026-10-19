"""扫描 SKILL.md 正文的视角与句长, 供 ISSUE-18 的 TS-002 机械复核使用.

用法: uv run python scan-voice.py <SKILL.md> [...]
退出码 0 表示无命中; 1 表示有命中, 命中项逐条打印.
这不是行为断言工具, 只做写作面机械审计: 被动句, 超长句, 第三人称 "用户", 以及
把执行 agent 写成 "我" 的短语. 句长按汉字计 (translate-a-skill 的 "中文单句不超 25 字"),
先去掉行内代码与链接地址.
"""

import re
import sys
from pathlib import Path

SENTENCE_SPLIT = re.compile(r"[。;]|\.(?=\s|$)")
THIRD_PERSON = re.compile(r"用户")
FIRST_PERSON_AGENT = re.compile(r"(是我的角色|我自己|让我|我负责|我先|我读|我跑|我拿|我查|我会|我调)")
PASSIVE = re.compile(r"被")
CJK = re.compile(r"[\u4e00-\u9fff]")
INLINE_CODE = re.compile(r"`[^`]*`")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
STRIP = re.compile(r"[\s,.;:!?()\[\]{}<>\"'`*#>|~-]")


def prose_lines(path: Path) -> list[tuple[int, str]]:
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


def long_sentences(lines: list[tuple[int, str]]) -> list[tuple[int, int, str]]:
    hits = []
    for number, line in lines:
        cleaned = LINK.sub(r"\1", INLINE_CODE.sub("", line))
        for piece in SENTENCE_SPLIT.split(cleaned):
            text = piece.strip()
            if not text:
                continue
            counted = len(CJK.findall(text))
            raw = len(STRIP.sub("", text))
            if counted > 25:
                hits.append((number, counted, f"{text} [汉字 {counted}, 全字符 {raw}]"))
    return hits


def main(paths: list[str]) -> int:
    failed = False
    for raw in paths:
        path = Path(raw)
        lines = prose_lines(path)
        print(f"== {path}")
        for number, line in lines:
            for pattern, label in ((THIRD_PERSON, "第三人称"), (FIRST_PERSON_AGENT, "把执行者写成我")):
                match = pattern.search(line)
                if match:
                    print(f"{path}:{number}: {label}: {match.group(0)}")
                    failed = True
            if PASSIVE.search(line):
                print(f"{path}:{number}: 被动表述: {line.strip()}")
                failed = True
        for number, counted, text in long_sentences(lines):
            print(f"{path}:{number}: 超长句 ({counted} 字): {text}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
