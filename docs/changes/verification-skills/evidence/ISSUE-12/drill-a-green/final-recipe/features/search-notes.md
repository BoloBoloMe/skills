# 搜索笔记

- 准备: 从不存在或为空的 `data/` 开始, 依次执行:
  - `python3 app.py add "会议 甲"` (得到 id 1)
  - `python3 app.py add "会议 乙"` (得到 id 2)
  - `python3 app.py archive 1`
- 命令: `python3 app.py search 会议`
- 验证: 只输出 `2<TAB>会议 乙` 和 `matches: 1`; 已归档的 id 1 不得出现.
- 说明: 输出里出现归档笔记就是产品缺陷, 按 Product 判失败, 不放宽验证条件.
