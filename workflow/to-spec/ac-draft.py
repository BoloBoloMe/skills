# /// script
# requires-python = ">=3.10"
# dependencies = ["gherkin-official>=42.0.1"]
# ///
"""验收草稿的机械预览与原文转正, 复用 check-ac.py 的全部校验.

preview <PRODUCT 暂存稿> <验收草稿>
promote <PRODUCT 暂存稿> <验收草稿> <PRODUCT.md> --review <审阅版本>
stdout 为单个 JSON. 退出码 0 成功 / 1 机检失败 / 2 输入或文件操作失败.
审阅版本只绑定输入字节, 不证明我已确认; 调用方负责等待 chat 中的明确采纳.
"""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import html
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from urllib.parse import quote
from uuid import uuid4

from gherkin.pickles.compiler import Compiler

# 历史脚本名含连字符, 按所在目录加载, 同步后不依赖 cwd 或 sys.path.
_spec = importlib.util.spec_from_file_location("to_spec_check_ac", Path(__file__).with_name("check-ac.py"))
checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checker)


def review_id(base: bytes, draft: bytes) -> str:
    """同时绑定产品上下文与用例, 防止同编号下的规则改动逃过版本检查."""
    return hashlib.sha256(len(base).to_bytes(8, "big") + base + draft).hexdigest()


def _inputs(base: Path, draft: Path) -> tuple[bytes, bytes]:
    return base.read_bytes(), draft.read_bytes()


def _table(rows: list[dict], cell_class: str, *, header: bool = False) -> str:
    output = []
    for row in rows:
        tag = "th" if header else "td"
        cells = "".join(f'<{tag} class="{cell_class}">{html.escape(cell["value"])}</{tag}>'
                        for cell in row["cells"])
        output.append(f"<tr>{cells}</tr>")
    return "".join(output)


def _arguments(argument: dict) -> str:
    output = []
    # Gherkin 支持同一步骤的表格与多行文本, 按官方展开结果的顺序显示.
    for kind in sorted(argument, key=lambda key: argument[key].get("argumentIndex", 0)):
        value = argument[kind]
        if kind == "dataTable":
            output.append('<div class="table-wrap"><table class="argument-table"><tbody>'
                          + _table(value["rows"], "argument-cell") + '</tbody></table></div>')
        elif kind == "docString":
            if "mediaType" in value:
                output.append('<p>文本类型: <span class="docstring-media">'
                              + html.escape(value["mediaType"] or "") + '</span></p>')
            output.append('<pre class="docstring-content">'
                          + html.escape(value["content"] or "") + '</pre>')
        else:
            raise checker.ValidationError(f"无法完整展示步骤附加内容: {kind}")
    return "".join(output)


def _step(step: dict, source: dict, background: dict[str, str]) -> str:
    labels = {"Context": "已有情况", "Action": "做这件事", "Outcome": "应该看到"}
    if step["type"] not in labels:
        raise checker.ValidationError(f"草稿第 {source['location']['line']} 行无法确定步骤阶段")
    notes = []
    if source["id"] in background:
        name = background[source["id"]]
        notes.append(f"共享前提: {name}" if name else "共享前提")
    keyword = source["keyword"].strip()
    if keyword in ("而且", "但是"):
        notes.append(keyword)
    note = f'<small class="step-note">{html.escape(" / ".join(notes))}</small>' if notes else ""
    return (f'<li data-source-line="{source["location"]["line"]}">'
            f'<div><strong class="step-label">{labels[step["type"]]}</strong>{note}</div>'
            f'<div class="step-body"><span class="step-text">{html.escape(step["text"])}</span>'
            + _arguments(step.get("argument", {})) + '</div></li>')


def _reading_view(markdown: str, draft: str) -> str:
    """官方编译器展开共享前提与每组数据, 展示原句, 不做自然语言改写."""
    match = checker.FENCE_RE.search(draft)
    # 调用前已通过 validate_draft, 补空行让位置指向草稿原文件.
    document = checker.Parser().parse("\n" * draft[:match.start(1)].count("\n") + match[1],
                                      checker.TokenMatcher("zh-CN"))
    feature = document["feature"]
    sources, background, rows = {}, {}, {}
    scenarios = []
    for child in feature["children"]:
        if "background" in child:
            node = child["background"]
            for step in node["steps"]:
                sources[step["id"]] = step
                background[step["id"]] = node["name"]
        else:
            node = child["scenario"]
            scenarios.append(node)
            if not node["steps"]:
                raise checker.ValidationError(f"场景 {node['name']!r} 无步骤, 不能生成完整阅读卡片")
            for step in node["steps"]:
                sources[step["id"]] = step
            if node["keyword"] == "场景大纲" and not node["examples"]:
                raise checker.ValidationError(f"场景大纲 {node['name']!r} 缺少例子数据")
            for example in node["examples"]:
                if not example.get("tableHeader") or not example["tableBody"]:
                    raise checker.ValidationError(f"场景 {node['name']!r} 的例子缺少表头或数据行")
                for row in example["tableBody"]:
                    rows[row["id"]] = (example, row)
    if not scenarios:
        raise checker.ValidationError("草稿没有可展示的场景")
    try:
        cases = Compiler().compile({**document, "uri": "draft.feature"})
    except Exception as exc:
        raise checker.ValidationError(f"Gherkin 数据展开失败: {exc}") from exc
    expected = sum(sum(len(ex["tableBody"]) for ex in sc["examples"])
                   if sc["examples"] else 1 for sc in scenarios)
    if len(cases) != expected:
        raise checker.ValidationError("Gherkin 数据未完整展开, 停止生成预览")

    entries = {"G": checker.extract_entry_texts(markdown, "目标"),
               "BR": checker.extract_entry_texts(markdown, "业务规则")}
    output = [f'<h2>{html.escape(feature["name"])}</h2>',
              f'<p>{len(scenarios)} 个场景, 展开为 {len(cases)} 张阅读卡片. 同一验收编号的分支和数据不另编编号.</p>']
    if document["comments"]:
        output.append('<aside aria-label="草稿注释"><h3>草稿注释 (原文)</h3>')
        lines = draft.splitlines()
        for comment in document["comments"]:
            text = lines[comment["location"]["line"] - 1]
            output.append(f'<pre class="source-comment">{html.escape(text)}</pre>')
        output.append('</aside>')
    type_names = {"@normal": "正常情况", "@failure": "失败情况", "@edge": "边界情况"}
    for index, case in enumerate(cases, 1):
        tags = list(dict.fromkeys(tag["name"] for tag in case["tags"]))
        ac = next(tag[1:] for tag in tags if checker.AC_TAG_RE.fullmatch(tag))
        meta = " / ".join([ac, f"阅读卡片 {index}"] + [type_names[tag] for tag in tags if tag in type_names])
        output.append(f'<article class="acceptance-card" id="case-{index}" data-ac="{ac}">'
                      f'<p class="case-meta">{meta}</p>'
                      f'<h3 class="case-title">{html.escape(case["name"])}</h3>')
        if len(case["astNodeIds"]) > 1:
            example, row = rows[case["astNodeIds"][1]]
            output.append('<section class="example-data"><h4>本组数据</h4>'
                          f'<p class="example-name">{html.escape(example["name"])}</p>'
                          '<div class="table-wrap"><table><thead>'
                          + _table([example["tableHeader"]], "example-header", header=True)
                          + '</thead><tbody>' + _table([row], "example-value")
                          + '</tbody></table></div></section>')
        output.append('<ol class="steps">')
        for step in case["steps"]:
            output.append(_step(step, sources[step["astNodeIds"][0]], background))
        output.append('</ol><aside class="references"><h4>对应目标与业务规则 (原文)</h4>')
        for tag in tags:
            if tag.startswith(("@G-", "@BR-")):
                key = tag[1:]
                text = entries[key.split("-")[0]][key]
                output.append(f'<p class="reference-text">{html.escape(text)}</p>')
        output.append('</aside></article>')
    return "".join(output)


def _page(markdown: str, draft: str, name: str, review: str) -> str:
    reading = _reading_view(markdown, draft)
    source = html.escape(quote(name), quote=True)
    content = html.escape(draft)
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>验收用例草稿</title>
<style>
:root {{ color-scheme: light; background: #f8f6ef; color: #302e29; }}
body {{ max-width: 64rem; margin: 3rem auto; padding: 0 1.25rem 4rem;
  font-family: "Noto Serif CJK SC", "Source Han Serif SC", Spectral, serif; line-height: 1.8; }}
h1, h2, h3 {{ font-weight: 500; line-height: 1.4; }}
h1, h2 {{ margin-top: 2.5rem; }}
h3 {{ margin-top: .5rem; }}
h4 {{ margin: .8rem 0; }}
a {{ color: #46645a; text-underline-offset: .2em; }}
nav ul {{ padding-left: 1.3rem; }}
pre, .step-text, .reference-text, .case-title, .example-name, .step-note, td, th {{
  white-space: pre-wrap; overflow-wrap: anywhere; }}
pre {{ font-size: .95rem; }}
pre, code {{ font-family: inherit; }}
code {{ overflow-wrap: anywhere; }}
small, .case-meta {{ color: #625f55; }}
.acceptance-card {{ background: #fffdf8; border: 1px solid #d8d3c6; border-radius: .6rem;
  margin: 1.5rem 0; padding: 1.5rem; scroll-margin-top: 1rem; }}
.case-meta {{ font-size: .9rem; margin: 0; }}
.steps {{ list-style: none; padding: 0; }}
.steps > li {{ display: grid; grid-template-columns: 7rem minmax(0, 1fr); gap: 1rem;
  padding: .8rem 0; border-top: 1px solid #e6e1d6; }}
.step-note {{ display: block; font-size: .85rem; }}
.step-body {{ min-width: 0; }}
.references {{ border-top: 1px solid #d8d3c6; margin-top: 1rem; }}
.reference-text {{ margin: .6rem 0; }}
.table-wrap {{ overflow-x: auto; margin: .8rem 0; }}
table {{ border-collapse: collapse; width: 100%; text-align: left; }}
td, th {{ border: 1px solid #d8d3c6; padding: .5rem .7rem; min-width: 4rem; }}
th {{ background: #f0ede4; }}
.docstring-content {{ border-left: 3px solid #d8d3c6; padding-left: 1rem; }}
@media (max-width: 40rem) {{
  body {{ margin-top: 1.5rem; }}
  .acceptance-card {{ padding: 1rem; }}
  .steps > li {{ grid-template-columns: 1fr; gap: .3rem; }}
}}
</style>
</head>
<body>
<header><p>待确认草稿</p><h1>验收用例草稿</h1></header>
<nav aria-label="目录"><ul><li><a href="#review">审阅说明与原文件</a></li>
<li><a href="#reading">阅读卡片</a></li><li><a href="#content">草稿原文</a></li></ul></nav>
<section id="review"><h2>审阅说明与原文件</h2>
<p>这是同一份验收正文的阅读排版, 不是摘要. 共享前提已放入每张卡片, 例子按 Gherkin 规则逐组代入, 表格, 多行文本与引用规则就地显示, 原句不做改写.</p>
<p>请在 chat 中确认采用这一版, 或指出需要修改的用例. 如果正文仍然难懂, 应修改原用例并重新展示, 不以另一份解释代替确认.</p>
<p><a href="{source}">打开草稿原文件</a>. 页面末尾也保留草稿全文, 便于对照.</p>
<p><small>审阅版本: <code>{review}</code>. 产品上下文或草稿变化后需要重新展示和确认, 采纳后仍原样转正.</small></p>
</section>
<section id="reading" aria-label="阅读卡片">{reading}</section>
<section id="content"><h2>草稿原文</h2>
<pre id="draft-content"><code>{content}</code></pre>
</section>
<script>window.__PRESENTATION_STATE__ = {{ version: 1, values: {{}} }};</script>
</body>
</html>
'''


def preview(base: Path, draft: Path) -> dict:
    base, draft = base.absolute(), draft.absolute()
    base_bytes, draft_bytes = _inputs(base, draft)
    checker.validate_draft(base_bytes.decode("utf-8"), draft_bytes.decode("utf-8"))
    review = review_id(base_bytes, draft_bytes)
    # 唯一文件名, 新预览不会覆盖我正在看的旧版本; 原文件不另作 LLM 副本.
    output = draft.with_name(f"{date.today().isoformat()}-acceptance-{review[:12]}-{uuid4().hex[:8]}.html")
    page = _page(base_bytes.decode("utf-8"), draft_bytes.decode("utf-8"), draft.name, review)
    with output.open("xb") as stream:
        stream.write(page.encode("utf-8"))
    return {"success": True, "command": "preview", "draft": str(draft),
            "preview": str(output), "review_id": review}


def _existing(path: Path) -> bytes | None:
    if path.is_symlink():
        raise checker.InputError("正式文件不能是符号链接")
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def _atomic_write(path: Path, content: bytes, previous: bytes | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if previous is not None else None
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if mode is not None:
            temporary.chmod(mode)
        if _existing(path) != previous:
            raise checker.InputError("正式文件在转正过程中已变化, 保留当前文件并停止")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def promote(base: Path, draft: Path, output: Path, review: str) -> dict:
    base, draft, output = base.absolute(), draft.absolute(), output.absolute()
    if output.resolve() in (base.resolve(), draft.resolve()):
        raise checker.InputError("正式输出必须与 PRODUCT 暂存稿及验收草稿分开")
    previous = _existing(output)
    base_bytes, draft_bytes = _inputs(base, draft)
    if review_id(base_bytes, draft_bytes) != review:
        raise checker.InputError("审阅版本不匹配, 产品上下文或草稿已变化; 请重新展示并确认")
    markdown, draft_text = base_bytes.decode("utf-8"), draft_bytes.decode("utf-8")
    checker.validate_draft(markdown, draft_text)
    candidate = checker.with_draft(markdown, draft_text, confirmed=True)
    checker.validate_product(candidate)
    # 全程用同一份已校验的字节构造结果; 发现输入在验证期间变化则停止.
    if _inputs(base, draft) != (base_bytes, draft_bytes):
        raise checker.InputError("输入在转正过程中已变化, 请重新展示并确认")
    _atomic_write(output, candidate.encode("utf-8"), previous)
    return {"success": True, "command": "promote", "output": str(output), "review_id": review}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preview", "promote"):
        command = commands.add_parser(name)
        command.add_argument("base", type=Path, help="PRODUCT 暂存稿, 提供目标/业务规则及其他正文")
        command.add_argument("draft", type=Path, help="只含最终 Gherkin 块的验收正文草稿")
        if name == "promote":
            command.add_argument("output", type=Path, help="正式 PRODUCT.md 路径")
            command.add_argument("--review", required=True, help="我明确确认的预览所返回的 review_id")
    args = parser.parse_args()
    try:
        if args.command == "preview":
            result = preview(args.base, args.draft)
        else:
            result = promote(args.base, args.draft, args.output, args.review)
    except checker.ValidationError as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    except (checker.InputError, OSError, UnicodeError) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
