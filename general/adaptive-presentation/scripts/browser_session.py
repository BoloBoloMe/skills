"""adaptive-presentation browser session helper.

CLI commands:
  open   <session-dir> <html-file>  - Open HTML in isolated headed browser
  state  <session-dir>              - Read __PRESENTATION_STATE__ from page
  status <session-dir>              - Check browser alive status (side-effect free)

stdout: single UTF-8 JSON object. Exit 0 success, non-zero failure.

结构: run_* 是展示会话核心 — 校验, 领域 state 检查, 经 browser_agent 公开
接口 (get_session / probe / attached_context) 动作, 一律返回结果 dict,
不碰 stdout 与 sys.exit. main() 是薄 CLI 适配器: argv 解析, JSON 序列化,
凭据脱敏, 退出码.
"""

import json
import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Result construction (core produces dicts, never prints or exits)
# ---------------------------------------------------------------------------

def _err(command, code, error):
    return {"success": False, "command": command, "code": code, "error": error}


def _success(command, payload):
    return {"success": True, "command": command, **payload}


# ---------------------------------------------------------------------------
# access-web location
# ---------------------------------------------------------------------------

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


def _import_attach():
    """Import browser_agent 只读会话视图. Raises RuntimeError if unavailable."""
    _ensure_access_web()
    try:
        from browser_agent.attach import attached_context
        from browser_agent.attach import probe
    except ImportError as e:
        raise RuntimeError(f"Cannot import browser_agent: {e}")
    return attached_context, probe


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------

def _validate_session_dir(session_dir_str, command):
    """Validate session-dir. Returns (Path, None) or (None, error-dict)."""
    # Check absolute BEFORE resolve, otherwise resolve() makes relative paths absolute
    if not Path(session_dir_str).is_absolute():
        return None, _err(command, "invalid_session_dir",
                          "session-dir must be absolute path")
    try:
        p = Path(session_dir_str).resolve()
    except Exception as e:
        return None, _err(command, "invalid_session_dir",
                          f"Cannot resolve path: {e}")
    if not p.exists():
        return None, _err(command, "invalid_session_dir",
                          f"session-dir does not exist: {p}")
    if not p.is_dir():
        return None, _err(command, "invalid_session_dir",
                          f"session-dir is not a directory: {p}")
    return p, None


def _validate_html_file(session_dir, html_file_str):
    """Validate html-file. Returns (Path, None) or (None, error-dict)."""
    # Check absolute BEFORE resolve (same reasoning as _validate_session_dir)
    if not Path(html_file_str).is_absolute():
        return None, _err("open", "invalid_html_file",
                          "html-file must be absolute path")
    try:
        html_path = Path(html_file_str).resolve()
    except Exception as e:
        return None, _err("open", "invalid_html_file",
                          f"Cannot resolve path: {e}")
    if not html_path.exists():
        return None, _err("open", "invalid_html_file",
                          f"HTML file does not exist: {html_path}")
    if not html_path.is_file():
        return None, _err("open", "invalid_html_file",
                          f"HTML path is not a regular file: {html_path}")
    if html_path.suffix.lower() != ".html":
        return None, _err("open", "invalid_html_file",
                          f"File extension must be .html, got: {html_path.suffix}")
    # Containment: html must be inside session-dir
    try:
        html_path.relative_to(session_dir)
    except ValueError:
        return None, _err("open", "invalid_html_file",
                          f"HTML file not inside session-dir: {html_path}")
    return html_path, None


# ---------------------------------------------------------------------------
# Core commands (return result dicts)
# ---------------------------------------------------------------------------

def run_open(session_dir_str, html_file_str):
    """Open HTML file in isolated headed browser session."""
    command = "open"

    session_dir, err = _validate_session_dir(session_dir_str, command)
    if err is not None:
        return err
    html_path, err = _validate_html_file(session_dir, html_file_str)
    if err is not None:
        return err

    # Set headed mode before any browser import
    os.environ["BROWSER_HEADED"] = "true"

    try:
        _ensure_access_web()
    except RuntimeError as e:
        return _err(command, "access_web_unavailable", str(e))
    try:
        from browser_agent import get_session
    except ImportError as e:
        return _err(command, "access_web_unavailable",
                    f"Cannot import browser_agent: {e}")

    # 首次 get_session(cwd=...) 绑定展示会话目录; .page 触发脱离式启动/复用
    try:
        page = get_session(cwd=str(session_dir)).page
    except Exception as e:
        return _err(command, "browser_unavailable", f"Browser start failed: {e}")

    try:
        url = html_path.as_uri()
        page.goto(url)
    except Exception as e:
        return _err(command, "navigation_failed", f"Navigation failed: {e}")

    return _success(command, {"url": url, "alive": True})


def run_state(session_dir_str):
    """Read __PRESENTATION_STATE__ from page. Must not start browser."""
    command = "state"

    session_dir, err = _validate_session_dir(session_dir_str, command)
    if err is not None:
        return err

    try:
        attached_context, probe = _import_attach()
    except RuntimeError as e:
        return _err(command, "access_web_unavailable", str(e))

    cwd = str(session_dir)
    if not probe(cwd=cwd).alive:
        return _err(command, "browser_not_running",
                    "Chromium is not running for this session")

    # 只读附加: 不启动浏览器; attach 内部遵守 "CDP 连接不 close" 纪律
    try:
        with attached_context(cwd=cwd) as context:
            if context is None or not context.pages:
                return _err(command, "state_unavailable",
                            "No page available to read state")
            state = context.pages[0].evaluate("window.__PRESENTATION_STATE__")
    except Exception as e:
        return _err(command, "state_unavailable",
                    f"Failed to read page state: {e}")

    # Validate state shape
    if not isinstance(state, dict):
        return _err(command, "state_unavailable",
                    "State object is not a dict")
    version = state.get("version")
    if not isinstance(version, int) or isinstance(version, bool):
        return _err(command, "state_unavailable",
                    f"State version must be int, got {type(version).__name__}: {version}")
    if version != 1:
        return _err(command, "state_unavailable",
                    f"Unsupported state version: {version}")
    values = state.get("values")
    if not isinstance(values, dict):
        return _err(command, "state_unavailable",
                    f"State values must be dict, got {type(values).__name__}")

    return _success(command, {"alive": True, "state": state})


def run_status(session_dir_str):
    """Check browser status. Side-effect free, must not start browser."""
    command = "status"

    session_dir, err = _validate_session_dir(session_dir_str, command)
    if err is not None:
        return err

    try:
        attached_context, probe = _import_attach()
    except RuntimeError as e:
        return _err(command, "access_web_unavailable", str(e))

    cwd = str(session_dir)
    alive = probe(cwd=cwd).alive
    result = {"alive": alive}

    if alive:
        # 只读附加读取 URL; 失败不致命, 降级为仅存活标记
        try:
            with attached_context(cwd=cwd) as context:
                if context is not None and context.pages:
                    result["url"] = context.pages[0].url
        except Exception:
            pass

    return _success(command, result)


# ---------------------------------------------------------------------------
# CLI adapter (argv, JSON serialization, sanitization, exit code)
# ---------------------------------------------------------------------------

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


def _emit(obj):
    """Serialize one result object to stdout; return exit code."""
    if not obj.get("success") and isinstance(obj.get("error"), str):
        obj = dict(obj, error=_sanitize_error(obj["error"]))
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0 if obj["success"] else 1


def main(argv=None):
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    command = argv[0] if argv else "unknown"
    try:
        if command == "open":
            if len(argv) < 3:
                obj = _err(command, "internal_error",
                           "Usage: browser_session.py open <session-dir> <html-file>")
            else:
                obj = run_open(argv[1], argv[2])
        elif command == "state":
            if len(argv) < 2:
                obj = _err(command, "internal_error",
                           "Usage: browser_session.py state <session-dir>")
            else:
                obj = run_state(argv[1])
        elif command == "status":
            if len(argv) < 2:
                obj = _err(command, "internal_error",
                           "Usage: browser_session.py status <session-dir>")
            else:
                obj = run_status(argv[1])
        elif command == "unknown":
            obj = _err(command, "internal_error",
                       "Usage: browser_session.py <open|state|status> <session-dir> [html-file]")
        else:
            obj = _err(command, "internal_error", f"Unknown command: {command}")
    except Exception as e:
        obj = _err(command, "internal_error", str(e))
    sys.exit(_emit(obj))


if __name__ == "__main__":
    main()
