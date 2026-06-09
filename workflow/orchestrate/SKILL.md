---
name: orchestrate
description: workflow skills 的默认入口和元编排器,接收软件工程类任务并在 setup-workspace/use-worktree/diagnose/zoom-out/improve-codebase-architecture/grill-with-docs/prototype/run-afk-workflow/tdd/to-prd/to-issues/to-plan/triage 间做静态路由/前置检查/顺序编排.当用户提出任何可能涉及代码理解/诊断/需求澄清/原型/AFK 执行/TDD/PRD/工单/执行计划/triage/架构评审或 worktree 管理的工程任务时优先使用本 skill;仅当用户明确点名某个下游 skill 或已处于该流程中时直接使用下游 skill.
---

# Orchestrate

工程 workflow 的默认入口.本 skill 只负责路由/前置检查和顺序编排;选中目标 workflow 后,读取目标 skill 的 `SKILL.md` 并按其流程执行,不要把下游流程复制到这里.

## 本 skill 管理的 workflow skills

本文档所说的 workflow skills 明确指以下 skill 名称:

- `setup-workspace`--建立本地 Markdown issue tracker,triage label,领域文档布局等前置约定.
- `use-worktree`--管理 Git worktree / repo 布局 / 分支隔离,避免改错分支.
- `diagnose`--处理未知根因 bug,失败,报错,性能回退.
- `zoom-out`--只读理解陌生代码,调用链,数据流和影响范围.
- `improve-codebase-architecture`--做架构评审,重构候选,模块深化和可测试性建议.
- `grill-with-docs`--结合代码,领域语言和 ADR 澄清新功能/新规则/需求边界.
- `prototype`--构建一次性逻辑/状态机/UI 原型验证设计问题.
- `run-afk-workflow`--在符合 AFK 调用条件后进入 AFK 阶段执行.
- `tdd`--在行为明确时用 red-green-refactor 测试驱动实现或修复.
- `to-prd`--把当前上下文沉淀为 PRD.
- `to-issues`--把已成形计划/PRD 拆为 tracer bullets 式执行工单.
- `to-plan`--为 to-issues 产出的所有 issues 生成合并源码级执行计划,供人类审核后由 AFK agent 执行. 由 to-issues 完成后 orchestrate 主动询问; 也可显式点名.
- `triage`--创建,分流,推进,审查单个 issue,管理状态,标签和 brief.

`grill-me` 不是 workflow skill,但可作为路由不确定时的澄清工具;澄清后必须回到本决策树.

## 核心原则

- **宽触发**:任何工程类任务先经过本 skill 判断.
- **静态路由**:决策树固化在本文档中;workflow skills 演进时同步更新本文档.
- **尊重显式指定**:用户明确点名某个 workflow skill 时直接进入该 skill;若明显误用,指出冲突并询问是否改路由.
- **不启动 workflow 也继续处理**:如果任务清楚且不需要任何 workflow,回复开头用一行短句说明原因,然后按普通助手任务继续完成.
- **启用 workflow 不加固定说明行**:直接读取并执行目标 skill.
- **模糊路由用 `grill-me`**:当无法高置信选择 workflow 时,调用 `grill-me` 澄清;澄清完成后回到本决策树.
- **顺序编排**:一个任务可依次经过多个 workflow;每阶段结束后回到本决策树判断下一阶段.不并行编排.

## 不启动 workflow

当任务清楚,很小,或不属于 workflow 能力时,不要强行套流程.格式:

```md
不启动 workflow: <一句话原因>.
<继续直接处理用户任务>
```

示例:小范围机械编辑,普通问答,解释一个正则,简单文件查看,无需工程流程的写作任务.

## 前置检查

### 1. 显式指定

如果用户明确要求使用某个 workflow skill,直接读取并执行它:

- `orchestrate` / 编排 / 选 workflow -> 留在本 skill
- `setup-workspace`/`use-worktree`/`diagnose`/`zoom-out`/`improve-codebase-architecture`/`grill-with-docs`/`prototype`/`tdd`/`to-prd`/`to-issues`/`to-plan`/`triage` -> 读取对应 skill 的 `SKILL.md`
- `run-afk-workflow` -> 先判断是否符合本 skill 的调用条件. 符合后读取该 skill. 不符合时,转入对应前置 workflow 或询问用户.

若显式指定与任务性质强冲突,先指出冲突并问一个问题.例:未知根因线上报错却要求直接 `tdd`,建议先 `diagnose`.

### 2. worktree 安全硬匹配

仅当用户明确提到 worktree/repo 布局/分支隔离/避免改错分支/创建/删除/迁移 worktree 时,先执行 `use-worktree`.完成后回到本决策树处理剩余任务.

### 3. setup-workspace 前置

当将要使用 `to-prd` / `to-issues` / `to-plan` / `triage` / `diagnose` / `tdd` / `improve-codebase-architecture` / `zoom-out`,且目标仓库缺少 `docs/agents/*`/`docs/changes/`/`docs/language/` 等 workflow 约定时,先执行 `setup-workspace`.

不要对所有任务无脑 setup:`prototype`/`use-worktree`/纯路由澄清/以及无需仓库约定的小任务不强制 setup.

### 4. run-afk-workflow 调用条件

`run-afk-workflow` 受本 skill 管理. 本 skill 只决定何时进入 AFK, 不展开 AFK 内部阶段细则.

仅在以下情况读取 `run-afk-workflow`:

- 用户显式要求 AFK, 子代理或后台执行, 且已有已批准的执行对象.
- `to-plan` 已完成, 用户确认执行某个 milestone.
- 当前已有 AFK run checkpoint, 需要继续, review 或 fix.
- 父会话需要短只读代码事实来压缩上下文, 且不需要完整 `zoom-out` 报告.

以下情况不要调用 `run-afk-workflow`:

- 未知根因 bug, 异常, 测试失败或性能回退.
- 需求边界, 验收标准, allowed files, plan 或 issue 缺失.
- dirty worktree 归属不清.
- 需要产品/API/架构/范围判断.
- 用户只是要求普通实现或修复, 且没有要求 AFK/子代理/后台执行.

## 决策树

按顺序判断;命中后读取目标 skill 并执行.

1. **Git worktree / repo 布局管理** -> `use-worktree`
   明确要求创建/删除/迁移/选择 worktree,或强调分支隔离/避免改错分支.

2. **未知根因 bug / 异常 / 报错 / 测试失败 / 性能回退** -> `diagnose`
   目标是定位原因或修复失败;先建立复现反馈循环.根因和期望行为已明确且用户要测试先行时再考虑 `tdd`.

3. **陌生模块 / 跨包调用链 / 历史代码 / 影响范围不清,目标是理解** -> `zoom-out`
   只读拉远视角,输出相关模块,调用方和数据流地图.如果用户要重构候选或架构改进,改走 `improve-codebase-architecture`.

4. **架构优化 / 降复杂度 / 模块边界 / 可测试性改善 / 重构候选报告** -> `improve-codebase-architecture`
   默认输出报告和建议,不直接大重构.

5. **新功能 / 新流程 / 新接口 / 新业务规则,需求边界不清但工程路由清楚** -> `grill-with-docs`
   用项目领域语言,代码事实和 ADR 压力测试计划;必要时更新词汇表或提出 ADR.

6. **需要先用可运行东西验证状态机/数据模型/业务逻辑或 UI 方案** -> `prototype`
   构建一次性原型.状态/业务逻辑走终端交互原型;UI 走多变体页面原型.

7. **AFK 执行 / review / fix** -> `run-afk-workflow`
   仅当符合 `run-afk-workflow 调用条件` 时读取该 skill. 具体 AFK 阶段选择和运行约束由 `run-afk-workflow` 管理.

8. **行为已明确,要实现或修复,且适合测试先行** -> `tdd`
   使用 red-green-refactor 和 tracer bullet 小循环.未知根因失败先回到 `diagnose`.

9. **要把当前上下文沉淀为 PRD** -> `to-prd`
   不再访谈用户,综合已有上下文和代码理解写 PRD.

10. **要把已成形计划 / PRD 拆为执行工单** -> `to-issues`
   使用 tracer bullets 式垂直切片拆分.

11. **to-issues 已完成, 要生成源码级执行计划** -> `to-plan`
   当 `to-issues` 阶段完成后, orchestrate 主动询问用户是否需要生成执行计划.

12. **要创建,分流,推进,审查单个 issue,或管理标签/状态/brief** -> `triage`
   issue tracker 状态机和 agent brief 由该 skill 处理.

13. **路由仍不确定** -> `grill-me`
   只用于缩小路由空间.一次问一个问题,提供推荐答案;确认后回到本决策树.

14. **无 workflow 匹配且任务清楚** -> 不启动 workflow
   用规定格式说明原因,然后继续直接处理用户任务.

## 多阶段编排

常见链路:

- `use-worktree` -> 回到本 skill -> `diagnose` / `tdd`
- `zoom-out` -> 回到本 skill -> `grill-with-docs` / `to-issues` / `tdd`
- `grill-with-docs` -> 回到本 skill -> `to-prd` -> `to-issues` -> (可选) `to-plan` -> 用户确认 -> `run-afk-workflow`
- `prototype` -> 用户确认 -> 回到本 skill -> `to-prd` / `tdd`
- `diagnose` -> 根因明确 + 回归接缝存在 -> `tdd` 或继续按 `diagnose` 的修复/回归阶段执行
- `to-plan` -> 用户确认执行某个 milestone -> `run-afk-workflow`
- `run-afk-workflow` -> review/fix/final validation -> 回到本 skill 判断下一步

每阶段完成时判断是否有明确下一阶段.若下一阶段依赖用户确认,停下等待;不要预先启动多个 workflow.
