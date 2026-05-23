#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
usage:
  status.sh [path]

Read-only check for standard layout:
  <workspace>/<project>/<project>-master
  <workspace>/<project>/<project>-<source-slug>-<branch-slug>
EOF
}

abs_path() {
  local p="$1"
  if [[ -e "$p" ]]; then
    (cd "$p" 2>/dev/null && pwd -P) || (cd "$(dirname "$p")" && printf '%s/%s\n' "$(pwd -P)" "$(basename "$p")")
  else
    case "$p" in
      /*) printf '%s\n' "$p" ;;
      *) printf '%s/%s\n' "$(pwd -P)" "$p" ;;
    esac
  fi
}

origin_project_from() {
  local dir="$1"
  local url name
  url="$(git -C "$dir" config --get remote.origin.url 2>/dev/null || true)"
  [[ -n "$url" ]] || return 1
  url="${url%.git}"
  url="${url%/}"
  name="${url##*/}"
  name="${name##*:}"
  [[ -n "$name" ]] || return 1
  printf '%s\n' "$name"
}

is_git_worktree() {
  git -C "$1" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

print_worktree() {
  local path="$1"
  echo "[worktree]"
  echo "path=$path"
  if [[ ! -d "$path" ]]; then
    echo "exists=false"
    echo "stale=true"
    echo
    return 0
  fi
  echo "exists=true"
  echo "stale=false"
  if ! is_git_worktree "$path"; then
    echo "git=false"
    echo
    return 0
  fi
  local branch head gitdir status dirty count
  branch="$(git -C "$path" branch --show-current 2>/dev/null || true)"
  head="$(git -C "$path" rev-parse --short HEAD 2>/dev/null || true)"
  gitdir="$(git -C "$path" rev-parse --git-dir 2>/dev/null || true)"
  status="$(git -C "$path" status --short --branch --untracked-files=all 2>/dev/null || true)"
  count="$(printf '%s\n' "$status" | sed '/^## /d; /^$/d' | wc -l | tr -d ' ')"
  if [[ "$count" == "0" ]]; then dirty=false; else dirty=true; fi
  echo "git=true"
  echo "branch=$branch"
  echo "head=$head"
  echo "gitdir=$gitdir"
  echo "dirty=$dirty"
  echo "status_count=$count"
  echo "status_begin"
  printf '%s\n' "$status"
  echo "status_end"
  echo
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

input="${1:-.}"
input_abs="$(abs_path "$input")"

echo "input=$input_abs"

# Determine a git root if the input is inside any worktree.
git_root=""
if is_git_worktree "$input_abs"; then
  git_root="$(git -C "$input_abs" rev-parse --show-toplevel)"
fi

project=""
project_dir=""
main=""
layout="nonstandard"
reason=""
repo_for_list=""

if [[ -n "$git_root" ]]; then
  if project="$(origin_project_from "$git_root")"; then
    project_dir="$(dirname "$git_root")"
    main="$project_dir/$project-master"
    repo_for_list="$git_root"
    if [[ "$(basename "$project_dir")" == "$project" && -d "$main" && "$(basename "$git_root")" == "$project"-* ]]; then
      layout="standard"
      reason="matched_origin_project_parent_and_main"
    else
      reason="git_root_not_in_standard_project_layout"
    fi
  else
    reason="missing_or_unparseable_origin"
    repo_for_list="$git_root"
  fi
else
  # Maybe input is the project directory itself: <workspace>/<project>.
  candidate_project="$(basename "$input_abs")"
  candidate_main="$input_abs/$candidate_project-master"
  if [[ -d "$candidate_main" ]] && is_git_worktree "$candidate_main"; then
    if project_from_main="$(origin_project_from "$candidate_main")"; then
      project="$project_from_main"
      project_dir="$input_abs"
      main="$project_dir/$project-master"
      repo_for_list="$main"
      if [[ "$candidate_project" == "$project" && -d "$main" ]]; then
        layout="standard"
        reason="input_is_standard_project_dir"
      else
        reason="project_dir_name_does_not_match_origin_project"
      fi
    else
      reason="main_missing_or_unparseable_origin"
      repo_for_list="$candidate_main"
    fi
  else
    reason="not_inside_git_worktree_or_standard_project_dir"
  fi
fi

workspace=""
if [[ -n "$project_dir" ]]; then
  workspace="$(dirname "$project_dir")"
fi

echo "layout=$layout"
echo "reason=$reason"
echo "project=$project"
echo "workspace=$workspace"
echo "project_dir=$project_dir"
echo "main=$main"
echo "git_root=$git_root"

if [[ -n "$repo_for_list" ]] && is_git_worktree "$repo_for_list"; then
  echo
  echo "[worktree_list]"
  git -C "$repo_for_list" worktree list --porcelain
  echo

  mapfile -t paths < <(git -C "$repo_for_list" worktree list --porcelain | awk '/^worktree /{sub(/^worktree /,""); print}')
  for wt in "${paths[@]}"; do
    if [[ "$layout" == "standard" ]]; then
      base_name="$(basename "$wt")"
      parent_name="$(basename "$(dirname "$wt")")"
      if [[ "$parent_name" != "$project" || "$base_name" != "$project"-* ]]; then
        echo "[layout_warning]"
        echo "path=$wt"
        echo "warning=registered_worktree_outside_standard_project_dir_or_name"
        echo
      fi
    fi
    print_worktree "$wt"
  done
else
  echo
  echo "worktree_list=unavailable"
fi
