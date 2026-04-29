asset_id: hilp-execution-capability-restoration-slice-meta-skill
artifact_name: stage-4-5/blueprint-slice-meta-skill
version: v1
state: ready-for-approval
state_label: 待审批
owner_skill: human-in-loop-planning
created_from: stage-3/design-choice@v1 [state=approved｜中文状态=已批准]
last_event: none
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批

# 子蓝图：meta-skill

## 适用范围

本切片补强技能编写元纪律，防止后续维护 `human-in-loop-execution/` 时继续无压力场景、无验证地退化。

## 所属主蓝图

- `stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`

## 文件范围

- 修改：`human-in-loop-execution/references/writing-skills.md`

## 职责边界

- 只服务技能创建、修改和验证。
- 不替代 HILP 需求、设计、审批或蓝图。
- 不恢复 Superpowers 插件、hooks、commands、测试工程或贡献流程。

## 具体改动约束

### `writing-skills.md`

必须补入：

- 核心原则：技能编写是文档 TDD。
- 铁律：没有失败压力场景，不写或修改技能。
- RED：运行无技能或旧技能基线，记录失败行为和 rationalization。
- GREEN：写最小技能内容，解决已观察失败。
- REFACTOR：发现新漏洞后补规则并复测。
- description 规则：只写触发条件，不写完整流程摘要。
- 搜索优化规则：关键词、触发症状、具体场景、避免 workflow summary。
- 文件组织规则：主 `SKILL.md`、supporting reference、prompt template 的使用边界。
- 压力场景类别：纪律型、技术型、参考型、pattern 型。
- 部署前 checklist：frontmatter、触发条件、压力场景、验证证据、禁止越界项。

## 局部风险检查点

- 不得允许“文档小改”跳过压力场景。
- 不得把业务审批流程写入执行技能。
- 不得新增蓝图外技能入口。

## 局部验证命令

```bash
grep -n "文档 TDD\|压力场景" human-in-loop-execution/references/writing-skills.md
grep -n "RED\|GREEN\|REFACTOR" human-in-loop-execution/references/writing-skills.md
grep -n "description" human-in-loop-execution/references/writing-skills.md
grep -n "frontmatter\|检查清单" human-in-loop-execution/references/writing-skills.md
```

## 确定性检查

- 未确定项：无。
- 模糊表达：无。
- 需要执行者自行裁量的规划判断：无。
- 禁止越界项：不触碰 `superpowers/`。
