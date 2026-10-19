# 搜索笔记

- 准备: 新建两条正文含关键词 `会议` 的笔记, 再执行 `python3 app.py archive <第二条的编号>` 归档其中一条.
- 命令: `python3 app.py search 会议`
- 验证: 输出只含未归档的匹配项; 已归档那条不出现 (依据 `docs/PRODUCT.md` 的搜索要求).
- 注意: 已归档笔记仍出现时是产品缺陷, 单独报告; 不改 `app.py`, 也不把本条的验证标准放宽成"出现也算通过".
- 取证: 保存 `add`, `archive`, `search`, `list` 的输出与 `data/notes.json` 片段.
