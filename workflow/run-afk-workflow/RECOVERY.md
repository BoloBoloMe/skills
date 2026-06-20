# AFK recovery

本文件定义 AFK 异常恢复规则. 任何恢复动作都必须服从 `SKILL.md` 中的父会话硬边界和 `CONTRACTS.md` 中的产物契约.

## 核心边界

父会话可以做:

- 机械性观察.
- 保存证据.
- 运行预检中确认的验证命令.
- 写流程性产物.
- 基于真实 diff, 已有日志和命令输出做流程决策.

父会话不得做:

- 修改生产代码.
- 修改测试代码.
- 修复编译错误, import, mock 配置, strict stubbing 等任何代码级问题.
- 替代 reviewer 做一致性, 正确性, 简洁性审查.
- 伪造 RED/GREEN 证据.

任何代码/测试修复都必须交给新 worker. 任何审查维度失败都必须交给替代 reviewer 或停下来问用户.

## recovery worker 模式

需要恢复 worker 时, 读取 `prompts/WORKER-RECOVER.md`, 替换占位符后拼入 task.

### complete-artifacts-only

只补齐产物, 不改代码. 用于代码 diff 看起来完整但报告缺失.

适用情况:

- worker 已留下可信 diff.
- 已有 `tdd-cycles.md` 或命令输出可以还原事实.
- 缺失的是 `worker-result.md`, `fix-result-rN.md` 或状态摘要.

### repair-validation

修复编译错误或测试失败. 必须遵守 allowed files 和 TDD 纪律.

适用情况:

- diff 在允许文件内.
- 验证命令失败指向明确的代码或测试问题.
- 修复不需要产品/API/架构决策.

### continue-from-dirty-tree

接着未完成 diff 继续实现. 必须先由父会话保存孤立 diff.

适用情况:

- worker 中断时工作树有未提交变更.
- 当前变更未完成, 但仍可在允许文件清单内继续.
- 父会话已写 `recovery-observation-rN.md` 和 `dirty-diff-rN.patch`.

## 恢复观察产物

父会话可以写 `recovery/recovery-observation-rN.md`, 内容只能来自可观察事实:

- diff 文件清单.
- 已存在的 `tdd-cycles.md` 片段.
- 子代理最终输出.
- 父会话实际运行过的验证命令和结果.
- 缺失证据列表.

如果需要补 `worker-result.md`, 必须标记:

```md
source: recovered-by-parent
```

并说明哪些字段缺失. 缺少可信 RED 时仍然不能进入 normal review.

## 恢复动作表

| 情况 | 动作 |
|---|---|
| worker 中途停滞, 工作树干净 | 不原样重跑. 根据 TDD 循环日志和产物判断进度, 缩小上下文后重新启动 worker. 不续接旧会话. |
| worker 中途停滞, 工作树有未提交变更 | 保存 `recovery/dirty-diff-rN.patch` 和 `recovery/recovery-observation-rN.md`. 机械检查 allowed files, 产物存在性, 验证命令结果. 若只缺产物, 启动 `complete-artifacts-only` worker. 若需要改代码, 启动 `repair-validation` 或 `continue-from-dirty-tree` worker. 不允许手工修复. |
| worker 有结果报告, 但报告信息不完整 | 可以补验命令并写恢复观察. 缺少 RED 证据时启动 recovery worker, 不直接放行. |
| worker 超时且已有代码 diff | 先确认是否支持恢复同一子代理. 若不恢复或恢复不可靠, 保存 diff 和恢复观察, 再启动 recovery worker. |
| worker 使用了错误验证环境 | 按 `validation-env.md` 重跑验证. 错误环境下的失败只记为环境噪音. 如需改代码, 启动 recovery worker. |
| reviewer 失败 | 最多重试一次. 再失败则启动替代 reviewer. 替代 reviewer 仍失败则标记 review 阻塞并询问用户. 不允许父会话直接审查该维度. |
| 已完成的 run 收到过期状态信号 | 忽略. |
| 子代理运行超时而中断 | 先保存可观察事实. 若已有产出符合预期且支持恢复, 可以恢复子代理. 否则按 worker 或 reviewer 对应恢复规则处理. |

## 恢复后回流

- `complete-artifacts-only` 成功后, 回到 `RUNBOOK.md` 的差异检查或 review 门禁.
- `repair-validation` 成功后, 回到差异检查与门禁.
- `continue-from-dirty-tree` 成功后, 回到差异检查.
- 任一恢复模式发现需要产品/API/架构决策, 停下来问用户.
- 任一恢复模式越过允许文件清单, 停止并报告.
