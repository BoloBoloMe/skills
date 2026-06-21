#!/usr/bin/env bash
# 人在回路复现循环.
# 复制本文件, 编辑下方步骤, 然后运行.
# agent 运行脚本, 用户按终端提示操作.
#
# 用法:
#   bash hitl-loop.template.sh
#
# 两个 helper:
#   step "<instruction>"          -> 展示指令, 等待 Enter
#   capture VAR "<question>"      -> 展示问题, 读取回答到 VAR
#
# 结束时, 捕获值会以 KEY=VALUE 输出, 供 agent 解析.

set -euo pipefail

step() {
  printf '\n>>> %s\n' "$1"
  read -r -p "    [完成后按 Enter] " _
}

capture() {
  local var="$1" question="$2" answer
  printf '\n>>> %s\n' "$question"
  read -r -p "    > " answer
  printf -v "$var" '%s' "$answer"
}

# --- edit below ---------------------------------------------------------

step "打开 http://localhost:3000 并登录."

capture ERRORED "点击 Export 按钮. 是否抛错? (y/n)"

capture ERROR_MSG "粘贴错误信息, 没有则填 none:"

# --- edit above ---------------------------------------------------------

printf '\n--- Captured ---\n'
printf 'ERRORED=%s\n' "$ERRORED"
printf 'ERROR_MSG=%s\n' "$ERROR_MSG"
