---
name: run-afk-workflow
description: 已确认 PRD, issue, DECISIONS 的 AFK 编码任务父会话控制器.
disable-model-invocation: true
---

# AFK workflow controller

## 触发门禁

只有同时满足以下条件才进入 AFK:

- 当前会话是父会话, 不是子代理.
- 我明确要求执行 AFK 编码任务.
- 关联 PRD 和 issue 已存在且已由我确认.
- issue 已写清 `相关决策`, `允许范围`, `禁止范围`, `验证入口`, `风险提示`, `适合 AFK 的原因`.
- `DECISIONS.md` 存在, 或 issue 明确写无相关决策.
- 当前运行时存在可承担 worker 和 reviewer 的 agent/role/profile 绑定.
- 任务不要求父会话直接写生产代码或测试代码.

完成标准: 全部满足则进入 AFK. 任一不满足则停止, 报告缺口和需要我补齐的输入. 如果运行时没有可用子代理或等价角色, 不降级为父会话编码, 改为请我切换到 `tdd` skill 流程.

## 父会话硬边界

父会话是调度器与唯一决策者, 负责流程推进, 机械门禁, reviewer 调度, 综合判定, 最终验证, 最终报告.

禁止:

- 写生产代码或测试代码.
- 替代 reviewer 做正确性或决策边界审查.
- 将调度职责下放给任何子代理.
- 伪造 RED/GREEN 证据或命令结果.
- 把 worker 偏离决策解释为新决策.

允许:

- 查看 `git status`, `git diff`, `git diff --name-only`, staged 状态等机械性状态.
- 基于真实 diff 检查是否越过 issue 允许/禁止范围.
- 保存 worker-owned diff 和失败摘要到 `afk-running/`.
- 运行 issue 验证入口或 worker/reviewer 报告中的验证命令.
- 写流程性产物, reviewer 综合结论, failure note, final report.
- 在 diff 门禁和 review 通过后, 将当前 issue 文件中的 `- [ ] 已实现` 回写为 `- [x] 已实现`.
- 按 `decision-ledger` skill 规则, 基于真实 diff 更新 `DECISIONS.md` 的实际影响.

推进规则: 进入下一步必须基于真实 diff, 工作树状态, 命令输出, reviewer 报告或我的确认. 无证据时停止或询问我.

## 角色边界

- **worker**: 编码执行器. 读取 PRD, issue, `DECISIONS.md`, 失败模式和 AFK brief, 自行阅读代码并找到实现路径. worker 可写生产代码和测试代码, 但只能在 issue 允许范围内行动. worker 不决定产品/API/架构决策, 不修改决策账本, 不读取 reviewer 输出, 不 stage 文件. 如果我显式要求或 issue/决策要求懒代码, 父会话把 `lazy-code` 约束注入 worker.
- **reviewer**: 只读审查员. 读取 PRD, issue, `DECISIONS.md`, 真实 diff 和 worker note, 输出审核报告. reviewer 不修改项目/源码文件, 不 stage 文件, 不修复代码, 不改决策账本.

worker 路线错误时, 父会话保存失败摘要和 worker-owned diff, 只回滚 worker-owned changes, 换新 worker 并注入失败模式.

父会话, worker, reviewer 职责隔离. 子代理互不通信, 通过文件路径和本轮摘要接收上下文, 不继承父会话历史.

## 子代理运行预算

父会话启动 worker 或 reviewer 时, 默认不主动设置 timeout. 不得为了流程整齐设置短 timeout.

如果运行时必须传入 timeout 参数, 使用该运行时允许的最大合理值. 如果运行时最大值仍明显不足以完成当前 issue, 启动前先拆小任务或问我, 不静默用短 timeout 开跑.

runtime 超时或中断不是 worker/reviewer 失败证据, 只说明运行预算耗尽或会话被打断.

中断处理:

- worker 中断后, 优先 resume 同一 worker. 同一 worker 持有实现上下文和未完成推理, 不要直接换新 worker.
- reviewer 中断后, 优先 resume 同一 reviewer.
- reviewer 无法恢复时可以换 reviewer, 但换前先确认它没有改文件, 没有 staged 变更.
- 只有确认无进展, 越界, 方向错误, 或不可恢复时, 才考虑新 worker 或停止问我.

## 必读文档

开始 AFK 前必须读取:

- 调用 `decision-ledger` skill, 读取决策账本维护规则.
- `~/.pi/run-afk-workflow/failure-modes.md` -- 长期失败模式. 如果不存在, 记录为无长期失败模式并继续.
- PRD, issue, `DECISIONS.md` (如存在).
- worker 和 reviewer prompt.

## 产物目录和命名

保留 `afk-running/` 收纳文档:

```text
docs/changes/<feature-slug>/afk-running/<issueKey>/
```

固定文件名防覆盖, 内容格式自由:

- `worker-note-aN.md`
- `review-correctness-aN.md`
- `review-decision-boundary-aN.md`
- `fix-note-aN.md`
- `failure-note-aN.md`
- `final-report.md`

`aN` 表示 attempt, 从 `a1` 起. 文件存在不证明完成, 只用于追溯. worker 完成看真实 diff, 工作树状态和命令输出.

## AFK brief

父会话启动 worker 前准备轻量 AFK brief, 可写入 issue 产物目录或直接放入 task. AFK brief 只包含:

- PRD 路径.
- issue 路径.
- `DECISIONS.md` 路径或无相关决策说明.
- 本 issue 目标.
- 相关决策 ID.
- 允许范围和禁止范围.
- 验证入口.
- 风险提示.
- 相关长期失败模式.
- 当前 attempt 和输出 note 路径.

AFK brief 不定义实现方案, 不要求 worker 按文件逐项照做.

## 主流程

### 1. 预检

父会话确认:

- 工作树干净, 无 staged 文件. 不干净时不启动 worker, 除非我明确说明这些变更属于当前 AFK 且可作为基线.
- PRD, issue, `DECISIONS.md` (如有) 可读取.
- issue 的相关决策 ID 存在. 单向引用缺失时, 可按 `decision-ledger` 规则机械补齐.
- issue 的允许范围, 禁止范围, 验证入口足够明确.
- 高风险变更, 产品/API/架构缺口已经由我确认. 否则停止询问我.
- worker/reviewer 角色已解析.

### 2. 启动 worker

读取 `prompts/WORKER-IMPLEMENT.md`, 传入 AFK brief. worker 自行读代码找实现路径, 并写 `worker-note-aN.md`.

如果 worker 被 runtime 中断:

- 不把中断视为 worker 失败.
- 优先 resume 同一 worker.
- 只有确认同一 worker 无进展, 越界, 方向错误, 或不可恢复时, 才保存可观察事实和 diff 到 `failure-note-aN.md`, 再换新 worker 或停止问我.

如果 worker 明确违反边界, 伪造证据, 大幅偏离 issue, 或同类错误重复出现:

- 保存 `failure-note-aN.md`.
- 只回滚 worker-owned changes. 如果 diff 混有我已有变更或来源不清, 停止问我.
- 换新 worker, 并把失败模式注入新 task.

### 3. diff 门禁

worker 结束后, 父会话自行检查真实 diff, 不只依赖 worker note:

- diff 是否为空.
- diff 是否越过允许范围或触碰禁止范围.
- 是否有 staged 文件.
- 是否存在未知来源变更.
- worker note 是否存在.
- worker 是否运行了验证入口或说明无法运行.
- 生产代码变更是否有对应测试或可复核验证证据.

通不过则不启动 reviewer. 根据情况恢复同 worker, 换新 worker, 或停止问我.

### 4. review

默认启动两个独立 reviewer, 小任务可由父会话合并为一个 reviewer并说明理由:

- 正确性 reviewer: 使用 `prompts/REVIEWER-CORRECTNESS.md`, 输出 `review-correctness-aN.md`.
- 决策边界 reviewer: 使用 `prompts/REVIEWER-DECISION-BOUNDARY.md`, 输出 `review-decision-boundary-aN.md`.

reviewer 被 runtime 中断时, 优先 resume 同一 reviewer. 如果无法恢复, 可换 reviewer; 换前先确认原 reviewer 没有改文件, 没有 staged 变更. 替代 reviewer 仍失败则停止问我.

### 5. 综合判定

父会话读取 reviewer 报告, 只做分流:

- 可直接修: 证据清楚, 不需要产品/设计/API 决策, 修复仍在允许范围内 -> 启动 worker 修复.
- 需我决策: 需要改变 PRD/issue/DECISIONS, 扩大允许范围, 或做产品/API/架构取舍 -> 停止问我.
- 不采纳: reviewer 缺证据, 误读 diff, 或建议超出本 issue/已确认决策 -> 父会话可驳回并写明依据.

### 6. 修复循环

读取 `prompts/WORKER-FIX.md`, 将可直接修的问题交给 worker. 修复后回到 diff 门禁.

不设置固定轮次, 按收敛性判断:

- 问题减少且不越界 -> 可继续.
- 同类问题第二次出现 -> 停止自动推进, 保存失败模式, 换新 worker 或问我.
- 问题数量/严重度没有下降 -> 停止.
- 修复引入另一 reviewer 维度问题 -> 停止问我或重跑相关 reviewer.
- 修复需要改变 PRD/issue/DECISIONS 或扩大范围 -> 停止问我.

### 7. 最终验证和追踪

父会话运行 issue 验证入口或 worker/reviewer 报告中可复核的验证命令. 必要时运行 full build, 或记录跳过理由.

通过后:

- 回写 issue 执行标记为 `- [x] 已实现`, 找不到标记则停止报告阻塞.
- 按 `decision-ledger` 规则, 基于真实 diff 更新相关决策的实际影响.
- 写 `final-report.md`, 覆盖最终 diff, 验证结果, reviewer 处理情况, 决策实际影响更新, 遗留阻塞项, 残余风险.

## 停止条件

出现以下任一情况, 父会话必须停止自动推进:

- 触发门禁或预检门禁不满足.
- 需要产品, API, 架构或范围决策.
- worker/reviewer 发现需要改变 `DECISIONS.md` 决策内容, 状态或约束性.
- 修复会越过允许范围或触碰禁止范围.
- diff 混有我已有变更或来源不清, 无法安全回滚 worker-owned changes.
- 验证失败且下一步需要代码级判断而不是继续交给 worker.
- reviewer 无法恢复, 且替代 reviewer 仍失败.
- 任一步缺少进入下一步所需的真实证据.

## 长期失败模式

长期失败模式固定写到:

```text
~/.pi/run-afk-workflow/failure-modes.md
```

AFK run 启动前读取并注入相关失败模式. AFK run 结束后, 父会话可建议新增长期失败模式, 但写入前必须由我确认.
