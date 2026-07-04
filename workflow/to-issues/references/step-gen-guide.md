# AFK 步骤生成指引

本文件由 `to-issues` 父会话在发布 AFK issue 时加载, 在 issue 产物目录生成全部步骤文件和初始 `_current.md`. AFK 父会话不读本文件.

## 生成规则

### 文件布局

全部产物写入 `<feature-dir>/afk-running/<issueKey>/`:

- `_current.md` — 初始内容 `step-01.md`
- `step-01.md` ~ `step-15.md`

### 占位符替换

`<...>` 占位符在生成时替换为绝对路径:

- `<issue产物目录>` — issue 产物目录绝对路径
- `<issue路径>` — issue 文件绝对路径
- `<contract路径>` — CONTRACT.md 绝对路径, 或 "无独立 contract"
- `<decisions路径>` — DECISIONS.md 绝对路径, 或 "无"
- `<worker_prompt>` — `workflow/run-afk-workflow/prompts/WORKER.md` 绝对路径
- `<reviewer_prompt>` — `workflow/run-afk-workflow/prompts/REVIEWER.md` 绝对路径

### 禁止

- 步骤文件不内联 prompt 或 contract 的完整内容.
- 步骤文件不写 issue 特有实现细节.

---

## 步骤模板

### step-01: 预检

```
# 步骤 01: 预检

确认以下条件全部满足:

- 工作树干净, 无 staged/未跟踪文件干扰.
- worker 和 reviewer 子代理可用.
- contract (<contract路径>) 可读取.
- issue (<issue路径>) 可读取.
- DECISIONS (<decisions路径>) 存在且可读取, 或明确无相关决策.
- issue 的相关决策, 允许范围, 禁止范围, 验证入口, 风险提示, 停止条件足够明确.

确定当前 attempt: 从产物目录已有 worker-note-aN 推断, 本次 N+1; 无则 a1.

确定 worker note 输出: <issue产物目录>/worker-note-aN.md.

---

全部满足 → 将 `_current.md` 写为 `step-02.md`
任一不满足 → 停止并向我报告
```

### step-02: 启动 worker

```
# 步骤 02: 启动 worker

启动 worker 子代理. task 必须包含:

- 角色文件: <worker_prompt>.
- 任务: 实现 issue (<issue路径>) 的全部目标.
- 输入文件: <contract路径>, <issue路径>, <decisions路径>.
- 输出文件: <issue产物目录>/worker-note-aN.md.
- 约束: 调用 `tdd` skill (默认, 跳过计划步骤), 同时读取该 skill 中的 `worker-tdd.md`. 用户说不用 TDD 时可省略全部. [父会话按需追加懒代码等额外约束].

worker 中断时优先 resume.

---

worker 完成 → 将 `_current.md` 写为 `step-03.md`
worker 不可恢复 → 停止并向我报告
```

### step-03: diff 门禁

> 步骤 03 和 步骤 10 使用相同逻辑, 分支出口不同.

```
# 步骤 03: diff 门禁

检查 worker 产出的真实 diff:

- git diff, git diff --name-only.
- diff 是否为空.
- diff 是否越过 issue 允许范围.
- diff 是否触碰 issue 禁止范围.
- 是否有 staged 文件.
- 是否存在未知来源变更.
- worker note 是否存在且完整.

---

diff 非空且通过所有检查 → 将 `_current.md` 写为 `step-04.md`
diff 为空 → 将 `_current.md` 写为 `step-01.md` (换新 worker)
越过允许范围/触碰禁止范围/未知来源变更 → 停止并向我报告
```

### step-04: 正确性 review

> 步骤 04 和 步骤 05 使用相同逻辑, 仅审查维度和输出文件名不同.

```
# 步骤 04: 正确性 review

启动正确性 reviewer. task 必须包含:

- 角色文件: <reviewer_prompt>.
- 审查维度: 正确性 (逻辑/边界/异常/回归/并发/数据一致性/测试覆盖).
- 输入文件: <contract路径>, <issue路径>, <decisions路径> (如存在), <issue产物目录>/worker-note-aN.md.
- diff 获取方式: git diff.
- 输出文件: <issue产物目录>/review-correctness-aN.md.

reviewer 中断时优先 resume.

---

reviewer 完成 → 将 `_current.md` 写为 `step-05.md`
reviewer 不可恢复 → 停止并向我报告
```

### step-05: 决策边界 review

```
# 步骤 05: 决策边界 review

启动决策边界 reviewer. task 必须包含:

- 角色文件: <reviewer_prompt>.
- 审查维度: 决策边界 (contract 目标/非目标/行为边界, DECISIONS 遵守情况, issue 允许/禁止范围, 是否越界/提前实现/需改决策).
- 输入文件: <contract路径>, <issue路径>, <decisions路径> (如存在), <issue产物目录>/worker-note-aN.md.
- diff 获取方式: git diff.
- 输出文件: <issue产物目录>/review-decision-boundary-aN.md.

reviewer 中断时优先 resume.

---

reviewer 完成 → 将 `_current.md` 写为 `step-06.md`
reviewer 不可恢复 → 停止并向我报告
```

### step-06: 等待 review

```
# 步骤 06: 等待 review

确认两份 review 报告就绪:

- <issue产物目录>/review-correctness-aN.md
- <issue产物目录>/review-decision-boundary-aN.md

任一缺失且 reviewer 在运行 → 等待.
任一缺失且 reviewer 已退出 → 重跑该 reviewer.

---

两份报告就绪 → 将 `_current.md` 写为 `step-07.md`
```

### step-07: 综合判定

```
# 步骤 07: 综合判定

读取两份 reviewer 报告, 分流:

- 可直接修: 证据清楚, 不需产品/设计/API 决策, 修复在允许范围内.
- 需我决策: 需改 contract/issue/DECISIONS, 扩大范围, 或做产品/API/架构取舍.
- 不采纳: reviewer 缺证据, 误读 diff, 或建议超出本 issue/已确认决策.
- 通过: 无实质问题.

---

可直接修 → 将 `_current.md` 写为 `step-08.md`
通过 (无问题/仅 deferred/全部不采纳) → 将 `_current.md` 写为 `step-11.md`
需我决策 → 停止并向我报告
```

### step-08: 修复循环判断

```
# 步骤 08: 修复循环判断

检查是否继续修复:

- 当前 fix attempt 计数 (从产物目录 fix-note-aN 推断).
- 对比当前与上一轮 reviewer 报告.
- 同类问题是否第二次出现.
- 问题数量/严重度是否下降.

---

可继续 (attempt < 3, 问题减少, 无同类重复) → 将 `_current.md` 写为 `step-09.md`
达到上限 (>=3) 或问题未收敛 → 将 `_current.md` 写为 `step-11.md` (记录残余风险)
同类问题重复或问题恶化 → 停止并向我报告
```

### step-09: 启动修复 worker

```
# 步骤 09: 启动修复 worker

启动修复 worker. task 必须包含:

- 角色文件: <worker_prompt>.
- 任务: 只修复综合判定中标记为可直接修的问题, 引用 reviewer 发现项编号. 不处理延期/驳回/需我决策项.
- 输入文件: <contract路径>, <issue路径>, <decisions路径>, reviewer 报告 (两份), 上轮 worker/fix note, 父会话综合判定.
- 输出文件: <issue产物目录>/fix-note-aN.md.
- 约束: 调用 `tdd` skill (默认, 修复场景), 同时读取该 skill 中的 `worker-tdd.md`. 用户说不用 TDD 时可省略全部. [父会话按需追加懒代码等额外约束].

worker 中断时优先 resume.

---

修复 worker 完成 → 将 `_current.md` 写为 `step-10.md`
修复 worker 不可恢复 → 停止并向我报告
```

### step-10: 修复 diff 门禁

> 与步骤 03 逻辑相同, 分支出口不同.

```
# 步骤 10: 修复 diff 门禁

检查修复 worker 产出的真实 diff:

- git diff, git diff --name-only.
- diff 是否为空.
- diff 是否越过 issue 允许范围.
- diff 是否触碰 issue 禁止范围.
- 是否有 staged 文件.
- fix note 是否存在且完整.

---

diff 非空且通过所有检查 → 将 `_current.md` 写为 `step-04.md` (重新进入 review 循环)
diff 为空 → 将 `_current.md` 写为 `step-01.md` (换新修复 worker)
越过允许范围/触碰禁止范围/未知来源变更 → 停止并向我报告
```

### step-11: 运行验证

```
# 步骤 11: 运行验证

运行 issue 验证入口:

- 从 issue 读取验证入口.
- 运行命令. 不可用时从 worker/reviewer 报告提取可复核验证.
- 记录结果. 必要时运行完整构建, 跳过则记录理由.

---

验证通过 → 将 `_current.md` 写为 `step-12.md`
验证失败 → 停止并向我报告
```

### step-12: 回写 issue

```
# 步骤 12: 回写 issue

回写执行标记:

- 读取 <issue路径>.
- 找到 `- [ ] 已实现` → 改为 `- [x] 已实现`.
- 找不到 → 停止并报告阻塞.

---

完成 → 将 `_current.md` 写为 `step-13.md`
找不到标记 → 停止并向我报告
```

### step-13: 更新决策

```
# 步骤 13: 更新决策

按 `decision-ledger` skill 规则更新 DECISIONS:

- 读取 `workflow/decision-ledger/SKILL.md`.
- 基于真实 diff, 更新 <decisions路径> 中相关决策的实际影响.
- 偏离可调整决策且 worker note 有说明 → 记录.
- diff 未改变决策相关内容 → 记录无影响.

---

完成 → 将 `_current.md` 写为 `step-14.md`
```

### step-14: 写 final-report

```
# 步骤 14: 写 final-report

写入 <issue产物目录>/final-report.md, 覆盖:

- 最终 diff 摘要.
- 验证结果.
- reviewer 发现项处理 (修复/驳回/延期及原因).
- 决策实际影响更新.
- 遗留阻塞项.
- 残余风险.

---

完成 → 将 `_current.md` 写为 `step-15.md`
```

### step-15: 结束

```
# 步骤 15: 结束

AFK 执行完成. 向我报告:

- issue 路径和完成状态.
- final-report 路径.
- 遗留阻塞项 (如有).
- 残余风险 (如有).

---

将 `_current.md` 写为 `done`.
```
