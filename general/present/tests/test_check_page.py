"""check_page.py 契约测试: 抓"图表退化成源码"的回归.

用例对应 2026-10-26 事故: 图放进折叠容器 + 页面脚本自己二次渲染.
Run: uv run python -m pytest general/present/tests/test_check_page.py -q
"""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "check_page.py"
)
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def _load():
    spec = importlib.util.spec_from_file_location("check_page", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cp = _load()

_LIB = '<script>/* pi-present-mermaid-inline */ var mermaid = {};</script>'
_SRC_BLOCK = '<pre class="mermaid">\nflowchart TD\n  A-->B\n</pre>'
_BAKED = '<div class="mermaid-rendered"><svg viewBox="0 0 10 10"></svg></div>'


def _page(body: str) -> str:
    return "<!DOCTYPE html><html><body>\n" + body + "\n</body></html>"


class TestAnalysis(unittest.TestCase):
    def _codes(self, result):
        return [finding["code"] for finding in result["findings"]]

    def test_plain_page_passes(self):
        result = cp.analyse(_page("<p>hello</p>"))
        self.assertTrue(result["success"])
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["counts"]["mermaid_blocks"], 0)

    def test_source_block_in_body_with_library_passes(self):
        result = cp.analyse(_page(_SRC_BLOCK + _LIB))
        self.assertTrue(result["success"])
        self.assertEqual(result["counts"]["mermaid_blocks"], 1)
        self.assertTrue(result["counts"]["library_inlined"])

    def test_source_block_in_opened_details_passes(self):
        body = "<details open><summary>s</summary>" + _SRC_BLOCK + "</details>" + _LIB
        result = cp.analyse(_page(body))
        self.assertTrue(result["success"], result["findings"])

    def test_source_block_in_closed_details_is_error(self):
        body = "<details><summary>s</summary>" + _SRC_BLOCK + "</details>" + _LIB
        result = cp.analyse(_page(body))
        self.assertFalse(result["success"])
        self.assertIn("diagram_in_hidden", self._codes(result))

    def test_source_block_in_hidden_attribute_is_error(self):
        body = '<div hidden>' + _SRC_BLOCK + "</div>" + _LIB
        result = cp.analyse(_page(body))
        self.assertIn("diagram_in_hidden", self._codes(result))

    def test_source_block_in_display_none_is_error(self):
        body = '<section style="display: none">' + _SRC_BLOCK + "</section>" + _LIB
        result = cp.analyse(_page(body))
        self.assertIn("diagram_in_hidden", self._codes(result))

    def test_source_block_without_library_is_error(self):
        result = cp.analyse(_page(_SRC_BLOCK))
        self.assertFalse(result["success"])
        self.assertIn("mermaid_not_inlined", self._codes(result))

    def test_baked_svg_passes(self):
        result = cp.analyse(_page(_BAKED))
        self.assertTrue(result["success"])
        self.assertEqual(result["counts"]["baked_blocks"], 1)

    def test_baked_container_without_svg_is_error(self):
        result = cp.analyse(_page('<div class="mermaid-rendered"><p>空</p></div>'))
        self.assertFalse(result["success"])
        self.assertIn("baked_svg_missing", self._codes(result))

    def test_baked_in_details_is_only_warning(self):
        body = "<details><summary>s</summary>" + _BAKED + "</details>"
        result = cp.analyse(_page(body))
        self.assertTrue(result["success"])
        self.assertIn("baked_in_hidden", self._codes(result))

    def test_baked_with_library_is_warning(self):
        result = cp.analyse(_page(_BAKED + _LIB))
        self.assertTrue(result["success"])
        self.assertIn("library_unused", self._codes(result))

    def test_custom_script_rerender_is_error(self):
        script = "<script>mermaid.run({ nodes: [pre] });</script>"
        result = cp.analyse(_page(_SRC_BLOCK + _LIB + script))
        self.assertFalse(result["success"])
        self.assertIn("manual_rerender", self._codes(result))

    def test_library_own_run_call_is_not_flagged(self):
        lib = '<script>/* pi-present-mermaid-inline */ function f(){ mermaid.run({}); }</script>'
        result = cp.analyse(_page(_SRC_BLOCK + lib))
        self.assertTrue(result["success"], result["findings"])


class TestIncidentFixture(unittest.TestCase):
    """2026-10-26 事故文件必须继续被抓到, 防止检查器静默退化."""

    def test_incident_page_reports_both_defects(self):
        fixture = FIXTURE_DIR / "incident-2026-10-26-diagram-in-details.html"
        result = cp.run_check(str(fixture))
        codes = [finding["code"] for finding in result["findings"]]
        self.assertFalse(result["success"])
        self.assertIn("diagram_in_hidden", codes)
        self.assertIn("manual_rerender", codes)


class TestCli(unittest.TestCase):
    def _write(self, text):
        path = Path(tempfile.mkdtemp(prefix="present-check-")) / "p.html"
        path.write_text(text, encoding="utf-8")
        return path

    def _run(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cp.main(argv)
        return code, json.loads(buf.getvalue())

    def test_success_page_exits_zero(self):
        path = self._write(_page(_BAKED))
        code, payload = self._run([str(path)])
        self.assertEqual(code, 0)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["html_file"], str(path))

    def test_error_page_exits_one(self):
        path = self._write(_page("<details>" + _SRC_BLOCK + "</details>" + _LIB))
        code, payload = self._run([str(path)])
        self.assertEqual(code, 1)
        self.assertFalse(payload["success"])

    def test_missing_file_exits_one(self):
        code, payload = self._run(["/nonexistent/page.html"])
        self.assertEqual(code, 1)
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"]["code"], "html_not_found")

    def test_usage_without_args(self):
        code, payload = self._run([])
        self.assertEqual(code, 1)
        self.assertEqual(payload["error"]["code"], "usage")


if __name__ == "__main__":
    unittest.main()
