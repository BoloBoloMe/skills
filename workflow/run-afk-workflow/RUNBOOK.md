# AFK runbook

本文件定义正常 AFK 主流程. 执行前必须先读取 `CONTRACTS.md`. 遇到异常, 超时, dirty tree, 产物缺失或 reviewer 失败时, 立即转读 `RECOVERY.md`. 进入或判断 `test-only-light` 时, 同时读取 `LIGHTWEIGHT-TEST-ONLY.md`.

## 预检

父会话在启动 worker 前必须确认:

- 工作树干净, 无未提交变更. 不干净时不启动 worker, 要求用户处理.
- PRD, issue, PLAN 已存在且已确认.
- 允许文件清单已明确.
- `validation-env.md` 已写入, 依赖预热已执行或明确跳过, 聚焦测试命令模板已 smoke 验证.
- `agent-binding.md` 已写入, implementation, review, recovery 角色已解析.
- 每个 issue 的 `review-policy.md` 已写入.
- TDD 可行性成立: 测试文件能进入允许文件清单, 聚焦测试命令模板能运行目标模块测试, 需求能通过公共接口验证.

预检任一门禁不满足, 不启动 worker, 向用户报告阻塞项.

## issue 处理循环

### 0. 初始化 issue 产物目录

挑选下一个 issue 后:

1. 确定 `issueKey`.
2. 创建 `issueArtifactDir = <AFK_RUN_DIR>/<issueKey>/`.
3. 在 `run-manifest.md` 记录 issue 顺序, issue 路径, issueKey 和 issueArtifactDir.
4. 设置初版 review round 为 `r0`.

本 issue 的所有 worker, reviewer, recovery worker 都只使用 `issueArtifactDir` 作为产物目录.

### 1. 实现

使用 `agent-binding.md` 中的 implementation role 启动 worker. 读取 `prompts/WORKER-IMPLEMENT.md`, 替换占位符后拼入 task.

worker task 必须传入:

- `issueArtifactDir`.
- PRD, PLAN, issue 绝对路径.
- 允许文件清单.
- issue 执行类型.
- `validation-env.md` 绝对路径.
- `incrementalTestCommandTemplate`.
- 允许回退阶梯.

### 2. 差异检查

worker 结束后, 父会话自行检查真实 diff, 不只依赖 worker 报告.

通用检查:

- diff 是否为空.
- diff 是否越过允许文件清单.
- 是否有 staged 文件.
- `worker-result.md`, `worker-status.md`, `tdd-cycles.md` 是否存在.
- 使用的测试命令是否符合 `validation-env.md`.

normal issue 还必须确认:

- 生产代码变更有对应测试变更和 RED/GREEN 证据.
- `tdd-cycles.md` 记录了 RED 失败和 GREEN 通过.
- 缺少可信 RED 证据时标记为实现失败, 不进入 review.

`test-only-light` issue 的差异检查见 `LIGHTWEIGHT-TEST-ONLY.md`.

差异检查通过后, 父会话将当前 issue 文件中的 `- [ ] 已实现` 改为 `- [x] 已实现`. 找不到执行标记时停止并报告阻塞, 不自行发明新格式.

worker 异常终止但工作树有未提交变更时, 不自动重跑 worker. 先保存当前 diff 和恢复观察, 再按 `RECOVERY.md` 处理.

### 3. 轻量 review 判定

如果 `review-policy.md` 为 `skip-with-verification`, 按 `LIGHTWEIGHT-TEST-ONLY.md` 判定是否跳过 3 reviewer 和综合判定.

不满足轻量条件时走完整 review.

### 4. review 门禁

启动 reviewer 前必须确认:

- [ ] worker 结果报告存在.
- [ ] 真实 diff 未越过允许文件清单.
- [ ] 空白和格式检查通过.
- [ ] 聚焦测试已运行, 或阻塞项已记录.
- [ ] normal issue 有可信 RED/GREEN 证据.

任何一项不满足就不启动 reviewer. 父会话先按 `RECOVERY.md` 处理或询问用户.

### 5. review

门禁通过后, 使用 `agent-binding.md` 中的 review role 同时启动 3 个 reviewer. 环境不支持并行时退化为串行.

每个 reviewer 各自独立, 互不读取对方输出. 每个 task 都必须包含:

```md
禁止修改项目/源码文件. 允许写入本次配置的 review 输出产物. 不允许修复代码, 不允许 stage 文件.
```

提示词模板和输出:

- 一致性: `prompts/REVIEWER-CONSISTENCY.md` -> `review-rN-一致性.md`.
- 正确性: `prompts/REVIEWER-CORRECTNESS.md` -> `review-rN-正确性.md`.
- 简洁性: `prompts/REVIEWER-SIMPLICITY.md` -> `review-rN-简洁性.md`.

### 6. 综合判定

父会话读取本轮 3 份 review 报告, 分类发现项:

- **可立即修复** -- blocker 或 required, 证据充分, minimal fix 明确, 不需要产品/架构决策, 不越过允许文件.
- **延期** -- 有价值但非紧急, 或超出当前 afk 编码任务范围.
- **需人工决策** -- 需要产品, API, 架构或范围判断.
- **证据不足驳回** -- 无文件/行号/diff/命令证据支撑.

写综合判定报告到 `review-综合判定-rN.md`.

以下条件阻止进入修复:

- 可立即修复项为空 -> 跳过修复, 直接进最终验证.
- 需人工决策项非空 -> 停下来问用户.
- 修复会越过允许文件清单 -> 停下来问用户.

### 7. 修复与增量 review

使用 `agent-binding.md` 中的 implementation role 再次启动 worker. 读取 `prompts/WORKER-FIX.md`, 替换占位符后拼入 task.

worker task 必须传入最新综合判定报告绝对路径, 当前 fix round, issue 执行类型, `validation-env.md` 和允许文件清单.

修复完成后不默认重跑全部 reviewer. 根据上轮综合判定报告中可立即修复项的来源维度选择 reviewer:

| 修复项来源维度 | 重跑的 reviewer |
|---|---|
| 仅一个维度 | 只重跑该维度 reviewer |
| 跨两个维度 | 重跑两个维度 reviewer |
| 跨三个维度, 或修复涉及新增/删除文件 | 重跑全部三个 reviewer |

增量 review 规则:

- 重跑的 reviewer 以修复 diff 为主要审查对象.
- 被修改文件中未变更的部分沿用上轮审查结论.
- 未重跑的维度直接复用上轮 review 报告.

### 8. 增量综合判定

合并本轮增量 review 报告与上轮复用报告, 重新分类. 增加收敛判定:

- 可立即修复项为空 -> 进入最终验证.
- 可立即修复项数量 >= 上轮数量 -> 标记发散, 全部转为需人工决策, 停止循环.
- 已达最大轮次 3 轮 -> 停止循环, 剩余项转延期.

若修复引入的新问题落在未重跑的维度, 标记为需人工决策.

若收敛判定允许继续修复, 回到修复步骤. 否则进入最终验证.

### 9. 最终验证

父会话自行运行 `validation-env.md` 中的聚焦验证, 必要时运行由父会话拥有的 full build 命令. 复核 TDD 循环日志与真实 diff 一致.

最终报告必须覆盖:

- 最终 diff.
- TDD 证据或 GREEN-only 证据.
- 验证结果.
- review 解决情况.
- 遗留阻塞项.
- 残余风险.

### 10. 判断是否继续

如果应该继续执行下一个 issue, 回到 issue 处理循环.

如果不继续, 停下来询问用户下一步行动.
