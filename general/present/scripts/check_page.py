"""present 页面交付前静态自检: 抓图表退化成源码/空白的那一类事故.

用法:
  check_page.py <html-file>

背景 (2026-10-26 事故): 曾把 `<pre class="mermaid">` 放进默认折叠的 `<details>`,
折叠容器量不出宽度, 于是又加了一段"展开时把图擦掉换回源码再重画"的补丁; 重画失败
时页面永久停在源码文本上. 本脚本把这三种退化做成可执行检查, 不靠人回忆.

检查项 (error 阻断交付, warning 只提示):
  diagram_in_hidden     mermaid 源码块在隐藏容器里 (details 未 open / hidden / display:none)
  mermaid_not_inlined   有 mermaid 源码块但没跑 embed_mermaid.py 内联渲染库
  baked_svg_missing     `.mermaid-rendered` 容器里没有 svg (本该是静态图却是空壳)
  manual_rerender       页面脚本自己调用 mermaid.run (禁止"擦掉再重画"式二次渲染)
  library_unused        已烘静态图却仍内联 3.5MB 渲染库 (浪费, 建议删)
  baked_in_hidden       静态图放在折叠容器里 (安全但读者可能永远看不到)

stdout: 单行 JSON. Exit 0 = 无 error, 1 = 有 error 或文件不可读.
"""

from __future__ import annotations

import json
import sys
from html.parser import HTMLParser
from pathlib import Path

LIBRARY_MARKER = "pi-present-mermaid-inline"
CHECK_COMMAND = "check"

_VOID = frozenset(
    "area base br col embed hr img input link meta param source track wbr".split()
)
_HIDING_STYLE = ("display:none", "display: none", "visibility:hidden", "visibility: hidden")


def _attrs(attrs) -> dict[str, str]:
    return {name.lower(): (value or "") for name, value in attrs}


def _hides_content(tag: str, attrs: dict[str, str]) -> bool:
    if "hidden" in attrs:
        return True
    if tag == "details" and "open" not in attrs:
        return True
    style = attrs.get("style", "").replace(" ", "").lower()
    return "display:none" in style or "visibility:hidden" in style


class _Scanner(HTMLParser):
    """一次遍历收集: mermaid 源码块/静态图容器/script 块及其隐藏祖先."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[tuple[str, bool]] = []
        self.hidden_chain: list[tuple[str, int]] = []
        self.mermaid_blocks: list[dict] = []
        self.baked_blocks: list[dict] = []
        self.script_blocks: list[dict] = []
        self._script_line = 0
        self._script_buf: list[str] | None = None
        self._baked_line = 0

    # --- 栈维护 ---
    def _push(self, tag: str, attrs: dict[str, str]) -> None:
        hiding = _hides_content(tag, attrs)
        self._stack.append((tag, hiding))
        if hiding:
            self.hidden_chain.append((tag, self.getpos()[0]))

    def _pop(self, tag: str) -> None:
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                removed = self._stack[index:]
                del self._stack[index:]
                for _, hiding in removed:
                    if hiding and self.hidden_chain:
                        self.hidden_chain.pop()
                return

    def _hidden_ancestors(self) -> list[str]:
        return [f"<{tag}> (第 {line} 行)" for tag, line in self.hidden_chain]

    def _mark_baked_svg(self) -> None:
        if self.baked_blocks and not self.baked_blocks[-1]["has_svg"]:
            self.baked_blocks[-1]["has_svg"] = True

    # --- 解析回调 ---
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        mapping = _attrs(attrs)
        classes = mapping.get("class", "").split()
        if tag == "svg":
            self._mark_baked_svg()
        if tag == "pre" and "mermaid" in classes:
            self.mermaid_blocks.append(
                {
                    "line": self.getpos()[0],
                    "hidden": self._hidden_ancestors(),
                    "has_svg": False,
                }
            )
        if tag == "div" and "mermaid-rendered" in classes:
            self._baked_line = self.getpos()[0]
            self.baked_blocks.append({"line": self._baked_line, "hidden": self._hidden_ancestors(), "has_svg": False})
        if tag == "script":
            self._script_line = self.getpos()[0]
            self._script_buf = []
        if tag not in _VOID:
            self._push(tag, mapping)

    def handle_startendtag(self, tag, attrs):
        tag = tag.lower()
        mapping = _attrs(attrs)
        classes = mapping.get("class", "").split()
        if tag == "svg":
            self._mark_baked_svg()
        if tag == "pre" and "mermaid" in classes:
            self.mermaid_blocks.append({"line": self.getpos()[0], "hidden": self._hidden_ancestors(), "has_svg": False})
        if tag == "div" and "mermaid-rendered" in classes:
            self.baked_blocks.append({"line": self.getpos()[0], "hidden": self._hidden_ancestors(), "has_svg": False})

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "script" and self._script_buf is not None:
            text = "".join(self._script_buf)
            self.script_blocks.append({"line": self._script_line, "text": text})
            self._script_buf = None
        self._pop(tag)

    def handle_data(self, data):
        if self._script_buf is not None:
            self._script_buf.append(data)


def _error(code: str, line: int, message: str, hint: str) -> dict:
    return {"severity": "error", "code": code, "line": line, "message": message, "hint": hint}


def _warning(code: str, line: int, message: str, hint: str) -> dict:
    return {"severity": "warning", "code": code, "line": line, "message": message, "hint": hint}


def analyse(html: str) -> dict:
    scanner = _Scanner()
    scanner.feed(html)
    findings: list[dict] = []

    inlined = LIBRARY_MARKER in html
    custom_scripts = [s for s in scanner.script_blocks if LIBRARY_MARKER not in s["text"]]

    for block in scanner.mermaid_blocks:
        if block["hidden"]:
            findings.append(
                _error(
                    "diagram_in_hidden",
                    block["line"],
                    "mermaid 源码块在隐藏容器里, 渲染时量不到宽度, 展开后也容易停在源码上",
                    "把图移到不折叠的正文; 或先渲染再折叠",
                )
            )
    if scanner.mermaid_blocks and not inlined:
        findings.append(
            _error(
                "mermaid_not_inlined",
                0,
                f"页面有 {len(scanner.mermaid_blocks)} 个 mermaid 源码块, 但渲染库没有内联",
                "运行 scripts/embed_mermaid.py <html-file>",
            )
        )

    for block in scanner.baked_blocks:
        if not block["has_svg"]:
            findings.append(
                _error(
                    "baked_svg_missing",
                    block["line"],
                    ".mermaid-rendered 容器里没有 svg",
                    "重新预渲染, 或改回内联库的运行时渲染",
                )
            )
        if block["hidden"]:
            findings.append(
                _warning(
                    "baked_in_hidden",
                    block["line"],
                    "静态图放在折叠容器里, 读者不展开就看不到",
                    "确认这是有意的; 否则把它移出折叠块",
                )
            )

    for script in custom_scripts:
        if "mermaid.run(" in script["text"]:
            findings.append(
                _error(
                    "manual_rerender",
                    script["line"],
                    "页面脚本自己调用 mermaid.run, 属于二次渲染",
                    "图只渲染一次; 删掉重画逻辑, 把图移出隐藏容器",
                )
            )

    if scanner.baked_blocks and inlined:
        findings.append(
            _warning(
                "library_unused",
                0,
                "已有静态图却仍内联渲染库 (约 3.5MB)",
                "删掉库与初始化脚本, 或用 --keep-library 保留以便继续编辑",
            )
        )

    errors = [f for f in findings if f["severity"] == "error"]
    return {
        "success": not errors,
        "command": CHECK_COMMAND,
        "counts": {
            "mermaid_blocks": len(scanner.mermaid_blocks),
            "baked_blocks": len(scanner.baked_blocks),
            "custom_scripts": len(custom_scripts),
            "library_inlined": inlined,
        },
        "findings": findings,
    }


def run_check(html_file: str) -> dict:
    path = Path(html_file)
    if not path.is_file():
        return {
            "success": False,
            "command": CHECK_COMMAND,
            "error": {"code": "html_not_found", "message": f"html file not found: {html_file}"},
            "findings": [],
        }
    try:
        html = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {
            "success": False,
            "command": CHECK_COMMAND,
            "error": {"code": "html_unreadable", "message": str(exc)},
            "findings": [],
        }
    result = analyse(html)
    result["html_file"] = str(path)
    return result


def main(argv=None) -> int:
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    try:
        if not argv:
            payload = {
                "success": False,
                "command": CHECK_COMMAND,
                "error": {
                    "code": "usage",
                    "message": "Usage: check_page.py <html-file>",
                },
                "findings": [],
            }
        else:
            payload = run_check(argv[0])
    except Exception as exc:  # noqa: BLE001 - CLI 边界统一转 JSON
        payload = {
            "success": False,
            "command": CHECK_COMMAND,
            "error": {"code": "internal_error", "message": str(exc)},
            "findings": [],
        }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0 if payload["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
