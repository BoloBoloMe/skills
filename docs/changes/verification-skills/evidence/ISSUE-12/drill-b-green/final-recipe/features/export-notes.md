# 导出笔记

- 准备: 删除项目根 `data/`, 新建两条笔记 (`add "导出笔记 A"`, `add "导出笔记 B"`); 导出包含全部笔记, 含已归档的笔记.
- 命令: `python3 app.py export /tmp/verify-notes-export.tsv`
- 期望: 退出码 0, 输出 `exported 2 notes to /tmp/verify-notes-export.tsv`, 文件存在.
- 验证: `wc -l < /tmp/verify-notes-export.tsv` 等于 `python3 app.py list | wc -l`; 导出文件每行为 `编号` + 制表符 + `正文`.
