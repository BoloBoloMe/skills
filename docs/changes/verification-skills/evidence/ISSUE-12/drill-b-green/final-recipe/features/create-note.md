# 新建笔记

- 准备: 删除项目根 `data/`, 确认 `python3 app.py --version` 输出 `0.3.0`.
- 命令: `python3 app.py add "第一条笔记"`
- 期望: 退出码 0, 输出 `added 1: 第一条笔记`.
- 验证: `python3 app.py list` 退出码 0, 首行为 `1` + 制表符 + `第一条笔记`.
