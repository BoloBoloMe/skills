"""HITL 复现循环模板.

复制本文件, 按下方标记编辑, 按项目声明的方式运行.
agent 运行脚本; 用户按终端提示操作.

两个辅助函数:
  step("指令")           -> 展示指令, 等待回车
  capture("VAR", "问题") -> 展示问题, 把回答记入 VAR

结束时, 捕获值以 KEY=VALUE 打印, 供 agent 解析.
capture 的值会打印回终端供 agent 读取, 所以只捕获观察结果;
登录等手工操作留给用户, 用 step.
"""

CAPTURED: dict[str, str] = {}


def step(instruction: str) -> None:
    input(f"\n>>> {instruction}\n    [完成后回车] ")


def capture(var: str, question: str) -> None:
    CAPTURED[var] = input(f"\n>>> {question}\n    > ")


# --- 在下方编辑 ---------------------------------------------------------

step("打开 http://localhost:3000 并登录.")
capture("ERRORED", "点击 'Export' 按钮. 报错了吗? (y/n)")
capture("ERROR_MSG", "粘贴错误信息 (无则填 none):")

# --- 在上方编辑 ---------------------------------------------------------

print("\n--- Captured ---")
for key, value in CAPTURED.items():
    print(f"{key}={value}")
