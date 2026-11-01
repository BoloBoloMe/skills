"""present web server helper.

CLI commands:
  start  <port> <root> --bind <addr> [--fixed-port] [--lan-host <addr>]
                                     - Start / reuse daemonized web server
  status [--lan-host <addr>]         - Check server alive status, rebuild if dead
  stop                               - Stop server and remove runtime files
  add-dir <dir>                      - Mount a directory via control endpoint

交付地址解析 (D011): 宿主 --lan-host > 已确认地址文件 > 候选 (待用户确认);
容器固定用 SWT_HOST_LAN_IP + SWT_HOST_WEB_PORT. 解析不到不阻止服务启动,
只出 address_missing 缺口; loopback bind 只给 localhost + loopback_bind 提示.

stdout: single UTF-8 JSON object. Exit 0 success, exit 1 failure.

结构: run_* 是命令核心, 一律返回结果 dict, 不碰 stdout 与 sys.exit.
main() 是薄 CLI 适配器: argv 解析, JSON 序列化, 凭据脱敏, 退出码.
双角色: 父进程跑 CLI; start 内部以隐藏子命令 __serve__ re-exec 自身起子进程.
"""

import datetime
import errno
import fcntl
import ipaddress
import json
import mimetypes
import os
import random
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
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ---------------------------------------------------------------------------
# Result construction (core produces dicts, never prints or exits)
# ---------------------------------------------------------------------------

def _err(command, code, error):
    return {"success": False, "command": command, "code": code, "error": error}


def _success(command, payload):
    return {"success": True, "command": command, **payload}


# ---------------------------------------------------------------------------
# Delivery address constants (D011)
# ---------------------------------------------------------------------------

# 容器识别标记: 存在即容器场景 (容器交付用 SWT_HOST_LAN_IP + SWT_HOST_WEB_PORT).
CONTAINER_MARKER_PATH = "/run/.containerenv"

# 隧道/虚拟接口前缀: 这些接口上的全局地址局域网够不着, 不作候选交付地址.
TUNNEL_INTERFACE_PREFIXES = (
    "tun", "tap", "wg", "ppp", "utun", "ts", "tailscale",
    "docker", "veth", "br-", "virbr", "zt", "podman",
)


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
    """Parse start argv.

    Return (port, root, bind, fixed_port, lan_host) or None if malformed.
    --lan-host 是本次展示明确指定的局域网地址 (D011), 只属本次调用上下文.
    """
    positional = []
    bind = None
    fixed_port = False
    lan_host = None
    i = 0
    while i < len(argv):
        token = argv[i]
        if token == "--bind":
            if i + 1 >= len(argv) or not argv[i + 1]:
                return None
            bind = argv[i + 1]
            i += 2
        elif token == "--lan-host":
            if i + 1 >= len(argv) or not argv[i + 1]:
                return None
            lan_host = argv[i + 1]
            i += 2
        elif token == "--fixed-port":
            fixed_port = True
            i += 1
        elif token.startswith("--"):
            return None
        else:
            positional.append(token)
            i += 1
    if len(positional) != 2 or bind is None:
        return None
    port, root = positional
    if not port or not root:
        return None
    return port, root, bind, fixed_port, lan_host


def _parse_lan_host(argv):
    """Parse optional --lan-host <addr>. Return (lan_host, ok)."""
    lan_host = None
    i = 0
    while i < len(argv):
        if argv[i] == "--lan-host":
            if i + 1 >= len(argv) or not argv[i + 1]:
                return None, False
            lan_host = argv[i + 1]
            i += 2
        else:
            return None, False
    return lan_host, True


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

def _in_container():
    """容器识别 (D011): /run/.containerenv 存在即容器场景."""
    return Path(CONTAINER_MARKER_PATH).exists()


def _host_confirmed_address_path():
    """宿主已确认局域网地址文件 (swt 默认 records_root 根级, 只读)."""
    return Path.home() / ".agents" / "sandbox-worktree" / "lan-address"


def _read_confirmed_lan_address(path=None):
    """读已确认局域网地址; 无文件或空内容返回 None (无值, 不猜测)."""
    target = Path(path) if path is not None else _host_confirmed_address_path()
    try:
        if not target.is_file():
            return None
        value = target.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def _candidate_lan_addresses():
    """枚举非隧道网卡的全局 IPv4 作候选地址 (D011, 仅候选不自动交付)."""
    try:
        out = subprocess.check_output(
            ["ip", "-o", "-4", "addr", "show", "scope", "global"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
    except Exception:
        return []
    candidates = []
    for line in out.splitlines():
        match = re.match(r"\d+: (\S+)\s+inet (\d+\.\d+\.\d+\.\d+)/", line)
        if not match:
            continue
        iface, addr = match.group(1), match.group(2)
        if iface.startswith(TUNNEL_INTERFACE_PREFIXES):
            continue
        if addr not in candidates:
            candidates.append(addr)
    return candidates


def _resolve_delivery_address(
    listen_port,
    lan_host=None,
    env=None,
    confirmed_path=None,
    in_container=None,
    candidates=None,
):
    """交付地址解析 (D011): 单一入口, 返回解析结果 dict.

    解析成功: {url_host, url_port, lan_ip}. 解析不到: {address_missing, candidates}.
    宿主顺序: --lan-host > 已确认地址文件 > 候选 (需调用会话请用户确认).
    容器分支固定用 SWT_HOST_LAN_IP + SWT_HOST_WEB_PORT, 不被 --lan-host 覆盖.
    明确不读 SSH_CONNECTION/SSH_TTY/主机名.
    """
    env = os.environ if env is None else env
    is_container = _in_container() if in_container is None else in_container

    if is_container:
        host = (env.get("SWT_HOST_LAN_IP") or "").strip()
        raw_port = (env.get("SWT_HOST_WEB_PORT") or "").strip()
        mapped_port = None
        if raw_port.isdigit():
            value = int(raw_port)
            if 1 <= value <= 65535:
                mapped_port = value
        missing = []
        if not host:
            missing.append("SWT_HOST_LAN_IP")
        if mapped_port is None:
            missing.append("SWT_HOST_WEB_PORT")
        if missing:
            return {
                "address_missing": {
                    "code": "container_env_missing",
                    "message": (
                        "container is missing "
                        + " and ".join(missing)
                        + "; ask the host session that created this container "
                        "for the confirmed LAN address and the host port "
                        "mapped to container port 8800, then retry"
                    ),
                }
            }
        return {"url_host": host, "url_port": mapped_port, "lan_ip": host}

    explicit = (lan_host or "").strip()
    if explicit:
        return {"url_host": explicit, "url_port": listen_port, "lan_ip": explicit}

    confirmed = _read_confirmed_lan_address(confirmed_path)
    if confirmed:
        return {
            "url_host": confirmed,
            "url_port": listen_port,
            "lan_ip": confirmed,
        }

    found = _candidate_lan_addresses() if candidates is None else list(candidates)
    return {
        "address_missing": {
            "code": "no_confirmed_address",
            "message": (
                "no confirmed LAN address for this host: pass --lan-host <addr> "
                "with an address the user confirmed, or have the user confirm one "
                "of the candidates, then retry; do not deliver a loopback, "
                "hostname or file path instead"
            ),
        },
        "candidates": found,
    }


def _loopback_bind_warning(bind, port):
    """loopback bind 的提示: 仅供隔离测试, 不是可交付的展示地址."""
    return (
        f"server bound to {bind}:{port} (loopback). This URL is for isolated "
        "tests only; never deliver it as the presentation link. Rebind to "
        "0.0.0.0 with a confirmed LAN address instead"
    )


def _apply_delivery(info, bind, listen_port, lan_host=None):
    """把交付字段写进 info, 返回需要合并进 warning 的提示列表."""
    warnings = []
    if bind in ("127.0.0.1", "::1"):
        info["url"] = f"http://localhost:{listen_port}/"
        info["address_missing"] = {
            "code": "loopback_bind",
            "message": (
                "server bound to a loopback address; the localhost URL is for "
                "isolated tests only and is not a deliverable LAN address"
            ),
        }
        warnings.append(_loopback_bind_warning(bind, listen_port))
        return warnings
    resolved = _resolve_delivery_address(listen_port, lan_host)
    if "address_missing" in resolved:
        info["address_missing"] = resolved["address_missing"]
        if "candidates" in resolved:
            info["candidates"] = resolved["candidates"]
        return warnings
    info["url"] = f"http://{resolved['url_host']}:{resolved['url_port']}/"
    info["lan_ip"] = resolved["lan_ip"]
    return warnings


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


def _http_error_payload(e):
    """读取 HTTPError 响应 body 的 JSON 错误载荷; 非 JSON 时回退到状态串."""
    try:
        data = json.loads(e.read().decode("utf-8"))
        if isinstance(data, dict) and data.get("error"):
            return data
    except Exception:
        pass
    return {"success": False, "error": str(e)}


def _post_add_dir(bind, port, directory_resolved):
    """POST /__control__/add-dir 挂载目录 (无锁辅助函数).

    调用方负责 flock 互斥与存活校验: run_add_dir 与 run_start 复用分支
    均已在锁内探活后调用; 此处只发请求, 避免重入 flock 死锁.
    返回端点载荷 dict; 4xx 读取 body 语义错误 (R3), 连接失败返回失败载荷.
    """
    url = f"http://{_ping_host(bind)}:{port}/__control__/add-dir"
    body = json.dumps({"dir": directory_resolved}).encode("utf-8")
    req = Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(req, timeout=2) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        return _http_error_payload(e)
    except URLError as e:
        return {"success": False, "error": f"cannot reach control endpoint: {e.reason}"}


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

# D005: 重建时原端口被占, 49152-65534 随机换端口的上限尝试次数
_REBUILD_RANDOM_ATTEMPTS = 10


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


def _spawn_serve(port, roots, bind, fixed_port=False):
    """re-exec 自身以隐藏子命令 __serve__ 起子进程.

    roots 为挂载目录列表 (保序), 以 JSON 数组编码进 argv;
    冷启动传单元素列表, 与旧单 root 行为兼容.
    fixed_port 为锁端口标志 (UD-05): 追加进 argv 由子进程持久化.
    """
    script_path = Path(__file__).resolve()
    cmd = [
        sys.executable,
        str(script_path),
        "__serve__",
        str(port),
        json.dumps(list(roots)),
        bind,
    ]
    if fixed_port:
        cmd.append("--fixed-port")
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


def _wait_child_ready(child, bind, port, expected_pid=None, timeout=10):
    """轮询 ping 直到子进程就绪或超时/子进程退出.

    expected_pid (R1): ping 携带 pid 指纹 (D020), 只认本子进程的就绪信号;
    防候选端口被另一 pi-present-web 实例占用时 ping 命中占用者而误判就绪.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if child.poll() is not None:
            break
        alive, _ = _ping_control(bind, port, expected_pid=expected_pid, timeout=2)
        if alive:
            return True
        time.sleep(0.1)
    return False


# ---------------------------------------------------------------------------
# Process helpers (stop)
# ---------------------------------------------------------------------------

def _pid_alive(pid):
    """探测 pid 是否存活 (信号 0 探测, 不发送任何信号)."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _wait_pid_exit(pid, timeout=5.0):
    """轮询等待进程退出; 返回是否确认已退出."""
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
    bind = None  # 本服务 bind 地址, _serve 注入 (U-009 守卫用)
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

    @staticmethod
    def _is_loopback_client(ip):
        """D020/ISSUE-07: 控制面仅 loopback 来源放行.

        接受 IPv4 127.0.0.0/8, IPv6 ::1, 以及 v4-mapped (::ffff:127.x).
        """
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            return False
        if addr.version == 4:
            return addr.is_loopback
        if addr.is_loopback:  # ::1
            return True
        mapped = addr.ipv4_mapped if isinstance(addr, ipaddress.IPv6Address) else None
        return mapped is not None and mapped.is_loopback

    @staticmethod
    def _is_control_path(path):
        """控制命名空间判定: raw path 前缀 (与守卫同轨, U-010)."""
        return path == "/__control__" or path.startswith("/__control__/")

    def _guard_control_namespace(self, path):
        """/__control__/ 命名空间仅本机来源放行 (U-009): loopback 来源,
        或 client IP == 本服务 bind 的地址; 其余 403 拒绝.

        远端无法以本机 bind IP 完成 TCP 握手, 放行源==bind 不扩大暴露面,
        保留 bind 具体 IP (AC-001) 时 CLI 就绪 ping/探活/add-dir 可用.
        bind 0.0.0.0/127.0.0.1 行为不变 (TC-022 不回归): 源不可能为 0.0.0.0,
        loopback 源恒被 loopback 条件放行. 拒绝时置 close_connection (审核 T1):
        未消费的 POST body 不得污染 keep-alive 连接.

        返回 True 表示请求属于控制命名空间且已被拒绝 (响应已写出).
        """
        if not self._is_control_path(path):
            return False
        ip = self.client_address[0]
        if self._is_loopback_client(ip) or ip == self.bind:
            return False
        self.close_connection = True
        self._write_json(
            403, {"success": False, "error": "control plane accepts loopback connections only"}
        )
        return True

    def do_GET(self):
        path = self.path
        # 控制面优先; /__control__/ 全命名空间仅本机来源 (D020/U-009)
        if self._guard_control_namespace(path):
            return
        # U-010: /__control__/* 为保留命名空间: 已定义端点路由不变,
        # 其余控制路径一律 404, 不回落静态查找 (静默遮蔽同路径文件).
        if self._is_control_path(path):
            if path == "/__control__/ping":
                self._write_json(200, {"service": "pi-present-web", "pid": os.getpid()})
                return
            self._send_error(404)
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

    def do_POST(self):
        try:
            # /__control__/ 全命名空间仅本机来源 (D020/U-009)
            if self._guard_control_namespace(self.path):
                return
            # U-010: 保留命名空间内仅 add-dir 已定义, 其余 404 不回落静态
            if self._is_control_path(self.path) and self.path != "/__control__/add-dir":
                self._send_error(404)
                return
            if self.path == "/__control__/add-dir":
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                except Exception:
                    self._write_json(400, {"success": False, "error": "invalid JSON body"})
                    return
                directory = payload.get("dir") if isinstance(payload, dict) else None
                if not isinstance(directory, str) or not directory:
                    self._write_json(400, {"success": False, "error": "missing dir"})
                    return
                resolved = str(Path(directory).resolve())
                if not Path(resolved).exists() or not Path(resolved).is_dir():
                    self._write_json(
                        400, {"success": False, "error": f"dir is not an existing directory: {resolved}"}
                    )
                    return
                with self.roots_lock:
                    if resolved not in self.roots:
                        self.roots.append(resolved)
                    roots = list(self.roots)
                    # R1/U-007: 持锁原子回写 server.json 的 roots,
                    # 保序, 0600, 使 status/重建的 roots 权威来源一致.
                    # 回写失败仅记日志: 内存挂载已生效, 不因此拒绝请求.
                    try:
                        json_path = self.runtime_dir / "server.json"
                        info = json.loads(json_path.read_text(encoding="utf-8"))
                        info["roots"] = roots
                        _atomic_write_json(json_path, info)
                    except Exception as e:
                        _log(self.runtime_dir, f"persist roots failed: {e}")
                self._write_json(200, {"success": True, "roots": roots})
                return
            self._send_error(404)
        except Exception as e:
            _log(self.runtime_dir, f"POST {self.path} error: {e}")
            self._send_error(500)

    def _serve_static(self, roots, rel):
        roots_resolved = [Path(r).resolve() for r in roots]
        if rel == "":
            # D007/U-008 (R1): 顶层路径 -> 各挂载目录顶层条目并集 listing
            # (D008: 去重, 先挂载者优先, 无遮蔽提示);
            # 部分不可读 -> 可读子集 200, 全部不可读 -> 404.
            if self._send_dir_listing(roots_resolved):
                return True
            return False
        for root_path in roots_resolved:
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
            if candidate == root_path:
                # R2: 非规范顶层路径 (/, a/../ 等) resolve 后等于挂载根,
                # 与 / 同义 -> 走顶层并集 listing 分支 (U-008 语义适用)
                if self._send_dir_listing(roots_resolved):
                    return True
                return False
            if candidate.is_dir():
                # D007/U-008 (R1): 子目录路径返回该目录自身 listing (非并集);
                # 单点不可读 -> 404 (恢复单目录原语义)
                if self._send_dir_listing([candidate]):
                    return True
                return False
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

    def _send_dir_listing(self, dir_paths):
        """目录 listing; 多目录时为条目并集 (D007/D008):
        按名去重, 先挂载者优先 (先见者的目录/文件类型定后缀), 按名排序.
        返回是否读到至少一个目录: 部分不可读 -> 可读子集 200 (True);
        全部不可读 -> False (调用方 404, U-008/R1: 不泄露存在性,
        恢复单目录时代原语义, 子目录单点不可读同此).
        """
        names = {}
        readable = 0
        for d in dir_paths:
            try:
                entries = os.listdir(d)
            except OSError:
                continue
            readable += 1
            for e in entries:
                if e not in names:
                    names[e] = (d / e).is_dir()
        if readable == 0:
            return False
        lines = ["<html><body><h1>Directory listing</h1><ul>"]
        for e in sorted(names):
            suffix = "/" if names[e] else ""
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

def _serve(port, roots, bind, fixed_port=False):
    """子进程入口: 绑定端口, 写 server.json, 开 HTTP 服务.

    roots 为挂载目录绝对路径列表, 顺序即遮蔽优先级; 逐个 resolve 后
    完整保序写入 server.json, 作为 status 重建的权威清单.
    fixed_port 为锁端口标志 (UD-05), 持久化进 server.json 供重建读取.
    """
    port = int(port)
    roots_resolved = [str(Path(r).resolve()) for r in roots]
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

    _Handler.roots = roots_resolved
    _Handler.runtime_dir = runtime_dir
    _Handler.bind = bind  # U-009: 守卫按源==bind 放行本机控制流

    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    data = {
        "pid": os.getpid(),
        "port": port,
        "bind": bind,
        "roots": roots_resolved,
        "started_at": started_at,
        "fixed_port": bool(fixed_port),
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

def run_start(port, root, bind, fixed_port=False, lan_host=None):
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
        # D002: 复用判定前先校验 server.json 属主; 非本人 -> instance_conflict,
        # 不复用不挂载 (异 uid 场景自动化不覆盖, 见 TC-029 人工验证).
        json_path = runtime_dir / "server.json"
        if json_path.exists():
            try:
                owner_uid = os.stat(json_path).st_uid
            except OSError as e:
                return _err("start", "internal_error", f"cannot stat server.json: {e}")
            if owner_uid != os.getuid():
                return _err(
                    "start",
                    "instance_conflict",
                    f"existing server.json owned by uid {owner_uid}, "
                    f"not current user (uid {os.getuid()}); not reusing",
                )
        alive, existing = _probe_existing(runtime_dir)
        if alive:
            if existing.get("bind") != bind:
                return _err(
                    "start",
                    "bind_conflict",
                    "existing instance bind differs; stop it first",
                )
            # D006: bind 一致 -> 真复用: 经控制端点幂等挂载 root,
            # 忽略端口差异仅告警, 返回现有实例信息.
            # flock 陷阱: 此处已持运行时锁, 直接调 run_add_dir 会重入 flock
            # 死锁, 故经无锁的 _post_add_dir 直发控制端点.
            payload = _post_add_dir(existing["bind"], existing["port"], root_resolved)
            if not payload.get("success"):
                return _err(
                    "start",
                    "internal_error",
                    f"reuse add-dir failed (service still alive): "
                    f"{payload.get('error', 'endpoint rejected')}",
                )
            ex_port = int(existing["port"])
            ex_bind = existing["bind"]
            info = {
                "hostname": socket.gethostname(),
                "port": ex_port,
                "bind": ex_bind,
                "roots": payload.get("roots", []),
                "reused": True,
            }
            warnings = _apply_delivery(info, ex_bind, ex_port, lan_host)
            if fixed_port and not existing.get("fixed_port", False):
                # UD-13: 锁定仅冷启动持久化; 复用不升级锁, 不一致须有声.
                warnings.append(
                    "--fixed-port ignored on reuse: lock only takes effect on "
                    "cold start; existing instance is not locked"
                )
            if port_int != ex_port:
                warnings.append(
                    f"requested port {port_int} differs from existing instance "
                    f"port {ex_port}; ignoring requested port, serving on {ex_port}"
                )
            if warnings:
                info["warning"] = "; ".join(warnings)
            return _success("start", info)

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

        child = _spawn_serve(port_int, [root_resolved], bind, fixed_port)
        # R1: 就绪 ping 带 pid 指纹, 防端口竞态窗口内 ping 命中占用者误判就绪
        # (防御性加固, 正常路径行为不变).
        if not _wait_child_ready(child, bind, port_int, expected_pid=child.pid):
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

        info = {
            "hostname": socket.gethostname(),
            "port": port_int,
            "bind": bind,
            "roots": [root_resolved],
            "reused": False,
        }
        warnings = _apply_delivery(info, bind, port_int, lan_host)
        if warnings:
            info["warning"] = "; ".join(warnings)
        return _success("start", info)
    finally:
        if lock_fd is not None:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()


def _status_alive_payload(data, rebuilt, lan_host=None):
    """由 server.json 数据构造 status 成功载荷 (含运行时信息).

    url/lan_ip 由同一次地址解析按记录的实际监听端口实时算出 (D011),
    不额外持久化地址; 存活与重建两条路径共用本构造函数, 不留下一条给地址.
    """
    result = {"alive": True, "rebuilt": rebuilt}
    for key in ("pid", "port", "bind", "roots", "started_at"):
        result[key] = data.get(key)
    try:
        listen_port = int(data.get("port"))
    except Exception:
        return _success("status", result)
    warnings = _apply_delivery(result, data.get("bind"), listen_port, lan_host)
    if warnings:
        result["warning"] = "; ".join(warnings)
    return _success("status", result)


def _rebuild_spawn(runtime_dir, bind, old_port, roots, fixed_port=False, lan_host=None):
    """按 roots 保序重 spawn 服务子进程.

    先试原端口; 被占 (预检或子进程绑定失败) 则 49152-65534 随机换端口
    重试 ≤10 次 (D005). 成功时子进程已写新 server.json, 读回并返回
    rebuilt 载荷; 全部失败返回 port_in_use / internal_error.
    fixed_port (UD-05): 锁定实例只试原端口, 被占即报错, 不换端口.
    """
    json_path = runtime_dir / "server.json"
    candidates = [old_port]
    if not fixed_port:
        candidates += [
            random.randint(49152, 65534) for _ in range(_REBUILD_RANDOM_ATTEMPTS)
        ]
    startup_err_path = _startup_error_path(runtime_dir)
    last_code, last_error = "internal_error", "no candidate port could bind"
    for port in candidates:
        if startup_err_path.exists():
            try:
                startup_err_path.unlink()
            except Exception:
                pass
        child = _spawn_serve(port, roots, bind, fixed_port)
        if _wait_child_ready(child, bind, port, expected_pid=child.pid):
            try:
                new_data = json.loads(json_path.read_text(encoding="utf-8"))
            except Exception as e:
                _terminate_child(child)
                return _err(
                    "status", "internal_error",
                    f"rebuilt but server.json unreadable: {e}",
                )
            # R1: 就绪后读回 server.json 校验指纹: pid 须为本子进程且 port
            # 须为候选端口; 不匹配 (如 ping 曾命中占用者) 按该候选失败处理,
            # 继续换端口, 不把残留旧 server.json 当重建成功.
            if new_data.get("pid") != child.pid or new_data.get("port") != port:
                _terminate_child(child)
                last_code, last_error = "internal_error", (
                    f"rebuilt server.json fingerprint mismatch on port {port}: "
                    f"pid={new_data.get('pid')!r} port={new_data.get('port')!r}, "
                    f"expected pid={child.pid}"
                )
                continue
            return _status_alive_payload(new_data, rebuilt=True, lan_host=lan_host)
        # 失败: 先读真实错误, 再强制回收子进程
        err = _read_startup_error(runtime_dir)
        _terminate_child(child)
        if err is not None:
            last_code = err.get("code", "internal_error")
            last_error = err.get("error", "server failed to start")
            if last_code != "port_in_use":
                # 非端口问题, 换端口无意义, 直接报错
                return _err("status", last_code, f"rebuild failed: {last_error}")
        else:
            return _err(
                "status", "internal_error",
                "rebuild failed: server did not become ready within timeout",
            )
    if fixed_port:
        return _err(
            "status", "port_in_use",
            f"rebuild failed: fixed port {old_port} is in use "
            f"(--fixed-port); refusing to switch ports (last: {last_error})",
        )
    return _err(
        "status", "port_in_use",
        f"rebuild failed: all candidate ports in use (last: {last_error})",
    )


def _rebuild_status(runtime_dir, json_path, lan_host=None):
    """D005 重建入口: 锁内重探活后按原 roots 保序重建.

    锁策略 (D023): 仅重建路径持锁 — 探活只读无共享可变状态, 存活路径
    无锁免争用; 锁内重读 server.json 并重探活, 防并发 start/stop/status
    竞争 (可能已被他人重建/清理/复用).
    """
    lock_fd = None
    try:
        lock_fd = _lock_runtime(runtime_dir)
        if not json_path.exists():
            # 锁内判定: 并发 stop/重建窗口已清走 -> 未启动
            return _success("status", {"alive": False, "rebuilt": False})
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:
            return _err("status", "internal_error", f"cannot read server.json: {e}")
        alive, _ = _ping_control(data["bind"], data["port"], data.get("pid"), timeout=2)
        if alive:
            # 并发 start/重建已恢复实例, 无需重建
            return _status_alive_payload(data, rebuilt=False, lan_host=lan_host)

        roots = data.get("roots")
        bind = data.get("bind")
        if (
            not isinstance(roots, list)
            or not roots
            or not all(isinstance(r, str) for r in roots)
            or not isinstance(bind, str)
            or not bind
        ):
            return _err(
                "status", "internal_error",
                "server.json lacks valid roots/bind; cannot rebuild",
            )
        try:
            old_port = int(data["port"])
        except Exception:
            return _err(
                "status", "internal_error",
                "server.json has invalid port; cannot rebuild",
            )
        return _rebuild_spawn(
            runtime_dir, bind, old_port, [str(r) for r in roots],
            fixed_port=bool(data.get("fixed_port", False)),
            lan_host=lan_host,
        )
    finally:
        if lock_fd is not None:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()


def run_status(lan_host=None):
    """Check server alive status; 死则重建 (D005).

    无 server.json -> alive=false 不重建; ping 指纹匹配 -> alive=true;
    server.json 在但探活失败 (进程死/指纹不匹配) -> 重建 (锁内).
    """
    runtime_dir = _runtime_dir()
    json_path = runtime_dir / "server.json"
    if not json_path.exists():
        return _success("status", {"alive": False, "rebuilt": False})
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        return _err("status", "internal_error", f"cannot read server.json: {e}")

    alive, _ = _ping_control(data["bind"], data["port"], data.get("pid"), timeout=2)
    if alive:
        return _status_alive_payload(data, rebuilt=False, lan_host=lan_host)
    return _rebuild_status(runtime_dir, json_path, lan_host=lan_host)


def run_stop():
    """Stop server and remove runtime files.

    D006/D020: 不经 HTTP; ping 指纹比对 + `ps` 命令行校验, 不匹配报错不杀;
    服务半死 (ping 失联) 时经 ps 校验仍可终止. 无 server.json 幂等成功.
    """
    runtime_dir = _runtime_dir()
    if not runtime_dir.exists():
        # 运行时目录不存在 -> 必然未启动, 幂等成功 (不为 no-op stop 创建目录).
        return _success("stop", {})

    lock_fd = _lock_runtime(runtime_dir)
    try:
        json_path = runtime_dir / "server.json"
        if not json_path.exists():
            # 锁内判定 (R2): 并发 stop 已清理或从未启动 -> 幂等成功;
            # 消除锁外见到文件, 锁内被并发 stop 删走而误报 cannot read 的窗口.
            return _success("stop", {})
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            pid = int(data["pid"])
        except Exception as e:
            return _err("stop", "internal_error", f"cannot read server.json: {e}")

        alive, payload = _ping_control(data["bind"], data["port"], pid, timeout=2)
        if not alive and payload is not None:
            # 端口上有应答但 pid 指纹不匹配: 疑似无关服务占用, 报错不杀.
            return _err(
                "stop",
                "internal_error",
                f"control endpoint on port {data['port']} answered with foreign "
                f"fingerprint; refuse to stop pid {pid}",
            )

        if not _pid_alive(pid):
            # 进程已死: 仅清理残留运行时文件.
            _remove_json(json_path)
            return _success("stop", {})

        if not _ps_args_contains(pid, str(Path(__file__).resolve())):
            # pid 已被其他进程复用: 报错不杀.
            return _err(
                "stop",
                "internal_error",
                f"pid {pid} command line does not contain this script; refuse to stop",
            )

        os.kill(pid, signal.SIGTERM)
        if not _wait_pid_exit(pid, timeout=5.0):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            _wait_pid_exit(pid, timeout=2.0)

        _remove_json(json_path)
        return _success("stop", {})
    finally:
        if lock_fd is not None:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()


def _remove_json(json_path):
    try:
        json_path.unlink()
    except FileNotFoundError:
        pass


def run_add_dir(directory):
    """Mount a directory via control endpoint (D006/D020).

    校验目录 (D012) -> 读 server.json 探活 -> POST /__control__/add-dir -> 返回 roots.
    """
    err = _validate_root(directory, command="add-dir")
    if err is not None:
        return err
    runtime_dir = _runtime_dir()
    if not runtime_dir.exists():
        return _err("add-dir", "internal_error", "server not running")

    lock_fd = _lock_runtime(runtime_dir)
    try:
        json_path = runtime_dir / "server.json"
        if not json_path.exists():
            # 锁内判定 (R2): server.json 在锁外见到但锁内已不存在
            # (并发 stop 已清理) -> 报 server not running, 不误报 cannot read.
            return _err("add-dir", "internal_error", "server not running")
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:
            return _err("add-dir", "internal_error", f"cannot read server.json: {e}")

        alive, _ = _ping_control(data["bind"], data["port"], data.get("pid"), timeout=2)
        if not alive:
            return _err("add-dir", "internal_error", "server not running")

        payload = _post_add_dir(
            data["bind"], data["port"], str(Path(directory).resolve())
        )
        if payload.get("success"):
            return _success("add-dir", {"roots": payload.get("roots", [])})
        return _err("add-dir", "internal_error", payload.get("error", "add-dir rejected"))
    finally:
        if lock_fd is not None:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()


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
        if len(argv) not in (4, 5) or (len(argv) == 5 and argv[4] != "--fixed-port"):
            sys.stderr.write(
                "Usage: web_server.py __serve__ <port> <roots_json> <bind> [--fixed-port]\n"
            )
            sys.exit(1)
        try:
            roots = json.loads(argv[2])
            if not isinstance(roots, list) or not all(
                isinstance(r, str) for r in roots
            ):
                raise ValueError("roots must be a JSON array of strings")
        except Exception:
            sys.stderr.write(
                "Usage: web_server.py __serve__ <port> <roots_json> <bind> [--fixed-port]\n"
            )
            sys.exit(1)
        try:
            _serve(argv[1], roots, argv[3], fixed_port=len(argv) == 5)
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
                    "Usage: web_server.py start <port> <root> --bind <addr> "
                    "[--fixed-port] [--lan-host <addr>]",
                )
            else:
                port, root, bind, fixed_port, lan_host = parsed
                obj = run_start(port, root, bind, fixed_port, lan_host)
        elif command == "status":
            lan_host, ok = _parse_lan_host(argv[1:])
            if not ok:
                obj = _err(
                    "status",
                    "invalid_args",
                    "Usage: web_server.py status [--lan-host <addr>]",
                )
            else:
                obj = run_status(lan_host)
        elif command == "stop":
            obj = run_stop()
        elif command == "add-dir":
            if len(argv) != 2:
                obj = _err(
                    "add-dir",
                    "invalid_args",
                    "Usage: web_server.py add-dir <dir>",
                )
            else:
                obj = run_add_dir(argv[1])
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
