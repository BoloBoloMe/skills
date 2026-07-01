# 眼罩: AFK 工作流逐步披露改造 Contract

## 背景

当前 `run-afk-workflow` 的 `SKILL.md` 包含完整执行流程 (预检 -> worker -> diff 门禁 -> review -> 判定 -> 修复 -> 验证). AFK 父会话一次读取后掌握全局, 导致抢 worker 的活, 跳过细节. 需要将执行指引拆分为逐步披露, AFK 父会话每次只持当前步骤, 不知后续步骤.

## 目标

- AFK 父会话执行时看不到全局流程, 只知当前步骤.
- AFK 父会话通过 `_next.md` 路由, 由步骤文件末尾指引机械推进.
- 步骤文件由 to-issues 阶段一次性生成, AFK 执行阶段不参与生成.
- 现有 worker, reviewer prompt 内容不变.
- 现有 AFK 产物规范不变 (产物目录, 文件命名, task brief 格式).
- 中断恢复: AFK 父会话读 `_next.md` 即可从断点继续.

## 非目标

- 不修改 `prompts/WORKER-IMPLEMENT.md`, `WORKER-FIX.md`, `REVIEWER-CORRECTNESS.md`, `REVIEWER-DECISION-BOUNDARY.md`.
- 不修改 subagent 调用机制.
- 不修改 issue 模板和格式.
- 不修改 `orchestrate`, `to-contract`, `to-prd`, `decision-ledger` 等其他 workflow skill.
- 不修改 AFK task brief 的内容结构.
- 不优化 AFK 执行的 token 消耗或性能.

## 行为边界

- to-issues 父会话执行 to-issues 时, 对适合 AFK 的 issue, 按 step-gen-guide 在 issue 产物目录生成全部步骤文件 (`step-01.md` ~ `step-19.md`) 和初始 `_next.md`.
- AFK 父会话读 `run-afk-workflow/SKILL.md` (极简入口) -> 读 `_next.md` -> 读当前步骤文件 -> 执行 -> 按步骤末尾指引更新 `_next.md` -> 重复.
- 步骤文件不含阶段语义 (纯数字命名).
- 同 issue 多次 attempt 复用同一套步骤文件.
- AFK 父会话不主动读同目录下的其他 `step-NN.md`.

## 决策引用

完整决策账本: `docs/changes/blinders/DECISIONS.md`.

| 决策 ID | 约束要点 |
|---------|---------|
| D001 | AFK 父会话只知当前步骤; to-issues 父会话掌握全貌 |
| D002 | `_next.md` 纯自然语言路由, AFK 父会话按指引机械写入 |
| D003 | 步骤文件纯数字命名, 不泄漏语义 |
| D004 | 步骤文件由 to-issues 一次性生成 |
| D005 | step-gen-guide 位于 run-afk-workflow/references/, to-issues 按需加载 |
| D006 | 步骤文件只写路由指针, 不内联 prompt |
| D007 | 步骤末尾预写分支条件和出口文件名 |
| D008 | 步骤文件不绑定 attempt, 运行时推断 |
| D009 | 全部文件放在 issue 产物目录 |
| D010 | 19 步粒度, 可调整 |

## 未确认假设

- 假设: AFK 父会话不会主动读取同目录下的其他 `step-NN.md` 文件.
  影响: 如模型读了后续步骤, 信息隔离被打破.
  验证方式: 在步骤文件中加入纪律约束. 首次跑通后检查父会话是否有越界行为.
- 假设: 19 步粒度足够覆盖所有 AFK issue.
  影响: 遇到不匹配 issue 时需调整 step-gen-guide.
  验证方式: 首次 AFK 执行后评估.

## 代码边界提示

涉及修改的文件:

- `workflow/run-afk-workflow/SKILL.md` — 改为极简入口 (触发门禁 + `_next.md` 路由 + 硬边界).
- `workflow/run-afk-workflow/references/step-gen-guide.md` — 新建. 被 to-issues 读取, 生成步骤文件.
- `workflow/to-issues/SKILL.md` — 步骤 6 (发布议题) 增加: AFK issue 时读取 step-gen-guide 并生成步骤文件.

prompt 文件 (WORKER-IMPLEMENT.md, WORKER-FIX.md, REVIEWER-CORRECTNESS.md, REVIEWER-DECISION-BOUNDARY.md) 为只读引用, 不改.

## 允许范围

- 可修改: `workflow/run-afk-workflow/SKILL.md`, `workflow/to-issues/SKILL.md` 的流程步骤.
- 可新建: `workflow/run-afk-workflow/references/step-gen-guide.md`.
- 可在步骤文件中引用现有 prompt 文件路径.

## 禁止范围

- 不修改 `prompts/` 目录下任何文件.
- 不修改 `workflow/orchestrate/SKILL.md` 的路由逻辑.
- 不在 `to-issues` 的 issue 模板中增加执行步骤相关字段.
- 不在 `run-afk-workflow` 中引入新的子代理角色.

## 验证入口

- 可观察: to-issues 执行后, issue 产物目录下存在 `_next.md` 和 19 个 `step-NN.md` 文件.
- 可观察: AFK 父会话执行时, 每个步骤只读当前步骤文件, 不触及后续步骤文件.
- 功能验证: 完整执行一个 AFK issue 通过所有阶段, 最终产出 `final-report.md`.

## 风险和停止条件

- 需要改变 subagent 调用 API 时停止.
- 需要改变 prompt 文件内容时停止.
- 发现 AFK 父会话无法只凭步骤文件完成操作时停止.
- 首次 AFK 执行发现步骤粒度过细或过粗时, 调整 D010 并更新 step-gen-guide.

## 下游 issue 约束

- issue 拆分时, AFK issue 的执行步骤文件必须由 to-issues 父会话按 step-gen-guide 生成.
- AFK issue 的执行相关产物一律在 `afk-running/<issueKey>/` 下.
- AFK 父会话不得自己生成或修改步骤文件.
