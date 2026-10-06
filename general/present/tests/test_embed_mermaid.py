"""embed_mermaid.py 契约与幂等测试."""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "embed_mermaid.py"


def _load():
    spec = importlib.util.spec_from_file_location("embed_mermaid", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


em = _load()

_PAGE = """<!DOCTYPE html>
<html><body>
<pre class="mermaid">
graph TD; A-->B;
</pre>
</body></html>
"""


class TestEmbedMermaid(unittest.TestCase):
    def _write(self, text):
        f = Path(tempfile.mkdtemp(prefix="present-embed-")) / "p.html"
        f.write_text(text, encoding="utf-8")
        return f

    def test_no_mermaid_block_is_noop(self):
        f = self._write("<!DOCTYPE html><html><body><p>plain</p></body></html>")
        before = f.read_text(encoding="utf-8")
        result = em.run_embed(str(f))
        self.assertTrue(result["success"])
        self.assertFalse(result["injected"])
        self.assertEqual(result["reason"], "no_mermaid_block")
        self.assertEqual(f.read_text(encoding="utf-8"), before)

    def test_inject_inlines_library_before_body_close(self):
        f = self._write(_PAGE)
        result = em.run_embed(str(f))
        self.assertTrue(result["success"])
        self.assertTrue(result["injected"])
        text = f.read_text(encoding="utf-8")
        self.assertIn(em.MARKER, text)
        self.assertIn("globalThis", text)
        self.assertIn("mermaid.initialize", text)
        self.assertLess(text.index(em.MARKER), text.index("</body>"))
        self.assertIn('<pre class="mermaid">', text)

    def test_idempotent(self):
        f = self._write(_PAGE)
        em.run_embed(str(f))
        result = em.run_embed(str(f))
        self.assertTrue(result["success"])
        self.assertFalse(result["injected"])
        self.assertEqual(result["reason"], "already_inlined")
        self.assertEqual(f.read_text(encoding="utf-8").count(em.MARKER), 1)

    def test_missing_file_fails(self):
        result = em.run_embed("/no/such/page.html")
        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "html_not_found")

    def test_cli_emits_single_line_json(self):
        f = self._write(_PAGE)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = em.main([str(f)])
        self.assertEqual(code, 0)
        lines = buf.getvalue().strip().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(json.loads(lines[0])["success"])

    def test_cli_usage_failure(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = em.main([])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(buf.getvalue().strip())["success"])


if __name__ == "__main__":
    unittest.main()
