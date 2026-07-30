# Spec 编写和执行 SOP

## 1. 目的

本 SOP 将已确认需求转换为 AI 可消费, 可追踪, 可执行的 Spec Pack, 并贯通实现, review 和验证.

文档只供 AI 使用. 我不通过阅读文档理解或批准方案. 影响产品, API, 架构, 范围, 风险或验证的决定, 必须在 `propose` 会话中向我解释并确认.

适用于中大型特性, 重构和技术改进. 行为已明确的微小修复可以直接进入 `tdd`.

## 2. 核心原则

- Why/How/Execution 分层, 每类事实只有一个权威来源.
- 会话是人类认知和决策界面, 文档是 AI 协作界面.
- 后续 Spec skill 只整理已确认内容, 不隐藏新决策.
- 层间使用稳定 ID 和路径引用, 不复制正文.
- Product 验收项必须追踪到 issue, 测试和完成证据.
- 机器可读 API/schema/迁移文件是对应事实的权威来源, Technical Spec 只做索引和约束说明.
- 执行计划按垂直切片组织, 不按技术层水平拆分.

## 3. Spec Pack

```text
docs/changes/<feature-slug>/
|-- PRODUCT.md
|-- TECHNICAL.md
|-- EXECUTION.md
|-- DECISIONS.md
|-- issues/
|   |-- ISSUE-01-<slug>.md
|   `-- ISSUE-02-<slug>.md
`-- afk-running/
    |-- _current.md
    |-- step-01.md ~ step-06.md
    `-- ISSUE-01/
```

### 3.1 PRODUCT.md

回答为什么做和交付什么产品结果.

必含:

- 背景, 真实受益者和需求来源.
- `G-001` 格式的目标.
- 非目标.
- `US-001` 格式的用户故事.
- `BR-001` 格式的业务规则.
- `AC-001` 格式的可观察验收标准.
- 成功指标, 或不设指标的已确认理由.
- 产品决策引用和非阻塞待验证事实.

禁止技术选型, API/schema, 模块和逐文件计划.

### 3.2 TECHNICAL.md

回答如何实现产品结果, 并索引技术权威来源.

必含:

- Product 目标和验收 ID 引用.
- `TG-001` 格式的技术目标.
- 架构与组件责任.
- API/schema/状态机等权威资产路径; 无机器资产时提供精确定义.
- 关键正常/失败流程.
- 边界和异常处理.
- 安全策略.
- `NFR-001` 格式的性能/可观测性/可用性要求.
- 测试策略.
- 技术决策/ADR 引用.
- 依赖, 风险, 代码边界提示和非阻塞待验证事实.

阻塞性产品/API/架构问题不得留在已完成的 Technical Spec 中.

### 3.3 EXECUTION.md

回答 AI 在什么边界内, 按什么任务图执行和验证.

必含:

- PRODUCT/TECHNICAL/DECISIONS 权威输入.
- 全局允许范围和禁止范围.
- build/lint/test/benchmark/人工验证组成的完成定义.
- AC/TG/NFR 测试策略.
- issue 任务图和依赖.
- `AC/TG/NFR -> issue -> 验证入口` 覆盖矩阵.
- 风险和停止条件.

EXECUTION 不复制 issue 正文, 不记录运行状态.

### 3.4 issues

每个 issue 是可独立验证的 tracer bullet, 是 `tdd-as-orchestra` 的直接入口.

必含:

- `- [ ] 已实现` 或 `- [x] 已实现`.
- 可观察结果.
- 覆盖的 AC/TG/NFR.
- 决策引用.
- 允许/禁止范围.
- 验证入口和通过标准.
- 风险和停止条件.
- AFK/HITL 依据.
- issue 验收标准和依赖.

### 3.5 DECISIONS.md 和 afk-running

`DECISIONS.md` 保存功能级决策历史, 约束性和代码实际影响. 它不是 Technical Spec 的替代品.

`afk-running` 保存状态机, worker/reviewer note 和完成证据. 它不是 Spec, 不承载产品或技术决策.

## 4. Skill 主链

```text
propose
  -> to-product-spec
  -> to-technical-spec
  -> to-execution-spec
  -> tdd-as-orchestra
```

### 4.1 propose

这是唯一设计决策入口.

先关闭产品分支, 再关闭技术分支. 一次只问一个问题. 在产品/技术/高影响专项发散点读取外部参考 `EXPLORE-DESIGN-OPTIONS.md` 生成多方案, 委派子代理验证并比较. 每项关键选择在会话中说明含义, 影响和推荐, 得到确认后才写入.

盘问期间不写领域文档/ADR/`DECISIONS.md`/Spec. 全部分支关闭后合并询问"是否固化当前方向并结束盘问?", 确认后才统一落盘. 固化结束后另问是否依次生成 Spec 链.

### 4.2 to-product-spec

把已确认产品结果写入 `PRODUCT.md`. 不做访谈或新增决定. 缺口或冲突退回 `propose`.

完成后只在会话中报告路径, 待验证事实和阻塞, 不展示全文.

### 4.3 to-technical-spec

探索代码事实, 将已确认设计写入 `TECHNICAL.md`. 不新增产品/API/架构/范围决策. 缺口或冲突退回 `propose`.

完成后只在会话中报告路径, 待验证事实和阻塞, 不要求文档审批.

### 4.4 to-execution-spec

按 tracer bullets 生成 `EXECUTION.md` 和 issues.

切片决策必须在会话中确认. 先说明推荐切片数, 再逐个说明可观察结果, 覆盖 ID, 依赖, 风险和 AFK/HITL 依据. 一次只问一个边界或依赖问题, 不展示 issue 全文.

确认后落盘并生成 AFK 步骤文件.

### 4.5 tdd-as-orchestra

执行前在会话中说明当前 issue 的结果, 代码边界, 验证方式和最高风险, 再问"是否执行?".

worker 按 TDD 实现, 两个 reviewer 分别检查正确性和 Spec/决策边界. 修复后重新 review. 验证通过且证据完整后才能勾选 issue.

需要改变任一 Spec, decision 或 issue 边界时停止. 会话中说明问题, 影响, 推荐和一个待回答问题, 不让我阅读运行产物后决定.

## 5. 追踪和完成

稳定 ID:

- Product goal: `G-001`.
- User story: `US-001`.
- Business rule: `BR-001`.
- Acceptance criterion: `AC-001`.
- Technical goal: `TG-001`.
- Non-functional requirement: `NFR-001`.
- Decision: `D001`.
- Issue: `ISSUE-01`.

完成一个 issue 必须具备:

- 验收标准全部满足.
- AC/TG/NFR 对应的测试或检查证据.
- 正确性和 Spec 边界 review 已处理.
- 真实验证命令及结果.
- 决策实际影响已回写.
- 未运行项和残余风险已记录并在会话中报告.

完成整个 feature 前, EXECUTION 覆盖矩阵中的每个 ID 必须指向已完成 issue 和 final report.

## 6. 维护

- 执行中发现 Spec 与代码事实冲突时停止, 不自行选择.
- 产品/API/架构/范围语义变化退回 `propose`, 新建或替代决策 ID, 再更新对应 Spec.
- 局部实现细节可在不改变 Spec/decision 的前提下调整, 并记录真实影响.
- 当前 feature 交付后保留 Spec Pack 和证据作为变更历史. 后续语义变化建立新的 feature 变更, 不静默改写历史.
