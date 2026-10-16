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

# 历史脚本名含连字符, 按所在目录加载, 同步后不依赖 cwd 或 sys.path.
_spec = importlib.util.spec_from_file_location("to_spec_check_ac", Path(__file__).with_name("check-ac.py"))
checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checker)


def review_id(base: bytes, draft: bytes) -> str:
    """同时绑定产品上下文与用例, 防止同编号下的规则改动逃过版本检查."""
    return hashlib.sha256(len(base).to_bytes(8, "big") + base + draft).hexdigest()


def _inputs(base: Path, draft: Path) -> tuple[bytes, bytes]:
    return base.read_bytes(), draft.read_bytes()


def _page(draft: str, name: str, review: str) -> str:
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
h1, h2 {{ font-weight: 500; line-height: 1.4; margin-top: 2.5rem; }}
a {{ color: #46645a; text-underline-offset: .2em; }}
nav ul {{ padding-left: 1.3rem; }}
pre {{ white-space: pre-wrap; overflow-wrap: anywhere; font-size: .95rem; }}
code {{ font-family: inherit; overflow-wrap: anywhere; }}
small {{ color: #625f55; }}
</style>
</head>
<body>
<header><p>待确认草稿</p><h1>验收用例草稿</h1></header>
<nav aria-label="目录"><ul><li><a href="#review">审阅说明与原文件</a></li>
<li><a href="#content">草稿原文</a></li></ul></nav>
<section id="review"><h2>审阅说明与原文件</h2>
<p>下文由草稿直接转为安全文本, 没有改写或删减. 请在 chat 中确认采用这一版, 或指出需要修改的用例.</p>
<p><a href="{source}">打开草稿原文件</a>. 服务不渲染 Markdown, 浏览器也可能下载原文件.</p>
<p><small>审阅版本: <code>{review}</code>. 产品上下文或草稿变化后需要重新展示和确认.</small></p>
</section>
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
    with output.open("xb") as stream:
        stream.write(_page(draft_bytes.decode("utf-8"), draft.name, review).encode("utf-8"))
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
