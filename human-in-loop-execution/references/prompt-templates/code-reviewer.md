# 代码审查员 prompt 模板

## 适用时机

需要对一个提交范围、任务批次或完整实现做最终代码审查时使用。

## 输入契约

```text
HILP design asset_ref:
HILP blueprint asset_ref:
HILP execution handoff asset_ref:
禁止越界项:
WHAT_WAS_IMPLEMENTED:
PLAN_OR_REQUIREMENTS:
BASE_SHA:
HEAD_SHA:
DESCRIPTION:
```

## 执行规则

prompt 必须包含：

```text
你正在审查已通过 HILP 执行交接范围内的代码变更。

HILP design asset_ref:
HILP blueprint asset_ref:
HILP execution handoff asset_ref:
禁止越界项:

Git 范围：BASE_SHA..HEAD_SHA
实现摘要：DESCRIPTION
要求或计划：PLAN_OR_REQUIREMENTS

请阅读 git diff，审查清单：代码质量、架构、测试、需求符合、生产就绪、HILP 越界。
输出格式：Strengths、Issues、Recommendations、Assessment。
每个 issue 必须有 file:line、问题、影响、修复方向。
严重性规则：Critical 只用于 bug、安全、数据丢失、破坏功能；Important 用于架构、缺失功能、错误处理、测试缺口；Minor 用于风格、文档、优化。
Assessment 必须包含 Ready to merge: Yes/No/With fixes。
```

## 禁止事项

- 不得给未审查代码下结论。
- 不得把风格建议标为 Critical。
- 不得忽略 HILP 执行交接和禁止越界项。
- 不得建议蓝图外重构而不标明需 HILP 重审。

## 输出契约

输出 Strengths、Issues、Recommendations、Assessment、Ready to merge 结论和是否阻断继续。

## 检查清单

- [ ] BASE_SHA..HEAD_SHA 明确。
- [ ] 执行交接已引用。
- [ ] 禁止越界项已检查。
- [ ] 每个 issue 含 file:line。
- [ ] Critical、Important、Minor 校准正确。
