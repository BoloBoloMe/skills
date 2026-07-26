# AFK 步骤生成指引

`to-execution-spec` 在切片确认后读取本文件, 一次性生成 6 个全局步骤文件和初始 `_current.md`. `afk` 不读本文件.

## 生成规则

全部文件写入 `docs/changes/<feature-slug>/afk-running/`:

- `_current.md`: 初始内容为第一个 issue key 加 `:01`.
- `step-01.md` 到 `step-06.md`: 全部 issues 共用.

per-issue 产物由 `afk` 写入 `afk-running/<ISSUE-KEY>/`.

步骤文件使用以下目录角色名, `afk` 根据 `_current.md` 推断路径:

- **feature 根目录**: `afk-running/` 的父目录.
- **product**: feature 根目录下的 `PRODUCT.md`.
- **technical**: feature 根目录下的 `TECHNICAL.md`.
- **execution**: feature 根目录下的 `EXECUTION.md`.
- **decisions**: feature 根目录下的 `DECISIONS.md` (如存在).
- **当前 issue**: `issues/` 中以当前 issue key 开头的 `.md`.
- **当前 issue 产物目录**: `afk-running/<ISSUE-KEY>/`.

步骤文件禁止内联 system prompt/Spec/issue 正文, 禁止写 feature 特有实现细节, 绝对路径或占位符.

## step-01

生成 `step-01.md`:

```markdown
# 步骤 01: 预检和启动 worker

确认工作树状态来源清楚, worker/reviewer 可用. 读取 product, technical, execution, decisions (如存在) 和当前 issue. 确认当前 issue 已物化 (issues/ 中存在对应文件, 非未决轮廓) 且 execution 含重切授权. 验证 issue 中的覆盖 ID/决策引用/父级引用可解析. 任一失败 -> 停止并在会话中报告.

创建当前 issue 产物目录. 扫描 worker-note-aN/fix-note-aN 确定 attempt N, 无则 N=1. 输出为当前 issue 产物目录/worker-note-aN.md.

按 afk 的 system prompt 规则启动初始 worker 的计划相:
- 目标: 阅读权威输入和相关代码, 不写实现代码或测试; 在 note 写出接口与测试清单 (公共接口草图, 计划测试的行为清单及顺序) 和改动入口预判, 然后停止返回.
- 必读: product, technical, execution, decisions (如存在), 当前 issue.
- 输出: 上述 worker note.

父会话审查计划: 接口草图和测试清单是否越出允许范围或触碰禁止范围, 是否与 spec/决策冲突, 是否漏盖验收标准的关键行为.
- 通过 -> resume 同一 worker 进入实现相: 按 worker-tdd.md 红-绿-重构实现当前 issue 全部验收标准, 更新同一 note.
- 可纠正问题 (顺序, 遗漏, 接口形状) -> resume 同一 worker 附纠正意见, 先修计划再实现.
- 需改 spec/issue/决策 -> 停止并在会话中报告.

worker 中断时优先 resume.

---
worker 完成 -> _current.md 写为 :02
worker 不可恢复 -> 停止并在会话中报告
```

## step-02

生成 `step-02.md`:

```markdown
# 步骤 02: diff 门禁

检查 worker diff:
- diff 非空.
- 每个改动可追溯到当前 issue 的 AC/TG/NFR 或必要测试.
- 未越过允许范围或触碰禁止范围.
- 无 staged 文件或未知来源变更.
- worker-note-aN.md 存在, 且含接口与测试清单, 实现发现, 重构候选, RED/GREEN/验证证据, 风险和阻塞.
- 实现发现中标注需改 spec/issue/决策的项 -> 停止并在会话中报告 (worker 应已停止, 本步为兜底).
- step-06 物化产生的文档变更 (新 issue 文件, EXECUTION 更新) 属已知来源.

---
通过 -> _current.md 写为 :03
diff 为空 -> _current.md 写为 :01
越界/未知变更/证据缺失 -> 停止并在会话中报告
```

## step-03

生成 `step-03.md`:

```markdown
# 步骤 03: 并行 review

按 afk 的 system prompt 规则并行启动两个只读 reviewer, 不共用 prompt:

1. 正确性 reviewer:
   - 维度: 逻辑, 边界, 异常, 回归, 并发, 数据一致性, 测试覆盖, 死代码.
   - 输入: product, technical, execution, decisions (如存在), 当前 issue, worker-note-aN, git diff.
   - 输出: 当前 issue 产物目录/review-correctness-aN.md.

2. Spec 边界 reviewer:
   - 维度: PRODUCT/TECHNICAL/EXECUTION/decisions 遵守, AC/TG/NFR 覆盖, issue 允许/禁止范围, 越界, 提前实现, 隐含新决策.
   - 输入: 同上.
   - 输出: 当前 issue 产物目录/review-spec-boundary-aN.md.

reviewer 中断时优先 resume.

---
两份报告就绪 -> _current.md 写为 :04
任一 reviewer 不可恢复 -> 停止并在会话中报告
```

## step-04

生成 `step-04.md`:

```markdown
# 步骤 04: 综合判定和修复

读取两份 review, 分类:
- 可直接修: 证据清楚, 不需产品/API/架构/范围决策, 且在当前 issue 范围内.
- 需我决策: 需改变任一 Spec/issue/decision, 扩大范围或作产品/API/架构取舍.
- 不采纳: 缺证据, 误读 diff, 或建议越界.
- 通过: 无实质问题.

可通过 -> _current.md 写为 :06.

需我决策 -> 停止. 在会话中说明问题, 影响, 推荐和一个待回答问题, 不要求我阅读 review.

可直接修:
- 根据已有 fix-note 确定下一 attempt.
- attempt >= 3 时转 :06, 在 final report 记录残余风险.
- 同类问题重复或恶化时停止并在会话中报告.
- 否则按 afk 的 prompt 规则启动修复 worker, 只修复明确采纳的发现项.
- 输入: 全部 Spec, decisions, 当前 issue, 两份 review, 上轮 note, 综合判定.
- 输出: 当前 issue 产物目录/fix-note-aN.md.

---
修复 worker 完成 -> _current.md 写为 :05
修复 worker 不可恢复 -> 停止并在会话中报告
```

## step-05

生成 `step-05.md`:

```markdown
# 步骤 05: 修复 diff 门禁

检查修复后的完整 diff:
- diff 非空.
- 只处理已采纳发现项和保持测试通过所需改动.
- 未越过允许范围或触碰禁止范围.
- 无 staged 文件或未知来源变更.
- fix-note-aN.md 存在且证据完整.

---
通过 -> _current.md 写为 :03
diff 为空 -> _current.md 写为 :04
越界/未知变更/证据缺失 -> 停止并在会话中报告
```

## step-06

生成 `step-06.md`:

```markdown
# 步骤 06: 验证和收尾

执行当前 issue 的验证入口和 EXECUTION 中与其覆盖 ID 对应的完成定义. 验证失败 -> 停止并在会话中报告, 不勾选完成.

验证每项 issue 验收标准都有可复核证据. 通过后:
- 将当前 issue 的 `- [ ] 已实现` 改为 `- [x] 已实现`.
- 调用 decision-ledger, 基于真实 diff 更新相关决策的实际影响.
- 写入当前 issue 产物目录/final-report.md, 包含可观察结果, 覆盖的 AC/TG/NFR, 最终 diff, 验证证据, review 处理, 决策实际影响, 实现发现与重构候选汇总, 未运行项和残余风险.
- 提交本次 issue 变更, 提交信息按以下模板生成:

  ```text
  [type]([scope]): [ISSUE-KEY] - [summary]

  [ISSUE-KEY] 实现完成.

  变更:
  - [change-1]
  - [change-2]
  - ...

  验收标准: 全部通过, 见 final-report.md.
  ```

  字段:
  - `[type]`: 从 issue 推断, 默认 `feat`. 可选: `feat` / `fix` / `refactor` / `perf` / `chore`.
  - `[scope]`: feature-slug.
  - `[ISSUE-KEY]`: 当前 issue key.
  - `[summary]`: issue 文件的一行描述, 取第一条非标题/非元数据行; 取不到则用 `[ISSUE-KEY]`.
  - `[change-N]`: 从 worker-note-aN 的 RED/GREEN 或 final-report 提取的关键变更点. 无变更点则省略 `变更:` 块.

按 EXECUTION 任务图找到下一个未决轮廓:
- 找到 -> 重切物化: 依据刚关闭 issue 的 final-report, 各 worker-note/fix-note 的实现发现和全部已关闭 issue 的实现知识, 按 EXECUTION 重切授权把该轮廓物化为 issues/ISSUE-NN-<slug>.md 全文 (遵循 issue 模板; 轻量重切内可调整覆盖 ID 组合, 顺序和边界), 并更新 EXECUTION 任务图与覆盖矩阵 (该条目标记已冻结). 物化文档随下一 issue 的提交一并入库. 在会话中一句话说明重切结果, 然后 _current.md 写为 <下一 issue key>:01, 继续.
- 触发越权条件 (切片数超上限; 需推翻已关闭 issue 的假设; 需改变 PRODUCT/TECHNICAL/DECISIONS) -> 停止并在会话中报告.
- 无未决轮廓 -> 检查 EXECUTION 覆盖矩阵中的每个 AC/TG/NFR 均有已完成 issue 和 final-report 证据. 写入 afk-running/final-report.md, 汇总各 issue 的可观察结果, 验证证据, 实现发现和重构候选, 再将 _current.md 写为 done.

覆盖缺口或证据缺失 -> 停止并在会话中报告.
```
