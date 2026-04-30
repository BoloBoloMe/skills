---
asset_id: hilp-superpowers-skills-blueprint-slice-quality-and-meta
artifact_name: stage-4-5/blueprint-slice-quality-and-meta
version: v1
state: approved
state_label: 已批准
owner_skill: hilp-blueprint
created_from: stage-4-5/implementation-blueprint@v1
last_event: human-approval-granted
last_decision: human-approval-2026-04-28-blueprint-package-v1
approval_marker: approved
approval_marker_label: 已批准
asset_path: D:/Workspace/skills/docs/changes/构建中文裁剪版Superpowers技能/planning/assets/03-实施蓝图_approved_blueprint-slice-quality-and-meta@v1.md
blueprint_form: package-slice
parent_blueprint: stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]
---

# 实施蓝图切片：质量辅助与元技能

## 职责边界
写入根因调试、完成前验证、并行 agent、技能编写元纪律，以及执行协议需要的 prompt/reference 支撑文件。

## 前置依赖
- `package-structure` 切片已创建目录。

## 禁止越界项
- 不创建源仓测试工程。
- 不复制上游插件配置、hooks 或 commands。
- 不把 `writing-skills` 放入普通业务开发主链路。
- 不要求执行者在未获 HILP 执行交接时使用这些能力推进实现。

## 涉及文件范围
创建并写入：
- `human-in-loop-execution/references/systematic-debugging.md`
- `human-in-loop-execution/references/verification-before-completion.md`
- `human-in-loop-execution/references/dispatching-parallel-agents.md`
- `human-in-loop-execution/references/writing-skills.md`
- `human-in-loop-execution/references/prompt-templates/implementer-prompt.md`
- `human-in-loop-execution/references/prompt-templates/spec-reviewer-prompt.md`
- `human-in-loop-execution/references/prompt-templates/code-quality-reviewer-prompt.md`
- `human-in-loop-execution/references/prompt-templates/code-reviewer.md`
- `human-in-loop-execution/references/prompt-templates/plan-document-reviewer-prompt.md`
- `human-in-loop-execution/references/testing-anti-patterns.md`
- `human-in-loop-execution/references/root-cause-tracing.md`
- `human-in-loop-execution/references/defense-in-depth.md`
- `human-in-loop-execution/references/condition-based-waiting.md`

## 数据形状
- `systematic-debugging.md` 固定保留四阶段：根因调查、模式分析、假设验证、实现修复。
- `verification-before-completion.md` 固定保留“没有新鲜验证证据，不得声明完成”。
- `dispatching-parallel-agents.md` 固定要求并行任务互不共享状态、无顺序依赖、不会编辑同一文件集。
- `writing-skills.md` 固定声明仅用于创建或修改技能，要求先有失败压力场景，再写技能文档。
- prompt templates 固定中文化源仓模板，并新增 HILP 资产引用字段：
```text
HILP design asset_ref:
HILP blueprint asset_ref:
HILP execution handoff asset_ref:
禁止越界项:
```

## 接口约束
- `systematic-debugging.md` 发现修复会改变蓝图、接口、数据形状或执行范围时，必须停止并回到 HILP 重审。
- `verification-before-completion.md` 的完成声明必须引用实际命令和输出摘要。
- `dispatching-parallel-agents.md` 禁止多个 agent 并行编辑同一文件或同一 HILP 资产。
- `writing-skills.md` 仅服务本仓库技能维护；业务开发不得用它替代 HILP 方案设计。

## 局部算法骨架
1. 将源仓 `systematic-debugging` 的四阶段过程中文化并加入 HILP 回退条件。
2. 将源仓 `verification-before-completion` 的证据优先原则中文化。
3. 将源仓 `dispatching-parallel-agents` 的独立域判定中文化并加入执行交接范围约束。
4. 将源仓 `writing-skills` 的技能 TDD 规则中文化并限定为元技能。
5. 中文化五个 prompt template，并加入 HILP 资产引用字段。
6. 中文化测试反模式、根因追踪、防御式验证和条件等待参考文件。

## 错误处理要求
- 若调试发现不是实现问题而是蓝图问题，停止修复并输出 HILP 重审请求。
- 若并行 agent 任务存在共享文件或顺序依赖，改用顺序执行，不并行派发。
- 若技能编写缺少压力场景，停止写技能并要求先补测试场景。

## 测试承诺
- grep 检查 `HILP`、`执行交接` 和 `禁止越界项` 出现在 prompt templates 中。
- grep 检查 `没有新鲜验证证据` 出现在完成前验证文件中。
- grep 检查 `根因` 出现在系统调试文件中。

## 局部确定性检查
- 未确定项：无。
- 模糊表达：无。
- 需要执行者自行裁量的实现决策：无。