# Skills

本仓库用于沉淀可复用的 AI coding agent 技能、人在回路规划协议资料，以及围绕这些技能形成的规划与审查资产。

本仓库是技能源码与资料仓库，不声明仓库内目录会被目标 agent 自动发现。真实使用时，应按目标 agent 的技能安装方式，将需要的技能目录安装或链接到对应环境。

## 当前内容

```text
.
├── cz-sdk-windows-build/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/jdk8-constraint.md
│   └── scripts/*.ps1
├── human-in-loop-planning/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/*.md
│   ├── 人在回路-概念设计稿.md
│   └── 工作流程.png
├── human-in-loop-execution/
│   ├── SKILL.md
│   └── references/
│       ├── *.md
│       └── prompt-templates/*.md
├── docs/
│   ├── hilp/
│   └── review/
└── 裁剪superpowers.md
```

## 技能一览

### cz-sdk-windows-build

面向 Windows 环境的 `cz_sdk`、`czsdk-parent`、`czsdk-paycenter` 等 Maven 项目构建与失败诊断技能。

核心约束：

- 构建前必须探测可用 JDK 8。
- 必须通过 `mvn -version` 确认 Maven 当前使用 Java 8。
- 统一使用 `scripts/run_build.ps1` 作为构建入口。
- 构建失败后使用 `scripts/diagnose_build_failure.ps1` 对日志进行分类诊断。
- 环境类失败优先按环境问题处理，不直接跳入源码调试。

入口文档：[`cz-sdk-windows-build/SKILL.md`](cz-sdk-windows-build/SKILL.md)

### human-in-loop-planning

人在回路规划协议的总入口，用于把复杂变更、重构、迁移、调查、设计审批、实施蓝图、执行交接和规划资产归档纳入同一状态机。

核心能力：

- 初始分流、需求事实对齐、方案设计与审批。
- 实施蓝图、变更重审、执行交接与规划资产归档。
- 阶段门控、资产状态、人工批准、确定性检查和重审规则。
- 将规划资产落盘到 `docs/hilp/<变更概述>/`，并用版本化文件名保留审批状态。

核心约束：

- 不用于直接写代码或绕过人工决策。
- `ready-for-approval` 不等于 `approved`；只有明确人工批准授予才能进入下游绑定。
- 从实施蓝图开始，正式资产必须确定、唯一、可执行，不得把待定项留给执行者临场判断。

入口文档：[`human-in-loop-planning/SKILL.md`](human-in-loop-planning/SKILL.md)  
概念资料：[`human-in-loop-planning/人在回路-概念设计稿.md`](human-in-loop-planning/人在回路-概念设计稿.md)

### human-in-loop-execution

HILP 执行交接完成后的执行纪律技能包，用于把已批准设计、已批准蓝图和执行交接资产落实为受约束的计划、实现、测试、审查、调试与收尾流程。

它与 `human-in-loop-planning` 的关系是：`human-in-loop-planning` 负责需求、事实、设计审批、实施蓝图、执行交接和规划资产归档；`human-in-loop-execution` 只在执行交接完成后使用，并始终绑定 HILP 的已批准设计、已批准蓝图和执行交接资产。

保留能力：

- 执行入口检查与路由。
- 将已批准蓝图机械拆分为执行计划。
- subagent 执行与 inline fallback。
- TDD、系统化调试、代码审查与审查反馈处理。
- 完成前验证、分支收尾、并行 agent 判定和技能编写元纪律。
- 补回 Superpowers 对应执行技能的强制门、红旗、反误用规则和 prompt 校准。

明确不包含：

- 不负责需求构思、需求裁剪、设计审批或蓝图补齐。
- 不创建隔离工作区技能入口。
- 不复制 Superpowers 插件、hooks、commands、assets、历史 plans/specs、测试目录或上游贡献规则。
- 不替代 HILP 变更重审；执行中发现新事实、越界需求或蓝图错误时必须回到 HILP。

使用前必须提供：

- 已批准的 `stage-3/design-choice@vN`。
- 已批准的 `stage-4-5/implementation-blueprint@vM`。
- `stage-6/execution-handoff@vK`。
- “无阻断项”的执行入口检查结果。
- 用户指定的执行工作区。

入口文档：[`human-in-loop-execution/SKILL.md`](human-in-loop-execution/SKILL.md)

## 资料与资产目录

- `docs/hilp/`：HILP 规划链落盘资产，按变更主题分目录保存阶段文件、审批状态和归档 manifest。
- `docs/review/`：代码审查、协议审查或能力对比报告。
- `裁剪superpowers.md`：裁剪 Superpowers 能力并对接 HILP 的原则性分析。

## 使用方式

1. 根据任务场景选择技能目录。
2. 先读取对应 `SKILL.md`，再按需读取 `references/`、脚本或 prompt 模板。
3. 若目标 agent 不会自动发现本仓库目录，按目标 agent 的安装方式安装或链接对应技能目录。
4. 对 HILP 任务，规划阶段使用 `human-in-loop-planning`；执行交接完成后才使用 `human-in-loop-execution`。
5. 不要跳过前置环境检查、证据收集、人工批准、确定性检查、执行入口检查或完成前验证。

## 维护约定

- 新增技能应使用独立目录，并至少提供 `SKILL.md` 作为入口文档。
- 技能目录应区分入口协议、参考资料、脚本、prompt 模板和资产文件。
- 根 `README.md` 负责登记仓库级目录与技能概览；除非内容不能由 `SKILL.md` 和根 `README.md` 承载，否则避免新增重复的技能包 README。
- 涉及构建、诊断、规划或执行纪律的强约束应写入技能文档，避免只存在于脚本或对话中。
- 审查报告保存到 `docs/review/`；HILP 规划资产保存到 `docs/hilp/<变更概述>/`。
