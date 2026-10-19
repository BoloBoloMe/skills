# 演练项目说明

本项目是 ISSUE-09 的临时演练项目, 用来核对 benchmark-checklist 的粗估, 选型与结论报告规则.

- `src/`: 冻结产品源码 (`report_job.py`, `liteidx.py`, `fastidx.py`). 演练期间不改.
- `bench/`: 已授权的独立实验脚本. 可在授权范围内修改或补计数.
- 数字全部由 `time.sleep` 模拟, 只证明方法, 不代表任何真实产品性能.

## 背景

- `report_job.py` 的 normalize 阶段有一个候选优化: new 侧把归一化耗时从 20ms/千行降到 6ms/千行.
- `liteidx.py` 与 `fastidx.py` 是待选型的两个候选索引库.
