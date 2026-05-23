#!/usr/bin/env python3
"""人在环路中的复现循环模板.

复制此文件, 编辑下面的步骤, 然后运行它.
代理运行脚本; 用户在自己的终端中按提示操作.

用法:
  uv run python hitl-loop.template.py

两个辅助函数:
  step("instruction")          -> 显示指令, 等待 Enter
  capture("VAR", "question")  -> 显示问题, 将回答记录到 VAR

变量名和最终 KEY=VALUE 字段保持英文, 便于代理解析; 展示给人的提示使用中文.
"""
from __future__ import annotations

import sys

if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", newline="\n")

captured: dict[str, str] = {}


def step(instruction: str) -> None:
    print(f"\n>>> {instruction}")
    input("    [完成后按 Enter] ")


def capture(var: str, question: str) -> None:
    print(f"\n>>> {question}")
    captured[var] = input("    > ")


# --- 在下方编辑 ---------------------------------------------------------

step("在 http://localhost:3000 打开应用并登录.")

capture("ERRORED", "点击 \"导出\" 按钮. 它是否抛出错误? (y/n)")

capture("ERROR_MSG", "粘贴错误消息(或 \"无\"):")

# --- 在上方编辑 ---------------------------------------------------------

print("\n--- 已捕获 ---")
print(f"ERRORED={captured.get('ERRORED', '')}")
print(f"ERROR_MSG={captured.get('ERROR_MSG', '')}")
