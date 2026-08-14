"""浏览器生命周期管理.

使用脱离式 Chromium 子进程 + CDP 连接实现跨进程共享.
首次启动时通过 subprocess.Popen 启动 Chromium, 后续进程通过
connect_over_cdp 复用同一浏览器与 profile.
"""

import contextlib
import json
import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import Browser as PWBrowser
from playwright.sync_api import BrowserContext
from playwright.sync_api import Page
from playwright.sync_api import Playwright
from playwright.sync_api import sync_playwright

from browser_agent._proc import find_pids_by_cmdline
from browser_agent._proc import is_port_open
from browser_agent._proc import kill_pid
from browser_agent.config import allocate_cdp_port
from browser_agent.config import BrowserConfig


@contextlib.contextmanager
def _startup_lock(config: BrowserConfig, timeout: float = 120.0):
    """启动/停止/清理并发互斥锁: 串行化 "读 metadata → 复用/启动/停止 → 写 metadata" 全程.

    POSIX 经 fcntl.flock 对 <session-key>.lock 加独占锁 (与 session 目录
    平级, 不被 cleanup 的 rmtree 删除, 避免锁文件 inode 分裂导致并发
    cleanup+start 双启同一 profile). 采用 LOCK_NB + 轮询 (每 0.2s),
    超过 timeout 抛 TimeoutError, 防止 holder 被 SIGSTOP/D-state 挂起时
    waiter 无限阻塞. Windows 降级为无锁: msvcrt 锁语义差异大, 且竞态窗口小.
    """
    if os.name == "nt":
        yield
        return
    import errno
    import fcntl

    config.session_root.parent.mkdir(parents=True, exist_ok=True)
    lock_path = config.startup_lock
    with open(lock_path, "a", encoding="utf-8") as lock_file:
        fd = lock_file.fileno()
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as e:
                if e.errno not in (errno.EACCES, errno.EAGAIN):
                    raise
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"获取 session 启动锁超时 ({timeout}s): {lock_path}"
                    ) from None
                time.sleep(0.2)
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)


def _load_session_cookies(context, config: BrowserConfig) -> None:
    """从 session 目录的 cookies.json 恢复 cookie 到 context."""
    cookies_path = config.session_root / "cookies.json"
    if not cookies_path.exists():
        return
    try:
        data = json.loads(cookies_path.read_text(encoding="utf-8"))
        if data:
            context.add_cookies(data)
    except Exception:
        pass


class Browser:
    """封装脱离式 Chromium 的启动与 CDP 连接.

    每次实例化持有独立的 Playwright 连接, 但底层 Chromium 进程可以
    跨实例/跨进程复用.
    """

    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[PWBrowser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    @property
    def page(self) -> Page:
        """获取当前页面对象, 必要时自动连接或启动."""
        if self._page is None:
            self.start()
        return self._page

    def start(self) -> "Browser":
        """连接到已有 Chromium, 或在需要时脱离式启动新实例."""
        # 已有页面且可用时直接复用
        if self._page is not None:
            try:
                self._page.evaluate("1")
                return self
            except Exception:
                self._release_handles()

        with _startup_lock(self.config):
            self.config.ensure_session_dirs()
            # 持锁后 (重)读 metadata: 等待期间可能已有其他进程完成首启
            meta = self._read_metadata()
            if meta and meta.get("cdp_port"):
                cdp_port = int(meta["cdp_port"])
                if is_port_open(cdp_port):
                    try:
                        self._connect(cdp_port)
                        if self._page is not None:
                            return self
                    except Exception:
                        self._release_handles()

            # 无法复用则脱离式启动 (杀旧 → 分配端口 → 启动 → 写 metadata 全程持锁)
            self._launch_detached()
        return self

    def stop(self) -> None:
        """释放 Playwright 连接, 不杀掉 Chromium 进程."""
        self._release_handles()

    def _read_metadata(self) -> Optional[dict]:
        if not self.config.browser_json.exists():
            return None
        try:
            return self.config.read_metadata()
        except Exception:
            return None

    def _connect(self, cdp_port: int) -> None:
        """通过 CDP 端口连接到已有 Chromium."""
        self._wait_for_port(cdp_port)
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.connect_over_cdp(
            f"http://127.0.0.1:{cdp_port}"
        )
        self._context = self._resolve_context(self._browser)
        self._page = self._resolve_page(self._context)
        # newtab 页面无法 set_content, 先跳到 blank
        if self._page and str(self._page.url).startswith("chrome://"):
            self._page.goto("about:blank")

    def _launch_detached(self) -> None:
        """脱离式启动 Chromium 并写入 metadata."""
        binary = self.config.locate_chromium_binary()
        self.config.profile_dir.mkdir(parents=True, exist_ok=True)

        # 清理可能存在的旧 metadata, 避免端口/PID 混淆
        if self.config.browser_json.exists():
            # N1: 先杀掉旧 Chromium 并等待其退出, 避免孤儿进程与新进程
            # 共享 user-data-dir (SingletonLock 竞态)
            old_meta = self._read_metadata()
            if old_meta:
                old_pid = old_meta.get("pid")
                if old_pid:
                    kill_pid(int(old_pid), identity_hint=str(self.config.profile_dir))
            try:
                self.config.browser_json.unlink()
            except Exception:
                pass

        try:
            self._spawn_and_connect(binary)
            return
        except Exception as first_error:
            # Popen 与 write_metadata 之间崩溃 (如工具进程被 kill) 会留下无
            # metadata 记录的孤儿 chromium, 它持有 profile 的 SingletonLock,
            # 导致新实例的 CDP 端口永不就绪 (每次 navigate 30s 超时).
            # POSIX 下严格按本 session 的 user-data-dir 清扫此类孤儿后重试一次;
            # Windows 无 /proc 可扫, 跳过清扫直接报错.
            if not self._sweep_orphan_chromium():
                raise RuntimeError(
                    f"Failed to launch detached Chromium: {first_error}"
                ) from first_error

        try:
            self._spawn_and_connect(binary)
        except Exception as e:
            raise RuntimeError(f"Failed to launch detached Chromium: {e}") from e

    def _spawn_and_connect(self, binary: Path) -> None:
        """分配端口, 脱离式启动 Chromium, CDP 连接, 恢复 cookie, 写 metadata."""
        cdp_port = allocate_cdp_port()
        headless = os.environ.get("BROWSER_HEADED", "").lower() != "true"
        args = self._build_chromium_args(binary, cdp_port, headless)

        popen_kwargs: dict = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "close_fds": True,
        }
        if os.name == "nt":
            import subprocess as _sp

            popen_kwargs["creationflags"] = (
                _sp.DETACHED_PROCESS | _sp.CREATE_NEW_PROCESS_GROUP
            )
        else:
            popen_kwargs["start_new_session"] = True

        process = subprocess.Popen(args, **popen_kwargs)

        try:
            self._connect(cdp_port)
            _load_session_cookies(self._context, self.config)
        except Exception:
            # 启动失败时杀掉新进程 (kill_pid 内置 SIGTERM → 等待 → SIGKILL
            # 升级), 并释放 Playwright 句柄, 避免残留
            kill_pid(process.pid, identity_hint=str(self.config.profile_dir))
            self._release_handles()
            raise

        self.config.write_metadata(
            {
                "pid": process.pid,
                "cdp_port": cdp_port,
                "profile_dir": str(self.config.profile_dir),
                "chromium_binary": str(binary),
            }
        )

    def _sweep_orphan_chromium(self) -> bool:
        """POSIX: 清扫 cmdline 指向本 session user-data-dir 的残留 chromium 进程.

        严格匹配本 session 的 user-data-dir 完整路径 (每个 session-key 唯一),
        不误杀其他会话的浏览器; 排除自身进程. Windows 无法安全枚举命令行,
        直接跳过.

        Returns:
            是否杀掉了至少一个进程 (决定是否值得重试启动).
        """
        if os.name == "nt":
            return False
        profile = str(self.config.profile_dir)
        swept = False
        for pid in find_pids_by_cmdline(profile):
            if pid in (os.getpid(), os.getppid()):
                continue
            if kill_pid(pid, identity_hint=profile):
                swept = True
        return swept

    def _build_chromium_args(
        self,
        binary: Path,
        cdp_port: int,
        headless: bool,
    ) -> list:
        args = [
            str(binary),
            f"--remote-debugging-port={cdp_port}",
            f"--user-data-dir={self.config.profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--disable-background-networking",
            "--disable-sync",
            "--disable-extensions",
            "--disable-features=TranslateUI",
        ]
        if headless:
            args.append("--headless=new")
        # 无头模式下不保留默认窗口大小限制
        args.append("--window-size=1280,720")
        return args

    def _resolve_context(self, browser: PWBrowser) -> BrowserContext:
        """优先使用默认 context, 以保留 persistent profile."""
        contexts = browser.contexts
        if contexts:
            return contexts[0]
        return browser.new_context()

    def _resolve_page(self, context: BrowserContext) -> Page:
        """复用已有页面; 否则新建页面."""
        pages = context.pages
        if pages:
            return pages[0]
        return context.new_page()

    def _release_handles(self) -> None:
        """释放 Playwright 连接句柄."""
        self._page = None
        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    @staticmethod
    def _wait_for_port(port: int, timeout: float = 30.0) -> None:
        """轮询等待 CDP 端口可用."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1.0):
                    return
            except Exception:
                time.sleep(0.1)
        raise TimeoutError(f"CDP port {port} not reachable within {timeout}s")
