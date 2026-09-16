#!/usr/bin/env -S uv run python
"""sandbox-worktree lifecycle command.

用法:
  swt birth|resume|status|terminate [--repo PATH] [--records-root PATH] ...

退出码:
  0 成功, 1 等待用户决定, 2 前置条件失败, 3 中途失败可重入, 4 环境错误.

status 只读盘点全部母体对 (config/daemon/容器/镜像/网络), 永不创建或修改 runtime 状态.

并行母体 (2026-09-13 改造): 管理单元 = (主仓, 母体分支) 对, 多对并存互不干扰.
hideRefs 按对下沉到各母体 config.worktree (主仓 config 只留跨母体共享的 deny 三键
+ extensions.worktreeConfig); 每对一个 git daemon (服务母体目录); identity 按对派生.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import ipaddress
import json
import os
import re
import shutil
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple


SCHEMA = 2
# 配置两层 (并行母体改造): 仓级 (主仓 config, 跨母体共享) + 对级 (母体 config.worktree, 每对一份).
REPO_CONFIG_KEYS = (
    "receive.denyCurrentBranch",
    "receive.denyNonFastForwards",
    "receive.denyDeletes",
    "extensions.worktreeConfig",
)
PAIR_CONFIG_KEYS = (
    "receive.hideRefs",
    "uploadpack.hideRefs",
)
SLUG_SCRIPT = Path(__file__).resolve().parents[2] / "use-worktree" / "scripts" / "slug.py"
_SLUG_CACHE: dict[Path, str] = {}
MUTATING_COMMANDS = ("podman", "nft", "ssh", "uv", "pgrep")
_UNSET = object()

# P0-1 git 通道: 容器不再经 pasta 映射访问 host daemon (宿主换网络后映射失效).
# 改为: host 侧 socat 把 unix socket (落容器挂载目录) 桥到 daemon 回环端口;
# 容器内 socat 监听固定回环端口转发到该 socket, remote 恒定, 永不失配.
GIT_CONTAINER_PORT = 9418
GIT_BRIDGE_CONTAINER_DIR = "/run/swt-git"
GIT_BRIDGE_SOCK = "git.sock"

# P1-6 agent 系统提示词母本制: 母本在 <skill>/agent-prompts/, birth 留档到
# runtime/<identity>/agent-prompts/<容器>/ 后只读单文件挂载进容器.
AGENT_PROMPT_SOURCE_DIR = Path(__file__).resolve().parents[1] / "agent-prompts"
AGENT_PROMPT_MOUNTS = (
    ("pi_AGENTS.md", "/home/bolo/.pi/agent/AGENTS.md"),
    ("codex_AGENTS.md", "/home/bolo/.codex/AGENTS.md"),
    ("kimi-code_AGENTS.md", "/home/bolo/.kimi-code/AGENTS.md"),
)

# M08 D003 启动脚本母本制: 母本在 <skill>/headed-browser/, birth 解析 chromium
# 精确路径 (F006) 生成实例留档 runtime/<identity>/ 后只读单文件挂载进容器固定路径.
HEADED_BROWSER_MASTER = Path(__file__).resolve().parents[1] / "headed-browser" / "swt-headed-browser.sh"
HEADED_BROWSER_CONTAINER_PATH = "/home/bolo/.local/bin/swt-headed-browser.sh"
CHROMIUM_PATH_PLACEHOLDER = "__CHROMIUM__"
# UD-06: 多 rev 并存取最高 (sort -V | tail -1), throwaway 一次性成本约 1s.
CHROMIUM_RESOLVE_PIPELINE = (
    "ls -d /home/bolo/.cache/ms-playwright/chromium-*/chrome-linux*/chrome | sort -V | tail -1"
)

# skill 库运行期挂载: host ~/.agents/skills 只读挂进容器同路径, 遮蔽镜像烤入
# 副本 (实时跟随 host 版本); 每个带 pyproject 的项目另挂 .venv 匿名卷 — 从镜像
# 播种可写, 源码树保持 ro. 依赖锁定靠已部署的 uv.lock, venv 种子与 lock 不匹配
# 时容器内无法联网重装, 需重建 base.
SKILLS_HOST_DIR = Path.home() / ".agents" / "skills"
SKILLS_CONTAINER_DIR = "/home/bolo/.agents/skills"


class SwtError(Exception):
    def __init__(self, code: int, tag: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.tag = tag
        self.message = message


class SwtEnvError(SwtError):
    def __init__(self, message: str) -> None:
        super().__init__(4, "ENV", message)


class PreconditionError(SwtError):
    def __init__(self, message: str) -> None:
        super().__init__(2, "FAIL", message)


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout: float | None = None,
    input: str | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        # input 仅在需要 stdin 的调用点传入 (M08 ISSUE-06 enroll-device-key),
        # 不污染既有 fake run 边界签名
        options: dict[str, Any] = {"cwd": cwd, "timeout": timeout}
        if input is not None:
            options["input"] = input
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            **options,
        )
    except FileNotFoundError as exc:
        raise SwtEnvError(f"缺少环境命令: {command[0]}") from exc


def validate_git_hide_refs_syntax() -> None:
    with tempfile.TemporaryDirectory(prefix="swt-git-probe-") as temporary:
        probe = Path(temporary) / "probe"
        initialized = run(["git", "init", "-q", "-b", "main", str(probe)])
        if initialized.returncode != 0:
            raise SwtEnvError(f"git ! 语法重验初始化失败: {initialized.stderr.strip()}")
        for key, value in (("user.name", "swt-probe"), ("user.email", "swt-probe@example.invalid")):
            configured = run(["git", "-C", str(probe), "config", key, value])
            if configured.returncode != 0:
                raise SwtEnvError(f"git ! 语法重验配置失败: {configured.stderr.strip()}")
        (probe / "probe.txt").write_text("probe\n", encoding="utf-8")
        for command in (
            ["git", "-C", str(probe), "add", "probe.txt"],
            ["git", "-C", str(probe), "commit", "-qm", "probe"],
            ["git", "-C", str(probe), "config", "--add", "uploadpack.hideRefs", "refs/heads"],
            ["git", "-C", str(probe), "config", "--add", "uploadpack.hideRefs", "!refs/heads/main"],
        ):
            result = run(command)
            if result.returncode != 0:
                raise SwtEnvError(f"git ! 语法重验失败: {result.stderr.strip()}")
        advertised = run(["git", "-C", str(probe), "ls-remote", "."])
        if advertised.returncode != 0 or "refs/heads/main" not in advertised.stdout:
            raise SwtEnvError(
                "git ! 否定 hideRefs 语法行为重验失败: "
                f"{advertised.stderr.strip() or advertised.stdout.strip()}"
            )


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise SwtEnvError(f"PATH 中缺少 {name}")


def resolve_repo(raw_repo: str | None) -> Path:
    base = Path(raw_repo).expanduser() if raw_repo else Path.cwd()
    base = base.resolve()
    result = run(["git", "-C", str(base), "rev-parse", "--git-common-dir"])
    if result.returncode != 0:
        raise PreconditionError("不是 git 仓库, 无法解析主仓")
    common = Path(result.stdout.strip())
    if not common.is_absolute():
        common = (base / common).resolve()
    else:
        common = common.resolve()
    if common.name == ".git":
        return common.parent
    raise PreconditionError("git common dir 不是预期的 .git 目录")


def resolve_project_slug(repo: Path) -> str:
    key = repo.resolve()
    cached = _SLUG_CACHE.get(key)
    if cached is not None:
        return cached
    result = run(["uv", "run", "python", str(SLUG_SCRIPT), repo.name])
    if result.returncode != 0:
        raise SwtEnvError(f"slug.py 失败: {result.stderr.strip()}")
    for line in result.stdout.splitlines():
        if line.startswith("slug="):
            value = line.removeprefix("slug=")
            _SLUG_CACHE[key] = value
            return value
    raise SwtEnvError(f"slug.py 未返回 slug: {result.stdout!r}")


def repo_scope_identity(repo: Path) -> str:
    """仓级作用域名 (锁文件): slug + sha1(主仓路径)[:8], 与旧版 runtime identity 同构造."""
    project_id = str(repo.resolve())
    digest = hashlib.sha1(project_id.encode("utf-8")).hexdigest()[:8]
    return f"{resolve_project_slug(repo)}-{digest}"


def pair_identity(repo: Path, mother: Path) -> str:
    """对级 identity (并行母体): slug + sha1(母体目录路径)[:8]."""
    digest = hashlib.sha1(str(mother.resolve()).encode("utf-8")).hexdigest()[:8]
    return f"{resolve_project_slug(repo)}-{digest}"


def load_runtime_tolerant(path: Path) -> dict[str, Any] | None:
    """扫描用宽松读取: 缺席/畸形一律 None, 不抛错."""
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def repo_runtime_files(records_root: Path, repo: Path) -> list[Path]:
    """本主仓的全部 runtime 文件 (并行母体 = 一对一份; 含旧 scheme 仓级 identity)."""
    directory = records_root / "runtime"
    if not directory.is_dir():
        return []
    repo_str = str(repo.resolve())
    found: list[Path] = []
    for path in sorted(directory.glob("*.json")):
        data = load_runtime_tolerant(path)
        if data is not None and data.get("repo") == repo_str:
            found.append(path)
    return found


def resolve_pair_identity(repo: Path, records_root: Path, mother: Path) -> str:
    """对 identity 解析. 兼容铁律: 旧 scheme (仓路径哈希) runtime 已绑定本母体时原样沿用 —
    桥 socket 路径焊死在运行中容器的 bind mount 里, 不可改名不可搬."""
    new = pair_identity(repo, mother)
    if (records_root / "runtime" / f"{new}.json").is_file():
        return new
    for path in repo_runtime_files(records_root, repo):
        if path.stem == new:
            continue
        data = load_runtime_tolerant(path)
        if data is None:
            continue
        _, directory = runtime_mother(data)
        if directory is not None and directory == mother.resolve():
            return path.stem
    return new


def pair_runtime_path(records_root: Path, repo: Path, mother: Path) -> Path:
    return records_root / "runtime" / f"{resolve_pair_identity(repo, records_root, mother)}.json"


def load_repo_runtimes(records_root: Path, repo: Path) -> list[tuple[Path, dict[str, Any]]]:
    """读入本主仓全部 runtime (跳过不可读文件并告警, 不阻断盘点)."""
    runtimes: list[tuple[Path, dict[str, Any]]] = []
    for path in repo_runtime_files(records_root, repo):
        data = load_runtime_tolerant(path)
        if data is None:
            print(f"[SWT] 跳过不可读 runtime: {path}", file=sys.stderr)
            continue
        runtimes.append((path, data))
    return runtimes


def no_mother_state(*, runtime_stale: bool = False) -> dict[str, Any]:
    state: dict[str, Any] = {
        "branch": None,
        "dir": None,
        "exists": False,
        "worktree-dirty": False,
    }
    if runtime_stale:
        state["runtime-stale"] = True
    return state


def empty_state(repo: Path) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "repo": str(repo.resolve()),
        "mother": no_mother_state(),
        "config": {"swt-form": False},
        "daemon": None,
        "containers": [],
        "image": None,
        "network": None,
        "mothers": [],
    }


def git_values(repo: Path, key: str) -> list[str]:
    result = run(["git", "-C", str(repo), "config", "--get-all", key])
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()


def worktree_entries(repo: Path) -> list[dict[str, str]]:
    result = run(["git", "-C", str(repo), "worktree", "list", "--porcelain"])
    if result.returncode != 0:
        return []
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in result.stdout.splitlines() + [""]:
        if not line:
            if current:
                entries.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current["dir"] = value
        elif key == "branch":
            current["branch"] = value.removeprefix("refs/heads/")
    return entries


def runtime_mother(runtime: dict[str, Any] | None) -> tuple[str | None, Path | None]:
    if not runtime:
        return None, None
    mother = runtime.get("mother")
    if isinstance(mother, dict):
        branch = mother.get("branch")
        directory = mother.get("dir")
        return (
            branch if isinstance(branch, str) else None,
            Path(directory).resolve() if isinstance(directory, str) else None,
        )
    branch = runtime.get("mother_branch")
    directory = runtime.get("mother_dir")
    return (
        branch if isinstance(branch, str) else None,
        Path(directory).resolve() if isinstance(directory, str) else None,
    )


def mother_state_from_runtime(repo: Path, runtime: dict[str, Any] | None) -> dict[str, Any]:
    """runtime 记录的母体对齐 worktree 现实: 记录缺失 = 无母体;
    分支无对应 worktree 或目录与记录不符 = runtime-stale."""
    runtime_branch, runtime_dir = runtime_mother(runtime)
    if runtime_branch is None and runtime_dir is None:
        return no_mother_state()
    selected: dict[str, str] | None = None
    for entry in worktree_entries(repo):
        if entry.get("branch") != runtime_branch:
            continue
        if runtime_dir is not None and Path(entry["dir"]).resolve() != runtime_dir:
            continue
        selected = entry
        break
    if selected is None:
        return no_mother_state(runtime_stale=True)
    directory = Path(selected["dir"]).resolve()
    dirty = False
    if directory.is_dir():
        result = run(["git", "-C", str(directory), "status", "--porcelain", "--untracked-files=all"])
        dirty = result.returncode == 0 and bool(result.stdout)
    return {
        "branch": runtime_branch,
        "dir": str(directory),
        "exists": directory.is_dir(),
        "worktree-dirty": dirty,
    }


def expected_repo_config() -> dict[str, list[str]]:
    """仓级 (主仓 config, 跨母体共享): deny 三键 + worktreeConfig 扩展开关."""
    return {
        "receive.denyCurrentBranch": ["updateInstead"],
        "receive.denyNonFastForwards": ["true"],
        "receive.denyDeletes": ["true"],
        "extensions.worktreeConfig": ["true"],
    }


def expected_pair_config(branch: str) -> dict[str, list[str]]:
    """对级 (母体 config.worktree, 每对一份): 只放行本对母体分支, 写入恒 --add."""
    return {
        "receive.hideRefs": ["refs/heads", f"!refs/heads/{branch}", "refs/tags", "refs/remotes"],
        "uploadpack.hideRefs": ["refs/heads", f"!refs/heads/{branch}", "refs/tags", "refs/remotes"],
    }


def worktree_config_values(mother: Path | None, key: str) -> list[str]:
    """母体 config.worktree 的值; 扩展未开/键不存在 → [] (--worktree 读写都要求扩展开启)."""
    if mother is None:
        return []
    result = run(["git", "-C", str(mother), "config", "--worktree", "--get-all", key])
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()


def config_layer_values(repo: Path, mother: Path | None, key: str) -> list[str]:
    """按键所属层读值: 对级键读母体 config.worktree, 其余读主仓 config."""
    if key in PAIR_CONFIG_KEYS:
        return worktree_config_values(mother, key)
    return git_values(repo, key)


def config_fingerprint(repo: Path, mother: Path | None) -> str:
    payload = {
        "repo": {key: git_values(repo, key) for key in REPO_CONFIG_KEYS},
        "pair-dir": str(mother) if mother else None,
        "pair": {key: worktree_config_values(mother, key) for key in PAIR_CONFIG_KEYS} if mother else {},
    }
    return hashlib.sha256(canonical_json(payload).encode()).hexdigest()


def values_match(actual: list[str], wanted: list[str]) -> bool:
    return Counter(actual) == Counter(wanted) if len(wanted) > 1 else actual == wanted


def config_matches_multiset(repo: Path, mother: Path | None, expected: dict[str, list[str]]) -> bool:
    return all(values_match(config_layer_values(repo, mother, key), wanted) for key, wanted in expected.items())


def pair_config_matches(repo: Path, mother: Path | None, branch: str | None) -> bool:
    """swt-form 对级判定: 仓级四键 + 本对 config.worktree hideRefs 全部就位."""
    if branch is None:
        return False
    if not config_matches_multiset(repo, None, expected_repo_config()):
        return False
    if mother is None:
        return False
    return config_matches_multiset(repo, mother, expected_pair_config(branch))


def validate_config_before_resources(repo: Path, mother: Path | None, expected: dict[str, list[str]]) -> None:
    for key, wanted in expected.items():
        actual = config_layer_values(repo, mother, key)
        if actual and not values_match(actual, wanted):
            raise PreconditionError(
                f"git config {key} 已有错误值, 不覆盖: 现有={actual!r}, 期望={wanted!r}"
            )


def config_unset_all(repo: Path, mother: Path | None, key: str) -> None:
    command = ["git", "-C", str(mother if key in PAIR_CONFIG_KEYS else repo), "config"]
    if key in PAIR_CONFIG_KEYS:
        if mother is None:
            return
        command.append("--worktree")
    command.extend(["--unset-all", key])
    run(command)


def config_add_value(repo: Path, mother: Path | None, key: str, value: str) -> subprocess.CompletedProcess[str]:
    # 对级键必须 -C 母体目录 (--worktree 写当前工作树的 config.worktree;
    # -C 主仓会写进主工作树的 config.worktree, 张冠李戴)
    command = ["git", "-C", str(mother if key in PAIR_CONFIG_KEYS else repo), "config"]
    if key in PAIR_CONFIG_KEYS:
        if mother is None:
            raise SwtError(3, "PARTIAL", f"对级配置 {key} 缺母体目录, 无法写入")
        command.append("--worktree")
    command.extend(["--add", key, value])
    return run(command)


def restore_config(repo: Path, mother: Path | None, snapshot: dict[str, list[str]]) -> None:
    for key, values in snapshot.items():
        config_unset_all(repo, mother, key)
        for value in values:
            config_add_value(repo, mother, key, value)


def configure_repo(repo: Path, mother: Path, branch: str) -> None:
    """两层一次写齐: 先仓级 (含 worktreeConfig 开关), 后对级 (--worktree --add);
    失败回滚快照. 对级多值恒 --add (裸赋值会覆盖前值, 实验踩坑)."""
    expected = {**expected_repo_config(), **expected_pair_config(branch)}
    snapshot = {key: config_layer_values(repo, mother, key) for key in expected}
    validate_config_before_resources(repo, mother, expected)
    try:
        for key, values in expected.items():
            if snapshot.get(key):
                continue
            for value in values:
                result = config_add_value(repo, mother, key, value)
                if result.returncode != 0:
                    raise PreconditionError(f"写入 git config {key} 失败: {result.stderr.strip()}")
        if not config_matches_multiset(repo, mother, expected):
            restore_config(repo, mother, snapshot)
            raise PreconditionError("git config 写入后校验失败, 已回滚快照")
    except SwtError:
        restore_config(repo, mother, snapshot)
        raise


def print_state(state: dict[str, Any], progress: str) -> None:
    print(progress)
    print("STATE " + json.dumps(state, ensure_ascii=False, separators=(",", ":")))


def load_runtime(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreconditionError(f"runtime 状态不可读取: {path}") from exc
    if not isinstance(data, dict):
        raise PreconditionError(f"runtime 状态不是对象: {path}")
    return data


def atomic_write_text(path: Path, content: str) -> None:
    """原子写文本: 同目录临时文件 + replace, 杜绝半截文件."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def resolve_mother_branch(_repo: Path, raw_branch: str) -> str:
    """母体分支名 = use-worktree 第零步产出的目标分支名原文 (不二次前缀化)."""
    value = raw_branch.strip()
    if not value:
        raise SwtEnvError("母体分支名为空")
    return value


def mother_dir_name(repo: Path, branch: str) -> str:
    """母体目录名 = use-worktree slug 规则 (<项目>-<真实来源分支>-<目标分支>)."""
    result = run(["uv", "run", "python", str(SLUG_SCRIPT), repo.name, default_branch(repo), branch])
    if result.returncode != 0:
        raise SwtEnvError(f"slug.py 失败: {result.stderr.strip()}")
    for line in result.stdout.splitlines():
        if line.startswith("dir="):
            value = line.removeprefix("dir=").strip()
            if value:
                return value
    raise SwtEnvError(f"slug.py 未返回 dir=: {result.stdout!r}")


def mother_path(repo: Path, branch: str) -> Path:
    # 母体 = 主仓同级兄弟目录 (用户拍板: 与 host 路径字面一致)
    return (repo.parent / mother_dir_name(repo, branch)).resolve()


def ref_tip(repo: Path, branch: str) -> str | None:
    result = run(["git", "-C", str(repo), "rev-parse", f"refs/heads/{branch}"])
    return result.stdout.strip() if result.returncode == 0 else None


def load_inherited_env(records_root: Path, slug: str) -> dict[str, str]:
    """环境变量继承清单: <records-root>/env.conf (全局) + <records-root>/<slug>/env.conf (项目, 同名覆盖).
    每行 NAME (值取 host 当前环境, 文件不存秘密) 或 NAME=value (固定值)."""
    inherited: dict[str, str] = {}
    for path in (records_root / "env.conf", records_root / slug / "env.conf"):
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                inherited[key.strip()] = value.strip()
            elif line in os.environ:
                inherited[line] = os.environ[line]
            else:
                print(f"[SWT] env 继承跳过: {line} (host 未设置)", file=sys.stderr)
    return inherited


# 隧道/虚拟接口前缀: 这些接口上的全局地址局域网够不着, 不得作局域网入口交付
# (VPN 在场时默认路由指向隧道, 跟默认路由必取错 — M14 发现 4)
TUNNEL_INTERFACE_PREFIXES = (
    "tun", "tap", "wg", "ppp", "utun", "ts", "tailscale",
    "docker", "veth", "br-", "virbr", "zt", "podman",
)


def lan_ip() -> str | None:
    """局域网入口 IP: 优先非隧道接口的全局 IPv4; 全是隧道/虚拟接口时退回默认路由口径."""
    addr = run(["ip", "-o", "-4", "addr", "show", "scope", "global"])
    for line in addr.stdout.splitlines():
        match = re.match(r"\d+: (\S+)\s+inet (\d+\.\d+\.\d+\.\d+)/", line)
        if match and not match.group(1).startswith(TUNNEL_INTERFACE_PREFIXES):
            return match.group(2)
    result = run(["ip", "-o", "-4", "route", "get", "1.1.1.1"])
    match = re.search(r"src (\d+\.\d+\.\d+\.\d+)", result.stdout)
    return match.group(1) if match else None


def confirmed_lan_address_path(records_root: Path) -> Path:
    """已确认局域网地址持久文件 (D010/UD-03): host 级, 放 records_root 根级."""
    return records_root / "lan-address"


def read_confirmed_lan_address(records_root: Path) -> str | None:
    """读取已确认局域网地址; 无持久文件或内容为空返回 None (无值, 不猜测)."""
    path = confirmed_lan_address_path(records_root)
    if not path.is_file():
        return None
    value = path.read_text(encoding="utf-8").strip()
    return value or None


def write_confirmed_lan_address(records_root: Path, address: str) -> None:
    """写入已确认局域网地址 (纯文本一行), 原子写 (与 atomic_write_json 共用骨架)."""
    atomic_write_text(confirmed_lan_address_path(records_root), address + "\n")


def require_valid_lan_ip(address: str) -> str:
    """--lan-ip 格式门禁 (仿 --hostname RFC1123 校验先例): 非法 IPv4 → PreconditionError."""
    try:
        ipaddress.IPv4Address(address)
    except ipaddress.AddressValueError:
        raise PreconditionError(f"--lan-ip 非法 (须为 IPv4 地址): {address}")
    return address


def lan_address_decision(
    records_root: Path,
    identity: str,
    fingerprint: dict[str, Any],
    lan_ip_arg: str | None,
    stale: bool,
) -> tuple[str, str, list[str]] | None:
    """D010/UD-03: 无已确认地址且未给 --lan-ip → lan-address 待决 (DECIDE + exit 1).
    走 decision_pending 收据闭环 (与其他 kind 同款): 指纹失配废票重问, 匹配即消费.
    已确认值优先 (持久文件或本次 flag 均视为已答); lan_ip() 现算值仅作候选提示
    (明确标注未确认, F006: 猜测不冒充可达), 不落确认值, 不作交付用址."""
    answered = bool(lan_ip_arg) or read_confirmed_lan_address(records_root) is not None
    if answered:
        return decision_pending(
            records_root, identity, "lan-address", fingerprint, True,
            "", "网络/配置状态已变化, 请重新确认宿主局域网地址",
            ["--lan-ip <addr>"], stale)
    candidate = lan_ip()
    hint = f"; 候选: {candidate} (候选, 未确认)" if candidate else ""
    return decision_pending(
        records_root, identity, "lan-address", fingerprint, False,
        f"请确认宿主局域网地址 (交付局域网 URL 用址){hint}",
        "网络/配置状态已变化, 请重新确认宿主局域网地址",
        ["--lan-ip <addr>"], stale)


def create_mother_worktree(repo: Path, branch: str, base: str | None = None) -> Path:
    directory = mother_path(repo, branch)
    directory.parent.mkdir(parents=True, exist_ok=True)
    if ref_tip(repo, branch):
        # 分支 ref 已存在 (上次终结后留存): 直接检出, 不再 -b 新建
        command = ["git", "-C", str(repo), "worktree", "add", str(directory), branch]
    else:
        command = ["git", "-C", str(repo), "worktree", "add", "-b", branch,
                   str(directory), base or default_branch(repo)]
    result = run(command)
    if result.returncode != 0:
        raise PreconditionError(f"创建母体失败: {result.stderr.strip()}")
    return directory




def live_repo_containers(repo: Path) -> list[dict[str, Any]]:
    try:
        return podman_json([
            "podman", "ps", "--filter", f"label=sandbox-worktree.repo={repo}",
            "--format", "json",
        ])
    except SwtEnvError:
        return []


def podman_row_name(row: dict[str, Any]) -> str:
    """podman ps 行的容器名: Names 列表取首项, 单名字符串剥前导 '/'; 无名返回 ''."""
    names = row.get("Names") or row.get("Name") or []
    if isinstance(names, list):
        return names[0] if names else ""
    return str(names).lstrip("/")


def birth_active_container_conflict(
    runtime: dict[str, Any] | None,
    live_rows: list[dict[str, Any]],
    branch: str,
    new_name: str,
) -> str | None:
    """D003: 同母体已有活跃容器 → 返回拒绝原因 (含旧容器名与 terminate 指引), 否则 None.
    活跃语义 = is_active_container (记录未 retired); 同名重入 (失败重试) 不算冲突;
    别的母体容器不影响本检查. 不追溯处置既有容器 (D009), 只拒绝本次新建.
    覆盖范围 (UD-12): live 兜底只认运行中容器 (live_repo_containers 走 `podman ps`,
    无 -a), 同为仓级 label 过滤; "停止但未终结仍算活跃" 的拒绝
    由 runtime 记录保证 (记录不看运行态, 未 retired 即活跃), 不依赖 live 行."""
    records = runtime.get("containers", []) if isinstance(runtime, dict) else []
    if not isinstance(records, list):
        records = []
    retired_names = {
        str(record.get("name")) for record in records
        if isinstance(record, dict) and record.get("retired") and record.get("name")
    }
    active: set[str] = set()
    for record in records:
        if is_active_container(record) and record.get("name"):
            active.add(str(record["name"]))
    for row in live_rows:
        if not isinstance(row, dict):
            continue
        labels = row.get("Labels") if isinstance(row.get("Labels"), dict) else {}
        row_branch = labels.get("sandbox-worktree.mother") or labels.get("sandbox-worktree.branch")
        if row_branch != branch:
            continue
        name = podman_row_name(row)
        if name and str(name) not in retired_names:
            active.add(str(name))
    active.discard(new_name)
    if not active:
        return None
    old = sorted(active)[0]
    return (
        f"母体 {branch} 已有活跃容器 {old} (一母体同一时刻只允许一个活跃容器); "
        f"请先 terminate --name {old} 再重新 birth"
    )


def find_mother(repo: Path, branch: str) -> tuple[Path | None, bool]:
    target = mother_path(repo, branch)
    for entry in worktree_entries(repo):
        if entry.get("branch") == branch:
            directory = Path(entry["dir"]).resolve()
            dirty = False
            if directory.is_dir():
                status_result = run([
                    "git", "-C", str(directory), "status", "--porcelain", "--untracked-files=all",
                ])
                dirty = status_result.returncode == 0 and bool(status_result.stdout)
            return directory, dirty
    return (target if target.exists() else None), False


def daemon_pids_for_serve_path(serve_path: Path) -> list[int]:
    """按服务目录匹配 daemon (并行母体: 一 daemon 服务一个母体目录).
    先按 base-path 缩小, 再核对命令行末位服务路径, 防误伤同父目录其他母体/他仓 daemon
    (旧实现只匹 base-path, 同父目录下其他对甚至其他项目的 daemon 都会被误杀)."""
    base_path = serve_path.parent.resolve()
    pattern = rf"git[ -]daemon.*--base-path={re.escape(str(base_path))}"
    result = run(["pgrep", "-af", pattern])
    if result.returncode not in (0, 1):
        return []
    pids: list[int] = []
    target = str(serve_path.resolve())
    for line in result.stdout.splitlines():
        fields = line.strip().split(None, 1)
        if not fields or not fields[0].isdigit():
            continue
        pid = int(fields[0])
        command = fields[1] if len(fields) > 1 else ""
        if pid == os.getpid() or "pgrep" in command:
            continue
        serve = command.strip().rsplit(None, 1)[-1].strip("'\"") if command.strip() else ""
        try:
            resolved = str(Path(serve).expanduser().resolve())
        except OSError:
            continue
        if resolved == target:
            pids.append(pid)
    return pids


def process_alive(pid: object) -> bool:
    if not isinstance(pid, int):
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class DaemonHandle(NamedTuple):
    process: subprocess.Popen[str]
    address: str
    port: int
    base_path: Path


class NetworkPlan(NamedTuple):
    mode: str
    allow: tuple[str, ...]
    deny: tuple[str, ...]
    gateway: str
    container_ip: str
    netns: str | None = None
    route_gateway: str | None = None


def reserve_port(address: str) -> tuple[socket.socket, int]:
    reservation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    reservation.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    reservation.bind((address, 0))
    return reservation, reservation.getsockname()[1]


def start_daemon(mother: Path) -> DaemonHandle:
    """per-mother daemon: 服务目录 = 母体工作树 (对级 hideRefs 随 config.worktree 生效),
    base-path 仍 = 主仓父目录 (容器请求路径 = 母体目录名). 只听宿主回环 (P0-1)."""
    base_path = mother.parent.resolve()
    last_error = ""
    for _ in range(5):
        try:
            reservation, port = reserve_port("127.0.0.1")
        except OSError as exc:
            last_error = str(exc)
            continue
        # 允许目录只给母体工作树本身: 兄弟仓库由 daemon 原生拒绝 (行为已实测),
        # export-ok 标记 (无 --export-all) 是第二道闸, 落母体私有 git 目录.
        command = [
            "git", "daemon", "--enable=receive-pack", f"--base-path={base_path}",
            "--listen=127.0.0.1", f"--port={port}", "--reuseaddr",
            "--log-destination=none", str(mother.resolve()),
        ]
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except OSError as exc:
            reservation.close()
            last_error = str(exc)
            continue
        reservation.close()
        time.sleep(0.15)
        if process.poll() is not None:
            last_error = process.stderr.read().strip() if process.stderr else "daemon exited"
            continue
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return DaemonHandle(process, "127.0.0.1", port, base_path)
        except OSError as exc:
            last_error = str(exc)
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
    raise SwtError(3, "PARTIAL", f"daemon 启动失败: {last_error}; 请释放端口后重跑 birth")


def git_bridge_dir(records_root: Path, identity: str) -> Path:
    return records_root / "runtime" / identity / "git-bridge"


def git_bridge_socket_path(records_root: Path, identity: str) -> Path:
    return git_bridge_dir(records_root, identity) / GIT_BRIDGE_SOCK


def git_bridge_pids(socket_path: Path) -> list[int]:
    """按 socket 路径找 host 侧桥进程 (含 runtime 未记录的孤儿)."""
    result = run(["pgrep", "-af", rf"socat.*UNIX-LISTEN:{re.escape(str(socket_path))}"])
    if result.returncode not in (0, 1):
        return []
    pids: list[int] = []
    for line in result.stdout.splitlines():
        fields = line.strip().split(None, 1)
        if fields and fields[0].isdigit() and int(fields[0]) != os.getpid():
            pids.append(int(fields[0]))
    return pids


def start_git_bridge(records_root: Path, identity: str, daemon_port: int) -> dict[str, Any]:
    """host 侧桥 (P0-1): socat 把 unix socket (容器挂载目录内) 桥到 daemon 回环端口.
    重入幂等: 同路径旧桥 (含孤儿) 先收, socket 文件重建."""
    require_command("socat")
    directory = git_bridge_dir(records_root, identity)
    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    socket_path = git_bridge_socket_path(records_root, identity)
    for pid in git_bridge_pids(socket_path):
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
    socket_path.unlink(missing_ok=True)
    process = subprocess.Popen(
        [
            "socat",
            f"UNIX-LISTEN:{socket_path},fork,mode=600",
            f"TCP:127.0.0.1:{daemon_port}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if process.poll() is not None:
            detail = process.stderr.read().strip() if process.stderr else "socat exited"
            raise SwtError(3, "PARTIAL", f"git 桥 socat 启动失败: {detail}")
        if socket_path.exists():
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
                    probe.connect(str(socket_path))
                return {"pid": process.pid, "socket": str(socket_path), "daemon-port": daemon_port}
            except OSError:
                pass
        time.sleep(0.05)
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)
    raise SwtError(3, "PARTIAL", "git 桥 socat 启动超时 (socket 未就绪)")


def stop_git_bridge(runtime: dict[str, Any] | None, records_root: Path, identity: str) -> list[int]:
    """收 host 侧桥: 记录 pid + 同路径孤儿一并收, socket 文件删除. 幂等."""
    pids: set[int] = set()
    daemon = runtime.get("daemon") if isinstance(runtime, dict) else None
    bridge = daemon.get("bridge") if isinstance(daemon, dict) else None
    if isinstance(bridge, dict) and isinstance(bridge.get("pid"), int):
        pids.add(bridge["pid"])
    socket_path = git_bridge_socket_path(records_root, identity)
    pids.update(git_bridge_pids(socket_path))
    killed: list[int] = []
    for pid in sorted(pids):
        if pid == os.getpid() or not process_alive(pid):
            continue
        killed.append(pid)
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and any(process_alive(pid) for pid in pids):
        time.sleep(0.05)
    for pid in sorted(pids):
        if process_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    socket_path.unlink(missing_ok=True)
    return killed


def ensure_git_bridge(records_root: Path, identity: str, runtime: dict[str, Any]) -> dict[str, Any]:
    """daemon 记录在位时保证桥存活 (birth 各重入分支共用); 死了就地重建."""
    daemon_record = runtime.get("daemon")
    if not isinstance(daemon_record, dict) or not isinstance(daemon_record.get("port"), int):
        raise SwtError(3, "PARTIAL", "daemon runtime 记录缺失, 无法建 git 桥")
    bridge = daemon_record.get("bridge")
    socket_value = bridge.get("socket") if isinstance(bridge, dict) else None
    if (
        isinstance(bridge, dict)
        and process_alive(bridge.get("pid"))
        and isinstance(socket_value, str)
        and Path(socket_value).exists()
    ):
        return bridge
    bridge = start_git_bridge(records_root, identity, int(daemon_record["port"]))
    daemon_record["bridge"] = bridge
    return bridge


def stop_daemon_pids(pids: set[int]) -> None:
    """收指定 daemon 进程: SIGTERM → 2s 宽限 → SIGKILL. 幂等."""
    for pid in sorted(pids):
        if pid == os.getpid() or not process_alive(pid):
            continue
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and any(process_alive(pid) for pid in pids):
        time.sleep(0.05)
    for pid in sorted(pids):
        if process_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def place_daemon_export_ok(mother: Path) -> None:
    """git-daemon-export-ok 落工作树私有 git 目录 (rev-parse 推导, 禁拼
    <主仓>/.git/worktrees/<名>: worktree gitdir 名与目录名不保证一致).
    放工作树目录本身无效 (实测报 access denied or repository not exported)."""
    result = run(["git", "-C", str(mother), "rev-parse", "--git-dir"])
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"解析母体私有 git 目录失败: {result.stderr.strip()}")
    gitdir = Path(result.stdout.strip())
    if not gitdir.is_absolute():
        gitdir = (mother / gitdir).resolve()
    (gitdir / "git-daemon-export-ok").touch()


def legacy_pair_branches(repo: Path) -> list[str]:
    """旧形态放行分支: 主仓 config hideRefs 里的 !refs/heads/<分支> 例外."""
    branches: list[str] = []
    for key in PAIR_CONFIG_KEYS:
        for value in git_values(repo, key):
            if value.startswith("!refs/heads/"):
                branch = value.removeprefix("!refs/heads/")
                if branch not in branches:
                    branches.append(branch)
    return branches


def pair_is_legacy_form(repo: Path, mother: Path | None, branch: str | None) -> bool:
    """旧形态判定: 主仓 config hideRefs 有本对分支例外, 而本对 config.worktree 为空."""
    if branch is None:
        return False
    if branch not in legacy_pair_branches(repo):
        return False
    if mother is not None and any(worktree_config_values(mother, key) for key in PAIR_CONFIG_KEYS):
        return False
    return True


def enable_worktree_config(repo: Path) -> None:
    result = run(["git", "-C", str(repo), "config", "extensions.worktreeConfig", "true"])
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"开启 extensions.worktreeConfig 失败: {result.stderr.strip()}")


def fixed_git_remote(mother: Path) -> str:
    """容器内恒定 remote (P0-1): 走容器内转发器, 与 daemon 端口/宿主网络脱钩;
    路径段 = 母体目录名 (per-mother daemon 服务母体目录)."""
    return f"git://127.0.0.1:{GIT_CONTAINER_PORT}/{mother.name}"


def container_git_forward_up(name: str) -> bool:
    """容器内转发器是否在监听: 直接读 /proc/net/tcp{,6} (与 swt-vnc 同法, 无额外依赖)."""
    hex_port = f"{GIT_CONTAINER_PORT:04X}"
    result = run([
        "podman", "exec", name, "sh", "-c",
        f"grep -qiE ':{hex_port}[[:space:]]+[0-9A-F]+:[0-9A-F]+[[:space:]]+0A[[:space:]]'"
        " /proc/net/tcp /proc/net/tcp6 2>/dev/null",
    ])
    return result.returncode == 0


def ensure_container_git_forward(name: str) -> None:
    """容器内 socat 转发器 (P0-1): 127.0.0.1:9418 -> 桥 socket. 幂等;
    容器 stop/start 后进程消失, birth/resume 都必须重保. 以 root 跑:
    rootless 下桥 socket (host bolo 属主) 在容器内呈现为 root 属主."""
    if container_git_forward_up(name):
        return
    result = run([
        "podman", "exec", "-d", name, "socat",
        f"TCP-LISTEN:{GIT_CONTAINER_PORT},bind=127.0.0.1,fork,reuseaddr",
        f"UNIX-CONNECT:{GIT_BRIDGE_CONTAINER_DIR}/{GIT_BRIDGE_SOCK}",
    ])
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器 git 转发器启动失败: {result.stderr.strip()}")
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if container_git_forward_up(name):
            return
        time.sleep(0.1)
    raise SwtError(3, "PARTIAL", "容器 git 转发器未进入监听 (socat 缺失? 镜像须含 socat)")


def stage_agent_prompts(records_root: Path, identity: str, container_name: str) -> Path:
    """P1-6: birth 时把母本拷到 runtime/<identity>/agent-prompts/<容器>/ 留档,
    返回挂载源目录. 每容器一份: 母本更新只对新 birth 的容器生效, 不动运行中容器."""
    if not AGENT_PROMPT_SOURCE_DIR.is_dir():
        raise SwtEnvError(f"agent 提示词母本目录缺失: {AGENT_PROMPT_SOURCE_DIR}")
    target_dir = records_root / "runtime" / identity / "agent-prompts" / container_name
    target_dir.mkdir(parents=True, exist_ok=True)
    for name, _target in AGENT_PROMPT_MOUNTS:
        source = AGENT_PROMPT_SOURCE_DIR / name
        if not source.is_file():
            raise SwtEnvError(f"agent 提示词母本缺失: {source}")
        staged = target_dir / name
        if not staged.is_file() or staged.read_bytes() != source.read_bytes():
            staged.write_bytes(source.read_bytes())
    return target_dir


def resolve_container_chromium_path(image_ref: str) -> str | None:
    """M08 F006/UD-06: throwaway 容器解析 playwright chromium 精确字面路径.
    解析失败 (非零退出/空输出) → stderr 告警 + None, birth 不因此失败
    (该容器仍可终端工作 + noVNC, 仅无直飞)."""
    result = run([
        "podman", "run", "--rm", "--entrypoint", "/bin/sh", image_ref,
        "-c", CHROMIUM_RESOLVE_PIPELINE,
    ])
    path = result.stdout.strip()
    if result.returncode != 0 or not path:
        print(
            f"[SWT] chromium 路径解析失败, 跳过窗口直飞脚本与挂载: {result.stderr.strip() or '空输出'}",
            file=sys.stderr,
        )
        return None
    return path


def stage_headed_browser_script(records_root: Path, identity: str, chromium_path: str) -> Path:
    """M08 D003: 母本 + chromium 精确路径 → 实例脚本落 runtime/<identity>/
    留档 (0755), 返回实例路径. 每容器一份: 母本更新只对新 birth 的容器生效."""
    if not HEADED_BROWSER_MASTER.is_file():
        raise SwtEnvError(f"headed 浏览器启动脚本母本缺失: {HEADED_BROWSER_MASTER}")
    master = HEADED_BROWSER_MASTER.read_text(encoding="utf-8")
    if CHROMIUM_PATH_PLACEHOLDER not in master:
        raise SwtEnvError(f"母本缺占位符 {CHROMIUM_PATH_PLACEHOLDER}: {HEADED_BROWSER_MASTER}")
    target_dir = records_root / "runtime" / identity
    target_dir.mkdir(parents=True, exist_ok=True)
    instance = target_dir / HEADED_BROWSER_MASTER.name
    instance.write_text(master.replace(CHROMIUM_PATH_PLACEHOLDER, chromium_path), encoding="utf-8")
    instance.chmod(0o755)
    return instance


def inspect_container(name: str) -> dict[str, Any]:
    rows = podman_json(["podman", "inspect", name])
    if not rows:
        raise SwtError(3, "PARTIAL", f"容器 {name} 创建后无法 inspect")
    return rows[0]


def container_ip(detail: dict[str, Any]) -> str:
    networks = detail.get("NetworkSettings", {}).get("Networks", {})
    if isinstance(networks, dict):
        for network in networks.values():
            if isinstance(network, dict) and network.get("IPAddress"):
                return str(network["IPAddress"])
    sandbox = detail.get("NetworkSettings", {}).get("SandboxKey")
    if isinstance(sandbox, str) and sandbox:
        result = run(["podman", "unshare", "nsenter", f"--net={sandbox}", "ip", "-o", "-4", "addr", "show"])
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                fields = line.split()
                if len(fields) >= 4 and fields[1] != "lo":
                    return fields[3].split("/", 1)[0]
    value = detail.get("NetworkSettings", {}).get("IPAddress")
    if value:
        return str(value)
    raise SwtError(3, "PARTIAL", "容器已启动但没有可用 IP, 请人工检查后重跑")


def container_netns(detail: dict[str, Any]) -> str | None:
    value = detail.get("NetworkSettings", {}).get("SandboxKey")
    return value if isinstance(value, str) and value else None


def container_gateway(name: str) -> str:
    """容器视角的宿主网关 (pasta 映射地址, DNS 走它); 与 daemon 无关 (P0-1 后 daemon 只听回环)."""
    result = run(["podman", "exec", name, "getent", "hosts", "host.containers.internal"])
    if result.returncode == 0:
        match = re.search(r"(?m)^([0-9.]+)\s+", result.stdout)
        if match:
            return match.group(1)
    return "169.254.1.2"


def pasta_network_mismatch(detail: dict[str, Any]) -> str | None:
    """P1-2: pasta --config-net 复制的是容器创建时的宿主接口名/地址; 宿主换网络后
    两者失配 (例: 容器 tun0 192.168.216.x, 宿主现 wlp1s0 192.168.31.x).
    返回人话描述; 无法判定或不失配返回 None."""
    sandbox = container_netns(detail)
    if not sandbox:
        return None
    inside = run(["podman", "unshare", "nsenter", f"--net={sandbox}", "ip", "-o", "-4", "addr", "show"])
    if inside.returncode != 0:
        return None
    container_ifaces: list[tuple[str, str]] = []
    for line in inside.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 4 and fields[1] != "lo":
            container_ifaces.append((fields[1], fields[3].split("/", 1)[0]))
    if not container_ifaces:
        return None
    host = run(["ip", "-o", "-4", "route", "get", "1.1.1.1"])
    match = re.search(r"dev (\S+).*?src (\d+\.\d+\.\d+\.\d+)", host.stdout)
    if not match:
        return None
    host_dev, host_src = match.groups()
    for name, address in container_ifaces:
        if name == host_dev and address == host_src:
            return None
    inner = ", ".join(f"{iface} {address}" for iface, address in container_ifaces)
    return f"容器网卡仍为 {inner}, 宿主当前为 {host_dev} {host_src}"


def pasta_netns(detail: dict[str, Any] | None = None) -> str | None:
    """返回目标容器的 SandboxKey, 仅保留安全的单实例兼容兜底.

    生产调用必须传入 podman inspect 结果. 未传目标时, 只有全机唯一 pasta
    实例才允许使用其 netns, 多实例时宁可失败也不猜别的容器.
    """
    if detail is not None:
        return container_netns(detail)
    try:
        result = run(["pgrep", "-af", "pasta --config-net"])
    except SwtEnvError:
        return None
    if result.returncode != 0:
        return None
    paths = [
        match.group(1)
        for line in result.stdout.splitlines()
        if (match := re.search(r"--netns\s+(\S+)", line))
    ]
    if len(paths) <= 1:
        return paths[0] if paths else None
    unique_paths = sorted(set(paths))
    raise SwtError(
        3,
        "PARTIAL",
        f"发现多个 pasta 实例, 无法安全猜测目标: {', '.join(unique_paths)}; 请改用 podman inspect 的 SandboxKey",
    )


def live_container_netns(name: str) -> str | None:
    """只从指定存活容器的 inspect 结果取得当前 SandboxKey."""
    result = run(["podman", "inspect", name])
    if result.returncode != 0:
        return None
    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return None
    detail = rows[0]
    state = detail.get("State") if isinstance(detail.get("State"), dict) else {}
    if state.get("Status") != "running":
        return None
    return pasta_netns(detail)


def container_route_gateway(detail: dict[str, Any]) -> str | None:
    sandbox = container_netns(detail)
    if not sandbox:
        return None
    result = run(["podman", "unshare", "nsenter", f"--net={sandbox}", "ip", "route"])
    if result.returncode != 0:
        return None
    match = re.search(r"(?m)^default via ([0-9.]+)", result.stdout)
    return match.group(1) if match else None


def _directed_port_query(name: str, container_port: str) -> tuple[subprocess.CompletedProcess, int | None]:
    """定向 `podman port <名> <容器端口>` 查询 + 行尾端口解析.

    定向查询输出无 '->' (形如 0.0.0.0:49155, 注意不能套全量输出的箭头解析),
    逐行取行尾端口号, 首个可解析行即结果; 查询失败或全无可解析行时端口为 None."""
    result = run(["podman", "port", name, container_port])
    if result.returncode != 0:
        return result, None
    for line in result.stdout.splitlines():
        _host_ip, _, host_port = line.strip().rpartition(":")
        if host_port.isdigit():
            return result, int(host_port)
    return result, None


def container_ssh_port(name: str) -> int:
    result, port = _directed_port_query(name, "22")
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"podman port 失败: {result.stderr.strip()}")
    if port is None:
        raise SwtError(3, "PARTIAL", f"podman port 没有返回 22 端口: {result.stdout.strip()!r}")
    return port


def parse_podman_ports(stdout: str) -> dict[str, int]:
    """podman port 全量输出 -> {容器端口: 宿主端口}.

    同一容器端口多表项时优先 0.0.0.0/[::]; 回环发布 (127.0.0.1) 落
    fallback. 多映射容器 (22 + 6080) 不能再用 '取末行' 旧法.
    """
    preferred: dict[str, int] = {}
    fallback: dict[str, int] = {}
    for line in stdout.splitlines():
        if "->" not in line:
            continue
        container_side, _, host_side = (part.strip() for part in line.partition("->"))
        container_port = container_side.split("/")[0]
        _host_ip, _, host_port = host_side.rpartition(":")
        if not host_port.isdigit():
            continue
        if _host_ip in ("0.0.0.0", "[::]"):
            preferred.setdefault(container_port, int(host_port))
        else:
            fallback.setdefault(container_port, int(host_port))
    return {**fallback, **preferred}


def container_vnc_port(name: str) -> int | None:
    """容器 6080 (noVNC) 的宿主映射端口; 无映射返回 None (缺省镜像无显示栈也允许)."""
    _result, port = _directed_port_query(name, "6080")
    return port


def container_web_port(name: str) -> int | None:
    """容器 8800 (web) 的宿主映射端口; 无映射返回 None (D009 前旧容器无 8800 发布)."""
    _result, port = _directed_port_query(name, "8800")
    return port


DISPLAY_SCRIPT = Path(__file__).with_name("swt-display.py")
SWT_VNC_PATH = "/usr/local/bin/swt-vnc"


def container_has_swt_vnc(name: str) -> bool:
    """容器镜像是否内置显示栈 (swt-vnc 可执行). 未内置 = 显示栈缺席, 跳过不判失败."""
    return run(["podman", "exec", name, "sh", "-c", f"test -x {SWT_VNC_PATH}"]).returncode == 0


def start_display_stack(name: str, geom: str | None = None) -> tuple[bool, str]:
    """podman exec swt-vnc start (幂等); 返回 (成功, 输出摘要)."""
    command = ["podman", "exec"]
    if geom:
        command.extend(["-e", f"GEOM={geom}"])
    command.extend([name, "swt-vnc", "start"])
    result = run(command, timeout=120)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def display_stack_status(name: str) -> tuple[bool, str]:
    """swt-vnc status 级秒级检查 (三进程 + 5900/6080 端口)."""
    result = run(["podman", "exec", name, "swt-vnc", "status"], timeout=60)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


WAYLAND_CONTAINER_DIR = "/run/swt-wayland"  # 宿主机 wayland socket 直挂目录 (D051)


def host_wayland_socket() -> Path | None:
    """宿主机 wayland socket 路径 (D051 本机直通); 缺席返回 None."""
    xdg = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    display = os.environ.get("WAYLAND_DISPLAY") or "wayland-0"
    candidate = Path(xdg) / display
    try:
        return candidate if candidate.is_socket() else None
    except OSError:
        return None


def relax_host_wayland_perms(socket_path: Path) -> None:
    """chmod 0777 宿主机 wayland socket (D051 权限解法): rootless uid_map 下直挂
    socket 在容器内属主映射为 root, 0755 属主权下 bolo 连不上; 777 后 bolo 可连.
    宿主暴露面 ≈ 零: 父目录 /run/user/<uid> 是 0700, 其他用户够不着路径; 本机
    同账户进程本来就以 bolo 身份可连. 登录会话重启会重置权限, 故 birth/resume
    都重保. 失败只警不阻 (回退 noVNC 由后续 probe 判定)."""
    try:
        os.chmod(socket_path, 0o777)
    except OSError as exc:
        print(f"[SWT] chmod 0777 {socket_path} 失败: {exc}; 本机直通可能降级", file=sys.stderr)


def host_display_probe(name: str) -> tuple[bool, str]:
    """wayland 直通实测 (D051): 以 bolo 身份 unix connect 直挂 socket, 验证整条
    权限链; python3 缺席 (极简镜像) 时回退 test -S 存在性检查."""
    script = (
        "import socket; s = socket.socket(socket.AF_UNIX); s.settimeout(3); "
        f"s.connect('{WAYLAND_CONTAINER_DIR}/wayland-0'); print('connect-ok')"
    )
    result = run(["podman", "exec", "--user", "bolo", name, "python3", "-c", script], timeout=30)
    if result.returncode == 0:
        return True, result.stdout.strip()
    fallback = run([
        "podman", "exec", "--user", "bolo", name, "test", "-S",
        f"{WAYLAND_CONTAINER_DIR}/wayland-0",
    ], timeout=30)
    if fallback.returncode == 0:
        return True, "socket 存在 (python3 缺席, 未做 connect 实测)"
    return False, (result.stderr or result.stdout).strip()[-160:]


def ensure_host_display(runtime: dict[str, Any], runtime_file: Path, record: dict[str, Any]) -> str:
    """birth/resume 共用的本机直通重保 + 实测 (D051). 失败降级回退 noVNC, 不阻断
    终端工作. 返回 ok / degraded / absent."""
    if record.get("host-display") != "mounted":
        return "absent"
    name = str(record.get("name"))
    socket_path = host_wayland_socket()
    if socket_path is not None:
        relax_host_wayland_perms(socket_path)
    ok, detail = host_display_probe(name)
    record["host-display"] = "ok" if ok else "degraded"
    upsert_container_record(runtime, record, runtime_file)
    if not ok:
        print(f"[SWT] 本机直通降级 (wayland 实测未过: {detail}); 回退 noVNC, 终端工作不受影响", file=sys.stderr)
    return str(record["host-display"])


def run_display_verify(name: str, evidence_dir: Path) -> tuple[bool, str]:
    """全量通道检查 (HTTP/ws/RFB/空白基线/渲染基线 0.2/headless 回切), 独立模块."""
    result = run(
        ["uv", "run", "python", str(DISPLAY_SCRIPT), "verify",
         "--name", name, "--evidence-dir", str(evidence_dir)],
        timeout=900,
    )
    return result.returncode == 0, ((result.stdout or "") + (result.stderr or "")).strip()


def host_port_free(port: int) -> bool:
    """宿主回环端口是否可绑 (pasta 发布端口占用检测, 多容器回落动态用)."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        probe.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        probe.close()


def ensure_agent_prompt_parents(container_name: str) -> None:
    """M14 发现 2: 母本单文件挂载的目标父目录若镜像内不存在, podman 会为挂载
    自动建成 root 属主 755, 容器 bolo 在其中无写权限 (kimi ~/.kimi-code 起步即
    EACCES). 启动后逐个保证父目录存在且 bolo 属主 — 与 D046 注入同模式,
    install -d 对已存在目录也会应用属主, 幂等."""
    parents = sorted({target.rsplit("/", 1)[0] for _master, target in AGENT_PROMPT_MOUNTS})
    script = " && ".join(f"install -d -o bolo -g bolo {shlex.quote(parent)}" for parent in parents)
    result = subprocess.run(
        ["podman", "exec", container_name, "sh", "-c", script],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"母本挂载父目录属主修正失败: {result.stderr.strip()}")


def inject_auth_json(container_name: str) -> None:
    """auth.json 启动后注入 (D046, 替代 D044 只读挂载): rootless uid_map 下 host bolo
    (uid 1000) 的文件在容器内呈现为 root 属主, ro 挂载 + 0600 = 容器 bolo 永不可读
    (F014). 改经 stdin 注入 + chown bolo: 不烤镜像层, 物理上不可能写回 host,
    resume 重注顺带支持换 key; host 缺失时跳过并 stderr 警告 (语义不变)."""
    source = Path.home() / ".pi" / "agent" / "auth.json"
    if not source.is_file():
        print(f"[SWT] auth.json 不存在 ({source}), 跳过注入; 容器内 LLM 凭据需另行注入", file=sys.stderr)
        return
    result = subprocess.run([
        "podman", "exec", "-i", container_name, "sh", "-c",
        "install -d -m 755 -o bolo -g bolo /home/bolo/.pi/agent && "
        "cat > /home/bolo/.pi/agent/auth.json && "
        "chown bolo:bolo /home/bolo/.pi/agent/auth.json && "
        "chmod 600 /home/bolo/.pi/agent/auth.json",
    ], input=source.read_text(encoding="utf-8"), capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"auth.json 注入失败: {result.stderr.strip()}")


# M08 ISSUE-06 (N4): 设备→容器当前是密码登录, 取信会话自动化代执行不能每次输密码.
# 单次 podman exec -i: 公钥经 stdin 进容器, 容器内 sh 完成目录保障 + 精确行去重合并.
DEVICE_PUBKEY_CONTAINER_SCRIPT = (
    "key=$(cat); "
    "install -d -m 700 -o bolo -g bolo /home/bolo/.ssh || exit 1; "
    "touch /home/bolo/.ssh/authorized_keys || exit 1; "
    "chown bolo:bolo /home/bolo/.ssh/authorized_keys || exit 1; "
    "chmod 600 /home/bolo/.ssh/authorized_keys || exit 1; "
    'grep -qxF "$key" /home/bolo/.ssh/authorized_keys || '
    "printf '%s\\n' \"$key\" >> /home/bolo/.ssh/authorized_keys"
)


def validate_device_pubkey(pubkey_text: str) -> str:
    """设备公钥校验: 单行、非注释、至少 2 字段 (openssh 公钥 type base64 [comment])."""
    key = pubkey_text.strip()
    if not key or "\n" in key or "\r" in key or key.startswith("#") or len(key.split()) < 2:
        raise PreconditionError(
            "设备公钥非法: 须单行、非注释、至少 2 字段 (openssh 公钥格式 type base64 [comment])")
    return key


def enroll_device_pubkey(container_name: str, pubkey_text: str) -> None:
    """公钥合并进容器 bolo 的 authorized_keys (grep -qxF 逐行去重, 幂等可重跑).
    容器不在 / 容器内命令失败 → 既有错误通道明报 (操作类错误, 非 DECIDE 协议)."""
    key = validate_device_pubkey(pubkey_text)
    result = run(
        ["podman", "exec", "-i", container_name, "sh", "-c", DEVICE_PUBKEY_CONTAINER_SCRIPT],
        input=key + "\n",
    )
    if result.returncode != 0:
        raise PreconditionError(
            f"设备公钥 enroll 失败 (容器 {container_name} 不在或容器内命令出错): {result.stderr.strip()}")


def cmd_enroll_device_key(args: argparse.Namespace) -> int:
    """enroll-device-key 子命令: 读公钥 (--pubkey-file 路径 / - 或缺省 stdin),
    校验后单次 exec 合并, 打印确认与设备侧测试提示."""
    if args.pubkey_file in (None, "-"):
        pubkey_text = sys.stdin.read()
    else:
        path = Path(args.pubkey_file)
        if not path.is_file():
            raise PreconditionError(f"公钥文件不存在: {path}")
        pubkey_text = path.read_text(encoding="utf-8")
    enroll_device_pubkey(args.container, pubkey_text)
    print(f"[SWT] 设备公钥已 enroll: 容器 {args.container} 的 authorized_keys 已合并"
          " (grep -qxF 逐行去重, 幂等可重跑)")
    try:
        port = container_ssh_port(args.container)
    except SwtError:
        port = None
    if port is not None:
        print(f"[SWT] 设备侧验证: ssh -p {port} bolo@127.0.0.1 'echo ok'"
              "  (通过后设备→容器免密, 取信会话可自动化代执行, 不再每次输密码)")
    else:
        print("[SWT] 设备侧验证: ssh bolo@<容器入口> 'echo ok'  (端口见 swt status)")
    return 0


def web_delivery_lines(web_port: int | None, lan: str | None, label: str | None = None) -> list[str]:
    """web 双 URL 交付行 (D003/D007/UD-04): birth/resume/status 同源组装.
    仅当容器有 web-port 才产行; 本机 URL 照打, 局域网只用已确认值 (D010/UD-03),
    无已确认值不拼猜测地址, 显式打未附发原因 (F3, 不静默丢失)."""
    if web_port is None:
        return []
    tag = f" ({label})" if label else ""
    lines = [f"[SWT] web 入口{tag} (本机):   http://127.0.0.1:{web_port}"]
    if lan:
        lines.append(f"[SWT] web 入口{tag} (局域网): http://{lan}:{web_port}")
    else:
        lines.append(f"[SWT] web 入口{tag} (局域网) 未附发: host 局域网地址无已确认值,"
                     " 确认 (--lan-ip) 后随下次交付附发")
    return lines


def headed_delivery_lines(ssh_port: int | None, lan: str | None, headed_script: str | None) -> list[str]:
    """窗口直飞交付行 (M08 ISSUE-07, D001(a) 底层零件命令模板, UD-09 -R 远端路径
    用 $(id -u) 由设备 shell 展开): 有实例脚本 → 前提行 + waypipe 模板行;
    lan 无已确认值 → 模板行改未附发 reason (F3, 附组装模板, 不静默丢失);
    无实例脚本 (chromium 解析失败/旧容器) → 一行 reason; 无 ssh 面 → 无行."""
    if ssh_port is None:
        return []
    if headed_script:
        template = (
            f"waypipe ssh -p {ssh_port} -R /tmp/swt/pulse-b.sock:/run/user/$(id -u)/pulse/native"
            f" bolo@{{lan}} {HEADED_BROWSER_CONTAINER_PATH}"
        )
        if lan:
            return [
                f"[SWT] 窗口直飞 (设备侧执行): {template.format(lan=lan)}",
                "[SWT] 窗口直飞前提: 设备须 Linux Wayland 桌面 + waypipe 客户端"
                " (waypipe --version 检查, 缺则安装, Atomic 系走 distrobox);"
                " 设备→容器免密先跑: swt enroll-device-key <容器名>",
            ]
        return [
            f"[SWT] 窗口直飞命令未附发: host 局域网地址不可知,"
            f" 请人工确认 host-LAN-IP 后组装: {template.format(lan='<host-LAN-IP>')}",
        ]
    return [
        "[SWT] 窗口直飞未附发: 容器无实例启动脚本 (chromium 路径解析失败或旧容器),"
        " 终端与 noVNC 不受影响",
    ]


def print_status_headed_lines(containers: list[dict[str, Any]], lan: str | None) -> None:
    """status 的窗口直飞交付 (ISSUE-07): running 且有 ssh-port 的容器逐个产行
    (有实例脚本 → 模板+前提, 无 → reason, 不静默丢失); 停止容器不附 (UD-11 同语义:
    不交付不可达链接)."""
    for entry in containers:
        if entry.get("state") != "running":
            continue
        for line in headed_delivery_lines(
                entry.get("ssh-port"), lan, entry.get("headed-script")):
            print(line)


def print_status_web_lines(containers: list[dict[str, Any]], lan: str | None) -> None:
    """status 的 web 交付 (UD-04/D003): 每个带 web-port 的容器在 STATE 之外附
    双 URL 行 (与 birth/resume 同源组装, 带容器名标识); 无 web-port 的旧容器不附.
    只对 running 容器附行 (UD-11): 停止容器点击即失败, 不交付不可达链接."""
    for entry in containers:
        if entry.get("state") != "running":
            continue
        name = entry.get("name")
        for line in web_delivery_lines(entry.get("web-port"), lan,
                                       label=str(name) if name else None):
            print(line)


def print_delivery_lines(
    heading: str,
    ssh_port: int | None,
    vnc_port: int | None,
    display_status: str | None,
    key_path: Path | None,
    lan: str | None,
    host_display: str | None = None,
    web_port: int | None = None,
    headed_script: str | None = None,
) -> None:
    """固定交付项 (每次 birth/resume 交付齐发, 禁止遗漏, D039/决策 8):
    ssh 双入口 (本机/局域网, 都带端口) + noVNC URL + 局域网隧道命令
    + herdr remote 双命令 + web 双 URL (仅 web-port 容器, D003/D007)
    + 窗口直飞行 (仅实例脚本在场的容器, ISSUE-07).
    无法附发的项显式打一行原因, 不静默丢失 (F3)."""
    print(f"[SWT] {heading}")
    if ssh_port is None:
        return
    print(f"[SWT] ssh 入口 (本机):   ssh -p {ssh_port} bolo@127.0.0.1  (用户 bolo, 密码 sandbox)")
    if lan:
        print(f"[SWT] ssh 入口 (局域网): ssh -p {ssh_port} bolo@{lan}  (用户 bolo, 密码 sandbox)")
    tunnel_printed = False
    if display_status == "ok" and vnc_port:
        print(f"[SWT] noVNC (本机):      http://127.0.0.1:{vnc_port}/vnc.html?resize=scale")
        if lan:
            tunnel_target = f"-L 6080:127.0.0.1:{vnc_port}"
            print(f"[SWT] noVNC (局域网隧道): ssh -p {ssh_port} {tunnel_target} bolo@{lan}"
                  "  然后浏览器开 http://127.0.0.1:6080/vnc.html?resize=scale")
            tunnel_printed = True
        else:
            print(f"[SWT] noVNC (局域网隧道) 未附发: host 局域网地址不可知, 请人工确认"
                  f" host-LAN-IP 后组装: ssh -p {ssh_port} -L 6080:127.0.0.1:{vnc_port}"
                  " bolo@<host-LAN-IP>")
    elif display_status == "absent":
        print("[SWT] 显示栈: 该容器镜像未内置 swt-vnc, 无 noVNC 交付, 亦无隧道命令可附发")
    elif display_status in ("degraded", "fail"):
        print("[SWT] 显示栈: 降级 (检查未过, 可用 swt display-check 诊断); 终端工作不受影响,"
              " 隧道命令待显示栈恢复后随下次交付附发")
    elif display_status == "ok":
        print("[SWT] 显示栈 ok 但容器无 6080 映射, 隧道命令未附发 (异常形态, 可跑 swt display-check 诊断)")
    if host_display == "ok":
        print("[SWT] 本机直通: wayland 已接通 — 容器内 headed 窗口 (登录墙等) 将直接弹在宿主机桌面,"
              " 本机场景可不开 noVNC; 远程仍走上方隧道")
    elif host_display == "degraded":
        print("[SWT] 本机直通: 降级 (wayland 实测未过, 已回退 noVNC; 可用 swt display-check 诊断)")
    elif host_display == "absent":
        print("[SWT] 本机直通: absent (无宿主机桌面会话/纯服务器宿主常态, 显示走 noVNC)")
    for line in web_delivery_lines(web_port, lan):
        print(line)
    for line in headed_delivery_lines(ssh_port, lan, headed_script):
        print(line)
    print(f"[SWT] herdr remote (host):    herdr --remote ssh://bolo@127.0.0.1:{ssh_port}")
    if lan:
        print(f"[SWT] herdr remote (局域网): herdr --remote ssh://bolo@{lan}:{ssh_port}")
    if lan is None:
        print("[SWT] 局域网 ssh/herdr 入口未附发: host 局域网地址不可知,"
              " 请人工确认 host-LAN-IP 后组装对应命令")
    if key_path:
        print(f"[SWT] ssh 私钥: {key_path}")


def image_digest(ref: str) -> str:
    result = run(["podman", "inspect", ref, "--format", "{{.Digest}}"])
    if result.returncode != 0:
        raise PreconditionError(f"镜像不存在或不可 inspect: {ref}: {result.stderr.strip()}")
    digest = result.stdout.strip()
    if digest and digest != "<no value>":
        return digest
    result = run(["podman", "inspect", ref, "--format", "{{.Id}}"])
    if result.returncode != 0 or not result.stdout.strip():
        raise PreconditionError(f"镜像没有可用 digest: {ref}")
    return result.stdout.strip()


def prepare_image(args: argparse.Namespace, repo: Path, records_root: Path) -> dict[str, Any]:
    if args.image:
        return {"ref": args.image, "digest": image_digest(args.image), "verdict": "EXPLICIT", "newer-available": False}
    requirements = Path(args.requirements).expanduser() if args.requirements else (
        records_root / resolve_project_slug(repo) / "requirements.md"
    )
    if not requirements.is_file():
        raise PreconditionError(f"requirements 不存在: {requirements}, 请先提供 --requirements 或 --image")
    image_prep = Path(__file__).with_name("image-prep.py")
    result = run(["uv", "run", "python", str(image_prep), "match", "--repo", str(repo),
        "--requirements", str(requirements), "--records-root", str(records_root),
    ])
    if result.returncode != 0:
        raise PreconditionError(f"image-prep match 失败: {result.stderr.strip()}")
    fields: dict[str, str] = {}
    for line in result.stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            fields[key] = value
    verdict = fields.get("verdict")
    if verdict == "REUSE" and fields.get("image") and fields.get("digest"):
        return {"ref": fields["image"], "digest": fields["digest"], "verdict": verdict, "newer-available": False}
    if verdict == "BUILD-NEW":
        return {"ref": None, "digest": None, "verdict": verdict, "newer-available": False, "reason": fields.get("reason", "requirements 不匹配")}
    raise PreconditionError(f"image-prep match 输出无法识别: {result.stdout.strip()!r}")


def mark_newer_available(image: dict[str, Any], runtime: dict[str, Any] | None) -> dict[str, Any]:
    result = dict(image)
    result["newer-available"] = False
    digest = result.get("digest")
    if not digest or not runtime:
        return result
    for record in runtime.get("containers", []):
        if not isinstance(record, dict) or record.get("state") != "running":
            continue
        running_digest = record.get("image-digest")
        if isinstance(running_digest, str) and running_digest and running_digest != digest:
            result["newer-available"] = True
            break
    return result


def decision_fingerprint_base(
    repo: Path,
    branch: str | None,
    mother: Path | None,
) -> dict[str, Any]:
    return {
        "repo": str(repo.resolve()),
        "mother": {
            "branch": branch,
            "dir": str(mother) if mother else None,
            "ref-tip": ref_tip(repo, branch or "") if branch else None,
        },
        "config": config_fingerprint(repo, mother),
    }


def decision_fingerprint(repo: Path, branch: str, mother: Path | None, image: dict[str, Any]) -> dict[str, Any]:
    fingerprint = decision_fingerprint_base(repo, branch, mother)
    fingerprint["image-digest"] = image.get("digest")
    return fingerprint


def receipt_files(records_root: Path, identity: str, kind: str) -> list[Path]:
    directory = records_root / "runtime" / identity / "decisions"
    if not directory.is_dir():
        return []
    found: list[Path] = []
    for path in sorted(directory.glob("d-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("kind") == kind:
            found.append(path)
    return found


def matching_receipt(records_root: Path, identity: str, kind: str, fingerprint: dict[str, Any]) -> Path | None:
    for path in receipt_files(records_root, identity, kind):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if canonical_json(payload.get("fingerprint")) == canonical_json(fingerprint):
            return path
    return None


def expire_receipts(
    records_root: Path,
    identity: str,
    kind: str,
    fingerprint: dict[str, Any],
) -> bool:
    expired = False
    for path in receipt_files(records_root, identity, kind):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if canonical_json(payload.get("fingerprint")) != canonical_json(fingerprint):
            path.unlink(missing_ok=True)
            expired = True
    return expired


def decision_pending(
    records_root: Path,
    identity: str,
    kind: str,
    fingerprint: dict[str, Any],
    answered: bool,
    question: str,
    drift_question: str,
    options: list[str],
    stale: bool,
) -> tuple[str, str, list[str]] | None:
    if not answered:
        return kind, question, options
    if stale or (
        receipt_files(records_root, identity, kind)
        and matching_receipt(records_root, identity, kind, fingerprint) is None
    ):
        return kind, drift_question, options
    receipt = matching_receipt(records_root, identity, kind, fingerprint)
    if receipt is not None:
        consume_receipt(records_root, identity, kind, fingerprint)
    return None


def decision_line(path: Path, kind: str, question: str, options: list[str]) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return f"DECIDE {payload['id']} {kind} {question} 选项: {' '.join(options)}"


def handle_dirty_decision(
    records_root: Path,
    identity: str,
    kind: str,
    fingerprint: dict[str, Any],
    dirty: bool,
    force: bool,
    question: str,
    options: list[str],
) -> tuple[bool, str | None]:
    expire_receipts(records_root, identity, kind, fingerprint)
    receipt = matching_receipt(records_root, identity, kind, fingerprint)
    if dirty and (not force or receipt is None):
        if receipt is None:
            receipt = create_receipt(records_root, identity, kind, fingerprint, options)
        print(decision_line(receipt, kind, question, options))
        return True, None
    if not dirty:
        return False, None
    payload = json.loads(receipt.read_text(encoding="utf-8")) if receipt else {}
    decision_id = payload.get("id")
    if not isinstance(decision_id, str) or not consume_receipt(records_root, identity, kind, fingerprint):
        raise SwtError(3, "PARTIAL", f"{kind} 决策收据消费失败, 请重新执行并确认")
    return False, decision_id




def print_birth_state(
    repo: Path,
    records_root: Path,
    runtime_file: Path | None,
    runtime: dict[str, Any] | None,
    mother: dict[str, Any],
    image: dict[str, Any] | None,
    network: dict[str, Any] | None,
    progress: str,
) -> None:
    containers = runtime.get("containers", []) if runtime else []
    daemon = runtime.get("daemon") if runtime else None
    print_state(
        build_state(
            repo,
            records_root,
            runtime_file,
            runtime,
            mother=mother,
            containers=containers,
            daemon=daemon,
            image=image,
            network=network,
        ),
        progress,
    )


def container_ssh_base(key: Path, port: int) -> list[str]:
    return [
        "ssh", "-i", str(key), "-o", "BatchMode=yes", "-o", "ConnectTimeout=2",
        "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
        "-p", str(port), "bolo@127.0.0.1",
    ]


def wait_for_ssh(key: Path, port: int) -> None:
    base = [*container_ssh_base(key, port), "true"]
    last = ""
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        result = run(base, timeout=3)
        if result.returncode == 0:
            return
        last = result.stderr.strip()
        time.sleep(0.2)
    raise SwtError(3, "PARTIAL", f"SSH BatchMode 连通失败: {last}")


def ssh_command(key: Path, port: int, command: str, timeout: float = 10) -> subprocess.CompletedProcess[str]:
    return run([*container_ssh_base(key, port), command], timeout=timeout)


def update_legacy_container_remote(repo: Path, records_root: Path, branch: str, mother: Path) -> None:
    """迁移收尾: 本分支全部未退役容器的 remote 改指母体目录路径 (daemon 服务目录变了).
    容器不可达/缺凭证时只告警不阻断, 由该对的 resume 自愈收敛."""
    remote = fixed_git_remote(mother)
    for path in repo_runtime_files(records_root, repo):
        data = load_runtime_tolerant(path)
        if not data:
            continue
        changed = False
        for record in data.get("containers", []):
            if not isinstance(record, dict) or record.get("branch") != branch or record.get("retired"):
                continue
            record["remote"] = remote
            changed = True
            key_value = record.get("ssh_private_key") or record.get("ssh-private-key")
            port = record.get("ssh-port")
            clone_dir = record.get("clone_dir") or record.get("clone-dir")
            if (
                isinstance(key_value, str)
                and isinstance(port, int)
                and isinstance(clone_dir, str)
                and Path(key_value).is_file()
            ):
                result = ssh_command(
                    Path(key_value), port,
                    f"git -C {shlex.quote(clone_dir)} remote set-url origin {shlex.quote(remote)}",
                    timeout=10,
                )
                if result.returncode != 0:
                    print(
                        f"[SWT] 迁移警告: 容器 {record.get('name')} remote 更新失败 ({result.stderr.strip()});"
                        " 由该对的 resume 自愈收敛",
                        file=sys.stderr,
                    )
        if changed:
            atomic_write_json(path, data)


def migrate_legacy_pairs(repo: Path, records_root: Path, *, skip_daemon_for: Path | None = None) -> None:
    """一次性迁移 (并行母体改造, 幂等): 主仓 config 的 hideRefs 五键原样移入各对应
    母体的 config.worktree, 并把服务主仓路径的旧形态 daemon 重摆为 per-mother 形态
    (停旧 → 移配置 → 落 export-ok → 起新 → 重建桥 → 容器 remote set-url).
    主仓级无 hideRefs 时无事发生. skip_daemon_for: 该母体的 daemon 由调用方
    (resume 标准恢复流程) 统一重拉, 迁移只做配置搬家与 export-ok, 不动其 runtime.
    步序保证授权域不空窗: 先停旧 daemon (配置搬走后继续跑会全分支裸露), 再动配置."""
    branches = legacy_pair_branches(repo)
    if not branches:
        return
    enable_worktree_config(repo)
    # 1. 停掉服务主仓路径的旧形态 daemon (其他对的 per-mother daemon 不在匹配面, 不误伤)
    stop_daemon_pids(set(daemon_pids_for_serve_path(repo.resolve())))
    # 2. 五键值原样移入各对应母体 config.worktree, 再清掉主仓级
    warned: set[str] = set()
    for key in PAIR_CONFIG_KEYS:
        values = git_values(repo, key)
        if not values:
            continue
        for branch in branches:
            mother, _dirty = find_mother(repo, branch)
            if mother is None or not mother.is_dir():
                if branch not in warned:
                    warned.add(branch)
                    print(
                        f"[SWT] 迁移警告: 分支 {branch} 无母体工作树, 其主仓级放行值随迁移丢弃",
                        file=sys.stderr,
                    )
                continue
            for value in values:
                result = config_add_value(repo, mother, key, value)
                if result.returncode != 0:
                    raise SwtError(3, "PARTIAL", f"迁移写入 {mother.name} config.worktree {key} 失败: {result.stderr.strip()}")
        result = run(["git", "-C", str(repo), "config", "--unset-all", key])
        if result.returncode != 0:
            raise SwtError(3, "PARTIAL", f"清理主仓 config {key} 失败: {result.stderr.strip()}")
    # 3. 各迁走的母体: export-ok + per-mother daemon + 桥 + 容器 remote (无 daemon 残留形态)
    for branch in branches:
        mother, _dirty = find_mother(repo, branch)
        if mother is None or not mother.is_dir():
            continue
        place_daemon_export_ok(mother)
        if skip_daemon_for is not None and mother.resolve() == skip_daemon_for.resolve():
            update_legacy_container_remote(repo, records_root, branch, mother)
            continue
        daemon = start_daemon(mother)
        identity = resolve_pair_identity(repo, records_root, mother)
        runtime_file = records_root / "runtime" / f"{identity}.json"
        runtime = load_runtime_tolerant(runtime_file)
        bridge = start_git_bridge(records_root, identity, daemon.port)
        if runtime is not None:
            runtime["daemon"] = {
                "pid": daemon.process.pid, "addr": daemon.address, "port": daemon.port,
                "base-path": str(daemon.base_path), "orphan": False, "bridge": bridge,
            }
            runtime["config"] = {"swt-form": pair_config_matches(repo, mother, branch)}
            atomic_write_json(runtime_file, runtime)
        update_legacy_container_remote(repo, records_root, branch, mother)


def apply_network(plan: NetworkPlan) -> dict[str, Any]:
    script = Path(__file__).with_name("net-firewall.py")
    command = [
        "uv", "run", "python", str(script), "apply", "--mode", plan.mode,
        "--container-ip", plan.container_ip, "--gateway", plan.gateway, "--merge",
    ]
    if plan.netns:
        command.extend(["--netns", plan.netns])
    auto_allow: list[str] = []
    if plan.mode == "whitelist":
        entries = list(plan.allow)
        if plan.gateway not in entries:
            entries.append(f"{plan.gateway}/32")
            auto_allow.append(plan.gateway)
        for entry in (plan.route_gateway, plan.container_ip):
            if entry and entry not in entries:
                entries.append(f"{entry}/32")
                auto_allow.append(entry)
        for entry in entries:
            command.extend(["--allow", entry])
    else:
        for entry in plan.deny:
            command.extend(["--deny", entry])
    result = run(command, timeout=30)
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"nft apply 失败, 容器已登记但网络未就绪: {result.stderr.strip()}")
    return {
        "mode": plan.mode,
        "table-present": True,
        "auto-allow": auto_allow,
        "allow": list(plan.allow),
        "deny": list(plan.deny),
        "gateway": plan.gateway,
        "route-gateway": plan.route_gateway,
    }


def network_plan_from_record(
    network: dict[str, Any],
    record: dict[str, Any],
    netns: str,
) -> NetworkPlan | None:
    mode = network.get("mode")
    gateway = network.get("gateway")
    container_ip = record.get("network-ip")
    if mode not in {"whitelist", "blacklist"} or not isinstance(gateway, str) or not isinstance(container_ip, str):
        return None
    allow = network.get("allow")
    deny = network.get("deny")
    route_gateway = network.get("route-gateway")
    return NetworkPlan(
        mode,
        tuple(allow) if isinstance(allow, list) else (),
        tuple(deny) if isinstance(deny, list) else (),
        gateway,
        container_ip,
        netns,
        route_gateway if isinstance(route_gateway, str) else None,
    )


def apply_sibling_networks(
    network: dict[str, Any],
    records: list[dict[str, Any]],
    netnses: set[str],
) -> None:
    for netns in sorted(netnses):
        for record in records:
            plan = network_plan_from_record(network, record, netns)
            if plan is None:
                continue
            try:
                apply_network(plan)
            except SwtError as exc:
                if "NETNS-UNREACHABLE" in exc.message:
                    continue
                raise


def upsert_container_record(runtime: dict[str, Any], record: dict[str, Any], runtime_file: Path) -> None:
    records = [
        item for item in runtime.get("containers", [])
        if not isinstance(item, dict) or item.get("name") != record.get("name")
    ]
    records.append(record)
    runtime["containers"] = records
    atomic_write_json(runtime_file, runtime)


def refresh_container(
    name: str,
    record: dict[str, Any],
    runtime: dict[str, Any],
    runtime_file: Path,
) -> dict[str, Any]:
    detail = inspect_container(name)
    status = detail.get("State", {}).get("Status") if isinstance(detail.get("State"), dict) else None
    if status != "running":
        started = run(["podman", "start", name])
        if started.returncode != 0:
            raise SwtError(3, "PARTIAL", f"PARTIAL container-start {name}; 请释放占用端口后重跑 birth: {started.stderr.strip()}")
    port = container_ssh_port(name)
    vnc_port = container_vnc_port(name)
    web_port = container_web_port(name)
    detail = inspect_container(name)
    record.update({"podman-id": detail.get("Id"), "state": "running", "ssh-port": port, "vnc-port": vnc_port, "web-port": web_port})
    runtime["stage"] = "container-started"
    upsert_container_record(runtime, record, runtime_file)
    return {"name": name, "port": port, "record": record, "detail": detail}


def container_default_name(branch: str) -> str:
    """容器缺省名 swt-<分支净化>; 分支含 / 等字符时经 slug 规则净化 (podman 名不允许)."""
    result = run(["uv", "run", "python", str(SLUG_SCRIPT), branch])
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if line.startswith("slug="):
                value = line.removeprefix("slug=").strip()
                if value:
                    return f"swt-{value}"
    clean = re.sub(r"[^a-zA-Z0-9_.-]+", "-", branch).strip(".-") or "branch"
    return f"swt-{clean}"


# ISSUE-06 birth 信箱接线 (D002/D006/D009): 探测 host 基础服务 → admin 申领容器 key
# → 注入容器 env → runtime 登记. 信箱是增强不是命脉: 任一步失败只告警跳过, 不阻断 birth.
BASE_SERVER_STATE_PATH = Path.home() / ".local/state/swt-base-server/state.json"
BASE_SERVER_PORT_RANGE = range(38417, 38427)  # D002 区间, 与服务端 PORT_RANGE 一致
BASE_SERVER_SERVICE = "swt-base-server"       # D002(2) __identity__ 应答名
MAILBOX_ALLOW_TYPES = ("notify", "open_url", "exec", "request")  # 全 4 类型; exec 由服务端指令集兜底降级 (UD-03)
MAILBOX_ENV_URL = "SWT_BASE_URL"
MAILBOX_ENV_KEY = "SWT_MAILBOX_KEY"
MAILBOX_ENV_NAME = "SWT_CONTAINER_NAME"


class MailboxWireError(Exception):
    """申领容器 key 失败; wire_container_mailbox 捕获后降级为 skipped, 不阻断 birth."""


def identity_probe(port: int, timeout: float = 0.5) -> bool:
    """D002(2): 无认证 GET /__identity__, 确认目标端口是 swt 基础服务."""
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/__identity__", timeout=timeout) as response:
            payload = json.loads(response.read() or b"{}")
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict) and payload.get("service") == BASE_SERVER_SERVICE


def probe_base_server(
    state_path: Path = BASE_SERVER_STATE_PATH,
    ports=BASE_SERVER_PORT_RANGE,
) -> dict[str, Any] | None:
    """D002(3): 读 host 状态文件免扫描; 文件缺席/失活/畸形时扫区间 __identity__ 兜底.
    返回 {"port", "admin_port", "admin_token"}; 扫描命中时 admin 字段为 None
    (扫描拿不到凭证, 失活状态文件里的 admin 字段不可信弃用); 完全未发现返回 None."""
    state: Any = None
    try:
        state = json.loads(Path(state_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = None
    if isinstance(state, dict):
        port = state.get("port")
        if isinstance(port, int) and identity_probe(port):
            return {"port": port,
                    "admin_port": state.get("admin_port"),
                    "admin_token": state.get("admin_token")}
    for port in ports:
        if identity_probe(port):
            return {"port": port, "admin_port": None, "admin_token": None}
    return None


def claim_container_key(admin_port: int, admin_token: str, container: str) -> str:
    """D006: 经 admin 口 (硬绑 127.0.0.1, X-Admin-Token) 申领容器 key.
    作用域: 全 4 消息类型 + 全目标 ("*" 覆盖缺省路由). 失败抛 MailboxWireError."""
    request = urllib.request.Request(
        f"http://127.0.0.1:{admin_port}/admin/container-keys",
        data=json.dumps({"container": container,
                         "allow_types": list(MAILBOX_ALLOW_TYPES),
                         "allow_targets": ["*"]}).encode(),
        headers={"Content-Type": "application/json",
                 "X-Admin-Token": admin_token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5.0) as response:
            payload = json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read() or b"{}").get("error", "")
        except (json.JSONDecodeError, OSError):
            detail = ""
        raise MailboxWireError(f"admin 拒绝 (HTTP {exc.code}): {detail}") from exc
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        raise MailboxWireError(f"admin 口不可达/应答畸形: {exc}") from exc
    key = payload.get("key") if isinstance(payload, dict) else None
    if not isinstance(key, str) or not key:
        raise MailboxWireError(f"admin 应答缺 key: {payload!r}")
    return key


def wire_container_mailbox(
    env: dict[str, str],
    container_name: str,
    *,
    state_path: Path = BASE_SERVER_STATE_PATH,
    ports=BASE_SERVER_PORT_RANGE,
) -> dict[str, Any]:
    """ISSUE-06 birth 信箱接线: 探测 → 申领 → 注入 env, 返回待登记的 mailbox 段.
    任何一步失败: stderr 告警 + status skipped, 不阻断 birth (信箱是增强不是命脉).
    完整 key 只进 env (podman -e + ssh 面 ~/.ssh/environment 双通道既有机制),
    登记只留前 8 位前缀, 不落 runtime 明文."""
    found = probe_base_server(state_path, ports)
    if found is None:
        record: dict[str, Any] = {
            "status": "skipped", "container": container_name,
            "reason": "基础服务未发现 (状态文件缺席且区间 __identity__ 扫描无应答)",
        }
    elif not found.get("admin_port") or not found.get("admin_token"):
        record = {
            "status": "skipped", "container": container_name,
            "reason": f"基础服务在线 (:{found['port']}) 但 admin 凭证不可得, 无法申领容器 key",
        }
    else:
        try:
            key = claim_container_key(
                int(found["admin_port"]), str(found["admin_token"]), container_name)
        except MailboxWireError as exc:
            record = {"status": "skipped", "container": container_name,
                      "reason": f"申领容器 key 失败: {exc}"}
        else:
            # D002(5): 容器内地址恒 host.containers.internal + 探测端口
            base_url = f"http://host.containers.internal:{found['port']}"
            env[MAILBOX_ENV_URL] = base_url
            env[MAILBOX_ENV_KEY] = key
            env[MAILBOX_ENV_NAME] = container_name
            record = {
                "status": "connected", "container": container_name,
                "base_url": base_url, "key_prefix": key[:8],
                "allow_types": list(MAILBOX_ALLOW_TYPES), "allow_targets": ["*"],
            }
    if record["status"] == "skipped":
        print(f"[SWT] 信箱接线跳过: {record['reason']} (不影响 birth)", file=sys.stderr)
    else:
        print(f"[SWT] 信箱接线完成: {record['base_url']} (key {record['key_prefix']}...)",
              file=sys.stderr)
    return record


def assert_skills_mountable(skills_dir: Path) -> list[str]:
    """前置检查 host skill 库并返回 pyproject 项目相对路径列表 (供 .venv 匿名卷挂载).

    rootless uid 映射下容器 bolo 只能靠 other 权限位读 host 树, 任何非全局可读
    路径都会在容器内变成不可读, 提前拦下并点名.
    """
    if not skills_dir.is_dir():
        raise PreconditionError(f"host skill 库不存在: {skills_dir}")
    projects: list[str] = []
    offenders: list[str] = []
    for root, dirs, files in os.walk(skills_dir):
        rel_root = Path(root).relative_to(skills_dir)
        if not (os.stat(root).st_mode & 0o005):
            offenders.append(f"{rel_root}/ (目录需 o+rx)")
        if "pyproject.toml" in files:
            projects.append(str(rel_root))
        for name in files:
            if not (os.stat(Path(root) / name).st_mode & 0o004):
                offenders.append(f"{rel_root / name} (文件需 o+r)")
        dirs[:] = [d for d in dirs if d not in (".venv", "venv", "__pycache__", ".git")]
    if offenders:
        shown = ", ".join(offenders[:5])
        more = f" ...等共 {len(offenders)} 项" if len(offenders) > 5 else ""
        raise PreconditionError(
            f"host skill 库存在非全局可读路径: {shown}{more}; chmod o+rX 后重跑"
        )
    return projects


def container_exists(name: str) -> bool:
    """podman 是否已有同名容器 (birth 重入判定, 与 create_and_start_container 同口径)."""
    return run(["podman", "inspect", name]).returncode == 0


def create_and_start_container(args: argparse.Namespace, repo: Path, image: dict[str, Any], branch: str, runtime: dict[str, Any], runtime_file: Path, env: dict[str, str], records_root: Path, identity: str, headed_script: Path | None = None) -> dict[str, Any]:
    name = args.name or container_default_name(branch)
    existing = run(["podman", "inspect", name])
    if existing.returncode == 0:
        records = runtime.get("containers", [])
        record = next((item for item in records if isinstance(item, dict) and item.get("name") == name), None)
        if record is None:
            raise PreconditionError(f"容器名已存在: {name}, 但不属于当前 runtime")
        refreshed = refresh_container(name, record, runtime, runtime_file)
        refreshed["headed-script"] = record.get("headed-script")
        return refreshed
    labels = [
        f"sandbox-worktree.repo={repo.resolve()}", f"sandbox-worktree.mother={branch}",
        f"sandbox-worktree.name={name}", f"sandbox-worktree.branch={branch}",
    ]
    command = ["podman", "create", "--name", name]
    for label in labels:
        command.extend(["--label", label])
    # 主机名 (D047): birth 经 DECIDE 确认后必带; 不设则 podman 拿容器 ID 充数
    command.extend(["--hostname", args.hostname])
    # 环境变量继承 (创建时烘入镜像 env, ssh 面由 inject_ssh_key 写 ~/.ssh/environment)
    for env_name, env_value in env.items():
        command.extend(["-e", f"{env_name}={env_value}"])
    # 显示栈发布 (D040): 只绑宿主回环; chromium 必需 --shm-size=1g;
    # 宿主 6080 已被占 (多容器并存) 时回落同回环动态端口, URL/隧道按实际端口交付
    if host_port_free(6080):
        command.extend(["-p", "127.0.0.1:6080:6080"])
    else:
        command.extend(["-p", "127.0.0.1::6080"])
    command.extend(["--shm-size", "1g"])
    # git 桥 socket 目录 (P0-1): host 侧 socat 在此建 git.sock, 容器转发器连它
    bridge_dir = git_bridge_dir(records_root, identity)
    bridge_dir.mkdir(parents=True, exist_ok=True)
    command.extend(["-v", f"{bridge_dir}:{GIT_BRIDGE_CONTAINER_DIR}"])
    # 本机 wayland 直通 (D051): 宿主机 socket 存在即恒挂 + 放宽属主权 (容器 bolo
    # 可连), 网络白名单语义不受影响 (socket 非网络通道). env 写入 env map, ssh 面
    # 经 ~/.ssh/environment 同步.
    wayland_socket = host_wayland_socket()
    if wayland_socket is not None:
        relax_host_wayland_perms(wayland_socket)
        command.extend(["-v", f"{wayland_socket}:{WAYLAND_CONTAINER_DIR}/wayland-0"])
        command.extend(["-e", f"XDG_RUNTIME_DIR={WAYLAND_CONTAINER_DIR}", "-e", "WAYLAND_DISPLAY=wayland-0"])
        env["XDG_RUNTIME_DIR"] = WAYLAND_CONTAINER_DIR
        env["WAYLAND_DISPLAY"] = "wayland-0"
        if Path("/dev/dri").is_dir():
            command.extend(["--device", "/dev/dri"])
    # agent 提示词母本只读单文件挂载 (P1-6): 每容器留档副本, rootless 下呈现为
    # root 属主 0644, 容器 bolo 可读不可写
    prompts_dir = stage_agent_prompts(records_root, identity, name)
    for master_name, target in AGENT_PROMPT_MOUNTS:
        command.extend(["-v", f"{prompts_dir / master_name}:{target}:ro"])
    # 启动脚本母本只读单文件挂载 (M08 D003): 实例由 birth 流程解析 chromium
    # 精确路径后落 runtime/<identity>/ 留档, 此处只负责挂载 (UD-06: 解析失败时
    # birth 传 None, 容器仍可终端工作 + noVNC, 仅无直飞).
    if headed_script is not None:
        command.extend(["-v", f"{headed_script}:{HEADED_BROWSER_CONTAINER_PATH}:ro"])
    # skill 库只读挂载 (遮蔽镜像烤入副本, 实时跟随 host) + 项目 .venv 匿名卷
    # (从镜像播种, 可写): 外层 ro 先挂, 内层卷后挂, 嵌套遮蔽出可写的 .venv
    skill_projects = assert_skills_mountable(SKILLS_HOST_DIR)
    command.extend(["-v", f"{SKILLS_HOST_DIR}:{SKILLS_CONTAINER_DIR}:ro"])
    for rel_project in skill_projects:
        command.extend(["-v", f"{SKILLS_CONTAINER_DIR}/{rel_project}/.venv"])
    # web 服务端口 (D001): 与 22 同款宿主 0.0.0.0 动态分配, 直达局域网, 禁止绑回环
    command.extend(["-p", "22", "-p", "8800", str(image["ref"])])
    created = run(command)
    if created.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器 create 失败: {created.stderr.strip()}")
    detail = inspect_container(name)
    record = {
        "name": name, "branch": branch, "podman-id": detail.get("Id"), "state": "created",
        "ssh-port": None, "vnc-port": None, "web-port": None, "image-digest": image.get("digest"), "retired": False,
        "display": "pending", "dirty": {"uncommitted": None, "unpushed": None, "relation": None, "reachable": False},
        "host-display": "mounted" if wayland_socket is not None else "absent",
        "headed-script": str(headed_script) if headed_script is not None else None,
    }
    runtime["stage"] = "container-created"
    upsert_container_record(runtime, record, runtime_file)
    refreshed = refresh_container(name, record, runtime, runtime_file)
    # M08 ISSUE-07 消费: 脚本有无经返回值与 runtime 容器记录双通道传递
    # (None = 无直飞, 交付打 reason 行)
    refreshed["headed-script"] = record.get("headed-script")
    return refreshed


def inject_ssh_key(container: dict[str, Any], records_root: Path, identity: str, runtime: dict[str, Any], runtime_file: Path, env: dict[str, str]) -> Path:
    require_command("ssh-keygen")
    key_dir = records_root / "runtime" / identity / "ssh"
    key_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(key_dir, 0o700)
    key = key_dir / f"{container['name']}.ed25519"
    # 重入: 上次 PARTIAL 已生成过就直接复用 (ssh-keygen 见已存在文件会交互询问, 非交互下必死).
    if not (key.is_file() and Path(str(key) + ".pub").is_file()):
        generated = run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)])
        if generated.returncode != 0:
            raise SwtError(3, "PARTIAL", f"SSH key 生成失败: {generated.stderr.strip()}")
    os.chmod(key, 0o600)
    public = key.with_suffix(key.suffix + ".pub").read_text(encoding="utf-8")
    result = subprocess.run([
        "podman", "exec", "-i", container["name"], "sh", "-c",
        "install -d -m 700 -o bolo -g bolo /home/bolo/.ssh && "
        "install -d -m 755 -o bolo -g bolo /home/bolo/Workspace && "
        "cat > /home/bolo/.ssh/authorized_keys && "
        "chown bolo:bolo /home/bolo/.ssh/authorized_keys && "
        "chmod 600 /home/bolo/.ssh/authorized_keys",
    ], input=public, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"authorized_keys 注入失败: {result.stderr.strip()}")
    if env:
        # sshd 不给登录会话传容器 env; PermitUserEnvironment + ~/.ssh/environment 才是 ssh 面通道
        env_text = "".join(f"{k}={v}\n" for k, v in env.items())
        env_result = subprocess.run([
            "podman", "exec", "-i", container["name"], "sh", "-c",
            "cat > /home/bolo/.ssh/environment && "
            "chown bolo:bolo /home/bolo/.ssh/environment && "
            "chmod 600 /home/bolo/.ssh/environment",
        ], input=env_text, capture_output=True, text=True, check=False)
        if env_result.returncode != 0:
            raise SwtError(3, "PARTIAL", f"environment 注入失败: {env_result.stderr.strip()}")
    # 密码登录 (用户拍板): 固定密码 sandbox, 与 key 同目录 0600 留档, 随 terminate 清除
    password = "sandbox"
    pw_result = subprocess.run([
        "podman", "exec", "-i", container["name"], "sh", "-c",
        f"echo 'bolo:{password}' | chpasswd",
    ], capture_output=True, text=True, check=False)
    if pw_result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器密码设置失败: {pw_result.stderr.strip()}")
    password_file = key_dir / f"{container['name']}.password"
    password_file.write_text(password + "\n", encoding="utf-8")
    os.chmod(password_file, 0o600)
    container["record"].update({"ssh_private_key": str(key), "password_file": str(password_file), "clone_dir": f"/home/bolo/Workspace/{container['record']['branch']}"})
    upsert_container_record(runtime, container["record"], runtime_file)
    runtime["stage"] = "ssh-ready"
    atomic_write_json(runtime_file, runtime)
    return key


def assert_container_clone(container: dict[str, Any], key: Path, branch: str, remote: str) -> None:
    port = int(container["port"])
    clone_dir = f"/home/bolo/Workspace/{branch}"
    command = (
        f"rm -rf {shlex.quote(clone_dir)} && "
        f"git clone -b {shlex.quote(branch)} {shlex.quote(remote)} {shlex.quote(clone_dir)}"
    )
    result = ssh_command(key, port, command, timeout=30)
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器 clone 失败: {result.stderr.strip()}")
    current = ssh_command(key, port, f"git -C {shlex.quote(clone_dir)} branch --show-current")
    if current.returncode != 0 or current.stdout.strip() != branch:
        raise SwtError(3, "PARTIAL", f"容器检出分支错误: {current.stdout.strip()!r}")
    refs = ssh_command(key, port, f"git -C {shlex.quote(clone_dir)} ls-remote origin")
    if refs.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器 ls-remote 失败: {refs.stderr.strip()}")
    advertised = [line.split()[1] for line in refs.stdout.splitlines() if len(line.split()) >= 2 and line.split()[1] != "HEAD"]
    if advertised != [f"refs/heads/{branch}"]:
        raise SwtError(3, "PARTIAL", f"daemon 读面越权: {advertised!r}")


def birth_display_gate_reentry(
    args: argparse.Namespace,
    repo: Path,
    records_root: Path,
    runtime: dict[str, Any] | None,
    runtime_file: Path,
) -> int | None:
    """处理显示栈门禁的 DECIDE 重入; 非重入场景返回 None."""
    if not runtime or runtime.get("stage") != "born":
        return None
    display = runtime.get("display") if isinstance(runtime.get("display"), dict) else None
    if not display or display.get("status") != "fail":
        return None
    identity = runtime_file.stem
    image = runtime.get("image") if isinstance(runtime.get("image"), dict) else {}
    fingerprint = birth_display_fingerprint(repo, runtime, image, display.get("container"))
    receipt = matching_receipt(records_root, identity, "display-verify", fingerprint)
    answered = args.display_continue or args.display_recheck
    if not answered:
        # 未带答案重跑同一命令: 重问 (沿用已开票据, 无票据则新开)
        if receipt is None:
            receipt = create_receipt(
                records_root, identity, "display-verify", fingerprint,
                DISPLAY_VERIFY_OPTIONS,
            )
        print(decision_line(receipt, "display-verify", str(display.get("question", "显示栈验证未通过")), DISPLAY_VERIFY_OPTIONS))
        print_birth_state(repo, records_root, runtime_file, runtime, runtime.get("mother") or {}, image, runtime.get("network"), "[SWT] birth: 等待用户决定 (显示栈)")
        return 1
    if receipt is None:
        raise PreconditionError("没有匹配的 display-verify 决策收据, 状态已变化, 请重跑 birth 重新判定")
    consume_receipt(records_root, identity, "display-verify", fingerprint)
    name = display.get("container")
    if not isinstance(name, str):
        raise PreconditionError("display 门禁记录缺容器名, 请人工检查后重跑")
    record = next((item for item in runtime.get("containers", [])
                   if isinstance(item, dict) and item.get("name") == name), None)
    if record is None:
        raise PreconditionError(f"容器 {name} 缺少 runtime 记录")
    if args.display_continue:
        display["status"] = "degraded"
        record["display"] = "degraded"
        upsert_container_record(runtime, record, runtime_file)
        print_delivery_lines(
            "birth: 完成 (显示栈降级, 终端工作不受影响)",
            record.get("ssh-port"), record.get("vnc-port"), "degraded",
            Path(record["ssh_private_key"]) if record.get("ssh_private_key") else None,
            read_confirmed_lan_address(records_root), record.get("host-display"),
            record.get("web-port"),
            headed_script=record.get("headed-script"),
        )
        print_birth_state(repo, records_root, runtime_file, runtime, runtime.get("mother") or {}, image, runtime.get("network"), "[SWT] birth: 已完成 (显示栈降级)")
        return 0
    # --display-recheck: 重验一次
    started, start_output = start_display_stack(name)
    ok = started
    detail = start_output
    if ok:
        ok, detail = run_display_verify(name, records_root / "runtime" / identity / "display")
    if ok:
        display["status"] = "ok"
        record["display"] = "ok"
        upsert_container_record(runtime, record, runtime_file)
        print_delivery_lines(
            "birth: 完成 (显示栈重验通过)",
            record.get("ssh-port"), record.get("vnc-port"), "ok",
            Path(record["ssh_private_key"]) if record.get("ssh_private_key") else None,
            read_confirmed_lan_address(records_root), record.get("host-display"),
            record.get("web-port"),
            headed_script=record.get("headed-script"),
        )
        print_birth_state(repo, records_root, runtime_file, runtime, runtime.get("mother") or {}, image, runtime.get("network"), "[SWT] birth: 已完成 (显示栈重验通过)")
        return 0
    # 重验仍失败: 开新票据重新 DECIDE
    display["status"] = "fail"
    display["question"] = f"显示栈重验仍未通过: {detail[-200:]}"
    atomic_write_json(runtime_file, runtime)
    receipt = create_receipt(records_root, identity, "display-verify", fingerprint, DISPLAY_VERIFY_OPTIONS)
    print(decision_line(receipt, "display-verify", str(display.get("question")), DISPLAY_VERIFY_OPTIONS))
    print_birth_state(repo, records_root, runtime_file, runtime, runtime.get("mother") or {}, image, runtime.get("network"), "[SWT] birth: 等待用户决定 (显示栈重验未过)")
    return 1


DISPLAY_VERIFY_OPTIONS = [
    "--display-continue (继续, 只开终端)",
    "--display-recheck (重验一次)",
    "terminate --name <容器> (终结)",
]


def birth_display_fingerprint(
    repo: Path,
    runtime: dict[str, Any],
    image: dict[str, Any],
    container_name: object,
) -> dict[str, Any]:
    branch, mother_dir = runtime_mother(runtime)
    fingerprint = decision_fingerprint(repo, branch or "", mother_dir, image)
    record = next((item for item in runtime.get("containers", [])
                   if isinstance(item, dict) and item.get("name") == container_name), {})
    fingerprint["container"] = container_name
    fingerprint["podman-id"] = record.get("podman-id")
    return fingerprint


def birth_display_gate(
    args: argparse.Namespace,
    repo: Path,
    records_root: Path,
    identity: str,
    runtime: dict[str, Any],
    runtime_file: Path,
    container: dict[str, Any],
) -> str:
    """birth 尾部显示栈门禁 (D040/D041): 未内置 swt-vnc → absent 跳过;
    自动 swt-vnc start 后跑全量 verify. 失败开 DECIDE 票据并返回 "fail"
    (由调用方 exit 1). 返回: ok / degraded / absent / fail."""
    name = container["record"]["name"]
    record = container["record"]
    if not container_has_swt_vnc(name):
        record["display"] = "absent"
        upsert_container_record(runtime, record, runtime_file)
        print("[SWT] 显示栈: 容器镜像未内置 swt-vnc, 跳过 (absent)")
        return "absent"
    started, start_output = start_display_stack(name)
    ok = started
    detail = start_output
    if ok:
        ok, detail = run_display_verify(name, records_root / "runtime" / identity / "display")
    if ok:
        record["display"] = "ok"
        upsert_container_record(runtime, record, runtime_file)
        return "ok"
    # 失败 → DECIDE (决策 3; 执行完成后的追加 DECIDE, D026 一次列全的例外)
    question = (
        f"显示栈验证未通过 ({detail[-200:] or 'start 失败'}); "
        "可继续只开终端, 重验一次, 或终结容器"
    )
    runtime["display"] = {"status": "fail", "container": name, "question": question}
    record["display"] = "fail"
    upsert_container_record(runtime, record, runtime_file)
    image = runtime.get("image") if isinstance(runtime.get("image"), dict) else {}
    fingerprint = birth_display_fingerprint(repo, runtime, image, name)
    receipt = create_receipt(records_root, identity, "display-verify", fingerprint, DISPLAY_VERIFY_OPTIONS)
    print(decision_line(receipt, "display-verify", question, DISPLAY_VERIFY_OPTIONS))
    print_birth_state(repo, records_root, runtime_file, runtime, runtime.get("mother") or {}, image, runtime.get("network"), "[SWT] birth: 等待用户决定 (显示栈)")
    return "fail"


def birth(args: argparse.Namespace, repo: Path) -> int:
    records_root = args.records_root.expanduser().resolve()
    if args.lan_ip:
        # D010/UD-03: 用户确认的局域网地址即持久化 (host 级), 之后读取优先用已确认值;
        # 格式校验先于写入 (仿 --hostname 先例), 非法值不落盘
        write_confirmed_lan_address(records_root, require_valid_lan_ip(args.lan_ip))
    if args.base and not any((args.mode, args.image, args.requirements, args.new_mother, args.reuse_mother)):
        raise PreconditionError("NOT-IMPLEMENTED birth")
    branch = resolve_mother_branch(repo, args.branch)
    identity_mother = mother_path(repo, branch)
    identity = resolve_pair_identity(repo, records_root, identity_mother)
    runtime_file = records_root / "runtime" / f"{identity}.json"
    runtime_existing = load_runtime(runtime_file)
    if runtime_existing is not None and runtime_existing.get("stage") == "idle":
        # 上次已彻底终结 (容器空/daemon 灭): 视为全新 birth, runtime 由后续流程重建覆盖.
        runtime_existing = None
    if runtime_existing is None:
        # 本对残留检查 (并行母体: 只看本对母体目录, 其他对的 daemon 是并存常态);
        # 旧形态主仓路径 daemon 不在此拦 — 由下方迁移统一重摆.
        active_daemons = daemon_pids_for_serve_path(identity_mother)
        if active_daemons:
            raise PreconditionError(
                f"母体 {identity_mother.name} 已有存活 daemon(pid={active_daemons[0]}), 请先清理 daemon 后再 birth"
            )
    mother_dir, dirty = find_mother(repo, branch)
    if dirty:
        raise PreconditionError(f"母体工作树脏, 请先人工处理: {mother_dir}")
    # 显示栈门禁重入 (D041): 上次 birth 已 born 但 display-verify 失败,
    # 带 --display-continue/--display-recheck (或不带 flag 重问) 只处理显示段,
    # 不重走全链 (全链重入会 re-clone, 丢容器内未提交工作).
    reentry = birth_display_gate_reentry(args, repo, records_root, runtime_existing, runtime_file)
    if reentry is not None:
        return reentry
    # 容器名单源 (评审修复): 推导一次写回 args, 后续冲突检查/hostname 候选/
    # wire/create 复用同一值, 不再各自 fork slug 子进程. name_explicit 在写回前
    # 捕获 — born 重入守卫仍要求显式 --name, 不受缺省回填影响.
    name_explicit = bool(args.name)
    args.name = args.name or container_default_name(branch)
    # D003: 一母体同一时刻只有一个活跃容器 — 同母体已有活跃容器 (异名) 时拒绝
    # 新建 (含 born 重入加新 --name 路径); 同名重入 (失败重试) 与 retired 容器
    # 不算冲突; 只拒绝本次新建, 不追溯处置既有容器 (D009). 放在显示门禁重入之后,
    # 不重伤 display 重入流.
    conflict = birth_active_container_conflict(
        runtime_existing, live_repo_containers(repo), branch, args.name)
    if conflict:
        raise PreconditionError(conflict)
    image = mark_newer_available(prepare_image(args, repo, records_root), runtime_existing)
    network_input = {"mode": args.mode, "allow": list(args.allow), "deny": list(args.deny)}
    identity = runtime_file.stem
    # 收据绑定当前外部状态; 用户本次填写的网络答案本身不应使上一张票据失效.
    fingerprint = decision_fingerprint(repo, branch, mother_dir, image)
    pending: list[tuple[str, str, list[str]]] = []

    stale_receipts: dict[str, bool] = {}
    # 母体选择决策废除 (并行母体): --branch 定对, 母体存在与否是机械事实, 不再问人;
    # 存在即复用, 不存在即按 --base/缺省分支新建. PARTIAL runtime (未 born) 重入时
    # 允许 --new-mother (首跑可能已建母体, 重跑须收敛而不是拒绝).
    partial_runtime = bool(runtime_existing and runtime_existing.get("stage") != "born")
    for decision_kind in ("network-mode", "image-build", "hostname", "lan-address"):
        stale_receipts[decision_kind] = expire_receipts(records_root, identity, decision_kind, fingerprint)

    network_decision = decision_pending(
        records_root, identity, "network-mode", fingerprint, args.mode is not None,
        "请选择网络模式; whitelist 会自动放行网关地址 (DNS); git 走 unix socket 桥, 不占网络白名单",
        "网络/配置状态已变化, 请重新确认",
        ["--mode whitelist --allow ...", "--mode blacklist [--deny ...]"],
        stale_receipts["network-mode"],
    )
    if network_decision:
        pending.append(network_decision)

    if mother_dir and args.new_mother and not partial_runtime:
        raise PreconditionError("母体已存在, 不能使用 --new-mother")
    if not mother_dir and args.reuse_mother:
        raise PreconditionError("母体不存在, 不能使用 --reuse-mother")

    # 主机名确认 (D047): 候选 = 容器名, host-llm 转述时可附推荐, 用户拍板后
    # 带 --hostname <名> 重跑; 缺省不答 (不放行默认), 保证每个容器名都经人确认
    hostname_candidate = args.name
    if args.hostname is not None and not re.fullmatch(r"[a-zA-Z0-9]([a-zA-Z0-9.-]{0,61}[a-zA-Z0-9])?", args.hostname):
        raise PreconditionError(f"--hostname 非法 (须为 RFC1123 主机名): {args.hostname}")
    hostname_decision = decision_pending(
        records_root, identity, "hostname", fingerprint, args.hostname is not None,
        f"容器主机名确认 (候选: {hostname_candidate})", "状态已变化, 请重新确认主机名",
        [f"--hostname {hostname_candidate}"],
        stale_receipts["hostname"],
    )
    if hostname_decision:
        pending.append(hostname_decision)

    # 局域网地址确认 (D010/UD-03): 顶部已把 --lan-ip 写入持久文件, 带 flag 重跑
    # 先持久化再判定; 无已确认值才问; 收据闭环同其他 kind (失配重问/匹配消费)
    lan_address = lan_address_decision(records_root, identity, fingerprint, args.lan_ip,
                                       stale_receipts["lan-address"])
    if lan_address:
        pending.append(lan_address)

    if not args.image and image.get("verdict") == "BUILD-NEW":
        pending.append(("image-build", "没有满足需求的镜像, 请按 reason 构建后重跑并指定 --image", ["--image <ref>"]))
    if pending:
        lines: list[str] = []
        for kind, question, options in pending:
            receipt = matching_receipt(records_root, identity, kind, fingerprint)
            if receipt is None:
                receipt = create_receipt(records_root, identity, kind, fingerprint, options)
            lines.append(decision_line(receipt, kind, question, options))
        mother_state = {"branch": branch, "dir": str(mother_dir) if mother_dir else None, "exists": bool(mother_dir), "worktree-dirty": dirty}
        for line in lines:
            print(line)
        print_birth_state(repo, records_root, runtime_file, runtime_existing, mother_state, image, network_input, "[SWT] birth: 等待用户决定")
        return 1

    # 并行母体一次性迁移 (幂等): 主仓级 hideRefs 残留迁入各母体 config.worktree 并重摆
    # per-mother daemon (含桥与容器 remote). 必须先于任何 per-mother 资源动作, 否则
    # 本对新 daemon 会被残留的主仓级 hideRefs 越权面波及; 迁移后重读本对 runtime
    # (若本对自身是旧形态, 迁移已更新其 daemon 记录).
    migrate_legacy_pairs(repo, records_root)
    runtime_existing = load_runtime(runtime_file)
    if runtime_existing is not None and runtime_existing.get("stage") == "idle":
        runtime_existing = None

    if runtime_existing and runtime_existing.get("stage") == "born":
        if not args.reuse_mother or not name_explicit:
            raise PreconditionError("已有 birth runtime, 同母体重入必须带 --reuse-mother 和新的 --name")
        runtime = runtime_existing
        mother_dir = Path(runtime["mother_dir"]).resolve()
        daemon_record = runtime.get("daemon")
        if not isinstance(daemon_record, dict) or not process_alive(daemon_record.get("pid")):
            raise PreconditionError("已有 runtime 但 daemon 不存活, 请先使用 resume")
    elif runtime_existing:
        if runtime_existing.get("stage") not in {"daemon", "container-created", "container-started", "network", "ssh-ready"}:
            raise PreconditionError("已有未完成 birth runtime, 请按 PARTIAL 指引处理")
        runtime = runtime_existing
        mother_dir = Path(runtime["mother_dir"]).resolve()
        daemon_record = runtime.get("daemon")
        if not isinstance(daemon_record, dict) or not process_alive(daemon_record.get("pid")):
            raise PreconditionError("已有 PARTIAL runtime 但 daemon 不存活, 请人工恢复 daemon")
    else:
        expected = {**expected_repo_config(), **expected_pair_config(branch)}
        validate_config_before_resources(repo, mother_dir, expected)
        if mother_dir is None:
            mother_dir = create_mother_worktree(repo, branch, args.base)
        elif not mother_dir.is_dir():
            raise PreconditionError(f"母体目录不存在: {mother_dir}")
        runtime = {
            "schema": SCHEMA, "repo": str(repo.resolve()), "mother": {"branch": branch, "dir": str(mother_dir)},
            "mother_branch": branch, "mother_dir": str(mother_dir), "stage": "mother",
            "config": {"swt-form": False}, "daemon": None, "containers": [], "image": image,
            "network": network_input,
        }
        atomic_write_json(runtime_file, runtime)
        try:
            place_daemon_export_ok(mother_dir)
            try:
                configure_repo(repo, mother_dir, branch)
            except SwtError as exc:
                raise SwtError(3, "PARTIAL", f"config 写入/校验失败, 母体和 runtime 已建立: {exc.message}") from exc
            runtime["config"] = {"swt-form": True}
            runtime["stage"] = "config"
            atomic_write_json(runtime_file, runtime)
            daemon = start_daemon(mother_dir)
            daemon_record = {"pid": daemon.process.pid, "addr": daemon.address, "port": daemon.port, "base-path": str(daemon.base_path), "orphan": False}
            runtime["daemon"] = daemon_record
            runtime["stage"] = "daemon"
            atomic_write_json(runtime_file, runtime)
        except SwtError:
            raise
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SwtError(3, "PARTIAL", f"birth 在 {runtime.get('stage')} 阶段失败, 请按现有 runtime/容器状态恢复: {exc}") from exc

    if not isinstance(daemon_record, dict):
        raise SwtError(3, "PARTIAL", "daemon runtime 记录缺失")
    runtime["daemon"] = daemon_record
    runtime["image"] = image
    atomic_write_json(runtime_file, runtime)
    try:
        ensure_git_bridge(records_root, identity, runtime)
        atomic_write_json(runtime_file, runtime)
        env_map = load_inherited_env(records_root, resolve_project_slug(repo))
        # ISSUE-06 信箱接线: 须在 create 之前 (podman -e 只在创建时烘入);
        # 失败只告警跳过, 不阻断 birth. 登记落容器记录 (多容器并存各自一段).
        # 容器名已于上方单源写回 args.name, wire 与 create 共用同一值.
        # 重入 (评审修复): 容器已存在时 create 走 refresh 早退, env 不重烘;
        # 此时申领新 key 只会在服务端累积有效 key 且 connected 登记与实况不符 —
        # 跳过 wire, 不动既有 mailbox 登记; 仅给无登记的老记录补一条 skipped 说明.
        container_existed = container_exists(args.name)
        mailbox_record = None if container_existed else wire_container_mailbox(env_map, args.name)
        # M08 D003: 解析 chromium 精确路径 (UD-06, 失败跳过不阻断) → 实例落档;
        # 重入 (容器已在) 不重生成, 挂载维持旧容器既有状态.
        headed_script = None
        if not container_existed:
            chromium_path = resolve_container_chromium_path(image["ref"])
            if chromium_path is not None:
                headed_script = stage_headed_browser_script(records_root, identity, chromium_path)
        container = create_and_start_container(args, repo, image, branch, runtime, runtime_file, env_map, records_root, identity, headed_script=headed_script)
        if mailbox_record is not None:
            container["record"]["mailbox"] = mailbox_record
            upsert_container_record(runtime, container["record"], runtime_file)
        elif "mailbox" not in container["record"]:
            container["record"]["mailbox"] = {
                "status": "skipped", "container": args.name,
                "reason": "container-exists: 重入不重复申领 key (env 不重烘)",
            }
            upsert_container_record(runtime, container["record"], runtime_file)
        gateway_address = container_gateway(container["name"])
        route_gateway = container_route_gateway(container["detail"])
        ip_value = container_ip(container["detail"])
        target_netns = pasta_netns(container["detail"])
        if not target_netns:
            raise SwtError(3, "PARTIAL", f"容器 {container['name']} 的 inspect 没有 SandboxKey")
        shared_netns = target_netns
        container["record"]["network-ip"] = ip_value
        runtime["network"] = apply_network(
            NetworkPlan(
                args.mode,
                tuple(args.allow),
                tuple(args.deny),
                gateway_address,
                ip_value,
                shared_netns,
                route_gateway,
            )
        )
        own_netns = container_netns(container["detail"])
        if own_netns and own_netns != shared_netns:
            apply_sibling_networks(
                runtime["network"],
                [
                    item for item in runtime.get("containers", [])
                    if is_active_container(item)
                ],
                {own_netns},
            )
        runtime["stage"] = "network"
        atomic_write_json(runtime_file, runtime)
        key = inject_ssh_key(container, records_root, identity, runtime, runtime_file, env_map)
        inject_auth_json(container["name"])
        ensure_agent_prompt_parents(container["name"])
        ensure_container_git_forward(container["name"])
        remote = fixed_git_remote(mother_dir)
        container["record"]["remote"] = remote
        atomic_write_json(runtime_file, runtime)
        wait_for_ssh(key, container["port"])
        assert_container_clone(container, key, branch, remote)
        runtime["stage"] = "born"
        runtime["network"] = {**runtime["network"], "gateway": gateway_address, "container-ip": ip_value, "netns": shared_netns}
        atomic_write_json(runtime_file, runtime)
        host_display_status = ensure_host_display(runtime, runtime_file, container["record"])
        display_status = birth_display_gate(args, repo, records_root, identity, runtime, runtime_file, container)
        if display_status == "fail":
            return 1
    except SwtError:
        raise
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SwtError(3, "PARTIAL", f"birth 在 {runtime.get('stage')} 阶段失败, 请按现有 runtime/容器状态恢复: {exc}") from exc
    port = container["record"].get("ssh-port") or container.get("port")
    print_delivery_lines(
        "birth: 已完成",
        port,
        container["record"].get("vnc-port"),
        display_status,
        key,
        read_confirmed_lan_address(records_root),
        host_display_status,
        container["record"].get("web-port"),
        headed_script=container.get("headed-script"),
    )
    observed_daemon = daemon_state(mother_dir, repo, runtime)
    state = build_state(
        repo, records_root, runtime_file, runtime,
        mother={"branch": branch, "dir": str(mother_dir), "exists": True, "worktree-dirty": False},
        containers=runtime["containers"],
        daemon=observed_daemon or {**runtime["daemon"], "orphan": True},
        image=runtime["image"], network=runtime["network"],
    )
    print_state(state, "[SWT] birth: 已完成")
    return 0


def default_branch(repo: Path) -> str:
    result = run(["git", "-C", str(repo), "symbolic-ref", "--short", "HEAD"])
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return "HEAD"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="swt")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("birth", "resume", "status", "terminate"):
        command = subparsers.add_parser(name)
        command.add_argument("--repo")
        command.add_argument("--records-root", type=Path, default=Path.home() / ".agents" / "sandbox-worktree")
    subparsers.choices["birth"].add_argument("--branch")
    subparsers.choices["birth"].add_argument("--base")
    subparsers.choices["birth"].add_argument("--name")
    subparsers.choices["birth"].add_argument("--mode", choices=("whitelist", "blacklist"))
    subparsers.choices["birth"].add_argument("--allow", action="append", default=[])
    subparsers.choices["birth"].add_argument("--deny", action="append", default=[])
    subparsers.choices["birth"].add_argument("--image")
    subparsers.choices["birth"].add_argument("--requirements")
    subparsers.choices["birth"].add_argument("--new-mother", action="store_true")
    subparsers.choices["birth"].add_argument("--reuse-mother", action="store_true")
    subparsers.choices["birth"].add_argument("--hostname")
    subparsers.choices["birth"].add_argument("--lan-ip", dest="lan_ip", metavar="IPV4",
                                             help="确认宿主局域网地址 (D010), 持久化后交付优先用已确认值")
    subparsers.choices["resume"].add_argument("--branch")
    subparsers.choices["resume"].add_argument("--name")
    subparsers.choices["resume"].add_argument("--confirm", action="store_true")
    subparsers.choices["terminate"].add_argument("--branch")
    subparsers.choices["terminate"].add_argument("--name")
    subparsers.choices["terminate"].add_argument("--force", action="store_true")
    subparsers.choices["birth"].add_argument("--display-continue", action="store_true",
                                             help="显示栈验证失败后选择继续 (显示栈降级)")
    subparsers.choices["birth"].add_argument("--display-recheck", action="store_true",
                                             help="显示栈验证失败后选择重验一次")
    display_check_parser = subparsers.add_parser(
        "display-check", help="显示栈全量通道检查 (诊断, 非 DECIDE)")
    display_check_parser.add_argument("--repo")
    display_check_parser.add_argument("--records-root", type=Path,
                                      default=Path.home() / ".agents" / "sandbox-worktree")
    display_check_parser.add_argument("--name")
    display_check_parser.add_argument("--evidence-dir")
    enroll_parser = subparsers.add_parser(
        "enroll-device-key", help="设备侧公钥并入容器 authorized_keys (设备→容器免密, N4)")
    enroll_parser.add_argument("container", metavar="容器名")
    enroll_parser.add_argument("--pubkey-file", dest="pubkey_file", metavar="路径|-", default=None,
                               help="公钥文件路径; - 或缺省读 stdin")
    return parser.parse_args(argv)


def runtime_container(runtime: dict[str, Any] | None, name: str, podman_id: str) -> dict[str, Any]:
    if not runtime:
        return {}
    records = runtime.get("containers", [])
    if not isinstance(records, list):
        return {}
    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("name") == name or record.get("podman-id") in {podman_id, podman_id[:12]}:
            return record
    return {}


def podman_json(command: list[str]) -> list[dict[str, Any]]:
    result = run(command)
    if result.returncode != 0:
        raise SwtEnvError(result.stderr.strip() or "podman 查询失败")
    if not result.stdout.strip():
        return []
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SwtEnvError("podman 输出不是 JSON") from exc
    if isinstance(value, dict):
        return [value]
    return [item for item in value if isinstance(item, dict)]


def ssh_container_git_status(
    runtime_record: dict[str, Any],
    ssh_port: int,
    branch: str | None,
    mother_tip: str | None,
) -> dict[str, Any] | None:
    private_key = runtime_record.get("ssh_private_key") or runtime_record.get("ssh-private-key")
    if not isinstance(private_key, str) or not Path(private_key).is_file():
        return None
    clone_dir = runtime_record.get("clone_dir") or runtime_record.get("clone-dir") or "/workspace"
    if not isinstance(clone_dir, str):
        return None
    base = container_ssh_base(Path(private_key), ssh_port)
    comparison = shlex.quote(mother_tip) if mother_tip else shlex.quote(f"origin/{branch or 'main'}")
    try:
        status_result = run(
            [*base, f"git -C {shlex.quote(clone_dir)} status --porcelain=v1"],
            timeout=3,
        )
        if status_result.returncode != 0:
            return None
        has_mother_object = None
        if mother_tip:
            has_mother_object = run(
                [
                    *base,
                    f"git -C {shlex.quote(clone_dir)} cat-file -e "
                    f"{shlex.quote(mother_tip + '^{commit}')}",
                ],
                timeout=3,
            )
        if has_mother_object is not None and has_mother_object.returncode != 0:
            probe_refspec = f"+refs/heads/{branch or 'main'}:refs/swt-probe/mother"
            fetched = run(
                [
                    *base,
                    f"git -C {shlex.quote(clone_dir)} fetch --quiet --no-write-fetch-head --refmap= origin "
                    f"{shlex.quote(probe_refspec)}",
                ],
                timeout=5,
            )
            if fetched.returncode != 0:
                return None
            comparison = "refs/swt-probe/mother"
        relation_result = run(
            [
                *base,
                f"git -C {shlex.quote(clone_dir)} rev-list --count --left-right "
                f"{comparison}...HEAD",
            ],
            timeout=3,
        )
        fields = relation_result.stdout.strip().split() if relation_result.returncode == 0 else []
        relation: str | None = None
        behind: int | None = None
        if len(fields) == 2 and all(field.isdigit() for field in fields):
            behind, ahead = (int(field) for field in fields)
            if ahead == 0 and behind == 0:
                relation = "same"
            elif ahead == 0:
                relation = "behind"
            elif behind == 0:
                relation = "ahead"
            else:
                relation = "diverged"
        elif len(fields) == 1 and fields[0].isdigit():
            # 兼容旧探针只返回一个总数的退回语义, 正常路径始终走双计数.
            ahead = int(fields[0])
        else:
            return None
    except (SwtEnvError, subprocess.TimeoutExpired):
        return None
    result: dict[str, Any] = {
        "uncommitted": len([line for line in status_result.stdout.splitlines() if line]),
        "unpushed": ahead,
        "relation": relation,
        "reachable": True,
    }
    if behind is not None:
        result["behind"] = behind
    return result


def podman_container_state(
    repo: Path,
    runtimes: list[dict[str, Any]] | dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """盘点主仓 label 下全部容器 (并行母体: 跨对聚合). 每容器的脏检查用
    它自己所属对的分支 (记录/label 反推), 不再假设全仓一个母体分支."""
    if isinstance(runtimes, dict) or runtimes is None:  # 兼容旧单 runtime 调用形态
        runtimes = [runtimes]
    records: list[dict[str, Any]] = []
    for runtime in runtimes:
        for record in (runtime or {}).get("containers", []):
            if isinstance(record, dict):
                records.append(record)

    def lookup(name: str, podman_id: str) -> dict[str, Any]:
        for record in records:
            if record.get("name") == name or record.get("podman-id") in {podman_id, podman_id[:12]}:
                return record
        return {}

    rows = podman_json(
        [
            "podman",
            "ps",
            "-a",
            "--filter",
            f"label=sandbox-worktree.repo={repo}",
            "--format",
            "json",
        ]
    )
    containers: list[dict[str, Any]] = []
    for row in rows:
        name = podman_row_name(row)
        if not name:
            continue
        inspected = podman_json(["podman", "inspect", name])
        detail = inspected[0] if inspected else row
        state = detail.get("State") if isinstance(detail.get("State"), dict) else {}
        podman_id = str(detail.get("Id") or detail.get("ID") or row.get("Id") or row.get("ID") or "")
        image_digest = (
            detail.get("ImageDigest")
            or detail.get("Image")
            or row.get("ImageDigest")
            or row.get("Image")
        )
        port_result = run(["podman", "port", name])
        mapped_ports: dict[str, int] = {}
        if port_result.returncode == 0:
            mapped_ports = parse_podman_ports(port_result.stdout)
        ssh_port = mapped_ports.get("22")
        vnc_port = mapped_ports.get("6080")
        web_port = mapped_ports.get("8800")
        retired_record = lookup(name, podman_id)
        labels = row.get("Labels") if isinstance(row.get("Labels"), dict) else {}
        branch = (
            retired_record.get("branch")
            or retired_record.get("mother")
            or (labels.get("sandbox-worktree.mother") if isinstance(labels.get("sandbox-worktree.mother"), str) else None)
        )
        mother_tip = ref_tip(repo, branch) if branch else None
        dirty: dict[str, Any] = {
            "uncommitted": None,
            "unpushed": None,
            "relation": None,
            "reachable": False,
        }
        if ssh_port is not None:
            ssh_dirty = ssh_container_git_status(retired_record, ssh_port, branch, mother_tip)
            if ssh_dirty is not None:
                dirty = ssh_dirty
        network_ip = retired_record.get("network-ip")
        if not isinstance(network_ip, str):
            try:
                network_ip = container_ip(detail)
            except SwtError:
                network_ip = None
        containers.append(
            {
                "name": name,
                "branch": branch,
                "podman-id": podman_id or None,
                "state": state.get("Status") or row.get("State") or row.get("Status"),
                "ssh-port": ssh_port,
                "vnc-port": vnc_port or retired_record.get("vnc-port"),
                "web-port": web_port or retired_record.get("web-port"),
                "display": retired_record.get("display"),
                "network-ip": network_ip,
                "image-digest": image_digest,
                "retired": bool(retired_record.get("retired", False)),
                "dirty": dirty,
            }
        )
    return containers


def terminate_container_candidates(
    repo: Path,
    runtimes: list[tuple[Path, dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """终结候选跨对聚合 (并行母体); 每个候选带 _runtime-file 指回所属对的 runtime."""
    observed = podman_container_state(repo, [data for _, data in runtimes])
    by_name = {item["name"]: item for item in observed if item.get("name")}
    file_by_name: dict[str, Path] = {}
    for path, data in runtimes:
        for record in data.get("containers", []):
            if isinstance(record, dict) and is_active_container(record) and record.get("name"):
                file_by_name.setdefault(str(record["name"]), path)
    candidates: list[dict[str, Any]] = []
    names = set(by_name) | set(file_by_name)
    for name in sorted(names):
        runtime_file = file_by_name.get(name)
        record: dict[str, Any] = {}
        if runtime_file is not None:
            data = next(data for path, data in runtimes if path == runtime_file)
            record = next(
                (item for item in data.get("containers", []) if isinstance(item, dict) and item.get("name") == name),
                {},
            )
        target = dict(record)
        target.update(by_name.get(name, {}))
        target["name"] = name
        target["_runtime-file"] = runtime_file
        if name not in by_name:
            target.setdefault("state", "missing")
            target["dirty"] = {
                "uncommitted": None,
                "unpushed": None,
                "relation": None,
                "reachable": False,
            }
        candidates.append(target)
    return candidates, observed


def is_active_container(item: Any) -> bool:
    return isinstance(item, dict) and not item.get("retired")


def terminate_dirty(dirty: dict[str, Any]) -> bool:
    if not dirty.get("reachable"):
        return True
    if dirty.get("uncommitted") is None or dirty.get("unpushed") is None:
        return True
    return bool(
        dirty.get("uncommitted", 0)
        or dirty.get("unpushed", 0)
        or dirty.get("relation") in {"ahead", "diverged"}
    )


def dirty_explanation(dirty: dict[str, Any]) -> str:
    if not dirty.get("reachable"):
        return "unknown(SSH 不可达或容器已停, 视同脏)"
    return (
        f"uncommitted={dirty.get('uncommitted', 0)} "
        f"ahead={dirty.get('unpushed', 0)} "
        f"behind={dirty.get('behind', 0)} "
        f"relation={dirty.get('relation') or 'unknown'}"
    )


def terminate_decision_fingerprint(
    repo: Path,
    runtime: dict[str, Any] | None,
    target: dict[str, Any],
) -> dict[str, Any]:
    branch, mother = runtime_mother(runtime)
    containers = runtime.get("containers", []) if isinstance(runtime, dict) else []
    if not isinstance(containers, list):
        containers = []
    fingerprint = decision_fingerprint_base(
        repo, branch or target.get("branch"), mother,
    )
    fingerprint.update({
        "containers": [
            {"name": item.get("name"), "podman-id": item.get("podman-id")}
            for item in containers
            if is_active_container(item)
        ],
        "image-digest": (runtime.get("image") or {}).get("digest") if isinstance(runtime, dict) and isinstance(runtime.get("image"), dict) else target.get("image-digest"),
        "network": runtime.get("network") if isinstance(runtime, dict) else None,
        "dirty": target.get("dirty", {}),
        "target-branch": branch or target.get("branch"),
    })
    return fingerprint


def terminate_state(
    repo: Path,
    records_root: Path,
    runtime_file: Path | None,
    runtime: dict[str, Any] | None,
    progress: str,
) -> None:
    containers = podman_container_state(repo, [data for _, data in load_repo_runtimes(records_root, repo)])
    print_state(
        build_state(
            repo,
            records_root,
            runtime_file,
            runtime,
            mother=_UNSET,
            containers=containers,
            daemon=_UNSET,
            image=_UNSET,
            network=_UNSET,
        ),
        progress,
    )


def append_audit_entry(records_root: Path, identity: str, entry: dict[str, Any]) -> Path:
    path = records_root / "runtime" / identity / "audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(canonical_json(entry) + "\n")
    return path


def append_audit(
    records_root: Path,
    identity: str,
    target: dict[str, Any],
    decision_id: str,
) -> Path:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "container": target.get("name"),
        "podman-id": target.get("podman-id"),
        "dirty": target.get("dirty"),
        "decision-id": decision_id,
    }
    return append_audit_entry(records_root, identity, entry)


def stop_pair_daemons(
    repo: Path,
    mother: Path | None,
    branch: str | None,
    runtime: dict[str, Any] | None,
) -> None:
    """收本对 daemon: per-mother 形态按母体目录匹配; 旧形态残留按主仓路径兑底
    (仅本对还处于旧形态时); 外加 runtime 记录的 pid. 不碰其他对的 daemon."""
    pids: set[int] = set()
    if mother is not None:
        pids.update(daemon_pids_for_serve_path(mother))
    if pair_is_legacy_form(repo, mother, branch):
        pids.update(daemon_pids_for_serve_path(repo.resolve()))
    recorded = runtime.get("daemon") if isinstance(runtime, dict) else None
    if isinstance(recorded, dict) and isinstance(recorded.get("pid"), int):
        pids.add(recorded["pid"])
    stop_daemon_pids(pids)
    remaining: set[int] = set(pids)
    if mother is not None:
        remaining.update(daemon_pids_for_serve_path(mother))
    if pair_is_legacy_form(repo, mother, branch):
        remaining.update(daemon_pids_for_serve_path(repo.resolve()))
    remaining = {pid for pid in remaining if process_alive(pid)}
    if remaining:
        raise SwtError(3, "PARTIAL", f"daemon 仍存活(pid={sorted(remaining)[0]}), 请先人工终止后重跑 terminate")


def remove_container_firewall(
    runtime: dict[str, Any] | None,
    target: dict[str, Any],
    has_siblings: bool,
    netns: str | None = None,
) -> None:
    container_ip = target.get("network-ip")
    if not isinstance(container_ip, str) or not container_ip:
        return
    script = Path(__file__).with_name("net-firewall.py")
    command = ["uv", "run", "python", str(script), "remove", "--container-ip", container_ip]
    if isinstance(netns, str) and netns:
        command.extend(["--netns", netns])
    else:
        # 没有目标容器的当前 SandboxKey 时, 不得退回 runtime 或全局 pasta 猜测.
        return
    result = run(command, timeout=30)
    if result.returncode == 0:
        return
    # 最后一个容器 rm 后 netns 可能随 pasta 一并消失, 此时规则也已随 netns 消失.
    if not has_siblings and "NETNS-UNREACHABLE" in result.stderr:
        return
    raise SwtError(3, "PARTIAL", f"nft remove 失败: {result.stderr.strip()}")


def remove_container_credentials(target: dict[str, Any]) -> None:
    paths: set[Path] = set()
    private_key = target.get("ssh_private_key") or target.get("ssh-private-key")
    if isinstance(private_key, str) and private_key:
        key_path = Path(private_key)
        paths.update((key_path, Path(str(key_path) + ".pub")))
    password_file = target.get("password_file") or target.get("password-file")
    if isinstance(password_file, str) and password_file:
        paths.add(Path(password_file))
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise SwtError(3, "PARTIAL", f"凭证清理失败: {path}: {exc}") from exc


def terminate(args: argparse.Namespace, repo: Path) -> int:
    records_root = args.records_root.expanduser().resolve()
    runtimes = load_repo_runtimes(records_root, repo)
    candidates, observed = terminate_container_candidates(repo, runtimes)
    if args.branch:
        candidates = [item for item in candidates if item.get("branch") == args.branch]
        if not candidates:
            raise PreconditionError(f"母体 {args.branch} 没有可终结容器")
    if args.name:
        target = next((item for item in candidates if item.get("name") == args.name), None)
        if target is None:
            raise PreconditionError(f"容器不存在或不属于当前主仓的任何母体对: {args.name}")
    elif len(candidates) == 1:
        target = candidates[0]
    elif not candidates:
        raise PreconditionError("没有可终结容器")
    else:
        names = ", ".join(f"{item.get('name')}({item.get('branch')})" for item in candidates)
        raise PreconditionError(f"多个候选容器, 请使用 --name 指定; 候选: {names}")

    runtime_file = target.get("_runtime-file")
    runtime = load_runtime(runtime_file) if runtime_file is not None else None
    if runtime is None:
        raise PreconditionError("容器存在但 runtime 记录缺失, 不自动拆除未登记资源")
    target_name = str(target["name"])
    observed_names = {item.get("name") for item in observed}
    fingerprint = terminate_decision_fingerprint(repo, runtime, target)
    identity = runtime_file.stem
    dirty = terminate_dirty(target.get("dirty", {})) if target_name in {item.get("name") for item in observed} else False
    question = (
        f"容器 {target_name} 脏检查为 {dirty_explanation(target['dirty'])}; "
        "请确认容器内 agent 已停手后再强拆"
    )
    blocked, decision_id = handle_dirty_decision(
        records_root, identity, "terminate-dirty", fingerprint, dirty,
        args.force, question, ["--force"],
    )
    if blocked:
        terminate_state(repo, records_root, runtime_file, runtime, "[SWT] terminate: 等待用户决定")
        return 1

    if dirty and args.force:
        append_audit(records_root, identity, target, decision_id)

    runtime_records = [
        item for item in runtime.get("containers", [])
        if isinstance(item, dict) and item.get("name") != target_name
    ]
    has_siblings = bool(runtime_records)
    network = runtime.get("network") if isinstance(runtime.get("network"), dict) else {}
    sibling_netnses: set[str] = set()
    for sibling in runtime_records:
        sibling_name = sibling.get("name") if isinstance(sibling, dict) else None
        if not isinstance(sibling_name, str):
            continue
        sibling_netns = live_container_netns(sibling_name)
        if sibling_netns:
            sibling_netnses.add(sibling_netns)
    netns_candidates: set[str] = set(sibling_netnses)
    target_netns = live_container_netns(target_name) if target_name in observed_names else None
    if target_netns:
        netns_candidates.add(target_netns)
    remove_errors: list[str] = []
    for netns in sorted(netns_candidates):
        try:
            remove_container_firewall(runtime, target, has_siblings, netns)
        except SwtError as exc:
            if "NETNS-UNREACHABLE" not in exc.message:
                remove_errors.append(exc.message)
    if remove_errors:
        raise SwtError(3, "PARTIAL", f"nft remove 失败: {'; '.join(remove_errors)}")
    if target_name in observed_names:
        removed = run(["podman", "rm", "-f", target_name], timeout=30)
        if removed.returncode != 0:
            still_there = run(["podman", "inspect", target_name])
            if still_there.returncode == 0:
                raise SwtError(3, "PARTIAL", f"容器 {target_name} 删除失败: {removed.stderr.strip()}")
    if has_siblings:
        apply_sibling_networks(network, runtime_records, sibling_netnses)
    if not has_siblings:
        pair_branch, pair_mother = runtime_mother(runtime)
        stop_pair_daemons(repo, pair_mother, pair_branch, runtime)
        stop_git_bridge(runtime, records_root, identity)
        if isinstance(runtime.get("daemon"), dict):
            runtime["daemon"].pop("bridge", None)

    remove_container_credentials(target)
    runtime["containers"] = runtime_records
    if has_siblings:
        runtime["stage"] = "born"
        if isinstance(runtime.get("network"), dict):
            runtime["network"]["table-present"] = True
    else:
        runtime["stage"] = "idle"
        runtime["daemon"] = None
        if isinstance(runtime.get("network"), dict):
            runtime["network"]["table-present"] = False
    atomic_write_json(runtime_file, runtime)
    mother = runtime.get("mother") if isinstance(runtime.get("mother"), dict) else {}
    mother_dir = mother.get("dir")
    progress = "[SWT] terminate: 已完成"
    if isinstance(mother_dir, str):
        progress += f"; 母体保留路径: {mother_dir}"
    terminate_state(repo, records_root, runtime_file, runtime, progress)
    return 0


def daemon_state(mother: Path | None, repo: Path, runtime: dict[str, Any] | None) -> dict[str, Any] | None:
    """单对 daemon 观测: 记录在先 (pid 存活即认); 无记录时按服务目录扫孤儿 —
    母体目录 (per-mother 形态) + 旧形态残留 (服务主仓路径, 仅本对处于旧形态时)."""
    recorded = runtime.get("daemon") if isinstance(runtime, dict) else None
    if not isinstance(recorded, dict):
        recorded = None
    branch, _ = runtime_mother(runtime)
    serve_candidates: set[str] = set()
    if mother is not None:
        serve_candidates.add(str(mother.resolve()))
    if pair_is_legacy_form(repo, mother, branch):
        serve_candidates.add(str(repo.resolve()))
    processes: list[tuple[int, str]] = []
    try:
        result = run(["pgrep", "-af", "git[ -]daemon"])
    except SwtEnvError:
        result = run(["ps", "-eo", "pid=,args="])
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            fields = line.strip().split(None, 1)
            if not fields or not fields[0].isdigit():
                continue
            pid_value = int(fields[0])
            command = fields[1] if len(fields) > 1 else ""
            if pid_value == os.getpid() or "pgrep" in command:
                continue
            serve = command.strip().rsplit(None, 1)[-1].strip("'\"") if command.strip() else ""
            try:
                serve_resolved = str(Path(serve).expanduser().resolve())
            except OSError:
                continue
            if serve_resolved in serve_candidates:
                processes.append((pid_value, command))
    pid = recorded.get("pid") if recorded else None
    alive = False
    if isinstance(pid, int):
        try:
            os.kill(pid, 0)
            alive = True
        except (OSError, ProcessLookupError):
            alive = False
    if recorded is None and processes:
        pid, command = processes[0]
        alive = True
    if recorded is None and not processes:
        return None
    addr = recorded.get("addr") if recorded else None
    port = recorded.get("port") if recorded else None
    base_path = recorded.get("base-path") if recorded else None
    if recorded is None and processes:
        command = processes[0][1]
        if addr is None:
            match = re.search(r"(?:--listen(?:=|\s+))([^\s]+)", command)
            addr = match.group(1) if match else "0.0.0.0"
        if port is None:
            match = re.search(r"(?:--port(?:=|\s+))(\d+)", command)
            port = int(match.group(1)) if match else None
        match = re.search(r"(?:--base-path(?:=|\s+))([^\s]+)", command)
        base_path = match.group(1).strip("'\"") if match else str(repo.parent.resolve())
    result = {"addr": addr, "port": port, "orphan": not alive or recorded is None}
    if recorded is not None:
        result.update({"pid": pid, "base-path": base_path})
        bridge = recorded.get("bridge")
        if isinstance(bridge, dict):
            result["bridge"] = {
                "pid": bridge.get("pid"),
                "socket": bridge.get("socket"),
                "alive": process_alive(bridge.get("pid")),
            }
    return result


def resume_decision_fingerprint(
    repo: Path,
    runtime: dict[str, Any],
    observed: list[dict[str, Any]],
    target: dict[str, Any],
    network_ready: bool,
) -> dict[str, Any]:
    branch, mother = runtime_mother(runtime)
    fingerprint = decision_fingerprint_base(repo, branch, mother)
    fingerprint.update({
        "config-swt-form": pair_config_matches(repo, mother, branch),
        "containers": [
            {
                "name": item.get("name"),
                "podman-id": item.get("podman-id"),
                "state": item.get("state"),
                "retired": bool(item.get("retired")),
            }
            for item in observed
            if not item.get("retired")
        ],
        "target": {
            "name": target.get("name"),
            "podman-id": target.get("podman-id"),
            "state": target.get("state"),
        },
        "network-ready": network_ready,
        "network": runtime.get("network"),
    })
    return fingerprint


def resume_container_candidates(
    runtime: dict[str, Any],
    observed: list[dict[str, Any]],
    name: str | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records = runtime.get("containers", [])
    if not isinstance(records, list):
        records = []
    observed_by_name = {item.get("name"): item for item in observed if item.get("name")}
    candidates: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict) or not record.get("name"):
            continue
        item = dict(record)
        item.update(observed_by_name.get(record["name"], {}))
        item["name"] = record["name"]
        candidates.append(item)
    if name:
        target = next((item for item in candidates if item.get("name") == name), None)
        if target is None:
            raise PreconditionError(f"容器不存在或不属于当前 runtime: {name}")
        return target, candidates
    active = [item for item in candidates if not item.get("retired")]
    if len(active) == 1:
        return active[0], candidates
    if len(active) > 1:
        names = ", ".join(str(item.get("name")) for item in active)
        raise PreconditionError(f"当前母体有多个可恢复容器, 请使用 --name; 候选: {names}")
    if len(candidates) == 1:
        return candidates[0], candidates
    raise PreconditionError("当前母体没有可恢复容器")


def ensure_display_after_resume(
    runtime: dict[str, Any],
    runtime_file: Path,
    record: dict[str, Any],
) -> str:
    """resume 显示栈重拉 (D040, 与防火墙重注入同位置) + status 级秒级检查
    (D041). 失败降级: 更新 STATE 显示栈状态并汇报注明, 不阻断终端工作.
    返回: ok / degraded / absent."""
    name = str(record.get("name"))
    if not container_has_swt_vnc(name):
        record["display"] = "absent"
        upsert_container_record(runtime, record, runtime_file)
        print("[SWT] 显示栈: 容器镜像未内置 swt-vnc, 跳过 (absent)")
        return "absent"
    started, start_output = start_display_stack(name)
    ok = started
    detail = start_output
    if ok:
        ok, detail = display_stack_status(name)
    if ok:
        record["display"] = "ok"
        upsert_container_record(runtime, record, runtime_file)
        return "ok"
    record["display"] = "degraded"
    upsert_container_record(runtime, record, runtime_file)
    print(f"[SWT] 显示栈降级 (重拉/状态检查未过: {detail[-160:]}); 终端工作不受影响", file=sys.stderr)
    return "degraded"


def resume_daemon_stale(daemon: dict[str, Any] | None, runtime: dict[str, Any]) -> bool:
    recorded = runtime.get("daemon")
    if not isinstance(recorded, dict) or not process_alive(recorded.get("pid")):
        return True
    return daemon is None or bool(daemon.get("orphan"))


def git_bridge_ready(runtime: dict[str, Any]) -> bool:
    daemon = runtime.get("daemon")
    bridge = daemon.get("bridge") if isinstance(daemon, dict) else None
    if not isinstance(bridge, dict) or not process_alive(bridge.get("pid")):
        return False
    socket_value = bridge.get("socket")
    return isinstance(socket_value, str) and Path(socket_value).exists()


def resume_git_ready(record: dict[str, Any], remote: str) -> bool:
    """git 通道就绪 (P0-1/P1-4): 记录 remote 已是固定桥地址, 容器内 origin 实际指向它,
    且经桥 ls-remote 通. 旧形态 remote (host.containers.internal:端口) 一律判未就绪,
    由恢复路径收敛."""
    if record.get("remote") != remote:
        return False
    key_value = record.get("ssh_private_key") or record.get("ssh-private-key")
    port = record.get("ssh-port")
    if not isinstance(key_value, str) or not isinstance(port, int) or not Path(key_value).is_file():
        return False
    clone_dir = record.get("clone_dir") or record.get("clone-dir") or f"/home/bolo/Workspace/{record.get('branch')}"
    probe = ssh_command(
        Path(key_value), port,
        f"git -C {shlex.quote(str(clone_dir))} remote get-url origin && git ls-remote {shlex.quote(remote)}",
        timeout=8,
    )
    if probe.returncode != 0:
        return False
    first_line = probe.stdout.splitlines()[0].strip() if probe.stdout.splitlines() else ""
    return first_line == remote


def resume_network_status(runtime: dict[str, Any], target: dict[str, Any]) -> tuple[bool, str]:
    network = runtime.get("network")
    container_name = target.get("name")
    container_ip_value = target.get("network-ip")
    if (
        not isinstance(network, dict)
        or not isinstance(container_name, str)
        or not isinstance(container_ip_value, str)
    ):
        return False, ""
    inspected = run(["podman", "inspect", container_name])
    if inspected.returncode != 0:
        return False, ""
    try:
        rows = json.loads(inspected.stdout)
    except json.JSONDecodeError:
        return False, ""
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return False, ""
    detail = rows[0]
    state = detail.get("State") if isinstance(detail.get("State"), dict) else {}
    if state.get("Status") != "running":
        return False, ""
    netns = pasta_netns(detail)
    if not netns:
        return False, ""
    script = Path(__file__).with_name("net-firewall.py")
    result = run(["uv", "run", "python", str(script), "show", "--netns", netns], timeout=10)
    return result.returncode == 0 and f"ip saddr {container_ip_value} " in result.stdout, result.stdout


def resume_ready(target: dict[str, Any], daemon_ready: bool, network_ready: bool, git_ready: bool) -> bool:
    return target.get("state") == "running" and daemon_ready and network_ready and git_ready


def locate_pair_runtime(
    records_root: Path,
    repo: Path,
    *,
    branch: str | None = None,
    container: str | None = None,
) -> tuple[Path, dict[str, Any]] | None:
    """按 --branch/--name 定位对 runtime; 都缺省时要求唯一记录对, 多对时点名消歧."""
    runtimes = load_repo_runtimes(records_root, repo)
    if branch:
        for path, data in runtimes:
            pair_branch, _ = runtime_mother(data)
            if pair_branch == branch:
                return path, data
        return None
    if container:
        for path, data in runtimes:
            for record in data.get("containers", []):
                if isinstance(record, dict) and record.get("name") == container:
                    return path, data
        return None
    if len(runtimes) == 1:
        return runtimes[0]
    if len(runtimes) > 1:
        names = ", ".join(str(runtime_mother(data)[0]) for _, data in runtimes)
        raise PreconditionError(f"本主仓有多对记录, 请用 --branch/--name 定位; 已知母体分支: {names}")
    return None


def collect_resume_daemons(
    repo: Path,
    mother: Path | None,
    branch: str | None,
    runtime: dict[str, Any],
) -> list[int]:
    """resume 收本对残留 daemon: 母体目录匹配 + 旧形态主仓路径兑底 + 记录 pid."""
    pids: set[int] = set()
    if mother is not None:
        pids.update(daemon_pids_for_serve_path(mother))
    if pair_is_legacy_form(repo, mother, branch):
        pids.update(daemon_pids_for_serve_path(repo.resolve()))
    recorded = runtime.get("daemon")
    if isinstance(recorded, dict) and isinstance(recorded.get("pid"), int):
        pids.add(recorded["pid"])
    killed: list[int] = []
    for pid in sorted(pids):
        if pid == os.getpid() or not process_alive(pid):
            continue
        killed.append(pid)
    stop_daemon_pids(pids)
    remaining: set[int] = set()
    if mother is not None:
        remaining.update(daemon_pids_for_serve_path(mother))
    if pair_is_legacy_form(repo, mother, branch):
        remaining.update(daemon_pids_for_serve_path(repo.resolve()))
    remaining = {pid for pid in remaining if process_alive(pid)}
    if remaining:
        raise SwtError(3, "PARTIAL", f"resume 收 daemon 失败(pid={sorted(remaining)[0]}), 请人工终止后重跑")
    return killed


def resume_probe(record: dict[str, Any], remote: str) -> None:
    """resume 的 git 校验 (P0-1): 固定 remote 经容器转发器 + host 桥到 daemon, 全程实测."""
    key_value = record.get("ssh_private_key") or record.get("ssh-private-key")
    port = record.get("ssh-port")
    if not isinstance(key_value, str) or not isinstance(port, int):
        raise SwtError(3, "PARTIAL", "resume 缺少 SSH runtime 记录, 无法校验就绪")
    key = Path(key_value)
    if not key.is_file():
        raise SwtError(3, "PARTIAL", f"resume SSH 私钥不存在: {key}")
    wait_for_ssh(key, port)
    probe = ssh_command(key, port, f"git ls-remote {shlex.quote(remote)}", timeout=10)
    if probe.returncode != 0:
        raise SwtError(3, "PARTIAL", f"git 桥 probe 失败: {probe.stderr.strip()}")
    clone_dir = record.get("clone_dir") or record.get("clone-dir") or f"/home/bolo/Workspace/{record.get('branch')}"
    set_remote = ssh_command(
        key, port,
        f"git -C {shlex.quote(str(clone_dir))} remote set-url origin {shlex.quote(remote)}",
        timeout=10,
    )
    if set_remote.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器 remote 更新失败: {set_remote.stderr.strip()}")
    fetched = ssh_command(
        key, port,
        f"git -C {shlex.quote(str(clone_dir))} fetch --quiet origin",
        timeout=20,
    )
    if fetched.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器 git fetch probe 失败: {fetched.stderr.strip()}")
    record["remote"] = remote


def resume(args: argparse.Namespace, repo: Path) -> int:
    records_root = args.records_root.expanduser().resolve()
    located = locate_pair_runtime(records_root, repo, branch=args.branch, container=args.name)
    if located is None:
        raise PreconditionError("没有 runtime 记录, 请先使用 birth")
    runtime_file, runtime = located
    branch, mother_dir = runtime_mother(runtime)
    if not branch:
        raise PreconditionError("runtime 缺少授权母体分支, 请先人工恢复或 terminate")
    if mother_dir is None:
        raise PreconditionError("runtime 缺少母体目录, 请先人工恢复或 terminate")
    identity = runtime_file.stem

    observed = podman_container_state(repo, [data for _, data in load_repo_runtimes(records_root, repo)])
    target, candidates = resume_container_candidates(runtime, observed, args.name)
    if target.get("retired"):
        raise PreconditionError(
            f"容器 {target.get('name')} 已 retired, resume 被拒绝; 唯一出路是 terminate"
        )
    # P1-2: pasta --config-net 复制宿主换网络前的接口名/地址, 失配时告警提示重建 (不强制)
    if target.get("name"):
        inspected = run(["podman", "inspect", str(target["name"])])
        try:
            rows = json.loads(inspected.stdout) if inspected.returncode == 0 else []
        except json.JSONDecodeError:
            rows = []
        if rows and isinstance(rows[0], dict):
            mismatch = pasta_network_mismatch(rows[0])
            if mismatch:
                print(
                    f"[SWT] 告警: pasta 网络配置与宿主失配 ({mismatch}); "
                    "建议 terminate 后重新 birth (当前不强制)",
                    file=sys.stderr,
                )
    daemon_observed = daemon_state(mother_dir, repo, runtime)
    daemon_ready = not resume_daemon_stale(daemon_observed, runtime) and git_bridge_ready(runtime)
    network_ready, _network_output = resume_network_status(runtime, target)
    pair_remote = fixed_git_remote(mother_dir)
    git_ready = resume_git_ready(target, pair_remote) if (
        target.get("state") == "running" and daemon_ready and network_ready
    ) else False
    active_observed = [item for item in candidates if not item.get("retired")]
    fingerprint = resume_decision_fingerprint(
        repo, runtime, active_observed, target, network_ready,
    )
    identity = runtime_file.stem
    recoverable = not resume_ready(target, daemon_ready, network_ready, git_ready)
    if not recoverable:
        runtime.pop("resume", None)
        runtime["stage"] = "born"
        atomic_write_json(runtime_file, runtime)
        display_status = ensure_display_after_resume(runtime, runtime_file, target)
        host_display_status = ensure_host_display(runtime, runtime_file, target)
        print_delivery_lines(
            "resume: 已就绪, 什么都没有需要恢复",
            target.get("ssh-port"), target.get("vnc-port"), display_status,
            Path(target["ssh_private_key"]) if target.get("ssh_private_key") else None,
            read_confirmed_lan_address(records_root),
            host_display_status,
            target.get("web-port"),
            headed_script=target.get("headed-script"),
        )
        # STATE 用刚写盘的 runtime 容器记录 (含本分支刚更新的 display),
        # 不用函数头取的 observed 快照 — 那是显示栈检查前的旧值, 会与交付行自相矛盾
        print_state(
            build_state(repo, records_root, runtime_file, runtime, mother=_UNSET, containers=runtime["containers"],
                        daemon=daemon_observed, image=_UNSET, network=_UNSET),
            "[SWT] resume: 已就绪, 什么都没有需要恢复",
        )
        return 0

    resume_record = runtime.get("resume")
    answered = (
        isinstance(resume_record, dict)
        and resume_record.get("answered") is True
        and canonical_json(resume_record.get("fingerprint")) == canonical_json(fingerprint)
    )
    receipt = matching_receipt(records_root, identity, "resume", fingerprint)
    receipt_payload = json.loads(receipt.read_text(encoding="utf-8")) if receipt is not None else None
    stale = bool(receipt_files(records_root, identity, "resume") and receipt is None)
    if stale:
        expire_receipts(records_root, identity, "resume", fingerprint)
        receipt = None
        answered = False
    pending = decision_pending(
        records_root,
        identity,
        "resume",
        fingerprint,
        answered or (args.confirm and receipt is not None),
        "检测到可恢复对象, 将收 stale daemon/迁移旧形态配置/start 容器/重拉 daemon/nft --merge/SSH 与 git fetch 校验",
        "恢复前提已变化, 请重新确认",
        ["--confirm"],
        stale,
    )
    if pending:
        pending_kind, pending_question, pending_options = pending
        receipt = matching_receipt(records_root, identity, pending_kind, fingerprint)
        if receipt is None:
            receipt = create_receipt(
                records_root, identity, pending_kind, fingerprint, pending_options,
            )
        print(decision_line(receipt, pending_kind, pending_question, pending_options))
        print_state(
            build_state(repo, records_root, runtime_file, runtime, mother=_UNSET, containers=observed,
                        daemon=daemon_observed, image=_UNSET, network=_UNSET),
            "[SWT] resume: 等待用户决定",
        )
        return 1
    if receipt is not None:
        runtime["resume"] = {
            "answered": True,
            "decision-id": receipt_payload["id"] if receipt_payload else None,
            "fingerprint": fingerprint,
        }
        atomic_write_json(runtime_file, runtime)

    target_name = str(target.get("name"))
    record = next(
        (item for item in runtime.get("containers", [])
         if isinstance(item, dict) and item.get("name") == target_name),
        None,
    )
    if record is None:
        raise PreconditionError(f"容器 {target_name} 缺少 runtime 记录")
    runtime["stage"] = "resume-start"
    atomic_write_json(runtime_file, runtime)
    killed: list[int] = []
    stale_daemon_pid = (
        runtime.get("daemon", {}).get("pid")
        if isinstance(runtime.get("daemon"), dict) and resume_daemon_stale(daemon_observed, runtime)
        else None
    )
    try:
        killed = collect_resume_daemons(repo, mother_dir, branch, runtime)
        # 并行母体迁移自愈 (幂等): 主仓级 hideRefs 残留 → 迁入各母体 config.worktree
        # 并重摆 per-mother daemon; 本对 daemon 由下方标准恢复流程重拉, 迁移跳过本对.
        migrate_legacy_pairs(repo, records_root, skip_daemon_for=mother_dir)
        stop_git_bridge(runtime, records_root, identity)
        detail = inspect_container(target_name)
        state = detail.get("State") if isinstance(detail.get("State"), dict) else {}
        if state.get("Status") != "running":
            started = run(["podman", "start", target_name], timeout=30)
            if started.returncode != 0:
                raise SwtError(3, "PARTIAL", f"resume container-start {target_name}: {started.stderr.strip()}")
        detail = inspect_container(target_name)
        record.update({
            "podman-id": detail.get("Id"), "state": "running",
            "network-ip": container_ip(detail), "retired": False,
        })
        runtime["stage"] = "resume-container-started"
        upsert_container_record(runtime, record, runtime_file)

        daemon = start_daemon(mother_dir)
        daemon_record = {
            "pid": daemon.process.pid, "addr": daemon.address, "port": daemon.port,
            "base-path": str(daemon.base_path), "orphan": False,
        }
        daemon_record["bridge"] = start_git_bridge(records_root, identity, daemon.port)
        runtime["daemon"] = daemon_record
        runtime["stage"] = "resume-daemon"
        atomic_write_json(runtime_file, runtime)

        netns = pasta_netns(detail)
        if not netns:
            raise SwtError(3, "PARTIAL", "resume 的 inspect 没有 SandboxKey")
        network = runtime.get("network") if isinstance(runtime.get("network"), dict) else {}
        gateway = container_gateway(target_name)
        route_gateway = container_route_gateway(detail)
        network.update({"gateway": gateway, "route-gateway": route_gateway, "netns": netns})
        plan = network_plan_from_record(network, record, netns)
        if plan is None:
            raise SwtError(3, "PARTIAL", "resume 缺少网络参数, 无法 fail-closed 注入")
        runtime["network"] = apply_network(plan)
        runtime["network"].update({"container-ip": record["network-ip"], "netns": netns})
        active_records = [
            item for item in runtime.get("containers", [])
            if isinstance(item, dict) and not item.get("retired") and item.get("name") != target_name
        ]
        apply_sibling_networks(runtime["network"], active_records, {netns})
        runtime["stage"] = "resume-network"
        atomic_write_json(runtime_file, runtime)

        ensure_display_after_resume(runtime, runtime_file, record)
        ensure_host_display(runtime, runtime_file, record)
        # auth.json 重注入 (D046): 幂等, 顺带让换 key 在 resume 后生效
        inject_auth_json(target_name)
        ensure_container_git_forward(target_name)

        record["remote"] = fixed_git_remote(mother_dir)
        record["ssh-port"] = container_ssh_port(target_name)
        resume_probe(record, record["remote"])
        runtime["stage"] = "born"
        runtime.pop("resume", None)
        runtime["network"]["table-present"] = True
        atomic_write_json(runtime_file, runtime)
        if killed or isinstance(stale_daemon_pid, int):
            append_audit_entry(records_root, identity, {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "resume", "killed-daemons": killed,
                "stale-daemon": stale_daemon_pid,
            })
    except SwtError:
        runtime["partial-error"] = "resume 执行失败"
        atomic_write_json(runtime_file, runtime)
        raise
    except (OSError, subprocess.TimeoutExpired) as exc:
        runtime["partial-error"] = str(exc)
        atomic_write_json(runtime_file, runtime)
        raise SwtError(3, "PARTIAL", f"resume 中途失败: {exc}") from exc

    observed = podman_container_state(repo, [data for _, data in load_repo_runtimes(records_root, repo)])
    print_delivery_lines(
        "resume: 已完成 fail-closed 恢复",
        record.get("ssh-port"), record.get("vnc-port"), record.get("display"),
        Path(record["ssh_private_key"]) if record.get("ssh_private_key") else None,
        read_confirmed_lan_address(records_root),
        record.get("host-display"),
        record.get("web-port"),
        headed_script=record.get("headed-script"),
    )
    print_state(
        build_state(repo, records_root, runtime_file, runtime, mother=_UNSET, containers=observed,
                    daemon=daemon_record, image=_UNSET, network=_UNSET),
        "[SWT] resume: 已完成 fail-closed 恢复",
    )
    return 0


def network_state(runtime: dict[str, Any] | None) -> dict[str, Any] | None:
    network = runtime.get("network") if isinstance(runtime, dict) else None
    if not isinstance(network, dict):
        return None
    script = Path(__file__).with_name("net-firewall.py")
    result = run(["uv", "run", "python", str(script), "show"])
    return {
        "mode": network.get("mode"),
        "table-present": result.returncode == 0,
        "auto-allow": network.get("auto-allow"),
    }


def latest_build_digest(records_root: Path, repo: Path) -> str | None:
    builds = records_root / resolve_project_slug(repo) / "builds"
    if not builds.is_dir():
        return None
    for build in sorted((path for path in builds.iterdir() if path.is_dir()), key=lambda path: path.name, reverse=True):
        manifest = build / "build.json"
        try:
            value = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        digest = value.get("digest") if isinstance(value, dict) else None
        if isinstance(digest, str) and digest:
            return digest
    return None


def image_state(records_root: Path, repo: Path, runtime: dict[str, Any] | None, containers: list[dict[str, Any]]) -> dict[str, Any] | None:
    image = runtime.get("image") if isinstance(runtime, dict) else None
    if not isinstance(image, dict):
        image = {}
    digest = image.get("digest") or next(
        (item.get("image-digest") for item in containers if item.get("image-digest")),
        None,
    )
    ref = image.get("ref")
    latest = latest_build_digest(records_root, repo)
    if digest is None and ref is None and latest is None:
        return None
    return {
        "ref": ref,
        "digest": digest,
        "verdict": image.get("verdict"),
        "newer-available": bool(latest and digest and latest != digest),
    }


def mothers_states(
    repo: Path,
    records_root: Path,
    primary: str | None = None,
) -> list[dict[str, Any]]:
    """mothers[] 数组: 每对一枚 (branch/dir/daemon/containers/...), 遵守只加不改名."""
    entries: list[dict[str, Any]] = []
    for path in repo_runtime_files(records_root, repo):
        data = load_runtime_tolerant(path) or {}
        branch, mother_dir = runtime_mother(data)
        mother_state = mother_state_from_runtime(repo, data)
        worktree_dirty = bool(mother_state["exists"] and mother_state.get("worktree-dirty"))
        pair_containers = [
            {"name": item.get("name"), "state": item.get("state"), "retired": bool(item.get("retired"))}
            for item in data.get("containers", [])
            if isinstance(item, dict)
        ]
        entries.append({
            "identity": path.stem,
            "branch": branch,
            "dir": str(mother_dir) if mother_dir else None,
            "exists": mother_state["exists"],
            "worktree-dirty": worktree_dirty,
            "runtime-stale": mother_state.get("runtime-stale", False),
            "stage": data.get("stage"),
            "config": {"swt-form": pair_config_matches(repo, mother_dir, branch)},
            "daemon": daemon_state(mother_dir, repo, data),
            "containers": pair_containers,
            "primary": path.stem == primary,
        })
    return entries


def pick_primary_runtime(
    runtimes: list[tuple[Path, dict[str, Any]]],
    containers: list[dict[str, Any]],
) -> tuple[Path, dict[str, Any]] | None:
    """顶层兼容字段的选取: 有运行中容器的对优先, 否则最近改动的 runtime."""
    running_names = {item.get("name") for item in containers if item.get("state") == "running"}
    for path, data in runtimes:
        for record in data.get("containers", []):
            if isinstance(record, dict) and not record.get("retired") and record.get("name") in running_names:
                return path, data
    if runtimes:
        return max(runtimes, key=lambda item: item[0].stat().st_mtime)
    return None


def build_state(
    repo: Path,
    records_root: Path,
    runtime_file: Path | None,
    runtime: dict[str, Any] | None,
    *,
    mother: dict[str, Any] | object,
    containers: list[dict[str, Any]] | object,
    daemon: dict[str, Any] | None | object,
    image: dict[str, Any] | None | object,
    network: dict[str, Any] | None | object,
) -> dict[str, Any]:
    """STATE (schema 2): 顶层字段 = 主对 (兼容旧消费方, 只加不改名);
    mothers[] = 全部对切片."""
    primary_branch, primary_mother = runtime_mother(runtime)
    observed_mother = mother_state_from_runtime(repo, runtime) if mother is _UNSET else mother
    observed_containers = (
        podman_container_state(repo, [data for _, data in load_repo_runtimes(records_root, repo)])
        if containers is _UNSET else containers
    )
    observed_daemon = daemon_state(primary_mother, repo, runtime) if daemon is _UNSET else daemon
    observed_image = image_state(records_root, repo, runtime, observed_containers) if image is _UNSET else image
    observed_network = network_state(runtime) if network is _UNSET else network
    state = empty_state(repo)
    state["mother"] = observed_mother
    state["config"]["swt-form"] = pair_config_matches(repo, primary_mother, primary_branch)
    state["containers"] = observed_containers
    state["daemon"] = observed_daemon
    state["image"] = observed_image
    state["network"] = observed_network
    runtime_display = (runtime or {}).get("display") if runtime else None
    state["display"] = runtime_display if isinstance(runtime_display, dict) else None
    if runtime:
        state["stage"] = runtime.get("stage")
    state["mothers"] = mothers_states(
        repo, records_root, primary=runtime_file.stem if runtime_file else None,
    )
    return state


def status(args: argparse.Namespace, repo: Path) -> int:
    require_command("podman")
    records_root = args.records_root.expanduser().resolve()
    runtimes = load_repo_runtimes(records_root, repo)
    containers = podman_container_state(repo, [data for _, data in runtimes])
    primary = pick_primary_runtime(runtimes, containers)
    if primary is not None:
        primary_file, primary_runtime = primary
        state = build_state(
            repo,
            records_root,
            primary_file,
            primary_runtime,
            mother=_UNSET,
            containers=containers,
            daemon=_UNSET,
            image=_UNSET,
            network=_UNSET,
        )
    else:
        state = build_state(
            repo,
            records_root,
            None,
            None,
            mother=_UNSET,
            containers=containers,
            daemon=None,
            image=None,
            network=None,
        )
    if not state["mother"]["exists"] and not runtimes and not state["containers"]:
        print_state(state, "[SWT] status: 什么都没有")
    else:
        print_state(state, "[SWT] status: 已完成只读盘点")
    print_status_web_lines(containers, read_confirmed_lan_address(records_root))
    print_status_headed_lines(containers, read_confirmed_lan_address(records_root))
    return 0


def display_check(args: argparse.Namespace, repo: Path | None) -> int:
    """诊断子命令 (D041): 对容器跑显示栈全量通道检查 (独立模块).
    退出码: 0 全过 / 1 有检查未过 / 2 传输层失败 — 诊断语义, 非 DECIDE.
    不改 runtime 状态, 不持锁."""
    name = args.name
    if not name:
        if repo is None:
            raise PreconditionError("display-check 需要 --name 或可推导主仓的 --repo/cwd")
        records_root = args.records_root.expanduser().resolve()
        active: list[dict[str, Any]] = []
        for _path, data in load_repo_runtimes(records_root, repo):
            active.extend(
                item for item in data.get("containers", [])
                if isinstance(item, dict) and item.get("name") and not item.get("retired")
            )
        if not active:
            raise PreconditionError("没有活动容器, 请用 --name 指定容器或先 birth")
        if len(active) > 1:
            names = ", ".join(str(item["name"]) for item in active)
            raise PreconditionError(f"有多个容器, 请使用 --name; 候选: {names}")
        name = str(active[0]["name"])
    if not container_has_swt_vnc(name):
        print("[SWT] display-check: 容器镜像未内置 swt-vnc (absent), 无通道可检查")
        return 1
    evidence = args.evidence_dir
    if evidence:
        evidence_arg = ["--evidence-dir", str(evidence)]
    else:
        evidence_arg = []
    result = run(
        ["uv", "run", "python", str(DISPLAY_SCRIPT), "verify", "--name", name, *evidence_arg],
        timeout=900,
    )
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def create_receipt(
    records_root: Path,
    identity: str,
    kind: str,
    fingerprint: dict[str, Any],
    options: list[str],
) -> Path:
    decisions = records_root.expanduser().resolve() / "runtime" / identity / "decisions"
    decisions.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    existing = sorted(decisions.glob(f"d-{stamp}-*.json"))
    decision_id = f"d-{stamp}-{len(existing) + 1:03d}"
    path = decisions / f"{decision_id}.json"
    payload = {
        "id": decision_id,
        "kind": kind,
        "fingerprint": fingerprint,
        "options": options,
        "created-at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_write_json(path, payload)
    return path


def consume_receipt(
    records_root: Path,
    identity: str,
    kind: str,
    fingerprint: dict[str, Any],
) -> bool:
    decisions = records_root.expanduser().resolve() / "runtime" / identity / "decisions"
    if not decisions.is_dir():
        return False
    for path in sorted(decisions.glob("d-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("kind") != kind:
            continue
        if canonical_json(payload.get("fingerprint")) != canonical_json(fingerprint):
            continue
        try:
            path.unlink()
        except FileNotFoundError:
            return False
        return True
    return False


def acquire_lock(repo: Path, records_root: Path) -> Any:
    # 仓级锁: 跨对资源 (主仓 config 迁移等) 共享一把, 文件名与旧 scheme identity 同构造
    path = (records_root.expanduser().resolve() / "runtime" / f"{repo_scope_identity(repo)}.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.seek(0)
        holder = handle.read().strip()
        handle.close()
        detail = f"LOCKED 当前主仓已有变更操作{f' (pid={holder})' if holder else ''}"
        raise PreconditionError(detail) from exc
    handle.seek(0)
    handle.truncate()
    handle.write(str(os.getpid()))
    handle.flush()
    return handle


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
        require_command("git")
        if args.command == "birth":
            for command in ("podman", "nft", "ssh", "ssh-keygen", "uv"):
                require_command(command)
            validate_git_hide_refs_syntax()
        if args.command == "status":
            return status(args, resolve_repo(args.repo))
        if args.command == "display-check":
            repo = None if args.name else resolve_repo(args.repo)
            return display_check(args, repo)
        if args.command == "enroll-device-key":
            require_command("podman")
            return cmd_enroll_device_key(args)
        repo = resolve_repo(args.repo)
        lock = acquire_lock(repo, args.records_root)
        try:
            if args.command == "birth":
                return birth(args, repo)
            if args.command == "resume":
                for command in MUTATING_COMMANDS:
                    require_command(command)
                return resume(args, repo)
            if args.command == "terminate":
                for command in MUTATING_COMMANDS:
                    require_command(command)
                return terminate(args, repo)
            raise PreconditionError(f"NOT-IMPLEMENTED {args.command}")
        finally:
            lock.close()
    except SwtError as exc:
        print(f"{exc.tag} {exc.message}", file=sys.stderr)
        return exc.code
    except OSError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
