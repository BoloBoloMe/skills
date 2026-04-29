# 实现 subagent prompt 模板

## 适用时机

派发单个实现任务给 subagent 时使用。

## 输入契约

```text
HILP design asset_ref:
HILP blueprint asset_ref:
HILP execution handoff asset_ref:
禁止越界项:
背景上下文:
任务全文:
工作目录:
验证命令:
```

## 执行规则

prompt 必须包含：

```text
你正在实现一个已通过 HILP 执行交接的任务。

HILP design asset_ref:
HILP blueprint asset_ref:
HILP execution handoff asset_ref:
禁止越界项:
背景上下文:

开始前：如果需求、验收标准、依赖、执行方式或禁止越界项不清楚，先提问，不要猜测。

任务全文：
<粘贴任务全文，不要求 subagent 自行读取整份计划>

代码组织规则：每个文件保持单一职责；遵守计划文件范围；发现文件拆分或重构超出计划时停止并报告。

升级条件：需要架构决策、上下文不足、重构超出计划、连续阅读无进展、蓝图外文件需求、HILP 越界风险。

自查维度：完整性、质量、纪律、测试、HILP 越界。

报告格式：状态 DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT；实现内容；测试结果；文件变更；自查发现；阻断项。
```

## 禁止事项

- 不得省略执行交接 asset_ref。
- 不得让 subagent 重新设计。
- 不得派发蓝图外文件。
- 不得隐藏禁止越界项。

## 输出契约

subagent 返回状态、实现内容、测试结果、文件变更、自查发现和阻断项。BLOCKED 或 NEEDS_CONTEXT 必须说明已尝试内容和需要的上下文。

## 检查清单

- [ ] HILP 三类 asset_ref 已填。
- [ ] 执行交接已填。
- [ ] 禁止越界项已填。
- [ ] 开始前提问规则已写入。
- [ ] 报告格式包含 DONE、BLOCKED 等状态。
