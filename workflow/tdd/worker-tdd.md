# afk worker 如何使用 TDD

## 阅读门禁

仅当 PRODUCT/TECHNICAL/EXECUTION/issue 已确定所有行为和接口, 无需再向我确认时才读本文件. 否则按 `tdd` 标准流程走, 包括会话计划.

## 红-绿-重构

Spec Pack 和当前 issue 已提供规格. 跳过 `tdd` 的计划步骤, 直接 red-green-refactor:

1. RED: 按 issue 覆盖的 AC/TG/NFR 写一个行为测试 -> 失败.
2. GREEN: 写最少代码通过.
3. REFACTOR: 清理重复/加深模块, 保持 green.

参考 `tests.md`, `mocking.md`, `refactoring.md`.

## 修复场景

review 指出测试偏离 Spec 时, 先修正测试, 使它表达正确规格并对当前错误代码变 red, 再修正代码到 green. note 中区分修正测试及原因和新增测试.

## 证据

note 记录每个 RED/GREEN 循环的命令和失败/通过输出. 无法提供 RED 时说明原因, 并给出可复核验证. 每项证据标出覆盖的 AC/TG/NFR.
