# Skills

本仓库用于沉淀可复用的 AI coding agent 技能,HITL 人在回路协议资料,工作流技能,通用回答/协作技能,以及少量特定技术栈辅助技能.

本仓库是技能源码与资料仓库,不声明仓库内目录会被目标 agent 自动发现.真实使用时,应按目标 agent 的技能安装方式,将需要的技能目录安装或链接到对应环境.

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
│   ├── orchestrate/
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
│   ├── workflow-subagent-router/
│   └── zoom-out/
├── agents/                          # pi subagent 定义
│   └── workflow/
│       ├── architect.md
│       ├── diagnostician.md
│       └── issue-steward.md
├── chains/                          # pi saved chain 定义
│   ├── workflow-context-gate.chain.json
│   ├── workflow-diagnose-to-tdd.chain.json
│   ├── workflow-implement-review.chain.json
│   ├── workflow-plan-only.chain.json
│   └── workflow-prd-to-issues.chain.json
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

`workflow/orchestrate` 是 workflow skills 的默认入口,负责在 `workflow/` 下的代码理解,诊断,需求澄清,原型,TDD,PRD,工单,triage,架构评审和 worktree 管理技能之间做路由与顺序编排.

`workflow/` 下的技能预期在目标项目仓库根目录工作.首次使用 `to-prd`,`to-issues`,`triage`,`diagnose`,`tdd`,`improve-codebase-architecture` 或 `zoom-out` 前,由 `orchestrate` 按需路由到 `setup-workspace` 生成约定文档.

目标项目推荐结构:

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

核心约定:

- 本地 Markdown issue tracker 固定使用 `docs/changes/<feature-slug>/`.
- 单上下文领域语言使用 `docs/language/UBIQUITOUS_LANGUAGE.md`.
- 多上下文项目使用 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md` 指向 `docs/language/contexts/*.md`.
- 系统级 ADR 位于 `docs/adr/*.md`;上下文级 ADR 位于 `docs/adr/contexts/<context>/`.
- `AGENTS.md` 中由 `setup-workspace` 写入 `## Docs Directory Structure` 区块.

入口文档:[`workflow/setup-workspace/SKILL.md`](workflow/setup-workspace/SKILL.md)

## Pi 子代理与 saved chains

最近一次提交新增了面向 pi 的 workflow subagent 路由资产. 这些资产不替代 `workflow/orchestrate`, 而是在工程任务需要 subagent 编排, 多阶段计划, 并行审查, 长任务 async 或标准化实现流程时使用.

- `workflow/workflow-subagent-router`: 父会话路由器. `orchestrate` 先判断 workflow 类型, router 再判断是否调用 saved chain 以及调用哪条 chain. 执行 chain 前必须向用户确认 `是否执行?`.
- `AGENTS.md`: 新增 workflow 子代理路由约束. 工程类任务先由 `orchestrate` 分类, 需要 subagent 编排时再读取 router, 默认单 writer.
- `agents/workflow/architect.md`: 架构评审, 模块边界, 重构候选, 可测试性和领域语言对齐. 默认只读, fresh context.
- `agents/workflow/diagnostician.md`: 未知根因诊断, 复现, 最小化, 假设, 验证和 TDD 修复建议. 默认只读, fresh context.
- `agents/workflow/issue-steward.md`: setup-workspace, PRD, tracer-bullet issues, triage, 标签和状态管理. 仅在父会话授权时改文档或 issue tracker.
- `chains/workflow-context-gate.chain.json`: 需求不清时并行收集请求 scope, 代码库上下文, 验证风险, 然后由父会话追问.
- `chains/workflow-plan-only.chain.json`: 先 scout, 再产出实现计划, 验收标准, 风险和验证命令, 不实现.
- `chains/workflow-implement-review.chain.json`: 单 worker 实现, fresh reviewers 并行审查正确性, 测试质量和简洁性, 再做 accepted fix pass.
- `chains/workflow-diagnose-to-tdd.chain.json`: 对未知根因问题先诊断, 再生成 TDD 修复计划, 默认不直接实现.
- `chains/workflow-prd-to-issues.chain.json`: 基于当前上下文生成 PRD draft, 再拆 tracer-bullet implementation issues.

入口文档: [`workflow/workflow-subagent-router/SKILL.md`](workflow/workflow-subagent-router/SKILL.md)

## 技能一览

### workflow/orchestrate

workflow skills 的默认入口和元编排器:接收工程类用户任务,按静态决策树在 `workflow/` skills 间路由,处理前置 `setup-workspace`,并支持多阶段顺序编排.

入口文档:[`workflow/orchestrate/SKILL.md`](workflow/orchestrate/SKILL.md)

### workflow/workflow-subagent-router

当 `orchestrate` 已完成任务类型判断, 且当前阶段需要 subagent 编排, saved chain, 多阶段计划, 并行审查或 async worker 时, 用它选择 `chains/workflow-*` 并保留父会话最终决策权.

入口文档: [`workflow/workflow-subagent-router/SKILL.md`](workflow/workflow-subagent-router/SKILL.md)

### workflow/setup-workspace

为目标项目建立 workflow 技能需要的本地工作区约定:`AGENTS.md`,`docs/agents/*`,本地 Markdown issue tracker,triage label 映射和领域文档布局.

入口文档:[`workflow/setup-workspace/SKILL.md`](workflow/setup-workspace/SKILL.md)

### workflow/grill-with-docs

围绕计划/设计进行拷问式澄清,并在术语或决策成形时更新 `docs/language/UBIQUITOUS_LANGUAGE.md` 或提出 ADR.

入口文档:[`workflow/grill-with-docs/SKILL.md`](workflow/grill-with-docs/SKILL.md)

### workflow/to-prd / workflow/to-issues / workflow/triage

面向本地 Markdown issue tracker 的需求与议题流程:

- `to-prd`:把当前对话上下文整理为 PRD,并发布到 `docs/changes/<feature-slug>/PRD.md`.
- `to-issues`:把 PRD/计划拆成垂直切片 issue,写入 `docs/changes/<feature-slug>/issues/`.
- `triage`:用 triage 状态机推进 issue,并在需要时维护 `.out-of-scope/`.

入口文档:

- [`workflow/to-prd/SKILL.md`](workflow/to-prd/SKILL.md)
- [`workflow/to-issues/SKILL.md`](workflow/to-issues/SKILL.md)
- [`workflow/triage/SKILL.md`](workflow/triage/SKILL.md)

### workflow/diagnose / workflow/tdd / workflow/zoom-out

代码理解,缺陷诊断和测试驱动实现流程:

- `diagnose`:复现,最小化,假设,插桩,修复,回归测试.
- `tdd`:按 red-green-refactor 小循环推进实现或修复.
- `zoom-out`:在陌生代码或跨模块调用链前先拉远视角.

入口文档:

- [`workflow/diagnose/SKILL.md`](workflow/diagnose/SKILL.md)
- [`workflow/tdd/SKILL.md`](workflow/tdd/SKILL.md)
- [`workflow/zoom-out/SKILL.md`](workflow/zoom-out/SKILL.md)

### workflow/improve-codebase-architecture

结合领域语言和 ADR,寻找代码库中的架构深化机会,输出可视化 HTML 架构评审报告,并可继续探索接口设计.

入口文档:[`workflow/improve-codebase-architecture/SKILL.md`](workflow/improve-codebase-architecture/SKILL.md)

### workflow/prototype

构建一次性原型,用于验证业务状态机,数据模型,终端交互或 UI 方案.

入口文档:[`workflow/prototype/SKILL.md`](workflow/prototype/SKILL.md)

### workflow/use-worktree

管理本地 Git worktree 标准布局,创建,检查,删除或迁移 worktree,并在修改前检查目标 worktree 状态以避免误改分支.

入口文档:[`workflow/use-worktree/SKILL.md`](workflow/use-worktree/SKILL.md)

### hitl/human-in-the-loop

HITL 0.0.1 人在回路协议入口,用于受控规划,固定批准,执行确认,审计链,高风险变更或可交接编码流程.

核心资产通常生成在目标项目:

```text
docs/changes/<中文变更>/
├── manifest.yaml
├── human-view.html
└── agent/
```

入口文档:[`hitl/human-in-the-loop/SKILL.md`](hitl/human-in-the-loop/SKILL.md)
脚本索引:[`hitl/human-in-the-loop/references/agent/script-index.md`](hitl/human-in-the-loop/references/agent/script-index.md)
端到端命令链:[`hitl/human-in-the-loop/references/agent/e2e-command-chain.md`](hitl/human-in-the-loop/references/agent/e2e-command-chain.md)

### hitl/human-in-loop-brief

读取 HITL manifest,planning/checks/execution agent assets,验证和收尾记录,生成中文"方案评审简报".

入口文档:[`hitl/human-in-loop-brief/SKILL.md`](hitl/human-in-loop-brief/SKILL.md)
简报模板:[`hitl/human-in-loop-brief/references/brief-template.md`](hitl/human-in-loop-brief/references/brief-template.md)

### general/*

通用交互/回答技能:

- [`general/grill-me/SKILL.md`](general/grill-me/SKILL.md):围绕计划持续追问直到达成共识.
- [`general/handoff/SKILL.md`](general/handoff/SKILL.md):交接上下文.
- [`general/rigorous-contrarian-answers/SKILL.md`](general/rigorous-contrarian-answers/SKILL.md):严格反方/批判式回答.
- [`general/telegraphic-style/SKILL.md`](general/telegraphic-style/SKILL.md):高密度电报式输出.
- [`general/write-a-skill/SKILL.md`](general/write-a-skill/SKILL.md):编写技能.

### others/*

特定技术栈辅助技能:

- [`others/cz-sdk-windows-build/SKILL.md`](others/cz-sdk-windows-build/SKILL.md):Windows 上按 JDK 8 工作流构建/诊断 cz_sdk 相关 Maven 项目.
- [`others/springboot-hcurl-generator/SKILL.md`](others/springboot-hcurl-generator/SKILL.md):从 Spring Boot Controller 生成 Hurl/.hcurl 接口测试脚本包.

## 使用方式

1. 根据任务场景选择技能目录.
2. 先读取对应 `SKILL.md`,再按需读取 `references/`,脚本,测试夹具或 prompt 模板.
3. 若目标 agent 不会自动发现本仓库目录,按目标 agent 的安装方式安装或链接对应技能目录.
4. workflow 类任务优先进入 `workflow/orchestrate`;由它按需运行 `workflow/setup-workspace` 建立目标项目约定.
5. 需要 pi subagent 编排, saved chain, 多阶段计划, 并行审查或 async worker 时, 在 `orchestrate` 分类后读取 `workflow/workflow-subagent-router`.
6. 高风险或需要人工批准的任务使用 `hitl/human-in-the-loop`;最终会议材料或方案摘要使用 `hitl/human-in-loop-brief`.

## 维护约定

- 新增技能应使用独立目录,并至少提供 `SKILL.md` 作为入口文档.
- 技能目录应区分入口协议,参考资料,脚本,prompt 模板,测试夹具和资产文件.
- 根 `README.md` 负责登记仓库级目录, 技能概览, pi agents 和 saved chains.
- 涉及构建,诊断,规划,执行,审查或输出纪律的强约束应写入技能文档,避免只存在于脚本或对话中.
- workflow 目标项目的需求/议题资产默认保存到 `docs/changes/<feature-slug>/...`.
- HITL 正式任务运行资产按协议保存到目标项目的 `docs/changes/<中文变更>/...`.
