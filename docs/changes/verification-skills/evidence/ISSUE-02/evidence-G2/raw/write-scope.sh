#!/usr/bin/env bash
# 本轮独立验收: BR-004 写入范围与清理记录 (验收输出, 非产品代码)
set -u
cd "$(git rev-parse --show-toplevel)" || exit 99
EV=docs/changes/tool-cli/evidence-7f360da
echo "time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "cwd: $(pwd)"
echo "HEAD: $(git rev-parse HEAD)"
echo
echo "===== 1. 本轮实际写入的资源 (证据目录内) ====="
find "$EV" -type f | sort | sed 's/^/  /'
echo
echo "===== 2. 本轮用到的临时资源 ====="
ls -l "$EV/raw/.accept-stderr" 2>&1 | sed 's/^/  /'
echo "  说明: raw/.accept-stderr 是 run-scenarios.sh 用来暂存 stderr 的临时文件, 位于证据目录内."
echo
echo "===== 3. 证据目录之外, 验收开始后是否有文件被写入 (排除 .git) ====="
ACCEPT_START="2026-10-19T11:09:00Z"
echo "  验收开始时间(本会话首次命令): $ACCEPT_START"
echo "  目标提交时间: $(git log -1 --format=%cI)"
echo "  \$ find . -path ./.git -prune -o -path ./\$EV -prune -o -type f -newermt \$ACCEPT_START -print"
find . -path ./.git -prune -o -path "./$EV" -prune -o -type f -newermt "$ACCEPT_START" -print | sed 's/^/  /'
echo "  --- 空输出 = 验收开始后证据目录外没有任何写入 ---"
echo "  参考: 工作区文件的 mtime (应为布置仓库时间, 早于验收开始):"
find . -path ./.git -prune -o -path "./$EV" -prune -o -type f -printf '%TY-%Tm-%TdT%TH:%TM:%TSZ %p\n' | sort | sed 's/^/  /' 
echo
echo "===== 4. 是否有构建/测试缓存或临时产品文件残留 ====="
find . -path ./.git -prune -o \( -name '__pycache__' -o -name '.pytest_cache' -o -name '*.pyc' \) -print | sed 's/^/  /'
echo "  missing.txt 是否存在: $( [ -e missing.txt ] && echo EXISTS || echo ABSENT )"
echo
echo "===== 5. 清理临时资源 ====="
rm -f "$EV/raw/.accept-stderr"
echo "  已执行: rm -f $EV/raw/.accept-stderr"
echo "  清理后检查: $( [ -e "$EV/raw/.accept-stderr" ] && echo STILL_EXISTS || echo GONE )"
echo
echo "===== 6. 清理后工作区状态 (本次证据目录输出之外不应有变化) ====="
echo '$ git status --porcelain'; git status --porcelain
echo '$ git status --ignored --porcelain'; git status --ignored --porcelain
echo '$ git diff --stat HEAD  (已跟踪文件改动, 空=无)'; git diff --stat HEAD
echo
echo "===== 7. 最终证据目录清单 ====="
find "$EV" -type f | sort | sed 's/^/  /'
echo
echo "===== 结束 $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
