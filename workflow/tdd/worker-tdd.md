# run-afk-workflow 的 worker 如何使用 TDD

## 阅读门禁

仅当 contract/issue 已确定所有行为和接口, 无需再与用户确认时, 才读本文件. 否则按 `tdd` skill 标准流程走, 包括计划步骤.

## 红-绿-重构

contract/issue 已为你提供规格. 跳过 `tdd` skill 的"计划"步骤, 直接 red-green-refactor:

1. RED: 按 contract/issue 要求的规格写一个测试 → 失败.
2. GREEN: 最少代码通过.
3. REFACTOR: 清理重复/加深模块, 保持绿.

参考 `tdd` skill 中的 `tests.md` (好/坏测试示例), `mocking.md` (mock 规则), `refactoring.md` (重构候选项).

## 修复场景

若审核报告指出你的测试偏离 contract: 先修正测试 (使其表达正确规格, 修正后的测试对当前错误代码应为 RED), 再修正代码到 GREEN. 
如果你的任务中本来就需要编写自由格式的执行记录如 node, 那么在你的 note 中补充说明: 区分哪些测试被修正 (及原因), 哪些是新增.

## 证据

在你的 note (如果有) 中记录每个 RED/GREEN 循环: 命令, 失败/通过输出. 无法提供 RED 时 (如项目不支持可信 RED) 说明原因并提供可复核验证.
