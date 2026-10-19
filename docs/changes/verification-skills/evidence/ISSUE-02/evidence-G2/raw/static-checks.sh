#!/usr/bin/env bash
# 本轮独立验收静态材料核对脚本 (验收输出, 非产品代码)
set -u
cd "$(git rev-parse --show-toplevel)" || exit 99
BASE=c6c44d7aa4562fc6190de0dcb1be4747e1c8adee   # 上一提交
TARGET=7f360da1d0bdf923472919523760bd4c59eb8576 # 目标提交 HEAD
echo "time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "TARGET=$(git rev-parse HEAD)"
echo
echo "===== 1. 两提交之间改动的文件清单 ====="
echo '$ git diff --stat '"$BASE"' '"$TARGET"
git diff --stat "$BASE" "$TARGET"
echo
echo '$ git diff --name-status '"$BASE"' '"$TARGET"
git diff --name-status "$BASE" "$TARGET"
echo
echo "===== 2. BR-002 依赖清单/锁文件/构建材料 逐项比对 (sha256) ====="
for f in deps.txt deps.lock build.sh; do
  a=$(git show "$BASE:$f" | sha256sum | cut -d' ' -f1)
  b=$(git show "$TARGET:$f" | sha256sum | cut -d' ' -f1)
  echo "$f  $BASE=$a  $TARGET=$b  $([ "$a" = "$b" ] && echo SAME || echo DIFF)"
done
echo
echo '$ git diff '"$BASE"' '"$TARGET"' -- deps.txt deps.lock build.sh   (空输出=无差异)'
git diff "$BASE" "$TARGET" -- deps.txt deps.lock build.sh
echo "[该命令退出码 $?]"
echo
echo "内容原文 (目标提交):"
for f in deps.txt deps.lock build.sh; do echo "--- $f ---"; git show "$TARGET:$f"; done
echo
echo "===== 3. BR-003 既有测试文件比对 (sha256) ====="
for f in tests/test_tool.py; do
  a=$(git show "$BASE:$f" | sha256sum | cut -d' ' -f1)
  b=$(git show "$TARGET:$f" | sha256sum | cut -d' ' -f1)
  echo "$f  $BASE=$a  $TARGET=$b  $([ "$a" = "$b" ] && echo SAME || echo DIFF)"
done
echo '$ git diff '"$BASE"' '"$TARGET"' -- tests/   (空输出=无差异)'
git diff "$BASE" "$TARGET" -- tests/
echo "[该命令退出码 $?]"
echo
echo "===== 4. AC-002-1 旧观察适用条件: count 相关代码与 notes.txt 是否未变 ====="
for f in tool.py notes.txt; do
  a=$(git show "$BASE:$f" | sha256sum | cut -d' ' -f1)
  b=$(git show "$TARGET:$f" | sha256sum | cut -d' ' -f1)
  echo "$f  $BASE=$a  $TARGET=$b  $([ "$a" = "$b" ] && echo SAME || echo DIFF)"
done
echo '$ git diff '"$BASE"' '"$TARGET"' -- notes.txt  (空输出=无差异)'
git diff "$BASE" "$TARGET" -- notes.txt
echo
echo '$ git diff -U0 '"$BASE"' '"$TARGET"' -- tool.py   (仅 greet 相关行)'
git diff -U0 "$BASE" "$TARGET" -- tool.py
echo
echo "notes.txt 目标提交原始字节:"
git show "$TARGET:notes.txt" | od -c
echo "empty.txt 目标提交原始字节 (应为空):"
git show "$TARGET:empty.txt" | od -c
echo
echo "===== 5. tool.py 的 import 清单 (是否只依赖标准库) ====="
grep -nE '^(import|from) ' tool.py
echo
echo "===== 6. 验收开始时的版本前提 ====="
echo '$ git rev-parse HEAD'; git rev-parse HEAD
echo '$ git status --porcelain  (空输出=已跟踪文件无改动)'; git status --porcelain
echo '$ git status --ignored --porcelain'; git status --ignored --porcelain
echo
echo "===== 结束 $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
