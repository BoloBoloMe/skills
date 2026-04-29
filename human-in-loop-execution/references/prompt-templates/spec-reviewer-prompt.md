# 规格审查 subagent prompt 模板

## 适用时机

实现 subagent 完成任务后，审查是否满足 HILP 执行交接和任务规格时使用。

## 输入契约

```text
HILP design asset_ref:
HILP blueprint asset_ref:
HILP execution handoff asset_ref:
禁止越界项:
任务全文:
实现报告:
变更文件:
```

## 执行规则

prompt 必须包含：

```text
你正在审查实现是否符合已通过 HILP 执行交接的任务规格。

HILP design asset_ref:
HILP blueprint asset_ref:
HILP execution handoff asset_ref:
禁止越界项:

不信任实现报告。请读取实际变更，对照任务全文逐项检查：
1. 缺失项：是否遗漏任务要求。
2. 额外项：是否新增未批准范围。
3. 误解项：是否用错误方式实现正确目标。
4. 越界项：是否违反禁止越界项或需要 HILP 重审。

每个问题输出 file:line、问题、为什么影响执行交接、修复方向。
输出：Spec compliant 或 Issues found。
```

## 禁止事项

- 不得只看实现报告。
- 不得审查蓝图外新方案。
- 不得把缺口解释为执行者可自行决定。
- 不得省略 file:line。

## 输出契约

输出规格符合性结论、缺失项、额外项、误解项、越界项、file:line 和是否阻断继续。

## 检查清单

- [ ] HILP asset_ref 完整。
- [ ] 执行交接已引用。
- [ ] 禁止越界项已检查。
- [ ] 实际文件已读取。
- [ ] 结论明确且含 file:line。
