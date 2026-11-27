## 父级
- `../EXECUTION.md`

## 执行
- [x] 已完成

## 要交付什么
同步 navigate 和仓库根 README 中必要的调用说明, 使规格盘问,验证方案设计和终点验收的通用语义一致. 保留 deliberate 的独立四步和其他调用者的独立入口. 只承接 PRODUCT.md 与 TECHNICAL.md 已确认的通用要求, 不把本变更的专属安排扩成泛用技能规则.

## 覆盖依据
- Product: `PRODUCT.md`, 验收25(@AC-025), 验收41(@AC-041)中 navigate/README 部分, 规则11.
- Technical: `TECHNICAL.md`, 模块划分中的调用说明与编号约定, 模块接口中的盘问与确认/验证方案盘问与成文, 接缝与依赖, 关键流程6.
- 验证依据: `VERIFICATION-PLAN.md` 中验收25和验收41的通用语义预期.

## 相关决策
- `DECISIONS.md`: 决策40, 决策41.

## 允许范围
- `workflow/navigate/SKILL.md`, `workflow/navigate/ACCEPTANCE-GUIDE.md`, 仓库根 `README.md` 中直接涉及本流程的调用说明.

## 禁止范围
- 不改正式规格,决策账本或 `roadmap/ROADMAP.json`.
- 不要求用户逐版阅读预写规格/成文 Gherkin 或整份验证方案, 不将代理检查,方案确认或其他流程通知说成产品验收.
- 不把单一变更的专属人工作业扩成 navigate 或 README 面向所有调用者的强制用户审改步骤.
- 不修改 deliberate 流程或删除非 to-spec 调用者独立使用 deliberate 的能力.

## 代码定位提示
- `workflow/navigate/SKILL.md`: 规格阶段,验证方案阶段,完成标准和用户终点验收入口.
- `workflow/navigate/ACCEPTANCE-GUIDE.md`: 规格与验证方案阶段的通用确认说明和实际验收指引.
- `README.md`: 仓库层面的 navigate/to-spec/verify-change 调用介绍及阶段衔接.

## 验证契约
- 变更类型: 行为变更.
- 对应范围: navigate 用户流程编排,通用确认边界和 README 调用者指引.
- 验证要求/证据: 本 issue 局部只按固定权威规格核对本 issue 修改的条文. 记录候选位置,来源位置,预期与判断. 全局交叉核对和 README 非作者复核是父级集成检查, 本 issue 只交接此待办, 完成和合并不等待集成结果.

## 验证入口
1. 对照 `PRODUCT.md` 验收25的两个场景, 核对 navigate 的规格盘问/转正说明与 deliberate 独立四步及非 to-spec 调用者入口. 两个场景分别对照.
2. 对照验收41的通用要求, 核对本 issue 改动的 navigate,`ACCEPTANCE-GUIDE.md` 和 README 条文是否准确表达规格确认,验证方案确认,执行/复验按变化补问和用户终点验收的关系. 不要求用户逐版读稿或整份阅读采纳方案.
3. 局部检查只使用固定的 `PRODUCT.md`,`TECHNICAL.md` 和 `VERIFICATION-PLAN.md` 作为标准. 本 issue 不依赖 ISSUE-01/02 的实施结果, 也不声称未更新的旧条文已与本 issue 内容一致. 全局交叉核对由 `EXECUTION.md` 在全部切片集成后安排.
4. 本 issue 交付时只记录全局集成检查的待办及其父级引用, 不等待其结果. 合并后由未参与相关文档修改的评审者通读 README 涉及的完整调用段及相邻说明, 对照最终真实的 to-spec,verify-change,navigate 和 acceptance guide 条文, 留位置,依据,结论和未覆盖范围; 实际结果由父级执行记录回链.
5. 对本 issue 修改的每个 `SKILL.md` 执行 `uv run python general/writing-for-llm/check_skill.py <路径>`, 保存完整输出和退出码.

## 交付证据
- 目标: `issue/03` 上包含本节与下列三份实现文件的 `feat: ISSUE-03: 对齐领航与 README 调用说明` 提交. 完整 SHA 见 `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-03/run1/INDEX`.
- 实际改动: `workflow/navigate/SKILL.md:41-42,55-56,71,75` (规格与方案的定义/完成标准, 执行与复验, 验收终点); `workflow/navigate/ACCEPTANCE-GUIDE.md:3,8,12-16` (阅读入口, 验收标准与方案确认); `README.md:41,50-51,65-67` (技能表与阶段衔接).
- 验收25场景1: `PRODUCT.md:262-266`, `VERIFICATION-PLAN.md:96`, 对照 navigate 的 `:41,55,73-79` 和验收指南的 `:5-10,18-27`. 场景2: `PRODUCT.md:268-272`, `VERIFICATION-PLAN.md:97`, 对照 `workflow/deliberate/SKILL.md:9-18` 四步, navigate `:40-41,52`, `workflow/to-execution/SKILL.md:15` 与 `README.md:45,65` 的独立入口. 四步及既有调用保留.
- 验收41: `PRODUCT.md:427-431`, `TECHNICAL.md:25-36,84`, `VERIFICATION-PLAN.md:124`, 对照以上三文件的方案定义与完成标准/方案确认/执行与复验/验收边界. 入口1-3逐项位置, 预期和判断见同一 run1 的 `local-check.md`; 局部核对通过, 不声明与 ISSUE-01/02 的旧条文一致.
- `uv run python general/writing-for-llm/check_skill.py workflow/navigate/SKILL.md`: OK, 退出码0, 同一 run1 的 `check_skill.log` / `check_skill.exit` 为原件.
- 待办交接: 全局交叉核对及 README 完整调用段与相邻说明的非作者复核, 按 `../EXECUTION.md:36,46,75` 在全部切片集成后执行, 结果回链 `../EXECUTION.md#执行记录`. 本 issue 未执行或等待, 不作为本 issue 合并前置. 未进行成品独立验证或用户验收.
- 记录回填 (m07-rw-06) 核对: `../evidence/m07-1bc15f612c10aa6e68e33587a01cd2de1ede2fe4/issue-03/run1/` 原件齐备 (`INDEX`, `local-check.md`, `candidate.patch`, `check_skill.log`, `check_skill.exit`, `scope.log`, `environment.txt`); `candidate.patch` 与 `git show --format= 70ae157 -- workflow/navigate/SKILL.md workflow/navigate/ACCEPTANCE-GUIDE.md README.md` 逐字节一致 (`cmp` 0); `local-check.md` 6 行覆盖入口1 两场景, 入口2 三行, 入口3 规则11; 固定来源 sha256 与本 `../EXECUTION.md` 一致; 分支起点 `775b5a2` 是评审起点 `9e8dd1d` 的直接后继. 本轮核对原件 `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-06/run1/logs/issue03-run1-binding.*`. 非作者全局交叉核对与 README 复核不在本 issue, 交父级集成记录回链, 本工单不代填结论.

## 风险提示
- navigate 统筹多个阶段. 将方案确认写成产品验收会错误放行流程.
- README 的简写可能与技能正文的通用确认语义冲突. 集成时须核对完整调用段和相邻说明, 但只改本任务必要内容.

## 停止条件
同全局; 若发现 navigate/README 与权威输入冲突, 不自行改变规格或路线图, 记录具体段落并交回既有规格/决定流程. 不新增权威输入未要求的强制审改或阶段条件.

## 验收标准
- [x] 验收25两个场景及验收41中本 issue 覆盖部分均有固定来源和候选条文位置. (`../evidence/m07-1bc15f612c10aa6e68e33587a01cd2de1ede2fe4/issue-03/run1/local-check.md` 入口1 两行与入口2 三行, 每行给 `PRODUCT.md`/`TECHNICAL.md`/`VERIFICATION-PLAN.md` 行号与候选位置)
- [x] 本 issue 修改的 navigate 和 README 通用语义符合已确认规格, 不含本次执行专属安排或新增普遍强制条件. (`local-check.md` 各行判断局部符合, 含入口2 验收边界一行; 固定来源 sha256 见 `scope.log`, 与本 EXECUTION.md 一致)
- [x] deliberate 的独立四步与其他调用入口保留, 无 to-spec 新流程反向覆盖. (`local-check.md` 入口1 场景2: `workflow/deliberate/SKILL.md:9-18` 四步无差异, `workflow/to-execution/SKILL.md:15` 调用未改, README 保留独立入口; `scope.log` 产品差异仅 3 文件)
- [x] 本 issue 的局部修改和依据核对留证, 并将全局交叉核对及 README 非作者复核明确交接给 `EXECUTION.md`; 不要求合并前取得全局结果. (`local-check.md` 待交接节, 本工单待办交接条, `EXECUTION.md` 完成定义; 全局结果交父级回链, 本工单不代填)
- [x] 所有改动 skill 的格式检查留有可复查证据. (`../evidence/m07-1bc15f612c10aa6e68e33587a01cd2de1ede2fe4/issue-03/run1/check_skill.log` 为 `workflow/navigate/SKILL.md: OK`, `check_skill.exit` 为 0; 本轮复核原件 `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-06/run1/logs/issue03-run1-binding.*`)

## 被阻塞于
- 无
