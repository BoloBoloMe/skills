"""present web server helper.

CLI commands:
  start  <port> <root> --bind <addr>  - Start / reuse daemonized web server
  status                             - Check server alive status
  stop                               - Stop server and remove runtime files
  add-dir <dir>                      - Mount a directory via control endpoint

stdout: single UTF-8 JSON object. Exit 0 success, exit 1 failure.

结构: run_* 是命令核心, 一律返回结果 dict, 不碰 stdout 与 sys.exit.
main() 是薄 CLI 适配器: argv 解析, JSON 序列化, 凭据脱敏, 退出码.
本 ISSUE 只搭 CLI 骨架与参数校验, run_* 暂返回 internal_error 桩.
"""

import json
import os
import re
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
# Platform guard
# ---------------------------------------------------------------------------

def _is_posix():
    """Return whether the runtime platform is POSIX."""
    return os.name == "posix"


# ---------------------------------------------------------------------------
# Argument parsing helpers
# ---------------------------------------------------------------------------

def _parse_start(argv):
    """Parse start argv. Return (port, root, bind) or None if malformed."""
    if len(argv) != 4:
        return None
    port, root, dash, bind = argv
    if dash != "--bind":
        return None
    if not port or not root or not bind:
        return None
    return port, root, bind


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------

def _validate_root(root_str, command="start"):
    """Validate root directory. Returns error dict or None."""
    if not Path(root_str).is_absolute():
        return _err(command, "invalid_args", "root must be absolute path")
    try:
        p = Path(root_str).resolve()
    except Exception as e:
        return _err(command, "invalid_args", f"Cannot resolve root path: {e}")
    if not p.exists():
        return _err(command, "invalid_args", f"root does not exist: {p}")
    if not p.is_dir():
        return _err(command, "invalid_args", f"root is not a directory: {p}")
    return None


# ---------------------------------------------------------------------------
# Core commands (return result dicts; ISSUE-01 stubs)
# ---------------------------------------------------------------------------

def run_start(port, root, bind):
    """Start or reuse the daemonized web server."""
    err = _validate_root(root, command="start")
    if err is not None:
        return err
    return _err("start", "internal_error", "not implemented in ISSUE-01")


def run_status():
    """Check server alive status."""
    return _err("status", "internal_error", "not implemented in ISSUE-01")


def run_stop():
    """Stop server and remove runtime files."""
    return _err("stop", "internal_error", "not implemented in ISSUE-01")


def run_add_dir(directory):
    """Mount a directory via control endpoint."""
    return _err("add-dir", "internal_error", "not implemented in ISSUE-01")


# ---------------------------------------------------------------------------
# CLI adapter (argv, JSON serialization, sanitization, exit code)
# ---------------------------------------------------------------------------

def _sanitize_error(msg):
    """Strip credential-like patterns from error messages.

    Technical Spec: error JSON must not contain credentials or full env vars.
    """
    patterns = [
        (r"(token[=:]\s*)([^\s,&\"]+)", r"\1[REDACTED]"),
        (r"(api_key[=:]\s*)([^\s,&\"]+)", r"\1[REDACTED]"),
        (r"(secret[=:]\s*)([^\s,&\"]+)", r"\1[REDACTED]"),
        (r"(password[=:]\s*)([^\s,&\"]+)", r"\1[REDACTED]"),
        (r"(auth[=:]\s*)([^\s,&\"]+)", r"\1[REDACTED]"),
        (r"(credential[=:]\s*)([^\s,&\"]+)", r"\1[REDACTED]"),
        (r"(bearer\s+)([^\s,&\"]+)", r"\1[REDACTED]"),
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
        if not _is_posix():
            obj = _err(command, "not_supported", "only POSIX platforms are supported")
        elif command == "start":
            parsed = _parse_start(argv[1:])
            if parsed is None:
                obj = _err(
                    "start",
                    "invalid_args",
                    "Usage: web_server.py start <port> <root> --bind <addr>",
                )
            else:
                port, root, bind = parsed
                obj = run_start(port, root, bind)
        elif command in ("status", "stop", "add-dir"):
            obj = _err(command, "internal_error", "not implemented in ISSUE-01")
        elif command == "unknown":
            obj = _err(
                command,
                "internal_error",
                "Usage: web_server.py <start|status|stop|add-dir> ...",
            )
        else:
            obj = _err(command, "internal_error", f"Unknown command: {command}")
    except Exception as e:
        obj = _err(command, "internal_error", str(e))
    sys.exit(_emit(obj))


if __name__ == "__main__":
    main()
