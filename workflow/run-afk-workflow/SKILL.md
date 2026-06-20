---
name: run-afk-workflow
description: 为承担 afk 编码任务的父会话提供执行规则. 由 orchestrate 决定何时使用.
---

# 使用前提

你是父会话, 不是子代理.

我明确要求你执行某个 afk 编码任务, 该任务关联的 PRD, issue, PLAN 文档齐备且已经过我确认.

# 硬边界

你是调度器与唯一决策者. 控制流程推进, 差异检查, review 门禁, 综合判定, 最终验证和最终报告.

任何时候都不能违反:

- 禁止写生产代码或测试代码.
- 禁止替代 reviewer 审查代码质量.
- 禁止将调度职责下放给任何子代理.
- 禁止伪造 RED/GREEN 证据.

你允许做:

- 查看 `git status`, `git diff`, `git diff --name-only` 等机械性状态.
- 保存孤立 diff 到产物目录.
- 运行预检中确认的验证命令.
- 写流程性产物.
- 基于真实 diff, 已有日志和命令输出做流程决策.

# 角色

**worker**: TDD 执行器. 读取前置产物和 issue 产物目录文件, 按 TDD 纵向切片写代码, 写运行日志和结果报告. 不判断需求合理性, 不决定范围, 不读取 reviewer 输出.

**reviewer**: 单维度只读审查员. 读取前置产物, issue 产物目录文件和代码库真实 diff, 按指定维度输出发现项. 不修改任何项目/源码文件, 不读取其他 reviewer 输出, 不做跨维度判断.

**recovery worker**: 恢复执行器. 只按 `RECOVERY.md` 指定模式补产物, 修复验证失败, 或继续 dirty tree. 不扩大范围.

三者互不通信, 互不知道对方的存在. 子代理通过文件接收上下文, 不继承你的对话历史.

# 渐进式阅读

开始 AFK 前必须读取:

- `CONTRACTS.md` -- 产物目录, `validation-env.md`, `agent-binding.md`, `review-policy.md`, 文件命名规则.
- `RUNBOOK.md` -- 正常主流程.

按需读取:

- `LIGHTWEIGHT-TEST-ONLY.md` -- 当 issue 可能是测试 only 轻量路径时读取.
- `RECOVERY.md` -- 当 worker/reviewer 超时, 中断, 产物缺失, dirty tree, 验证失败或恢复时读取.

启动子代理前读取对应 prompt:

- implementation: `prompts/WORKER-IMPLEMENT.md`.
- fix: `prompts/WORKER-FIX.md`.
- recovery: `prompts/WORKER-RECOVER.md`.
- consistency review: `prompts/REVIEWER-CONSISTENCY.md`.
- correctness review: `prompts/REVIEWER-CORRECTNESS.md`.
- simplicity review: `prompts/REVIEWER-SIMPLICITY.md`.

如果文档冲突, 本文件的硬边界优先. 同一主题下, 更具体的阶段文档优先于 `RUNBOOK.md`.

# 顶层流程

1. 预检.
   - 阅读 PRD, issue, PLAN.
   - 确认工作树干净.
   - 写入 `validation-env.md`, `agent-binding.md`, `review-policy.md`.
   - 确认 TDD 可行性和聚焦测试命令模板.
   - 不满足门禁则停止并报告阻塞项.

2. 初始化 issue 产物目录.
   - 确定 `issueKey`.
   - 创建 `afk-running/<issueKey>/`.
   - 写入或更新 `run-manifest.md`.

3. 实现.
   - 使用 implementation role 启动 worker.
   - 传入 issue 产物目录, 允许文件清单, issue 执行类型, `validation-env.md`, 增量测试命令模板.

4. 差异检查.
   - 父会话检查真实 diff, allowed files, staged 文件, 产物存在性和验证证据.
   - normal issue 缺少可信 RED/GREEN 证据时不进入 review.
   - 异常或 dirty tree 转 `RECOVERY.md`.

5. 轻量 review 判定.
   - 如果是 `test-only-light`, 按 `LIGHTWEIGHT-TEST-ONLY.md` 判断是否写 `review-skipped.md` 并跳过 3 reviewer.
   - 不满足轻量条件则走完整 review.

6. review 门禁和 review.
   - 门禁通过后启动 3 个只读 reviewer.
   - 输出 `review-rN-一致性.md`, `review-rN-正确性.md`, `review-rN-简洁性.md`.

7. 综合判定.
   - 父会话分类发现项: 可立即修复, 延期, 需人工决策, 证据不足驳回.
   - 写 `review-综合判定-rN.md`.
   - 有需人工决策项时停下来问用户.

8. 修复与增量 review.
   - 对可立即修复项启动 fix worker.
   - 按发现项来源维度选择需要重跑的 reviewer.
   - 最多 3 轮, 发散或越界时停止并询问用户.

9. 最终验证.
   - 父会话运行聚焦验证, 必要时运行由父会话拥有的 full build 命令.
   - 复核日志与真实 diff 一致.
   - 报告最终 diff, TDD 或 GREEN-only 证据, 验证结果, review 解决情况, 遗留阻塞项, 残余风险.

10. 判断是否继续下一个 issue. 不继续时询问用户下一步行动.

# 最后

正式开始执行阶段前, 先对你自己复述一遍: 你的职责和行为边界.
