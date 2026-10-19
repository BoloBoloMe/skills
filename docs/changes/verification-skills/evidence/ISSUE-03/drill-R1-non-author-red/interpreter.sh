#!/usr/bin/env bash
# 环境说明与解释器一致性复核: 顶层 shell 的 python3 是 uv run python 的函数包装.
cd "$(dirname "$0")/../../../.." || exit 99
E=docs/changes/tool-cli/evidence-93ba124-20261019
OUT="$E/02-scenarios/interpreter-note.txt"
{
  echo '$ type -a python3'
  type -a python3
  echo '[exit='"$?"']'
  echo
  echo '$ python3 -VV   # 即 uv run python'
  python3 -VV
  echo '[exit='"$?"']'
  echo
  echo '$ /usr/bin/python3 -VV'
  /usr/bin/python3 -VV
  echo '[exit='"$?"']'
  echo
  echo '# 下面用 /usr/bin/python3 直接重跑全部 5 个场景, 与 uv run python 的结果对照.'
  while IFS= read -r c; do
    echo "--- /usr/bin/python3 tool.py $c"
    /usr/bin/python3 tool.py $c
    echo "[exit=$?]"
  done <<'CMDS'
greet --name Ada
greet --name Ada --shout
count --file notes.txt
count --file notes.txt --chars
export --name Ada
CMDS
} > "$OUT" 2>&1
