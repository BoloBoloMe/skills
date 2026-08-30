"""present web server helper.

CLI commands:
  start  <port> <root> --bind <addr>  - Start / reuse daemonized web server
  status                             - Check server alive status
  stop                               - Stop server and remove runtime files
  add-dir <dir>                      - Mount a directory via control endpoint

stdout: single UTF-8 JSON object. Exit 0 success, exit 1 failure.

结构: run_* 是命令核心, 一律返回结果 dict, 不碰 stdout 与 sys.exit.
main() 是薄 CLI 适配器: argv 解析, JSON 序列化, 凭据脱敏, 退出码.
双角色: 父进程跑 CLI; start 内部以隐藏子命令 __serve__ re-exec 自身起子进程.
"""

import datetime
import errno
import fcntl
import json
import mimetypes
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote
from urllib.request import urlopen


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
# Runtime directory / lock
# ---------------------------------------------------------------------------

def _runtime_dir():
    """运行时目录: 系统临时目录/pi-present-web-<uid>, env 可覆盖前缀."""
    base = os.environ.get("PI_PRESENT_WEB_RUNTIME_DIR") or tempfile.gettempdir()
    return Path(base) / f"pi-present-web-{os.getuid()}"


def _ensure_runtime_dir(runtime_dir):
    """创建运行时目录并保证 0700."""
    runtime_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(runtime_dir, 0o700)


def _lock_runtime(runtime_dir):
    """获取运行时目录 flock 互斥锁, 返回文件对象 (调用方负责关闭)."""
    lock_path = runtime_dir / ".lock"
    fd = open(lock_path, "w+")
    fcntl.flock(fd.fileno(), fcntl.LOCK_EX)
    return fd


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
# Host / URL helpers
# ---------------------------------------------------------------------------

def _default_route_iface():
    """尝试从 /proc/net/route 读取默认路由接口 (Linux)."""
    try:
        with open("/proc/net/route", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 8 and parts[1] == "00000000" and parts[7] != "00000000":
                    return parts[0]
    except Exception:
        pass
    return None


def _iface_ipv4(iface):
    """尝试读取接口 IPv4 地址 (Linux ip 命令), 失败返回 None."""
    try:
        out = subprocess.check_output(
            ["ip", "-4", "-o", "addr", "show", iface],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
        for line in out.splitlines():
            parts = line.split()
            if "inet" in parts:
                idx = parts.index("inet")
                if idx + 1 < len(parts):
                    return parts[idx + 1].split("/")[0]
    except Exception:
        pass
    return None


def _detect_lan_host():
    """D011 优先级: SSH_CONNECTION 第 3 字段 > 默认路由接口 IP > 主机名."""
    ssh = os.environ.get("SSH_CONNECTION")
    if ssh:
        parts = ssh.split()
        if len(parts) >= 4:
            return parts[2]
    iface = _default_route_iface()
    if iface:
        ip = _iface_ipv4(iface)
        if ip:
            return ip
    try:
        return socket.gethostname()
    except Exception:
        return "localhost"


def _url_host(bind):
    """构造对外 URL 时使用的 host."""
    if bind in ("127.0.0.1", "::1"):
        return "localhost"
    return _detect_lan_host()


def _ping_host(bind):
    """本机 ping 控制面时使用的 host."""
    if bind in ("0.0.0.0", "::", "::0"):
        return "127.0.0.1"
    return bind


# ---------------------------------------------------------------------------
# Control ping
# ---------------------------------------------------------------------------

def _ping_control(bind, port, expected_pid=None, timeout=2):
    """GET /__control__/ping, 返回 (alive, payload)."""
    host = _ping_host(bind)
    url = f"http://{host}:{port}/__control__/ping"
    try:
        with urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("service") != "pi-present-web":
            return False, data
        if expected_pid is not None and data.get("pid") != expected_pid:
            return False, data
        return True, data
    except Exception:
        return False, None


def _probe_existing(runtime_dir):
    """读 server.json 并 ping 探活. 返回 (alive, server_info)."""
    json_path = runtime_dir / "server.json"
    if not json_path.exists():
        return False, None
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        alive, _ = _ping_control(data["bind"], data["port"], data.get("pid"))
        return alive, data
    except Exception:
        return False, None


# ---------------------------------------------------------------------------
# Startup error propagation (child → parent)
# ---------------------------------------------------------------------------

def _startup_error_path(runtime_dir):
    return runtime_dir / "startup_error"


def _write_startup_error(runtime_dir, code, message):
    """子进程启动失败时写入错误码与消息, 供父进程读取后区分失败类型."""
    path = _startup_error_path(runtime_dir)
    try:
        data = json.dumps({"code": code, "error": message}, ensure_ascii=False)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(data, encoding="utf-8")
        os.replace(tmp, path)
        os.chmod(path, 0o600)
    except Exception:
        pass


def _read_startup_error(runtime_dir):
    """读取并删除 startup_error; 不存在或损坏返回 None."""
    path = _startup_error_path(runtime_dir)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        path.unlink()
        return data
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Port / spawn helpers
# ---------------------------------------------------------------------------

def _check_port_available(bind, port):
    """试探 bind:port 是否可绑定.

    返回 (available, code_or_none): available=True 表示可绑定;
    available=False 时 code_or_none 为错误码 (port_in_use/internal_error).
    """
    host = "" if bind in ("0.0.0.0", "::") else bind
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        return True, None
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            return False, "port_in_use"
        return False, "internal_error"
    finally:
        s.close()


def _atomic_write_json(path, data):
    """原子写 JSON 文件并保持 0600."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    os.chmod(path, 0o600)


def _spawn_serve(port, root, bind):
    """re-exec 自身以隐藏子命令 __serve__ 起子进程."""
    script_path = Path(__file__).resolve()
    cmd = [sys.executable, str(script_path), "__serve__", str(port), root, bind]
    env = os.environ.copy()
    return subprocess.Popen(
        cmd,
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )


def _terminate_child(child):
    """SIGTERM 回收子进程; 超时再加 SIGKILL 兜底."""
    if child.poll() is not None:
        return
    try:
        child.terminate()
    except Exception:
        pass
    try:
        child.wait(timeout=2)
        return
    except Exception:
        pass
    if child.poll() is None:
        try:
            child.kill()
        except Exception:
            pass
    try:
        child.wait(timeout=2)
    except Exception:
        pass


def _wait_child_ready(child, bind, port, timeout=10):
    """轮询 ping 直到子进程就绪或超时/子进程退出."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if child.poll() is not None:
            break
        alive, _ = _ping_control(bind, port, timeout=2)
        if alive:
            return True
        time.sleep(0.1)
    return False


# ---------------------------------------------------------------------------
# HTTP handler & log
# ---------------------------------------------------------------------------

_LOG_LOCK = threading.Lock()


def _log(runtime_dir, message):
    """追加一条访问/错误日志到 server.log."""
    try:
        log_path = runtime_dir / "server.log"
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with _LOG_LOCK:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{ts} {message}\n")
    except Exception:
        pass


class _Handler(BaseHTTPRequestHandler):
    """HTTP 服务处理器: 控制面 ping + 扁平并集静态内容."""

    roots = []
    roots_lock = threading.RLock()
    runtime_dir = Path(".")
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        _log(self.runtime_dir, f"{self.client_address[0]} - {fmt % args}")

    def _write_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, code):
        """Send a plain HTTP error response; BaseHTTPRequestHandler.send_error
        would also log, which is fine, but we keep it short and avoid raising.
        """
        try:
            self.send_error(code)
        except BrokenPipeError:
            pass

    def do_GET(self):
        path = self.path
        # 控制面优先
        if path == "/__control__/ping":
            self._write_json(200, {"service": "pi-present-web", "pid": os.getpid()})
            return
        try:
            with self.roots_lock:
                roots = list(self.roots)
            rel = unquote(path).lstrip("/")
            if self._serve_static(roots, rel):
                return
            self._send_error(404)
        except Exception as e:
            _log(self.runtime_dir, f"GET {path} error: {e}")
            self._send_error(500)

    def _serve_static(self, roots, rel):
        for root in roots:
            root_path = Path(root).resolve()
            try:
                candidate = (root_path / rel).resolve()
            except (OSError, ValueError):
                continue
            # containment: 命中文件必须位于某个挂载目录内
            try:
                candidate.relative_to(root_path)
            except ValueError:
                continue
            if not candidate.exists():
                continue
            if candidate.is_dir():
                self._send_dir_listing(candidate)
                return True
            if candidate.is_file():
                self._send_file(candidate)
                return True
        return False

    def _send_file(self, path):
        ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        size = path.stat().st_size
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(size))
        self.end_headers()
        with open(path, "rb") as f:
            shutil.copyfileobj(f, self.wfile)
        return True

    def _send_dir_listing(self, path):
        try:
            entries = sorted(os.listdir(path))
        except OSError:
            self._send_error(404)
            return True
        lines = ["<html><body><h1>Directory listing</h1><ul>"]
        for e in entries:
            suffix = "/" if (path / e).is_dir() else ""
            lines.append(f'<li><a href="{e}{suffix}">{e}{suffix}</a></li>')
        lines.append("</ul></body></html>")
        body = "\n".join(lines).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return True


# ---------------------------------------------------------------------------
# Serve entry (child process only)
# ---------------------------------------------------------------------------

def _serve(port, root, bind):
    """子进程入口: 绑定端口, 写 server.json, 开 HTTP 服务."""
    port = int(port)
    root_resolved = str(Path(root).resolve())
    runtime_dir = _runtime_dir()
    _ensure_runtime_dir(runtime_dir)

    log_path = runtime_dir / "server.log"
    try:
        if log_path.exists() and log_path.stat().st_size > 10 * 1024 * 1024:
            log_path.write_text("", encoding="utf-8")
        log_path.touch(exist_ok=True)
        os.chmod(log_path, 0o600)
    except Exception:
        pass

    try:
        server = ThreadingHTTPServer((bind, port), _Handler)
    except OSError as e:
        code = "port_in_use" if e.errno == errno.EADDRINUSE else "internal_error"
        _log(runtime_dir, f"bind failed on {bind}:{port}: {e}")
        _write_startup_error(runtime_dir, code, f"bind failed on {bind}:{port}: {e}")
        sys.exit(1)

    _Handler.roots = [root_resolved]
    _Handler.runtime_dir = runtime_dir

    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    data = {
        "pid": os.getpid(),
        "port": port,
        "bind": bind,
        "roots": [root_resolved],
        "started_at": started_at,
    }
    _atomic_write_json(runtime_dir / "server.json", data)

    _log(runtime_dir, f"server started on {bind}:{port} pid={os.getpid()}")

    try:
        server.serve_forever()
    except Exception as e:
        _log(runtime_dir, f"serve error: {e}")
    finally:
        server.server_close()


# ---------------------------------------------------------------------------
# Core commands
# ---------------------------------------------------------------------------

def run_start(port, root, bind):
    """Start or reuse the daemonized web server."""
    err = _validate_root(root, command="start")
    if err is not None:
        return err
    try:
        port_int = int(port)
        if not 1 <= port_int <= 65535:
            raise ValueError("out of range")
    except Exception:
        return _err("start", "invalid_args", f"invalid port: {port}")
    if not isinstance(bind, str) or not bind:
        return _err("start", "invalid_args", "invalid bind address")

    root_resolved = str(Path(root).resolve())
    runtime_dir = _runtime_dir()
    try:
        _ensure_runtime_dir(runtime_dir)
    except Exception as e:
        return _err("start", "internal_error", f"cannot create runtime dir: {e}")

    lock_fd = None
    try:
        lock_fd = _lock_runtime(runtime_dir)
        alive, existing = _probe_existing(runtime_dir)
        if alive:
            # 存活实例: 按 D006 先校验 bind 一致, 一致则复用 (本 ISSUE 暂不实现 add-dir)
            if existing.get("bind") != bind:
                return _err(
                    "start",
                    "bind_conflict",
                    "existing instance bind differs; stop it first",
                )
            # 复用挂载尚未实现 (ISSUE-04); 现在明确失败, 不静默复用.
            return _err(
                "start",
                "internal_error",
                "实例已存活, 复用挂载尚未实现 (ISSUE-04)",
            )

        available, err_code = _check_port_available(bind, port_int)
        if not available:
            if err_code == "port_in_use":
                return _err("start", "port_in_use", f"port {port_int} already in use")
            return _err("start", "internal_error", f"cannot bind to {bind}:{port_int}")

        # 清除可能残留的启动错误文件, 避免误读旧错误.
        startup_err_path = _startup_error_path(runtime_dir)
        if startup_err_path.exists():
            try:
                startup_err_path.unlink()
            except Exception:
                pass

        child = _spawn_serve(port_int, root_resolved, bind)
        if not _wait_child_ready(child, bind, port_int):
            # 子进程启动失败或超时: 先读真实错误, 再强制回收.
            startup_err = _read_startup_error(runtime_dir)
            _terminate_child(child)
            if startup_err is not None:
                code = startup_err.get("code", "internal_error")
                if code == "port_in_use":
                    return _err("start", "port_in_use", f"port {port_int} already in use")
                return _err("start", "internal_error", startup_err.get("error", "server failed to start"))
            return _err("start", "internal_error", f"server failed to start within timeout")

        try:
            data = json.loads((runtime_dir / "server.json").read_text(encoding="utf-8"))
        except Exception as e:
            _terminate_child(child)
            return _err("start", "internal_error", f"server started but server.json missing: {e}")

        host = _detect_lan_host()
        return _success("start", {
            "url": f"http://{_url_host(bind)}:{port_int}/",
            "hostname": socket.gethostname(),
            "lan_ip": host,
            "port": port_int,
            "bind": bind,
            "roots": [root_resolved],
            "reused": False,
        })
    finally:
        if lock_fd is not None:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()


def run_status():
    """Check server alive status (本 ISSUE 不重建)."""
    runtime_dir = _runtime_dir()
    json_path = runtime_dir / "server.json"
    if not json_path.exists():
        return _success("status", {"alive": False})
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        return _err("status", "internal_error", f"cannot read server.json: {e}")

    alive, _ = _ping_control(data["bind"], data["port"], data.get("pid"), timeout=2)
    result = {"alive": alive}
    for key in ("pid", "port", "bind", "roots", "started_at"):
        result[key] = data.get(key)
    return _success("status", result)


def run_stop():
    """Stop server and remove runtime files."""
    return _err("stop", "internal_error", "not implemented in ISSUE-02")


def run_add_dir(directory):
    """Mount a directory via control endpoint."""
    return _err("add-dir", "internal_error", "not implemented in ISSUE-02")


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

    # 隐藏子命令: 子进程入口, 不输出 JSON
    if command == "__serve__":
        if len(argv) != 4:
            sys.stderr.write(
                "Usage: web_server.py __serve__ <port> <root> <bind>\n"
            )
            sys.exit(1)
        try:
            _serve(argv[1], argv[2], argv[3])
        except Exception as e:
            sys.stderr.write(f"serve failed: {e}\n")
            sys.exit(1)
        return

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
        elif command == "status":
            obj = run_status()
        elif command in ("stop", "add-dir"):
            obj = _err(command, "internal_error", "not implemented in ISSUE-02")
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
