"""present Mermaid 内联 helper.

用法:
  embed_mermaid.py <html-file>

页面用 `<pre class="mermaid">...</pre>` 写图表. 本脚本把 `vendor/mermaid.min.js`
内联进 HTML 末尾, 页面保持单文件自包含, `file://` 可开, 远程/容器通用.

stdout: 单行 JSON. Exit 0 success, 非零失败. 无 mermaid 块或已内联时幂等跳过.
"""

import json
import re
import sys
from pathlib import Path

MARKER = "pi-present-mermaid-inline"
_MERMAID_BLOCK = re.compile(r'class\s*=\s*["\'][^"\']*\bmermaid\b')
_BODY_CLOSE = re.compile(r"</body\s*>", re.IGNORECASE)


def _vendor_path():
    return Path(__file__).resolve().parent.parent / "vendor" / "mermaid.min.js"


def _err(code, error):
    return {"success": False, "command": "embed", "code": code, "error": error}


def _snippet():
    lib = _vendor_path().read_text(encoding="utf-8")
    return (
        "<script>\n/* " + MARKER + " */\n" + lib + "\n</script>\n"
        "<script>mermaid.initialize({ startOnLoad: true });</script>\n"
    )


def run_embed(html_file):
    path = Path(html_file)
    if not path.is_file():
        return _err("html_not_found", f"html file not found: {html_file}")
    html = path.read_text(encoding="utf-8")
    if not _MERMAID_BLOCK.search(html):
        return {"success": True, "command": "embed", "injected": False,
                "reason": "no_mermaid_block", "html_file": str(path)}
    if MARKER in html:
        return {"success": True, "command": "embed", "injected": False,
                "reason": "already_inlined", "html_file": str(path)}
    if not _vendor_path().is_file():
        return _err("vendor_missing", f"mermaid library not found: {_vendor_path()}")
    snippet = _snippet()
    last = None
    for last in _BODY_CLOSE.finditer(html):
        pass
    if last is not None:
        html = html[:last.start()] + snippet + html[last.start():]
    else:
        html = html + "\n" + snippet
    path.write_text(html, encoding="utf-8")
    return {"success": True, "command": "embed", "injected": True,
            "html_file": str(path), "bytes_added": len(snippet.encode("utf-8"))}


def main(argv=None):
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    try:
        if not argv:
            obj = _err("internal_error", "Usage: embed_mermaid.py <html-file>")
        else:
            obj = run_embed(argv[0])
    except Exception as e:
        obj = _err("internal_error", str(e))
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0 if obj["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
