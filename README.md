# Skills

本仓库用于沉淀可复用的 AI coding agent 技能与规划资料。

## 目录结构

- `cz-sdk-windows-build/`：面向 Windows 环境的 `cz_sdk` Maven 构建与失败诊断技能。
- `human-in-the-loop/`：人在回路 Planning Protocol 的概念设计资料。

## 技能一览

### cz-sdk-windows-build

该技能用于在 Windows 上编译、验证和诊断 `cz_sdk` 相关 Maven 项目。

核心约束：

- 构建前必须自动探测并使用 JDK 8。
- 必须通过 `mvn -version` 确认 Maven 当前使用 Java 8。
- 统一使用 `scripts/run_build.ps1` 作为构建入口。
- 构建失败后使用 `scripts/diagnose_build_failure.ps1` 对日志进行分类诊断。

更多说明见：[`cz-sdk-windows-build/SKILL.md`](cz-sdk-windows-build/SKILL.md)

### human-in-the-loop

该目录保存人在回路规划协议的概念稿，目标是在编码前通过受约束、可审阅、可裁决的规划过程，对齐需求、事实、方案、改动路径与实现约束。

核心内容包括：

- 统一主协议与条件分支路由。
- Planning Archetype、Spec Strategy、Validation Strategy 与 Governance Mode。
- 六阶段规划流程。
- 人类决策点、资产状态与事件-动作裁决规则。

更多说明见：[`human-in-the-loop/人在回路-概念设计稿.md`](human-in-loop-planning/人在回路-概念设计稿.md)

## 使用方式

1. 根据任务场景选择对应目录。
2. 阅读目录内的 `SKILL.md`、设计稿或脚本说明。
3. 按技能约束执行，不要跳过前置环境检查、证据收集或人工决策点。

## 维护约定

- 新增技能建议使用独立目录，并提供清晰的入口文档。
- 技能目录应尽量区分协议说明、脚本、参考资料与资产文件。
- 涉及构建、诊断或规划流程的约束应写入技能文档，避免只存在于脚本或对话中。
