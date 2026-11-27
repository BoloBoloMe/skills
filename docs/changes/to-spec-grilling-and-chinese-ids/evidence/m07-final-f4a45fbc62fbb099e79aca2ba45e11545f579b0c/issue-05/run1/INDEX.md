# ISSUE-05 (m07-rw-05) 证据索引

改动: `workflow/verify-change/SKILL.md:45,51,79` 术语 `设计方式` -> `设计验证方案`.

| 文件 | 内容 |
| --- | --- |
| notes.md | 依据, 逐处对照, 语义零变化证明, 命令与退出码, 未覆盖范围 |
| diff.patch | 完整 `git diff` 原件 |
| diff-numstat.txt | 行级统计 (3 增 3 删, 单文件) |
| term-normalized-diff.txt | 逐行归一比对结果 (仅术语替换) |
| check-skill.txt | 改后 `check_skill.py` 输出与退出码 |
| pre/ | 改前副本 (`git show HEAD:...`) 及其 `check_skill.py` 输出 |
| changed-files-pre-commit.txt | 提交前 `git status --porcelain` |
| environment.txt | uname/uv/python/时间 |
| manifest.sha256 | 本目录文件清单 |
