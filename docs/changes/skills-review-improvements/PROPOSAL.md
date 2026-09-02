# 提案: skills 仓库审查改进提案

- 日期: 2026-08-23
- 状态: 提案待审 (未决策)
- 审查范围: `general/` 与 `workflow/` 全部 SKILL.md 及附属文档 (30 个 skill), `deprecated/` 归档项, `docs/` (adr/changes/handoff), `pi/` 配置, `sync-to-pi.py` 与 `tests/`, `README.md`/`AGENTS.md`
- 审查方法: 通读全部 skill 正文与附属文档, 机械校验 (frontmatter name 与目录名一致性, 相对链接完整性, skill 互相引用可达性, 测试运行), 交叉核对文档间引用 (docs/changes, docs/handoff, pi 配置), git 历史沿革

> 改名注解 (2026-09-02): 文中 `to-product-spec` 与 `to-technical-spec` 即现行 `to-spec` (`workflow/to-spec/`), `to-execution-spec` 即现行 `to-execution` (`workflow/to-execution/`); 决策见 `docs/changes/spec-skills-merge/DECISIONS.md`.

## 总体评价

审查目标达成度整体高, 先记录查无问题的项, 避免凑数:

- frontmatter `name` 与目录名全部一致 (30/30), 无按名字抵达断链风险.
- 相对链接完整性极好: 全部 skill 内部引用 (SKILL.md -> 附属文档, 附属文档 -> 附属文档) 无真实断链 (扫描到的 5 处伪断链 2 处是代码行号误识别, 3 处是 UBIQUITOUS_LANGUAGE_FORMAT.md 展示目录结构用的示例路径, 均可接受).
- skill 互相引用全部可达: 12 个被 `调用 x skill` 固定句式引用的 skill 全部存在于当前仓库, 无悬空 skill 引用 (deprecated/ 除外, 见 发现 4).
- 指南质量整体优秀: 步骤均带可检查的完成标准, 边界/反模式齐全, 语言统一遵循 writing-for-llm 的写作纪律 (紧凑, 完成标准, 强度词).
- 无生成物污染: 仓库 git 状态干净, .gitignore 覆盖 .venv/pytest_cache/egg-info/uv.lock.

以下发现按严重度排列. 每条含 现象与证据 / 影响 / 建议改法 / 优先级.

---

## 发现 1 (严重): sync-to-pi.py 测试会清空真实 `~/.agents/skills`, 且当前测试红态

**现象与证据**: `sync-to-pi.py` L367 `skills_dir = Path.home() / ".agents" / "skills"` 是硬编码的真实用户目录; `main()` 中用户回答确认即执行 `_clear_skills(skills_dir)` (L437-452). `tests/test_sync_to_pi.py` 构造的旧 skill 放在临时目录 `pi_dir = Path(tmp) / "agent"` (L28-29, L38-39), 只 mock 了 `detect_pi_dir`, 未隔离 `Path.home()`. `test_clear_only_runs_after_final_confirmation` (L36-45) 的输入序列末尾是 `"y"` (确认执行), 于是测试真实清空了 `~/.agents/skills`. 本审查运行 `uv run python -m pytest tests/ -q` 后 `~/.agents/skills` 已为空 (目录存在但 0 项), **副作用已经实际发生** (仓库 git 状态不受影响).

**影响**: (a) 在任何机器上跑这套测试都会删除用户真实安装的 agent skills, 是数据破坏级缺陷; (b) 该测试当前就是红态: `tests/test_sync_to_pi.py:44` `AssertionError` (它断言 tmp `pi_dir/skills` 被清空, 而实现清的是 home 下真实目录, 断言位置错配); (c) `test_final_rejection_keeps_old_skills` (L26-34) 断言 `pi_dir/skills/old-skill` 仍在, 但实现根本不触碰该目录, 该测试是假阳性, 对拒绝路径零保护.

**建议改法**: 测试内 mock `Path.home()` (patch `pathlib.Path.home` 或注入 `skills_dir` 参数), 使清空目标限定在 tmp; 断言改为验证被 mock 的 `_clear_skills` 调用参数, 或直接对 `_clear_skills` 传入 tmp 目录做单测 (已有 `test_clear_removes_all_children_and_preserves_root` 做对了). 修复后本审查造成的空目录需重新运行 `uv run python sync-to-pi.py` 恢复 (见 结论).

**优先级**: 高 (数据破坏 + 红态 + 假阳性三合一)

---

## 发现 2 (高): docs/ 多处对已改名/已删除 skill 与旧路径的悬空引用

**现象与证据**: git 历史确认 `adaptive-presentation` -> `present` (f22847e), `propose` 已被删除. 现存文档仍引用旧名:

- `docs/changes/上下文管理优化/DECISIONS.md` L1 `# 决策账本: propose 上下文窗口优化`; L9/18/27/36 五次写 `预计影响: workflow/propose/SKILL.md` (workflow/ 下无 propose); L25 `委派逻辑写入 workflow/propose/SKILL.md. adaptive-presentation 保持纯展示层`.
- `docs/changes/browser-agent-session-contract/PROPOSAL.md` L7-8/14/66/145 引用 `general/adaptive-presentation/...` (现为 `general/present/`).
- `docs/changes/less-is-more-palette/conclusion.md` L19 `最终方案已写回 general/adaptive-presentation/examples/less-is-more.html` (现为 `general/present/examples/less-is-more.html`).

**影响**: 这些是给 LLM 读的权威文档 (DECISIONS.md 声明"必须遵守"), 引用实际不存在的 skill 路径会让后续会话按旧名寻找文件失败或误判责任方在不到位的模块.

**建议改法**: 最小改动是批量把 `workflow/propose/SKILL.md` 更正为实际承担委派纪律的 `workflow/deliberate/SKILL.md` (或核对 D001-D006 决策归属, 见 DECISIONS.md 待决点), 把 `adaptive-presentation` 更正为 `present`. 历史提案类 (PROPOSAL.md/conclusion.md) 可加一行"当时命名备注"而不追溯修改正文.

**优先级**: 高 (权威文档指错方向)

---

## 发现 3 (高): docs/handoff 必读推荐使用已过时的 skills 绝对路径 `~/.pi/agent/skills/`

**现象与证据**: `docs/handoff/2026-07-19-classification-design.md` L21-22 与 `2026-07-19-ui-design.md` L20-21 写 `~/.pi/agent/skills/grilling/SKILL.md` / `~/.pi/agent/skills/probe/SKILL.md`. 而 pi skills 实际安装于 `~/.agents/skills/` (sync-to-pi.py L367 硬编码), pi/AGENTS.md 亦约定 `~/.agents/skills/<skill-name>/SKILL.md`.

**影响**: `receive-handoff` skill 要求 agent 按必读推荐逐项读取, 这些旧路径按名读文件会失败; 也反映"skills 安装位置"这一环境事实在仓库内有两个说法.

**建议改法**: handoff 文档本就不该写死的绝对路径 (环境相关的指针应收敛为相对仓库约定或路径解析规则); 至少把两处 handoff 的 bug 必读推荐改为 `~/.agents/skills/`. 同时建议在 README 或 AGENTS.md 单一真相源写明 skills 安装位置, 消除两套路径并存.

**优先级**: 高 (功能性断链)

---

## 发现 4 (高): deprecated/ 无归档元数据, 归档项内部悬空引用, 教训未沉淀

**现象与证据**: `deprecated/` 下 9 个归档项无统一归档说明 (无 README 记录归档时间/原因/替代品). `deprecated/orchestrate/SKILL.md` 引用已不在仓库的 `propose`, `setup-workspace`, `adaptive-presentation`, `zoom-out`, `code-review-with-me`, `explore-repo` 等; 其中 `setup-workspace` 甚至从未存在于当前仓库. `deprecated/write-a-skill` 已被 general/writing-for-llm 取代, `deprecated/code-review-with-me` 被 workflow/code-review 取代, 替代关系只可从 git 历史推断.

**影响**: 归档项既无法指导"为什么不用它", 也无法指引"改用哪个"; 巨型归档 (hitl/human-in-the-loop: 19 个 scripts + 12 个 references, 架构复杂度远超现行 diagnosing-bugs 的轻量模板) 的失败经验完全不可见, 重建同类内容时可能重蹈覆辙 (过度脚本化). deprecated/ 内容同步时被排除在 sync 之外, 归档残留只会继续制造引用噪音.

**建议改法**: 在 deprecated/ 下加 `README.md`, 每项一行: 归档日期, 归档原因 (一句话), 替代去向 (无替代写"无"). 对 orchestrate 等引用悬空项的, 在 README 注明"其引用的 skill 大多已删, 仅作历史参考". 可选: 把 hitl 归档教训写一条到 writing-for-llm 或诊断类 skill 的参考 (过度脚本化反模式), 以 writing-for-llm 已有"过度脚本化"概念承接.

**优先级**: 高 (成本低, 收益直接)

---

## 发现 5 (中-高): present 对 access-web 的跨 skill 代码依赖与运行时环境假设未声明

**现象与证据**: `general/present/scripts/browser_session.py` L46 `access_web_browse = script_dir.parent.parent / "access-web" / "browse"` 靠 sibling 目录猜测定位 browser_agent 源码并注入 sys.path (L54-62); 两个 skill 各自独立 pyproject (present 无 pyproject, access-web/browse 有, playwright>=1.40), 无版本契约. SKILL.md 的调用形式是 `uv run python <helper> open ...`, 对运行环境前置 (playwright 可 import, Chromium 二进制已安装) 零声明. 实测: `uv run python -c "import playwright"` 在无 pyproject 目录下行为取决于 uv 版本与系统 site-packages (普通模式可用, `--isolated` 模式 ModuleNotFoundError), 行为不确定. 且 `sync-to-pi.py` 的 `_SYNC_IGNORE` 忽略 `.venv`/`uv.lock`/`tests`, 同步到目标机后 access-web 是裸代码, 首次调用前必须手动 `uv sync` + `uv run python -m playwright install chromium` (数百 MB 二进制), 流程中无任何提醒.

**影响**: 首次在干净环境使用 access-web/present 必然红; 失败时 user 无指引可循; browser_agent 内部重构可静默破坏 present (该风险 browser-agent-session-contract/PROPOSAL.md P1 已识别, 但至今未落地契约化).

**建议改法**: (a) present SKILL.md 或 access-web/SKILL.md 补一节"前置安装: uv sync + playwright install chromium"及首次失败自查路径; (b) PI/落地侧给 sync-to-pi.py 增加"首次使用提示"或 post-sync 自检清单; (c) 推进 browser-agent-session-contract/PROPOSAL.md 已提的 `__init__.py` 导出契约 (get_session/evaluate_js cwd/start 参数), 把访问面收窄为公开 API.

**优先级**: 高 (确定性运行时前提), 中 (契约化按既有提案推进)

---

## 发现 6 (中): README 目标结构与 docs/changes 实际产物结构两套并存

**现象与证据**: README.md 目标结构是 `changes/<feature-slug>/{PRODUCT,TECHNICAL,EXECUTION,DECISIONS}.md + issues/`; 实际 `docs/changes/` 下产物形态是 PROPOSAL.md (browser-agent-session-contract), conclusion.md + prototypes/ (less-is-more-palette), BACKLOG.md + ITEM-*.md + DECISIONS.md (pi-token-stats), 以及非 kebab-case 中文目录名 `个人代码风格指南/` (AI_JAVA_CODE_STYLE_GUIDE.md + PERSONAL_CODE_STYLE_FINDINGS.md) 与 `上下文管理优化/` (上下文窗口管理建议.md + DECISIONS.md).

**影响**: 新 contributor/新会话对"变更产物该是什么结构"无所适从; 中文目录名在跨平台/URL/命令行引用时带来风险; README 宣称的结构没有一处实例完全落地.

**建议改法**: 二选一后固化: (1) 把 README 目标结构降级为"变化期目标规范", 在 docs/changes 下加 README 说明各类产物的适用形态 (probe 工作流产物 vs spec 工作流产物), 或 (2) 收紧为单一结构并给出迁移指引. 至少统一目录 slug 命名 (中文 -> kebab-case), 并给 handoff 型/研究型产物一个明确的放置约定 (ITEM-01-findings.md 这类 findings 文件目前无规范).

**优先级**: 中

---

## 发现 7 (中): probe 术语改名 (ADR-0004) 后存量档案未迁移, 出现新旧术语并存

**现象与证据**: ADR-0004 (docs/adr/0004-probe-roadmap-milestone-terminology.md) 把 Backlog/Item 改名 Roadmap/Milestone, 规定 ROADMAP.md/MILESTONE-NN.md 并置于 `docs/changes/<feature-slug>/roadmap` 子目录; 而 `docs/changes/pi-token-stats/` 仍全部用 ITEM-*.md + BACKLOG.md 命名且平铺在 changes/ 根 (TEMPLATES.md 要求 research/deliberate 产物放 `milestone-NN/` 子目录). handoff 文档 (2026-07-19-classification-design.md) 全文沿用 Item 术语.

**影响**: 同一时段产物两套术语并存, 新会话按现行 TEMPLATES 找 ROADMAP.md 会找不到 pi-token-stats 的 BACKLOG.md; ITEM-03/04 的 handoff 用旧词, 术语漂移源扩散.

**建议改法**: 对已关闭/存档的历史 workstream (pi-token-stats 已闭环) 加一行归档注解即可, 不强求重命名文件; 但 ADR-0004 应补一句"存量档案迁移范围", 明示已关闭 workstream 不追溯. 这是 ADR 变更管理的一次演练.

**优先级**: 中

---

## 发现 8 (中): 无路由 skill, workflow 主链入口全压在用户认知负载上

**现象与证据**: deprecated/orchestrate 是唯一路由 skill, 其过时说明在 git 历史 (9c915a2 "orchestrate 技能过时") 但无替代. 当前 19 个用户调用 skill; workflow 主链 (probe -> deliberate -> to-product-spec -> to-technical-spec -> to-execution-spec -> tdd-as-orchestra) 的入口选择依赖用户逐次点名. general/writing-for-llm/SKILL-MECHANICS.md 明确描述了"路由 skill"模式 (用户调用 skill 多到记不住时用一张路由 skill 化解), 仓库内却无实例.

**影响**: 用户必须记住每个 skill 的精确名字 (`to-execution-spec` vs `to-technical-spec` vs `to-product-spec` 三者仅中间词不同, 记忆负担高); skill 之间无"我该从哪个入口开始"的指引.

**建议改法**: 参照 SKILL-MECHANICS 的路由 skill 模式, 新建一个轻量用户调用路由 skill (如 `workflow/spec-flow`), 内容仅一张主链 + 判定条件表, 不承载逻辑, 指向既有 skill; 或在 README/AGENTS.md 补一条"skill 地图"段. 注意避免重蹈 orchestrate 覆辙: 路由 skill 应保持纯指针, 不编排决策.

**优先级**: 中

---

## 发现 9 (中): 测试覆盖不均匀且无统一执行入口

**现象与证据**: 30 个 skill 中仅 `general/present/tests/test_skill_contract.py` 有 skill 契约测试 (校验 frontmatter 与关键指令文本, 脆弱但存在); `general/access-web/browse/tests/` (13 个测试文件) 与 `general/access-web/scrape/tests/test_scrape.py` (1245 行) 覆盖代码, 但全部被 sync 忽略 (合理, 运行时不需要), 且仓库无 CI 配置 (.github/) 也无统一测试任务定义 (无 Makefile/justfile/pyproject 根级配置), 只能靠手动 `uv run python -m pytest`.

**影响**: "skill 契约" (frontmatter 字段, 调用方式, 关键指令) 无机械守护, 改名/改描述回归只能靠人肉; 一旦有人改了 `name:` 或某条指令措辞, 无告警.

**建议改法**: (a) 补一个轻量 `tests/test_skill_contracts.py`, 遍历 general/workflow 所有 SKILL.md, 断言 frontmatter name == 目录名, description 非空, 相对链接存在, 完成标准节点存在等 (本次审查的机械校验可固化为测试); (b) 如仓库引入 CI, 挂接该测试 + tests/test_sync_to_pi.py + present 契约测试.

**优先级**: 中

---

## 发现 10 (低): 文案与命名小瑕疵

**现象与证据**: `general/translate-a-skill/SKILL.md` L3 description `汉化英文 skill, 保持行为语义和低 上下文负载` (术语"上下文负载"前有多余空格); 该 description 是模型调用级, resident 常驻上下文, 值得一次微修.

**影响**: token 浪费 + 排版瑕疵极轻微; 指出的意义在于演示"description 剪枝"纪律在校验环节应可机械检出.

**建议改法**: 删空格; 在 translate-a-skill 自有校验或通用契约测试中加"description 内部无游离空格"类检查 (可选).

**优先级**: 低

---

## 建议落地次序 (供后续 EXECUTION/issues 拆分参考)

1. 立刻: 修复 tests/test_sync_to_pi.py (发现 1) — 数据破坏级, 且当前红态.
2. 一批文档修正: 发现 2/3 (悬空引用, 旧路径) — 纯文本改动, 低风险.
3. deprecated/README.md 归档元数据 (发现 4).
4. 运行时前提声明与契约化推进 (发现 5): 先补文档声明, 契约化走既有提案.
5. 结构对齐与术语修正 (发现 6/7): 约 1 小时工作量.
6. 路由 skill / 契约测试 / 文案 (发现 8/9/10): 视资源.

## 结论

本仓库的 skill 内容质量 (可执行性, 完成标准, 语言纪律) 处于很高水平; 主要风险集中在**外围资产**: 测试的破坏性缺陷 (发现 1), 文档对已删/已改名实体的悬空引用 (发现 2/3/4), 以及运行时环境前提未声明 (发现 5). 这些均不涉及 skill 行为本体, 修复成本低而收益直接 (尤其发现 1 是数据破坏级). 内容层的结构性商榷 (路由缺口, 结构对齐) 值得开单跟踪但非急务.