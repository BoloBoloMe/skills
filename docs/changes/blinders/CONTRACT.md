# 眼罩: AFK 工作流逐步披露改造 Contract

## 背景

`run-afk-workflow` 的 per-issue 15 步架构存在过度工程: N 个 issue 产生 N×15 个重复步骤文件. 审核报告 `docs/review/per-issue-step-files.md` 确定: 步骤文件应为全局共享 (每 feature 6 个), `_current.md` 格式改为 `ISSUE-KEY:NN` 以承载多 issue 串行编排.

## 目标

- 步骤文件从 per-issue 15 步改为全局共享 6 步, 存放在 `afk-running/` 根, 全 feature 共用.
- `_current.md` 格式从 `step-01.md` 改为 `ISSUE-01:01`, 终点 `done`. 承载当前 issue key 和步骤编号.
- to-issues 父会话在确认切分方案后一次性生成 6 个步骤文件 + 初始 `_current.md`, 后续发布 issue 时不重生.
- 步骤文件内容用目录角色名 (如 "当前 issue 产物目录"), 不写 absolute path 或占位符. run-afk-workflow 父会话按约定推断.
- step-06 收尾后自动扫描 `afk-running/` 下未完成 issue, 切换至下一 issue 或写入 `done`.
- 现有 worker, reviewer prompt 保持静态 (WORKER.md, REVIEWER.md), 父会话通过 task 注入路径.
- 中断恢复: run-afk-workflow 父会话读 `_current.md` 获取 `ISSUE-KEY:NN` 即可从断点继续.

## 非目标

- 不修改 subagent 调用机制.
- 不修改 issue 模板和格式.
- 不修改 `orchestrate`, `to-contract`, `to-prd`, `decision-ledger` 等其他 workflow skill.
- 不引入 index.md 或 issue 清单文件.

## 行为边界

- to-issues 父会话: 切分方案确认后, 发布全部 issues, 然后在 `afk-running/` 根一次性生成 `step-01.md` ~ `step-06.md` 和 `_current.md` (内容 `ISSUE-01:01`).
- to-issues 父会话: 生成步骤文件时, 按 `step-gen-guide.md` 中的 6 步定义, 用目录角色名写入指引.
- run-afk-workflow 父会话: 读 `_current.md` → 解析 `ISSUE-KEY:NN` → 读 `step-NN.md` → 执行 → 按步骤末尾出口更新 `_current.md`.
- run-afk-workflow 父会话: 从 `_current.md` 中的 issue key 推断: issue 定义文件 (`issues/` 下以 key 开头的 .md), 产物目录 (`afk-running/<key>/`), contract, decisions.
- step-06: 验证 + 回写 issue + 更新决策 + 写 final-report. 然后扫描 `afk-running/ISSUE-*` 目录, 找下一个未完成的 issue, 更新 `_current.md` 为 `<next-key>:01`. 全部完成 → `done`.
- 修复循环: step-04 → step-05 → step-03 → step-04 (回路). attempt 数由 run-afk-workflow 父会话扫描产物目录推断, 上限 3.
- 步骤文件不含阶段语义 (纯数字命名 `step-01.md` ~ `step-06.md`).
- run-afk-workflow 父会话不主动读其他 `step-NN.md`.

## 决策引用

完整决策账本: `docs/changes/blinders/DECISIONS.md`.

| 决策 ID | 约束要点 |
|---------|---------|
| D001 | AFK 父会话只知当前步骤; to-issues 父会话可掌握全貌 |
| D003 | 步骤文件纯数字命名, 不泄漏语义 |
| D007 | 步骤末尾预写分支条件和出口值 |
| D008 | 步骤文件不绑定 attempt, 运行时从产物目录推断 |
| D011 | 6 步粒度, 全局共享: 01 预检+启动 / 02 diff门禁 / 03 review并行 / 04 判定+修复 / 05 修复diff / 06 收尾+切换 |
| D012 | 目录: `afk-running/` 根放步骤文件, `ISSUE-*/` 放 per-issue 产物 |
| D013 | `_current.md` 格式 `ISSUE-KEY:NN`, 终点 `done` |
| D014 | to-issues 一次性生成全局步骤文件 |
| D015 | 步骤文件用目录角色名, run-afk-workflow 父会话推断路径 |
| D016 | step-gen-guide 改写为 6 步 |
| D017 | step-06 扫描 ISSUE-* 目录, 自动切换下一 issue |

## 未确认假设

- 假设: run-afk-workflow 父会话不会主动读取同目录下其他 `step-NN.md`.
  影响: 如读后续步骤, 信息隔离被打破.
  验证方式: 首次跑通后检查父会话是否有越界行为.
- 假设: 6 步粒度足够覆盖所有 AFK issue.
  影响: 遇不匹配 issue 时需调整 step-gen-guide.
  验证方式: 首次 AFK 执行后评估.

## 代码边界提示

涉及修改的文件:

- `workflow/run-afk-workflow/SKILL.md` — 更新执行循环 (ISSUE-KEY:NN), 步骤文件位置 (afk-running/ 根), 边界约束.
- `workflow/to-issues/references/step-gen-guide.md` — 从 15 步 per-issue 模板改写为 6 步全局步骤定义.
- `workflow/to-issues/SKILL.md` — 步骤 6a 从 per-issue 生成改为首次全局生成.
- `docs/changes/blinders/DECISIONS.md` — 已更新 (D011-D017).
- `docs/changes/blinders/CONTRACT.md` — 本文档, 已同步.

不变文件:
- `workflow/run-afk-workflow/prompts/WORKER.md` — 不动.
- `workflow/run-afk-workflow/prompts/REVIEWER.md` — 不动.

## 允许范围

- 可修改: `workflow/run-afk-workflow/SKILL.md`, `workflow/to-issues/SKILL.md`, `workflow/to-issues/references/step-gen-guide.md`.
- 可在步骤文件中引用现有 prompt 文件路径.

## 禁止范围

- 不修改 prompt 文件 (WORKER.md, REVIEWER.md).
- 不在 `run-afk-workflow` 中引入新的子代理角色.
- 不在 `to-issues` 的 issue 模板中增加执行步骤相关字段.

## 验证入口

- 可观察: to-issues 执行后, `afk-running/` 下存在 `_current.md` (内容 `ISSUE-01:01`) 和 6 个 `step-NN.md`.
- 可观察: run-afk-workflow 父会话执行时, 每个步骤只读当前 `step-NN.md`.
- 可观察: step-06 结束后, `_current.md` 变为 `ISSUE-02:01` (多 issue) 或 `done` (全部完成).
- 功能验证: 完整执行至少 2 个 AFK issue 串行通过所有阶段, 最终产出两个 `final-report.md`.

## 风险和停止条件

- 需要改变 subagent 调用 API 时停止.
- 需要改变 prompt 文件内容时停止.
- 发现 run-afk-workflow 父会话无法按目录角色名推断路径时停止.
- 首次 AFK 执行发现 6 步粒度过粗或过细时, 调整 D011 并更新 step-gen-guide.
- ISSUE-* 目录扫描发现编号不连续或命名不一致时停止.

## 下游 issue 约束

- issue 拆分必须在 `docs/changes/<slug>/issues/<NN>-<slug>.md`.
- AFK issue 的执行产物一律在 `afk-running/<ISSUE-KEY>/` 下.
- 步骤文件是全局资产, to-issues 只生成一次; run-afk-workflow 父会话不参与生成.
