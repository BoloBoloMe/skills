"""adaptive-presentation browser session helper.

CLI commands:
  open   <session-dir> <html-file>  - Open HTML in isolated headed browser
  state  <session-dir>              - Read __PRESENTATION_STATE__ from page
  status <session-dir>              - Check browser alive status (side-effect free)

stdout: single UTF-8 JSON object. Exit 0 success, non-zero failure.
"""

import json
import os
import socket
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json_out(obj):
    """Write single JSON object to stdout."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _sanitize_error(msg):
    """Strip credential-like patterns from error messages.

    Technical Spec: error JSON must not contain credentials or full env vars.
    """
    import re
    # Redact common credential patterns in paths and exception strings
    patterns = [
        (r'(token[=:]\s*)([^\s,&"]+)', r'\1[REDACTED]'),
        (r'(api_key[=:]\s*)([^\s,&"]+)', r'\1[REDACTED]'),
        (r'(secret[=:]\s*)([^\s,&"]+)', r'\1[REDACTED]'),
        (r'(password[=:]\s*)([^\s,&"]+)', r'\1[REDACTED]'),
        (r'(auth[=:]\s*)([^\s,&"]+)', r'\1[REDACTED]'),
        (r'(credential[=:]\s*)([^\s,&"]+)', r'\1[REDACTED]'),
        (r'(bearer\s+)([^\s,&"]+)', r'\1[REDACTED]'),
    ]
    for pattern, replacement in patterns:
        msg = re.sub(pattern, replacement, msg, flags=re.IGNORECASE)
    return msg


def _fail(command, code, error, exit_code=1):
    """Write failure JSON and exit."""
    _json_out({
        "success": False,
        "command": command,
        "code": code,
        "error": _sanitize_error(error),
    })
    sys.exit(exit_code)


def _ok(command, payload):
    """Write success JSON and exit."""
    obj = {"success": True, "command": command}
    obj.update(payload)
    _json_out(obj)
    sys.exit(0)


def _find_access_web():
    """Locate sibling access-web/browse/ and return its path.

    Expected layout:
      general/adaptive-presentation/scripts/browser_session.py
      general/access-web/browse/browser_agent/
    """
    script_dir = Path(__file__).resolve().parent
    access_web_browse = script_dir.parent.parent / "access-web" / "browse"
    if (access_web_browse / "browser_agent" / "__init__.py").is_file():
        return access_web_browse
    return None


def _ensure_access_web():
    """Ensure access-web is on sys.path. Raises RuntimeError if unavailable."""
    aw_path = _find_access_web()
    if aw_path is None:
        raise RuntimeError("access-web not found at expected sibling path")
    aw_str = str(aw_path)
    if aw_str not in sys.path:
        sys.path.insert(0, aw_str)


def _validate_session_dir(session_dir_str):
    """Validate session-dir. Returns Path or calls _fail."""
    # Check absolute BEFORE resolve, otherwise resolve() makes relative paths absolute
    if not Path(session_dir_str).is_absolute():
        _fail(_current_cmd, "invalid_session_dir",
              "session-dir must be absolute path")
    try:
        p = Path(session_dir_str).resolve()
    except Exception as e:
        _fail(_current_cmd, "invalid_session_dir",
              f"Cannot resolve path: {e}")
    if not p.exists():
        _fail(_current_cmd, "invalid_session_dir",
              f"session-dir does not exist: {p}")
    if not p.is_dir():
        _fail(_current_cmd, "invalid_session_dir",
              f"session-dir is not a directory: {p}")
    return p


def _validate_html_file(session_dir, html_file_str):
    """Validate html-file. Returns Path or calls _fail."""
    # Check absolute BEFORE resolve (same reasoning as _validate_session_dir)
    if not Path(html_file_str).is_absolute():
        _fail("open", "invalid_html_file",
              "html-file must be absolute path")
    try:
        html_path = Path(html_file_str).resolve()
    except Exception as e:
        _fail("open", "invalid_html_file",
              f"Cannot resolve path: {e}")
    if not html_path.exists():
        _fail("open", "invalid_html_file",
              f"HTML file does not exist: {html_path}")
    if not html_path.is_file():
        _fail("open", "invalid_html_file",
              f"HTML path is not a regular file: {html_path}")
    if html_path.suffix.lower() != ".html":
        _fail("open", "invalid_html_file",
              f"File extension must be .html, got: {html_path.suffix}")
    # Containment: html must be inside session-dir
    try:
        html_path.relative_to(session_dir)
    except ValueError:
        _fail("open", "invalid_html_file",
              f"HTML file not inside session-dir: {html_path}")
    return html_path


def _is_pid_alive(pid):
    """Cross-platform PID liveness check."""
    try:
        if os.name == "nt":
            import re as _re
            import subprocess as _sp
            result = _sp.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                stdout=_sp.PIPE, stderr=_sp.PIPE,
                text=True, check=False,
            )
            return _re.search(rf"\b{pid}\b", result.stdout) is not None
        else:
            os.kill(pid, 0)
            return True
    except (ProcessLookupError, OSError):
        return False


def _is_port_open(port, timeout=1.0):
    """Check if TCP port is accepting connections."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except Exception:
        return False


def _check_alive(config):
    """Check browser alive via metadata pid+CDP port. Side-effect free."""
    if not config.browser_json.exists():
        return False, None
    try:
        meta = config.read_metadata()
    except Exception:
        return False, None
    if not isinstance(meta, dict):
        return False, meta
    pid = meta.get("pid")
    cdp_port = meta.get("cdp_port")
    if (
        not isinstance(pid, int)
        or isinstance(pid, bool)
        or pid <= 0
        or not isinstance(cdp_port, int)
        or isinstance(cdp_port, bool)
        or not 1 <= cdp_port <= 65535
    ):
        return False, meta
    alive = _is_pid_alive(pid) and _is_port_open(cdp_port)
    return alive, meta


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

_current_cmd = "unknown"


def cmd_open(session_dir_str, html_file_str):
    """Open HTML file in isolated headed browser session."""
    global _current_cmd
    _current_cmd = "open"

    session_dir = _validate_session_dir(session_dir_str)
    html_path = _validate_html_file(session_dir, html_file_str)

    # Set headed mode before any browser import
    os.environ["BROWSER_HEADED"] = "true"

    # Import access-web
    try:
        _ensure_access_web()
    except RuntimeError as e:
        _fail("open", "access_web_unavailable", str(e))

    try:
        from browser_agent.browser import Browser
        from browser_agent.config import BrowserConfig
    except ImportError as e:
        _fail("open", "access_web_unavailable",
              f"Cannot import browser_agent: {e}")

    # Navigate
    try:
        config = BrowserConfig(cwd=str(session_dir))
        browser = Browser(config)
        browser.start()
    except Exception as e:
        _fail("open", "browser_unavailable", f"Browser start failed: {e}")

    try:
        page = browser.page
        url = html_path.as_uri()
        page.goto(url)
    except Exception as e:
        _fail("open", "navigation_failed", f"Navigation failed: {e}")

    _ok("open", {"url": url, "alive": True})


def cmd_state(session_dir_str):
    """Read __PRESENTATION_STATE__ from page. Must not start browser."""
    global _current_cmd
    _current_cmd = "state"

    session_dir = _validate_session_dir(session_dir_str)

    # Import access-web (import only, no browser start)
    try:
        _ensure_access_web()
    except RuntimeError as e:
        _fail("state", "access_web_unavailable", str(e))

    try:
        from browser_agent.config import BrowserConfig
    except ImportError as e:
        _fail("state", "access_web_unavailable",
              f"Cannot import browser_agent: {e}")

    config = BrowserConfig(cwd=str(session_dir))
    alive, meta = _check_alive(config)

    if not alive:
        _fail("state", "browser_not_running",
              "Chromium is not running for this session")

    cdp_port = meta.get("cdp_port")

    # Connect via CDP and read state (no browser start)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(
                f"http://127.0.0.1:{cdp_port}"
            )
            try:
                context = browser.contexts[0] if browser.contexts else None
                if context is None or not context.pages:
                    _fail("state", "state_unavailable",
                          "No page available to read state")
                page = context.pages[0]
                state = page.evaluate("window.__PRESENTATION_STATE__")
            finally:
                # Do NOT call browser.close() on a CDP connection;
                # it kills the remote Chromium process (NFR-003).
                # sync_playwright() context manager handles local cleanup.
                pass
    except Exception as e:
        _fail("state", "state_unavailable",
              f"Failed to read page state: {e}")

    # Validate state shape
    if not isinstance(state, dict):
        _fail("state", "state_unavailable",
              "State object is not a dict")
    version = state.get("version")
    if not isinstance(version, int) or isinstance(version, bool):
        _fail("state", "state_unavailable",
              f"State version must be int, got {type(version).__name__}: {version}")
    if version != 1:
        _fail("state", "state_unavailable",
              f"Unsupported state version: {version}")
    values = state.get("values")
    if not isinstance(values, dict):
        _fail("state", "state_unavailable",
              f"State values must be dict, got {type(values).__name__}")

    _ok("state", {"alive": True, "state": state})


def cmd_status(session_dir_str):
    """Check browser status. Side-effect free, must not start browser."""
    global _current_cmd
    _current_cmd = "status"

    session_dir = _validate_session_dir(session_dir_str)

    # Import access-web (import only, no browser start)
    try:
        _ensure_access_web()
    except RuntimeError as e:
        _fail("status", "access_web_unavailable", str(e))

    try:
        from browser_agent.config import BrowserConfig
    except ImportError as e:
        _fail("status", "access_web_unavailable",
              f"Cannot import browser_agent: {e}")

    config = BrowserConfig(cwd=str(session_dir))
    alive, meta = _check_alive(config)

    result = {"alive": alive}

    if alive and meta:
        cdp_port = meta.get("cdp_port")
        # Try to get URL/title via CDP (side-effect free read)
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.connect_over_cdp(
                    f"http://127.0.0.1:{cdp_port}"
                )
                try:
                    context = (
                        browser.contexts[0] if browser.contexts else None
                    )
                    if context and context.pages:
                        page = context.pages[0]
                        result["url"] = page.url
                finally:
                    # Do NOT call browser.close(); see cmd_state.
                    pass
        except Exception:
            pass

    _ok("status", result)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global _current_cmd
    if len(sys.argv) < 2:
        _fail("unknown", "internal_error",
              "Usage: browser_session.py <open|state|status> <session-dir> [html-file]")

    command = sys.argv[1]
    _current_cmd = command

    if command == "open":
        if len(sys.argv) < 4:
            _fail("open", "internal_error",
                  "Usage: browser_session.py open <session-dir> <html-file>")
        cmd_open(sys.argv[2], sys.argv[3])
    elif command == "state":
        if len(sys.argv) < 3:
            _fail("state", "internal_error",
                  "Usage: browser_session.py state <session-dir>")
        cmd_state(sys.argv[2])
    elif command == "status":
        if len(sys.argv) < 3:
            _fail("status", "internal_error",
                  "Usage: browser_session.py status <session-dir>")
        cmd_status(sys.argv[2])
    else:
        _fail(command, "internal_error", f"Unknown command: {command}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        _fail(_current_cmd, "internal_error", str(e))
