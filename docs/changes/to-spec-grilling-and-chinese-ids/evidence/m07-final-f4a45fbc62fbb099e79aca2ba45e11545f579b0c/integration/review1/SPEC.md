# milestone-07 Spec 评审报告 (review1)

- 任务标识: m07-rev-spec; 回信地址: 01a21b35-1a38-779a-b0e7-7a28184df3ec.
- 评审方向: Spec 符合性 (a 缺失/不完整, b 范围蔓延, c 实现方式有误, d 证据与契约不符), 并承担 EXECUTION.md 完成定义第 3 项 (三切片合并后的跨文件集成核对) 与 README 非作者复核.
- 独立性: 未参与本变更的规格, 拆分, 实施, 条文化与集成; 只读评审, 未改仓库任何文件, 未提交, 未推送. 本报告写在仓库外证据根.
- 评审起点 `9e8dd1dfe92b3b446c88c2cb8fce33cb0c67a77a`; 实际核对 HEAD `1e3c9844c6f2aea8df7135214c5225fcc2d3d766`.

## 0. 结论摘要

- 发现总数 8 条: 产品条文 3 条 (F1, F2, F3), 证据/契约 5 条 (F4-F8). 其中"需处理"1 条 (F1), 其余为非阻塞的记录, 措辞或范围问题.
- 未发现代码/脚本实现类缺陷: `ac-draft.py` 与 `check-ac.py` 的改动逐段对照 AC-019 至 AC-024 与 TECHNICAL 脚本约定, 行为与证据一致.
- 未发现阻塞主干流程的缺失: to-spec 盘问即写稿与机械转正, verify-change 按方法盘问与写后独立核对, navigate 阶段衔接与终点验收, 三处语义互不矛盾.
- 最严重问题: F1, AC-041 要求"相关调用说明"与 verify-change 的"按决定变化补问"语义一致, 而 `workflow/navigate/reference/VERIFICATION.md:9` 仍写"判据或方案依据变化须先更新权威输入并重新确认方案", 与同族另外四处"只补问新增或改变的验证决定"方向相反, 该文件也不在 ISSUE-03 的允许范围内.
- 线索结论: Q1 成立 (轻微), Q2 不成立, Q3 方向相反属实但本变更不冲突, Q4 属实但不构成 spec 不符; VERIFICATION.md:9 属实并升级为 F1.

## 1. 已检查范围

### 1.1 评审对象 (候选产品与文档)

| 路径 | 读法 |
| --- | --- |
| `workflow/to-spec/SKILL.md` (90 行) | 全文 |
| `workflow/to-spec/GHERKIN.md`, `TEMPLATES.md` | 全文 + 差异 |
| `workflow/to-spec/ac-draft.py` | `promote`, `preview`, `_existing`, `_atomic_write`, `main` 全文; `workspace`, `_page`, `_reading_view` 读改动片段与调用方 |
| `workflow/to-spec/check-ac.py` | `with_draft`, `extract_gherkin_block`, `extract_entry_texts`, `Violations`, 标记常量与 `main` 退出码 |
| `workflow/to-spec/tests/test_ac_draft.py`, `test_ac_reading.py` | 完整差异 (含删除/新增用例) |
| `workflow/verify-change/SKILL.md` (79 行), `REVERIFY.md` | 全文 + 差异 |
| `workflow/navigate/SKILL.md`, `ACCEPTANCE-GUIDE.md`, `README.md` | 全文 + 差异 |
| `workflow/navigate/reference/VERIFICATION.md`, `VOYAGE.md`, `MAPPING.md`, `TEMPLATES.md` | 全文 (交叉引用与遗留措辞排查) |
| `docs/changes/.../issues/` 三份工单, `EXECUTION.md` | 全文 + 差异 |
| 未改动的 `workflow/deliberate/`, `workflow/decision-ledger/`, `workflow/to-execution/`, `general/*`, `docs/changes/.../{PRODUCT,TECHNICAL,VERIFICATION-PLAN,DECISIONS,roadmap}` | 只读对照, 确认未变 |

### 1.2 规格与依据

- `PRODUCT.md` (SHA256 `c8823e0e…239d5`), `TECHNICAL.md` (`e825dd57…0f1e`), `VERIFICATION-PLAN.md` v3 (`7c4c450f…9583`), `DECISIONS.md` 决策 31-42 及事实 11/12, `EXECUTION.md`, 三份 issue 的验证契约与验证入口.
- `workflow/verification-contract/SKILL.md` 及 `SAFETY.md` (共用底线, 记录证据, 行为变更完成证据).
- 证据: 仓库外 `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/{issue-01,issue-02,issue-03,integration,post-impl-snapshot,pre-impl-snapshot,m07-review-inputs.md}` 与仓库内归档 `docs/changes/.../evidence/m07-1bc15f6…/` (逐项抽查, 见 4.2).

### 1.3 局限

- 未运行候选 skill 或真实需求; 未运行 pytest (由工程检查证据承担, 我复核其结果与原件形态, 未复跑).
- 未审 `docs/changes/.../evidence/` 下 1212 个证据文件的全部内容, 只抽查与结论直接相关者 (ISSUE-01 run5 日志/INDEX/text-mapping, ISSUE-02 check1 报告, ISSUE-03 local-check, integration/run1, 两次安装目录摘要).
- 不判 milestone-08 独立验证结论, 不代用户验收.

## 2. 跨文件集成核对 (EXECUTION 完成定义第 3 项)

逐项结论 (依据为三份候选条文原文, 不是差异摘要):

| 核对项 | 结论 | 依据与说明 |
| --- | --- | --- |
| 术语: 盘问即写稿/机械转正 | 一致 | to-spec SKILL:44-49 (机检与机械落正式), navigate:55, ACCEPTANCE-GUIDE:8, README:50 与 :65 均写"盘问结束即确认内容, 稿件机械转正/复制, 无逐版读稿". |
| 术语: 验证方案确认 | 一致 | verify-change:31-41 (闭环即内容确认), navigate:56, ACCEPTANCE-GUIDE:14, README:65 同义. |
| 确认边界 (规格确认≠方案确认≠验收) | 一致 | to-spec:23, :86; verify-change:8, :31, :33; navigate:42, :75; ACCEPTANCE-GUIDE:16; README:67 均把三者分开, 并禁止反方/检查代用户拍板. |
| 阶段衔接 | 一致 | navigate:70 依赖链 `spec -> verification-plan -> ...`; ACCEPTANCE-GUIDE:14 "先确认权威输入, 再设计验证方案"; verify-change:16 "规格先确认, 不把规格结束确认当作方案确认". |
| 复验与方案修订语义 | 不一致 (F1) | verify-change:43-47, REVERIFY:7, navigate:71, ACCEPTANCE-GUIDE:14, README:67 都是"只补问新增或改变的验证决定"; `navigate/reference/VERIFICATION.md:9` 是"重新确认方案". |
| deliberate 独立四步保留 | 一致 | `git diff 9e8dd1df...HEAD -- workflow/deliberate/` 为空; navigate:41 明确"独立的 deliberate 里程碑照常可用"; to-spec:17 "不整体调用 deliberate"; README:65 保留独立入口. |
| 非 to-spec 调用者入口 | 一致 | ACCEPTANCE-GUIDE:9 保留"不调用 to-spec 时"分支; navigate:41 未删 spec 的替代路径; deliberate 正文未改. |
| 交叉引用可解析 | 通过 | to-spec 的 `SAFETY.md#脱敏`, `GHERKIN.md`, `TEMPLATES.md`, `#达标标准与检查边界`, `#规格约束与停止条件`; verify-change 的 `#执行验证方案`, `#方案修订`, `REVERIFY.md`, `reference/SCENARIO-CHECK.md`; navigate/ACCEPTANCE-GUIDE 的 `SKILL.md#milestone` 全部存在且指向内容相符. |
| 新增执行调用是否都被 README 收录 | 通过 | 新增/保留的执行调用 domain-awareness, codebase-design, grilling, decision-ledger, handoff, opposing-viewpoint, domain-modeling, present, verification-contract, use-herdr, llm-select, benchmark-checklist, blast-radius 均在 README 技能表中. |
| 遗留旧确认语义扫描 | 1 处 (F1) | 全仓 `rg "逐版\|整份采纳\|重新确认"` 只余 `navigate/reference/VERIFICATION.md:9`. |

## 3. README 非作者复核记录

- 位置: `README.md:32` (调用关系口径), `:41`, `:50-51` (技能表三行), `:65-67` (两段阶段衔接说明).
- 依据: `PRODUCT.md` AC-025/AC-041/规则7/规则11, `TECHNICAL.md` 关键流程 6, plus 实际候选 `to-spec/SKILL.md:17-23,44-49,86`, `verify-change/SKILL.md:8,16,31-47,51-52`, `navigate/SKILL.md:41-42,55-56,71,75`, `ACCEPTANCE-GUIDE.md:5-16`.
- 结论:
  - `:32` 口径 ("调用图只画执行调用, 维护时人工核对 README 技能表与正文执行调用语句, 并经非作者复核") 与实际调用一致; 本次即为该复核.
  - `:41` navigate 行: 罗列"规格确认, 验证方案确认, 实施, 独立验证与终点验收", 与 navigate 的 Milestone 类型和完成标准相符.
  - `:50` to-spec 行: "在规格流程内盘问, 用户明确结束后成文, 产品验收草稿机械转正, 技术稿机械复制, 检查通过后交付" 与 to-spec:23, :37-49, :80-86 逐项对应, 无超出或遗漏.
  - `:51` verify-change 行: "按验证方法盘问, 用户明确结束后成文并独立检查; 成品实施后按方案独立验证" 与 verify-change:24-41, :51-71 对应.
  - `:65` 段: "不要求用户逐版审阅预写规格或成文 Gherkin" (AC-025), "`deliberate` 仍可独立调用" (非目标2/决策1), "已有足够且已确认的权威输入后才调用设计方式" (AC-040), "明确结束方案盘问即确认方案内容, 无需通读并采纳整份成文方案" (AC-032) 全部有出处.
  - `:67` 段: "执行/复验前核实当前内容与来源仍适用, 只补问新增或改变的验证决定, 转述错误直接修正并独立复查, 修订递增版本并保留确认依据, 新轮绑定目标提交与方案修订号" 与 AC-036 两条场景与 REVERIFY 一致; "规格确认, 方案确认, 代理检查与独立验证报告都不是验收" 与 AC-040/navigate:75 一致.
  - 未见把本变更专属人工作业 (用户审改等待) 写进 README 的泛化要求, 与决策 42 边界一致.
- 未覆盖范围: README `:1-31`, `:33-40`, `:42-49`, `:52-64` 与本次无关, 未逐句复核; `general/*` 各技能正文的执行调用语句未逐条复核 (只按新增调用集合反查 README 收录); 未验证模型实际执行 README 描述的能力.

## 4. 全部发现

严重度: 需处理 / 记录问题 / 观察. 除 F1 外均不影响主干流程正确性.

### F1 [类型 a, 需处理] AC-041 覆盖不全: navigate 的验证分支文档仍是旧"重新确认方案"措辞

- Spec 原文: `PRODUCT.md:427-431` (AC-041) "当 核查 navigate, README 及相关调用说明中验证方案完成标准和复验确认的表述 / 那么 说明与 verify-change 的盘问确认内容, 按决定变化补问及保留版本追溯的语义一致 / 而且 说明不再把阅读预写方案并采纳整份文件作为必要确认方式". `TECHNICAL.md` 关键流程 6 同向要求"verify-change 执行入口/REVERIFY 的重新确认说明同步为只补问变化决定". `EXECUTION.md` 完成定义要求三切片合并后"交叉核对调用关系,确认语义和相互引用"一致.
- 候选位置: `workflow/navigate/reference/VERIFICATION.md:9` (本次未改, `git diff 9e8dd1df...HEAD` 对该文件无输出): "…只有方法变化不改产品判据, 判据或方案依据变化须先更新权威输入并重新确认方案."
- 对照同族四处: `verify-change/SKILL.md:51` "先回设计方式按 方案修订 分流…只为新增或改变的验证决定补问; 不改产品判据, 不逐版重读采纳"; `verify-change/REVERIFY.md:7` "只补问新增或改变的验证决定, 不重新阅读采纳整份方案"; `navigate/SKILL.md:71` "不再适用时先回到 verify-change 的设计方式更新方案: 只补问新增或改变的验证决定…"; `ACCEPTANCE-GUIDE.md:14` 与 `README.md:67` 同.
- 后果: 走 navigate 的 verification 分支时, 读到的是对整份方案的"重新确认", 与 verify-change 方案修订的"只补问变化决定, 不整份采纳"方向相反; 这正是 AC-041 要消除的旧语义; 并使"完成定义"的"相互引用一致"无法成立.
- 范围问题 (第二层): ISSUE-03 允许范围只写 `workflow/navigate/SKILL.md`, `ACCEPTANCE-GUIDE.md`, 根 `README.md`; 其验证入口 2 也只核这三处. 所以按现行授权, 该文件既未被改也未被核对, AC-041 的"相关调用说明"实际无法在授权内满足.
- 建议处理 (不代裁决): 由调用方在 milestone-12/13 或返工时扩大该文件到 ISSUE-03 范围并按"只补问变化"改写 :9, 并补该 issue 的核对记录; 或在 EXECUTION 授权范围里显式排除并说明 AC-041 只覆盖三文件, 同时修正 AC-041 承接口径.

### F2 [类型 a, 记录问题] AC-036 第三条: "不新增盘问专用记录格式"未写进"方案修订"段

- Spec 原文: `PRODUCT.md:366-371` (AC-036) 第三条 "而且 条文沿用现有来源引用与检查产物组织依据, 不新增盘问专用记录格式".
- 候选位置: `workflow/verify-change/SKILL.md:43-47` (§方案修订): "每次内容修订递增方案版本, 用现有来源引用和检查产物保留变更及确认依据…版本号, 确认状态或通知不证明内容已获确认." 只承接前半 (沿用现有来源引用与检查产物), 未写后半个禁令. 该禁令只出现在 `:28` (§设计验证方案第 2 步, 讲盘问记录): "不新增盘问专用文件, 章节或格式."
- 判断: AC-036 的核查对象是"VERIFICATION-PLAN.md 修订的规定", 修订段自身没写该禁令; 若要求修订规则自含, 属承接不完整; 现有两段合成后行为无歧义, 故不阻塞. 与线索 Q1 一致.
- 建议: 在 :47 补一句"不新增盘问专用记录格式", 或在 ISSUE-02 证据里登记"由 :28 承接"的判定.

### F3 [类型 b, 记录问题] verify-change 复验会话与工具选择的收紧被放宽, spec 未要求

- Spec: AC-031 至 AC-041 与规则 16-22 只约束验证方案盘问, 检查会话独立性与修订分流; 没有任何条目要求改变"执行方式"的会话新开规则或工具选择规则. `VERIFICATION-PLAN.md:178` 前提 3 反而写"每轮独立验证使用本轮新开且未参与实现/修复的会话".
- 候选位置 (对照基线 `9e8dd1df`):
  - `verify-change/SKILL.md:60`: 基线"每名验证者使用本轮新开的子会话" → 现"首轮使用本轮新开的子会话; 复验按 复验规则 决定新开或恢复".
  - `verify-change/SKILL.md:62`: 基线"启动时调用 `use-herdr` skill 并读取其 `launch.md`" → 现"启动时使用已确认的会话工具; 没有另定工具时, 调用 `use-herdr` skill".
  - `REVERIFY.md:5`: 基线"原指挥与验证者会话可由调用方安排恢复或新开" → 现"当前确认方案要求新开会话时照办; 否则…恢复或新开".
- 判断: 这三条把"每轮新开"的通用默认改成"方案未要求就允许恢复旧会话", 并让会话工具可替换; 它确实消解了旧文内部的矛盾, 且本变更通过"照办"条款仍满足方案前提 3, 故不阻塞本变更. 但它不是本次规格要求的改动, 且削弱了通用独立性默认 (只剩"改过产品的必须替换"和非作者要求). 基线 REVERIFY 已允许恢复, 因此风险有限.
- 建议: 由调用方明确保留或回退到"每名验证者本轮新开"; 若保留, 在 EXECUTION 或 issue 里登记该改动的依据.

### F4 [类型 d, 记录问题] ISSUE-02 的交付证据与验收标准未回填归档的非作者报告

- Issue 契约: `ISSUE-02` 交付证据要求"填写…所有覆盖行的来源与条文位置,每个 AC 场景预期的逐项核对结果,同文件/跨引用矛盾检查…"; 验收标准 5 项含"验收31-验收40及验收41中 verify-change/REVERIFY 部分的全部 normal/failure/edge 场景均有条文位置和逐项核对证据"; `EXECUTION.md` 完成定义"三个 issue 均完成, 各自的变更和证据符合 issue 的验证契约".
- 实际证据: 非作者报告已存在并已归档: `evidence/m07-1bc15f6…/issue-02/check1/CHECKS-ISSUE-02.md` (21 场景 43 条预期, 4 条非阻塞疑点, 结论无阻塞; `finished-at.txt` = 2026-11-27T04:38:52Z, 早于集成提交 `1bc15f6` 的 04:57:27Z). `EXECUTION.md` 执行记录也引用了其结论 ("21 场景 43 条预期无已证实缺陷 (4 条非阻塞疑点)").
- 现状: 工单交付证据仍写"非作者核对已委派独立检查会话…本轮未取得非作者报告: INDEX 逐场景只提供来源和候选定位, 不作通过判断"; 5 项验收标准仍为 `- [ ]`; 集成提交 `1bc15f6` 只改了 `## 执行` 的 `- [x] 已完成`. `m07-review-inputs.md` 登记的"回填待办: CHECKS-ISSUE-02.md 于集成时复制入产物根并回链 ISSUE-02 交付证据节"未执行 (全仓检索无该文件名引用).
- 区分: 检查本身已通过 (无阻塞), 属"没有记录证据/未回链", 不是"检查未通过".
- 违反: verification-contract 共用底线"记录证据 (记录对应要求, 入口操作与输入, 预期与实际结果…可复查的脱敏原始材料)"; 以及本 issue 自己的验收标准.
- 建议: 在 ISSUE-02 交付证据补 check1 路径与结论, 勾选 5 项验收标准, 并逐条裁决 4 个疑点 (本报告第 5 节给出独立结论).

### F5 [类型 d, 记录问题] ISSUE-03 验收标准未勾选, 且其交接项在 EXECUTION 中无回链位

- Issue 契约: `ISSUE-03` 验收标准 5 项, 含"将全局交叉核对及 README 非作者复核明确交接给 EXECUTION.md"; 交付证据写"结果回链 `../EXECUTION.md#执行记录`". `EXECUTION.md` 完成定义要求该复核"留位置,依据,结论和未覆盖范围".
- 实际证据: `issue-03/run1/{INDEX,local-check.md,check_skill.log,scope.log}` 齐备, 局部核对 (验收25 两场景, 验收41 三文件部分, 规则11) 有逐项表格; 交接事项已在 `local-check.md` 和交付证据写明.
- 现状: 5 项验收标准全为 `- [ ]`; `## 执行` 已由 `1bc15f6` 勾成 `- [x] 已完成`; `EXECUTION.md` 执行记录没有为"跨文件语义核对 + README 非作者复核"留结果位 (只有门槛判定行提到 `IMPACT-REVIEW.md`).
- 区分: 局部核对通过, 缺的是记录回填与回链位, 不是检查失败.
- 建议: 勾选并补回链 (本报告即为该复核结果, 可回链本文件).

### F6 [类型 d, 记录问题] 实施前安装目录摘要缺取得时间/命令/取得者记录, 未按完成定义列缺口

- Spec: `EXECUTION.md` 完成定义"安装目录只读摘要分两次留证: 调度方须在首轮任何产品修改前安排取得实施前摘要; 实施后摘要由全切片集成检查补取, 与实施前范围和时间对应. 未能追溯的历史时段如实列缺口, 不假定已观察或未变化"; 风险节同.
- 实际证据: `pre-impl-snapshot/` 只有 `skills-manifest.sha256` (231 行), 无 `taken-at.txt`, 无命令记录 (实施后有 `post-impl-snapshot/taken-at.txt` = 2026-11-27T04:58:27Z 与命令). `post-impl-snapshot/COMPARE.md` 只声称"实施前…调度方在首轮产品修改前取得", 无原件支撑该时点.
- 可用间接事实: 文件 mtime 2026-11-27 04:15Z, 早于首条产品提交 `70ae157` (04:30:38Z) 与 `b260081` (04:31:55Z), 数据本身可信.
- 判断: 缺少"时间对应"的登记与命令原件, 且未按完成定义把该时段列为缺口; 属记录不完备, 不是摘要内容错误 (COMPARE.md 的归一化比对与 `normalized-diff.txt` 0 行可复核).
- 建议: 补记 pre 摘要的取得时间/命令/取得者, 或明确写"取得时点无原件记录, 以文件 mtime 与首条产品提交先后作旁证, 该时段未独立观察".

### F7 [类型 d, 记录问题] ISSUE-01 的条文对照表引用 run4 原件, 但 INDEX 声明 run5 为结论依据

- Issue 契约: 交付证据"绑定最终提交的复跑见 run5/…(final-pytest)"; "run5 (8ce78be 最终绑定轮, 全部结论依据)"; 证据"原件 `run5/logs/<name>`".
- 实际证据: `run5/text-mapping.md` 表头写"对象提交 fd26618", 多行证据列写 `run4 CLI`, `run4 trace`, `run4 logs/target-ac-*` 等; `run5/logs/` 确有同名 `target-ac-*`(32 文件) 与 `trace-*`(24 文件), 内容抽查与预期一致.
- 判断: 数据存在且可复核, 但"结论依据"与"引用路径"不一致, 读者无法从对照表判定每行的原件是 run4 还是 run5; 属引用层不一致 (低).
- 建议: 在 `text-mapping.md` 或 `run5/INDEX` 注明"run5 与 run4 同名原件同值复跑"的对应关系, 或把表中 run4 引用改为 run5.

### F8 [类型 b, 观察] verify-change 执行步 1 新增"整轮前置条件"检查

- 候选位置: `verify-change/SKILL.md:52` "开始前核对方案规定的整轮前置条件, 如尚待用户明确通知完成其环节, 停下报告, 不从状态或版本推断已完成."
- Spec: 决策 42 "不将本变更的人工作业扩成所有 verify-change 调用都必须新增的通用产品规则"; AC-031 至 AC-041 未要求该句.
- 判断: 该句以"方案规定"为准, 未把本次用户审改环节硬编码成通用步骤, 与决策 42 边界不冲突; 但它是新增的通用检查语句, 建议在 issue/EXECUTION 里登记"由方案前提驱动"的依据, 以免被读成通用强制人工节点. 判为观察, 不算缺陷.

## 5. 待验证线索核对结论 (独立核对, 不作通过依据)

| 线索 | 来源 | 独立核对 | 结论 |
| --- | --- | --- | --- |
| Q1 修订段是否补禁令 | `m07-review-inputs.md` (源自 check1 CHECKS:Q1) | `verify-change/SKILL.md:43-47` 只写"用现有来源引用和检查产物保留变更及确认依据", 禁令在 `:28` | 成立 (轻微), 见 F2 |
| Q2 规则10 领域语言/ADR 维护承接 | 同上 Q2, `PRODUCT.md:38` | to-spec `SKILL.md:22` 末句"领域术语或 ADR 需要维护时另按 `domain-modeling` 既有规则处理"已承接; verify-change 未提 domain-modeling, 但旧文亦无, 且其设计流程不产生领域维护需求, 规则10 是"仍遵循各自技能"型审计 | 不成立 (无缺口); 建议在集成记录写一句"verify-change 不涉及领域维护, 规则10 由 to-spec 与既有技能承接" |
| Q3 REVERIFY:5 与方案前提方向 | 同上 Q3, `VERIFICATION-PLAN.md:178` | `REVERIFY.md:5` 用"当前确认方案要求新开会话时照办"把方案优先; 本变更方案前提 3 要求每轮新开, 故本变更合规; 但通用默认由"每轮新开"变为"可恢复" | 方向相反属实, 对本变更不冲突; 属 F3 的一部分 |
| Q4 术语统一 ("设计方式") | 同上 Q4 | `verify-change/SKILL.md:45,51,79`, `README.md:65`, `navigate/SKILL.md:41,56,71` 使用"设计方式"/"设计验证方案方式", 而 `:11-12` 的两种调用方式名为"设计验证方案"/"执行验证方案", 正文未定义"设计方式" | 属实; 无 AC 要求统一术语, 不构成 spec 不符, 判为可读性观察 (建议在 :11 定义处补"设计方式"/"执行方式"作为简称) |
| VERIFICATION.md:9 来源变化措辞 | 同上集成待办 | 见 F1 | 属实且需处理 |

## 6. 复核通过的主要项 (无发现的范围)

- AC-001 至 AC-018, AC-026 至 AC-030 (to-spec 条文): 逐条对照 `PRODUCT.md` 原文与 `to-spec/SKILL.md:17-86`, 含同一 AC 号下 normal/failure/edge 分场景; 未发现缺失, 反向, 或把"可选"写成"必须"的表述. 抽样复核了 check1/text-mapping 的判定, 未发现其"通过"结论被夸大.
- AC-019 至 AC-024 (`ac-draft.py`, `check-ac.py`): `promote` 参数已无 `--review`, 校验顺序为"草稿机检→组装候选→正式机检→输入复核→原子替换" (`checker.validate_draft` → `with_draft(confirmed=True)` → `validate_product` → `_inputs` 复核 → `_atomic_write` 内 `_existing(path) != previous` 拦截); `preview` 页面已去掉"待确认/请在 chat 确认/审阅版本", 保留卡片与原文; `with_draft` 把"草稿不得带标记"前置, 对应 AC-024 例 7; 退出码 0/1/2 与 TECHNICAL 一致. `check-tech.py` 未改, 符合"保留既有".
- AC-031 至 AC-040 (verify-change 条文): 逐条对照, 除 F2 外无承接缺失; 覆盖表粒度, 不以方案自证, 首次全量/修订复查, 附条件方案, 输入边界, 通用账本与 handoff 均在 `:24-47` 有对应句.
- AC-025 (navigate/deliberate): 见第 2 节与第 3 节.
- 规则 9/11/12/13/14/15/16-22: 未发现上限表述, 未改历史文件与引用, 未新增服务或依赖, 审计断言归属与证据路径归属与 `TEMPLATES.md` 一致.
- 范围蔓延排查: 除 F3 与 F8 外, 差异内新增条文都能追到具体 AC 或 TECHNICAL 段; 未发现无关重构, 未发现对 `docs/changes/.../{PRODUCT,TECHNICAL,VERIFICATION-PLAN,DECISIONS,roadmap}` 或历史评审/快照的改动 (`git diff --name-only` 全表核对).
- 证据形态抽查: `issue-01/run5` 的 `target-ac-*`, `trace-*`, `target-promote-removed-option`, `final-pytest`(39 passed + 39 subtests, exit 0), `final-check-skill`(OK, 0) 均与 issue 声明一致, 命令/输出/退出码齐全; `integration/run1` 的 pytest/check-skill/审计/归档核对/密钥扫描原件齐备.

## 7. 汇总

- 需处理: F1 (AC-041 相关调用说明仍有旧"重新确认方案"措辞, 且该文件不在 ISSUE-03 授权范围).
- 记录问题: F2, F3, F4, F5, F6, F7 (均为证据回填, 时点登记或措辞问题, 不改变已实现行为).
- 观察: F8; 以及 Q2 (无缺口), Q4 (术语可读性), `GHERKIN.md` 说"固定 v1"而 `check-ac.py` 的 `MARKER_RE` 仍接受 `vN` (TECHNICAL 明确"不额外引入未确认的产品拒绝判据", 故不算缺陷).
- 本报告不构成验收, 不代替 milestone-08 独立验证; 结论只覆盖实际核对的文件与证据.