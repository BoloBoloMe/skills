# Skills

本仓库用于沉淀可复用的 AI coding agent 技能、HITL 人在回路协议资料、PRD 写作规范，以及围绕这些技能形成的审查资产。

本仓库是技能源码与资料仓库，不声明仓库内目录会被目标 agent 自动发现。真实使用时，应按目标 agent 的技能安装方式，将需要的技能目录安装或链接到对应环境。

## 当前内容

```text
.
├── jdk8-windows-build/
├── human-in-the-loop/
│   ├── SKILL.md
│   ├── references/{agent,shared,human-view}/...
│   ├── scripts/*.py
│   └── tests/...
├── human-in-loop-brief/
├── prd-writer/
├── rigorous-contrarian-answers/
├── springboot-hcurl-generator/
├── prompts/
│   ├── hitl.md
│   ├── hilb.md
│   └── *.md
└── docs/
    ├── 人在回路-概念设计稿.md
    └── review/*.md
```

## 技能一览

### jdk8-windows-build

面向 Windows 环境、必须使用 JDK 8 的 Maven 项目构建与失败诊断技能。

核心约束：

- 构建前必须发现或确认 JDK 8，并通过 `mvn -version` 验证 Maven 正在使用 Java 8。
- 默认使用仓库根 `pom.xml`；非根 POM 需显式传 `-PomPath`。
- 默认不启用离线、本地仓库覆盖或跳过测试；这些行为需显式传参。
- Gradle、Ant 和直接 `javac` 构建不在本技能执行范围内。

入口文档：[`jdk8-windows-build/SKILL.md`](jdk8-windows-build/SKILL.md)

### human-in-the-loop

HITL 0.0.1 人在回路协议入口，用于明确要求受控规划、固定批准、执行确认、审计链、高风险变更或任意环节可交接的编码流程。

核心能力：

- 启动分层：确认启用前只做 chat-only 建议；确认后才创建正式资产。
- 使用单一 `docs/changes/<中文变更>/manifest.yaml` 作为业务事实源。
- 使用唯一 `docs/changes/<中文变更>/human-view.html` 作为正式人类审核入口。
- 当前 agent 资产使用扁平布局 `agent/<artifact>.vN.yaml`，历史资产使用 `agent/archive/<artifact>.vN.yaml`。
- 支持 tiny / standard / strict tier，支持 implementation-package、asset-check 审计记录、Plan/Runbook、allowed-files gate、verification、close 与 reassessment。
- `human-view@current` 是 derived human-view registry 记录，不是 agent YAML asset。

核心约束：

- 不用于绕过人工决策；批准/确认事实只写入 manifest.decision_log。
- tiny / standard 批准命令：`批准方案: planning/implementation-package@vN`。
- strict 设计命令：`批准设计: planning/design@vN`。
- strict 蓝图命令：`批准蓝图: planning/blueprint@vN`。
- standard / strict 执行在修改文件前必须生成并确认 Plan / Runbook。
- 执行确认只能使用固定命令：`执行计划: execution/plan@vN` 或 `执行计划: execution/runbook@vN`。
- HTML 生成或 `transform_human_view.py --check` 失败时，不得请求批准或确认。
- 批准前必须有 completed/pass/pre-approval `checks/asset-check@vN`；生成 Plan/Runbook 前必须有 completed/pass/final `checks/asset-check@vN`。

入口文档：[`human-in-the-loop/SKILL.md`](human-in-the-loop/SKILL.md)  
脚本索引：[`human-in-the-loop/references/agent/script-index.md`](human-in-the-loop/references/agent/script-index.md)  
端到端命令链：[`human-in-the-loop/references/agent/e2e-command-chain.md`](human-in-the-loop/references/agent/e2e-command-chain.md)

### human-in-loop-brief

HITL 中文方案评审简报技能，用于读取 HITL 0.0.1 manifest、planning/checks/execution agent assets、验证和收尾记录，并生成可直接用于会议的中文《方案评审简报》。

核心约束：

- 只做资产解读和简报生成，不启动新的 HITL 流程。
- 正式事实优先来自 manifest 和 agent assets；HTML 仅作为人类审核入口证据。
- 重要结论必须可回溯到资料来源；缺失证据需明确标记。
- 最终输出必须遵循 [`human-in-loop-brief/references/brief-template.md`](human-in-loop-brief/references/brief-template.md)。

入口文档：[`human-in-loop-brief/SKILL.md`](human-in-loop-brief/SKILL.md)

### prd-writer

面向产品需求文档（PRD）的专业写作、改写、审查与标准化技能。

入口文档：[`prd-writer/SKILL.md`](prd-writer/SKILL.md)

### rigorous-contrarian-answers

严格反方/批判式回答技能，用于用户明确要求严谨、批判、逆向、无恭维、高细节、前提检验、论证压力测试或置信度分析的场景。

入口文档：[`rigorous-contrarian-answers/SKILL.md`](rigorous-contrarian-answers/SKILL.md)

### springboot-hcurl-generator

Spring Boot Controller 到 Hurl/.hcurl 接口测试脚本包的生成技能。

入口文档：[`springboot-hcurl-generator/SKILL.md`](springboot-hcurl-generator/SKILL.md)

## 资料与资产目录

- `docs/`：HITL 概念说明和仓库级资料。
- `docs/review/`：仓库内既有审查报告。
- `prompts/`：独立 prompt 草案或快捷入口，其中 `hitl.md` 用于 HITL 受控流程，`hilb.md` 用于简报生成。
- `human-in-the-loop/references/`：HITL agent/shared/human-view 参考资料。
- `human-in-loop-brief/references/brief-template.md`：中文方案评审简报模板。
- `prd-writer/references/`：PRD 路由、模板、质量清单、示例、测试用例和组织定制说明。

HITL 正式任务运行时通常会在目标项目的 `docs/changes/<中文变更>/` 下生成 manifest、HTML human view 和 agent assets；该路径是协议约定交付位置，不代表本仓库当前保存所有运行产物。

## 使用方式

1. 根据任务场景选择技能目录。
2. 先读取对应 `SKILL.md`，再按需读取 `references/`、脚本、测试夹具或 prompt 模板。
3. 若目标 agent 不会自动发现本仓库目录，按目标 agent 的安装方式安装或链接对应技能目录。
4. 受控流程使用 `human-in-the-loop`；最终会议材料或方案摘要使用 `human-in-loop-brief`。
5. 不要跳过前置事实收集、人工批准、确定性检查、scope gate、脚本校验或完成前验证。

## 维护约定

- 新增技能应使用独立目录，并至少提供 `SKILL.md` 作为入口文档。
- 技能目录应区分入口协议、参考资料、脚本、prompt 模板、测试夹具和资产文件。
- 根 `README.md` 负责登记仓库级目录与技能概览。
- 涉及构建、诊断、规划、执行、审查或输出纪律的强约束应写入技能文档，避免只存在于脚本或对话中。
- 仓库内审查报告默认保存到 `docs/review/`；HITL 运行资产按协议保存到目标项目的 `docs/changes/<中文变更>/...`。
