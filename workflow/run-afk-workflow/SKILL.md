---
name: run-afk-workflow
description: 已确认 contract, issue, DECISIONS 的 AFK 编码任务父会话控制器.
disable-model-invocation: true
---

# AFK workflow controller

## 触发门禁

同时满足以下条件才进入 AFK:

- 你是父会话, 不是子代理.
- 关联 issue 已存在且已由我确认.
- 任务满足以下二选一: 存在可读取的 `CONTRACT.md`; 或 issue 自包含目标, 允许范围, 禁止范围, 验证入口, 风险提示, 停止条件和相关决策.
- issue 已写清 `相关决策`, `允许范围`, `禁止范围`, `验证入口`, `风险提示`, `停止条件`, `适合 AFK 的原因`.
- `DECISIONS.md` 存在, 或 issue/contract 明确写无相关决策.
- 当前运行时存在可承担 worker 和 reviewer 的子代理.
- 任务不要求父会话直接写生产或测试代码.
- lazy-code 选择已确定. 用户未说明时主动询问 "是否使用 lazy-code?".

任一不满足则停止, 报告缺口. 无可用子代理时不降级为父会话编码, 请我切换到 `tdd` skill.

全部满足 → 继续.

## 硬边界

你只按步骤文件机械执行.

禁止:

- 写生产或测试代码.
- 替代 reviewer 做审查.
- 将调度职责下放给子代理.
- 伪造证据.
- 把 worker 偏离解释为新决策.
- 读同目录下其他 `step-NN.md`.
- 自主决定跳过或重排步骤.

## 子代理 system prompt 编写

仓库不维护 worker/reviewer prompt 模板. 每次启动新的子代理前, 父会话根据本轮任务和执行现场编写专用 system prompt. 不引用角色文件, 不把上一轮 prompt 原样复用于不同任务. resume 同一子代理时沿用其原 system prompt, 并在恢复消息中补充新增事实.

system prompt 只写完成当前任务所需且权威输入中没有的信息. 文档和代码已有的内容不复述, 放入 `必读推荐` 章节, 给出文件路径/代码位置/URL 及阅读目的. 不确定的事实明确要求子代理读取或验证, 不替它猜测.

编写时逐项覆盖:

- **身份和单一目标**: 明确本轮是初始实现 worker/修复 worker/正确性 reviewer/决策边界 reviewer, 只描述当前一轮要完成的结果.
- **现场事实**: 写明当前 attempt, 工作树和 diff 的来源, 已有 note/review, 已采纳或排除的发现项, 已知阻塞, 可用工具与 skill. 只写父会话已验证的事实.
- **权威输入**: 指向 contract, issue, DECISIONS (如存在) 及本轮所需产物. 标明相关当前决策的约束性: `必须遵守` 不可改变; `可调整` 只允许在不改变产品/API/边界时采用更好方案, 并在 note 说明偏离. 输入冲突时停止, 不授权子代理自行改需求或决策.
- **权限和禁止项**: worker 可改代码和测试, 但不做产品/API/架构决策, 不改 DECISIONS, 不 stage. 初始 worker 不读 review; 修复 worker 只读父会话指定的 review 和发现项. reviewer 只读, 不修改/修复/stage 项目文件. 未明确授权时不得委派其他子代理.
- **执行方法**: worker 默认暴露 `tdd` skill 并要求按其执行; 用户选择 lazy-code 时额外暴露 `lazy-code` skill 并要求按其执行. reviewer 写明唯一审查维度, 检查范围和证据标准.
- **停止条件**: 包含 issue 的停止条件, 并要求在需要改变 contract/issue/必须遵守的决策, 扩大范围, 触碰禁止范围, 无法验证, 缺少测试接缝且风险不可接受, 或文档与代码冲突时停止, 不自行取舍.
- **输出契约**: 指定唯一输出路径和必含内容. worker note 是 handoff note, 包含改动入口, 验证入口及结果, 风险/阻塞, 决策偏离; 高风险操作前先刷新 note. reviewer 的每个发现项包含严重度 (`blocker`/`required`/`recommended`/`deferred`), 证据, 问题性质, 最小修复方向, 是否需用户决策; 无发现项时写检查范围和结论.
- **完成证据**: 指定应运行的验证入口和应检查的 diff, 禁止伪造命令结果或缺失事实.

system prompt 必须针对本轮任务收窄: 初始实现覆盖当前 issue 目标; 修复只覆盖父会话采纳的发现项; 两类 reviewer 分别聚焦正确性和决策边界, 不共用同一份 prompt.

## 子代理运行预算

启动 worker 或 reviewer 时不主动设 timeout. 不得为流程整齐设短 timeout. 如果运行时要求 timeout 必须传, 使用该运行时允许的最大合理值.
worker 推荐以前台方式启用, 必须单 worker 串行. reviewer 推荐以前台方式启用, 多个 reviewer 必须并行.
中断处理: worker/reviewer 中断后优先 resume 同一子代理. 确认无进展/越界/方向错误/不可恢复时才换新或停止.

## 执行循环

`_current.md` 格式: `ISSUE-KEY:NN` (如 `ISSUE-01:03`). 冒号前定位当前 issue, 冒号后定位当前步骤文件. 终点 `done`.

首次进入: 读 `_current.md` → 解析 `ISSUE-KEY:NN` → 若为 `done` 则报告已完成并退出; 否则读 `step-NN.md` → 执行 → 更新 `_current.md` → 连续执行 (不重复读).
中断恢复: 读 `_current.md` → 获得断点 (`ISSUE-KEY:NN`) → 读 `step-NN.md` → 继续.
每次执行: 读当前步骤文件 → 按指引机械执行 → 按末尾分支条件选出口 → 写入 `_current.md` (出口值如 `:02`, `:03`, `<next-key>:01`, `done`) → 进入下一步.
你每次只持有 `_current.md` + 当前步骤文件. 不知道后续步骤数量, 名称, 内容.

### 步骤文件位置

`_current.md` 和 6 个步骤文件 (`step-01.md` ~ `step-06.md`) 在 `afk-running/` 根, 全 feature 共用:
```text
docs/changes/<feature-slug>/afk-running/
  _current.md               ← "ISSUE-01:03"
  step-01.md ~ step-06.md   ← 6 个全局共享
  ISSUE-01/                  ← per-issue 产物
  ISSUE-02/
```

步骤文件由 to-issues 父会话在确认切分方案后一次性生成. 你执行阶段不参与生成.

### 路径推断

步骤文件用目录角色名指代路径. 你按 `_current.md` 中的 issue key 和以下约定推断实际路径:

- feature 根目录: `afk-running/` 的父目录
- contract: feature 根目录下的 `CONTRACT.md`
- decisions: feature 根目录下的 `DECISIONS.md`
- 当前 issue 定义文件: feature 根目录下 `issues/` 中以当前 issue key 开头的 .md 文件
- 当前 issue 产物目录: `afk-running/<ISSUE-KEY>/`

## 必读文档

开始 AFK 前读取:

- 调用 `decision-ledger` skill, 了解决策账本维护规则.
- contract, issue, DECISIONS (如存在).

## 停止条件

以下情况停止自动推进:

- 触发门禁或步骤内预检不满足.
- 需要产品/API/架构/范围决策.
- 步骤文件末尾指引要求停止.
- 任一步缺少进入下一步所需的真实证据.
- diff 混有我已有变更或来源不清, 无法安全回滚.
- reviewer 不可恢复且替代仍失败.
