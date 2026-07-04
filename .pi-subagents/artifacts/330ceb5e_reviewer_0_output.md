所有文件已读取完毕, 下面逐项对照 DECISIONS.md 和 CONTRACT.md 进行审核.

---

## Review

### 1. step-gen-guide 是否定义了 6 步 (D011), 且步骤职责一致?

**一致**.

D011 定义: 01 预检+启动 / 02 diff门禁 / 03 review并行 / 04 判定+修复 / 05 修复diff / 06 收尾+切换.

step-gen-guide.md `## 步骤定义` 下定义 step-01 ~ step-06:
- step-01: "预检 + 启动 worker" (lines ~68)
- step-02: "diff 门禁" (lines ~88)
- step-03: "review 并行" — 正确性 + 决策边界 (lines ~104)
- step-04: "综合判定 + 修复决策" + 启动修复 worker (lines ~124)
- step-05: "修复 diff 门禁" — 出口 `:03`(通过) / `:04`(空diff 回退) (lines ~174)
- step-06: "收尾" — 验证/回写/决策/report/扫描切换 (lines ~192)

step-05 中 `diff 为空 → :04` 是对 D011 "出口 → 03" 的补充细化 (非空走 :03, 空走 :04 重试修复), 不是矛盾. ✓

### 2. step-gen-guide 是否使用目录角色名而非绝对路径/占位符 (D015)?

**一致**.

step-gen-guide.md 含 `## 生成规则 > ### 目录角色名` 节, 明确定义:
- feature 根目录 / contract / decisions / 当前 issue 定义文件 / 当前 issue 产物目录 / worker 角色文件 / reviewer 角色文件

步骤正文中使用以上角色名, 如 "读取 contract, decisions (如存在), 当前 issue 定义文件" (step-01), "worker 角色文件" (step-01). 全文无绝对路径 (如 `/home/...`) 也无 `<PLACEHOLDER>` 占位符. `### 禁止` 节明确禁止绝对路径和占位符. ✓

### 3. run-afk-workflow/SKILL.md 执行循环是否实现 ISSUE-KEY:NN 和 done sentinel (D013)?

**一致**.

`## 执行循环` 节:
- "`_current.md` 格式: `ISSUE-KEY:NN` (如 `ISSUE-01:03`). 冒号前定位当前 issue, 冒号后定位当前步骤文件. 终点 `done`."
- 首次进入: 解析 → 若 `done` 则报告退出; 否则读 `step-NN.md` → 执行 → 更新.
- 中断恢复: 读断点 `ISSUE-KEY:NN` → 继续.
- 出口值: `:02`, `:03`, `<next-key>:01`, `done`.

与 D013 "内容为 `ISSUE-KEY:NN`, 全部完成时写入 `done`" 完全吻合. ✓

### 4. run-afk-workflow/SKILL.md 步骤文件位置是否描述为 afk-running/ 根 + ISSUE-*/ 产物目录 (D012)?

**一致**.

`### 步骤文件位置` 节明确给出目录结构:
```
docs/changes/<feature-slug>/afk-running/
  _current.md               ← "ISSUE-01:03"
  step-01.md ~ step-06.md   ← 6 个全局共享
  ISSUE-01/                  ← per-issue 产物
  ISSUE-02/
```

与 D012 "6 个步骤文件和 `_current.md` 存放于 `afk-running/` 根, per-issue 产物存放于 `afk-running/<ISSUE-KEY>/`" 完全吻合. ✓

### 5. run-afk-workflow/SKILL.md 是否包含路径推断约定 (D015)?

**一致**.

`### 路径推断` 节列出 6 条推断规则, 与 step-gen-guide.md 的目录角色名一一对应:
- feature 根目录 / contract / decisions / 当前 issue 定义文件 / 当前 issue 产物目录 / worker/reviewer 角色文件

D015 要求 "run-afk-workflow 父会话按 `_current.md` 中的 issue key 和约定目录结构推断实际路径", 该节完整实现. ✓

### 6. run-afk-workflow/SKILL.md 盲视约束是否保留 (D001)?

**一致**.

D001 要求 "AFK 父会话只知当前步骤, 不知全局".

run-afk-workflow/SKILL.md 多处实现该约束:
- 开头: "你只按步骤文件机械执行, 不掌握全局流程"
- `## 硬边界` 禁止项: "读同目录下其他 `step-NN.md`", "自主决定跳过或重排步骤"
- `## 执行循环` 末尾: "你每次只持有 `_current.md` + 当前步骤文件. 不知道后续步骤数量, 名称, 内容"

三条共同确保盲视约束. ✓

### 7. to-issues/SKILL.md 步骤 6a 是否描述为"一次性全局生成"而非"per-issue 生成" (D014)?

**一致**.

`### 6a. AFK 步骤文件生成` 节:
- 开头: "切分方案确认且全部 issues 发布后, 按以下流程生成**全局步骤文件**"
- 步骤 1: 检查是否**已有** `step-01.md` (幂等性)
- 步骤 2-3: 若不存在 → 一次性生成 6 步 + `_current.md`
- 末尾: "后续发布 issue 时**不重生步骤文件**"

完全符合 D014 "一次性生成 6 个全局步骤文件 + 初始 `_current.md`, 后续发布新 issue 时不重生". ✓

### 8. to-issues/SKILL.md 步骤 6a _current.md 初始值是否为 ISSUE-01:01 (D013)?

**一致**.

步骤 6a 第 3 点: `_current.md` — 初始内容 `ISSUE-01:01`.

与 D013 "初始值 `ISSUE-01:01`" 完全吻合. ✓

### 9. 步骤文件数量: 6 步 (非 15), 7 个文件 (非 16)?

**一致**.

- step-gen-guide.md: 定义 step-01 ~ step-06, 共 **6 步**, 无 step-07 及以上, 无 15 步残留.
- to-issues/SKILL.md 步骤 6a 末尾: "确认目录下存在 **7 个文件** (`_current.md` + 6 个 `step-NN.md`)", 非 16.

D011 "6 步" 和 D014 隐含的 7 个文件数均吻合. ✓

### 10. step-06 (收尾) 是否包含多 issue 扫描切换逻辑 (D017)?

**一致**.

step-gen-guide.md step-06 末尾:
```
扫描: 列出 afk-running 下所有 ISSUE-* 目录, 按编号排序. 跳过已有 final-report.md 的.
  找到未完成 → _current.md 写为 <下一个 key>:01
  全部完成 → _current.md 写为 done
→ 继续执行
```

与 D017 "扫描 `afk-running/` 下 `ISSUE-*` 目录, 按编号排序, 跳过已有 `final-report.md` 的目录. 取第一个未完成的 issue key, 更新 `_current.md` 为 `<next-key>:01`. 全部完成 → `done`" 完全吻合. ✓

---

## 汇总

| # | 检查项 | 结论 |
|---|--------|------|
| 1 | step-gen-guide 6 步 + 职责一致 | 一致 |
| 2 | step-gen-guide 目录角色名 | 一致 |
| 3 | run-afk-workflow ISSUE-KEY:NN + done | 一致 |
| 4 | run-afk-workflow 步骤文件位置 | 一致 |
| 5 | run-afk-workflow 路径推断 | 一致 |
| 6 | run-afk-workflow 盲视约束 | 一致 |
| 7 | to-issues 一次性全局生成 | 一致 |
| 8 | to-issues _current.md 初始值 | 一致 |
| 9 | 文件数量 (6 步, 7 文件) | 一致 |
| 10 | step-06 多 issue 扫描切换 | 一致 |

**全部 10 项一致, 无偏差, 无 blocker.**