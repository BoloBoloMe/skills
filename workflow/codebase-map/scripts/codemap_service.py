#!/usr/bin/env python3
"""codebase-map 常驻服务与运行时状态 (m25 TECHNICAL.md "常驻服务与状态").

责任: 运行时目录与文件锁, state.json 读写与真实探活, 端口决策,
HTTP 静态服务 (前台守护循环 + 守护子进程启动), 显式停止.
藏住: 锁协议, 探活三步判定, 子进程回收.

对外函数只有 run_serve / run_stop / run_update_data_keys: 返回结果 dict,
不碰 stdout 与 sys.exit, 由 codebase-map.py 的 CLI 适配层统一输出与定
退出码. `_serve-daemon` 是内部隐藏入口 (守护子进程 re-exec 本脚本), 不写
进 SKILL.md 用法, 不对外文档化.

网络面 (BR-027): serve/stop 不做任何出网动作, 不调 podman; 唯二的网络
行为是 TECHNICAL 探活三步自身要求的 127.0.0.1 连通探测与本机 0.0.0.0
静态文件服务, 全部只触本机.

时间常量 (TECHNICAL 写明是实现选择, m25 EXECUTION 验证策略约定不写用例,
只按实现常量核对一次记入交付证据): 锁等待 30 秒, 端口就绪 10 秒,
stop 等待 10 秒.

状态与换端口 (m25 D018): stop 只把 pid 置空并写 stopped_at, 保留
port/last_port/last_url, 于是"已知停机"与"旧实例死掉的残留"可区分, 换
端口时报得出真实旧地址. last_url 由 serve 在每次成功启动时写为
http://127.0.0.1:<port>/: 它只承担端口留痕, 不落任何已解析地址
(全局禁止: 不把 --address 或任何地址写进 state.json); 交付 URL 由
ISSUE-05 的交付输出层 (_apply_delivery) 在响应里现场组装, 不落盘.
--address 的值按 D017 永不写入 state.json.

交付输出层 (ISSUE-05, m25 D002/D006/D017/D020): run_serve 在启动/复用
成功的结果上追加 url/base_url/keys/delivery_notes/address_missing 等
交付字段; 启动, 复用, 探活, 端口决策, 锁与 stop 语义一概不动 (ISSUE-04
面不变), 本层只加输出字段, 地址解析纯函数在 codemap_common.
"""
from __future__ import annotations

import datetime
import errno
import fcntl
import functools
import http.client
import json
import mimetypes
import os
import signal
import socket
import subprocess
import sys
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codemap_common as cmc  # noqa: E402  (脚本同目录, 保证任意 cwd 可跑)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

STATE_VERSION = 1
STATE_FILENAME = "state.json"
LOCK_FILENAME = "lock"
LOG_REL = "logs/service.log"
STARTUP_ERROR_FILENAME = "startup_error.json"
DATA_SUFFIX = ".cc.json"

# 时间常量: 实现选择, 与 TECHNICAL 一致 (30/10/10), 可调整 (核对见交付证据)
LOCK_WAIT_SECONDS = 30
READY_TIMEOUT_SECONDS = 10
STOP_WAIT_SECONDS = 10
PROBE_TIMEOUT_SECONDS = 2

DAEMON_SUBCOMMAND = "_serve-daemon"  # 内部隐藏入口, 不对外文档化
ENV_PORT = "CODEMAP_PORT"  # 首选端口覆盖, 只供隔离测试, 不构成换端口入口 (BR-004)

SERVICE_SCRIPT = Path(__file__).resolve()


# ---------------------------------------------------------------------------
# 小工具: 时间, 端口, 进程, 探活
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _loopback_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/"


def _preferred_port() -> int:
    """首选端口: $CODEMAP_PORT 覆盖 (测试隔离), 否则 8090."""
    raw = os.environ.get(ENV_PORT)
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return cmc.DEFAULT_PORT


def _pid_alive(pid) -> bool:
    """探活第一步: os.kill(pid, 0) 不抛错."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # 进程存在但非本用户: 仍算"存活", 后续归属判定会拦下


def _is_our_daemon(pid) -> bool:
    """pid 是否本脚本的 _serve-daemon 守护进程 (读 /proc cmdline, 只在 Linux 可用)."""
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return False
    args = [part.decode("utf-8", "replace") for part in raw.split(b"\0") if part]
    return DAEMON_SUBCOMMAND in args and str(SERVICE_SCRIPT) in args


def _http_status(port, timeout=PROBE_TIMEOUT_SECONDS):
    """GET http://127.0.0.1:<port>/ 的响应码; 连不上/超时/端口非法返回 None."""
    if not isinstance(port, int) or not (1 <= port <= 65535):
        return None
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    except OSError:
        return None
    try:
        conn.request("GET", "/")
        resp = conn.getresponse()
        resp.read()
        return resp.status
    except (OSError, http.client.HTTPException):
        return None
    finally:
        conn.close()


def _port_free(port: int) -> bool:
    """探测 0.0.0.0:<port> 能否 bind (SO_REUSEADDR 只豁免 TIME_WAIT, 不豁免监听者)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((cmc.BIND, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


# ---------------------------------------------------------------------------
# 文件锁 (flock, 覆盖 serve 启动/复用, build 的副本复制与 data_keys 更新, stop 全过程)
# ---------------------------------------------------------------------------


def _acquire_lock(base: Path):
    """runtime_dir/lock 的 flock(LOCK_EX), 最多等 LOCK_WAIT_SECONDS 秒; 超时返回 None."""
    lock_path = base / LOCK_FILENAME
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    deadline = time.monotonic() + LOCK_WAIT_SECONDS
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except OSError:
            if time.monotonic() >= deadline:
                os.close(fd)
                return None
            time.sleep(0.05)


def _release_lock(fd, base: Path | None = None, unlink: bool = False) -> None:
    """释放 flock; unlink=True 时先清锁文件再放锁 (stop 成功路径, TECHNICAL "清锁文件")."""
    if unlink and base is not None:
        try:
            (base / LOCK_FILENAME).unlink()
        except FileNotFoundError:
            pass
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


# ---------------------------------------------------------------------------
# state.json 读写 (原子写: 临时文件 + rename, 0600)
# ---------------------------------------------------------------------------


def _load_state(base: Path):
    """读 state.json; 返回 (state|None, 错误说明|None). 文件不存在返回 (None, None)."""
    path = base / STATE_FILENAME
    if not path.exists():
        return None, None
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, ValueError) as exc:
        return None, f"state.json 无法读取或已损坏: {exc}"


def _atomic_write_state(base: Path, state: dict) -> None:
    path = base / STATE_FILENAME
    tmp = path.with_name(STATE_FILENAME + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _fresh_state(base: Path) -> dict:
    """build 首次登记时的骨架状态 (pid/port 尚空); serve 只读它, 写入走启动/停止路径."""
    return {
        "version": STATE_VERSION,
        "port": None,
        "last_port": None,
        "last_url": None,
        "pid": None,
        "bind": cmc.BIND,
        "started_at": None,
        "stopped_at": None,
        "command_path": str(SERVICE_SCRIPT),
        "serve_root": str(base / "serve-root"),
        "log_path": str(base / LOG_REL),
        "runtime_dir": str(base),
        "data_keys": [],
    }


# ---------------------------------------------------------------------------
# 数据键交集判定 (m25 D020, BR-030)
# ---------------------------------------------------------------------------


def _disk_keys(serve_root: Path) -> set:
    if not serve_root.is_dir():
        return set()
    return {
        entry.name
        for entry in serve_root.iterdir()
        if entry.is_file() and entry.name.endswith(DATA_SUFFIX)
    }


def _no_data_keys_error(base: Path, state) -> dict | None:
    """state.data_keys 与 serve-root 实际 .cc.json 的交集为空时返回错误, 否则 None.

    两类文案 (m25 D020): 清单与磁盘都空 = 还没 build 过; 清单有条目但副本
    全缺 = 副本已删, 建议重新 build. 磁盘上有未登记文件只提示, 不自动收编.
    """
    serve_root = base / "serve-root"
    registered = {
        entry.get("key")
        for entry in (state or {}).get("data_keys") or []
        if isinstance(entry, dict) and entry.get("key")
    }
    disk = _disk_keys(serve_root)
    if registered & disk:
        return None
    unregistered = sorted(disk - registered)
    extra = (
        f" 另有 {len(unregistered)} 个未登记的磁盘副本 ({', '.join(unregistered[:3])}"
        f"{'...' if len(unregistered) > 3 else ''}), 不自动收编."
        if unregistered
        else ""
    )
    if not registered:
        return cmc.error_result(
            "serve",
            "no_data_keys",
            f"还没有 build 过: 状态清单与 {serve_root} 里都没有数据副本, 不起空服务.{extra}",
            "先执行 build <目标目录> 生成数据副本, 再执行 serve.",
        )
    return cmc.error_result(
        "serve",
        "no_data_keys",
        f"副本已删, 建议重新 build: 状态清单登记了 {len(registered)} 个键, 但 {serve_root} 里一个副本都不在, 不起空服务.{extra}",
        "副本被删不会自动恢复, 重新执行 build 重建副本后再执行 serve.",
    )


# ---------------------------------------------------------------------------
# 守护子进程
# ---------------------------------------------------------------------------


def _log_line(base: Path, line: str) -> None:
    """追加一行到 logs/service.log (0600); 日志只含事件与相对文件名, 不含源码内容."""
    try:
        path = base / LOG_REL
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as handle:
            handle.write(f"{_utc_now_iso()} {line}\n")
    except OSError:
        pass


def _startup_error_path(base: Path) -> Path:
    return base / STARTUP_ERROR_FILENAME


def _write_startup_error(base: Path, code: str, message: str, hint: str) -> None:
    payload = {"code": code, "message": message, "hint": hint}
    path = _startup_error_path(base)
    tmp = path.with_name(STARTUP_ERROR_FILENAME + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _consume_startup_error(base: Path):
    path = _startup_error_path(base)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        path.unlink()
        return data
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return None


def _terminate_child(proc: subprocess.Popen) -> None:
    """失败启动路径的清扫: SIGTERM -> 等 2 秒 -> 仍活才 SIGKILL (navigate 先例做法).

    "不自动 SIGKILL" 是 stop 对运行中服务的纪律; 这里是我们刚拉起、从未
    就绪过的自家子进程, 放任残留会一直占住端口.
    """
    if proc.poll() is not None:
        return
    try:
        proc.terminate()
    except OSError:
        pass
    try:
        proc.wait(timeout=2)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        proc.kill()
        proc.wait(timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        pass


def _spawn_daemon(base: Path, port: int) -> subprocess.Popen:
    """起守护子进程: python3 <本脚本> _serve-daemon <port> <runtime_dir>.

    start_new_session=True 脱离父进程生命周期 (父退出服务仍在); stdout/
    stderr 追加到 logs/service.log.
    """
    log_path = base / LOG_REL
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    log_file = os.fdopen(fd, "wb", 0)
    try:
        return subprocess.Popen(
            [sys.executable, str(SERVICE_SCRIPT), DAEMON_SUBCOMMAND, str(port), str(base)],
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
            env=os.environ.copy(),
        )
    finally:
        log_file.close()  # 子进程已持有复制的 fd, 父进程关掉自己的副本


# ---------------------------------------------------------------------------
# 启动路径
# ---------------------------------------------------------------------------


def _start_service(base: Path, target_port: int, old_state, note: str) -> dict:
    """共同启动路径 (首次 / 已知停机 / 旧实例已死): 交集检查 -> 端口检查 -> 起守护 -> 写状态."""
    blocked = _no_data_keys_error(base, old_state)
    if blocked is not None:
        return blocked
    if not _port_free(target_port):
        return cmc.error_result(
            "serve",
            "port_in_use",
            f"目标端口 {target_port} 已被其它程序占用, 不换端口不接管.",
            "确认占用者身份后二选一: 换端口用 serve --port <N>; 或先处理占用该端口的程序再重试.",
        )
    old = old_state or {}
    old_last_port = old.get("last_port")
    stale_error = _startup_error_path(base)
    try:
        stale_error.unlink()
    except FileNotFoundError:
        pass
    proc = _spawn_daemon(base, target_port)
    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    ready = False
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            failure = _consume_startup_error(base)
            if failure:
                return cmc.error_result(
                    "serve", failure.get("code", "internal_error"),
                    failure.get("message", "守护子进程启动失败."), failure.get("hint", "查看日志后重试."),
                )
            return cmc.error_result(
                "serve", "internal_error",
                f"守护子进程启动后立即退出 (exit={proc.returncode}), 没有留下启动错误记录.",
                f"查看日志 {base / LOG_REL} 后重试.",
            )
        if _http_status(target_port) is not None:  # 就绪 = 有 HTTP 应答 (状态码不论)
            ready = True
            break
        time.sleep(0.1)
    if not ready:
        _terminate_child(proc)
        return cmc.error_result(
            "serve", "internal_error",
            f"守护子进程未在 {READY_TIMEOUT_SECONDS} 秒内监听端口 {target_port}, 已清扫.",
            f"查看日志 {base / LOG_REL} 后重试.",
        )
    state = dict(_fresh_state(base))
    state.update({
        "port": target_port,
        "last_port": target_port,
        "last_url": _loopback_url(target_port),
        "pid": proc.pid,
        "started_at": _utc_now_iso(),
        "stopped_at": None,
        "data_keys": old.get("data_keys") or [],
    })
    _atomic_write_state(base, state)
    _log_line(base, f"serve: started pid={proc.pid} port={target_port} by ppid={os.getppid()}")
    result = cmc.success_result(
        "serve",
        port=target_port,
        bind=cmc.BIND,
        reused=False,
        pid=proc.pid,
        serve_root=str(base / "serve-root"),
        note=note,
    )
    if old_last_port is not None and target_port != old_last_port:
        # 换端口 (m25 D018): 报旧地址已失效, 旧地址取留痕的 last_url, 不假定 8090
        result["port_changed"] = True
        result["previous_url"] = old.get("last_url") or _loopback_url(old_last_port)
    return result


# ---------------------------------------------------------------------------
# serve 判定分支 (TECHNICAL 判定顺序)
# ---------------------------------------------------------------------------


def _serve_core(explicit_port=None, runtime_base=None) -> dict:
    """serve 启动/复用核心 (ISSUE-04 面, 原样保留): 判定分支与端口决策.

    不碰 stdout, 不退出进程; 交付字段由 run_serve 的输出层追加.
    """
    if explicit_port is not None and not (1 <= explicit_port <= 65535):
        return cmc.error_result(
            "serve", "internal_error",
            f"--port 取值非法: {explicit_port} (应为 1-65535).",
            "换一个 1-65535 之间的端口重试.",
        )
    base = Path(runtime_base).resolve() if runtime_base is not None else cmc.runtime_dir()
    cmc.ensure_runtime_layout(base)
    lock_fd = _acquire_lock(base)
    if lock_fd is None:
        return cmc.error_result(
            "serve", "internal_error",
            f"运行时目录锁等待超过 {LOCK_WAIT_SECONDS} 秒: {base / LOCK_FILENAME}",
            "确认没有其它 codebase-map 调用长时间持锁后重试.",
        )
    try:
        state, err = _load_state(base)
        if err is not None:
            return cmc.error_result(
                "serve", "internal_error", err,
                "state.json 损坏无法判读; 按 SKILL.md 复原步骤处理 (删运行时目录等于放弃当前实例).",
            )
        # 端口决策: --port 实参, 否则 state.last_port, 否则首选端口 (m25 D018)
        if explicit_port is not None:
            target = explicit_port
        elif state is not None and state.get("last_port"):
            target = int(state["last_port"])
        else:
            target = _preferred_port()
        if state is None:
            return _start_service(base, target, None, "运行时目录还没有状态记录, 新起服务实例.")
        pid = state.get("pid")
        if pid is None:
            # 已知停机 (pid 置空 + stopped_at) 或从未起过: 直接按目标端口起
            return _start_service(base, target, state, "状态记录显示服务未在运行, 按目标端口启动.")
        if not _pid_alive(pid):
            # 旧实例已死: 目标端口空闲就重起并报告; 被别的程序占用则 port_in_use, 不静默顺延
            if _port_free(target):
                return _start_service(
                    base, target, state,
                    "旧实例已死 (记录的 pid 不存在), 残留记录不算存活, 已按目标端口重新启动.",
                )
            return cmc.error_result(
                "serve", "port_in_use",
                f"旧实例已死 (pid {pid} 不存在), 但目标端口 {target} 已被其它程序占用, 不换端口不接管.",
                "确认占用者身份后二选一: 换端口用 serve --port <N>; 或先处理占用该端口的程序再重试.",
            )
        if not _is_our_daemon(pid):
            return cmc.error_result(
                "serve", "state_mismatch",
                f"状态记录的 pid {pid} 存活, 但它不是本服务的守护进程, 端口上的监听者无法确认属于本服务; 不接管不重起.",
                "先核实该 pid 的归属; 确认后按 SKILL.md 复原步骤处理.",
            )
        recorded_port = state.get("port")
        if not isinstance(recorded_port, int):
            return cmc.error_result(
                "serve", "internal_error",
                f"状态记录缺有效的 port 字段: {recorded_port!r}.",
                "state.json 不完整; 按 SKILL.md 复原步骤处理.",
            )
        status = _http_status(recorded_port)
        if status != HTTPStatus.OK:
            return cmc.error_result(
                "serve", "state_mismatch",
                f"状态记录的 pid {pid} 存活, 但记录的端口 {recorded_port} 无人应答"
                f" (GET / 状态: {'无应答' if status is None else status}); 状态与探活结果不一致, 不接管不重起.",
                "先核实该端口与进程; 确认后按 SKILL.md 复原步骤处理.",
            )
        if explicit_port is not None and explicit_port != recorded_port:
            return cmc.error_result(
                "serve", "instance_running",
                f"已有存活实例运行在端口 {recorded_port} (pid {pid}); 换端口前必须先 stop 现有实例.",
                "先执行 stop, 再用 serve --port <N> 换端口; 或不带 --port 直接复用现有实例.",
            )
        return cmc.success_result(
            "serve",
            port=recorded_port,
            bind=cmc.BIND,
            reused=True,
            pid=pid,
            serve_root=str(state.get("serve_root") or (base / "serve-root")),
            note="已有存活实例 (探活三步全过), 直接复用, 不起新进程.",
        )
    finally:
        _release_lock(lock_fd)


# ---------------------------------------------------------------------------
# 交付输出层 (ISSUE-05): 地址解析 + keys 交集 + delivery_notes, 只加输出字段
# ---------------------------------------------------------------------------


def _delivery_keys(state, serve_root: Path, with_details: bool) -> tuple:
    """keys = state.data_keys 与 serve-root 实际 .cc.json 的交集 (m25 D020, BR-030).

    输出前逐个核文件存在; 记录有而磁盘缺的键不进 keys (作缺失清单返回);
    磁盘有而清单没有的 (手工放入) 不收编, 只作未登记清单返回 (BR-036 不删).
    with_details=False 时按 AC-008 地址缺口形态只给键名, 不给 built_at/bytes.
    """
    registered = [
        entry for entry in (state or {}).get("data_keys") or []
        if isinstance(entry, dict) and entry.get("key")
    ]
    disk = _disk_keys(serve_root)
    keys, missing = [], []
    for entry in registered:
        key = entry["key"]
        if key not in disk or not (serve_root / key).is_file():
            missing.append(key)
            continue
        if with_details:
            keys.append({
                "key": key,
                "built_at": entry.get("built_at"),
                "bytes": entry.get("bytes"),
            })
        else:
            keys.append({"key": key})
    unregistered = sorted(disk - {entry["key"] for entry in registered})
    return keys, missing, unregistered


def _delivery_notes(serve_root: Path, keys) -> dict:
    """三类交付说明 (m25 D006, BR-023/BR-024); 数字取自 serve-root 实际副本.

    依赖树文件数用 codemap_analyze 的只读统计函数 (与 build stats 同口径,
    不写第二份); 懒加载且只调纯函数, 不触 podman 与网络 (BR-027).
    """
    import codemap_analyze as cma  # noqa: PLC0415  (延迟导入, 只用只读统计纯函数)
    counts = []
    for item in keys:
        path = serve_root / item["key"]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            counts.append(f"{item['key']}: 数据文件无法解析, 文件数缺报")
            continue
        counts.append(f"{item['key']}: {cma.files_in_tree_of(data)}")
    return {
        "level_hint": "层号/环/向上依赖在官方依赖视图里看; 3D 城市图按官方默认指标.",
        "integrity_note": "依赖抽取完整性未量化, 不能当作分层完全可信.",
        "denominator_note": (
            "分母口径: 依赖树里的文件数 " + ("; ".join(counts) if counts else "无")
            + "; 零声明文件不进依赖树, 测试与 build 目录默认不扫, "
            "分析端自带忽略规则单列为工具默认过滤."
        ),
    }


def _apply_delivery(result: dict, explicit_address, runtime_base=None) -> dict:
    """在 serve 成功结果上追加交付输出 (m25 D002/D006/D017/D020, AC-008).

    地址解析成功 (含 --address 传入的确认值): 给 url/base_url 与
    keys[].url, address_source 标明来源. 解析失败且未传 --address: 不给
    url/base_url, keys 只给键名, 给 address_missing + candidates; 服务照常
    监听, 退出码仍为 0. 锁已释放后的状态重读按 TECHNICAL 关键流程
    ("释放锁 -> 解析地址并输出") 执行; 地址与 URL 一律不落盘.
    """
    base = Path(runtime_base).resolve() if runtime_base is not None else cmc.runtime_dir()
    state, state_err = _load_state(base)
    serve_root = Path(result.get("serve_root") or (base / "serve-root"))
    resolved = cmc.resolve_delivery_address(explicit_address)
    has_address = "url_host" in resolved
    keys, missing, unregistered = _delivery_keys(state, serve_root, with_details=has_address)
    notes = []
    if state_err is not None:
        notes.append(f"交付组装时状态记录无法读取, keys 可能不完整: {state_err}")
    if missing:
        notes.append(
            f"状态清单登记但磁盘缺失的键 {len(missing)} 个 (不进 keys, 不交付失效 URL): "
            + ", ".join(missing)
        )
    if unregistered:
        notes.append(
            f"存在未登记的磁盘副本 {len(unregistered)} 个 (不自动收编): "
            + ", ".join(unregistered)
        )
    result["keys"] = keys
    result["delivery_notes"] = _delivery_notes(serve_root, keys)
    if notes:
        result["notes"] = notes
    if has_address:
        host = resolved["url_host"]
        port = result.get("port")
        base_url = f"http://{host}:{port}/"
        result["url"] = base_url
        result["base_url"] = base_url
        result["address_source"] = resolved["address_source"]
        for item in keys:
            item["url"] = f"http://{host}:{port}/?file={item['key']}"
    else:
        result["address_missing"] = resolved["address_missing"]
        result["candidates"] = resolved["candidates"]
    return result


def run_serve(explicit_port=None, explicit_address=None, runtime_base=None) -> dict:
    """起或复用常驻服务并组装交付输出. 不碰 stdout, 不退出进程.

    启动/复用/探活/端口决策全在 _serve_core (ISSUE-04 面, 不改); 成功结果
    交 _apply_delivery 追加交付字段; 失败结果 (no_data_keys, port_in_use,
    state_mismatch, instance_running 等) 原样返回, 不加交付字段.
    """
    result = _serve_core(explicit_port, runtime_base)
    if result.get("success"):
        _apply_delivery(result, explicit_address, runtime_base)
    return result


# ---------------------------------------------------------------------------
# stop
# ---------------------------------------------------------------------------


def run_stop(runtime_base=None) -> dict:
    """停整个服务并归一化状态; 没有实例时幂等成功. 不碰 stdout, 不退出进程."""
    base = Path(runtime_base).resolve() if runtime_base is not None else cmc.runtime_dir()
    cmc.ensure_runtime_layout(base)
    lock_fd = _acquire_lock(base)
    if lock_fd is None:
        return cmc.error_result(
            "stop", "internal_error",
            f"运行时目录锁等待超过 {LOCK_WAIT_SECONDS} 秒: {base / LOCK_FILENAME}",
            "确认没有其它 codebase-map 调用长时间持锁后重试.",
        )
    unlink_lock = False
    try:
        state, err = _load_state(base)
        if err is not None:
            return cmc.error_result(
                "stop", "internal_error", err,
                "state.json 损坏无法判读; 按 SKILL.md 复原步骤处理.",
            )
        if state is None:
            return cmc.success_result(
                "stop", stopped=False,
                note="当前没有在跑的服务 (运行时目录还没有状态记录).",
            )
        pid = state.get("pid")
        if pid is None or not _pid_alive(pid):
            # 幂等: 归一化状态 (pid 置空, 写 stopped_at, 保留端口记录), 清锁文件
            if pid is not None:
                note = f"记录的 pid {pid} 已不存在, 残留记录不算存活, 没有在跑的服务."
            elif state.get("stopped_at"):
                note = "当前没有在跑的服务 (状态记录显示已知停机)."
            else:
                note = "当前没有在跑的服务."
            state["pid"] = None
            if not state.get("stopped_at"):
                state["stopped_at"] = _utc_now_iso()
            _atomic_write_state(base, state)
            unlink_lock = True
            return cmc.success_result("stop", stopped=False, note=note)
        if not _is_our_daemon(pid):
            return cmc.error_result(
                "stop", "state_mismatch",
                f"状态记录的 pid {pid} 存活, 但它不是本服务的守护进程; 拒绝停止以免误伤无关进程.",
                "先核实该 pid 的归属; 确认后按 SKILL.md 复原步骤处理.",
            )
        recorded_port = state.get("port")
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass  # 恰好在发送前死了: 落到下面的等待循环按已死处理
        deadline = time.monotonic() + STOP_WAIT_SECONDS
        while _pid_alive(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        if _pid_alive(pid):
            return cmc.error_result(
                "stop", "stop_failed",
                f"已发送 SIGTERM, 但 pid {pid} 在 {STOP_WAIT_SECONDS} 秒后仍在运行; 不自动 SIGKILL.",
                "稍后可再次执行 stop; 若持续失败, 按日志排查该进程为何不退出.",
            )
        state["pid"] = None
        state["stopped_at"] = _utc_now_iso()
        _atomic_write_state(base, state)
        unlink_lock = True
        _log_line(base, f"stop: stopped pid={pid} port={recorded_port}")
        payload = {}
        if isinstance(recorded_port, int):
            payload["port"] = recorded_port
        return cmc.success_result(
            "stop", stopped=True, pid=pid,
            note=f"服务已停止, 端口 {recorded_port} 上的旧地址已失效; serve-root 与 cache 保留.",
            **payload,
        )
    finally:
        _release_lock(lock_fd, base=base, unlink=unlink_lock)


# ---------------------------------------------------------------------------
# build 侧接线 (ISSUE-02/03 消费): 锁内更新 data_keys
# ---------------------------------------------------------------------------


def run_update_data_keys(entries, runtime_base=None) -> dict:
    """build 专用: 文件锁内更新 state.json 的 data_keys, 其余字段保留 (缺失时初始化骨架).

    entries 形如 [{key, source_cc_json, built_at, bytes}]; TECHNICAL 要求
    build 的副本复制与 data_keys 更新都在锁内完成, 副本复制由 build 自己做,
    本函数只承接锁与状态落盘.
    """
    base = Path(runtime_base).resolve() if runtime_base is not None else cmc.runtime_dir()
    cmc.ensure_runtime_layout(base)
    lock_fd = _acquire_lock(base)
    if lock_fd is None:
        return cmc.error_result(
            "build", "internal_error",
            f"运行时目录锁等待超过 {LOCK_WAIT_SECONDS} 秒: {base / LOCK_FILENAME}",
            "确认没有其它 codebase-map 调用长时间持锁后重试.",
        )
    try:
        state, err = _load_state(base)
        if err is not None:
            return cmc.error_result(
                "build", "internal_error", err,
                "state.json 损坏无法判读; 按 SKILL.md 复原步骤处理.",
            )
        if state is None:
            state = _fresh_state(base)
        state["data_keys"] = list(entries)
        _atomic_write_state(base, state)
        return cmc.success_result(
            "update-data-keys",
            data_keys=state["data_keys"],
            runtime_dir=str(base),
        )
    finally:
        _release_lock(lock_fd)


# ---------------------------------------------------------------------------
# HTTP 面: 只读静态服务 serve_root (BR-029, m13 D023)
# ---------------------------------------------------------------------------


class _Handler(SimpleHTTPRequestHandler):
    """只读静态服务: 先 resolve() 再判 relative_to(serve_root), 根外路径与根外软链一律 404.

    不做目录 listing (无 index.html 的目录 404), 不做 HTML5 回退, 不提供
    上传/写接口 (POST/PUT 走基类的 501 Unsupported method).
    """

    def send_head(self):
        root = Path(self.directory).resolve()
        try:
            fs = Path(super().translate_path(self.path)).resolve()
            fs.relative_to(root)
        except (ValueError, OSError):
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None
        if fs.is_dir():
            index = fs / "index.html"
            if index.is_file():
                fs = index
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Directory listing disabled")
                return None
        if not fs.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None
        try:
            handle = open(fs, "rb")
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None
        try:
            size = os.fstat(handle.fileno()).st_size
            ctype = mimetypes.guess_type(str(fs))[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(size))
            self.end_headers()
            return handle
        except Exception:
            handle.close()
            raise


def serve_forever(port: int, runtime_base) -> None:
    """守护进程主体: 绑 0.0.0.0:<port>, 只读静态服务 serve_root, 不设空闲退出."""
    base = Path(runtime_base).resolve()
    cmc.ensure_runtime_layout(base)
    serve_root = (base / "serve-root").resolve()
    handler = functools.partial(_Handler, directory=str(serve_root))
    try:
        httpd = ThreadingHTTPServer((cmc.BIND, port), handler)
    except OSError as exc:
        code = "port_in_use" if exc.errno == errno.EADDRINUSE else "internal_error"
        _write_startup_error(
            base, code,
            f"守护进程绑定 {cmc.BIND}:{port} 失败: {exc}",
            "端口被占不接管不换端口; 换端口用 serve --port <N>.",
        )
        _log_line(base, f"daemon: bind failed on {cmc.BIND}:{port}: {exc}")
        raise SystemExit(1)
    _log_line(base, f"daemon: serving {serve_root} on {cmc.BIND}:{port} pid={os.getpid()}")
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
        _log_line(base, f"daemon: exiting pid={os.getpid()}")


# ---------------------------------------------------------------------------
# 内部隐藏入口
# ---------------------------------------------------------------------------


def _daemon_main(argv) -> int:
    if len(argv) != 2:
        sys.stderr.write("用法(内部): codemap_service.py _serve-daemon <port> <runtime_dir>\n")
        return 2
    serve_forever(int(argv[0]), Path(argv[1]))
    return 0


if __name__ == "__main__":
    _argv = sys.argv[1:]
    if _argv and _argv[0] == DAEMON_SUBCOMMAND:
        raise SystemExit(_daemon_main(_argv[1:]))
    sys.stderr.write(
        "codebase-map 内部模块: 请通过 codebase-map.py 调用"
        f" (守护入口 {DAEMON_SUBCOMMAND} 不对外).\n"
    )
    raise SystemExit(2)
