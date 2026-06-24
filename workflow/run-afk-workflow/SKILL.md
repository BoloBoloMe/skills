---
name: run-afk-workflow
description: 已确认 PRD, issue, PLAN 的 AFK 编码任务父会话控制器.
disable-model-invocation: true
---

# AFK workflow controller

## 触发门禁

只有同时满足以下条件才进入 AFK:

- 当前会话是父会话, 不是子代理.
- 用户明确要求执行 AFK 编码任务.
- 关联 PRD, issue, PLAN 已存在且已由用户确认.
- 任务不要求父会话直接写生产代码或测试代码.
- 当前运行时存在可承担 implementation, review, recovery 的 agent/role/profile 绑定.
- 前 5 条全满足后, 父代理向用户询问"要不要懒代码"; 用户回答 (要/不要) 则本条满足. 决议由父代理在会话内持有, 不落库, 不写 run manifest 或预检产物.

完成标准: 全部满足则进入 `PREFLIGHT`; 任一不满足则停止, 报告缺口和需要用户补齐的输入. 懒代码必问无答视为第 6 条不满足, 按门禁失败停止. 如果运行时没有可用子代理或等价角色, 不降级为父会话编码, 改为请用户切换到 `tdd` skill 或 `diagnosing-bugs` skill 流程.

## 父会话硬边界

父会话是调度器与唯一决策者, 负责流程推进, 差异检查, review 门禁, 综合判定, 最终验证, 最终报告.

禁止:

- 写生产代码或测试代码.
- 替代 reviewer 审查代码质量.
- 将调度职责下放给任何子代理.
- 伪造 RED/GREEN 证据.

允许:

- 查看 `git status`, `git diff`, `git diff --name-only` 等机械性状态.
- 保存孤立 diff 到产物目录.
- 运行预检中确认的验证命令.
- 写流程性产物.
- 基于真实 diff, 已有日志, 命令输出做流程决策.

推进规则: 进入下一状态的决定必须基于真实 diff, 产物文件, 命令输出, 或用户确认. 无证据时停止, 转 recovery, 或询问用户.

## 角色边界

- **worker**: TDD 执行器. 读取前置产物和 issue 产物目录文件, 按 TDD 纵向切片写代码, 写运行日志和结果报告. 不判断需求合理性, 不决定范围, 不读取 reviewer 输出. 若懒代码决议为要, 父代理在启动任一 worker (implementation/fix/recover) 的初始提示词注入指引, 让 worker 自读 `lazy-code` skill 并遵循其标准; lazy-code 不替代 TDD, 需测试先行时仍按 `tdd` skill 完整流程. reviewer 不注入.
- **reviewer**: 单维度只读审查员. 读取前置产物, issue 产物目录文件和代码库真实 diff, 按指定维度输出发现项. 不修改任何项目/源码文件, 不读取其他 reviewer 输出, 不做跨维度判断.
- **recovery worker**: 恢复执行器. 只按 `RECOVERY.md` 指定模式补产物, 修复验证失败, 或继续 dirty tree. 不扩大范围.

三者互不通信, 互不知道对方的存在. 子代理通过文件接收上下文, 不继承父会话历史.

## 渐进式阅读

开始 AFK 前必须读取:

- `CONTRACTS.md` -- 产物目录, 产物命名, 写入者, 下游消费者, validation, agent binding, review policy 契约.
- `RUNBOOK.md` -- 正常主流程.

按需读取:

- `LIGHTWEIGHT-TEST-ONLY.md` -- 当 issue 可能是测试 only 轻量路径时读取.
- `RECOVERY.md` -- 当 worker/reviewer 超时, 中断, 产物缺失, dirty tree, 验证失败或恢复时读取.

启动子代理前读取对应 prompt: implementation `prompts/WORKER-IMPLEMENT.md`; fix `prompts/WORKER-FIX.md`; recovery `prompts/WORKER-RECOVER.md`; consistency review `prompts/REVIEWER-CONSISTENCY.md`; correctness review `prompts/REVIEWER-CORRECTNESS.md`; simplicity review `prompts/REVIEWER-SIMPLICITY.md`.

## 冲突优先级

文档冲突时按以下顺序裁决:

1. 本文件父会话硬边界.
2. `CONTRACTS.md`.
3. `RECOVERY.md` 或 `LIGHTWEIGHT-TEST-ONLY.md`.
4. `RUNBOOK.md`.
5. `prompts/*`.

## 状态机

所有产物路径, 命名, 写入者, 下游消费者以 `CONTRACTS.md` 为唯一真相源. 本状态机只描述父会话控制流和完成标准.

| 状态 | 动作 | 完成标准 |
|---|---|---|
| `PREFLIGHT` | 阅读 PRD/issue/PLAN; 确认工作树; 按 `CONTRACTS.md` 写预检产物; 确认 TDD 可行性, 聚焦测试命令模板, 依赖预热和模板 smoke. | 预检产物存在且字段完整; 工作树干净且无 staged 文件; 模板 smoke 通过或阻塞项已记录; implementation/review/recovery 角色已解析. 任一失败则停止, 不启动 worker. |
| `ISSUE_INIT` | 确定下一个 issue 的 `issueKey`; 创建或确认 issue 产物目录; 按 `CONTRACTS.md` 更新 run manifest; 设置初始 review round. | issue 产物目录存在; run manifest 记录 issue 顺序, issue 路径, `issueKey`, issue 产物目录; 本 issue 后续子代理均使用该目录. |
| `IMPLEMENT` | 读取 implementation prompt; 使用 implementation role 启动 worker; 传入 PRD, PLAN, issue, issue 产物目录, 允许文件清单, issue 执行类型, validation 契约和增量测试命令模板. | worker 已结束或产生可恢复状态; 必需实现阶段产物存在, 或缺失项已记录为恢复输入; 父会话未写代码. worker 异常, 超时, 中断, dirty tree, 或产物缺失则转 `RECOVERY.md`. |
| `DIFF_GATE` | 父会话检查真实 diff, allowed files, staged 状态, 产物存在性, 验证命令, RED/GREEN 或 GREEN-only 证据. | 每项检查均有结论. normal issue 缺少可信 RED/GREEN 证据则不进 review. test-only-light 不满足轻量门禁则不静默继续. dirty tree 异常先保存证据, 再转 `RECOVERY.md`. |
| `REVIEW_GATE` | 判断轻量跳过条件; 不满足时检查完整 review 门禁; 门禁通过后启动 3 个只读 reviewer, 环境不支持并行时串行. | 轻量跳过成立则按 `LIGHTWEIGHT-TEST-ONLY.md` 写跳过产物并进 `FINAL_VERIFY`; 完整 review 成立则 review 产物齐全; reviewer 失败按 `RECOVERY.md` 处理; 门禁失败不启动 reviewer. |
| `SYNTHESIZE` | 读取本轮 review 产物; 将发现项分类为可立即修复, 延期, 需人工决策, 证据不足驳回; 按 `CONTRACTS.md` 写综合判定产物. | 每个发现项都有分类和去向; 证据不足项有驳回原因; 有人工决策项则停止询问用户; 无可立即修复项则进 `FINAL_VERIFY`; 可立即修复且不越界则进 `FIX_LOOP`. |
| `FIX_LOOP` | 读取 fix prompt; 对可立即修复项启动 fix worker; 修复后回到 `DIFF_GATE`; 按发现项来源维度选择重跑 reviewer; 重复综合判定. | 每轮修复有真实 diff 和修复产物; 最多 3 轮; 可立即修复项清零则进 `FINAL_VERIFY`; 数量不降, 修复越界, 或引入未审维度新问题则停止询问用户; 达轮次上限则剩余项转延期. |
| `FINAL_VERIFY` | 父会话运行聚焦验证; 必要时运行 full build; 复核 TDD 或 GREEN-only 日志与真实 diff 一致; 输出最终报告. | 聚焦验证已记录; full build 已运行或跳过理由已记录; 最终报告覆盖最终 diff, 证据, 验证结果, review 解决情况, 遗留阻塞项, 残余风险. 验证失败则转 recovery 或询问用户. |
| `NEXT_OR_STOP` | 判断是否继续下一个 issue; 继续则回到 `ISSUE_INIT`; 不继续则询问用户下一步行动. | 只有当前 issue 完成 `FINAL_VERIFY` 后才允许进入; 下一步明确为继续指定 issue, 停止等待用户, 或报告阻塞. |

## 停止条件

出现以下任一情况, 父会话必须停止自动推进:

- 触发门禁或预检门禁不满足.
- 需要产品, API, 架构或范围决策.
- 修复会越过允许文件清单.
- RED/GREEN 证据缺失且无法通过 recovery 补齐.
- reviewer 维度无法完成且替代 reviewer 仍失败.
- 验证失败且恢复动作需要代码级判断超出 recovery 契约.
- 任一状态缺少进入下一状态所需的真实证据.
