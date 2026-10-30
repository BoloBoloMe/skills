# demo 改名与 PoC 类型落地 Execution Spec

## 权威输入与决策引用
- Product Spec: `PRODUCT.md` (G-001..G-012, BR-001..BR-006, NG-001..NG-004, AC-001..AC-022)
- Technical Spec: `TECHNICAL.md` (模块划分 / 模块接口 / 接缝与依赖 / 安全策略 / 非功能要求)
- 决策引用 (只读, 非意图来源): `../milestone-01/DECISIONS.md` 的 D004, D005, D006, D007, D013; `../milestone-03/DECISIONS.md` 的 D001, D002, D004, D005, D011, D012, D013, D014, D015, D016, D017, D018, D019.

## 评审起点
- 待填

## 全局允许范围
- `workflow/demo/`: 由 `workflow/prototype/` 改名而来, 可改 `SKILL.md`, `LOGIC.md`, `UI.md`.
- `workflow/navigate/`: `SKILL.md`, `TEMPLATES.md`, `scripts/roadmap.py` (只改 `TYPE_VALUES` 一行), `web/index.html` (类型元数据, 图例, 星球外观分派, 配色表), `tests/visual/render_checks.py` (类型清单, 夹具, 新增巡检项), `tests/test_roadmap_validation.py` (只新增枚举用例).
- `README.md`: 工作流技能表 demo 一行.
- 新增 `docs/adr/0024-demo-poc-milestone-types.md`.
- 本目录的 `EXECUTION.md` 与 `issues/`.

## 全局禁止范围
- NG-001: 不加 `prototype` 别名, 不做旧图读取兼容.
- NG-002: 不改历史一手材料: 既有 `docs/changes/<slug>/prototypes/` 产物, 旧格式 `ROADMAP.md`/`MILESTONE-NN.md`, 历史 `prototype/<slug>` 分支名.
- NG-003: 不新建 `poc` skill 目录, 不改三子形态落位规则.
- NG-004: 不运行 `sync-to-pi.py`, 不改已安装 skills 与全局配置, 不宣称安装效果或模型行为已验证.
- 不改 `PRODUCT.md`, `TECHNICAL.md`, `DECISIONS.md`, `workflow/software-engineering-consensus/` 的正文.
- 不改 `roadmap.py` 的命令集 (query/save/delete) 与写入路径语义, 不改 `web_server.py`, 不加状态枚举, 不用 `off_course` 记 PoC 终止.
- 不改 `docs/changes/workflow-stack-review/roadmap/ROADMAP.json` 的内容, 里程碑状态流转归 `drive-execution`.

## 完成定义
- pytest: 先 `uv run python workflow/navigate/scripts/web_server.py stop`, 再 `uv run python workflow/navigate/scripts/web_server.py status` 确认 `alive:false` (展示服务占着默认端口时三个 lifecycle 用例会失败), 然后 `uv run python -m pytest workflow/navigate/tests`; 通过标准 退出码 0 且无 failed. 拆分时基线 27 passed.
- 视觉巡检 (不属 pytest 套件, 不会被 pytest 收集): `uv run --project general/access-web/browse python workflow/navigate/tests/visual/render_checks.py`; 通过标准 退出码 0 且报告 0 项失败. 拆分时实测本容器可用 (playwright 由该项目提供, chromium 已在 `~/.cache/ms-playwright`). 执行时若缺 playwright 或 chromium, 该条降级为人工核对 + 截图 + 读页面代码, 并在交付证据里写明环境缺口, 不得写成已跑.
- 文档机检: 每个改过的 `SKILL.md` 跑 `uv run python general/writing-for-llm/check_skill.py <path>`; 通过标准 输出 OK 且退出码 0.
- 审计: 标 (审计) 的 BR-001..BR-004 按覆盖矩阵的人工核验方式执行, 结论记入 ISSUE-06 完成证据.
- 每轮合并后跑本轮受影响的检查; 提前跑全套的两个节点: ISSUE-01 完成后立即跑完整 pytest (枚举是共享底层, 决定夹具与页面数据类型), ISSUE-04 完成后跑 render_checks 加完整 pytest (网页与巡检脚本同动).
- 全部 issues 集成后跑一次完整检查: pytest, render_checks, 两份 SKILL.md 的 check_skill.
- 不碰生产环境, 不引入外部依赖; 原始输出与截图放仓库外 `/tmp/m9-04-<NN>/` 并默认保留.

## 验证策略
- 变更类型 (按 verification-contract 选定): ISSUE-01 / 03 / 04 行为变更; ISSUE-02 结构变更 + 行为变更; ISSUE-05 非行为改动; ISSUE-06 纯核验.
- 自动化只加两处: ISSUE-01 的三条 pytest 用例 (TC-002 demo 可写入, TC-003 prototype 被拒且文件逐字节不变, TC-005 poc 可写入), ISSUE-04 在 render_checks 新增的一条巡检项 (TC-006). 其余断言用可复跑命令加人工读文件: 交付物本身是文本, 逐条对照 PRODUCT 措辞才是真验证.
- 结构变更的改前基线: ISSUE-02 先留 `grep -rn prototype workflow/ README.md` 快照与三文件目录清单, 改后用相同命令复跑, 只允许预期内的变化.
- 审计项一律人工核验并留脱敏材料 (命令输出, 截图, 读文件结论), 不塞进自动化.
- 未采用自动化测试的 TECHNICAL 不变量: "不含 demo/poc 的既有 ROADMAP.json 照常读取与校验通过" 用 CLI 复跑代替 (查询现网 ROADMAP.json, 在 /tmp 副本上做 save 往返), 因为既有测试已覆盖 schema 机制, 新增用例只会重复枚举字面量; 展示页 "未知类型回退 task" 用人工读代码加页面观察代替, 因为那是单行回退表达式, 没有分支逻辑.

## 任务图
- 宽重构判定: 不适用 `refactor-expand-contract.md`. 理由: 机械改名的爆炸半径只落在仓库内文本与两处模块内部接缝 (`TYPE_VALUES` 常量与校验, `TYPE_META` 与渲染分派), 没有数据迁移, 也没有读取旧名的兼容需求 (NG-001; 全部历史 ROADMAP.json 未用过 `prototype` 类型). 改动在一个 issue 内即可让全套检查保持通过, 因此不设兼容扩展 / 分批迁移 / 收缩清理序列, 也不需要共享 integration branch.
- ISSUE-01: `issues/ISSUE-01-milestone-type-enum.md`; 覆盖: AC-002, AC-003, AC-005, BR-001, AC-016 (TEMPLATES 部分); 依赖: 无.
- ISSUE-02: `issues/ISSUE-02-demo-skill-rename-rewrite.md`; 覆盖: AC-001, AC-004, AC-010, AC-018, AC-019, AC-016 (README 部分), BR-006; 依赖: 无.
- ISSUE-03: `issues/ISSUE-03-navigate-type-vocabulary.md`; 覆盖: AC-007, AC-008, AC-009, AC-011, AC-012, AC-013, AC-016 (navigate 部分), AC-020, AC-021, AC-022, BR-005; 依赖: ISSUE-02.
- ISSUE-04: `issues/ISSUE-04-web-demo-poc-visuals.md`; 覆盖: AC-006, BR-002; 依赖: ISSUE-01.
- ISSUE-05: `issues/ISSUE-05-adr-naming-record.md`; 覆盖: AC-014; 依赖: 无.
- ISSUE-06: `issues/ISSUE-06-regression-and-audit.md`; 覆盖: AC-015, AC-017, BR-003, BR-004, BR-006 复核, 非功能要求 回归检查 / 文档机检 / 不宣称安装效果; 依赖: ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04, ISSUE-05.

## 覆盖矩阵
- AC-001 -> ISSUE-02 -> `ls workflow/demo/` 见 SKILL.md/LOGIC.md/UI.md; `test ! -e workflow/prototype` 成立; `sed -n 1,4p workflow/demo/SKILL.md` 见 `name: demo` 与演示用途 description; check_skill OK.
- AC-002 -> ISSUE-01 -> TC-002; CLI `save <tmp>/r.json milestones.milestone-01.type demo` 退出 0, `query` 得 demo.
- AC-003 -> ISSUE-01 -> TC-003; CLI `save ... type prototype` 退出 1, `error` 里合法值恰为 research, deliberate, demo, poc, task, acceptance; 前后 `md5sum` 相同.
- AC-004 -> ISSUE-02 -> 读 `workflow/demo/LOGIC.md` 与 `UI.md`: 子形态判定顺序 A 到 B 到 C, `demo.` 前缀在 `src/` 宿主页面附近, `/demo/<name>` 路由与 `demo/` 子目录, `docs/changes/<feature-slug>/demos/<demo-name>/`, 变体集进 `demo/<feature-slug>` 分支; 用 `grep -n 'demo\.\|/demo/\|demos/\|demo/<feature-slug>'` 定位逐条核对.
- AC-005 -> ISSUE-01 -> TC-005; CLI `save ... type poc` 退出 0, `query` 得 poc.
- AC-006 -> ISSUE-04 -> TC-006 (render_checks: 图例含 `演示 demo` 与 `实验 PoC`, 画布标注含两者, 元数据与配色两类型互不相同) 加人工截图核对两颗星球一眼可分; 人工入口 `web_server.py start` 后开 `<URL>?roadmap=<夹具绝对路径>`.
- AC-007 -> ISSUE-03 -> 读 `workflow/navigate/SKILL.md` Milestone 种类节 poc 行含 AFK 与代理独立驱动; 完成标准节有 poc 一行; 收口产物节把 poc 产物写成其里程碑里的结论与依据.
- AC-008 -> ISSUE-03 -> 读 demo 条目的何时创建: 含问题是什么样子, 如何运行, 需要让人看清某个样子/行为/过程; 含成品或线上系统演示也归 demo 与不新增交付承诺.
- AC-009 -> ISSUE-03 -> 读 demo 完成标准句与收口产物句: 我看过并能据此判断; 成品演示关闭摘要记一行 (演示了什么, 哪个版本, 产物可为空); `grep -n 'demos/' workflow/navigate/SKILL.md` 无强制留档要求.
- AC-010 -> ISSUE-02 -> 读三文件保留与清理约定: 都写明可留回看, 代理不主动删除, 清理由仓库主人点名; `grep -n '合并主干前由人类清理\|用完即删\|用完即焚' workflow/demo/` 零命中; LOGIC.md 第 5 步原句已换.
- AC-011 -> ISSUE-03 -> 读 poc 条目: 只有何时创建, 完成标准, 收口产物, 终止处置四部分; 指针句指向 `workflow/software-engineering-consensus/SKILL.md` 的 PoC 词条; 无可行/不可行与可复查依据定义复述.
- AC-012 -> ISSUE-03 -> research 何时创建只留 "藏在当前工作目录之外的事实"; `grep -n '无处可查\|须先做实验测出' workflow/navigate/SKILL.md` 零命中.
- AC-013 -> ISSUE-03 -> task 何时创建含 "需要实测才能得出结论, 但结论是描述现状" 的指派与压测/性能基线例子.
- AC-014 -> ISSUE-05 -> 读 `docs/adr/0024-demo-poc-milestone-types.md`: demo 取代 prototype, poc 为新增类型, 旧分支与旧目录按历史证据保留且不做读取兼容.
- AC-015 -> ISSUE-06 -> 先 stop 再 status 确认 `alive:false`, 跑 `uv run python -m pytest workflow/navigate/tests`, 退出 0 且末行全通过.
- AC-016 -> ISSUE-01 / 02 / 03 -> README 行指向 `workflow/demo/SKILL.md` 且用途写演示 (02); `TEMPLATES.md` 枚举行 (01); navigate 的 deliberate 条目写 "无法靠演示提升保真度" 且该条目无 prototype (03).
- AC-017 -> ISSUE-06 -> 对 `workflow/demo/SKILL.md` 与 `workflow/navigate/SKILL.md` 各跑 check_skill.py, 均输出 OK 且退出 0.
- AC-018 -> ISSUE-02 -> 读 `workflow/demo/SKILL.md` 适用范围句: 成品或线上系统演示时不调用本 skill, 直接跑成品; `grep -ni 'poc' workflow/demo/SKILL.md` 零命中.
- AC-019 -> ISSUE-02 -> 读规则 1/5/6: 规则 1 不进产品/不承诺交付/可保留回看; 规则 5 记录演示了什么, 请仓库主人据此判断什么, 材料位置与相关 issue 指针; 规则 6 验证止于能演示; `grep -n '注定被丢弃\|验证止于冒烟' workflow/demo/SKILL.md` 零命中.
- AC-020 -> ISSUE-03 -> 读 poc 条目何时创建: 一个结论能一次收口就一个里程碑, 多个可分别收口的结论才拆并用依赖串, 单结论跨会话保持进行中, 会话规模只作经验; 实质交付产品代码归 task.
- AC-021 -> ISSUE-03 -> 读 poc 终止处置: 未证实默认保持未完成; 只有仓库主人裁决终止才记关闭; 关闭摘要写 "未证实即终止, 不构成可行性结论" 及原因; 按裁决移出终点验收依赖; 不记成歧路.
- AC-022 -> ISSUE-03 -> 读 research 就地查段落: 工作目录内事实就地查, 不单立里程碑; 查影响面用 blast-radius, 查领域用 domain-awareness; 需要单独立项才查得清的内部调查通常说明里程碑划错了.
- BR-001 (审计) -> ISSUE-01 -> 人工核验: 读 `TYPE_VALUES` 单行恰为 research/deliberate/demo/poc/task/acceptance; 跑 AC-002/003/005 三条 CLI 命令, 记录退出码与 stdout JSON; 复核 `git diff workflow/navigate/scripts/roadmap.py` 只动该常量.
- BR-002 (审计) -> ISSUE-04 -> 人工核验: 起服务开 `?roadmap=<含 demo 与 poc 的夹具>`, 截图存档, 逐项确认图例两项文本与两类型星球配色/地貌不同; 自动化侧由 TC-006 提供图例与元数据差异证据.
- BR-003 (审计) -> ISSUE-06 -> 人工核验: `grep -rn prototype workflow/ README.md --include=*.md --include=*.py --include=*.html` 零命中; 对 `docs/changes/` 与 `docs/adr/0024-*` 的命中逐条判定为允许例外 (历史一手材料, 记录旧名由来的 ADR), 判定结论连同命令输出写入完成证据.
- BR-004 (审计) -> ISSUE-06 -> 人工核验: `git status --short` 与 `git diff --stat` 只落在全局允许范围内; `ls ~/.agents/skills | grep -xE 'demo|prototype'` 仍只有 prototype; 全程无 `sync-to-pi.py` 调用记录; 不写任何安装效果或模型行为结论.
- BR-005 -> ISSUE-03 -> 人工核验: poc 条目只写流程语, 交付定义以指针指向 `workflow/software-engineering-consensus/SKILL.md` 的 PoC 词条; 对照该词条正文确认 navigate 侧没有复述可行/不可行结论与可复查依据.
- BR-006 -> ISSUE-02 / ISSUE-06 -> ISSUE-02 三文件清理约定改为点名删除; ISSUE-06 人工核验 `git diff --stat docs/changes` 无删除, `ls docs/changes/less-is-more-palette/prototypes/` 仍在, `git branch --list 'prototype/*'` 与改前一致.
- 非功能要求 回归检查 (`TECHNICAL.md` 非功能要求) -> ISSUE-01 / 04 / 06 -> 各自验证入口的 pytest 与 render_checks 命令, 通过标准 退出码 0 且无 failed/0 项失败.
- 非功能要求 文档机检 -> ISSUE-02 / 03 / 06 -> check_skill.py 对两份改过的 SKILL.md 输出 OK.
- 非功能要求 不宣称安装效果 -> ISSUE-06 -> 完成证据里只写仓库内观察, 不含安装后行为或触发率结论.
- 模块接口不变量 (roadmap.py 命令行) -> ISSUE-01 -> `git diff` 确认命令集与写入路径语义未变; 对现网 `ROADMAP.json` 跑 `query milestones.milestone-04.type` 成功且前后 `md5sum` 相同 (query 不写文件), 在 `/tmp` 副本上 `save notes.0 '"y"'` 往返成功.
- 安全策略 (写入范围限于仓库内文件, 不碰已安装 skills 与全局配置) -> ISSUE-06 -> BR-004 审计: `git status --short` 与 `git diff --stat` 全落在允许范围, `ls ~/.agents/skills` 只读到旧名, 全程无同步调用.
- 模块接口不变量 (展示页元数据覆盖 6 值, 未知类型回退 task) -> ISSUE-04 -> 读 `TYPE_META` 六键齐全; 人工用含未知类型夹具起页面, 该星球按 task 外观渲染且 pageerror 为 0 (回退表达式 `TYPE_META[node.m.type] || TYPE_META.task` 保留).
- 模块接口不变量 (demo SKILL.md frontmatter 与调用方式) -> ISSUE-02 -> check_skill OK; `grep -n 'disable-model-invocation: true' workflow/demo/SKILL.md` 命中; 正文只谈造演示材料.
- 模块接口不变量 (ADR 遵循既有格式) -> ISSUE-05 -> 编号 0024 连续, 标题一行加 1 到 3 句正文, 与 `docs/adr/0023-*.md` 体例一致.

## 全局风险和停止条件
- 需要改变 PRODUCT/TECHNICAL/DECISIONS 时停止.
- 需要扩大允许范围或触碰禁止范围时停止.
- Spec 与代码事实冲突或无法提供完成证据时停止 (例如 AC-011 的指针范围与 AC-021 的默认句在落笔时无法同时满足, 见 ISSUE-03 风险提示).
- 视觉巡检环境缺失时不停工, 按完成定义降级为人工核对并写明缺口.
