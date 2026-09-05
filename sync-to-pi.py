#!/usr/bin/env python3
"""pi skill sync
----------------
问答式同步脚本: 将本仓库中的 skills 同步到 ~/.agents/skills/, extensions/pi/AGENTS.md 同步到 pi agent 目录.

用法:
    python sync-to-pi.py

跨平台: Windows / Linux / macOS, 纯 Python 标准库.
"""

import sys
import shutil
from pathlib import Path


# ============================================================================
# 同步时忽略的生成/运行时文件
# ============================================================================
_SYNC_IGNORE = shutil.ignore_patterns(
    # Python 缓存 & 虚拟环境
    "__pycache__", "*.pyc", "*.pyo",
    ".venv", "venv",
    # setuptools / 构建产物
    "*.egg-info", "*.egg",
    # pytest
    ".pytest_cache",
    # 测试目录 (agent 运行不需要; ignore_patterns 按 basename 全层级匹配,
    # 同步范围 (general/workflow/pi) 内无需要保留的同名目录)
    "tests",
    # 包管理器锁文件 (从 pyproject.toml 可重建)
    "uv.lock", "poetry.lock", "Pipfile.lock",
    # macOS
    ".DS_Store",
    # Node
    "node_modules",
)


# ============================================================================
# Windows terminal: enable ANSI escape code support (VT processing)
# ============================================================================
def _enable_vt() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        STD_OUTPUT_HANDLE = -11
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        mode = ctypes.c_uint32()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        mode.value |= ENABLE_VIRTUAL_TERMINAL_PROCESSING
        kernel32.SetConsoleMode(handle, mode.value)
    except Exception:
        pass


_enable_vt()


# ============================================================================
# ANSI color helpers
# ============================================================================
class _C:
    RST = "\033[0m"
    BLD = "\033[1m"
    CYN = "\033[36m"
    BLU = "\033[34m"
    MAG = "\033[35m"
    GRN = "\033[32m"
    RED = "\033[31m"
    YEL = "\033[33m"


def _ct(text: str, *codes: str) -> str:
    return "".join(codes) + text + _C.RST


# 语义色
Q = lambda t: _ct(t, _C.BLD, _C.CYN)   # 问题 / 提示符
SRC = lambda t: _ct(t, _C.BLU)          # 源路径
DST = lambda t: _ct(t, _C.MAG)          # 目标路径
SYNC = lambda t: _ct(t, _C.GRN)         # 同步操作
SKIP = lambda t: _ct(t, _C.RED)         # 跳过操作
SEL = lambda t: _ct(t, _C.YEL)          # 选择操作
CNF = lambda t: _ct(t, _C.BLD, _C.YEL)  # 确认提示
OK = lambda t: _ct(t, _C.GRN)           # 成功
ERR = lambda t: _ct(t, _C.RED)          # 失败 / 警告


# ============================================================================
# 用户输入
# ============================================================================
def _ask(options: dict[str, str], default: str, prompt: str = "") -> str:
    """询问用户从 options 中选一项. 返回 key (单字符). Enter 返回 default."""
    opts_text = "  ".join(options.values())
    line = f"{prompt}  {opts_text}? (默认={default}) "
    while True:
        raw = input(line).strip().lower()
        if raw == "":
            return default
        if raw in options:
            return raw
        print(ERR(f"  无效, 请输入 {'/'.join(options.keys())}"))


def _ask_yn(prompt: str) -> bool:
    while True:
        raw = input(prompt + " [y/N] ").strip().lower()
        if raw in ("", "n"):
            return False
        if raw == "y":
            return True


# ============================================================================
# pi 目录探测
# ============================================================================
def _looks_like_pi_dir(path: Path) -> bool:
    return (
        (path / "settings.json").exists()
        or (path / "skills").is_dir()
        or (path / "extensions").is_dir()
    )


def detect_pi_dir() -> Path | None:
    """找到并确认 pi agent 根目录."""
    default = Path.home() / ".pi" / "agent"

    if _looks_like_pi_dir(default):
        print(Q(f"\n检测到 pi agent 目录: {default}"))
        if _ask_yn(CNF("确认为 pi agent 根目录?")):
            return default
        print()
    else:
        print(Q(f"\n默认位置 {default} 下未找到 pi agent 目录"))

    while True:
        raw = input(Q("请输入 pi agent 根目录路径: ")).strip()
        if not raw:
            print(ERR("路径不能为空"))
            continue
        path = Path(raw).expanduser().resolve()
        if _looks_like_pi_dir(path):
            if _ask_yn(CNF(f"确认 {path} 为 pi agent 根目录?")):
                return path
        else:
            print(ERR(f"{path} 不含 settings.json / skills/ / extensions/ 任一, 不像 pi agent 目录"))
            if _ask_yn("仍要使用该目录?"):
                return path
        # 继续循环让用户重新输入


# ============================================================================
# 同步计划项
# ============================================================================
class PlanItem:
    __slots__ = ("src", "dst", "label", "is_dir")

    def __init__(self, src: Path, dst: Path, label: str, is_dir: bool):
        self.src = src
        self.dst = dst
        self.label = label
        self.is_dir = is_dir


# ============================================================================
# 交互询问
# ============================================================================
def _query_top_dir(
    repo_root: Path,
    name: str,
    src: Path,
    dst_parent: Path,
    *,
    flatten: bool = False,
) -> list[PlanItem]:
    """顶层目录: 同步 / 跳过 / 选择.

    flatten=True  : 子项直接放 dst_parent 下 (如 general/ → skills/).
    flatten=False : src 目录整体放 dst_parent 下 (如 pi/extensions/ → extensions/).
    """
    if flatten:
        display_dst = dst_parent
    else:
        display_dst = dst_parent / src.name

    print()
    print(Q(f"[{name}]") + f"  {SRC(str(src.relative_to(repo_root)))}  →  {DST(str(display_dst))}")

    sub_items: list[Path] = sorted(src.iterdir()) if src.is_dir() else []

    opts = {"s": SYNC("[s]同步"), "k": SKIP("[k]跳过"), "x": SEL("[x]选择")}
    choice = _ask(opts, default="k", prompt=" ")

    if choice == "s":
        if flatten:
            return [
                PlanItem(sub, dst_parent / sub.name, str(sub.relative_to(repo_root)), sub.is_dir())
                for sub in sub_items
            ]
        else:
            return [PlanItem(src, display_dst, str(src.relative_to(repo_root)), True)]
    elif choice == "x":
        plan: list[PlanItem] = []
        for sub in sub_items:
            plan.extend(_query_sub(repo_root, sub, display_dst))
        return plan
    else:
        return []


def _query_top_file(repo_root: Path, name: str, src: Path, dst: Path) -> list[PlanItem]:
    """顶层单文件: 同步 / 跳过."""
    print()
    print(Q(f"[{name}]") + f"  {SRC(str(src.relative_to(repo_root)))}  →  {DST(str(dst))}")

    opts = {"s": SYNC("[s]同步"), "k": SKIP("[k]跳过")}
    choice = _ask(opts, default="k", prompt=" ")

    if choice == "s":
        return [PlanItem(src, dst, str(src.relative_to(repo_root)), False)]
    return []


def _query_sub(repo_root: Path, src: Path, dst_parent: Path) -> list[PlanItem]:
    """子项 (skill 目录 / 文件): 同步 / 跳过."""
    dst = dst_parent / src.name
    is_dir = src.is_dir()

    print()
    print(f"  {SRC(str(src.relative_to(repo_root)))}  →  {DST(str(dst))}")

    opts = {"s": SYNC("[s]同步"), "k": SKIP("[k]跳过")}
    choice = _ask(opts, default="k", prompt="  ")

    if choice == "s":
        return [PlanItem(src, dst, str(src.relative_to(repo_root)), is_dir)]
    return []


# ============================================================================
# 执行同步
# ============================================================================
def _clear_skills(skills_dir: Path) -> None:
    """删除 skills_dir 中的全部内容, 但保留目录本身."""
    if skills_dir.is_symlink():
        raise OSError(f"拒绝清空符号链接目录: {skills_dir}")
    if skills_dir.exists() and not skills_dir.is_dir():
        raise NotADirectoryError(f"目标不是目录: {skills_dir}")

    skills_dir.mkdir(parents=True, exist_ok=True)
    for child in skills_dir.iterdir():
        if child.is_symlink() or child.is_file():
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def _merge_models(src: Path, dst: Path) -> int:
    """把 src 的 providers 合并到 dst models.json.

    provider 级整体覆盖 (源中每个 provider 是完整定义).
    保留 dst 中源未提及的 provider. 写前备份 .bak.
    返回合并的 provider 数.
    """
    import json

    file_cfg = json.loads(src.read_text(encoding="utf-8"))
    file_providers = file_cfg.get("providers", {})
    if not file_providers:
        raise ValueError(f"{src} 无 providers")

    if dst.exists():
        backup = dst.with_name(dst.name + ".bak")
        shutil.copy2(dst, backup)
        models = json.loads(dst.read_text(encoding="utf-8"))
    else:
        backup = None
        models = {}
    models.setdefault("providers", {})
    models["providers"].update(file_providers)

    dst.write_text(json.dumps(models, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OK(f"  \u2713 合并 {len(file_providers)} 个 provider → {dst}"))
    if backup:
        print(OK(f"    备份: {backup}"))
    return len(file_providers)


def execute_plan(plan: list[PlanItem], clear_skills_dir: Path | None = None, merge_models: tuple[Path, Path] | None = None) -> None:
    print()
    print(Q("开始执行 ..."))

    ok_count = 0
    fail_count = 0

    if clear_skills_dir is not None:
        try:
            _clear_skills(clear_skills_dir)
            print(OK(f"  \u2713 已清空 {clear_skills_dir}"))
            ok_count += 1
        except Exception as e:
            print(ERR(f"  \u2717 清空 {clear_skills_dir} 失败: {e}"))
            print(ERR("已停止, 未执行后续同步."))
            return

    for item in plan:
        try:
            if item.is_dir:
                if item.dst.exists():
                    shutil.rmtree(item.dst)
                shutil.copytree(item.src, item.dst, ignore=_SYNC_IGNORE)
            else:
                item.dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item.src, item.dst)
            print(OK(f"  \u2713 {item.label}"))
            ok_count += 1
        except Exception as e:
            print(ERR(f"  \u2717 {item.label}: {e}"))
            fail_count += 1

    if merge_models is not None:
        src, dst = merge_models
        try:
            _merge_models(src, dst)
            ok_count += 1
        except Exception as e:
            print(ERR(f"  \u2717 合并模型配置失败: {e}"))
            fail_count += 1

    print()
    if fail_count == 0:
        print(OK(f"全部完成: {ok_count} 项操作成功"))
    else:
        print(Q(f"完成: {ok_count} 成功, {fail_count} 失败"))


# ============================================================================
# 主流程
# ============================================================================
def main() -> None:
    repo_root = Path(__file__).resolve().parent

    print(_ct("pi skill sync", _C.BLD))
    print(f"仓库根目录: {SRC(str(repo_root))}")
    print(Q("本脚本将仓库中的 skills 同步到 ~/.agents/skills/, extensions / pi/AGENTS.md 同步到 pi agent 目录"))
    print(SKIP("注意: 目标路径已有内容将被直接覆盖"))
    print(SKIP("首次使用 general/access-web 或 general/present 前, 按其 SKILL.md 的 Setup 完成依赖安装 (uv sync + playwright install chromium)"))

    # ── 1. 探测 pi 目录 ──────────────────────────────────────────────
    pi_dir = detect_pi_dir()
    if pi_dir is None:
        print(ERR("\n未找到 pi agent 目录, 退出."))
        sys.exit(1)

    pi_dir = pi_dir.resolve()
    print()
    print(Q(f"pi agent 根目录: {pi_dir}"))

    # ── 2. 清空选项 ──────────────────────────────────────────────────
    skills_dir = Path.home() / ".agents" / "skills"
    clear_skills = _ask_yn(CNF(f"清空 {skills_dir} 下的所有旧 skills?"))
    if clear_skills:
        print(ERR("已选择永久删除全部旧 skills, 操作将在最终确认后执行."))

    # ── 3. 逐项询问 ──────────────────────────────────────────────────
    plan: list[PlanItem] = []

    # pi/AGENTS.md (单文件)
    plan.extend(
        _query_top_file(
            repo_root,
            "pi/AGENTS.md",
            repo_root / "pi" / "AGENTS.md",
            pi_dir / "AGENTS.md",
        )
    )

    # pi/herdr-pi.md (单文件)
    plan.extend(
        _query_top_file(
            repo_root,
            "pi/herdr-pi.md",
            repo_root / "pi" / "herdr-pi.md",
            pi_dir / "herdr-pi.md",
        )
    )

    # pi/keybindings.json (单文件)
    plan.extend(
        _query_top_file(
            repo_root,
            "pi/keybindings.json",
            repo_root / "pi" / "keybindings.json",
            pi_dir / "keybindings.json",
        )
    )

    # general/ → skills/ (flatten: 跳过 general 中间目录名)
    plan.extend(
        _query_top_dir(
            repo_root,
            "general/",
            repo_root / "general",
            skills_dir,
            flatten=True,
        )
    )

    # pi/extensions/ → extensions/ (保持目录名)
    plan.extend(
        _query_top_dir(
            repo_root,
            "pi/extensions/",
            repo_root / "pi" / "extensions",
            pi_dir,
        )
    )

    # workflow/ → skills/ (flatten)
    plan.extend(
        _query_top_dir(
            repo_root,
            "workflow/",
            repo_root / "workflow",
            skills_dir,
            flatten=True,
        )
    )

    # ── 3.5 模型配置同步选项 ────────────────────────────────────────
    models_src = repo_root / "pi" / "models.json"
    merge_models = False
    if models_src.exists():
        print()
        merge_models = _ask_yn(CNF(
            f"同步模型配置 ({SRC(str(models_src.relative_to(repo_root)))}) → {DST(str(pi_dir / 'models.json'))}? (provider 级覆盖, 写前备份)"
        ))
    else:
        print(ERR(f"\n模型配置源不存在: {models_src}, 跳过同步选项"))

    # ── 4. 展示计划, 确认 ────────────────────────────────────────────
    if not plan and not clear_skills and not merge_models:
        print()
        print(Q("没有要执行的操作, 退出."))
        return

    print()
    print(Q("=" * 54))
    print(Q("执行计划:"))
    if clear_skills:
        print(ERR(f"  [清空] 永久删除 {skills_dir} 下的全部内容"))
    for item in plan:
        print(f"  {SRC(item.label)}  →  {DST(str(item.dst))}")
    if merge_models:
        print(f"  {SYNC('[合并]')} 模型 providers  →  {DST(str(pi_dir / 'models.json'))}")
    print(Q("=" * 54))

    if not _ask_yn(CNF("确认执行?")):
        print(SKIP("已取消."))
        return

    # ── 5. 执行 ──────────────────────────────────────────────────────
    execute_plan(
        plan,
        skills_dir if clear_skills else None,
        (models_src, pi_dir / "models.json") if merge_models else None,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + _ct("已取消.", _C.RED))
    except EOFError:
        print("\n" + _ct("输入结束, 退出.", _C.RED))
