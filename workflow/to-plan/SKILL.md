---
name: to-plan
description: Issues 到合并源码级执行计划 PLAN.md 的生成流程.
disable-model-invocation: true
---

# To Plan

为 PRD 下的所有 issues 生成合并源码级执行计划, 并写入 `docs/changes/<feature-slug>/PLAN.md`.

## 流程

### 1. 读取输入

基于对话上下文中已有内容开展工作. 如果用户传入 issues 引用(issues 编号/URL 或路径), 从议题跟踪器获取这些 issues, 并阅读完整正文和评论.

完成标准: 已确定 PRD 引用, issue 列表, issue 依赖关系, 输出 feature 目录. 如果来源不在 `docs/changes/<feature-slug>/`, 仍按功能标题推断 `<feature-slug>` 并写入 `docs/changes/<feature-slug>/PLAN.md`.

### 2. 聚焦代码探索

基于 issue 描述中的领域术语和模块名, 在代码库中做聚焦搜索, 确定每个 issue 的代码修改边界. 以 issue 为维度组织探索结果, 不要求全局代码扫描.

完成标准: 每个 issue 都有变更层级, 文件候选, 关键符号或入口点. 修改边界不确定的情况写入 PLAN.md `风险点`.

### 3. 整合交叉风险

合并所有 issue 的文件候选, 标出共享文件, 相邻修改区, 同一函数/类/接口的重叠修改, 顺序依赖和测试依赖.

完成标准: 已生成交叉风险概览. 无共享文件冲突时明确写 `无交叉风险.`

### 4. 生成 PLAN.md

按下方模板生成 `docs/changes/<feature-slug>/PLAN.md`.

完成标准: PLAN.md 已写入, 内层 fenced code 已正确闭合, `变更目录树` 非空或明确写无变更. 输出后向用户展示 PLAN.md 路径和内容摘要(涉及的代码层, 文件总数, 风险概览).

## PLAN.md 模板

````markdown
# 执行计划

> 基于 PRD: `path/to/PRD.md`

## 交叉风险概览

<!-- 列出被多个 issues 共享的文件, 标注重叠/相邻修改区域 -->

| 文件 | 涉及 issues | 重叠级别 |
|------|-------------|----------|
| `path/to/file` | issue-a, issue-b | 同一函数 / 相邻区域 / 同文件不同区域 |

<!-- 若不存在共享文件冲突, 写 "无交叉风险." -->

## issues 执行计划

<!-- 按 issues 依赖关系和推荐执行顺序正序排列. 每个 issue 一个 section. -->

### <issue 标题>

> 基于 issue: `path/to/issue`

#### 变更列表

<!-- 采用双层列表结构: 外层为需要变更的代码层, 内层为代码层内需要变更的文件列表 -->
<!-- 按项目实际架构动态命名层名, 只写涉及变更的层, 如 Controller / Service / Dao -->
<!-- 文件变更类型分四类: 修改 / 新增 / 删除 / 只读参考 -->

##### <层名>

**修改** (路径 + 关键符号 + 关键行号):

- `path/to/file` -- `ClassName.methodName()` (L45~L72): <概要变更意图>
- `path/to/file` -- `functionName()` (L100~L130): <概要变更意图>

**新增** (路径 + 职责概要):

- `path/to/new/file` -- <该文件的预期职责>

**删除** (路径):

- `path/to/old/file`

**只读参考** (路径, 实现时需理解但不修改):

- `path/to/reference/file`

#### issue 测试用例清单

<!-- 针对 issue 功能边界(深模块)的测试用例清单, 不要深入边界内部的具体代码细节(浅模块) -->

- [ ] <外部可观察行为或验收标准>

#### 风险点

<!-- 高/中/低 三档 + 缓解建议 -->

- **[高/中/低]** <风险描述>. 缓解: <建议措施>

## 变更目录树

<!-- 画一棵目录树展示变更文件列表及其所在目录. 文件前加符号表示变更类型: + 新增, x 删除, e 修改, r 只读参考. 文件后写注释: 哪些 issue 会写它, 为什么要写. -->

```text
project-root/
`-- src/
    |-- main/
    |   `-- java/
    |       `-- example/
    |           |-- e ExistingService.java  # issue-a: 调整业务规则
    |           `-- + NewPolicy.java        # issue-b: 新增策略封装
    `-- test/
        `-- java/
            `-- example/
                `-- + ExistingServiceTest.java  # issue-a, issue-b: 覆盖外部行为
```
````
