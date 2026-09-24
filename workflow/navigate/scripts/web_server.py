"""navigate 展示服务.

CLI 子命令:
  start   - 启动/复用守护化展示服务 (同 uid 单例, 幂等; 默认端口 39271, 被占自动回退)
  status  - 读运行时文件报告存活状态与实际端口
  stop    - 停止服务并清理运行时文件

stdout: 单行 UTF-8 JSON, {"success": true/false, ...}. 退出码 0 成功 / 1 失败.

HTTP 端点 (绑定 0.0.0.0, 网段可读为已接受取舍, 不做认证/TLS):
  GET / 与 /index.html       - 占位页 (web/index.html, ISSUE-05 重写为完整 SPA)
  GET /api/roadmap?path=...  - 仅放行以 .json 结尾且存在的绝对路径, 否则结构化错误
  GET /__control__/ping      - 判活 (service/pid 指纹)

空闲自退: 最后一次请求 (覆盖所有端点含判活) 后 24h 无新请求则退出并清理运行时文件;
阈值经 NAVIGATE_WEB_TTL_SECONDS 可缩短 (测试用).

结构: run_* 是命令核心, 一律返回结果 dict, 不碰 stdout 与 sys.exit.
main() 是薄 CLI 适配器: argv 解析, JSON 序列化, 退出码.
双角色: 父进程跑 CLI; start 内部以隐藏子命令 __serve__ re-exec 自身起守护进程.
"""

import datetime
import errno
import fcntl
import json
import math
import os
import random
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.request import urlopen

SERVICE_NAME = "navigate-web"
DEFAULT_PORT = 39271  # D010: 避开 mailbox LLM 中转 38427-38436
BIND = "0.0.0.0"  # D009: 网段可读为已接受取舍
INDEX_PATH = Path(__file__).resolve().parent.parent / "web" / "index.html"

# 默认端口被占时的回退候选次数 (随机 49152-65534, 对齐 present 重建先例)
_PORT_FALLBACK_ATTEMPTS = 10

_DEFAULT_TTL_SECONDS = 86400  # 默认空闲 24h 自退


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
    return os.name == "posix"


# ---------------------------------------------------------------------------
# Runtime directory / lock
# ---------------------------------------------------------------------------

def _runtime_dir():
    """运行时目录: 系统临时目录/navigate-web-<uid>, env 可覆盖前缀 (测试隔离)."""
    base = os.environ.get("NAVIGATE_WEB_RUNTIME_DIR") or tempfile.gettempdir()
    return Path(base) / f"navigate-web-{os.getuid()}"


def _ensure_runtime_dir(runtime_dir):
    runtime_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(runtime_dir, 0o700)


def _lock_runtime(runtime_dir):
    """获取运行时目录 flock 互斥锁, 返回文件对象 (调用方负责关闭)."""
    lock_path = runtime_dir / ".lock"
    fd = open(lock_path, "w+")
    fcntl.flock(fd.fileno(), fcntl.LOCK_EX)
    return fd


# ---------------------------------------------------------------------------
# Host / URL helpers
# ---------------------------------------------------------------------------

def _default_route_iface():
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
    """SSH_CONNECTION 第 3 字段 > 默认路由接口 IP > 主机名."""
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


def _instance_url(port):
    return f"http://{_detect_lan_host()}:{port}/"


# ---------------------------------------------------------------------------
# Liveness ping (判活发真实请求, 不只看 pid 文件)
# ---------------------------------------------------------------------------

def _ping(port, expected_pid=None, timeout=2):
    """GET /__control__/ping, 返回 (alive, payload). bind 恒为 0.0.0.0, 经 loopback 判活."""
    url = f"http://127.0.0.1:{port}/__control__/ping"
    try:
        with urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("service") != SERVICE_NAME:
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
        alive, _ = _ping(int(data["port"]), data.get("pid"))
        return alive, data
    except Exception:
        return False, None


# ---------------------------------------------------------------------------
# Startup error propagation (child → parent)
# ---------------------------------------------------------------------------

def _startup_error_path(runtime_dir):
    return runtime_dir / "startup_error"


def _write_startup_error(runtime_dir, code, message):
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

def _atomic_write_json(path, data):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    os.chmod(path, 0o600)


def _spawn_serve(port):
    """re-exec 自身以隐藏子命令 __serve__ 起守护进程 (脱离父进程生命周期)."""
    script_path = Path(__file__).resolve()
    return subprocess.Popen(
        [sys.executable, str(script_path), "__serve__", str(port)],
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ.copy(),
    )


def _terminate_child(child):
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


def _wait_child_ready(child, port, expected_pid=None, timeout=10):
    """轮询 ping 直到子进程就绪或超时/子进程退出; ping 带 pid 指纹防误判."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if child.poll() is not None:
            break
        alive, _ = _ping(port, expected_pid=expected_pid, timeout=2)
        if alive:
            return True
        time.sleep(0.1)
    return False


# ---------------------------------------------------------------------------
# Process helpers (stop)
# ---------------------------------------------------------------------------

def _pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _wait_pid_exit(pid, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _pid_alive(pid):
            return True
        time.sleep(0.05)
    return not _pid_alive(pid)


def _ps_args_contains(pid, needle):
    """`ps -o args= -p <pid>` 校验命令行含 needle (防 pid 复用误杀)."""
    try:
        out = subprocess.run(
            ["ps", "-o", "args=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return False
    if out.returncode != 0:
        return False
    return needle in out.stdout


# ---------------------------------------------------------------------------
# HTTP handler & log
# ---------------------------------------------------------------------------

_LOG_LOCK = threading.Lock()


def _log(runtime_dir, message):
    try:
        log_path = runtime_dir / "server.log"
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with _LOG_LOCK:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{ts} {message}\n")
    except Exception:
        pass


class _Handler(BaseHTTPRequestHandler):
    """HTTP 处理器: 判活 ping + 占位页 + 路线图数据端点."""

    runtime_dir = Path(".")
    # 最后任一请求的 time.monotonic() 时间戳; 单属性赋值在 GIL 下原子,
    # 更新轻量无锁 (watchdog 只读). 覆盖所有端点含判活 ping.
    last_activity = 0.0
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        _log(self.runtime_dir, f"{self.client_address[0]} - {fmt % args}")

    def _note_activity(self):
        type(self).last_activity = time.monotonic()

    def _write_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_bytes(self, code, body, content_type):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, code):
        try:
            self.send_error(code)
        except BrokenPipeError:
            pass

    def do_GET(self):
        self._note_activity()
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            if path == "/__control__/ping":
                self._write_json(200, {"service": SERVICE_NAME, "pid": os.getpid()})
                return
            if path in ("/", "/index.html"):
                self._serve_index()
                return
            if path == "/api/roadmap":
                self._serve_roadmap(parsed)
                return
            self._send_error(404)
        except Exception as e:
            _log(self.runtime_dir, f"GET {self.path} error: {e}")
            self._send_error(500)

    def _serve_index(self):
        try:
            body = INDEX_PATH.read_bytes()
        except OSError as e:
            self._write_json(
                500,
                {"success": False, "code": "internal_error",
                 "error": f"index page unavailable: {e}"},
            )
            return
        self._write_bytes(200, body, "text/html; charset=utf-8")

    def _serve_roadmap(self, parsed):
        """数据端点: 仅放行以 .json 结尾且存在的绝对路径.

        .json 后缀检查在任何文件读取之前 (D009: 挡任意文件探测);
        错误响应为非 2xx + JSON {"success": false, "code", "error"},
        前端据此渲染友好提示.
        """
        query = parse_qs(parsed.query)
        path = query.get("path", [None])[0]
        if not path:
            self._write_json(
                400,
                {"success": False, "code": "invalid_args",
                 "error": "missing query param: path"},
            )
            return
        if not path.endswith(".json"):
            self._write_json(
                403,
                {"success": False, "code": "not_json",
                 "error": f"refused: only .json files are served: {path}"},
            )
            return
        if not os.path.isabs(path):
            self._write_json(
                400,
                {"success": False, "code": "invalid_args",
                 "error": f"path must be absolute: {path}"},
            )
            return
        target = Path(path)
        if not target.is_file():
            self._write_json(
                404,
                {"success": False, "code": "not_found",
                 "error": f"roadmap file not found: {path}"},
            )
            return
        try:
            body = target.read_bytes()
        except OSError as e:
            self._write_json(
                500,
                {"success": False, "code": "internal_error",
                 "error": f"cannot read roadmap file: {e}"},
            )
            return
        self._write_bytes(200, body, "application/json; charset=utf-8")


# ---------------------------------------------------------------------------
# Idle TTL
# ---------------------------------------------------------------------------

def _idle_ttl_seconds(runtime_dir):
    """空闲 TTL: env NAVIGATE_WEB_TTL_SECONDS 覆盖, 默认 86400s.
    非法值 (非数字/非正/非有限) 记日志并回退默认, 不拒绝启动."""
    raw = os.environ.get("NAVIGATE_WEB_TTL_SECONDS")
    if raw is None:
        return _DEFAULT_TTL_SECONDS
    try:
        value = float(raw)
    except ValueError:
        _log(runtime_dir, f"invalid NAVIGATE_WEB_TTL_SECONDS={raw!r}; fallback to {_DEFAULT_TTL_SECONDS}")
        return _DEFAULT_TTL_SECONDS
    if not math.isfinite(value) or value <= 0:
        _log(runtime_dir, f"non-positive/non-finite NAVIGATE_WEB_TTL_SECONDS={raw!r}; fallback to {_DEFAULT_TTL_SECONDS}")
        return _DEFAULT_TTL_SECONDS
    return value


# ---------------------------------------------------------------------------
# Serve entry (child process only)
# ---------------------------------------------------------------------------

def _serve(port):
    """守护进程入口: 绑定端口, 写 server.json, 开 HTTP 服务, 空闲自退."""
    port = int(port)
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
        server = ThreadingHTTPServer((BIND, port), _Handler)
    except OSError as e:
        code = "port_in_use" if e.errno == errno.EADDRINUSE else "internal_error"
        _log(runtime_dir, f"bind failed on {BIND}:{port}: {e}")
        _write_startup_error(runtime_dir, code, f"bind failed on {BIND}:{port}: {e}")
        sys.exit(1)

    _Handler.runtime_dir = runtime_dir

    data = {
        "pid": os.getpid(),
        "port": port,
        "bind": BIND,
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    _atomic_write_json(runtime_dir / "server.json", data)
    _log(runtime_dir, f"server started on {BIND}:{port} pid={os.getpid()}")

    # 空闲 TTL 自退: watchdog 周期检查, 空闲超 TTL -> shutdown, serve_forever
    # 返回后清理运行时文件, 进程自然退出. 检查间隔 = TTL/4, 下限 0.1s 上限 30s:
    # 默认 86400s 时 30s 一查, 秒级 TTL 时及时退出; 最坏退出延迟 = TTL + 间隔.
    ttl = _idle_ttl_seconds(runtime_dir)
    _Handler.last_activity = time.monotonic()
    interval = max(0.1, min(ttl / 4.0, 30.0))

    def _idle_watchdog():
        while True:
            time.sleep(interval)
            if time.monotonic() - _Handler.last_activity > ttl:
                _log(runtime_dir, f"idle exceeded ttl={ttl}s; shutting down")
                server.shutdown()
                return

    threading.Thread(target=_idle_watchdog, daemon=True).start()

    try:
        server.serve_forever()
    except Exception as e:
        _log(runtime_dir, f"serve error: {e}")
    finally:
        server.server_close()
        # 空闲自退路径清运行时文件; stop 路径经 SIGTERM 直接终止, 由 run_stop 清理.
        try:
            (runtime_dir / "server.json").unlink()
        except FileNotFoundError:
            pass


# ---------------------------------------------------------------------------
# Core commands
# ---------------------------------------------------------------------------

def run_start():
    """启动或复用守护进程; 默认端口 39271 被占时自动探测可用端口."""
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
            port = int(existing["port"])
            return _success("start", {
                "url": _instance_url(port),
                "hostname": socket.gethostname(),
                "lan_ip": _detect_lan_host(),
                "port": port,
                "bind": existing["bind"],
                "pid": existing.get("pid"),
                "reused": True,
            })

        candidates = [DEFAULT_PORT] + [
            random.randint(49152, 65534) for _ in range(_PORT_FALLBACK_ATTEMPTS)
        ]
        startup_err_path = _startup_error_path(runtime_dir)
        last_error = "no candidate port could bind"
        for port in candidates:
            if startup_err_path.exists():
                try:
                    startup_err_path.unlink()
                except Exception:
                    pass
            child = _spawn_serve(port)
            if _wait_child_ready(child, port, expected_pid=child.pid):
                try:
                    data = json.loads(
                        (runtime_dir / "server.json").read_text(encoding="utf-8")
                    )
                except Exception as e:
                    _terminate_child(child)
                    return _err("start", "internal_error",
                                f"server started but server.json missing: {e}")
                # 指纹校验: 就绪后 server.json 的 pid/port 须为本子进程与候选端口,
                # 不匹配按该候选失败处理, 继续回退.
                if data.get("pid") != child.pid or data.get("port") != port:
                    _terminate_child(child)
                    last_error = f"server.json fingerprint mismatch on port {port}"
                    continue
                return _success("start", {
                    "url": _instance_url(port),
                    "hostname": socket.gethostname(),
                    "lan_ip": _detect_lan_host(),
                    "port": port,
                    "bind": BIND,
                    "pid": child.pid,
                    "reused": False,
                })
            # 启动失败: 先读子进程回报的真实错误, 再回收子进程.
            # 端口探测与绑定之间有竞态: port_in_use 一律继续回退下一候选.
            err = _read_startup_error(runtime_dir)
            _terminate_child(child)
            if err is not None:
                if err.get("code") == "port_in_use":
                    last_error = err.get("error", last_error)
                    continue
                return _err("start", err.get("code", "internal_error"),
                            err.get("error", "server failed to start"))
            return _err("start", "internal_error",
                        "server failed to start within timeout")
        return _err("start", "port_in_use",
                    f"all candidate ports unavailable (default {DEFAULT_PORT} + "
                    f"{_PORT_FALLBACK_ATTEMPTS} fallbacks); last: {last_error}")
    finally:
        if lock_fd is not None:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()


def run_status():
    """读运行时文件报告存活状态与实际端口 (判活发真实请求)."""
    runtime_dir = _runtime_dir()
    json_path = runtime_dir / "server.json"
    if not json_path.exists():
        return _success("status", {"alive": False})
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        return _err("status", "internal_error", f"cannot read server.json: {e}")

    alive, _ = _ping(int(data["port"]), data.get("pid"), timeout=2)
    if alive:
        return _success("status", {
            "alive": True,
            "pid": data.get("pid"),
            "port": data.get("port"),
            "bind": data.get("bind"),
            "started_at": data.get("started_at"),
        })
    return _success("status", {"alive": False})


def run_stop():
    """停止服务并清理运行时文件; 无实例时幂等成功.

    不经 HTTP 控制面: ping 指纹比对 + `ps` 命令行校验, 不匹配报错不杀;
    服务半死 (ping 失联) 时经 ps 校验仍可终止.
    """
    runtime_dir = _runtime_dir()
    if not runtime_dir.exists():
        return _success("stop", {})

    lock_fd = _lock_runtime(runtime_dir)
    try:
        json_path = runtime_dir / "server.json"
        if not json_path.exists():
            return _success("stop", {})
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            pid = int(data["pid"])
        except Exception as e:
            return _err("stop", "internal_error", f"cannot read server.json: {e}")

        alive, payload = _ping(int(data["port"]), pid, timeout=2)
        if not alive and payload is not None:
            # 端口上有应答但指纹不匹配: 疑似无关服务占用, 报错不杀.
            return _err("stop", "internal_error",
                        f"endpoint on port {data['port']} answered with foreign "
                        f"fingerprint; refuse to stop pid {pid}")

        if not _pid_alive(pid):
            try:
                json_path.unlink()
            except FileNotFoundError:
                pass
            return _success("stop", {})

        if not _ps_args_contains(pid, str(Path(__file__).resolve())):
            return _err("stop", "internal_error",
                        f"pid {pid} command line does not contain this script; "
                        f"refuse to stop")

        os.kill(pid, signal.SIGTERM)
        if not _wait_pid_exit(pid, timeout=5.0):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            _wait_pid_exit(pid, timeout=2.0)

        try:
            json_path.unlink()
        except FileNotFoundError:
            pass
        return _success("stop", {})
    finally:
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
        lock_fd.close()


# ---------------------------------------------------------------------------
# CLI adapter (argv, JSON serialization, exit code)
# ---------------------------------------------------------------------------

def _emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0 if obj["success"] else 1


def main(argv=None):
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    command = argv[0] if argv else "unknown"

    # 隐藏子命令: 守护进程入口, 不输出 JSON
    if command == "__serve__":
        if len(argv) != 2:
            sys.stderr.write("Usage: web_server.py __serve__ <port>\n")
            sys.exit(1)
        try:
            _serve(argv[1])
        except Exception as e:
            sys.stderr.write(f"serve failed: {e}\n")
            sys.exit(1)
        return

    try:
        if not _is_posix():
            obj = _err(command, "not_supported", "only POSIX platforms are supported")
        elif command == "start":
            obj = run_start()
        elif command == "status":
            obj = run_status()
        elif command == "stop":
            obj = run_stop()
        elif command == "unknown":
            obj = _err(command, "internal_error",
                       "Usage: web_server.py <start|status|stop>")
        else:
            obj = _err(command, "internal_error", f"Unknown command: {command}")
    except Exception as e:
        obj = _err(command, "internal_error", str(e))
    sys.exit(_emit(obj))


if __name__ == "__main__":
    main()
