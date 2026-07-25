---
name: afk
description: 按已确认 Execution Spec 自动实现, 审查和验证 issues.
disable-model-invocation: true
---

开始前, 调用 `domain-awareness` skill 只读感知当前工作目录的领域模型.

## 触发门禁

同时满足以下条件才进入 AFK:

- 你是父会话, 不是子代理.
- `PRODUCT.md`, `TECHNICAL.md`, `EXECUTION.md` 和关联 issue 均存在且可读.
- issue 已在会话中由我确认, 并写清覆盖依据, 相关决策, 允许/禁止范围, 验证入口, 风险, 停止条件和 AFK 原因.
- `DECISIONS.md` 存在, 或 Spec/issue 明确写无相关决策.
- 当前运行时存在可承担 worker 和 reviewer 的子代理.
- 任务不要求父会话直接写生产或测试代码.
- lazy-code 选择已确定. 我未说明时, 在会话中问"是否使用 lazy-code?", 并说明你的推荐.

任一不满足则停止并在会话中报告缺口. 无可用子代理时不降级为父会话编码, 调用 `tdd` skill.
执行前, 在会话中用简短语言告诉我本轮将执行的 issue, 可观察结果, 主要代码边界, 验证方式和最高风险, 然后问"是否执行?". 不让我阅读 Spec 或 issue 后再决定.
全部满足且我确认执行 -> 继续.

## 职责与边界

你只按步骤文件机械执行.

禁止:

- 写生产或测试代码.
- 替代 reviewer 做审查.
- 将调度职责下放给子代理.
- 伪造证据.
- 把 worker 偏离解释为新决策.
- 读同目录下其他 `step-NN.md`.
- 自主决定跳过或重排步骤.

## 执行循环

`_current.md` 格式为 `ISSUE-KEY:NN`, 如 `ISSUE-01:03`; 终点为 `done`.
首次进入或中断恢复: 读取 `_current.md` -> 若为 `done`, 在会话中报告已完成并退出 -> 否则读取对应 `step-NN.md` -> 执行 -> 按步骤出口更新 `_current.md` -> 继续.
每次只持有 `_current.md` 和当前步骤文件. 不读未来步骤.

### 步骤文件位置

```text
docs/changes/<feature-slug>/afk-running/
  _current.md
  step-01.md ~ step-06.md
  ISSUE-01/
  ISSUE-02/
```

步骤文件由之前的 HITL 流程一次性生成. AFK 不生成或修改步骤定义.

### 路径推断

- feature 根目录: `afk-running/` 的父目录.
- product: feature 根目录下的 `PRODUCT.md`.
- technical: feature 根目录下的 `TECHNICAL.md`.
- execution: feature 根目录下的 `EXECUTION.md`.
- decisions: feature 根目录下的 `DECISIONS.md` (如存在).
- 当前 issue: `issues/` 中以当前 issue key 开头的 `.md`.
- 当前 issue 产物目录: `afk-running/<ISSUE-KEY>/`.

## 必读

为编写子代理 system prompt 和判断停止/输入冲突, 开始前先建立对权威输入的理解:
调用 `decision-ledger` 了解账本规则, 再读取 PRODUCT, TECHNICAL, EXECUTION, 当前 issue 和 DECISIONS (如存在).

## 子代理 system prompt 编写

仓库不维护 prompt 模板. 每次启动新子代理前, 父会话根据本轮任务和执行现场编写专用 system prompt. 不引用角色文件, 不把上一轮 prompt 原样复用于不同任务. resume 同一子代理时沿用其原 system prompt, 并在恢复消息中补充新增事实.
system prompt 只写权威输入中没有且当前任务必需的信息. 文档和代码已有内容不复述, 放入 `必读推荐`, 给出路径和阅读目的. 不确定事实要求子代理读取或验证, 不替它猜测.

逐项覆盖:

- **身份和单一目标**: 初始 worker/修复 worker/正确性 reviewer/Spec 边界 reviewer, 只描述当前一轮结果.
- **现场事实**: 当前 attempt, 工作树和 diff 来源, 已有 note/review, 已采纳或排除发现项, 已知阻塞, 可用工具与 skill. 只写父会话已验证事实.
- **权威输入**: 指向 PRODUCT, TECHNICAL, EXECUTION, issue, DECISIONS (如存在) 和本轮产物. 输入冲突时停止, 不授权子代理改需求或决策.
- **权限和禁止项**: worker 可改代码和测试, 但不做产品/API/架构/范围决策, 不改 Spec/DECISIONS, 不 stage. 初始 worker 不读 review; 修复 worker 只读父会话指定的 review 和发现项. reviewer 只读, 不修改/修复/stage 项目文件. 未授权时不得委派其他子代理.
- **执行方法**: worker 默认暴露 `tdd` skill 并按其执行; 我选择 lazy-code 时额外暴露 `lazy-code`. reviewer 写明唯一审查维度, 检查范围和证据标准.
- **skill 使用**: 每次分派子代理时, 父会话按 `强制`/`推荐` 两级列出本轮子代理应使用的 skill. `强制` = 子代理必须按其执行; `推荐` = 视情况使用. 具体列哪些由父会话根据本轮任务, 现场和角色决定, 不固定.
- **停止条件**: 包含 issue 停止条件. 需要改变任一 Spec/issue/必须遵守决策, 扩大范围, 触碰禁止范围, 无法验证, 缺少测试接缝且风险不可接受, 或文档与代码冲突时停止.
- **输出契约**: 指定唯一输出路径和必含内容. worker note 包含改动入口, RED/GREEN 证据, 验证结果, 风险/阻塞, 决策偏离; 高风险操作前先刷新 note. reviewer 每个发现项包含严重度, 证据, 问题性质, 最小修复方向, 是否需我决策.
- **完成证据**: 指定验证入口, 覆盖的 AC/TG/NFR 和应检查的 diff. 禁止伪造或省略命令结果.

初始实现覆盖当前 issue; 修复只覆盖父会话采纳发现项; 两类 reviewer 分别聚焦正确性和 Spec/决策边界, 不共用 prompt.

## 子代理运行预算

启动 worker/reviewer 时不主动设 timeout. 运行时强制要求时, 使用允许的最大合理值. worker 单个串行; reviewer 多个并行. 中断后优先 resume, 确认无进展/越界/方向错误/不可恢复时才换新或停止.

## 停止和会话汇报

以下情况停止自动推进:

- 触发门禁或步骤预检不满足.
- 需要产品/API/架构/范围决策.
- 步骤要求停止.
- 缺少进入下一步的真实证据.
- diff 混有我已有变更或来源不清.
- reviewer 不可恢复且替代仍失败.

停止时直接在会话中说明: 发生了什么, 对产品/技术/范围的影响, 你的推荐, 只需要我回答的一个问题. 不让我阅读运行产物后再决定.

全部完成时直接在会话中说明: 已交付的可观察结果, 验证结果, 未运行项, 残余风险. 文档路径只作为 AI 后续定位信息.

## 反模式

**伪同步调度子代理**: 以异步+后台运行的方式启动单个子代理, 然后再阻塞等待子代理完成任务. 这完全是多此一举, 引入了额外的开销. 避免办法是直接同步调用+台前调度单个子代理.
**亲自完成本该交给子代理的工作**: 父会话自己完成代码编写或者审核. 违背afk执行流程. 避免办法是严格遵守父会话的行为规范.
