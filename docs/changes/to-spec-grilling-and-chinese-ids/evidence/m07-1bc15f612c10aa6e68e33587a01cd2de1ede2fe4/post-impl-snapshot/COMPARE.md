# 安装目录只读摘要: 实施前 vs 实施后

- 实施前: `pre-impl-snapshot/skills-manifest.sha256` (调度方在首轮产品修改前取得).
- 实施后: `post-impl-snapshot/skills-manifest.sha256`, 命令 `find ~/.agents/skills -type f | sort | xargs sha256sum` (派工单原文), 取于 `taken-at.txt` (2026-11-27T04:58:27Z, 集成提交 A `1bc15f6` 之后).
- 文件数: 实施前 231 行, 实施后 231 行.

## 结论: 无差异

两次清单的路径写法不同 (实施前取自 `cd ~/.agents/skills` 的 `./<相对路径>`; 实施后按派工单用 `find ~/.agents/skills` 的绝对路径), 故直接 `diff` 会全表不同 (`manifest-diff.txt`, 仅路径差异, 464 行 = 231 对). 归一化去掉路径前缀后逐文件比对:

- `pre.normalized.sha256` / `post.normalized.sha256`: 去掉 `./` 与 `/home/bolo/.agents/skills/` 前缀, 按相对路径排序.
- `normalized-diff.txt`: `diff` 退出码 0, 0 行差异.
- 结论: 231 个文件的 SHA256 逐一同值, 本变更未触碰任何已安装技能.
