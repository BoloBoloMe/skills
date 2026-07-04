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

- 状态: 当前有效
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

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: to-issues 的父会话在执行 to-issues 时, 对适合 AFK 的 issue 一次性生成全部步骤文件. AFK 父会话不参与步骤文件生成.
- 理由: 谁生成步骤文件谁就知道全貌. to-issues 父会话知道全貌是可接受的, AFK 父会话不可以.
- 预计影响: to-issues `SKILL.md` 中增加: "如 issue 适合 AFK, 读取 `run-afk-workflow/references/step-gen-guide.md`, 按指引在 issue 产物目录生成步骤文件".
- 相关 issue: 待关联

## D005 — 步骤生成指引

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 步骤生成指引位于 `run-afk-workflow/references/step-gen-guide.md`, 是 run-afk-workflow 的外部参考材料. 它描述如何根据 issue 内容生成一整套步骤文件. to-issues 父会话是唯一消费者.
- 理由: step-gen-guide 是 to-issues 的分支所需, 不是 AFK 执行的分支所需. 按"分支是最干净的披露测试"原则, 推至外部参考.
- 预计影响: 新建 `workflow/run-afk-workflow/references/step-gen-guide.md`.
- 相关 issue: 待关联

## D006 — 步骤文件内容

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 步骤文件只写路由指针: 读哪个 prompt, 传入什么参数, 启动什么子代理, 产物路径是什么. 不内联 prompt 或 contract 的完整内容.
- 理由: 步骤文件负责"在这一步做什么"; prompt 文件负责"worker/reviewer 的详细角色定义". 分离后各自短小, AFK 父会话按需加载.
- 预计影响: 步骤文件中出现"读取 `prompts/WORKER-IMPLEMENT.md`, 传入 issue 路径..." 等指针性文字.
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

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: `_current.md` 和全部 `step-NN.md` 存放于 issue 产物目录 `docs/changes/<feature-slug>/afk-running/<issueKey>/`. prompt 文件, step-gen-guide 等静态模板仍留在 `workflow/run-afk-workflow/` 下.
- 理由: 步骤文件是 issue 产物, to-issues 生成; prompt 是 skill 静态资产. 同目录便于 AFK 父会话访问, 不跨目录跳转.
- 预计影响: issue 产物目录内容从当前的 `worker-note-aN.md` 扩展到包含 `_current.md` 和 `step-NN.md`.
- 相关 issue: 待关联

## D010 — 步骤粒度

- 状态: 当前有效
- 约束性: 可调整
- 决策: 步骤划分为 19 步: 预检门禁 / 工作树检查 / 角色解析 / 读取失败模式 / 构建 task brief / 启动 worker / diff 门禁 / 正确性 review / 决策边界 review / review 等待 / 综合判定 / 启动修复 worker / 修复 diff 门禁 / 修复循环判断 / 运行验证 / 回写 issue / 更新决策 / 写 final-report / 结束.
- 理由: 每步一个原子操作, AFK 父会话可机械执行. 步骤边界与子代理启动, diff 检查, 用户数据写入等自然分段对齐.
- 预计影响: step-gen-guide 生成 19 个步骤文件. 后续可按需增减.
- 相关 issue: 待关联
