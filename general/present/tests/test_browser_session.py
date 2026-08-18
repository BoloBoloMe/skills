"""browser_session.py unit tests.

结构跟随被测对象: 行为测试直接命中 run_* 核心接缝 (断言结果 dict),
CLI 契约 (argv 解析 / 单行 JSON / 退出码 / 脱敏) 经 _run_main 走 main().

Covers: CLI, path validation, JSON output, error codes, sibling detection,
security, isolation, state shape, lifecycle (mocked attach seam).

Run: python -m pytest general/present/tests/ -v
Or:  python -m unittest discover -s general/present/tests -v
"""

import contextlib
import importlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


# ---------------------------------------------------------------------------
# Module loading
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
SCRIPT_PATH = SCRIPT_DIR / "browser_session.py"

def _load_bs():
    """Load browser_session.py as a module."""
    spec = importlib.util.spec_from_file_location("browser_session", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

bs = _load_bs()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_main(*argv):
    """跑 main(argv), 捕获 stdout 与退出码. 返回 (json_dict, exit_code, lines)."""
    buf = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(buf):
        try:
            bs.main(list(argv))
        except SystemExit as e:
            code = e.code if e.code is not None else 0
    lines = [l for l in buf.getvalue().splitlines() if l.strip()]
    obj = json.loads(lines[-1]) if lines else None
    return obj, code, lines


def _attach_modules(alive=True, page=None, attach_error=None):
    """构造 patch.dict 用的 browser_agent / browser_agent.attach 模拟模块.

    只读会话视图 (probe / attached_context) 是 run_state/run_status 触及
    browser_agent 的唯一接缝; 测试只模拟这一道接缝, 不模拟内部件.
    """
    mock_probe = mock.MagicMock(return_value=mock.MagicMock(alive=alive))
    mock_context = mock.MagicMock()
    mock_context.pages = [page] if page is not None else []
    mock_attached = mock.MagicMock()
    ctx_mgr = mock_attached.return_value
    if attach_error is not None:
        ctx_mgr.__enter__.side_effect = attach_error
    else:
        ctx_mgr.__enter__.return_value = mock_context
    ctx_mgr.__exit__.return_value = False
    return {
        "browser_agent": mock.MagicMock(),
        "browser_agent.attach": mock.MagicMock(
            probe=mock_probe, attached_context=mock_attached
        ),
    }


def _open_modules(page):
    """构造 patch.dict 用的 browser_agent.get_session 模拟模块 (open 接缝)."""
    mock_session = mock.MagicMock()
    mock_session.page = page
    return {
        "browser_agent": mock.MagicMock(
            get_session=mock.MagicMock(return_value=mock_session)
        ),
    }


def _state_page(state):
    """返回 evaluate 给出指定 state 的模拟页面."""
    page = mock.MagicMock()
    page.evaluate.return_value = state
    return page


# ===========================================================================
# CLI Tests
# ===========================================================================

class TestCLI(unittest.TestCase):
    """CLI argument parsing and dispatch."""

    def test_no_args_fails(self):
        obj, code, _ = _run_main()
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "internal_error")

    def test_unknown_command(self):
        obj, code, _ = _run_main("foo", "/tmp")
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "internal_error")
        self.assertEqual(obj["command"], "foo")

    def test_open_missing_args(self):
        obj, code, _ = _run_main("open")
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])

    def test_state_missing_args(self):
        obj, code, _ = _run_main("state")
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])

    def test_status_missing_args(self):
        obj, code, _ = _run_main("status")
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])

    def test_output_is_single_json(self):
        """stdout contains exactly one JSON object per call."""
        with tempfile.TemporaryDirectory() as td:
            obj, code, lines = _run_main("status", td)
        self.assertEqual(len(lines), 1)
        self.assertIn("success", obj)
        self.assertIn("command", obj)

    def test_exit_code_0_on_success(self):
        with tempfile.TemporaryDirectory() as td:
            obj, code, _ = _run_main("status", td)
        self.assertEqual(code, 0)
        self.assertTrue(obj["success"])

    def test_exit_code_nonzero_on_failure(self):
        obj, code, _ = _run_main("status", "/nonexistent/path/xyz")
        self.assertNotEqual(code, 0)
        self.assertFalse(obj["success"])

    def test_uncaught_exception_handled(self):
        """Uncaught exceptions produce internal_error, not traceback."""
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(bs, "run_status",
                                   side_effect=RuntimeError("unexpected")):
                obj, code, lines = _run_main("status", td)
        self.assertNotEqual(code, 0)
        self.assertEqual(obj["code"], "internal_error")
        self.assertEqual(obj["error"], "unexpected")
        self.assertEqual(len(lines), 1)


# ===========================================================================
# Path Validation Tests
# ===========================================================================

class TestPathValidation(unittest.TestCase):
    """Session dir and HTML file validation (via core seam)."""

    def test_nonexistent_session_dir(self):
        obj = bs.run_status("/nonexistent/path/xyz")
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_session_dir")

    def test_session_dir_is_file(self):
        with tempfile.NamedTemporaryFile() as f:
            obj = bs.run_status(f.name)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_session_dir")

    def test_nonexistent_html_file(self):
        with tempfile.TemporaryDirectory() as td:
            obj = bs.run_open(td, "/nonexistent/file.html")
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_html_file")

    def test_html_file_is_directory(self):
        with tempfile.TemporaryDirectory() as td:
            html_dir = Path(td) / "fake.html"
            html_dir.mkdir()
            obj = bs.run_open(td, str(html_dir))
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_html_file")

    def test_wrong_extension(self):
        with tempfile.TemporaryDirectory() as td:
            txt_file = Path(td) / "test.txt"
            txt_file.write_text("hello", encoding="utf-8")
            obj = bs.run_open(td, str(txt_file))
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_html_file")

    def test_html_outside_session_dir(self):
        with tempfile.TemporaryDirectory() as td:
            with tempfile.TemporaryDirectory() as other:
                html_file = Path(other) / "test.html"
                html_file.write_text("<html></html>", encoding="utf-8")
                obj = bs.run_open(td, str(html_file))
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_html_file")

    def test_valid_html_inside_session_dir(self):
        """Validation passes for valid HTML inside session-dir.

        (open will fail at browser step, but path validation succeeds.)
        """
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / "test.html"
            html_file.write_text("<html></html>", encoding="utf-8")
            with mock.patch.object(bs, "_ensure_access_web",
                                   side_effect=RuntimeError("test")):
                obj = bs.run_open(td, str(html_file))
            # Path validation passed, failed at browser step
            self.assertEqual(obj["code"], "access_web_unavailable")

    def test_case_insensitive_extension(self):
        """'.HTML' and '.Html' are accepted."""
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / "test.HTML"
            html_file.write_text("<html></html>", encoding="utf-8")
            with mock.patch.object(bs, "_ensure_access_web",
                                   side_effect=RuntimeError("test")):
                obj = bs.run_open(td, str(html_file))
            self.assertEqual(obj["code"], "access_web_unavailable")

    def test_relative_session_dir_rejected(self):
        """Relative session-dir is rejected before resolve."""
        obj = bs.run_status("relative/path")
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_session_dir")

    def test_relative_html_file_rejected(self):
        """Relative html-file is rejected before resolve."""
        with tempfile.TemporaryDirectory() as td:
            obj = bs.run_open(td, "relative/test.html")
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_html_file")


# ===========================================================================
# JSON Output Tests
# ===========================================================================

class TestJSONOutput(unittest.TestCase):
    """JSON output format compliance."""

    def test_success_has_required_fields(self):
        with tempfile.TemporaryDirectory() as td:
            obj = bs.run_status(td)
        self.assertTrue(obj["success"])
        self.assertEqual(obj["command"], "status")
        self.assertIn("alive", obj)

    def test_failure_has_required_fields(self):
        obj = bs.run_status("/nonexistent/xyz")
        self.assertFalse(obj["success"])
        self.assertEqual(obj["command"], "status")
        self.assertIn("code", obj)
        self.assertIn("error", obj)

    def test_status_alive_false_when_no_metadata(self):
        """status returns alive:false when no browser.json exists."""
        with tempfile.TemporaryDirectory() as td:
            obj = bs.run_status(td)
        self.assertTrue(obj["success"])
        self.assertFalse(obj["alive"])

    def test_state_browser_not_running_when_no_metadata(self):
        """state returns browser_not_running when no browser.json."""
        with tempfile.TemporaryDirectory() as td:
            obj = bs.run_state(td)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "browser_not_running")

    def test_error_no_traceback_in_stdout(self):
        obj, code, lines = _run_main("status", "/nonexistent/xyz")
        self.assertNotIn("Traceback", obj.get("error", ""))

    def test_all_stable_error_codes_are_strings(self):
        valid_codes = {
            "invalid_session_dir", "invalid_html_file",
            "access_web_unavailable", "browser_not_running",
            "browser_unavailable", "navigation_failed",
            "state_unavailable", "internal_error",
        }
        obj = bs.run_status("/nonexistent/xyz")
        self.assertIn(obj["code"], valid_codes)


# ===========================================================================
# Sibling Detection Tests
# ===========================================================================

class TestSiblingDetection(unittest.TestCase):
    """access-web sibling location detection."""

    def test_find_access_web_returns_path(self):
        result = bs._find_access_web()
        # In the actual repo, sibling exists
        if result is not None:
            self.assertTrue(
                (result / "browser_agent" / "__init__.py").is_file()
            )

    def test_find_access_web_checks_init(self):
        result = bs._find_access_web()
        if result is not None:
            init_file = result / "browser_agent" / "__init__.py"
            self.assertTrue(init_file.is_file())

    def test_ensure_access_web_adds_to_sys_path(self):
        aw_path = bs._find_access_web()
        if aw_path is not None:
            aw_str = str(aw_path)
            sys.path = [p for p in sys.path if p != aw_str]
            bs._ensure_access_web()
            self.assertIn(aw_str, sys.path)

    def test_ensure_access_web_raises_when_missing(self):
        with mock.patch.object(bs, "_find_access_web", return_value=None):
            with self.assertRaises(RuntimeError):
                bs._ensure_access_web()


# ===========================================================================
# Lifecycle Tests (mocked seams: get_session / attach)
# ===========================================================================

class TestLifecycle(unittest.TestCase):
    """Browser lifecycle tests, mocked at the browser_agent seams."""

    def test_open_success(self):
        """open navigates to HTML and returns url+alive."""
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / "test.html"
            html_file.write_text("<html></html>", encoding="utf-8")

            mock_page = mock.MagicMock()
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", _open_modules(mock_page)):
                    obj = bs.run_open(td, str(html_file))

            self.assertTrue(obj["success"])
            self.assertEqual(obj["command"], "open")
            self.assertTrue(obj["alive"])
            self.assertIn("url", obj)
            self.assertTrue(obj["url"].startswith("file://"))
            mock_page.goto.assert_called_once()

    def test_open_binds_session_dir(self):
        """open 经 get_session(cwd=session_dir) 绑定展示会话目录."""
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / "test.html"
            html_file.write_text("<html></html>", encoding="utf-8")

            mock_page = mock.MagicMock()
            modules = _open_modules(mock_page)
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", modules):
                    obj = bs.run_open(td, str(html_file))

            self.assertTrue(obj["success"])
            modules["browser_agent"].get_session.assert_called_once_with(
                cwd=str(Path(td).resolve())
            )

    def test_open_idempotent_reuse(self):
        """open on same session reuses browser (session 单例处理复用)."""
        with tempfile.TemporaryDirectory() as td:
            html1 = Path(td) / "v1.html"
            html1.write_text("<html>v1</html>", encoding="utf-8")
            html2 = Path(td) / "v2.html"
            html2.write_text("<html>v2</html>", encoding="utf-8")

            mock_page = mock.MagicMock()
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", _open_modules(mock_page)):
                    obj1 = bs.run_open(td, str(html1))
                    obj2 = bs.run_open(td, str(html2))

            self.assertTrue(obj1["success"])
            self.assertTrue(obj2["success"])
            self.assertEqual(mock_page.goto.call_count, 2)

    def test_open_browser_unavailable(self):
        """open returns browser_unavailable when Chromium can't start."""
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / "test.html"
            html_file.write_text("<html></html>", encoding="utf-8")

            mock_session = mock.MagicMock()
            type(mock_session).page = mock.PropertyMock(
                side_effect=RuntimeError("Chromium not installed")
            )
            modules = {
                "browser_agent": mock.MagicMock(
                    get_session=mock.MagicMock(return_value=mock_session)
                ),
            }
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", modules):
                    obj = bs.run_open(td, str(html_file))

            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "browser_unavailable")

    def test_open_navigation_failed(self):
        """open returns navigation_failed when goto fails."""
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / "test.html"
            html_file.write_text("<html></html>", encoding="utf-8")

            mock_page = mock.MagicMock()
            mock_page.goto.side_effect = Exception("net::ERR_FILE_NOT_FOUND")
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", _open_modules(mock_page)):
                    obj = bs.run_open(td, str(html_file))

            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "navigation_failed")

    def test_state_reads_presentation_state(self):
        """state 经只读附加读取 __PRESENTATION_STATE__."""
        with tempfile.TemporaryDirectory() as td:
            expected_state = {"version": 1, "values": {"selected": "A"}}
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict(
                    "sys.modules",
                    _attach_modules(page=_state_page(expected_state)),
                ):
                    obj = bs.run_state(td)

            self.assertTrue(obj["success"])
            self.assertEqual(obj["state"], expected_state)

    def test_state_browser_not_running(self):
        """probe 不存活时 state 返回 browser_not_running, 且不尝试附加.

        pid 死亡与端口关闭的区分由 browser_agent.attach.probe 负责,
        在 access-web 侧测试; 此处只验证接缝上的语义映射.
        """
        with tempfile.TemporaryDirectory() as td:
            modules = _attach_modules(alive=False)
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", modules):
                    obj = bs.run_state(td)

            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "browser_not_running")
            modules["browser_agent.attach"].attached_context.assert_not_called()

    def test_state_no_page_available(self):
        """存活但无页面: state 返回 state_unavailable."""
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict(
                    "sys.modules", _attach_modules(alive=True, page=None)
                ):
                    obj = bs.run_state(td)

            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "state_unavailable")

    def test_state_attach_failure_is_state_unavailable(self):
        """CDP 附加抛异常: state 返回 state_unavailable."""
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict(
                    "sys.modules",
                    _attach_modules(attach_error=Exception("refused")),
                ):
                    obj = bs.run_state(td)

            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "state_unavailable")

    def test_state_invalid_version(self):
        """state returns state_unavailable for unsupported version."""
        with tempfile.TemporaryDirectory() as td:
            page = _state_page({"version": 99, "values": {}})
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict(
                    "sys.modules", _attach_modules(page=page)
                ):
                    obj = bs.run_state(td)
            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "state_unavailable")

    def test_state_missing_values(self):
        """state returns state_unavailable when values key missing."""
        with tempfile.TemporaryDirectory() as td:
            page = _state_page({"version": 1})
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict(
                    "sys.modules", _attach_modules(page=page)
                ):
                    obj = bs.run_state(td)
            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "state_unavailable")

    def test_state_bool_version_rejected(self):
        """state returns state_unavailable when version is bool (True)."""
        with tempfile.TemporaryDirectory() as td:
            page = _state_page({"version": True, "values": {}})
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict(
                    "sys.modules", _attach_modules(page=page)
                ):
                    obj = bs.run_state(td)
            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "state_unavailable")

    def test_state_float_version_rejected(self):
        """state returns state_unavailable when version is float (1.0)."""
        with tempfile.TemporaryDirectory() as td:
            page = _state_page({"version": 1.0, "values": {}})
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict(
                    "sys.modules", _attach_modules(page=page)
                ):
                    obj = bs.run_state(td)
            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "state_unavailable")

    def test_state_values_not_dict_rejected(self):
        """state returns state_unavailable when values is a list."""
        with tempfile.TemporaryDirectory() as td:
            page = _state_page({"version": 1, "values": [1, 2, 3]})
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict(
                    "sys.modules", _attach_modules(page=page)
                ):
                    obj = bs.run_state(td)
            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "state_unavailable")

    # "CDP 连接绝不调用 browser.close()" 的纪律已随实现集中到
    # browser_agent.attach, 由 access-web 侧 test_attach.py 覆盖.

    def test_status_alive_returns_url(self):
        """status 存活时经只读附加带回当前 URL."""
        with tempfile.TemporaryDirectory() as td:
            page = mock.MagicMock()
            page.url = "file:///test.html"
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict(
                    "sys.modules", _attach_modules(page=page)
                ):
                    obj = bs.run_status(td)

            self.assertTrue(obj["success"])
            self.assertTrue(obj["alive"])
            self.assertEqual(obj["url"], "file:///test.html")

    def test_status_alive_but_attach_fails_degrades(self):
        """status 存活但附加失败: 仍成功, 降级为仅存活标记."""
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict(
                    "sys.modules",
                    _attach_modules(attach_error=Exception("no pw")),
                ):
                    obj = bs.run_status(td)

            self.assertTrue(obj["success"])
            self.assertTrue(obj["alive"])
            self.assertNotIn("url", obj)

    def test_status_no_side_effect_on_closed_browser(self):
        """status does not start browser when session is not alive."""
        with tempfile.TemporaryDirectory() as td:
            modules = _attach_modules(alive=False)
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", modules):
                    obj = bs.run_status(td)

            self.assertTrue(obj["success"])
            self.assertFalse(obj["alive"])
            modules["browser_agent.attach"].attached_context.assert_not_called()

    def test_recovery_after_close(self):
        """After browser close, state returns browser_not_running,
        then open can restart (mocked)."""
        with tempfile.TemporaryDirectory() as td:
            # Phase 1: state shows browser_not_running
            obj = bs.run_state(td)
            self.assertEqual(obj["code"], "browser_not_running")

            # Phase 2: open can be called (mocked browser)
            html_file = Path(td) / "recover.html"
            html_file.write_text("<html></html>", encoding="utf-8")

            mock_page = mock.MagicMock()
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", _open_modules(mock_page)):
                    obj2 = bs.run_open(td, str(html_file))

            self.assertTrue(obj2["success"])


# ===========================================================================
# Security Tests
# ===========================================================================

class TestSecurity(unittest.TestCase):
    """Security boundary tests."""

    def test_html_file_outside_session_rejected(self):
        with tempfile.TemporaryDirectory() as session:
            with tempfile.TemporaryDirectory() as outside:
                html_file = Path(outside) / "secret.html"
                html_file.write_text("<html></html>", encoding="utf-8")
                obj = bs.run_open(session, str(html_file))
            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "invalid_html_file")

    def test_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / ".." / "evil.html"
            obj = bs.run_open(td, str(html_file))
            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "invalid_html_file")

    def test_credentials_not_in_error_output(self):
        obj, code, _ = _run_main("status", "/nonexistent/xyz")
        error_str = json.dumps(obj)
        self.assertNotIn("password", error_str.lower())
        self.assertNotIn("token", error_str.lower())
        self.assertNotIn("secret", error_str.lower())

    def test_credential_patterns_sanitized_in_error(self):
        """Error messages with credential patterns are sanitized."""
        cases = [
            ("token=abc123secret", "token=[REDACTED]"),
            ("api_key=sk-12345", "api_key=[REDACTED]"),
            ("secret=mysecret", "secret=[REDACTED]"),
            ("password=hunter2", "password=[REDACTED]"),
            ("Bearer eyJhbGciOiJIUzI1NiJ9.xxx", "Bearer [REDACTED]"),
            ("auth=Basic dXNlcjpwYXNz", "auth=[REDACTED]"),
            ("credential=xyz", "credential=[REDACTED]"),
        ]
        for raw, expected in cases:
            sanitized = bs._sanitize_error(raw)
            self.assertIn(expected, sanitized)
            self.assertNotIn(raw.split("=")[1] if "=" in raw else raw.split(" ")[1],
                             sanitized)

    def test_sanitize_preserves_normal_text(self):
        normal = "session-dir does not exist: /tmp/nonexistent"
        self.assertEqual(bs._sanitize_error(normal), normal)

    def test_error_sanitized_at_cli_boundary(self):
        """脱敏发生在 CLI 适配器: 核心返回原文, 出口 JSON 已脱敏."""
        with mock.patch.object(
            bs, "run_status",
            return_value={"success": False, "command": "status",
                          "code": "internal_error", "error": "token=abc123"},
        ):
            obj, code, _ = _run_main("status", "/tmp")
        self.assertEqual(obj["error"], "token=[REDACTED]")

    def test_session_containment_uses_resolve(self):
        """Containment check uses Path.relative_to, not string prefix."""
        with tempfile.TemporaryDirectory() as td:
            parent = Path(td).parent
            sibling = parent / (Path(td).name + "-evil")
            try:
                sibling.mkdir(exist_ok=True)
                html_file = sibling / "test.html"
                html_file.write_text("<html></html>", encoding="utf-8")
                obj = bs.run_open(td, str(html_file))
                self.assertFalse(obj["success"])
                self.assertEqual(obj["code"], "invalid_html_file")
            finally:
                import shutil
                shutil.rmtree(sibling, ignore_errors=True)

    def test_helper_only_allows_html_extension(self):
        """Non-.html files are rejected even if inside session-dir."""
        with tempfile.TemporaryDirectory() as td:
            for ext in [".py", ".js", ".json", ".txt", ".htm", ".xhtml"]:
                f = Path(td) / f"test{ext}"
                f.write_text("content", encoding="utf-8")
                obj = bs.run_open(td, str(f))
                self.assertFalse(obj["success"],
                                 f"Extension {ext} should be rejected")
                self.assertEqual(obj["code"], "invalid_html_file",
                                 f"Extension {ext} wrong error code")


# ===========================================================================
# Isolation Tests
# ===========================================================================

class TestIsolation(unittest.TestCase):
    """Session isolation tests."""

    def test_different_session_dirs_different_configs(self):
        """Different session-dirs produce different BrowserConfig session-keys."""
        with tempfile.TemporaryDirectory() as td1:
            with tempfile.TemporaryDirectory() as td2:
                # Try real BrowserConfig if access-web is importable
                try:
                    bs._ensure_access_web()
                    from browser_agent.config import BrowserConfig
                    config1 = BrowserConfig(cwd=td1)
                    config2 = BrowserConfig(cwd=td2)
                    self.assertNotEqual(config1.session_key, config2.session_key)
                    self.assertNotEqual(config1.browser_json, config2.browser_json)
                    self.assertNotEqual(config1.profile_dir, config2.profile_dir)
                except (RuntimeError, ImportError):
                    # Fallback: 路径隔离性直接比较派生路径
                    self.assertNotEqual(
                        Path(td1) / "browser.json",
                        Path(td2) / "browser.json",
                    )

    def test_headed_env_set_in_open(self):
        """open sets BROWSER_HEADED=true before importing."""
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / "test.html"
            html_file.write_text("<html></html>", encoding="utf-8")

            env_at_import = {}

            def capture_env():
                env_at_import["BROWSER_HEADED"] = os.environ.get(
                    "BROWSER_HEADED"
                )
                raise RuntimeError("captured")

            with mock.patch.object(bs, "_ensure_access_web",
                                   side_effect=capture_env):
                bs.run_open(td, str(html_file))

            self.assertEqual(env_at_import.get("BROWSER_HEADED"), "true")


# ===========================================================================
# URL Generation Tests
# ===========================================================================

class TestURLGeneration(unittest.TestCase):
    """URL must be generated via Path.as_uri()."""

    def test_url_is_file_uri(self):
        """open URL starts with file://."""
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / "test.html"
            html_file.write_text("<html></html>", encoding="utf-8")

            mock_page = mock.MagicMock()
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", _open_modules(mock_page)):
                    obj = bs.run_open(td, str(html_file))

            expected_url = html_file.as_uri()
            mock_page.goto.assert_called_once_with(expected_url)
            self.assertEqual(obj["url"], expected_url)

    def test_special_chars_in_path(self):
        """Paths with spaces and unicode are handled correctly."""
        with tempfile.TemporaryDirectory(prefix="pi-test ") as td:
            html_file = Path(td) / "test page.html"
            html_file.write_text("<html></html>", encoding="utf-8")

            mock_page = mock.MagicMock()
            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", _open_modules(mock_page)):
                    obj = bs.run_open(td, str(html_file))

            self.assertTrue(obj["success"])
            self.assertEqual(mock_page.goto.call_args[0][0],
                             html_file.as_uri())


# ===========================================================================
# Degradation Tests
# ===========================================================================

class TestDegradation(unittest.TestCase):
    """Degradation and error handling."""

    def test_access_web_unavailable(self):
        """Returns access_web_unavailable when sibling not found."""
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / "test.html"
            html_file.write_text("<html></html>", encoding="utf-8")

            with mock.patch.object(bs, "_find_access_web",
                                   return_value=None):
                obj = bs.run_open(td, str(html_file))

            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "access_web_unavailable")

    def test_state_access_web_unavailable(self):
        """state returns access_web_unavailable when sibling not found."""
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(bs, "_find_access_web",
                                   return_value=None):
                obj = bs.run_state(td)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "access_web_unavailable")

    def test_status_access_web_unavailable(self):
        """status returns access_web_unavailable when sibling not found."""
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(bs, "_find_access_web",
                                   return_value=None):
                obj = bs.run_status(td)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "access_web_unavailable")


if __name__ == "__main__":
    unittest.main()
