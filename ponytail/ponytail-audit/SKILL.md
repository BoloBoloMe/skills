---
name: ponytail-audit
description: >
  当我说 "audit this codebase", "find bloat" 或 /ponytail-audit 时使用.
  全仓库过工程审计, 按删除优先级排序. 一次性报告.
---

ponytail-review, 全仓库版. 扫描整棵树而非 diff. 按最大可砍量排序.

## Tags

与 ponytail-review Format 段相同.

## Hunt

标准库或平台已覆盖的依赖, 单实现 interface, 单产品 factory, 仅委托的 wrapper, 只导出一个东西的文件, 死掉的 flag 和配置, 手写标准库.

## Output

每个发现一行, 排序: `<tag> <砍什么>. <替代>. [path]`.
结尾: `净减少: -<N> 行, -<M> 依赖.` 无可砍: `已经很精简了. 提交.`

## Boundaries

范围: 仅限过工程和复杂度. 正确性 bug, 安全漏洞, 性能不在范围内. 只列出, 不应用. 一次性.
