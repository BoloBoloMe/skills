# 眼罩 — 决策账本

AFK 工作流逐步披露改造. 目标: AFK 父会话只知当前步骤, 不掌握全局流程.

## D001 — 信息隔离模型

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: AFK 父会话通过 `_current.md` 路由文件获知当前应执行的步骤, 每次只持有当前步骤文件的内容. AFK 父会话不知道后续步骤的数量, 名称, 内容. to-issues 父会话负责一次性生成全部步骤文件, 可掌握 AFK 全貌.
- 理由: AFK 父会话掌握全局时会抢 worker 的活, 跳过细节, 急于完成. 限制其视野到当前步骤, 迫使它专注.
- 预计影响: `run-afk-workflow/SKILL.md` 改写为极简入口; `to-issues/SKILL.md` 增加步骤生成分支.
- 相关 issue: 待关联

## D002 — 状态追踪

- 状态: 已替代 → D013
- 约束性: 必须遵守
- 决策: 路由文件 `_current.md` 存于 issue 产物目录, 内容为纯自然语言, 写入当前应立即执行的步骤文件名. AFK 父会话读 `_current.md` 取出文件名即开始执行该步骤, 步骤完成后按末尾指引机械写入下一个步骤文件名. AFK 父会话不自主决定写什么.
- 理由: 纯自然语言避免结构化格式的维护负担. 模型足够理解自然语言. AFK 父会话不写内容则避免它自指自路的矛盾.
- 预计影响: `_current.md` 由 to-issues 初始化 (内容为 `step-01.md`), 由 AFK 父会话在各步骤末尾按指引更新.
- 相关 issue: 待关联

## D003 — 步骤文件命名

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 步骤文件名为纯数字序号 `step-01.md`, `step-02.md` 等, 不含阶段语义. 如将来需插入新步骤, 可增加小数 `step-02b.md`.
- 理由: 文件名是 AFK 父会话看到的信息之一, 含语义 (如 `step-launch-worker.md`) 会泄漏全局流程结构.
- 预计影响: `step-gen-guide.md` 按数字序号生成步骤文件.
- 相关 issue: 待关联

## D004 — 步骤文件生成者

- 状态: 已替代 → D014
- 约束性: 必须遵守
- 决策: to-issues 的父会话在执行 to-issues 时, 对适合 AFK 的 issue 一次性生成全部步骤文件. AFK 父会话不参与步骤文件生成.
- 理由: 谁生成步骤文件谁就知道全貌. to-issues 父会话知道全貌是可接受的, AFK 父会话不可以.
- 预计影响: to-issues `SKILL.md` 中增加: "如 issue 适合 AFK, 读取 `references/step-gen-guide.md`, 按指引在 issue 产物目录生成步骤文件".
- 相关 issue: 待关联

## D005 — 步骤生成指引

- 状态: 已替代 → D016
- 约束性: 必须遵守
- 决策: 步骤生成指引位于 `to-issues/references/step-gen-guide.md`, 是 to-issues 的外部参考材料. 它描述如何根据 issue 内容生成一整套步骤文件. to-issues 父会话是唯一消费者.
- 理由: step-gen-guide 是 to-issues 的分支所需, 不是 AFK 执行的分支所需. 按"分支是最干净的披露测试"原则, 放在 to-issues 下.
- 预计影响: 新建 `workflow/to-issues/references/step-gen-guide.md`.
- 相关 issue: 待关联

## D006 — 步骤文件内容

- 状态: 已替代 → D015
- 约束性: 必须遵守
- 决策: 步骤文件只写路由指针: 读哪个 prompt, 传入什么参数, 启动什么子代理, 产物路径是什么. 不内联 prompt 或 contract 的完整内容.
- 理由: 步骤文件负责"在这一步做什么"; prompt 文件负责"worker/reviewer 的详细角色定义". 分离后各自短小, AFK 父会话按需加载.
- 预计影响: 步骤文件中出现"告诉 worker 读取 `prompts/WORKER.md` 了解角色, 传入 issue 路径..." 等指针性文字. 父会话不读 prompt.
- 相关 issue: 待关联

## D007 — 分支出口

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 步骤文件末尾预写条件和对应的 `_current.md` 值. 如"如果 diff 为空, 将 `_current.md` 改为 `step-03.md`; 如果通过, 改为 `step-06.md`". AFK 父会话按条件选出口, 写 `_current.md`, 然后在下一次循环中读它. 不感知"回退"或"跳转"语义.
- 理由: AFK 父会话只需读条件、选分支、写路径, 不需要理解流程拓扑.
- 预计影响: 每个有分支的步骤文件末尾出现条件块.
- 相关 issue: 待关联

## D008 — attempt 处理

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 步骤文件不绑定 attempt 号, 一个 issue 的步骤文件适用于全部 attempt. AFK 父会话在需要 attempt 时 (如写 `worker-note-a2.md`) 从产物目录已有文件的编号推断.
- 理由: 如果步骤文件绑定 attempt, 每次重试需要新步骤文件, 又需生成能力, 违反信息隔离.
- 预计影响: 步骤文件中写"检查产物目录中已有的 `worker-note-aN`, 本次编号为 N+1".
- 相关 issue: 待关联

## D009 — 文件布局

- 状态: 已替代 → D012
- 约束性: 必须遵守
- 决策: `_current.md` 和全部 `step-NN.md` 存放于 issue 产物目录 `docs/changes/<feature-slug>/afk-running/<issueKey>/`. prompt 文件留在 `workflow/run-afk-workflow/prompts/`, step-gen-guide 留在 `workflow/to-issues/references/`.
- 理由: 步骤文件是 issue 产物, to-issues 生成; prompt 是 skill 静态资产. 同目录便于 AFK 父会话访问, 不跨目录跳转.
- 预计影响: issue 产物目录内容从当前的 `worker-note-aN.md` 扩展到包含 `_current.md` 和 `step-NN.md`.
- 相关 issue: 待关联

## D010 — 步骤粒度

- 状态: 已替代 → D011
- 约束性: 可调整
- 决策: 步骤划分为 15 步: 预检 (含组织输入) / 启动 worker / diff 门禁 / 正确性 review / 决策边界 review / 等待 review / 综合判定 / 修复循环判断 / 启动修复 worker / 修复 diff 门禁 / 运行验证 / 回写 issue / 更新决策 / 写 final-report / 结束.
- 理由: 每步一个原子操作. 预检与组织输入合并 — 均为执行前机械准备, 无分支无产物.
- 预计影响: step-gen-guide 生成 15 个步骤文件. 后续可按需增减.
- 相关 issue: 待关联

## D011 — 步骤粒度: 15 → 6

- 状态: 当前有效
- 约束性: 可调整
- 替代: D010
- 决策: 步骤划分为 6 步, 全局共享 (非 per-issue).
  01: 预检 + 启动 worker.
  02: diff 门禁.
  03: 正确性 + 决策边界 review (并行).
  04: 综合判定 + 修复决策 + 启动修复 worker.
  05: 修复 diff 门禁 (出口 → 03).
  06: 验证 + 回写 issue + 更新决策 + final-report + 下一 issue 切换 (出口 → 下一 issue:01 或 done).
- 理由: per-issue 15 步导致 N×15 文件爆炸. 步骤内容对所有 issue 通用, 唯一 per-issue 状态是 _current.md 中的 issue key + 步骤编号. 6 步固定, 不随 issue 数增长.
- 预计影响: `step-gen-guide.md` 从 15 步改为 6 步. `_current.md` 格式改为 `ISSUE-KEY:NN`. 步骤文件从 per-issue 产物目录移到 `afk-running/` 根.
- 相关 issue: 待关联

## D012 — 文件布局: 全局共享

- 状态: 当前有效
- 约束性: 必须遵守
- 替代: D009
- 决策: 6 个步骤文件 (`step-01.md` ~ `step-06.md`) 和 `_current.md` 存放于 `docs/changes/<feature-slug>/afk-running/` 根, 全 feature 共用. per-issue 产物 (worker note, review, fix-note, final-report) 存放于 `afk-running/<ISSUE-KEY>/`. prompt 文件留在 `workflow/run-afk-workflow/prompts/`, step-gen-guide 留在 `workflow/to-issues/references/`.
- 理由: 步骤文件是工作流定义 (what to do), 非 per-issue 产物. `_current.md` 承载唯一 per-issue 状态 (where we are). 分离定义与状态后, 文件数从 1 + 15N 降为 8 固定.
- 预计影响: `run-afk-workflow/SKILL.md` 执行循环和步骤文件位置描述更新. to-issues 步骤 6a 生成路径改为 `afk-running/` 根 + ISSUE-KEY 子目录.
- 相关 issue: 待关联

## D013 — 状态追踪: ISSUE-KEY:NN 格式

- 状态: 当前有效
- 约束性: 必须遵守
- 替代: D002
- 决策: `_current.md` 内容为 `ISSUE-KEY:NN` (如 `ISSUE-01:03`). run-afk-workflow 父会话解析: 冒号前 issue key, 冒号后步骤编号. 初始值 `ISSUE-01:01`. 全部 issue 完成时写入 `done`.
- 理由: 全局共享步骤文件需要同时标识当前 issue 和当前步骤. `ISSUE-KEY:NN` 一条记录承载两个维度. `done` sentinel 替代旧 `_current.md` 中无意义的旧值残留.
- 预计影响: `_current.md` 生成和更新逻辑改为写入 `ISSUE-KEY:NN` 或 `done`.
- 相关 issue: 待关联

## D014 — 步骤文件生成: 一次全 feature

- 状态: 当前有效
- 约束性: 必须遵守
- 替代: D004
- 决策: to-issues 父会话在用户确认切分方案并发布全部 issues 后, 一次性生成 6 个全局步骤文件 + 初始 `_current.md` (`ISSUE-01:01`) 到 `afk-running/`. 后续发布新 issue 时不重生步骤文件.
- 理由: per-issue 生成导致 N×16 文件, 其中 15N 是重复模板. 一次性全局生成消除文件爆炸, 且与 prompt 重构原则一致 (静态内容不按实例复制).
- 预计影响: to-issues 步骤 6a 从 per-issue 生成改为首次全局生成. 需要区分"步骤文件已存在"和"首次创建".
- 相关 issue: 待关联

## D015 — 步骤文件内容: 目录角色名

- 状态: 当前有效
- 约束性: 必须遵守
- 替代: D006
- 决策: 步骤文件中用目录角色名指代路径, 不写绝对路径或 `<...>` 占位符. 如: "feature 根目录下的 CONTRACT.md", "issues 目录下以当前 issue key 开头的 .md 文件", "当前 issue 产物目录". run-afk-workflow 父会话按 `_current.md` 中的 issue key 和约定目录结构推断实际路径.
- 理由: 步骤文件不含 baked-in 路径, 避免旧模型"编译期替换占位符"的矛盾. 父会话已在做路径注入 (给子代理的 task), 同样的能力可用于自己的步骤文件.
- 预计影响: `step-gen-guide.md` 不含 `<...>` 占位符. 步骤文件内容用角色名描述, run-afk-workflow 父会话按约定解析.
- 相关 issue: 待关联

## D016 — 步骤生成指引: 改写

- 状态: 当前有效
- 约束性: 必须遵守
- 替代: D005
- 决策: 步骤生成指引仍位于 `workflow/to-issues/references/step-gen-guide.md`, 内容从 15 步 per-issue 模板改为 6 步全局步骤定义. to-issues 父会话是唯一消费者.
- 理由: 文件位置不变, 角色不变 — 是 to-issues 的外部参考. 内容需改写以支持 6 步 + 全局共享 + 目录角色名.
- 预计影响: `step-gen-guide.md` 重写. to-issues 的 SKILL.md 步骤 6a 描述更新.
- 相关 issue: 待关联

## D017 — 多 issue 编排

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: step-06 结束时, run-afk-workflow 父会话扫描 `afk-running/` 下 `ISSUE-*` 目录, 按编号排序, 跳过已有 `final-report.md` 的目录. 取第一个未完成的 issue key, 更新 `_current.md` 为 `<next-key>:01`. 全部完成 → `done`.
- 理由: 全局步骤文件使多个 issue 可以串行执行而无需重新生成步骤文件. 扫描 ISSUE-* 目录按命名约定发现下一 issue, 不需要 index 文件.
- 预计影响: step-06 内容包含扫描和切换逻辑. 无 index.md.
- 相关 issue: 待关联
