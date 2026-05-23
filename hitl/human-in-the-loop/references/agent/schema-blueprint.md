# Blueprint Schema

通用头字段和禁止字段见 `schema-common.md`。

## planning/blueprint

必须包含：

- `source_design_ref`
- `implementation_units`
- `execution_contract`

`implementation_units[]` 至少包含：

- `unit_id`：固定格式 `EU-001`，同一 Blueprint 内唯一。
- `objective`
- `implementation_intent`
- `dependencies`：执行单元依赖列表，可为空；必须引用同一 Blueprint 内存在的 `unit_id`，不得自依赖或成环。
- `implementation_step_outline`：Plan 前盘问使用的步骤轮廓，非空。

`implementation_step_outline[]` 至少包含：

- `step_id`：固定格式 `<unit_id>-S01`，全 Blueprint 唯一。
- `title`
- `expected_files`：预期文件或 glob，必须是 workspace 相对 POSIX 路径。

`implementation_step_outline[].depends_on` 可选；若存在，只能引用同一单元内较早步骤或已完成依赖单元内步骤，且不得成环。

`execution_contract` 至少包含：

- `allowed_files`
- `prohibited_files`
- `prohibited_scope`
- `verification_contract`
- `stop_conditions`
- `planning_requirement`

写 `planning/blueprint@vN` 前必须关闭并校验 `pre_blueprint` gate。
