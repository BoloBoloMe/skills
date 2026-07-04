# AFK 步骤生成指引

你在确认切分方案后读取本文件, 一次性在 `afk-running/` 根生成 6 个全局步骤文件和初始 `_current.md`. run-afk-workflow 父会话不读本文件.

## 生成规则

### 文件布局

全部步骤文件写入 `docs/changes/<feature-slug>/afk-running/`:

- `_current.md` — 初始内容 `ISSUE-01:01`
- `step-01.md` ~ `step-06.md` — 6 个全局共用步骤文件

per-issue 产物由 run-afk-workflow 父会话在执行时写入 `afk-running/<ISSUE-KEY>/`.

### 目录角色名

步骤文件中用以下角色名指代路径, run-afk-workflow 父会话按 `_current.md` 中的 issue key 和约定目录结构推断:

- **feature 根目录**: `afk-running/` 的父目录
- **contract**: feature 根目录下的 `CONTRACT.md`
- **decisions**: feature 根目录下的 `DECISIONS.md` (如存在)
- **当前 issue 定义文件**: issues 目录下以当前 issue key 开头的 .md 文件
- **当前 issue 产物目录**: `afk-running/<ISSUE-KEY>/`
- **worker 角色文件**: `run-afk-workflow` 的 `prompts/WORKER.md`
- **reviewer 角色文件**: `run-afk-workflow` 的 `prompts/REVIEWER.md`

### 禁止

- 步骤文件不内联 prompt 或 contract 的完整内容.
- 步骤文件不写 issue 特有实现细节.
- 步骤文件不写绝对路径或 `<...>` 占位符.

---

## 步骤定义

### step-01: 预检 + 启动 worker

```
# 步骤 01: 预检 + 启动 worker

确认: 工作树干净, worker 和 reviewer 子代理可用.
读取 contract, decisions (如存在), 当前 issue 定义文件. 全部可读 → 继续.

确定 attempt N: 扫描当前 issue 产物目录下现有 worker-note-aN 或 fix-note-aN, 无则 N=1.
输出: 当前 issue 产物目录/worker-note-aN.md.

启动 worker 子代理. task:
- 角色文件: worker 角色文件
- 任务: 实现当前 issue 的全部目标
- 输入: contract, decisions (如存在), 当前 issue 定义文件
- 输出: 上述输出路径
- 约束: 调用 tdd skill, 读 worker-tdd.md (用户说不用 TDD 时可省略)

worker 中断时优先 resume.

---

worker 完成 → _current.md 写为 :02
worker 不可恢复 → 停止并报告
```

### step-02: diff 门禁

```
# 步骤 02: diff 门禁

检查 worker 产出的 diff:

- git diff 非空
- 未越过当前 issue 允许范围
- 未触碰当前 issue 禁止范围
- 无 staged 文件 / 未知来源变更
- 当前 issue 产物目录下 worker-note-aN.md 存在且完整

---

diff 非空且通过 → _current.md 写为 :03
diff 为空 → _current.md 写为 :01 (重新启动 worker)
越过范围/未知变更 → 停止并报告
```

### step-03: review 并行

```
# 步骤 03: review 并行

启动两个 reviewer 子代理 (并行):

1. 正确性 reviewer. task:
   - 角色文件: reviewer 角色文件
   - 审查维度: 正确性 (逻辑/边界/异常/回归/并发/数据一致性/测试覆盖)
   - 输入: contract, decisions (如存在), 当前 issue 定义文件, 当前 issue 产物目录/worker-note-aN.md
   - diff 获取: git diff
   - 输出: 当前 issue 产物目录/review-correctness-aN.md

2. 决策边界 reviewer. task:
   - 角色文件: reviewer 角色文件
   - 审查维度: 决策边界 (contract 目标/非目标/行为边界, decisions 遵守, issue 允许/禁止范围, 是否越界/提前实现/需改决策)
   - 输入: 同上
   - diff 获取: git diff
   - 输出: 当前 issue 产物目录/review-decision-boundary-aN.md

reviewer 中断时优先 resume.

---

两份报告就绪 → _current.md 写为 :04
任一 reviewer 不可恢复 → 停止并报告
```

### step-04: 综合判定 + 修复决策 + 启动修复 worker

```
# 步骤 04: 综合判定 + 修复决策

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
```

### step-05: 修复 diff 门禁

```
# 步骤 05: 修复 diff 门禁

检查修复 worker 产出的 diff:

- git diff 非空
- 未越过当前 issue 允许范围
- 未触碰当前 issue 禁止范围
- 无 staged 文件
- 当前 issue 产物目录下 fix-note-aN.md 存在且完整

---

diff 非空且通过 → _current.md 写为 :03 (重新进入 review)
diff 为空 → _current.md 写为 :04 (重新启动修复 worker)
越过范围/未知变更 → 停止并报告
```

### step-06: 收尾

```
# 步骤 06: 收尾

验证: 执行当前 issue 的验证入口.
回写: 读取当前 issue 定义文件, 将 "- [ ] 已实现" 改为 "- [x] 已实现". 找不到标记 → 停止并报告.
决策: 调用 decision-ledger skill, 基于真实 diff 更新 feature 根目录下的 DECISIONS.md 中相关决策的实际影响.
报告: 写入 当前 issue 产物目录/final-report.md. 覆盖: 最终 diff 摘要, 验证结果, reviewer 发现项处理, 决策实际影响更新, 遗留阻塞项, 残余风险.

扫描: 列出 afk-running 下所有 ISSUE-* 目录, 按编号排序. 跳过已有 final-report.md 的.
  找到未完成 → _current.md 写为 <下一个 key>:01
  全部完成 → _current.md 写为 done
→ 继续执行
```
