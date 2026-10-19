#!/usr/bin/env bash
# 本轮验收脚本: 只读产品代码, 只在本证据目录内写输出.
cd "$(dirname "$0")/../../../.." || exit 99
EVD="docs/changes/tool-cli/evidence-93ba124-20261019"

rec() { # rec <outfile> <cmd...>
  local out="$1"; shift
  {
    echo "\$ $*"
    "$@"
    echo "[exit=$?]"
  } > "$EVD/$out" 2>&1
}

# 01 版本前提
rec 01-version/rev-parse.txt git rev-parse HEAD
rec 01-version/status.txt git status --porcelain=v1 --untracked-files=all
rec 01-version/log.txt git log --oneline -3
rec 01-version/diff-name-status-prev.txt git diff --name-status c6a3745 HEAD
rec 01-version/head-tracked-files.txt git ls-tree -r --name-only HEAD

# 02 验收场景 (逐条实跑, 保留原文 stdout/stderr/exit)
rec 02-scenarios/AC-001-1.txt python3 tool.py greet --name Ada
rec 02-scenarios/AC-001-2.txt python3 tool.py greet --name Ada --shout
rec 02-scenarios/AC-002-1.txt python3 tool.py count --file notes.txt
rec 02-scenarios/AC-002-2.txt python3 tool.py count --file notes.txt --chars
rec 02-scenarios/AC-003-1.txt python3 tool.py export --name Ada
rec 02-scenarios/notes-bytes.txt od -c notes.txt

# 03 BR-002 静态材料核对
rec 03-audit-br002/diff-deps-build.txt git diff c6a3745 HEAD -- deps.txt deps.lock build.sh prepare.sh tools/build_manifest.py
rec 03-audit-br002/blob-hashes-both-commits.txt git show --no-patch --format='%H %s' c6a3745 HEAD
for f in deps.txt deps.lock build.sh prepare.sh tools/build_manifest.py; do
  rec "03-audit-br002/hash-$(echo "$f" | tr '/' '_').txt" bash -c "git rev-parse c6a3745:$f HEAD:$f; sha256sum $f"
done

# 04 项目自带检查 (TECHNICAL 操作线索, 非产品判据)
rec 04-tests/pytest.txt python3 -m pytest -q
rec 04-tests/build-sh.txt bash build.sh
rec 04-tests/prepare-sh.txt bash prepare.sh
rec 04-tests/dist-app.txt cat dist/app.txt
