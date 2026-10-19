# 新建笔记

- 准备: 在项目根执行一次 `python3 app.py --version`, 确认输出 `0.3.0`.
- 命令: `python3 app.py add "第一条笔记"`
- 验证: `python3 app.py list` 输出含 `1	第一条笔记`; 正文与输入一致, 不带参数名.
- 注意: `add` 把剩余参数用空格拼接成正文, 正文要整体加引号, 不能写 `add --text "..."`.
- 取证: 保存 `add` 与 `list` 的输出.
