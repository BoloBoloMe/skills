# /// script
# requires-python = ">=3.10"
# dependencies = ["gherkin-official>=42.0.1"]
# ///
"""PRODUCT.md 验收标准机检脚本 (D011/D012).

用法: uv run check-ac.py <PRODUCT.md 路径> [--draft <验收用例草稿.md>]
草稿模式以 PRODUCT 暂存稿提供目标/业务规则, 只豁免确认标记, 不修改文件.

确认标记 + 六项格式校验, 规则与同目录 SKILL.md / GHERKIN.md 对齐:
0. 确认标记: `验收标准` 节必须含 `<!-- confirmed-flow: vN -->` (由 to-spec
   验收标准确认流程写入), 正式模式缺失判为输入错误; 标记本身不证明实际确认.
1. 解析: gherkin-official parser 必须成功解析 gherkin 块.
2. 标签封闭集与 @AC 唯一性 (D003/D007): 只允许 @AC-NNN / @G-NNN /
   @BR-NNN / @normal / @failure / @edge; 每场景 (含场景大纲) 恰好一个 @AC-NNN.
3. 覆盖完整性 (D003): 每个出现过的 @AC-NNN 至少挂在一个场景上; 每场景至少一个
   覆盖标签 (@G-NNN / @BR-NNN).
4. 关键字子集白名单 (D005/D008): 禁 规则: (Rule); 禁官方同义变体
   (假如/假设/剧本/剧本大纲/并且/同时), 节点与步骤关键字只允许唯一写法
   (背景/场景/场景大纲, 假定/当/那么/而且/但是).
   注意: parser 对非关键字行不报错而是吸收为 description (实测行为), 因此
   "描述非空" 视为存在非关键字行 (如 给定/则/英文关键字), 判为违规.
5. 标签位置: 标签只允许出现在场景/场景大纲行; 功能级/例子块级标签会
   向下继承, 破坏每场景恰好一个 @AC 的语义, 一律判为违规.
6. 编号对账: 场景引用的 @G-NNN/@BR-NNN 必须在 PRODUCT.md 的 目标/业务规则 节
   真实存在; @BR 不得指向标 (审计) 的审计式断言.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from gherkin import Parser
from gherkin.token_matcher import TokenMatcher

CONFIRMATION_MARKER = "<!-- confirmed-flow: v1 -->"
FENCE_RE = re.compile(r"^```gherkin[^\n]*\n(.*?)^```", re.S | re.M)
MARKER_RE = re.compile(r"<!--\s*confirmed-flow:\s*v\d+\s*-->")

AC_TAG_RE = re.compile(r"^@AC-\d{3}$")
COVER_TAG_RES = (
    re.compile(r"^@G-\d{3}$"),
    re.compile(r"^@BR-\d{3}$"),
)
TYPE_TAGS = ("@normal", "@failure", "@edge")

# 官方 zh-CN 关键字的规范化子集 (GHERKIN.md §1): 禁用同义变体
# (假如/假设/剧本/剧本大纲/并且/同时), 统一唯一写法.
BACKGROUND_KEYWORDS = ("背景",)
SCENARIO_KEYWORDS = ("场景", "场景大纲")
STEP_KEYWORDS = ("假定", "当", "那么", "而且", "但是")

# 编号对账 (校验 6): 从 PRODUCT.md 正文节提取 G/BR 条目
ENTRY_RE = re.compile(r"^\s*[-*]\s*(G|BR)-(\d{3})\s*[:：]")
AUDIT_MARKS = ("(审计)", "（审计）")


class InputError(ValueError):
    """文件或文档结构不符合输入约定, CLI 退出码 2."""


class ValidationError(ValueError):
    """Gherkin 解析或既有规则未通过, CLI 退出码 1."""


def section_bounds(markdown: str, section: str, *, required: bool = True) -> tuple[int, int] | None:
    """返回唯一二级节的正文字符范围, 忽略代码块内的伪标题."""
    headings: list[tuple[str, int, int]] = []
    fence: tuple[str, int] | None = None
    offset = 0
    for line in markdown.splitlines(keepends=True):
        text = line.rstrip("\r\n")
        if fence is not None:
            char, length = fence
            if re.fullmatch(rf"[ ]{{0,3}}{re.escape(char)}{{{length},}}[ \t]*", text):
                fence = None
        elif match := re.match(r"^[ ]{0,3}(`{3,}|~{3,})", text):
            fence = (match[1][0], len(match[1]))
        elif match := re.fullmatch(r"##[ \t]+(.+?)[ \t]*", text):
            headings.append((match[1], offset, offset + len(line)))
        offset += len(line)
    if fence is not None:
        raise InputError("PRODUCT 中有未闭合代码块, 无法安全确定章节范围")
    matches = [index for index, (name, _, _) in enumerate(headings) if name == section]
    if not matches:
        if required:
            raise InputError(f"未找到 `## {section}` 节")
        return None
    if len(matches) != 1:
        raise InputError(f"`## {section}` 节重复, 无法确定唯一替换位置")
    index = matches[0]
    end = headings[index + 1][1] if index + 1 < len(headings) else len(markdown)
    return headings[index][2], end


def extract_entries(markdown: str, section: str) -> dict[str, bool]:
    """提取 `## <section>` 节中的 G/BR 条目, 返回 {编号: 是否 (审计) 条目}.

    节不存在视为空集 (模板允许 业务规则 节无内容), 引用自然全部判为悬挂.
    """
    bounds = section_bounds(markdown, section, required=False)
    if bounds is None:
        return {}
    body = markdown[bounds[0] : bounds[1]]
    entries: dict[str, bool] = {}
    for line in body.splitlines():
        em = ENTRY_RE.match(line)
        if em:
            entries[f"{em.group(1)}-{em.group(2)}"] = any(
                mark in line for mark in AUDIT_MARKS
            )
    return entries


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


def extract_gherkin_block(markdown: str, *, require_marker: bool = True) -> tuple[str, int]:
    """定位 `## 验收标准` 节并提取其中唯一的 ```gherkin 块.

    返回 (块文本, 块首行在 PRODUCT.md 中的 1 基行号).
    """
    start, end = section_bounds(markdown, "验收标准")
    section = markdown[start:end]
    m = FENCE_RE.search(section)
    if m is None:
        raise InputError("`## 验收标准` 节中未找到 ```gherkin 代码块")
    marker = MARKER_RE.search(section)
    if require_marker and marker is None:
        raise InputError(
            f"`## 验收标准` 节缺少确认流程标记 `{CONFIRMATION_MARKER}` "
            "(由 to-spec 验收标准确认流程写入)"
        )
    if marker is not None and marker.start() > m.start():
        raise InputError(
            "确认流程标记 `<!-- confirmed-flow: vN -->` 必须位于 gherkin 代码块之前"
        )
    if FENCE_RE.search(section, m.end()):
        raise InputError("`## 验收标准` 节应恰好一个 ```gherkin 块, 实际多于一个")
    block = m.group(1)
    if not block.lstrip().startswith("# language:"):
        raise InputError("gherkin 块首行必须是 `# language: zh-CN`")
    # 保留原文换行, AST 行号与完整 PRODUCT 对齐.
    first_line = markdown[: start + m.start(1)].count("\n") + 1
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
                f"非法标签 {name} (封闭集: @AC-NNN/@G-NNN/@BR-NNN/"
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


def walk(gdt: dict, v: Violations) -> tuple[int, int, list[tuple[str, str, str]]]:
    """遍历 AST, 返回 (场景数, AC 数, 覆盖标签引用列表)."""
    feature = gdt.get("feature")
    if feature is None:
        v.add("关键字白名单", "gherkin 块", "缺少 `功能:` 行")
        return 0, 0, []
    if feature.get("keyword") != "功能":
        v.add(
            "关键字白名单",
            loc(feature),
            f"功能关键字为 {feature.get('keyword')!r}, 必须是 `功能`",
        )
    check_description(feature, v, "功能")

    # W2: 功能级不允许挂任何标签 (会向所有场景继承)
    check_tag_position(feature, v, "功能级")

    state = {"scenarios": 0, "ac_on": set(), "cover_refs": []}

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
                for tag in sc.get("tags") or []:
                    if any(r.match(tag["name"]) for r in COVER_TAG_RES):
                        state["cover_refs"].append((tag["name"], loc(tag), sc_where))
                if not cover_names:
                    v.add(
                        "覆盖完整性",
                        f"{loc(sc)} ({sc_where})",
                        "缺少覆盖标签, 每场景至少一个 @G-NNN/@BR-NNN",
                    )
                for ex in sc.get("examples") or []:
                    # W2: 例子块级不允许挂任何标签
                    check_tag_position(ex, v, f"{sc_where} 的例子")
                    check_description(ex, v, f"{sc_where} 的例子")

    handle_children(feature.get("children") or [])
    return state["scenarios"], len(state["ac_on"]), state["cover_refs"]


def with_draft(markdown: str, draft: str, *, confirmed: bool) -> str:
    """只替换验收正文, 草稿本身不经 strip/换行转换/重新序列化."""
    match = FENCE_RE.search(draft)
    if match is None or draft[:match.start()].strip() or draft[match.end():].strip():
        raise InputError("草稿只能包含一个完整的 gherkin 代码块及首尾空白")
    if MARKER_RE.search(draft):
        raise InputError("草稿不携带确认标记, 由转正脚本在确认后添加")
    start, end = section_bounds(markdown, "验收标准")
    newline = "\r\n" if "\r\n" in markdown else "\n"
    body = newline
    if confirmed:
        body += CONFIRMATION_MARKER + newline
    body += draft
    if not body.endswith("\n"):
        body += newline
    body += newline
    return markdown[:start] + body + markdown[end:]


def validate_draft(markdown: str, draft: str) -> tuple[int, int]:
    return validate_product(with_draft(markdown, draft, confirmed=False), require_marker=False)


def validate_product(markdown: str, *, require_marker: bool = True) -> tuple[int, int]:
    """两种模式共用全部解析/标签/覆盖/编号规则, 只切换标记要求."""
    block, first_line = extract_gherkin_block(markdown, require_marker=require_marker)

    try:
        # 前面补空行, 使 AST 行号与 PRODUCT.md 文件行号对齐
        padded = "\n" * (first_line - 1) + block
        gdt = Parser().parse(padded, TokenMatcher("zh-CN"))
    except Exception as e:
        raise ValidationError(f"[解析] gherkin 块解析失败 (行号为文件行号):\n{e}") from e

    v = Violations()
    n_scenarios, n_acs, cover_refs = walk(gdt, v)

    # 校验 6: 编号对账 — 引用的 G/BR 必须在正文节真实存在且类别正确
    g_entries = extract_entries(markdown, "目标")
    br_entries = extract_entries(markdown, "业务规则")
    for name, where, sc_where in cover_refs:
        key = name.lstrip("@")
        if name.startswith("@G-"):
            if key not in g_entries:
                v.add(
                    "编号对账",
                    f"{where} ({sc_where})",
                    f"{name} 在 `## 目标` 节不存在 (对账来源: 该节的 `- G-NNN:` 列表项)",
                )
        elif name.startswith("@BR-"):
            if key not in br_entries:
                v.add(
                    "编号对账",
                    f"{where} ({sc_where})",
                    f"{name} 在 `## 业务规则` 节不存在 (对账来源: 该节的 `- BR-NNN:` 列表项)",
                )
            elif br_entries[key]:
                v.add(
                    "编号对账",
                    f"{where} ({sc_where})",
                    f"{name} 指向 (审计) 条目, 审计式断言禁止进 Gherkin, 由覆盖矩阵承接",
                )
    if v:
        raise ValidationError("\n".join(v.items))
    return n_scenarios, n_acs


def read_utf8(path: Path) -> str:
    # read_text 的通用换行转换会破坏草稿原文的字节一致性.
    return path.read_bytes().decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("product", type=Path, help="正式 PRODUCT 或提供目标/业务规则的暂存稿")
    parser.add_argument("--draft", type=Path, help="验收正文草稿, 仅豁免确认标记")
    args = parser.parse_args()
    try:
        markdown = read_utf8(args.product)
        if args.draft is not None:
            n_scenarios, n_acs = validate_draft(markdown, read_utf8(args.draft))
        else:
            n_scenarios, n_acs = validate_product(markdown)
    except (InputError, OSError, UnicodeError) as exc:
        print(f"[输入] {exc}", file=sys.stderr)
        return 2
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    mode = " (草稿)" if args.draft is not None else ""
    print(f"check-ac{mode}: 通过 - {n_scenarios} 个场景, {n_acs} 个 AC")
    return 0


if __name__ == "__main__":
    sys.exit(main())
