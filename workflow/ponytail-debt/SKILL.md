---
name: ponytail-debt
description: >
  收集代码库中所有 `ponytail:` 注释, 生成债务账本, 让 ponytail 留下的刻意简化和延迟
  不会悄悄烂成 "later means never". 当用户说 "ponytail debt", "/ponytail-debt",
  "what did ponytail defer", "list the shortcuts", "ponytail ledger"
  或 "what did we mark to do later" 时使用. 一次性报告, 不修改任何文件.
---

每个刻意的 ponytail 简化都用 `ponytail:` 注释标记了上限和升级路径. 本 skill 将它们收集到账本中, 防止延迟变成永久.

## Scan

Grep 仓库中的注释标记, 跳过 `node_modules`, `.git` 和构建产物:

`grep -rnE '(#|//) ?ponytail:' .` (如果技术栈有其他注释前缀, 加上)

每个匹配是一行账本. 注释前缀保证仅提及约定的文字不会进入账本.

## Output

每个标记一行, 按文件分组:

`<file>:<line>, <what was simplified>. ceiling: <the limit named>. upgrade: <the trigger to revisit>.`

约定格式是 `ponytail: <ceiling>, <upgrade path>`, 直接从注释中提取 ceiling 和 trigger. 想要每行的 owner? 加 `git blame -L<line>,<line>`.

标记腐烂风险: 没有升级路径或 trigger 的 `ponytail:` 注释标记 `no-trigger`, 这些是会悄悄烂掉的.

结尾: `<N> markers, <M> with no trigger.` 未找到: `No ponytail: debt. Clean ledger.`

## Boundaries

只读和报告, 不修改任何文件. 如需持久化, 用户要求后写入文件 (如 `PONYTAIL-DEBT.md`). 一次性. "stop ponytail-debt" 或 "normal mode" 还原.
