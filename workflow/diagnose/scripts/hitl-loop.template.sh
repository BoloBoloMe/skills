#!/usr/bin/env bash
# 人在环路中的复现循环。
# 复制此文件，编辑下面的步骤，然后运行它。
# 代理运行脚本；用户在自己的终端中按提示操作。
#
# 用法：
#   bash hitl-loop.template.sh
#
# 两个辅助函数：
#   step "<instruction>"          → 显示指令，等待 Enter
#   capture VAR "<question>"      → 显示问题，将回答读入 VAR
#
# 结束时，捕获的值会以 KEY=VALUE 输出，供代理解析。

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

# --- 在下方编辑 ---------------------------------------------------------

step "在 http://localhost:3000 打开应用并登录。"

capture ERRORED "点击“导出”按钮。它是否抛出错误？(y/n)"

capture ERROR_MSG "粘贴错误消息（或“无”）："

# --- 在上方编辑 ---------------------------------------------------------

printf '\n--- 已捕获 ---\n'
printf 'ERRORED=%s\n' "$ERRORED"
printf 'ERROR_MSG=%s\n' "$ERROR_MSG"
