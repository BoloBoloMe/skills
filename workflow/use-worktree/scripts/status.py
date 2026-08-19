"""Read-only inspection for the standard local git worktree layout."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", newline="\n")

USAGE = """用法:
  status.py [路径]

只读检查标准 worktree 布局:
  <workspace>/<project>/<project>-<主分支名>
  <workspace>/<project>/<project>-<source-slug>-<branch-slug>

说明:
  正常输出中的 section header, key=value 字段和状态 token 保持英文, 便于脚本和 agent 解析.
"""


def run_git(path: str | Path, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(path), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=check,
    )


def git_text(path: str | Path, *args: str) -> str:
    result = run_git(path, *args)
    return result.stdout.rstrip("\n") if result.returncode == 0 else ""


def is_git_worktree(path: str | Path) -> bool:
    return run_git(path, "rev-parse", "--is-inside-work-tree").returncode == 0


def abs_path(value: str) -> str:
    p = Path(value)
    try:
        if p.exists():
            return str(p.resolve())
        if p.is_absolute():
            return str(p)
        return str((Path.cwd() / p).resolve(strict=False))
    except OSError:
        if p.is_absolute():
            return str(p)
        return str(Path.cwd() / p)


def dirname(path: str) -> str:
    return str(Path(path).parent)


def basename(path: str) -> str:
    return Path(path).name


def origin_project_from(path: str | Path) -> str | None:
    url = git_text(path, "config", "--get", "remote.origin.url")
    if not url:
        return None
    url = url.removesuffix(".git").rstrip("/")
    name = url.rsplit("/", 1)[-1].rsplit(":", 1)[-1]
    return name or None


def main_worktree_branch(repo: str | Path) -> str:
    """Checked-out branch of the main worktree; empty when detached or unreadable."""
    porcelain = git_text(repo, "worktree", "list", "--porcelain")
    for line in porcelain.splitlines():
        if line.startswith("worktree "):
            return git_text(line.removeprefix("worktree "), "branch", "--show-current")
    return ""


def infer_main_branch(repo: str | Path) -> str:
    """Infer main branch from origin/HEAD, common names, or main worktree; empty when undetectable."""
    head_ref = git_text(repo, "symbolic-ref", "refs/remotes/origin/HEAD")
    if head_ref:
        branch = head_ref.rsplit("/", 1)[-1]
        if branch:
            return branch
    for candidate in ("main", "master", "trunk"):
        if run_git(repo, "rev-parse", "--verify", f"refs/heads/{candidate}").returncode == 0:
            return candidate
    return main_worktree_branch(repo)


def print_worktree(path: str) -> None:
    print("[worktree]")
    print(f"path={path}")
    if not Path(path).is_dir():
        print("exists=false")
        print("stale=true")
        print()
        return

    print("exists=true")
    print("stale=false")
    if not is_git_worktree(path):
        print("git=false")
        print()
        return

    branch = git_text(path, "branch", "--show-current")
    head = git_text(path, "rev-parse", "--short", "HEAD")
    gitdir = git_text(path, "rev-parse", "--git-dir")
    status = git_text(path, "status", "--short", "--branch", "--untracked-files=all")
    status_lines = status.splitlines() if status else []
    count = sum(1 for line in status_lines if line and not line.startswith("## "))
    dirty = "false" if count == 0 else "true"

    print("git=true")
    print(f"branch={branch}")
    print(f"head={head}")
    print(f"gitdir={gitdir}")
    print(f"dirty={dirty}")
    print(f"status_count={count}")
    print("status_begin")
    if status:
        print(status)
    print("status_end")
    print()


def worktree_paths(repo: str) -> list[str]:
    porcelain = git_text(repo, "worktree", "list", "--porcelain")
    return [line.removeprefix("worktree ") for line in porcelain.splitlines() if line.startswith("worktree ")]


def main(argv: list[str]) -> int:
    if argv and argv[0] in {"-h", "--help"}:
        print(USAGE, end="")
        return 0

    input_abs = abs_path(argv[0] if argv else ".")
    print(f"input={input_abs}")

    git_root = ""
    if is_git_worktree(input_abs):
        git_root = git_text(input_abs, "rev-parse", "--show-toplevel")

    project = ""
    project_dir = ""
    main_path = ""
    layout = "nonstandard"
    reason = ""
    repo_for_list = ""

    if git_root:
        inferred = origin_project_from(git_root)
        if inferred:
            project = inferred
            project_dir = dirname(git_root)
            main_branch = infer_main_branch(git_root)
            main_path = str(Path(project_dir) / f"{project}-{main_branch}") if main_branch else ""
            repo_for_list = git_root
            if (
                main_path
                and basename(project_dir) == project
                and Path(main_path).is_dir()
                and basename(git_root).startswith(f"{project}-")
            ):
                layout = "standard"
                reason = "matched_origin_project_parent_and_main"
            elif not main_branch:
                reason = "main_branch_unknown"
            else:
                reason = "git_root_not_in_standard_project_layout"
        else:
            reason = "missing_or_unparseable_origin"
            repo_for_list = git_root
    else:
        candidate_project = basename(input_abs)
        candidate_main = ""
        try:
            children = sorted(Path(input_abs).iterdir())
        except OSError:
            children = []
        for child in children:
            if (
                child.is_dir()
                and child.name.startswith(f"{candidate_project}-")
                and (child / ".git").is_dir()
                and is_git_worktree(child)
            ):
                candidate_main = str(child)
                break
        if candidate_main:
            inferred = origin_project_from(candidate_main)
            if inferred:
                project = inferred
                project_dir = input_abs
                main_branch = infer_main_branch(candidate_main)
                main_path = str(Path(project_dir) / f"{project}-{main_branch}") if main_branch else ""
                repo_for_list = main_path if main_path and Path(main_path).is_dir() else candidate_main
                if not main_branch:
                    reason = "main_branch_unknown"
                elif candidate_project == project and Path(main_path).is_dir():
                    layout = "standard"
                    reason = "input_is_standard_project_dir"
                elif candidate_project != project:
                    reason = "project_dir_name_does_not_match_origin_project"
                else:
                    reason = "main_worktree_path_missing"
            else:
                reason = "main_missing_or_unparseable_origin"
                repo_for_list = candidate_main
        else:
            reason = "not_inside_git_worktree_or_standard_project_dir"

    workspace = dirname(project_dir) if project_dir else ""

    print(f"layout={layout}")
    print(f"reason={reason}")
    print(f"project={project}")
    print(f"workspace={workspace}")
    print(f"project_dir={project_dir}")
    print(f"main={main_path}")
    print(f"git_root={git_root}")

    if repo_for_list and is_git_worktree(repo_for_list):
        print()
        print("[worktree_list]")
        porcelain = git_text(repo_for_list, "worktree", "list", "--porcelain")
        if porcelain:
            print(porcelain)
        print()

        for wt in worktree_paths(repo_for_list):
            if layout == "standard":
                base_name = basename(wt)
                parent_name = basename(dirname(wt))
                if parent_name != project or not base_name.startswith(f"{project}-"):
                    print("[layout_warning]")
                    print(f"path={wt}")
                    print("warning=registered_worktree_outside_standard_project_dir_or_name")
                    print()
            print_worktree(wt)
    else:
        print()
        print("worktree_list=unavailable")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
