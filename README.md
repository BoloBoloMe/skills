# Skills

本仓库用于沉淀可复用的 AI coding agent 技能、HITL 人在回路协议资料、工作流技能、通用回答/协作技能，以及少量特定技术栈辅助技能。

本仓库是技能源码与资料仓库，不声明仓库内目录会被目标 agent 自动发现。真实使用时，应按目标 agent 的技能安装方式，将需要的技能目录安装或链接到对应环境。

## 当前目录

```text
.
├── general/                         # 通用交互与写作类技能
│   ├── grill-me/
│   ├── handoff/
│   ├── rigorous-contrarian-answers/
│   ├── telegraphic-style/
│   └── write-a-skill/
├── workflow/                        # 面向代码库工作的流程技能
│   ├── setup-workspace/
│   ├── grill-with-docs/
│   ├── diagnose/
│   ├── tdd/
│   ├── to-prd/
│   ├── to-issues/
│   ├── triage/
│   ├── improve-codebase-architecture/
│   ├── prototype/
│   ├── use-worktree/
│   └── zoom-out/
├── hitl/                            # HITL 0.0.1 协议与简报技能
│   ├── human-in-the-loop/
│   │   ├── references/{agent,shared,human-view}/...
│   │   ├── scripts/*.py
│   │   └── tests/...
│   └── human-in-loop-brief/
├── others/                          # 特定技术栈/项目辅助技能
│   ├── cz-sdk-windows-build/
│   └── springboot-hcurl-generator/
├── prompts/                         # 独立 prompt 草案或快捷入口
├── AGENTS.md
└── README.md
```

## Workflow 工作区约定

`workflow/` 下的技能预期在目标项目仓库根目录工作。首次使用 `to-prd`、`to-issues`、`triage`、`diagnose`、`tdd`、`improve-codebase-architecture` 或 `zoom-out` 前，先运行/安装 `setup-workspace` 生成约定文档。

目标项目推荐结构：

```text
project-root/
├── AGENTS.md
├── docs/
│   ├── agents/
│   │   ├── issue-tracker.md
│   │   ├── triage-labels.md
│   │   └── domain.md
│   ├── language/
│   │   ├── UBIQUITOUS_LANGUAGE.md
│   │   ├── UBIQUITOUS_LANGUAGE_MAP.md      # 仅多上下文项目需要
│   │   └── contexts/                       # 多上下文语言文件
│   ├── adr/
│   │   ├── 0001-system-level-decision.md
│   │   └── contexts/                       # 多上下文 ADR
│   └── changes/
│       └── <feature-slug>/
│           ├── PRD.md
│           └── issues/
│               └── 01-slice.md
└── src/
```

核心约定：

- 本地 Markdown issue tracker 固定使用 `docs/changes/<feature-slug>/`。
- 单上下文领域语言使用 `docs/language/UBIQUITOUS_LANGUAGE.md`。
- 多上下文项目使用 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md` 指向 `docs/language/contexts/*.md`。
- 系统级 ADR 位于 `docs/adr/*.md`；上下文级 ADR 位于 `docs/adr/contexts/<context>/`。
- `AGENTS.md` 中由 `setup-workspace` 写入 `## Docs Directory Structure` 区块。

入口文档：[`workflow/setup-workspace/SKILL.md`](workflow/setup-workspace/SKILL.md)

## 技能一览

### workflow/setup-workspace

为目标项目建立 workflow 技能需要的本地工作区约定：`AGENTS.md`、`docs/agents/*`、本地 Markdown issue tracker、triage label 映射和领域文档布局。

入口文档：[`workflow/setup-workspace/SKILL.md`](workflow/setup-workspace/SKILL.md)

### workflow/grill-with-docs

围绕计划/设计进行拷问式澄清，并在术语或决策成形时更新 `docs/language/UBIQUITOUS_LANGUAGE.md` 或提出 ADR。

入口文档：[`workflow/grill-with-docs/SKILL.md`](workflow/grill-with-docs/SKILL.md)

### workflow/to-prd / workflow/to-issues / workflow/triage

面向本地 Markdown issue tracker 的需求与议题流程：

- `to-prd`：把当前对话上下文整理为 PRD，并发布到 `docs/changes/<feature-slug>/PRD.md`。
- `to-issues`：把 PRD/计划拆成垂直切片 issue，写入 `docs/changes/<feature-slug>/issues/`。
- `triage`：用 triage 状态机推进 issue，并在需要时维护 `.out-of-scope/`。

入口文档：

- [`workflow/to-prd/SKILL.md`](workflow/to-prd/SKILL.md)
- [`workflow/to-issues/SKILL.md`](workflow/to-issues/SKILL.md)
- [`workflow/triage/SKILL.md`](workflow/triage/SKILL.md)

### workflow/diagnose / workflow/tdd / workflow/zoom-out

代码理解、缺陷诊断和测试驱动实现流程：

- `diagnose`：复现、最小化、假设、插桩、修复、回归测试。
- `tdd`：按 red-green-refactor 小循环推进实现或修复。
- `zoom-out`：在陌生代码或跨模块调用链前先拉远视角。

入口文档：

- [`workflow/diagnose/SKILL.md`](workflow/diagnose/SKILL.md)
- [`workflow/tdd/SKILL.md`](workflow/tdd/SKILL.md)
- [`workflow/zoom-out/SKILL.md`](workflow/zoom-out/SKILL.md)

### workflow/improve-codebase-architecture

结合领域语言和 ADR，寻找代码库中的架构深化机会，输出可视化 HTML 架构评审报告，并可继续探索接口设计。

入口文档：[`workflow/improve-codebase-architecture/SKILL.md`](workflow/improve-codebase-architecture/SKILL.md)

### workflow/prototype

构建一次性原型，用于验证业务状态机、数据模型、终端交互或 UI 方案。

入口文档：[`workflow/prototype/SKILL.md`](workflow/prototype/SKILL.md)

### workflow/use-worktree

管理本地 Git worktree 标准布局，创建、检查、删除或迁移 worktree，并在修改前检查目标 worktree 状态以避免误改分支。

入口文档：[`workflow/use-worktree/SKILL.md`](workflow/use-worktree/SKILL.md)

### hitl/human-in-the-loop

HITL 0.0.1 人在回路协议入口，用于受控规划、固定批准、执行确认、审计链、高风险变更或可交接编码流程。

核心资产通常生成在目标项目：

```text
docs/changes/<中文变更>/
├── manifest.yaml
├── human-view.html
└── agent/
```

入口文档：[`hitl/human-in-the-loop/SKILL.md`](hitl/human-in-the-loop/SKILL.md)  
脚本索引：[`hitl/human-in-the-loop/references/agent/script-index.md`](hitl/human-in-the-loop/references/agent/script-index.md)  
端到端命令链：[`hitl/human-in-the-loop/references/agent/e2e-command-chain.md`](hitl/human-in-the-loop/references/agent/e2e-command-chain.md)

### hitl/human-in-loop-brief

读取 HITL manifest、planning/checks/execution agent assets、验证和收尾记录，生成中文《方案评审简报》。

入口文档：[`hitl/human-in-loop-brief/SKILL.md`](hitl/human-in-loop-brief/SKILL.md)  
简报模板：[`hitl/human-in-loop-brief/references/brief-template.md`](hitl/human-in-loop-brief/references/brief-template.md)

### general/*

通用交互/回答技能：

- [`general/grill-me/SKILL.md`](general/grill-me/SKILL.md)：围绕计划持续追问直到达成共识。
- [`general/handoff/SKILL.md`](general/handoff/SKILL.md)：交接上下文。
- [`general/rigorous-contrarian-answers/SKILL.md`](general/rigorous-contrarian-answers/SKILL.md)：严格反方/批判式回答。
- [`general/telegraphic-style/SKILL.md`](general/telegraphic-style/SKILL.md)：高密度电报式输出。
- [`general/write-a-skill/SKILL.md`](general/write-a-skill/SKILL.md)：编写技能。

### others/*

特定技术栈辅助技能：

- [`others/cz-sdk-windows-build/SKILL.md`](others/cz-sdk-windows-build/SKILL.md)：Windows 上按 JDK 8 工作流构建/诊断 cz_sdk 相关 Maven 项目。
- [`others/springboot-hcurl-generator/SKILL.md`](others/springboot-hcurl-generator/SKILL.md)：从 Spring Boot Controller 生成 Hurl/.hcurl 接口测试脚本包。

## 使用方式

1. 根据任务场景选择技能目录。
2. 先读取对应 `SKILL.md`，再按需读取 `references/`、脚本、测试夹具或 prompt 模板。
3. 若目标 agent 不会自动发现本仓库目录，按目标 agent 的安装方式安装或链接对应技能目录。
4. workflow 类任务优先运行 `workflow/setup-workspace` 建立目标项目约定。
5. 高风险或需要人工批准的任务使用 `hitl/human-in-the-loop`；最终会议材料或方案摘要使用 `hitl/human-in-loop-brief`。

## 维护约定

- 新增技能应使用独立目录，并至少提供 `SKILL.md` 作为入口文档。
- 技能目录应区分入口协议、参考资料、脚本、prompt 模板、测试夹具和资产文件。
- 根 `README.md` 负责登记仓库级目录与技能概览。
- 涉及构建、诊断、规划、执行、审查或输出纪律的强约束应写入技能文档，避免只存在于脚本或对话中。
- workflow 目标项目的需求/议题资产默认保存到 `docs/changes/<feature-slug>/...`。
- HITL 正式任务运行资产按协议保存到目标项目的 `docs/changes/<中文变更>/...`。
