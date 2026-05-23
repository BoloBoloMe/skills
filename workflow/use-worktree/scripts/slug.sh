#!/usr/bin/env bash
set -euo pipefail

MAX_LEN=60
HASH_LEN=7
PREFIX_LEN=$((MAX_LEN - HASH_LEN - 1))

usage() {
  cat <<'EOF'
usage:
  slug.sh <branch>
  slug.sh <project> <source-branch> <target-branch>

rules:
  Windows-illegal path chars and control chars -> -
  space -> _
  preserve Chinese/Unicode
  max slug length 60; overlong slug -> first 52 chars + '-' + sha1[0:7]
EOF
}

hash7() {
  if command -v sha1sum >/dev/null 2>&1; then
    printf '%s' "$1" | sha1sum | awk '{print substr($1,1,7)}'
  elif command -v shasum >/dev/null 2>&1; then
    printf '%s' "$1" | shasum -a 1 | awk '{print substr($1,1,7)}'
  else
    printf '%s' "$1" | git hash-object --stdin | cut -c1-7
  fi
}

sanitize() {
  local raw="$1"
  if command -v perl >/dev/null 2>&1; then
    printf '%s' "$raw" | perl -CS -Mutf8 -pe 's/^[ .]+//; s/[ .]+$//g; s/[\/\\:\*\?"<>|\x00-\x1F\x7F]+/-/g; s/ /_/g; s/-+/-/g; s/^[.]+//; s/[.]+$//g'
  else
    printf '%s' "$raw" \
      | sed -E 's/^[ .]+//; s/[ .]+$//; s#[/\\:*?"<>|]+#-#g; s/ /_/g; s/-+/-/g; s/^[.]+//; s/[.]+$//'
  fi
}

strlen() {
  if command -v perl >/dev/null 2>&1; then
    printf '%s' "$1" | perl -CS -Mutf8 -e 'local $/; $s=<STDIN>; print length($s)'
  else
    local s="$1"
    printf '%s' "${#s}"
  fi
}

substr_prefix() {
  local s="$1"
  local n="$2"
  if command -v perl >/dev/null 2>&1; then
    printf '%s' "$s" | perl -CS -Mutf8 -e '$n=shift; local $/; $s=<STDIN>; print substr($s,0,$n)' "$n"
  else
    printf '%s' "${s:0:n}"
  fi
}

slug_one() {
  local branch="$1"
  local clean len h prefix
  clean="$(sanitize "$branch")"
  if [[ -z "$clean" ]]; then
    clean="branch"
  fi
  len="$(strlen "$clean")"
  if (( len > MAX_LEN )); then
    h="$(hash7 "$branch")"
    prefix="$(substr_prefix "$clean" "$PREFIX_LEN")"
    prefix="$(sanitize "$prefix")"
    prefix="${prefix%-}"
    if [[ -z "$prefix" ]]; then
      clean="$h"
    else
      clean="$prefix-$h"
    fi
  fi
  printf '%s' "$clean"
}

if [[ $# -eq 0 || "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -eq 1 ]]; then
  branch="$1"
  slug="$(slug_one "$branch")"
  echo "branch=$branch"
  echo "slug=$slug"
  echo "length=$(strlen "$slug")"
  exit 0
fi

if [[ $# -eq 3 ]]; then
  project="$1"
  source_branch="$2"
  target_branch="$3"
  source_slug="$(slug_one "$source_branch")"
  target_slug="$(slug_one "$target_branch")"
  dir="$project-$source_slug-$target_slug"
  echo "project=$project"
  echo "source_branch=$source_branch"
  echo "source_slug=$source_slug"
  echo "target_branch=$target_branch"
  echo "target_slug=$target_slug"
  echo "dir=$dir"
  exit 0
fi

usage >&2
exit 2
