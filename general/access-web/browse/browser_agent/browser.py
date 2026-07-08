"""浏览器生命周期管理.

使用脱离式 Chromium 子进程 + CDP 连接实现跨进程共享.
首次启动时通过 subprocess.Popen 启动 Chromium, 后续进程通过
connect_over_cdp 复用同一浏览器与 profile.
"""

import json
import os
import shutil
import signal
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

from browser_agent.config import allocate_cdp_port
from browser_agent.config import BrowserConfig


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

        # 尝试根据 metadata 复用已存在的 Chromium
        meta = self._read_metadata()
        if meta and meta.get("cdp_port"):
            cdp_port = int(meta["cdp_port"])
            if self._is_port_open(cdp_port):
                try:
                    self._connect(cdp_port)
                    if self._page is not None:
                        return self
                except Exception:
                    self._release_handles()

        # 无法复用则脱离式启动
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
        cdp_port = allocate_cdp_port()
        self.config.profile_dir.mkdir(parents=True, exist_ok=True)

        # 清理可能存在的旧 metadata, 避免端口/PID 混淆
        if self.config.browser_json.exists():
            # N1: 先杀掉旧 Chromium, 避免孤儿进程与新进程共享 user-data-dir
            old_meta = self._read_metadata()
            if old_meta:
                old_pid = old_meta.get("pid")
                if old_pid:
                    _kill_pid(int(old_pid))
            try:
                self.config.browser_json.unlink()
            except Exception:
                pass

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
        except Exception as e:
            # 启动失败时尽量清理, 避免残留
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            except Exception:
                pass
            raise RuntimeError(f"Failed to launch detached Chromium: {e}") from e

        self.config.write_metadata(
            {
                "pid": process.pid,
                "cdp_port": cdp_port,
                "profile_dir": str(self.config.profile_dir),
                "chromium_binary": str(binary),
            }
        )

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
    def _is_port_open(port: int, timeout: float = 1.0) -> bool:
        """快速探测端口是否可连接."""
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=timeout):
                return True
        except Exception:
            return False

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


def _kill_pid(pid: int) -> None:
    """跨平台尝试结束进程, 用于 _launch_detached 清理孤儿 Chromium."""
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            pass
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except Exception:
            pass
