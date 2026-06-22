---
name: ponytail-review
description: >
  当我说 "review for over-engineering", "what can we delete",
  "is this over-engineered" 或 /ponytail-review 时使用.
  Diff 审查, 专找过工程, 每个发现一行.
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

❌ "这个 EmailValidator 类可能比必要的复杂, 你是否考虑过现阶段是否需要所有这些校验规则?"

✅ `L12-38: stdlib: 27 行校验类. "@" in email 一行, 真正校验靠确认邮件.`

✅ `L4: native: 导入 moment.js 只为一次 format 调用. Intl.DateTimeFormat, 0 依赖.`

✅ `repo.py:L88: yagni: AbstractRepository 只有一个实现. 内联, 等第二个实现出现再说.`

✅ `L52-71: delete: 幂等本地调用的 retry wrapper. 不需要替代.`

✅ `L30-44: shrink: 手动循环构建 dict. dict(zip(keys, values)) 一行.`

## Scoring

结尾给出唯一重要的指标: `净减少: -<N> 行.`

如果没有可砍的, 说 `已经很精简了. 提交.` 然后停止.

## Boundaries

范围: 仅限过工程和复杂度. 正确性 bug, 安全漏洞, 性能不在范围内, 转到普通审查. 冒烟测试或 `assert` 自检是 ponytail 最低要求, 不是膨胀, 不标记删除. 不应用修复, 只列出.
