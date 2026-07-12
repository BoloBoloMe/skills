"""真实 Chromium 验收测试.

显式运行:
  ADAPTIVE_PRESENTATION_REAL_BROWSER=1 python -m unittest \
    general/adaptive-presentation/tests/test_browser_session_integration.py -v
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "browser_session.py"
ACCESS_WEB_BROWSE = SKILL_DIR.parent / "access-web" / "browse"
RUN_REAL_BROWSER = os.environ.get("ADAPTIVE_PRESENTATION_REAL_BROWSER") == "1"


@unittest.skipUnless(RUN_REAL_BROWSER, "set ADAPTIVE_PRESENTATION_REAL_BROWSER=1")
class TestRealBrowserLifecycle(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory(prefix="pi-presentation-视觉-")
        self.session_dir = Path(self.tempdir.name).resolve()

    def tearDown(self):
        self._cleanup_browser()
        self.tempdir.cleanup()

    def _run(self, command, *args):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), command, *map(str, args)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        self.assertEqual(lines and len(lines), 1, completed.stdout + completed.stderr)
        payload = json.loads(lines[0])
        return completed.returncode, payload

    def _cleanup_browser(self):
        sys.path.insert(0, str(ACCESS_WEB_BROWSE))
        try:
            from browser_agent.session import cleanup_browser_session
            cleanup_browser_session(cwd=str(self.session_dir))
        finally:
            try:
                sys.path.remove(str(ACCESS_WEB_BROWSE))
            except ValueError:
                pass

    def _browser_command_line(self):
        sys.path.insert(0, str(ACCESS_WEB_BROWSE))
        try:
            from browser_agent.config import BrowserConfig
            pid = BrowserConfig(cwd=str(self.session_dir)).read_metadata()["pid"]
        finally:
            sys.path.remove(str(ACCESS_WEB_BROWSE))

        if os.name == "nt":
            completed = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-Command",
                    f'(Get-CimInstance Win32_Process -Filter "ProcessId = {pid}").CommandLine',
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )
            return completed.stdout
        proc_cmdline = Path(f"/proc/{pid}/cmdline")
        if proc_cmdline.exists():
            return proc_cmdline.read_bytes().replace(b"\0", b" ").decode()
        completed = subprocess.run(
            ["ps", "-p", str(pid), "-o", "args="],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return completed.stdout

    def _connect_page(self):
        sys.path.insert(0, str(ACCESS_WEB_BROWSE))
        try:
            from browser_agent.config import BrowserConfig
            from playwright.sync_api import sync_playwright

            config = BrowserConfig(cwd=str(self.session_dir))
            port = config.read_metadata()["cdp_port"]
            playwright = sync_playwright().start()
            browser = playwright.chromium.connect_over_cdp(
                f"http://127.0.0.1:{port}"
            )
            page = browser.contexts[0].pages[0]
            return playwright, browser, page
        finally:
            try:
                sys.path.remove(str(ACCESS_WEB_BROWSE))
            except ValueError:
                pass

    def _write_page(self, name, title, selected):
        external_text = '<img src=x onerror="document.body.dataset.pwned=1">'
        escaped_text = external_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: sans-serif; color: #202124; background: #f7f7f8; }}
main {{ width: min(100% - 24px, 760px); margin: 24px auto; }}
h1 {{ font-size: 24px; margin: 0 0 16px; }}
.choices {{ display: flex; flex-wrap: wrap; gap: 8px; }}
button {{ min-height: 40px; padding: 8px 14px; border: 2px solid #444; background: white; color: #202124; }}
button[aria-pressed="true"] {{ border-style: double; background: #d9ead3; }}
#status {{ margin-top: 16px; overflow-wrap: anywhere; }}
</style>
</head>
<body>
<main>
<h1>{title}</h1>
<div class="choices" role="group" aria-label="方案">
<button id="a" type="button" aria-pressed="{'true' if selected == 'A' else 'false'}">方案 A</button>
<button id="b" type="button" aria-pressed="{'true' if selected == 'B' else 'false'}">方案 B</button>
</div>
<p id="status" role="status">✓ 当前选择: <strong>{selected}</strong>. 外部文本: {escaped_text}</p>
</main>
<script>
window.__PRESENTATION_STATE__ = {{version: 1, values: {{selected: {json.dumps(selected)}}}}};
for (const button of document.querySelectorAll('button')) {{
  button.addEventListener('click', () => {{
    const value = button.id.toUpperCase();
    window.__PRESENTATION_STATE__.values.selected = value;
    for (const item of document.querySelectorAll('button')) item.setAttribute('aria-pressed', String(item === button));
    document.querySelector('#status strong').textContent = value;
  }});
}}
</script>
</body>
</html>"""
        path = self.session_dir / name
        path.write_text(html, encoding="utf-8")
        return path

    def test_headed_cross_process_lifecycle_and_representative_page(self):
        first = self._write_page("关系 页面-v1.html", "关系视图 v1", "A")
        second = self._write_page("关系 页面-v2.html", "关系视图 v2", "B")

        code, opened = self._run("open", self.session_dir, first)
        self.assertEqual(code, 0)
        self.assertTrue(opened["alive"])
        self.assertEqual(opened["url"], first.as_uri())

        code, state = self._run("state", self.session_dir)
        self.assertEqual(code, 0)
        self.assertEqual(state["state"], {"version": 1, "values": {"selected": "A"}})

        playwright, browser, page = self._connect_page()
        try:
            self.assertEqual(len(browser.contexts[0].pages), 1)
            self.assertNotIn("--headless", self._browser_command_line())
            self.assertEqual(page.locator("img").count(), 0)
            self.assertIsNone(page.locator("body").get_attribute("data-pwned"))
            for width in (360, 1440):
                page.set_viewport_size({"width": width, "height": 800})
                layout = page.evaluate("""() => ({
                    overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
                    mainRight: document.querySelector('main').getBoundingClientRect().right,
                    viewport: document.documentElement.clientWidth
                })""")
                self.assertFalse(layout["overflow"])
                self.assertLessEqual(layout["mainRight"], layout["viewport"])
            page.locator("#b").focus()
            page.keyboard.press("Enter")
        finally:
            playwright.stop()

        code, keyboard_state = self._run("state", self.session_dir)
        self.assertEqual(code, 0)
        self.assertEqual(keyboard_state["state"]["values"]["selected"], "B")

        code, reopened = self._run("open", self.session_dir, second)
        self.assertEqual(code, 0)
        self.assertEqual(reopened["url"], second.as_uri())
        code, status = self._run("status", self.session_dir)
        self.assertEqual(code, 0)
        self.assertTrue(status["alive"])
        self.assertEqual(status["url"], second.as_uri())

        playwright, browser, page = self._connect_page()
        try:
            self.assertEqual(len(browser.contexts[0].pages), 1)
            self.assertEqual(page.title(), "关系视图 v2")
        finally:
            playwright.stop()

        self._cleanup_browser()
        code, stopped_state = self._run("state", self.session_dir)
        self.assertNotEqual(code, 0)
        self.assertEqual(stopped_state["code"], "browser_not_running")
        code, stopped_status = self._run("status", self.session_dir)
        self.assertEqual(code, 0)
        self.assertFalse(stopped_status["alive"])

        code, recovered = self._run("open", self.session_dir, first)
        self.assertEqual(code, 0)
        self.assertTrue(recovered["alive"])

        sys.path.insert(0, str(ACCESS_WEB_BROWSE))
        try:
            from browser_agent.config import BrowserConfig
            project = BrowserConfig(cwd=str(SKILL_DIR.parent.parent))
            presentation = BrowserConfig(cwd=str(self.session_dir))
            self.assertNotEqual(project.session_key, presentation.session_key)
            self.assertNotEqual(project.profile_dir, presentation.profile_dir)
        finally:
            sys.path.remove(str(ACCESS_WEB_BROWSE))


if __name__ == "__main__":
    unittest.main()
