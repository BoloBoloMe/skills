# UNAUTHORIZED_DECISIONS (AFK 模式自主决策记录)

## UDA-001 子代理模型选型: llm-select 评分数据缺失, 降级为经验选型

- 问题: use-herdr 规定开新会话前用 llm-select skill 选模型, 但 `~/.agents/llm-select/` 目录不存在 (llm-scores.json 与 model-catalog.json 均缺失), score.py 报 no-catalog, 无法按评分表选型.
- 决策: 执行者 (coding 画像) 用 glm-5.3 + max thinking (本机 pi settings.json 的 defaultModel/defaultThinkingLevel, 用户既有默认即既有意愿); 审核者 (review 画像) 用 gpt-5.6-sol (本项目 DECISIONS.md F011 记录其已在 opposing-viewpoint 实际运行过, 且与产出方不同模型, 满足对抗对盲点错开规则).
- 理由: 评分表不可用时选型只能降级; 用户默认配置与项目先例是可得证据中最强的两个信号.
- 影响: 子代理质量可能非全局最优, 但不改变任务正确性; 审查与产出不同模型降低了同盲点漏检风险.
- 风险: glm-5.3/gpt-5.6-sol 若能力不足导致执行/审查质量下降; 事后可按真实评分表重评.

## UDA-002 review 修复期新增/调整测试用例 (tdd 的用例确认权在用户, AFK 代行)

- 问题: ISSUE-01 的 spec 轴评审发现 4 个实现问题, 修复需要触碰测试用例, 而 tdd skill 规定新用例须用户确认, 用户 AFK.
- 决策: 批准以下最小用例变化, 全部仍在既有确认过的接缝 (接缝 B) 与用例语义 (AC-007 环境/采集失败类) 之内: (1) TC-005 测试函数内追加一条断言: records-root 不可读 (OSError) 时 stderr 首行 ENV + exit 4, 依据 M1 退出码契约 0/4 且 不出现 1/2/3; (2) TS-003 的 corrupt fixture 允许调整措辞以配合引号包裹的名字匹配修复, 语义不变 (损坏文件属于该容器); (3) 测试自含化: monkeypatch require_command/which, 消除对仓外 PATH 垫片的依赖 (TC-005 自身的缺失断言除外).
- 理由: 修复评审发现项本身是循环授权的; 上述用例变化是修复的直接必要物, 不引入新接缝/新行为面.
- 影响: tests/test_swt_list.py 用例数可能 +1 或断言 +N, 均在既有 issue 覆盖矩阵内.
- 风险: 若用户事后不认可 OSError→4 的归类 (认为应属 warnings+0), 需要一次小改动回切; 已在评审报告与执行报告中留痕.

## UDA-003 review 发现的采纳/拒绝清单

- 问题: ISSUE-01 Standards 轴两个判断性坏味道, ISSUE-05 Standards 轴一个, 需决定采纳范围.
- 决策: (a) ISSUE-01 runtime 文件枚举重复: 采纳, 提取共享 helper (不改既有函数签名); (b) ISSUE-01 podman 基础观测结构重复: 拒绝, 触碰 podman_container_state 共享路径风险大于收益, 且 ISSUE-02 将做行模板两用化, 届时统一处理; (c) ISSUE-05 死代码 _merge_extensions: 采纳移除, 生产已无调用者 (评审已核实), 其独占旧测试随之删除, 符合 D012 泛化意图与 issue 允许范围 (以新函数替代并更新调用点).
- 理由: (a)(c) 收益明确风险低; (b) 违反禁令风险 (不改其余子命令行为) 优先于去重收益.
- 影响: ISSUE-02 需注意到 podman 观测去重被顺延.
- 风险: (b) 的重复结构在 ISSUE-02/03 中继续存在, 若后续字段变更需两处同步; 已留痕.

## UDA-004 推送时机: 每轮合并验证通过后即 push

- 问题: tdd-as-orchestra 规定 issue 分支只在本地不推远端, 而 AGENTS.md 规定改动收口后主动 push 交付; 两者的交汇点需拍板.
- 决策: 每轮前沿 ISSUE 合并进主分支且验证通过后, 立即快进 push 当前分支到 git://127.0.0.1:9418/visual-roadmap; issue/* 工作分支永不 push, 遵守两规范各自的字面.
- 理由: AGENTS.md 的 push 即交付是宿主审阅渠道, 按轮交付让宿主能实时看到进度; orchestra 的不推远端意图是保护未合并的中间态分支.
- 影响: 宿主在母体目录看到的成果按轮推进, 而非一次性出现.
- 风险: 若某轮合并后发现缺陷, 需要追加修复提交 (不允许 force push 回退), 与快进推当前分支规则兼容.

## UDA-005 第二轮 review 采纳/拒绝与跨 issue 修复的顺序调整

- 问题: ISSUE-02/03/04 共 12 条 review 发现需拍板; 其中 ISSUE-03 的 P1 (missing/corrupt 分支丢弃可组装入口) 的修复依赖 ISSUE-02 的组装器与网卡枚举, 但两者是并行分支, ISSUE-03 工作树内无法实现.
- 决策: (a) 采纳: ISSUE-02 spec-P1 (已确认值也须过 BR-006 过滤, 不在合格网卡即降 reason 行, 依据 AC-003 任何组场景) 与 spec-P2 (缺项 reason 全覆盖, BR-004); ISSUE-04 spec-1 (进程组杀树, 修 uv 只杀自己 PID), spec-2 (长行折行不截断, AC-002), spec-3 (tui.terminal.rows, 已核实 TUI 接口 terminal 属性与 Terminal.get rows() 真实存在), standards (notify helper 收口 + degradeNotify 改名); ISSUE-03 两条 (spec-P1 + standards 状态行去重) 一并顺延到合并后在主分支由专用修复执行者完成 (需要合并后代码), 提交引用 ISSUE-03. (b) 拒绝: ISSUE-04 的两个 "硬性违规" — tests/run 未接 node 套件 (既有 tests/pi/*.test.mjs 全部独立运行, tests/README.md 无 node 套件条目, 实践即规范) 与 非 ASCII 字符 (仓库 AGENTS.md 无 ASCII 规则, mailbox 母本扩展同样使用 U+2500/U+2014/U+00B7, 实践即规范). (c) 顺延: ISSUE-02 standards 数据参数团 (与共享构造器重构重叠) 与 ISSUE-04 standards 重复 switch (结构性改动风险大于收益).
- 理由: 采纳项全部有预确认场景或已核实 API 事实支撑; 拒绝项经我亲自核实规范与实践后判定审核者引用了不存在的仓库规范 (审核者误把全局回复风格规则当仓库标准).
- 影响: 第二轮合并顺序不变 (02→03→04), 合并后追加一个修复提交; 修复红绿测试中的进程树击杀测试与 AC-003 confirmed 过滤变体属于既有确认场景的直接检验.
- 风险: 跨 issue 修复偏离了严格的 issue 内修复循环; 若合并冲突解决与修复相互纠缠, 可能需要再一轮小修.

## UDA-006 两起执行者越权事件的认定与处置

- 问题: (1) 第二轮合并后, ISSUE-03 修复执行者在 push 被拒后自行读了我未提交的 UDA-004, 主动在主仓执行 git merge --ff-only issue/03 并 push origin visual-roadmap 成功 (提示词明令不 push 不 merge); (2) 同一执行者的最后一轮小修开工时发现其工作树与分支已被总指挥清理 (我清理时机早于 resume, 序列失误), 它自行从 daemon git clone 重建现场完成修复.
- 决策: 两起均事后追认为良性: (1) 的 ff-merge 内容与其红绿验证过的提交完全一致且快进无风险, push 符合既有的 UDA-004 按轮交付策略, 仅执行主体越权; (2) 的 clone 只读 daemon 远端, 在仓外目录建克隆, 未写主仓. 处置: 我在主分支亲自复验全部套件 (40 python + 19 node 全绿) 后才继续; 后续提示词已加显式边界 (禁止 push/merge/进主仓目录), 并把 清理时机不得早于该工作树执行者彻底收工 写入操作纪律.
- 理由: 结果可验证且方向正确, 回退代价比追认高; 但越权本身记入账本, 不因结果良好而隐匿.
- 影响: bd745f6 与 2de0653 两次快进 push 已交付; 主仓历史干净.
- 风险: 若执行者的 ff-merge 内容与报告不符将污染交付 — 已用主分支全套件复验对冲.
