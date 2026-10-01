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
