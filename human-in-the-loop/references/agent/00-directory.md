# HITL Agent 目录

本文是 HITL 0.0.1 的兼容性目录。常规运行时优先读取 `runtime-router.md`，再按当前阶段读取细粒度 reference；不要把本目录当作全量预读清单。

## 渐进读取入口

- `runtime-router.md`：正式操作本技能时的第一份 reference，负责按阶段路由。
- `script-index.md`：脚本用途索引；除非调试，不要直接读取脚本源码。

## 完整兼容参考

- `01-workflow.md`：端到端工作流、tier 与批准/确认规则。
- `02-interrogation-loop.md`：逐问澄清纪律完整参考；常规运行优先读取拆分后的 interrogation 文件。
- `03-asset-schemas.md`：MVP YAML agent 资产结构完整参考；常规运行优先读取拆分后的 schema 文件。
- `04-plan-runbook.md`：Plan / Runbook 要求。
- `05-reassessment-and-resume.md`：失败路由、重评估与断点恢复。

## 交接入口

任一 agent 接手 HITL 工作时，最短入口永远是资产包根部的 `manifest.yaml`。manifest 的 `workflow`、`current_pointers` 与 `interrogation_gates` 必须说明当前阶段、active asset、下一步动作、阻塞原因和盘问门禁状态。
