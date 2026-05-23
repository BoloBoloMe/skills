# Pre-blueprint Interrogation

写 `planning/blueprint@vN` 前必须关闭并校验 `pre_blueprint` gate。

## 盘问目标

pre_blueprint gate 用于把已批准或当前有效的 design 转化为可执行蓝图前的阻断未知项全部关闭。必须确认：

- 推荐方案是否仍然成立；
- implementation units 的边界、目标和依赖；
- 每个 unit 的 step outline 是否足以支持后续源码级盘问；
- `execution_contract.allowed_files`、`prohibited_files`、`prohibited_scope` 是否明确；
- 验证契约、停止条件和 planning requirement 是否足以约束后续 Plan / Runbook。

如果发现 design 失效、范围变化、新事实影响方案或执行契约无法从 design 推导，必须进入 reassessment；不得直接在 blueprint 中静默扩大范围。

gate 关闭后，运行：

```bash
scripts/validate_interrogation_gate.py --gate pre_blueprint --target planning/blueprint@vN
```
