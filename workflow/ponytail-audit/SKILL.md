---
name: ponytail-audit
description: >
  全仓库过工程审计. 类似 ponytail-review, 但扫描整个代码库而非 diff:
  按删除优先级排序的列表, 包含什么该删, 什么该简化, 什么该用标准库/原生替代.
  当用户说 "audit this codebase", "audit for over-engineering",
  "what can I delete from this repo", "find bloat", "ponytail-audit"
  或 "/ponytail-audit" 时使用. 一次性报告, 不应用修复.
---

ponytail-review, 全仓库版. 扫描整棵树而非 diff. 按最大可砍量排序.

## Tags

与 ponytail-review 相同:

- `delete:` 死代码, 未使用的灵活性, 投机性功能. 替代: 无.
- `stdlib:` 标准库已提供的手写实现. 指出函数名.
- `native:` 依赖或代码在做平台已原生支持的事. 指出特性名.
- `yagni:` 一个实现的抽象, 没人设置的配置, 一个调用者的层.
- `shrink:` 同样逻辑, 更少行数. 给出更短的写法.

## Hunt

标准库或平台已覆盖的依赖, 单实现 interface, 单产品 factory, 仅委托的 wrapper, 只导出一个东西的文件, 死掉的 flag 和配置, 手写标准库.

## Output

每个发现一行, 排序: `<tag> <what to cut>. <replacement>. [path]`.
结尾: `net: -<N> lines, -<M> deps possible.` 无可砍: `Lean already. Ship.`

## Boundaries

范围: 仅限过工程和复杂度. 正确性 bug, 安全漏洞, 性能明确不在范围内. 把它们转到普通审查. 只列出发现, 不应用. 一次性. "stop ponytail-audit" 或 "normal mode" 还原.
