---
name: to-plan
description: 为 to-issues 产出的所有 issues 生成合并源码级执行计划, 包含代码修改边界/分层变更意图/文件变更顺序/测试策略/风险点. 当用户需要在 AFK agent 执行前预览源码级执行计划时使用; 通常由 orchestrate 在 to-issues 完成后主动询问, 也可显式点名.
---

# To Plan

为 `docs/changes/<change-id>/` 下的所有 issue 生成合并源码级执行计划, 写入 `docs/changes/<change-id>/PLAN.md`. 人类审核通过后, AFK agent 按计划执行.

## 流程

### 1. 确定 change-id

从对话上下文或用户输入确定 change-id. 若无法确定, 询问用户.

### 2. 读取输入

按顺序读取:

1. `docs/changes/<change-id>/PRD.md` -- 获取全局上下文: 实现决策, 架构约束, 测试决策, 范围外
2. `docs/changes/<change-id>/issues/` 下所有 issue 文件 -- 获取每个 issue 的行为描述, 验收标准, 阻塞关系

### 3. 聚焦代码探索

基于 issue 描述中的领域术语和模块名, 在代码库中做聚焦搜索, 确定每个 issue 的代码修改边界. 以 issue 为维度组织探索结果, 不要求全局代码扫描.

对于修改边界不确定的情况, 标注在对应 issue 的风险字段中, 不穷举.

### 4. 生成 PLAN.md

按下方模板生成 PLAN.md, 写入 `docs/changes/<change-id>/PLAN.md`. 若目录不存在则创建.

输出后向用户展示 PLAN.md 路径和内容摘要 (issue 数量, 涉及文件总数, 风险概览). 不内置审核循环.

## PLAN.md 模板

```markdown
# 执行计划: <change-id>

> 基于 PRD: `docs/changes/<change-id>/PRD.md`
> 生成时间: <timestamp>

## 交叉风险概览

<!-- 列出被多个 issue 共享的文件, 标注重叠/相邻修改区域 -->

| 文件 | 涉及 Issue | 重叠级别 |
|------|-----------|---------|
| `path/to/file` | issue-a, issue-b | 同一函数 / 相邻区域 / 同文件不同区域 |

<!-- 若不存在共享文件冲突, 写 "无交叉风险." -->

## Issue 执行计划

<!-- 按 issue 依赖关系和推荐执行顺序正序排列. 每个 issue 一个 section. -->

### <issue-文件名> -- <issue 标题>

**关联 PRD 用户故事**: <引用 PRD 中相关用户故事编号>

#### 文件清单

<!-- 分四类: 修改 / 新增 / 删除 / 只读参考 -->

**修改** (路径 + 关键符号 + 关键行号):

- `path/to/file` -- `ClassName.methodName()` (L45~L72): <概要变更意图>
- `path/to/file` -- `functionName()` (L100~L130): <概要变更意图>

**新增** (路径 + 职责概要):

- `path/to/new/file` -- <该文件的预期职责>

**删除** (路径):

- `path/to/old/file`

**只读参考** (路径, 实现时需理解但不修改):

- `path/to/reference/file`

#### 分层变更意图

<!-- 按项目实际架构动态命名层名. 只写涉及变更的层. -->

**<层名 1>** (如 Controller / API 层):

- <该层变更描述>

**<层名 2>** (如 Service / 业务逻辑层):

- <该层变更描述>

**<层名 N>**:

- <该层变更描述>

#### 文件变更顺序

<!-- 推荐的文件级变更顺序, 考虑编译/测试依赖 -->

1. <先变更的文件, 如 schema / 接口定义>
2. <依赖第 1 步产物的文件>
3. ...

#### Issue 级测试策略

<!-- 描述该 issue 整体功能的测试方式. 不展开具体用例/方法细节. -->

- **新增测试文件**: `path/to/test_file` -- 验证 <功能场景>
- **修改已有测试**: `path/to/existing_test` -- 补充 <功能场景> 的覆盖
- **测试方式**: 单元测试 / 集成测试 / E2E

#### 风险点

<!-- 高/中/低 三档 + 缓解建议 -->

- **[高/中/低]** <风险描述>. 缓解: <建议措施>
```