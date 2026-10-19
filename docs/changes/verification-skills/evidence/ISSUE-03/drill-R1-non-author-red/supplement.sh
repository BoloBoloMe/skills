#!/usr/bin/env bash
# 补充证据: 版本前提复核, 输出字节复核, 依赖哈希复核, 非产品检查.
cd "$(dirname "$0")/../../../.." || exit 99
E=docs/changes/tool-cli/evidence-93ba124-20261019

{
  echo '$ git status --porcelain=v1 --untracked-files=all -- . :(exclude)docs/changes/tool-cli/evidence-93ba124-20261019'
  git status --porcelain=v1 --untracked-files=all -- . ':(exclude)docs/changes/tool-cli/evidence-93ba124-20261019'
  echo "[exit=$?]"
  echo '# 排除项即本轮证据目录; 输出为空表示已跟踪源码/配置/测试无改动, 也无证据目录外的未跟踪产品文件.'
} > "$E/01-version/status-clean-excluding-evidence.txt" 2>&1

{
  echo '$ git status --porcelain=v1 --untracked-files=all'
  git status --porcelain=v1 --untracked-files=all
  echo "[exit=$?]"
} > "$E/01-version/status-all-untracked.txt" 2>&1

{
  echo '$ python3 -VV ; uv --version'
  python3 -VV
  uv --version
  echo "[exit=$?]"
} > "$E/04-tests/env.txt" 2>&1

{
  echo '$ timeout 120 uv run --no-project --with pytest python -m pytest -q'
  timeout 120 uv run --no-project --with pytest python -m pytest -q 2>&1
  echo "[exit=$?]"
  echo '# 非产品判据: TECHNICAL.md 的操作线索; --with pytest 仅临时环境, 不改项目依赖文件.'
} > "$E/04-tests/pytest-uv.txt" 2>&1

{
  echo '$ git diff --stat c6a3745 HEAD -- deps.txt deps.lock build.sh prepare.sh tools/build_manifest.py'
  git diff --stat c6a3745 HEAD -- deps.txt deps.lock build.sh prepare.sh tools/build_manifest.py
  echo "[diff_exit=$?]"
  echo '$ sha256sum deps.txt deps.lock build.sh prepare.sh tools/build_manifest.py'
  sha256sum deps.txt deps.lock build.sh prepare.sh tools/build_manifest.py
  echo "[sha_exit=$?]"
  echo '# 验收运行之后再取一次哈希, 用于确认本轮操作未改动依赖/构建材料.'
} > "$E/03-audit-br002/post-run-hashes.txt" 2>&1

{
  echo '# 各场景标准输出逐字节 (确认仅多一个行尾换行, 无其他字符差异)'
  while IFS= read -r c; do
    echo "--- python3 tool.py $c | od -c"
    python3 tool.py $c | od -c
    echo "[pipe_exit=${PIPESTATUS[0]}]"
  done <<'CMDS'
greet --name Ada
greet --name Ada --shout
count --file notes.txt
count --file notes.txt --chars
export --name Ada
CMDS
} > "$E/02-scenarios/stdout-bytes.txt" 2>&1
