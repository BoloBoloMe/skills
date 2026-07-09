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

## 子代理接口

调度所需的最小接口:

**worker**: 可写代码和测试. 不决定产品/API/架构, 不改 DECISIONS, 不 stage. 输入: contract/issue/decisions + task. 输出: note 文件 + diff. 除非我明确要求, 否则默认对其暴露 `tdd` skill, task 追加一句 "按 `tdd` skill 的要求执行". 我要求使用 lazy-code 时, 额外暴露 `lazy-code` skill, task 再追加一句 "按 `lazy-code` skill 的要求写代码". 推荐以前台方式启用, 必须单 worker 串行. 

**reviewer**: 只读. 不改任何项目文件, 不 stage. 输入: contract/issue/decisions/worker note/diff. 输出: review 文件. 推荐以前台方式启用, 多个 reviewer 要并行.

在给子代理的提示词中补充有助于其完成任务的信息, 但只写其他文档没有的信息,
其他文档已有的信息在提示词中增加 `必读推荐` 章节, 指引子代理找到提示词中未包含的 **必读信息** (文件路径/代码位置/URL)

## 子代理运行预算

启动 worker 或 reviewer 时不主动设 timeout. 不得为流程整齐设短 timeout. 如果运行时要求 timeout 必须传, 使用该运行时允许的最大合理值.
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
- worker/reviewer 角色文件: `run-afk-workflow/prompts/` 中的 WORKER.md / REVIEWER.md

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
