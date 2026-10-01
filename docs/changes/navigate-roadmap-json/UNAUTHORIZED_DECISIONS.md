# UNAUTHORIZED_DECISIONS (AFK 模式自主决策记录)

任务: docs/changes/navigate-roadmap-json ISSUE-07 (tdd-as-orchestra 流程, 总指挥 = 主会话).

## D-AFK-1 总指挥预写的测试草稿删除, 由执行者重写
- 问题: 总指挥在用户转入 AFK 前已亲手写了 `workflow/navigate/tests/test_stdlib_only_and_no_external_refs.py` 草稿, 违反 tdd-as-orchestra "总指挥不亲自写代码" 分工.
- 决策: 删除草稿 (rm, 未提交过, 无历史损失), 由执行者子代理按 TC-102 权威输入从零重写.
- 理由: 遵守分工纪律; 测试质量责任归执行者, 便于 review 归因.
- 影响: 无代码损失 (草稿未提交); 执行者多一次编写工作量.
- 风险: 执行者写出的测试质量波动 — 由 code-review 审核环节兜底.

## D-AFK-2 子代理 LLM 选型
- 问题: 用户授权两个子代理 llm: glm-5.3-flash • max 或 deepseek-v4.1-flash-expires-on-0910 • max, 未指定各角色用哪个.
- 决策: 执行者 (impl-07) 用 ai-work-deepseek/deepseek-v4.1-flash-expires-on-0910:max; 审核者用 ai-work-zai/glm-5.3-flash:max.
- 理由: deepseek 在本任务早期 (planet-fix) 已实测表现良好; 审核者换用不同模型形成交叉验证, 降低同模型盲区.
- 影响: 审核者若 glm 输出质量不足, 视为审核降级, 总指挥亲自复核其发现项.
- 风险: glm-5.3-flash 首次在本任务使用, 行为未知; 缓解 = 其结论仅作参考, 不直接决定合并.

## D-AFK-3 ISSUE-07 文中 "load" 操作不存在, 以 D003 为准
- 问题: ISSUE-07 第 1 条写 "守门脚本调用 (load/query/save/delete)", 但 D003 与 roadmap.py 实际只定义 save/query/delete 三个操作.
- 决策: 提示词中向执行者声明: 接口以 D003 与脚本 docstring 为准, "load" 视为笔误 (query 即加载), 不得为此新增脚本操作 (那会越出允许范围).
- 理由: EXECUTION 全局禁止范围禁止改 roadmap.py; D003 是接口权威.
- 影响: SKILL.md 改述只出现 save/query/delete.
- 风险: 若用户本意确要 load (别名), 需后续追补 — 列入待确认.

## D-AFK-4 review 发现项处置
- 问题: 审核者 (glm-5.3-flash) 给出 2 个 minor 发现项.
- 决策: 采纳发现 1 (TEMPLATES.md 补 D006(d) 顶层字段拒绝与 D007 整文档兜底校验说明, 执行者已补, commit ec7bb00); 不采纳发现 2 (测试扩展扫描 CSS url()/JS 字符串外链).
- 理由: 发现 2 的扫描接缝由 ISSUE-07 权威输入钉死为 "src/href 正则扫描", 扩大接缝违反 tdd skill "不在切片里的用例不得进入循环"; 当前 index.html 无此类内容, 无即时风险.
- 影响: 后续若 index.html 引入 canvas 内联外链形态, TC-102 可能漏报.
- 风险: 低; 列入待确认, 用户可授权扩大接缝后由执行者补用例.

## D-AFK-5 全仓快层证据以子集替代
- 问题: 执行者与合并后验证均无法跑完整 `uv run pytest -q` (根 tests/conftest.py 的 pytest_sessionstart 需要 podman, 容器内无 podman, 会话级 INTERNALERROR).
- 决策: 以 `general/present/tests + workflow/navigate/tests` 子集替代, 并在基线 (合并前 e8b4fd2) 复跑确认 test_browser_session.py 的 5 个失败预先存在 (环境相关, 与 ISSUE-07 无关).
- 理由: ISSUE-07 完成定义要求 "全仓库既有测试不回归", 子集覆盖了本次改动相邻面; 基线对照排除了回归嫌疑.
- 影响: 全仓其余 tests/ 目录未在本次循环中复验.
- 风险: 低 (diff 仅 3 个 navigate 文件, 不触其他目录).

## D-AFK-6 ISSUE-07 勾选与验收标准勾选
- 问题: ISSUE-07 结尾要求 "最终审阅由用户 (验收含 LLM 可执行性检查)", AFK 下用户不在场.
- 决策: 勾选 ISSUE-07 的 [x] 已实现与 4 条验收标准 — 依据 = 执行者自证 + 审核者逐项复核通过 + 自动化证据 (27 passed, grep 走查); 用户终审列为待确认项.
- 理由: 实现与审核证据链完整, 勾选动作可逆; AFK 授权覆盖流程性拍板.
- 影响: 若用户终审推翻某项, 需回滚勾选并重开 ISSUE.
- 风险: 低.

## D-AFK-7 UNAUTHORIZED_DECISIONS.md 纳入提交
- 问题: 本文件属 AFK 决策档案, 未跟踪.
- 决策: 随收口提交一并入库 (docs/changes/navigate-roadmap-json/ 任务目录内, 无敏感信息).
- 理由: AFK skill 要求落盘防记忆清空; 入库使决策可追溯.
- 影响: 仓库多一份过程档案.
- 风险: 无.

## D-AFK-8 背景星闪烁物理化 (用户直接下令的视觉迭代)
- 问题: 用户下令将背景星闪烁改为物理真实 (多频叠加/幅度分层/位置微抖), 此需求不属于任何既有 ISSUE (7 个 ISSUE 已全部闭环).
- 决策: 不立正式 ISSUE (用户直接指令的单文件视觉微调, 相当于 ISSUE-05/06 验收反馈的延续); resume planet-fix 执行 (其上下文含整个页面实现史), 主仓库直接提交, 总指挥独立复核后推送.
- 理由: 用户是任务所有者, 直接下令即为授权; 完整 ISSUE 流程对单文件视觉调优过重.
- 影响: 分支 issue/* 规范未用于此轮; 复核链 = 执行者自证 (render_checks/测试) + 总指挥验证 (JS 语法/27 passed/零外链).
- 风险: 视觉效果未经用户肉眼验收即推送 — 不满意则继续迭代新 commit (历史可回溯).
