"""运行时环境探测与会话路径配置.

负责:
- OS / Python 解释器 / 系统临时目录探测
- session-key 计算
- session 目录规划
- CDP 端口自绑分配
- Chromium 二进制定位与缓存
- browser metadata 读写
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from playwright.sync_api import sync_playwright


class ChromiumNotInstalledError(RuntimeError):
    """Chromium 未安装时抛出, 携带修复命令."""

    def __init__(self) -> None:
        command = f"{sys.executable} -m playwright install chromium"
        super().__init__(f"Chromium not installed. Run: {command}")


def _canonicalize(cwd: str) -> str:
    """返回跨平台稳定的 cwd 规范化字符串.

    使用 os.path.normcase: Windows 统一大小写, POSIX 保持原样
    (POSIX 文件系统大小写敏感, /tmp/ProjA 与 /tmp/proja 是不同目录).
    """
    path = Path(cwd).resolve()
    return os.path.normcase(str(path))


def compute_session_key(cwd: str) -> str:
    """基于 cwd 计算 16 位十六进制 session-key."""
    canonical = _canonicalize(cwd)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest[:16]


def get_runtime_info() -> Dict[str, Any]:
    """返回运行时探测信息."""
    return {
        "os": os.name,
        "python_executable": sys.executable,
        "tempdir": tempfile.gettempdir(),
    }


def get_session_paths(tempdir: str, session_key: str) -> Dict[str, Path]:
    """规划 session 目录结构, 返回各路径.

    startup_lock 放在与 session_root 平级的位置而非其内部: cleanup 的
    rmtree 删除 session_root 后锁文件仍在, 避免锁文件被删后新 open 得到
    新 inode, 导致并发 cleanup+start 各持一把锁的 split-brain 双启.
    """
    session_root = Path(tempdir) / "access-web" / session_key
    artifacts = session_root / "artifacts"
    return {
        "session_root": session_root,
        "startup_lock": session_root.parent / f"{session_key}.lock",
        "browser_json": session_root / "browser.json",
        "profile_dir": session_root / "profile",
        "artifacts_dir": artifacts,
        "screenshots_dir": artifacts / "screenshots",
        "downloads_dir": artifacts / "downloads",
        "logs_dir": artifacts / "logs",
    }


def allocate_cdp_port() -> int:
    """自绑 socket 到端口 0, 返回可用端口."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    _, port = s.getsockname()
    s.close()
    return int(port)


def read_metadata(path: Path | str) -> Dict[str, Any]:
    """从 JSON 文件读取 metadata."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_metadata(path: Path | str, data: Dict[str, Any]) -> None:
    """将 metadata 写入 JSON 文件, 按需创建父目录."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _chmod_private(path: Path) -> None:
    """POSIX 下将目录权限设为 700 (session 目录含 cookies/登录态); Windows 跳过."""
    if os.name == "nt":
        return
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass


class BrowserConfig:
    """封装单个 browser session 的运行时配置."""

    def __init__(self, cwd: Optional[str] = None, tempdir: Optional[str] = None):
        self.cwd = cwd or os.getcwd()
        self.tempdir = tempdir or tempfile.gettempdir()
        self.session_key = compute_session_key(self.cwd)
        paths = get_session_paths(self.tempdir, self.session_key)
        self.session_root: Path = paths["session_root"]
        self.startup_lock: Path = paths["startup_lock"]
        self.browser_json: Path = paths["browser_json"]
        self.profile_dir: Path = paths["profile_dir"]
        self.artifacts_dir: Path = paths["artifacts_dir"]
        self.screenshots_dir: Path = paths["screenshots_dir"]
        self.downloads_dir: Path = paths["downloads_dir"]
        self.logs_dir: Path = paths["logs_dir"]

    def ensure_session_dirs(self) -> None:
        """创建 session 根目录与 artifacts 子目录, 并修正权限 (幂等).

        POSIX 下 session 根目录 chmod 700 (含 cookies/登录态), 已存在的
        目录也会修正权限; Windows 跳过 chmod.
        """
        self.session_root.mkdir(parents=True, exist_ok=True)
        _chmod_private(self.session_root)
        for d in (
            self.artifacts_dir,
            self.screenshots_dir,
            self.downloads_dir,
            self.logs_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

    def read_metadata(self) -> Dict[str, Any]:
        """读取 session 的 browser.json."""
        return read_metadata(self.browser_json)

    def write_metadata(self, data: Dict[str, Any]) -> None:
        """写入 session 的 browser.json."""
        write_metadata(self.browser_json, data)

    def locate_chromium_binary(self) -> Path:
        """定位 Chromium 二进制, 优先使用缓存, 否则经 Playwright 探测.

        若 Chromium 未安装, 抛出 ChromiumNotInstalledError.
        """
        if self.browser_json.exists():
            try:
                cached = self.read_metadata().get("chromium_binary")
                if cached and Path(cached).exists():
                    return Path(cached)
            except (OSError, ValueError):
                pass

        with sync_playwright() as p:
            binary = Path(p.chromium.executable_path)

        if not binary.exists():
            raise ChromiumNotInstalledError()

        try:
            metadata = self.read_metadata() if self.browser_json.exists() else {}
        except (OSError, ValueError):
            metadata = {}
        metadata["chromium_binary"] = str(binary)
        self.write_metadata(metadata)
        return binary
