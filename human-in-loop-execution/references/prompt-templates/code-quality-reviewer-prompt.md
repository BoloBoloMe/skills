# 代码质量审查 subagent prompt 模板

## 适用时机

规格审查通过后，请 subagent 审查代码质量、测试质量和可维护性时使用。

## 输入契约

```text
HILP design asset_ref:
HILP blueprint asset_ref:
HILP execution handoff asset_ref:
禁止越界项:
规格审查结论:
实现摘要:
任务或计划引用:
变更范围:
```

## 执行规则

只能在规格审查通过后使用。prompt 必须包含：

```text
你正在审查一个已通过 HILP 执行交接范围内的实现。

HILP design asset_ref:
HILP blueprint asset_ref:
HILP execution handoff asset_ref:
禁止越界项:

请检查：职责清晰、错误处理、测试真实行为、文件结构一致性、执行交接越界、回归风险。
严重性校准：Critical 只用于 bug、安全、数据丢失、破坏功能；Important 用于架构、缺失功能、错误处理、测试缺口；Minor 用于风格、文档、优化。
输出 Strengths、Issues、Recommendations、Assessment。
```

## 禁止事项

- 不得在规格审查未通过前做质量审查。
- 不得把蓝图外建议当作必须修复。
- 不得忽略禁止越界项。
- 不得把风格问题标为 Critical。

## 输出契约

输出质量审查结论，按 Critical、Important、Minor 分类，并说明是否可继续。

## 检查清单

- [ ] 执行交接 asset_ref 已填。
- [ ] 禁止越界项已填。
- [ ] 规格审查已通过。
- [ ] 严重级别清楚。
- [ ] 结论可执行。
