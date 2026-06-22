---
name: ponytail-review
description: >
  专注于过工程的代码审查. 找出可以删除的东西: 重复实现的标准库功能, 不必要的依赖,
  投机性抽象, 死掉的灵活性. 每个发现一行: 位置, 砍什么, 用什么替代.
  当用户说 "review for over-engineering", "what can we delete",
  "is this over-engineered", "simplify review" 或调用 /ponytail-review 时使用.
  与正确性审查互补, 本 skill 只找复杂度.
---

审查 diff 中的不必要复杂度. 每个发现一行: 位置, 砍什么, 用什么替代. Diff 的最好结果是变短.

## Format

`L<line>: <tag> <what>. <replacement>.`, 多文件 diff 用 `<file>:L<line>: ...`.

Tags:

- `delete:` 死代码, 未使用的灵活性, 投机性功能. 替代: 无.
- `stdlib:` 标准库已提供的手写实现. 指出函数名.
- `native:` 依赖或代码在做平台已原生支持的事. 指出特性名.
- `yagni:` 一个实现的抽象, 没人设置的配置, 一个调用者的层.
- `shrink:` 同样逻辑, 更少行数. 给出更短的写法.

## Examples

❌ "This EmailValidator class might be more complex than necessary, have you
considered whether all these validation rules are needed at this stage?"

✅ `L12-38: stdlib: 27-line validator class. "@" in email, 1 line, real validation is the confirmation mail.`

✅ `L4: native: moment.js imported for one format call. Intl.DateTimeFormat, 0 deps.`

✅ `repo.py:L88: yagni: AbstractRepository with one implementation. Inline it until a second one exists.`

✅ `L52-71: delete: retry wrapper around an idempotent local call. Nothing replaces it.`

✅ `L30-44: shrink: manual loop builds dict. dict(zip(keys, values)), 1 line.`

## Scoring

结尾给出唯一重要的指标: `net: -<N> lines possible.`

如果没有可砍的, 说 `Lean already. Ship.` 然后停止.

## Boundaries

范围: 仅限过工程和复杂度. 正确性 bug, 安全漏洞, 性能明确不在范围内. 把它们转到普通审查. 一个简单的冒烟测试或基于 `assert` 的自检是 ponytail 最低要求, 不是膨胀, 永远不要标记为删除. 不应用修复, 只列出. "stop ponytail-review" 或 "normal mode": 还原为详细审查风格.
