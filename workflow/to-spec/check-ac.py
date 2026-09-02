# /// script
# requires-python = ">=3.10"
# dependencies = ["gherkin-official>=42.0.1"]
# ///
"""PRODUCT.md 验收标准机检脚本 (D011/D012).

用法: uv run check-ac.py <PRODUCT.md 路径>

校验五项, 规则与同目录 SKILL.md / GHERKIN.md 对齐:
1. 解析: gherkin-official parser 必须成功解析 gherkin 块.
2. 标签封闭集与 @AC 唯一性 (D003/D007): 只允许 @AC-NNN / @G-NNN / @US-NNN /
   @BR-NNN / @normal / @failure / @edge; 每场景 (含场景大纲) 恰好一个 @AC-NNN.
3. 覆盖完整性 (D003): 每个出现过的 @AC-NNN 至少挂在一个场景上; 每场景至少一个
   覆盖标签 (@G-NNN / @US-NNN / @BR-NNN).
4. 关键字子集白名单 (D005/D008): 禁 规则: (Rule); 禁官方同义变体
   (假如/假设/剧本/剧本大纲/并且/同时), 节点与步骤关键字只允许唯一写法
   (背景/场景/场景大纲, 假定/当/那么/而且/但是).
   注意: parser 对非关键字行不报错而是吸收为 description (实测行为), 因此
   "描述非空" 视为存在非关键字行 (如 给定/则/英文关键字), 判为违规.
5. 标签位置: 标签只允许出现在场景/场景大纲行; 功能级/例子块级标签会
   向下继承, 破坏每场景恰好一个 @AC 的语义, 一律判为违规.
"""

from __future__ import annotations

import re
import sys

from gherkin import Parser
from gherkin.token_matcher import TokenMatcher

SECTION_HEADING_RE = re.compile(r"^##\s*验收标准\s*$")
NEXT_SECTION_RE = re.compile(r"^##\s")
FENCE_RE = re.compile(r"^```gherkin[^\n]*\n(.*?)^```", re.S | re.M)

AC_TAG_RE = re.compile(r"^@AC-\d{3}$")
COVER_TAG_RES = (
    re.compile(r"^@G-\d{3}$"),
    re.compile(r"^@US-\d{3}$"),
    re.compile(r"^@BR-\d{3}$"),
)
TYPE_TAGS = ("@normal", "@failure", "@edge")

# 官方 zh-CN 关键字的规范化子集 (GHERKIN.md §1): 禁用同义变体
# (假如/假设/剧本/剧本大纲/并且/同时), 统一唯一写法.
BACKGROUND_KEYWORDS = ("背景",)
SCENARIO_KEYWORDS = ("场景", "场景大纲")
STEP_KEYWORDS = ("假定", "当", "那么", "而且", "但是")


class Violations:
    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, rule: str, where: str, detail: str) -> None:
        self.items.append(f"[{rule}] {where}: {detail}")

    def __bool__(self) -> bool:
        return bool(self.items)


def loc(obj: dict) -> str:
    location = obj.get("location") or {}
    line = location.get("line", "?")
    return f"行 {line}"


def fail_input(detail: str) -> None:
    print(f"[输入] {detail}", file=sys.stderr)
    sys.exit(2)


def extract_gherkin_block(markdown: str) -> tuple[str, int]:
    """定位 `## 验收标准` 节并提取其中唯一的 ```gherkin 块.

    返回 (块文本, 块首行在 PRODUCT.md 中的 1 基行号).
    """
    lines = markdown.splitlines()
    start = None
    for i, line in enumerate(lines):
        if SECTION_HEADING_RE.match(line):
            start = i + 1
            break
    if start is None:
        fail_input("未找到 `## 验收标准` 节")
    end = len(lines)
    for j in range(start, len(lines)):
        if NEXT_SECTION_RE.match(lines[j]):
            end = j
            break
    section = "\n".join(lines[start:end])
    m = FENCE_RE.search(section)
    if m is None:
        fail_input("`## 验收标准` 节中未找到 ```gherkin 代码块")
    if FENCE_RE.search(section, m.end()):
        fail_input("`## 验收标准` 节应恰好一个 ```gherkin 块, 实际多于一个")
    block = m.group(1)
    if not block.lstrip().startswith("# language:"):
        fail_input("gherkin 块首行必须是 `# language: zh-CN`")
    # 块首内容行 (```gherkin 的下一行) 在文件中的行号
    first_line = start + section[: m.start(1)].count("\n") + 1
    return block, first_line


def check_tags(
    tags: list[dict], v: Violations, where: str
) -> tuple[list[str], list[str]]:
    """检查一组标签是否都在封闭集内, 返回 (合法的 @AC 标签名, 覆盖标签名)."""
    ac_names: list[str] = []
    cover_names: list[str] = []
    for tag in tags:
        name = tag["name"]
        if AC_TAG_RE.match(name):
            ac_names.append(name)
        elif any(r.match(name) for r in COVER_TAG_RES):
            cover_names.append(name)
        elif name in TYPE_TAGS:
            pass
        else:
            v.add(
                "标签封闭集",
                f"{loc(tag)} ({where})",
                f"非法标签 {name} (封闭集: @AC-NNN/@G-NNN/@US-NNN/@BR-NNN/"
                "@normal/@failure/@edge)",
            )
    return ac_names, cover_names


def check_description(node: dict, v: Violations, where: str) -> None:
    """描述非空 = 存在被 parser 吸收的非关键字行 (如 给定/则/英文关键字)."""
    desc = (node.get("description") or "").strip()
    if desc:
        v.add(
            "关键字白名单",
            f"{loc(node)} ({where})",
            f"存在非关键字行 (被 parser 吸收为描述): {desc.splitlines()[0]!r}; "
            "官方 zh-CN 关键字: 假定/当/那么/而且/但是 (步骤), 给定/则/英文关键字均非法",
        )


def check_node_keywords(
    node: dict, v: Violations, where: str, allowed: tuple[str, ...]
) -> None:
    """W1: 节点 keyword 与各步骤 keyword 必须在白名单内 (变体即违规)."""
    keyword = (node.get("keyword") or "").strip()
    if keyword not in allowed:
        v.add(
            "关键字白名单",
            f"{loc(node)} ({where})",
            f"关键字为 {keyword!r}, 只允许 {'/'.join(allowed)}; "
            "官方同义变体 (假如/假设/剧本/剧本大纲/并且/同时) 已禁用 (D005)",
        )
    for step in node.get("steps") or []:
        kw = (step.get("keyword") or "").strip()
        if kw not in STEP_KEYWORDS:
            v.add(
                "关键字白名单",
                f"{loc(step)} ({where})",
                f"步骤关键字为 {kw!r}, 只允许 {'/'.join(STEP_KEYWORDS)}; "
                "官方同义变体 (假如/假设/并且/同时) 已禁用 (D005)",
            )


def check_tag_position(node: dict, v: Violations, where: str) -> None:
    """W2: 标签只允许出现在场景/场景大纲行; feature/examples 节点挂标签即违规."""
    for tag in node.get("tags") or []:
        v.add(
            "tag-position",
            f"{loc(tag)} ({where})",
            f"标签 {tag['name']} 只允许出现在场景/场景大纲行 "
            "(功能级/例子块级标签会继承, 破坏每场景恰好一个 @AC 的语义)",
        )


def walk(gdt: dict, v: Violations) -> tuple[int, int]:
    """遍历 AST, 返回 (场景数, AC 数)."""
    feature = gdt.get("feature")
    if feature is None:
        v.add("关键字白名单", "gherkin 块", "缺少 `功能:` 行")
        return 0, 0
    if feature.get("keyword") != "功能":
        v.add(
            "关键字白名单",
            loc(feature),
            f"功能关键字为 {feature.get('keyword')!r}, 必须是 `功能`",
        )
    check_description(feature, v, "功能")

    # W2: 功能级不允许挂任何标签 (会向所有场景继承)
    check_tag_position(feature, v, "功能级")

    state = {"scenarios": 0, "ac_on": set()}

    def handle_children(children: list[dict]) -> None:
        for child in children:
            if "rule" in child:
                rule = child["rule"]
                v.add(
                    "关键字白名单",
                    f"{loc(rule)} (规则 {rule.get('name', '')!r})",
                    "禁用 `规则:` (Rule) 关键字 (D008), 业务规则归属仅靠 @BR-NNN 标签表达",
                )
                handle_children(rule.get("children") or [])
            elif "background" in child:
                bg = child["background"]
                check_node_keywords(bg, v, "背景", BACKGROUND_KEYWORDS)
                check_description(bg, v, "背景")
            elif "scenario" in child:
                sc = child["scenario"]
                state["scenarios"] += 1
                sc_where = f"场景 {sc.get('name', '')!r}"
                check_node_keywords(sc, v, sc_where, SCENARIO_KEYWORDS)
                check_description(sc, v, sc_where)
                ac_names, cover_names = check_tags(
                    sc.get("tags") or [], v, sc_where
                )
                if len(ac_names) != 1:
                    v.add(
                        "@AC 唯一性",
                        f"{loc(sc)} ({sc_where})",
                        f"@AC 标签数为 {len(ac_names)} ({ac_names or '无'}), "
                        "每场景必须恰好一个 @AC-NNN",
                    )
                state["ac_on"].update(ac_names)
                if not cover_names:
                    v.add(
                        "覆盖完整性",
                        f"{loc(sc)} ({sc_where})",
                        "缺少覆盖标签, 每场景至少一个 @G-NNN/@US-NNN/@BR-NNN",
                    )
                for ex in sc.get("examples") or []:
                    # W2: 例子块级不允许挂任何标签
                    check_tag_position(ex, v, f"{sc_where} 的例子")
                    check_description(ex, v, f"{sc_where} 的例子")

    handle_children(feature.get("children") or [])
    return state["scenarios"], len(state["ac_on"])


def main() -> int:
    if len(sys.argv) != 2:
        fail_input("用法: uv run check-ac.py <PRODUCT.md 路径>")
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            markdown = f.read()
    except OSError as e:
        fail_input(f"无法读取 {sys.argv[1]}: {e}")

    block, first_line = extract_gherkin_block(markdown)

    try:
        # 前面补空行, 使 AST 行号与 PRODUCT.md 文件行号对齐
        padded = "\n" * (first_line - 1) + block
        gdt = Parser().parse(padded, TokenMatcher("zh-CN"))
    except Exception as e:
        print("[解析] gherkin 块解析失败, parser 原始错误 (行号为文件行号):", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 1

    v = Violations()
    n_scenarios, n_acs = walk(gdt, v)
    if v:
        for item in v.items:
            print(item, file=sys.stderr)
        return 1
    print(f"check-ac: 通过 - {n_scenarios} 个场景, {n_acs} 个 AC")
    return 0


if __name__ == "__main__":
    sys.exit(main())
