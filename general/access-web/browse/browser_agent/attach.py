"""只读会话视图: 附加到已运行会话做观察, 绝不启动浏览器.

本模块全部函数无副作用: 不启动 Chromium, 不写 metadata, 不创建目录.
CDP 只读路径不调用 browser.close() (CDP 连接上的 close 会杀远端 Chromium),
仅经 sync_playwright 上下文管理器释放本地句柄.

注意: 若当前进程已持有活跃 Session (operations 已连接浏览器), 应优先复用
Session 页面 (见 operations.status), 避免嵌套 sync_playwright 事件循环.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Iterator, Optional, TYPE_CHECKING

from browser_agent._proc import is_pid_alive
from browser_agent._proc import is_port_open
from browser_agent.config import BrowserConfig

if TYPE_CHECKING:
    from playwright.sync_api import BrowserContext


@dataclass
class SessionProbe:
    """存活探测结果: 双检结论 + metadata 摘录 (无可用 metadata 时字段为 None)."""

    alive: bool
    pid: Optional[int] = None
    cdp_port: Optional[int] = None
    profile_dir: Optional[str] = None


def _valid_pid_port(pid: object, cdp_port: object) -> bool:
    """metadata 中的 pid/端口类型与取值合法 (拒绝 bool, 它是 int 子类)."""
    return (
        isinstance(pid, int)
        and not isinstance(pid, bool)
        and pid > 0
        and isinstance(cdp_port, int)
        and not isinstance(cdp_port, bool)
        and 1 <= cdp_port <= 65535
    )


def probe(cwd: Optional[str] = None) -> SessionProbe:
    """pid + CDP 端口双检会话存活. 无副作用: 不启动浏览器, 不写 metadata."""
    config = BrowserConfig(cwd=cwd)
    if not config.browser_json.exists():
        return SessionProbe(alive=False)
    try:
        meta = config.read_metadata()
    except Exception:
        return SessionProbe(alive=False)
    if not isinstance(meta, dict):
        return SessionProbe(alive=False)

    pid = meta.get("pid")
    cdp_port = meta.get("cdp_port")
    profile_dir = meta.get("profile_dir") or str(config.profile_dir)

    alive = (
        _valid_pid_port(pid, cdp_port)
        and is_pid_alive(pid)
        and is_port_open(cdp_port)
    )
    return SessionProbe(
        alive=alive, pid=pid, cdp_port=cdp_port, profile_dir=profile_dir
    )


@contextlib.contextmanager
def attached_context(cwd: Optional[str] = None) -> Iterator[Optional["BrowserContext"]]:
    """只读附加到存活会话的默认 context.

    Yields:
        默认 BrowserContext; 会话未存活或无可用 context 时 yield None.

    不启动浏览器, 不写 metadata. CDP 连接失败抛异常, 由调用方决定语义
    (状态探测可将异常折算为 alive=False, 读取命令可映射为领域错误码).
    """
    from playwright.sync_api import sync_playwright

    p = probe(cwd=cwd)
    if not p.alive:
        yield None
        return
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{p.cdp_port}")
        # 不调用 browser.close(): CDP 连接上的 close 会杀远端 Chromium;
        # sync_playwright 上下文管理器负责释放本地句柄.
        yield browser.contexts[0] if browser.contexts else None
