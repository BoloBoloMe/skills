---
asset_id: hilp-superpowers-skills-blueprint-slice-package-structure
artifact_name: stage-4-5/blueprint-slice-package-structure
version: v1
state: approved
state_label: 已批准
owner_skill: hilp-blueprint
created_from: stage-4-5/implementation-blueprint@v1
last_event: human-approval-granted
last_decision: human-approval-2026-04-28-blueprint-package-v1
approval_marker: approved
approval_marker_label: 已批准
asset_path: D:/Workspace/skills/docs/hilp/构建中文裁剪版Superpowers技能/03-实施蓝图_approved_blueprint-slice-package-structure@v1.md
blueprint_form: package-slice
parent_blueprint: stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]
---

# 实施蓝图切片：包结构与仓库登记

## 职责边界
创建 `human-in-loop-execution/` 的外层结构、入口文档和仓库 README 登记，不写执行规则细节。

## 前置依赖
- 已批准设计：`stage-3/design-choice@v3 [state=approved｜中文状态=已批准]`。
- 当前切片依赖 manifest：`stage-4-5/implementation-blueprint@v1`。

## 禁止越界项
- 不创建 `superpowers-skills/`。
- 不修改 `superpowers/`。
- 不修改 `human-in-loop-planning/`。
- 不创建任何 worktree 技能入口。
- 不写原始 Superpowers brainstorming/spec approval 的替代实现。

## 涉及文件范围
创建：
- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/README.md`
- `human-in-loop-execution/references/`
- `human-in-loop-execution/references/prompt-templates/`

修改：
- `README.md`

## 数据形状
`human-in-loop-execution/README.md` 固定包含以下章节：
```text
# human-in-loop-execution
## 定位
## 与 human-in-loop-planning 的关系
## 保留能力
## 明确不包含
## 安装与使用边界
## 目录结构
```

仓库根 `README.md` 固定新增：
- 目录结构条目：`human-in-loop-execution/`。
- 技能一览章节：`human-in-loop-execution`。
- 说明：该技能包服务 HILP 执行交接后的执行纪律，不负责规划审批。

## 接口约束
- `SKILL.md` frontmatter 固定使用：
```yaml
---
name: human-in-loop-execution
description: Use when HILP execution handoff has been approved and implementation, testing, review, debugging, or branch finishing needs execution discipline
---
```
- README 不声明仓库内技能会被 agents 自动发现。
- README 明确真实使用时由用户从仓库安装到目标 agent 环境。

## 局部算法骨架
1. 检查 `human-in-loop-execution/` 是否存在。
2. 若不存在，创建目录和 `references/prompt-templates/`。
3. 写入 `SKILL.md` 入口协议骨架。
4. 写入 `human-in-loop-execution/README.md`。
5. 修改仓库根 `README.md` 的目录结构和技能一览。

## 错误处理要求
- 若 `human-in-loop-execution/` 已存在，停止写入并报告冲突。
- 若 `README.md` 不包含可定位的目录结构或技能一览区域，停止修改根 README 并报告需要人工确认插入位置。

## 测试承诺
- 文件存在性检查。
- frontmatter 名称检查。
- 根 README 包含 `human-in-loop-execution` 检查。
- 确认未创建 `superpowers-skills`。

## 局部确定性检查
- 未确定项：无。
- 模糊表达：无。
- 需要执行者自行裁量的实现决策：无。