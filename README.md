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
│   ├── run-afk-workflow/
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

## Pi 子代理 direct recipes

AFK 采用 direct `subagent({...})` recipes, 不依赖仓库级 chain JSON 自动发现. 这些资产受 `workflow/orchestrate` 管理, 不替代 `workflow/orchestrate`, 也不把需求对齐, 方案制定, PRD, issue 拆分或执行决策外包给子代理.

- `workflow/run-afk-workflow`: AFK 阶段入口. `orchestrate` 先判断 workflow 类型和调用条件, 本技能只判断是否调用只读代码库探索 direct recipe, implement-only direct recipe, review-only direct recipe 或 fix-only direct recipe. 执行写入阶段前必须向用户确认 `是否执行?`.
- `workflow/run-afk-workflow/AFK-RECIPES.md`: 可复制 direct `subagent({...})` 模板. AFK writer 默认使用 builtin `worker`, 并通过 one-step `chain` 的 step 参数设置 `context:"fresh"`, `reads:false`, `progress:false`, `chainDir:<AFK_RUN_DIR>`, `outputMode:"file-only"` 等关键项.
- `workflow/run-afk-workflow/AFK-RUNBOOK.md`: AFK 状态机, preflight, artifact 布局, review synthesis, fix scope 和 failure recovery.
- `AGENTS.md`: workflow 路由约束. 工程类任务先由 `orchestrate` 分类. 子代理只用于只读代码库探索, 已批准计划的 AFK 编码执行, diff 后 review, 或 accepted finding 修复.

本仓库不维护 workflow chain JSON. 如目标项目需要 chain 文件, 由目标项目自行维护. 本仓库只维护 direct recipes 文档.

入口文档: [`workflow/run-afk-workflow/SKILL.md`](workflow/run-afk-workflow/SKILL.md)

## 技能一览

### workflow/orchestrate

workflow skills 的默认入口和元编排器:接收工程类用户任务,按静态决策树在 `workflow/` skills 间路由,处理前置 `setup-workspace`,并支持多阶段顺序编排.

入口文档:[`workflow/orchestrate/SKILL.md`](workflow/orchestrate/SKILL.md)

### workflow/run-afk-workflow

`run-afk-workflow` 是 `orchestrate` 管辖下的 AFK 阶段入口. 当 `orchestrate` 已完成任务类型判断并符合 AFK 调用条件, 且当前阶段需要只读代码库探索以压缩上下文, 或需要已批准计划的 AFK 单阶段编码执行, diff 后 review, accepted finding 修复时, 用它选择 direct `subagent({...})` recipe 并保留父会话最终决策权. 运行模板见 [`workflow/run-afk-workflow/AFK-RECIPES.md`](workflow/run-afk-workflow/AFK-RECIPES.md), 运行细节见 [`workflow/run-afk-workflow/AFK-RUNBOOK.md`](workflow/run-afk-workflow/AFK-RUNBOOK.md).

入口文档: [`workflow/run-afk-workflow/SKILL.md`](workflow/run-afk-workflow/SKILL.md)

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

入口文档:[`hitl/human-in-the-loop/SKILL.md`](deprecated/hitl/human-in-the-loop/SKILL.md)
脚本索引:[`hitl/human-in-the-loop/references/agent/script-index.md`](deprecated/hitl/human-in-the-loop/references/agent/script-index.md)
端到端命令链:[`hitl/human-in-the-loop/references/agent/e2e-command-chain.md`](deprecated/hitl/human-in-the-loop/references/agent/e2e-command-chain.md)

### hitl/human-in-loop-brief

读取 HITL manifest,planning/checks/execution agent assets,验证和收尾记录,生成中文"方案评审简报".

入口文档:[`hitl/human-in-loop-brief/SKILL.md`](deprecated/hitl/human-in-loop-brief/SKILL.md)
简报模板:[`hitl/human-in-loop-brief/references/brief-template.md`](deprecated/hitl/human-in-loop-brief/references/brief-template.md)

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
5. 需要只读代码库探索以压缩上下文, 或需要已批准计划的 AFK 编码执行, diff 后 review, accepted finding 修复时, 由 `orchestrate` 判断符合 AFK 调用条件后读取 `workflow/run-afk-workflow`.
6. 高风险或需要人工批准的任务使用 `hitl/human-in-the-loop`;最终会议材料或方案摘要使用 `hitl/human-in-loop-brief`.

## 维护约定

- 新增技能应使用独立目录,并至少提供 `SKILL.md` 作为入口文档.
- 技能目录应区分入口协议,参考资料,脚本,prompt 模板,测试夹具和资产文件.
- 根 `README.md` 负责登记仓库级目录, 技能概览和 pi direct recipes.
- 涉及构建,诊断,规划,执行,审查或输出纪律的强约束应写入技能文档,避免只存在于脚本或对话中.
- workflow 目标项目的需求/议题资产默认保存到 `docs/changes/<feature-slug>/...`.
- HITL 正式任务运行资产按协议保存到目标项目的 `docs/changes/<中文变更>/...`.
