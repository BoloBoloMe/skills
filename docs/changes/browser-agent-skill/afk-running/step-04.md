# 步骤 04: 综合判定 + 修复决策 + 启动修复 worker

读取 review-correctness-aN.md 和 review-decision-boundary-aN.md, 分类:

- 可直接修: 证据清楚, 不需产品/设计/API 决策, 修复在允许范围内.
- 需我决策: 需改 contract/issue/decisions, 扩大范围, 或做产品/API/架构取舍.
- 不采纳: reviewer 缺证据, 误读 diff, 或建议超出本 issue/已确认决策.
- 通过: 无实质问题.

---

可通过 (无问题/仅 deferred/全部不采纳):
  → _current.md 写为 :06

需我决策:
  → 停止并报告

可直接修:
  检查修复 attempt: 扫描当前 issue 产物目录下 fix-note-aN, 当前 attempt = N+1.
  当前 attempt >= 3 或问题未收敛 → _current.md 写为 :06 (记录残余风险).
  同类问题重复或恶化 → 停止并报告.
  可继续 → 启动修复 worker.

修复 worker task:
  - 角色文件: worker 角色文件
  - 任务: 只修复综合判定中标记为可直接修的问题, 引用 reviewer 发现项编号. 不处理延期/驳回/需我决策项.
  - 输入: contract, decisions, 当前 issue 定义文件, 两份 reviewer 报告, 上轮 worker/fix note, 综合判定
  - 输出: 当前 issue 产物目录/fix-note-aN.md
  - 约束: 调用 tdd skill, 读 worker-tdd.md (用户说不用 TDD 时可省略)

修复 worker 中断时优先 resume.

---

修复 worker 完成 → _current.md 写为 :05
修复 worker 不可恢复 → 停止并报告
