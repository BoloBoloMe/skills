---
name: ponytail-debt
description: >
  当我说 "ponytail debt", "list the shortcuts" 或 /ponytail-debt 时使用.
  收集所有 `ponytail:` 注释到账本, 一次性报告.
---

每个刻意的 ponytail 简化都用 `ponytail:` 注释标记了上限和升级路径. 本 skill 将它们收集到账本中, 防止延迟变成永久.

## Scan

Grep 仓库中的注释标记, 跳过 `node_modules`, `.git` 和构建产物:

`grep -rnE '(#|//) ?ponytail:' .` (如果技术栈有其他注释前缀, 加上)

每个匹配是一行账本. 注释前缀保证仅提及约定的文字不会进入账本.

## Output

每个标记一行, 按文件分组:

`<file>:<line>, <简化了什么>. 上限: <命名的上限>. 升级: <重新审视的触发条件>.`

约定格式是 `ponytail: <上限>, <升级路径>`, 直接从注释中提取. 想要每行的 owner? 加 `git blame -L<line>,<line>`.

标记腐烂风险: 没有升级路径或 trigger 的 `ponytail:` 注释标记 `no-trigger`, 这些是会悄悄烂掉的.

结尾: `<N> 个标记, <M> 个无触发器.` 未找到: `无 ponytail 债务. 账本干净.`

## Boundaries

只读和报告, 不修改文件. 如需持久化, 用户要求后写入文件 (如 `PONYTAIL-DEBT.md`). 一次性.
