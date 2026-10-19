# 新建笔记

- 准备: 项目根执行 `python3 app.py --version`, 期望 `0.3.0`; 确认 `data/` 不存在或为空, 使新笔记从 id 1 开始.
- 命令: `python3 app.py add "第一条笔记"`
- 验证: `add` 输出 `added 1: 第一条笔记`; `python3 app.py list` 输出含 `1<TAB>第一条笔记` (制表符分隔), 正文与输入一致.
- 注意: 正文要作为一个参数传入. `app.py` 没有 `--text` 选项, 传 `--text` 会被当成正文一部分, 导致正文与输入不一致.
