"""browser_session.py unit tests.

Covers: CLI, path validation, JSON output, error codes, sibling detection,
security, isolation, state shape, lifecycle (mocked).

Run: python -m pytest general/adaptive-presentation/tests/ -v
Or:  python -m unittest discover -s general/adaptive-presentation/tests -v
"""

import importlib
import importlib.util
import json
import os
import socket
import subprocess
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
# Helper: capture JSON output and exit
# ---------------------------------------------------------------------------

class ExitCalled(Exception):
    """Raised when sys.exit is called."""
    def __init__(self, code):
        self.code = code

def _run_cmd(func, *args):
    """Run a command function, capture JSON output and exit code.

    Returns (json_dict, exit_code).
    """
    captured = []
    original_json_out = bs._json_out

    def mock_json_out(obj):
        captured.append(obj)
        original_json_out(obj)

    exit_code = 0
    with mock.patch.object(bs, "_json_out", side_effect=mock_json_out):
        try:
            func(*args)
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0

    return captured[-1] if captured else None, exit_code


# ===========================================================================
# CLI Tests
# ===========================================================================

class TestCLI(unittest.TestCase):
    """CLI argument parsing and dispatch."""

    def test_no_args_fails(self):
        """No arguments produces internal_error."""
        with mock.patch("sys.argv", ["browser_session.py"]):
            obj, code = _run_cmd(bs.main)
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "internal_error")

    def test_unknown_command(self):
        """Unknown command produces internal_error."""
        with mock.patch("sys.argv", ["browser_session.py", "foo", "/tmp"]):
            obj, code = _run_cmd(bs.main)
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "internal_error")
        self.assertEqual(obj["command"], "foo")

    def test_open_missing_args(self):
        """open without session-dir and html-file fails."""
        with mock.patch("sys.argv", ["browser_session.py", "open"]):
            obj, code = _run_cmd(bs.main)
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])

    def test_state_missing_args(self):
        """state without session-dir fails."""
        with mock.patch("sys.argv", ["browser_session.py", "state"]):
            obj, code = _run_cmd(bs.main)
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])

    def test_status_missing_args(self):
        """status without session-dir fails."""
        with mock.patch("sys.argv", ["browser_session.py", "status"]):
            obj, code = _run_cmd(bs.main)
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])

    def test_output_is_single_json(self):
        """stdout contains exactly one JSON object per call."""
        with tempfile.TemporaryDirectory() as td:
            obj, code = _run_cmd(bs.cmd_status, td)
        # Status should succeed or fail with a single JSON
        self.assertIsNotNone(obj)
        self.assertIn("success", obj)
        self.assertIn("command", obj)

    def test_exit_code_0_on_success(self):
        """Successful command exits with 0."""
        with tempfile.TemporaryDirectory() as td:
            obj, code = _run_cmd(bs.cmd_status, td)
        # status with no metadata returns alive:false, which is success
        self.assertEqual(code, 0)
        self.assertTrue(obj["success"])

    def test_exit_code_nonzero_on_failure(self):
        """Failed command exits with non-zero."""
        obj, code = _run_cmd(bs.cmd_status, "/nonexistent/path/xyz")
        self.assertNotEqual(code, 0)
        self.assertFalse(obj["success"])


# ===========================================================================
# Path Validation Tests
# ===========================================================================

class TestPathValidation(unittest.TestCase):
    """Session dir and HTML file validation."""

    def test_nonexistent_session_dir(self):
        obj, code = _run_cmd(bs.cmd_status, "/nonexistent/path/xyz")
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_session_dir")

    def test_session_dir_is_file(self):
        with tempfile.NamedTemporaryFile() as f:
            obj, code = _run_cmd(bs.cmd_status, f.name)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_session_dir")

    def test_nonexistent_html_file(self):
        with tempfile.TemporaryDirectory() as td:
            obj, code = _run_cmd(bs.cmd_open, td, "/nonexistent/file.html")
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_html_file")

    def test_html_file_is_directory(self):
        with tempfile.TemporaryDirectory() as td:
            html_dir = Path(td) / "fake.html"
            html_dir.mkdir()
            obj, code = _run_cmd(bs.cmd_open, td, str(html_dir))
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_html_file")

    def test_wrong_extension(self):
        with tempfile.TemporaryDirectory() as td:
            txt_file = Path(td) / "test.txt"
            txt_file.write_text("hello", encoding="utf-8")
            obj, code = _run_cmd(bs.cmd_open, td, str(txt_file))
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_html_file")

    def test_html_outside_session_dir(self):
        with tempfile.TemporaryDirectory() as td:
            with tempfile.TemporaryDirectory() as other:
                html_file = Path(other) / "test.html"
                html_file.write_text("<html></html>", encoding="utf-8")
                obj, code = _run_cmd(bs.cmd_open, td, str(html_file))
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_html_file")

    def test_valid_html_inside_session_dir(self):
        """Validation passes for valid HTML inside session-dir.

        (open will fail at browser step, but path validation succeeds.)
        """
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / "test.html"
            html_file.write_text("<html></html>", encoding="utf-8")
            # Mock the browser import to avoid actual browser launch
            with mock.patch.object(bs, "_ensure_access_web",
                                   side_effect=RuntimeError("test")):
                obj, code = _run_cmd(bs.cmd_open, td, str(html_file))
            # Path validation passed, failed at browser step
            self.assertEqual(obj["code"], "access_web_unavailable")

    def test_case_insensitive_extension(self):
        """'.HTML' and '.Html' are accepted."""
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / "test.HTML"
            html_file.write_text("<html></html>", encoding="utf-8")
            with mock.patch.object(bs, "_ensure_access_web",
                                   side_effect=RuntimeError("test")):
                obj, code = _run_cmd(bs.cmd_open, td, str(html_file))
            self.assertEqual(obj["code"], "access_web_unavailable")

    def test_relative_session_dir_rejected(self):
        """Relative session-dir is rejected before resolve."""
        obj, code = _run_cmd(bs.cmd_status, "relative/path")
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_session_dir")

    def test_relative_html_file_rejected(self):
        """Relative html-file is rejected before resolve."""
        with tempfile.TemporaryDirectory() as td:
            obj, code = _run_cmd(bs.cmd_open, td, "relative/test.html")
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_html_file")


# ===========================================================================
# JSON Output Tests
# ===========================================================================

class TestJSONOutput(unittest.TestCase):
    """JSON output format compliance."""

    def test_success_has_required_fields(self):
        """Success response has success and command."""
        with tempfile.TemporaryDirectory() as td:
            obj, code = _run_cmd(bs.cmd_status, td)
        self.assertTrue(obj["success"])
        self.assertEqual(obj["command"], "status")
        self.assertIn("alive", obj)

    def test_failure_has_required_fields(self):
        """Failure response has success, command, code, error."""
        obj, code = _run_cmd(bs.cmd_status, "/nonexistent/xyz")
        self.assertFalse(obj["success"])
        self.assertEqual(obj["command"], "status")
        self.assertIn("code", obj)
        self.assertIn("error", obj)

    def test_status_alive_false_when_no_metadata(self):
        """status returns alive:false when no browser.json exists."""
        with tempfile.TemporaryDirectory() as td:
            obj, code = _run_cmd(bs.cmd_status, td)
        self.assertTrue(obj["success"])
        self.assertFalse(obj["alive"])

    def test_state_browser_not_running_when_no_metadata(self):
        """state returns browser_not_running when no browser.json."""
        with tempfile.TemporaryDirectory() as td:
            obj, code = _run_cmd(bs.cmd_state, td)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "browser_not_running")

    def test_error_no_traceback_in_stdout(self):
        """Error messages don't contain tracebacks."""
        obj, code = _run_cmd(bs.cmd_status, "/nonexistent/xyz")
        self.assertNotIn("Traceback", obj.get("error", ""))

    def test_all_stable_error_codes_are_strings(self):
        """All error codes are string values."""
        valid_codes = {
            "invalid_session_dir", "invalid_html_file",
            "access_web_unavailable", "browser_not_running",
            "browser_unavailable", "navigation_failed",
            "state_unavailable", "internal_error",
        }
        # Test a few scenarios and check code is in valid set
        obj, _ = _run_cmd(bs.cmd_status, "/nonexistent/xyz")
        self.assertIn(obj["code"], valid_codes)


# ===========================================================================
# Sibling Detection Tests
# ===========================================================================

class TestSiblingDetection(unittest.TestCase):
    """access-web sibling location detection."""

    def test_find_access_web_returns_path(self):
        """_find_access_web returns a path when sibling exists."""
        result = bs._find_access_web()
        # In the actual repo, sibling exists
        if result is not None:
            self.assertTrue(
                (result / "browser_agent" / "__init__.py").is_file()
            )

    def test_find_access_web_checks_init(self):
        """_find_access_web verifies browser_agent/__init__.py exists."""
        result = bs._find_access_web()
        if result is not None:
            init_file = result / "browser_agent" / "__init__.py"
            self.assertTrue(init_file.is_file())

    def test_ensure_access_web_adds_to_sys_path(self):
        """_ensure_access_web adds browse/ to sys.path."""
        aw_path = bs._find_access_web()
        if aw_path is not None:
            # Remove from sys.path if already there
            aw_str = str(aw_path)
            sys.path = [p for p in sys.path if p != aw_str]
            bs._ensure_access_web()
            self.assertIn(aw_str, sys.path)

    def test_ensure_access_web_raises_when_missing(self):
        """_ensure_access_web raises RuntimeError when sibling not found."""
        with mock.patch.object(bs, "_find_access_web", return_value=None):
            with self.assertRaises(RuntimeError):
                bs._ensure_access_web()


# ===========================================================================
# Lifecycle Tests (mocked browser)
# ===========================================================================

class TestLifecycle(unittest.TestCase):
    """Browser lifecycle tests with mocked Browser class."""

    def test_open_success(self):
        """open navigates to HTML and returns url+alive."""
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / "test.html"
            html_file.write_text("<html></html>", encoding="utf-8")

            mock_page = mock.MagicMock()
            mock_page.url = html_file.as_uri()
            mock_browser_instance = mock.MagicMock()
            mock_browser_instance.page = mock_page
            mock_browser_cls = mock.MagicMock(
                return_value=mock_browser_instance
            )
            mock_config_cls = mock.MagicMock()

            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", {
                    "browser_agent": mock.MagicMock(),
                    "browser_agent.browser": mock.MagicMock(
                        Browser=mock_browser_cls
                    ),
                    "browser_agent.config": mock.MagicMock(
                        BrowserConfig=mock_config_cls
                    ),
                }):
                    obj, code = _run_cmd(bs.cmd_open, td, str(html_file))

            self.assertEqual(code, 0)
            self.assertTrue(obj["success"])
            self.assertEqual(obj["command"], "open")
            self.assertTrue(obj["alive"])
            self.assertIn("url", obj)
            self.assertTrue(obj["url"].startswith("file://"))
            mock_page.goto.assert_called_once()

    def test_open_idempotent_reuse(self):
        """open on same session reuses browser (Browser.start handles this)."""
        with tempfile.TemporaryDirectory() as td:
            html1 = Path(td) / "v1.html"
            html1.write_text("<html>v1</html>", encoding="utf-8")
            html2 = Path(td) / "v2.html"
            html2.write_text("<html>v2</html>", encoding="utf-8")

            mock_page = mock.MagicMock()
            mock_browser_instance = mock.MagicMock()
            mock_browser_instance.page = mock_page
            mock_browser_cls = mock.MagicMock(
                return_value=mock_browser_instance
            )
            mock_config_cls = mock.MagicMock()

            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", {
                    "browser_agent": mock.MagicMock(),
                    "browser_agent.browser": mock.MagicMock(
                        Browser=mock_browser_cls
                    ),
                    "browser_agent.config": mock.MagicMock(
                        BrowserConfig=mock_config_cls
                    ),
                }):
                    obj1, code1 = _run_cmd(bs.cmd_open, td, str(html1))
                    obj2, code2 = _run_cmd(bs.cmd_open, td, str(html2))

            self.assertEqual(code1, 0)
            self.assertEqual(code2, 0)
            # Both navigated
            self.assertEqual(mock_page.goto.call_count, 2)

    def test_open_browser_unavailable(self):
        """open returns browser_unavailable when Chromium can't start."""
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / "test.html"
            html_file.write_text("<html></html>", encoding="utf-8")

            mock_browser_cls = mock.MagicMock(
                side_effect=RuntimeError("Chromium not installed")
            )
            mock_config_cls = mock.MagicMock()

            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", {
                    "browser_agent": mock.MagicMock(),
                    "browser_agent.browser": mock.MagicMock(
                        Browser=mock_browser_cls
                    ),
                    "browser_agent.config": mock.MagicMock(
                        BrowserConfig=mock_config_cls
                    ),
                }):
                    obj, code = _run_cmd(bs.cmd_open, td, str(html_file))

            self.assertNotEqual(code, 0)
            self.assertEqual(obj["code"], "browser_unavailable")

    def test_open_navigation_failed(self):
        """open returns navigation_failed when goto fails."""
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / "test.html"
            html_file.write_text("<html></html>", encoding="utf-8")

            mock_page = mock.MagicMock()
            mock_page.goto.side_effect = Exception("net::ERR_FILE_NOT_FOUND")
            mock_browser_instance = mock.MagicMock()
            mock_browser_instance.page = mock_page
            mock_browser_cls = mock.MagicMock(
                return_value=mock_browser_instance
            )
            mock_config_cls = mock.MagicMock()

            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", {
                    "browser_agent": mock.MagicMock(),
                    "browser_agent.browser": mock.MagicMock(
                        Browser=mock_browser_cls
                    ),
                    "browser_agent.config": mock.MagicMock(
                        BrowserConfig=mock_config_cls
                    ),
                }):
                    obj, code = _run_cmd(bs.cmd_open, td, str(html_file))

            self.assertNotEqual(code, 0)
            self.assertEqual(obj["code"], "navigation_failed")

    def test_state_reads_presentation_state(self):
        """state reads __PRESENTATION_STATE__ via CDP."""
        with tempfile.TemporaryDirectory() as td:
            # Write fake metadata
            config_dir = Path(td)
            # We need to mock BrowserConfig to return proper config
            mock_config = mock.MagicMock()
            mock_config.browser_json = Path(td) / "browser.json"
            mock_config.browser_json.write_text(
                json.dumps({"pid": 99999, "cdp_port": 19222}),
                encoding="utf-8",
            )
            mock_config.read_metadata.return_value = {
                "pid": 99999, "cdp_port": 19222
            }
            mock_config_cls = mock.MagicMock(return_value=mock_config)

            expected_state = {"version": 1, "values": {"selected": "A"}}

            # Mock alive check
            with mock.patch.object(bs, "_is_pid_alive", return_value=True):
                with mock.patch.object(bs, "_is_port_open", return_value=True):
                    # Mock playwright
                    mock_page = mock.MagicMock()
                    mock_page.evaluate.return_value = expected_state
                    mock_context = mock.MagicMock()
                    mock_context.pages = [mock_page]
                    mock_browser = mock.MagicMock()
                    mock_browser.contexts = [mock_context]
                    mock_pw = mock.MagicMock()
                    mock_pw.chromium.connect_over_cdp.return_value = mock_browser
                    mock_pw.__enter__ = mock.MagicMock(return_value=mock_pw)
                    mock_pw.__exit__ = mock.MagicMock(return_value=False)

                    with mock.patch.object(bs, "_ensure_access_web"):
                        with mock.patch.dict("sys.modules", {
                            "browser_agent": mock.MagicMock(),
                            "browser_agent.config": mock.MagicMock(
                                BrowserConfig=mock_config_cls
                            ),
                            "playwright": mock.MagicMock(),
                            "playwright.sync_api": mock.MagicMock(
                                sync_playwright=lambda: mock_pw
                            ),
                        }):
                            obj, code = _run_cmd(bs.cmd_state, td)

            self.assertEqual(code, 0)
            self.assertTrue(obj["success"])
            self.assertEqual(obj["state"], expected_state)

    def test_state_browser_not_running_dead_pid(self):
        """state returns browser_not_running when pid is dead."""
        with tempfile.TemporaryDirectory() as td:
            mock_config = mock.MagicMock()
            mock_config.browser_json = Path(td) / "browser.json"
            mock_config.browser_json.write_text(
                json.dumps({"pid": 99999, "cdp_port": 19222}),
                encoding="utf-8",
            )
            mock_config.read_metadata.return_value = {
                "pid": 99999, "cdp_port": 19222
            }
            mock_config_cls = mock.MagicMock(return_value=mock_config)

            with mock.patch.object(bs, "_is_pid_alive", return_value=False):
                with mock.patch.object(bs, "_ensure_access_web"):
                    with mock.patch.dict("sys.modules", {
                        "browser_agent": mock.MagicMock(),
                        "browser_agent.config": mock.MagicMock(
                            BrowserConfig=mock_config_cls
                        ),
                    }):
                        obj, code = _run_cmd(bs.cmd_state, td)

            self.assertNotEqual(code, 0)
            self.assertEqual(obj["code"], "browser_not_running")

    def test_state_browser_not_running_closed_port(self):
        """state returns browser_not_running when CDP port is closed."""
        with tempfile.TemporaryDirectory() as td:
            mock_config = mock.MagicMock()
            mock_config.browser_json = Path(td) / "browser.json"
            mock_config.browser_json.write_text(
                json.dumps({"pid": 99999, "cdp_port": 19222}),
                encoding="utf-8",
            )
            mock_config.read_metadata.return_value = {
                "pid": 99999, "cdp_port": 19222
            }
            mock_config_cls = mock.MagicMock(return_value=mock_config)

            with mock.patch.object(bs, "_is_pid_alive", return_value=True):
                with mock.patch.object(bs, "_is_port_open", return_value=False):
                    with mock.patch.object(bs, "_ensure_access_web"):
                        with mock.patch.dict("sys.modules", {
                            "browser_agent": mock.MagicMock(),
                            "browser_agent.config": mock.MagicMock(
                                BrowserConfig=mock_config_cls
                            ),
                        }):
                            obj, code = _run_cmd(bs.cmd_state, td)

            self.assertNotEqual(code, 0)
            self.assertEqual(obj["code"], "browser_not_running")

    def test_state_invalid_version(self):
        """state returns state_unavailable for unsupported version."""
        with tempfile.TemporaryDirectory() as td:
            mock_config = mock.MagicMock()
            mock_config.browser_json = Path(td) / "browser.json"
            mock_config.browser_json.write_text(
                json.dumps({"pid": 99999, "cdp_port": 19222}),
                encoding="utf-8",
            )
            mock_config.read_metadata.return_value = {
                "pid": 99999, "cdp_port": 19222
            }
            mock_config_cls = mock.MagicMock(return_value=mock_config)

            with mock.patch.object(bs, "_is_pid_alive", return_value=True):
                with mock.patch.object(bs, "_is_port_open", return_value=True):
                    mock_page = mock.MagicMock()
                    mock_page.evaluate.return_value = {
                        "version": 99, "values": {}
                    }
                    mock_context = mock.MagicMock()
                    mock_context.pages = [mock_page]
                    mock_browser = mock.MagicMock()
                    mock_browser.contexts = [mock_context]
                    mock_pw = mock.MagicMock()
                    mock_pw.chromium.connect_over_cdp.return_value = mock_browser
                    mock_pw.__enter__ = mock.MagicMock(return_value=mock_pw)
                    mock_pw.__exit__ = mock.MagicMock(return_value=False)

                    with mock.patch.object(bs, "_ensure_access_web"):
                        with mock.patch.dict("sys.modules", {
                            "browser_agent": mock.MagicMock(),
                            "browser_agent.config": mock.MagicMock(
                                BrowserConfig=mock_config_cls
                            ),
                            "playwright": mock.MagicMock(),
                            "playwright.sync_api": mock.MagicMock(
                                sync_playwright=lambda: mock_pw
                            ),
                        }):
                            obj, code = _run_cmd(bs.cmd_state, td)

            self.assertNotEqual(code, 0)
            self.assertEqual(obj["code"], "state_unavailable")

    def test_state_missing_values(self):
        """state returns state_unavailable when values key missing."""
        with tempfile.TemporaryDirectory() as td:
            mock_config = mock.MagicMock()
            mock_config.browser_json = Path(td) / "browser.json"
            mock_config.browser_json.write_text(
                json.dumps({"pid": 99999, "cdp_port": 19222}),
                encoding="utf-8",
            )
            mock_config.read_metadata.return_value = {
                "pid": 99999, "cdp_port": 19222
            }
            mock_config_cls = mock.MagicMock(return_value=mock_config)

            with mock.patch.object(bs, "_is_pid_alive", return_value=True):
                with mock.patch.object(bs, "_is_port_open", return_value=True):
                    mock_page = mock.MagicMock()
                    mock_page.evaluate.return_value = {"version": 1}
                    mock_context = mock.MagicMock()
                    mock_context.pages = [mock_page]
                    mock_browser = mock.MagicMock()
                    mock_browser.contexts = [mock_context]
                    mock_pw = mock.MagicMock()
                    mock_pw.chromium.connect_over_cdp.return_value = mock_browser
                    mock_pw.__enter__ = mock.MagicMock(return_value=mock_pw)
                    mock_pw.__exit__ = mock.MagicMock(return_value=False)

                    with mock.patch.object(bs, "_ensure_access_web"):
                        with mock.patch.dict("sys.modules", {
                            "browser_agent": mock.MagicMock(),
                            "browser_agent.config": mock.MagicMock(
                                BrowserConfig=mock_config_cls
                            ),
                            "playwright": mock.MagicMock(),
                            "playwright.sync_api": mock.MagicMock(
                                sync_playwright=lambda: mock_pw
                            ),
                        }):
                            obj, code = _run_cmd(bs.cmd_state, td)

            self.assertNotEqual(code, 0)
            self.assertEqual(obj["code"], "state_unavailable")

    def test_state_bool_version_rejected(self):
        """state returns state_unavailable when version is bool (True)."""
        with tempfile.TemporaryDirectory() as td:
            mock_config = mock.MagicMock()
            mock_config.browser_json = Path(td) / "browser.json"
            mock_config.browser_json.write_text(
                json.dumps({"pid": 99999, "cdp_port": 19222}),
                encoding="utf-8",
            )
            mock_config.read_metadata.return_value = {
                "pid": 99999, "cdp_port": 19222
            }
            mock_config_cls = mock.MagicMock(return_value=mock_config)

            with mock.patch.object(bs, "_is_pid_alive", return_value=True):
                with mock.patch.object(bs, "_is_port_open", return_value=True):
                    mock_page = mock.MagicMock()
                    mock_page.evaluate.return_value = {
                        "version": True, "values": {}
                    }
                    mock_context = mock.MagicMock()
                    mock_context.pages = [mock_page]
                    mock_browser = mock.MagicMock()
                    mock_browser.contexts = [mock_context]
                    mock_pw = mock.MagicMock()
                    mock_pw.chromium.connect_over_cdp.return_value = mock_browser
                    mock_pw.__enter__ = mock.MagicMock(return_value=mock_pw)
                    mock_pw.__exit__ = mock.MagicMock(return_value=False)

                    with mock.patch.object(bs, "_ensure_access_web"):
                        with mock.patch.dict("sys.modules", {
                            "browser_agent": mock.MagicMock(),
                            "browser_agent.config": mock.MagicMock(
                                BrowserConfig=mock_config_cls
                            ),
                            "playwright": mock.MagicMock(),
                            "playwright.sync_api": mock.MagicMock(
                                sync_playwright=lambda: mock_pw
                            ),
                        }):
                            obj, code = _run_cmd(bs.cmd_state, td)

            self.assertNotEqual(code, 0)
            self.assertEqual(obj["code"], "state_unavailable")

    def test_state_float_version_rejected(self):
        """state returns state_unavailable when version is float (1.0)."""
        with tempfile.TemporaryDirectory() as td:
            mock_config = mock.MagicMock()
            mock_config.browser_json = Path(td) / "browser.json"
            mock_config.browser_json.write_text(
                json.dumps({"pid": 99999, "cdp_port": 19222}),
                encoding="utf-8",
            )
            mock_config.read_metadata.return_value = {
                "pid": 99999, "cdp_port": 19222
            }
            mock_config_cls = mock.MagicMock(return_value=mock_config)

            with mock.patch.object(bs, "_is_pid_alive", return_value=True):
                with mock.patch.object(bs, "_is_port_open", return_value=True):
                    mock_page = mock.MagicMock()
                    mock_page.evaluate.return_value = {
                        "version": 1.0, "values": {}
                    }
                    mock_context = mock.MagicMock()
                    mock_context.pages = [mock_page]
                    mock_browser = mock.MagicMock()
                    mock_browser.contexts = [mock_context]
                    mock_pw = mock.MagicMock()
                    mock_pw.chromium.connect_over_cdp.return_value = mock_browser
                    mock_pw.__enter__ = mock.MagicMock(return_value=mock_pw)
                    mock_pw.__exit__ = mock.MagicMock(return_value=False)

                    with mock.patch.object(bs, "_ensure_access_web"):
                        with mock.patch.dict("sys.modules", {
                            "browser_agent": mock.MagicMock(),
                            "browser_agent.config": mock.MagicMock(
                                BrowserConfig=mock_config_cls
                            ),
                            "playwright": mock.MagicMock(),
                            "playwright.sync_api": mock.MagicMock(
                                sync_playwright=lambda: mock_pw
                            ),
                        }):
                            obj, code = _run_cmd(bs.cmd_state, td)

            self.assertNotEqual(code, 0)
            self.assertEqual(obj["code"], "state_unavailable")

    def test_state_values_not_dict_rejected(self):
        """state returns state_unavailable when values is a list."""
        with tempfile.TemporaryDirectory() as td:
            mock_config = mock.MagicMock()
            mock_config.browser_json = Path(td) / "browser.json"
            mock_config.browser_json.write_text(
                json.dumps({"pid": 99999, "cdp_port": 19222}),
                encoding="utf-8",
            )
            mock_config.read_metadata.return_value = {
                "pid": 99999, "cdp_port": 19222
            }
            mock_config_cls = mock.MagicMock(return_value=mock_config)

            with mock.patch.object(bs, "_is_pid_alive", return_value=True):
                with mock.patch.object(bs, "_is_port_open", return_value=True):
                    mock_page = mock.MagicMock()
                    mock_page.evaluate.return_value = {
                        "version": 1, "values": [1, 2, 3]
                    }
                    mock_context = mock.MagicMock()
                    mock_context.pages = [mock_page]
                    mock_browser = mock.MagicMock()
                    mock_browser.contexts = [mock_context]
                    mock_pw = mock.MagicMock()
                    mock_pw.chromium.connect_over_cdp.return_value = mock_browser
                    mock_pw.__enter__ = mock.MagicMock(return_value=mock_pw)
                    mock_pw.__exit__ = mock.MagicMock(return_value=False)

                    with mock.patch.object(bs, "_ensure_access_web"):
                        with mock.patch.dict("sys.modules", {
                            "browser_agent": mock.MagicMock(),
                            "browser_agent.config": mock.MagicMock(
                                BrowserConfig=mock_config_cls
                            ),
                            "playwright": mock.MagicMock(),
                            "playwright.sync_api": mock.MagicMock(
                                sync_playwright=lambda: mock_pw
                            ),
                        }):
                            obj, code = _run_cmd(bs.cmd_state, td)

            self.assertNotEqual(code, 0)
            self.assertEqual(obj["code"], "state_unavailable")

    def test_state_does_not_close_browser(self):
        """state connects via CDP but does NOT call browser.close()."""
        with tempfile.TemporaryDirectory() as td:
            mock_config = mock.MagicMock()
            mock_config.browser_json = Path(td) / "browser.json"
            mock_config.browser_json.write_text(
                json.dumps({"pid": 99999, "cdp_port": 19222}),
                encoding="utf-8",
            )
            mock_config.read_metadata.return_value = {
                "pid": 99999, "cdp_port": 19222
            }
            mock_config_cls = mock.MagicMock(return_value=mock_config)

            with mock.patch.object(bs, "_is_pid_alive", return_value=True):
                with mock.patch.object(bs, "_is_port_open", return_value=True):
                    mock_page = mock.MagicMock()
                    mock_page.evaluate.return_value = {
                        "version": 1, "values": {"x": 1}
                    }
                    mock_context = mock.MagicMock()
                    mock_context.pages = [mock_page]
                    mock_browser = mock.MagicMock()
                    mock_browser.contexts = [mock_context]
                    mock_pw = mock.MagicMock()
                    mock_pw.chromium.connect_over_cdp.return_value = mock_browser
                    mock_pw.__enter__ = mock.MagicMock(return_value=mock_pw)
                    mock_pw.__exit__ = mock.MagicMock(return_value=False)

                    with mock.patch.object(bs, "_ensure_access_web"):
                        with mock.patch.dict("sys.modules", {
                            "browser_agent": mock.MagicMock(),
                            "browser_agent.config": mock.MagicMock(
                                BrowserConfig=mock_config_cls
                            ),
                            "playwright": mock.MagicMock(),
                            "playwright.sync_api": mock.MagicMock(
                                sync_playwright=lambda: mock_pw
                            ),
                        }):
                            obj, code = _run_cmd(bs.cmd_state, td)

            self.assertEqual(code, 0)
            self.assertTrue(obj["success"])
            # The critical assertion: browser.close() must NOT be called
            mock_browser.close.assert_not_called()

    def test_status_does_not_close_browser(self):
        """status connects via CDP but does NOT call browser.close()."""
        with tempfile.TemporaryDirectory() as td:
            mock_config = mock.MagicMock()
            mock_config.browser_json = Path(td) / "browser.json"
            mock_config.browser_json.write_text(
                json.dumps({"pid": 99999, "cdp_port": 19222}),
                encoding="utf-8",
            )
            mock_config.read_metadata.return_value = {
                "pid": 99999, "cdp_port": 19222
            }
            mock_config_cls = mock.MagicMock(return_value=mock_config)

            with mock.patch.object(bs, "_is_pid_alive", return_value=True):
                with mock.patch.object(bs, "_is_port_open", return_value=True):
                    mock_page = mock.MagicMock()
                    mock_page.url = "file:///test.html"
                    mock_context = mock.MagicMock()
                    mock_context.pages = [mock_page]
                    mock_browser = mock.MagicMock()
                    mock_browser.contexts = [mock_context]
                    mock_pw = mock.MagicMock()
                    mock_pw.chromium.connect_over_cdp.return_value = mock_browser
                    mock_pw.__enter__ = mock.MagicMock(return_value=mock_pw)
                    mock_pw.__exit__ = mock.MagicMock(return_value=False)

                    with mock.patch.object(bs, "_ensure_access_web"):
                        with mock.patch.dict("sys.modules", {
                            "browser_agent": mock.MagicMock(),
                            "browser_agent.config": mock.MagicMock(
                                BrowserConfig=mock_config_cls
                            ),
                            "playwright": mock.MagicMock(),
                            "playwright.sync_api": mock.MagicMock(
                                sync_playwright=lambda: mock_pw
                            ),
                        }):
                            obj, code = _run_cmd(bs.cmd_status, td)

            self.assertEqual(code, 0)
            self.assertTrue(obj["success"])
            # The critical assertion: browser.close() must NOT be called
            mock_browser.close.assert_not_called()

    def test_status_alive_with_metadata(self):
        """status returns alive:true when pid+port are alive."""
        with tempfile.TemporaryDirectory() as td:
            mock_config = mock.MagicMock()
            mock_config.browser_json = Path(td) / "browser.json"
            mock_config.browser_json.write_text(
                json.dumps({"pid": 99999, "cdp_port": 19222}),
                encoding="utf-8",
            )
            mock_config.read_metadata.return_value = {
                "pid": 99999, "cdp_port": 19222
            }
            mock_config_cls = mock.MagicMock(return_value=mock_config)

            with mock.patch.object(bs, "_is_pid_alive", return_value=True):
                with mock.patch.object(bs, "_is_port_open", return_value=True):
                    # Mock playwright for CDP connect (may fail, that's ok)
                    with mock.patch.object(bs, "_ensure_access_web"):
                        with mock.patch.dict("sys.modules", {
                            "browser_agent": mock.MagicMock(),
                            "browser_agent.config": mock.MagicMock(
                                BrowserConfig=mock_config_cls
                            ),
                            "playwright": mock.MagicMock(),
                            "playwright.sync_api": mock.MagicMock(
                                sync_playwright=mock.MagicMock(
                                    side_effect=Exception("no pw")
                                )
                            ),
                        }):
                            obj, code = _run_cmd(bs.cmd_status, td)

            self.assertEqual(code, 0)
            self.assertTrue(obj["success"])
            self.assertTrue(obj["alive"])

    def test_status_no_side_effect_on_closed_browser(self):
        """status does not start browser when metadata shows dead process."""
        with tempfile.TemporaryDirectory() as td:
            mock_config = mock.MagicMock()
            mock_config.browser_json = Path(td) / "browser.json"
            mock_config.browser_json.write_text(
                json.dumps({"pid": 99999, "cdp_port": 19222}),
                encoding="utf-8",
            )
            mock_config.read_metadata.return_value = {
                "pid": 99999, "cdp_port": 19222
            }
            mock_config_cls = mock.MagicMock(return_value=mock_config)

            with mock.patch.object(bs, "_is_pid_alive", return_value=False):
                with mock.patch.object(bs, "_ensure_access_web"):
                    with mock.patch.dict("sys.modules", {
                        "browser_agent": mock.MagicMock(),
                        "browser_agent.config": mock.MagicMock(
                            BrowserConfig=mock_config_cls
                        ),
                    }):
                        obj, code = _run_cmd(bs.cmd_status, td)

            self.assertEqual(code, 0)
            self.assertTrue(obj["success"])
            self.assertFalse(obj["alive"])

    def test_recovery_after_close(self):
        """After browser close, state returns browser_not_running,
        then open can restart (mocked)."""
        with tempfile.TemporaryDirectory() as td:
            # Phase 1: state shows browser_not_running
            obj, code = _run_cmd(bs.cmd_state, td)
            self.assertEqual(obj["code"], "browser_not_running")

            # Phase 2: open can be called (mocked browser)
            html_file = Path(td) / "recover.html"
            html_file.write_text("<html></html>", encoding="utf-8")

            mock_page = mock.MagicMock()
            mock_browser_instance = mock.MagicMock()
            mock_browser_instance.page = mock_page
            mock_browser_cls = mock.MagicMock(
                return_value=mock_browser_instance
            )
            mock_config_cls = mock.MagicMock()

            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", {
                    "browser_agent": mock.MagicMock(),
                    "browser_agent.browser": mock.MagicMock(
                        Browser=mock_browser_cls
                    ),
                    "browser_agent.config": mock.MagicMock(
                        BrowserConfig=mock_config_cls
                    ),
                }):
                    obj2, code2 = _run_cmd(bs.cmd_open, td, str(html_file))

            self.assertEqual(code2, 0)
            self.assertTrue(obj2["success"])


# ===========================================================================
# Security Tests
# ===========================================================================

class TestSecurity(unittest.TestCase):
    """Security boundary tests."""

    def test_html_file_outside_session_rejected(self):
        """HTML file outside session-dir is rejected."""
        with tempfile.TemporaryDirectory() as session:
            with tempfile.TemporaryDirectory() as outside:
                html_file = Path(outside) / "secret.html"
                html_file.write_text("<html></html>", encoding="utf-8")
                obj, code = _run_cmd(bs.cmd_open, session, str(html_file))
            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "invalid_html_file")

    def test_path_traversal_rejected(self):
        """Path traversal attempts are rejected."""
        with tempfile.TemporaryDirectory() as td:
            html_file = Path(td) / ".." / "evil.html"
            # Don't actually create the file; resolve will normalize
            # Just test with a resolved path outside
            obj, code = _run_cmd(bs.cmd_open, td, str(html_file))
            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "invalid_html_file")

    def test_credentials_not_in_error_output(self):
        """Error output does not contain credential-like strings."""
        # Even if session-dir path contains sensitive info, error is generic
        obj, code = _run_cmd(bs.cmd_status, "/nonexistent/xyz")
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
        """_sanitize_error does not alter normal error messages."""
        normal = "session-dir does not exist: /tmp/nonexistent"
        self.assertEqual(bs._sanitize_error(normal), normal)

    def test_session_containment_uses_resolve(self):
        """Containment check uses Path.relative_to, not string prefix."""
        with tempfile.TemporaryDirectory() as td:
            # Create a sibling dir with similar prefix
            parent = Path(td).parent
            sibling = parent / (Path(td).name + "-evil")
            try:
                sibling.mkdir(exist_ok=True)
                html_file = sibling / "test.html"
                html_file.write_text("<html></html>", encoding="utf-8")
                obj, code = _run_cmd(bs.cmd_open, td, str(html_file))
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
                obj, code = _run_cmd(bs.cmd_open, td, str(f))
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
                    # Fallback: verify paths differ via _check_alive
                    alive1, _ = bs._check_alive(
                        mock.MagicMock(
                            browser_json=Path(td1) / "browser.json"
                        )
                    )
                    alive2, _ = bs._check_alive(
                        mock.MagicMock(
                            browser_json=Path(td2) / "browser.json"
                        )
                    )
                    self.assertFalse(alive1)
                    self.assertFalse(alive2)
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
                _run_cmd(bs.cmd_open, td, str(html_file))

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

            captured_url = {}
            mock_page = mock.MagicMock()
            def capture_goto(url):
                captured_url["url"] = url
            mock_page.goto = capture_goto
            mock_browser_instance = mock.MagicMock()
            mock_browser_instance.page = mock_page
            mock_browser_cls = mock.MagicMock(
                return_value=mock_browser_instance
            )
            mock_config_cls = mock.MagicMock()

            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", {
                    "browser_agent": mock.MagicMock(),
                    "browser_agent.browser": mock.MagicMock(
                        Browser=mock_browser_cls
                    ),
                    "browser_agent.config": mock.MagicMock(
                        BrowserConfig=mock_config_cls
                    ),
                }):
                    obj, code = _run_cmd(bs.cmd_open, td, str(html_file))

            expected_url = html_file.as_uri()
            self.assertEqual(captured_url["url"], expected_url)
            self.assertEqual(obj["url"], expected_url)

    def test_special_chars_in_path(self):
        """Paths with spaces and unicode are handled correctly."""
        with tempfile.TemporaryDirectory(prefix="pi-test ") as td:
            # Directory with space
            html_file = Path(td) / "test page.html"
            html_file.write_text("<html></html>", encoding="utf-8")

            captured_url = {}
            mock_page = mock.MagicMock()
            def capture_goto(url):
                captured_url["url"] = url
            mock_page.goto = capture_goto
            mock_browser_instance = mock.MagicMock()
            mock_browser_instance.page = mock_page
            mock_browser_cls = mock.MagicMock(
                return_value=mock_browser_instance
            )
            mock_config_cls = mock.MagicMock()

            with mock.patch.object(bs, "_ensure_access_web"):
                with mock.patch.dict("sys.modules", {
                    "browser_agent": mock.MagicMock(),
                    "browser_agent.browser": mock.MagicMock(
                        Browser=mock_browser_cls
                    ),
                    "browser_agent.config": mock.MagicMock(
                        BrowserConfig=mock_config_cls
                    ),
                }):
                    obj, code = _run_cmd(bs.cmd_open, td, str(html_file))

            self.assertEqual(code, 0)
            self.assertTrue(obj["success"])
            # URL should be properly encoded
            self.assertIn("file://", captured_url["url"])
            self.assertEqual(
                captured_url["url"],
                html_file.as_uri(),
            )


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
                obj, code = _run_cmd(bs.cmd_open, td, str(html_file))

            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "access_web_unavailable")

    def test_state_access_web_unavailable(self):
        """state returns access_web_unavailable when sibling not found."""
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(bs, "_find_access_web",
                                   return_value=None):
                obj, code = _run_cmd(bs.cmd_state, td)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "access_web_unavailable")

    def test_status_access_web_unavailable(self):
        """status returns access_web_unavailable when sibling not found."""
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(bs, "_find_access_web",
                                   return_value=None):
                obj, code = _run_cmd(bs.cmd_status, td)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "access_web_unavailable")

    def test_uncaught_exception_handled(self):
        """Uncaught exceptions produce internal_error, not traceback."""
        # Simulate the __main__ block's try/except
        captured = []
        original_json_out = bs._json_out

        def mock_json_out(obj):
            captured.append(obj)
            original_json_out(obj)

        with mock.patch.object(bs, "_json_out", side_effect=mock_json_out):
            try:
                raise RuntimeError("unexpected")
            except SystemExit:
                pass
            except Exception as e:
                try:
                    bs._fail(bs._current_cmd, "internal_error", str(e))
                except SystemExit:
                    pass

        self.assertTrue(len(captured) > 0)
        obj = captured[-1]
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "internal_error")
        self.assertEqual(obj["error"], "unexpected")


# ===========================================================================
# PID/Port Check Tests
# ===========================================================================

class TestPidPortChecks(unittest.TestCase):
    """Low-level pid and port check functions."""

    def test_is_pid_alive_false_for_bogus_pid(self):
        """_is_pid_alive returns False for non-existent PID."""
        self.assertFalse(bs._is_pid_alive(999999))

    def test_is_port_open_false_for_closed_port(self):
        """_is_port_open returns False for closed port."""
        # Use a port that's very unlikely to be open
        self.assertFalse(bs._is_port_open(59999, timeout=0.5))

    def test_is_port_open_true_for_listening_socket(self):
        """_is_port_open returns True for a listening socket."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
        try:
            self.assertTrue(bs._is_port_open(port, timeout=1.0))
        finally:
            s.close()

    def test_check_alive_no_metadata(self):
        """_check_alive returns False when browser.json doesn't exist."""
        with tempfile.TemporaryDirectory() as td:
            mock_config = mock.MagicMock()
            mock_config.browser_json = Path(td) / "nonexistent.json"
            alive, meta = bs._check_alive(mock_config)
            self.assertFalse(alive)
            self.assertIsNone(meta)

    def test_check_alive_dead_pid(self):
        """_check_alive returns False when PID is dead."""
        with tempfile.TemporaryDirectory() as td:
            meta_path = Path(td) / "browser.json"
            meta_path.write_text(
                json.dumps({"pid": 999999, "cdp_port": 59999}),
                encoding="utf-8",
            )
            mock_config = mock.MagicMock()
            mock_config.browser_json = meta_path
            mock_config.read_metadata.return_value = {
                "pid": 999999, "cdp_port": 59999
            }
            alive, meta = bs._check_alive(mock_config)
            self.assertFalse(alive)
            self.assertIsNotNone(meta)

    def test_corrupt_metadata_is_not_running(self):
        """Malformed pid/port metadata is treated as a stopped browser."""
        corrupt_values = [
            [],
            {"pid": "not-a-pid", "cdp_port": 9222},
            {"pid": -1, "cdp_port": 9222},
            {"pid": 1234, "cdp_port": 0},
            {"pid": 1234, "cdp_port": 70000},
            {"pid": True, "cdp_port": 9222},
        ]
        with tempfile.TemporaryDirectory() as td:
            mock_config = mock.MagicMock()
            mock_config.browser_json = Path(td) / "browser.json"
            mock_config.browser_json.write_text("{}", encoding="utf-8")
            for metadata in corrupt_values:
                with self.subTest(metadata=metadata):
                    mock_config.read_metadata.return_value = metadata
                    alive, returned = bs._check_alive(mock_config)
                    self.assertFalse(alive)
                    self.assertEqual(returned, metadata)


if __name__ == "__main__":
    unittest.main()
