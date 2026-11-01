# workflow skills 写作审核 (对照 writing-for-llm)

## 0 审核信息

| 项 | 值 |
| --- | --- |
| 评审对象 | `workflow/` 下 25 个 skill 的 `SKILL.md` 与被主文件直接引用的参考文件; 排除 `codebase-map/` |
| 标准 | `general/writing-for-llm/SKILL.md` (含 SKILL-MECHANICS.md) |
| 分支 / 提交 | `refactor-skill-around-verification` @ `436b842`, 工作区干净, 本轮未改任何 skill |
| 完整通读 | 25 个 SKILL.md; domain-awareness 3 篇格式参考, codebase-design 2 篇, to-spec 2 篇, to-execution 2 篇, navigate 2 篇, verify-change 1 篇, maintain-verification-skill 1 篇, code-review 1 篇, benchmark-checklist 1 篇, blast-radius 2 篇, demo 2 篇, improve-codebase-architecture 1 篇 |
| 未通读 | `use-sandbox-worktree/reference/` 12 篇与两个 `PROVENANCE.md` 仅做机械扫描 (标点/路径/否定词/跨文件重复句) 与抽查, 未逐行判读 |
| 未验证 | 未实跑任何 skill, 不评估触发率, 漏触发率, 模型遵从率; 结论只覆盖文本 |

机械检查结果 (可复跑, 见 §6): `check_skill.py` 25/25 通过; 全角标点 0; 绝对路径 0 (use-sandbox 的容器固定路径已声明平台限制); 相对链接与标题锚点 0 断链; "调用 `x` skill" 指向的 skill 目录全部存在; 跨文件同句扫描与 H1 统计见各条发现.

## 1 结论

这套 skill 的骨架是健康的: 137 处 "完成标准" 密集覆盖流程型 skill 的每个步骤, 机械判定普遍交给了脚本 (to-spec 的 ac-draft/check-ac/check-tech, navigate 的 roadmap.py, use-worktree 的 slug/status), 参考材料大多按需披露, 分工边界 (fix-bugs↔verification-contract, maintain↔create 的新会话复跑) 也做到了不互相复述. 按标准逐条审, 没有发现需要推翻结构的重写.

问题集中在四类, 都不是"写得不对", 而是"同一件事说了几遍"或"把该藏的放在最前面":

- 重复 (违反单一真相源): 产物根目录默认值 5 处, 分工模板句 6 处, 授权节与权限边界各 4 处, 若干 skill 内部同义重申.
- 结构不齐: H1 三种用法并存 (无 H1 / 多个 H1 / H1 只有 skill 名), 7 个 skill 把前置段放在 H1 之前.
- 否定式清单: demo/LOGIC 的 6 条反模式全是"不要 X", GHERKIN 的禁忌关键字说了三遍.
- 少量环境绑定的机制细节: 编排命令, worktree 命名, 前端框架用法.

统计: 明确问题 14 条 (F-01 至 F-14), 判断性发现 8 条 (F-15 至 F-22), 返工顺序见 §5.

## 2 明确问题

**F-01 破折号 "—" 共 44 处, 违反仓库半角 ASCII 标点约定.** 4 个 SKILL.md 22 处: `follow-the-money` 11, `domain-modeling` 6, `fix-bugs` 3, `demo` 2 (含 description); 参考文件 22 处: `demo/UI.md` 9, `demo/LOGIC.md` 4, `use-sandbox-worktree/reference/` 的 pull-window 6, ops 1, risks 1, `image/requirements-browser.md` 1, `to-spec/GHERKIN.md` 1. 另有 4 行用全角角括号「」 (orchestration.md, to-execution:62, SAFETY.md:28, verification-contract:14). 仓库 AGENTS.md 要求标点一律半角 ASCII. **已修**: 44 处破折号与 5 对「」全部换成逗号, 冒号, 分号, 括号或 ASCII 引号; 复查后非 ASCII 标点剩 0 (navigate/tests/visual/README.md 的 6 个句号属测试夹具, 未动). 首轮审核只扫了 SKILL.md, 漏掉参考文件, 数量由 22 更正为 44.

**F-02 产物根目录默认值在 5 处各自成文.** 定义在 `software-engineering-consensus:48`; 另 4 处复述: `decision-ledger:11`, `to-execution:25`, `to-spec:8`, `verify-change:16`. 措辞已经分叉 ("默认/约定为/调用方指定/我调用时另行指定/调用上下文确定"). 标准的单一真相源要求改默认只需一处编辑; 现状改一次要动 5 个文件, 且下游会读到 4 种说法. 改法: consensus 保留定义, 其余 4 处改一行指针. **已修**: 4 处改为指向 consensus 的 产物根目录 词条, 定义仍只在 `software-engineering-consensus:48`.

**F-03 两条模板句散落在多个 skill 开头.** "本 skill 可选, 不构成完成标准; 完成标准见 verification-contract" 在 6 个文件第 7 行逐字重复 (codebase-design, deliberate, demo, follow-the-money, improve-codebase-architecture, lazy-dev); "开始前/开始前调用 `domain-awareness` skill 感知领域模型" 的变体散在 12 个文件的 15 处. 分工声明本身有必要 (它阻止 agent 把方法 skill 当验收门槛), 但逐字复制使措辞无法演进, 且占了每个文件的首屏. 改法: 在 consensus 或 verification-contract 写一次"方法 skill 不构成完成标准", 各 skill 只留一句指名自己的入口. **已修**: verification-contract 的 交付边界 节新增"方法 skill 与完成标准"一段, 6 个 skill 改称"本 skill 是方法 skill"; domain-awareness 启动句统一为"开始前, 调用 `domain-awareness` skill 感知当前工作目录的领域模型." (去掉冗余的"只读"), 6 个入口文件现在用同一句.

**F-04 create 与 maintain 两个 skill 的授权节近逐字重复.** `create-verification-skill:33-39` 与 `maintain-verification-skill:44-49` 的正文与完成标准除"配方/维护"两词外一致 (都写"批准前不写配方或建辅助脚本", 完成标准都是"派工单范围一致, 写入与数据保留记录可对照复查. 否则已停在批准之前"). 两者已经有先例: maintain 的"新子会话复跑"明确指向 create 作唯一真相源. 授权节没照此办理. 改法: 只在一个 skill 维护该节, 另一个用指针抵达, 各留本 skill 特有条款. **已修**: maintain 的 写入授权 改指 create 的同名节, 只留维护特有条款与自己的完成标准.

**F-05 navigate 把同一张"类型→关账要求"映射拆在几处.** 类型清单与"何时创建"在 Milestone 节, 各类完成标准在 `navigate:42-50`, 收口产物在 `navigate:118` 的航行第 4 步, poc 条目 (37 行) 内还有第三处同义表述. 验收 Milestone 的领取条件也写了两遍: `navigate:56-57` (验收终点) 与 `navigate:114` (航行第 2 步). 前者是定义, 后者是执行, 但都写成完整规则, 改一处必忘另一处. 改法: 定义留 Milestone 节, 执行步骤只写"按上文各类别的收口产物记录". **已修 (方案 A)**: 收口产物清单移入 Milestone 节, 航行第 4 步只留指针与提交信息; 验收领取条件只在航行第 2 步写动作门槛, 验收终点改为指向它.

**F-06 demo/LOGIC.md 的反模式是 6 条纯否定.** `demo/LOGIC.md:67-72` 依次"不要加测试 / 不要泛化 / 不要引入框架, CDN 或构建步骤 / 不要装修 / 不要把逻辑和渲染混在一起 / 不要把页面外壳交付到生产环境". 其中"不引入框架/CDN/构建"与"逻辑和渲染不混"两条的正向要求正文已经写过 (§2 写死内联 vanilla JS 且逻辑块无 DOM); 其余 4 条是正文没有的判据. 标准指出否定会把被禁行为拉进上下文. 改法: 正向要求已写过的不再以否定形式重述. **已修**: 反模式节改为 3 条正向边界 (只回答一个问题 / 页面为读状态服务 / 讨论材料不是验收件), 删掉与正文重复的框架, DOM, 加测试三条.

**F-07 benchmark 的权限边界说了 4 遍, 其中一遍在参考文件.** `benchmark-checklist:16`, `:55`, `:63` 与 `reference/measurement-branches.md:30` 都在讲"本清单不授予冻结源码写入权限/不自行取权限". 同一约束的第三次重申不增加遵从度, 只增加维护面. 改法: 输入与授权节说一次, 其余行改为"按输入与授权节的权限边界". **已修**: `:55`, `:63` 与 `measurement-branches:30` 均改为指向 输入与授权 节.

**F-08 verify-change 内部大量同义重申.** 同一文件内: 作者自证不能顶替 (第 4 步 48 行, 第 8 步), 环境/权限缺口不算产品缺陷 (第 7 步 82, 89, 94 行三处), 不许用替身或自建服务桩 (第 7 步两处). 该文件 134 行, 是栈里最长的一份; 标准允许长度, 但每行都要"活着且唯一". 改法: 每类规则只在其首次出现的步骤写全, 后续步骤写"按第 N 步". **改判**: 单独微调只省约 3 句; 真正的冗余是第 7, 8 步整段写给验收者的规则占据了指挥者文件. 并入 F-16 一起处理. **已修 (随 F-16)**: 替身与自建服务桩两处合并成一句, 权限与环境缺口只在职责与三类去向各出现一次, 作者材料只按"旧观察"归类一次; 规则的执行部分移入披露文件.

**F-09 GHERKIN 的禁忌关键字说了三遍.** `to-spec/GHERKIN.md` 的 §1 "显式禁令" 列 5 组被禁同义关键字与 2 个非官方关键字, §1 白名单表已能表达同一约束, §2 又给反例代码块, §4 校验项 4 再讲一次; 而真正强制它的是 `check-ac.py` 的白名单. 三处负向表述会让 agent 更容易写出被禁关键字. 改法: 白名单表 + 脚本为准, 正文只留一句"关键字只认上表写法, 变体由机检拒绝". **已修**: §1 的禁令清单改为一段"关键字只认一种写法", 白名单表与 §4 机检项保留.

**F-10 H1 与首屏结构不齐.** 统计: 9 个 SKILL.md 没有 H1 (blast-radius, code-review, deliberate, domain-awareness, explain-diff, fix-bugs, improve-codebase-architecture, navigate, verification-contract); 4 个有多个 H1 (to-execution 5, to-spec 3, verify-change 3, drive-execution 2); 3 个 H1 只写 skill 名 (maintain-verification-skill, use-worktree, use-sandbox-worktree); 其余单 H1. 另有 6 个 skill 把"本 skill 是方法 skill…"前置段放在 H1 之前. 标准的信息层级要求首屏就是 agent 该做的事; H1 缺席或只有名字时, 首屏信息量取决于偶然. 改法: 统一为"一个能说清目的的 H1 + 前置声明放 H1 之后"; 多 H1 的降为 H2. **已修**: 25 个 SKILL.md 现在各有一个目的名 H1 (14 个新增, 3 个改名, 4 个把原 H1 降为 H2), 6 个前置声明移到 H1 之后. decision-ledger 模板代码块内还有一行 H1 形态的标题, 属模板内容, 未动.

**F-11 drive-execution 第 4 步没有完成标准.** 第 1-3 步都有 "完成标准:", `drive-execution:22` 的"检查出缺口时立即停下来向我汇报, 无缺口则按以下规范执行循环"没有; 执行循环内的 10 个节点都有. 同时"发现缺口立即停下汇报"在第 1, 2, 3 步各出现一次. 可把第 4 步并入执行循环的前置句, 或给它一句可判定的完成标准. **已修**: 第 4 步改为过渡句加完成标准 (缺口列清且停, 或前沿全部具备开始条件并进入循环).

**F-12 lazy-dev 的阶梯, 规则, 降级信号大量互指.** "不抽象, 不分层, 不预留扩展点" 出现在决策阶梯第 5 级 (35 行), 实现阶梯第 6 级 (49 行), 降级信号 (78 行); "只有一个实现/只有单点" 在降级信号 81-82 行又出现一次, 而规则节"单点即内联"已经定义判据; 依赖规则在决策阶梯第 7 级, 实现阶梯第 4 级, 验收标准, 降级信号共 4 处. 阶梯本身是好的引导结构, 但"阶梯 + 规则 + 降级信号 + 验收标准"四层各写一遍同一纪律, 读者要自己合并. 改法: 纪律只在规则节定义一次, 降级信号改成对规则节的引用清单. **已修**: 两套阶梯保留原样 (设计阶段与实现阶段各自需要); 降级信号删掉与阶梯/规则重复的 3 条 (只有一个实现, 只有一个调用点, 引入依赖), 7 条减为 5 条, 并把"新增层级"改写成收益条件; 实现阶梯第 4 级的"不新增依赖"与"不引新依赖"合并成一句.

**F-13 code-review 的"完整列出发现"说了 3 遍. 复审改判: 可接受, 不改.** 65, 72 行在各自的 reviewer 任务简述里, 两份简报面向独立上下文, 必须自包含; 96 行是母会话汇总报告的口径, 主体不同. 86 与 107 行分属规则与理由, 各司其职. 首轮把"同一句出现在不同主体"误判为重复.

**F-14 domain-awareness 的两处格式瑕疵.** `ADR-FORMAT.md` 用 `--` 当破折号 ("惰性创建 `docs/adr/` 目录--只在需要第一篇 ADR 时创建"), 与 F-01 同源, 读起来像漏字. `UBIQUITOUS_LANGUAGE_FORMAT.md` 的示例链接 `./contexts/ordering.md` 等 3 个断链是示例占位, 本身可接受, 但若被当真实指针使用会误判; 建议在示例块旁标明"示例路径, 非仓库真实文件". **已修**: `--` 改成冒号; 示例块后加"示例里的 `./contexts/*.md` 是示意路径, 不是本仓库真实文件".

**F-23 三个 description 含未加引号的冒号加空格, 严格 YAML 解析失败.** `benchmark-checklist`, `fix-bugs`, `navigate` 的 description 写成"摘要: 展开"形式; 普通标量里的冒号加空格非法, 严格解析器报 `mapping values are not allowed in this context` (navigate 报 line 2 column 24). 原 `check_skill.py` 只拦模型调用 description 的冒号, 用户调用漏检. **已修**: 三处改成逗号或括号, 仓库内活跃 SKILL.md 全部通过 `yaml.safe_load`; `check_skill.py` 增加普通标量含冒号加空格或冒号结尾的拒绝, `SKILL-MECHANICS.md` 同步说明. `docs/changes/` 下 5 个历史证据夹具仍故意保留坏 frontmatter, 不在修的范围.

## 3 判断性发现

**F-15 navigate 应按调用拆成"制图"与"航行".** 文件 125 行, 原文明确"制图和航行永不同会话进行", 是标准里最干净的调用切口: 两个分支互斥, 各自只需要自己那半 (制图 7 步约 40 行, 航行 7 步约 45 行, 加上未知海域/歧路/Milestone 定义 ~35 行). 拆开后每次加载少约一半, 代价是多一个名字和一次认知选择. 若要保留单文件, 至少把航行步骤移到披露文件. **已修 (方案 B, 我裁决)**: 两半共用约 80 行定义 (未知海域/歧路/Milestone/验收终点/读写纪律/展示服务), 拆成两个 skill 要复制这些定义; 且"有无 ROADMAP.json"已能自动分流, 不必我记两个名字. 故保留单 skill: 制图步骤移入 `reference/MAPPING.md`, 航行步骤移入 `reference/VOYAGE.md`, 主文件 129 行降到 89 行, 每次加载少约 40 行; `tests/test_env_docs.py` 的对应断言同步改指新文件.

**F-16 verify-change 的第 7, 8 步与 code-review 的三份任务简述适合按分支披露.** verify-change 第 7, 8 步的规则本体是给验收者子会话执行的, 指挥者只在核对时用; code-review 的三段 reviewer 任务简述只在派 reviewer 时需要. 两者都是"只有部分分支触及"的材料, 标准建议推到指针后, 主文件留派工契约与完成标准. 顺带解决 F-08 的一部分长度. **已修**: verify-change 第 7 步规则移入 `reference/SCENARIO-CHECK.md`, 第 8 步规则移入 `reference/EVIDENCE.md`, 主文件第 7, 8 步只留派工契约, 判据边界与完成标准 (136 行降到 106 行), 派工单改为交这两份文件的路径; code-review 三段 reviewer 任务简述移入 `references/reviewer-briefs.md`, 主文件第 5 步只留输入清单与指针.

**F-17 证据状态分类没有单一真相源.** 同一条规则在 5 处各自定义: `verify-change` 第 8 步 (观察/旧观察/推断/未运行四类), `navigate/ACCEPTANCE-GUIDE.md` (已观察/推断/未验证), `explain-diff` (已观察/推断/未验证), `blast-radius` (1-5 级证据级别), `benchmark-checklist` (判定词与缺口清单). 四类与五级不是同一套, 但边界重叠, 措辞已分叉. 建议: 在 verification-contract 定义一套"材料类型 + 适用性"最小模型, 其余 4 处指向它, 只留各自特有判据. 这条涉及语义合并, 需先确认再动. **已修 (只对齐措辞, 我裁决)**: 不新建真相源. 以 verify-change 第 8 步的四类材料 (当前观察/引用的旧观察/推断/未运行) 与三档结论 (通过/失败/未验证) 为统一用词, `ACCEPTANCE-GUIDE`, `explain-diff` 按此改写, `blast-radius` 补一句 5 级与四类的映射 (4, 5 级属当前观察, 1 到 3 级属推断), `benchmark-checklist` 判定词明确"无法下结论即未验证". 各处特有判据与梯子保留.

**F-18 少量机制细节绑定环境.** `drive-execution/reference/orchestration.md` 固定了 worktree 目录名, `issue/<NN>` 分支名, `git merge --no-ff`, 并写"所有分支与提交仅存在本地, 不推远端"; `blast-radius/reference/multimodel.md` 内嵌 herdr 命令形态; `demo/UI.md` 依赖前端框架 (router, `process.env.NODE_ENV`, `?variant=`). 标准允许机制细节, 条件是"默认行为确实犯过这个错"且冲突时有出路. 后者三处都有降级 (子形态 C, 单路, 冲突报告), 但没写"现场与本文件冲突时以现场为准"这类元规则, 而本仓库的实际交付走宿主 Git 桥并被要求推送, 与"仅本地"直接冲突. 建议每处补一句冲突裁定. **已修**: `orchestration.md` 的"所有分支与提交仅存在本地"改为"默认只存在本地, 现场要求交付时只快进推当轮分支", 并补"现场与本文件冲突时以现场为准" ; `multimodel.md` 补命令形态以 `use-herdr` 现场说明为准; `demo/UI.md` 补框架写法只是默认示例, 技术栈不同时按现场实现同一效果.

**F-19 domain-awareness 的过程没有完成标准, 末尾 3 个指针没有触发条件.** "判断任务处于哪个阶段"是流程动作, 但没有"探测到什么算够"; 末尾 `REPO-LAYOUT.md` / `UBIQUITOUS_LANGUAGE_FORMAT.md` / `ADR-FORMAT.md` 三行只写"见/读", 没有分支条件 (何时候读布局, 何时只读格式). 它被 12 个 skill 调用, 弱指针会被静默跳过. 建议每条补触发条件 ("仓库有 `docs/language/` 多上下文时读布局"). **已修**: 补完成标准 (阶段已判定; 设计阶段给出约定或领域文档的实际路径并列出术语, 边界与 ADR 位置; 执行阶段指到复用的产物位置或说明为何仍需探测), 三个指针各自加上触发条件.

**F-20 完成标准的强弱不均.** 强样板: `verify-change` 第 1 步 ("清单条数等于场景数与审计 BR 数之和"), `to-spec` 第 3 步 (脚本 `success` 为 true), `benchmark-checklist` 判定节 (判定词 + 四项材料), `fix-bugs` 阶段 1 (五项勾选). 弱项: `domain-awareness` 无完成标准 (见 F-19); `deliberate` 与 `domain-modeling` 的部分标准依赖我在场答复 (这类模糊不可避免, 但可先加一半可查的边界, 如"待我回答的术语已列成清单"); `codebase-design` 纯参考, 未声明它不产出交付物, agent 容易把它当步骤执行. **已修**: `domain-awareness` 补完成标准 (见 F-19); `codebase-design` 声明只提供词汇与判据, 不产出交付物, 也不作为流程步骤执行; `deliberate` 与 `domain-modeling` 各补一句可查边界 (待定的决定与各自选项, 待解析的术语已列成清单).

**F-21 两个模型调用 skill 的 description 混入内容.** `verification-contract` 的 "写代码/拆 issue 前调用, 为变更挑选验证方式" 后半是内容; `software-engineering-consensus` 的 "判断交付物属于 MVP/PoC/demo/迭代, 或需本仓库权威输入与产物根目录约定时调用" 前半是内容. 标准要求模型调用 description 只写何时调用. 两者都是常驻负载, 值得剪. 改法示例: "写代码或拆 issue 前调用" / "交付物定性或引用本仓库约定时调用". **已修**: 两处按此措辞替换, 常驻上下文不再携带内容介绍与 MVP/PoC/demo/迭代 的枚举.

**F-22 硬护栏类否定予以保留, 但有一处重复.** `verification-contract/SAFETY.md` 的"禁止 `--force` 与 `-D` 硬删"是标准允许的硬护栏, 建议保留 (可补正向: "只用 `remove`/`-d`, 让 Git 的脏检查挡路"). `navigate/TEMPLATES.md` 的"llm 禁用 read/write/edit 工具直接触碰 ROADMAP.json"与 `navigate/SKILL.md` 读写纪律的正向表述"一切读写只经守门脚本"重复, 后者已足够. **保留不改 (本轮)**: 硬护栏按标准留位; TEMPLATES 与读写纪律的重复表述未动, 待我另行裁决是否删.

## 4 保持的优点

- 完成标准覆盖: 22 个流程/参考型 skill 共 137 处, 流程型几乎每步都有; 三个 0 处的 (domain-awareness, consensus, verification-contract) 是纯参考材料, 用"要求量"承担详尽性, 合理.
- 机械判定交给脚本, 且脚本与文档分工写明: to-spec 的 `check-ac.py`/`check-tech.py`, navigate 的 `roadmap.py` 守门, use-worktree 的 `status.py`. 文档只写何时调用, 失败如何处理.
- 指针普遍带分支条件, `use-sandbox-worktree` 的"按需参考"列表与 `verify-change/REVERIFY.md` 的"只写差异"是全栈最好的两个样例.
- 引导词用得住: 紧凑/变红 (fix-bugs), 未知海域/歧路/航行 (navigate), tracer bullet, 深模块, 三根轴, 删除测试.
- 分工边界清楚, 且有不重复的成功先例: fix-bugs 把证据要求交给 verification-contract; maintain 把复跑派工交给 create.

## 5 返工进度

1. 已完成 (纯文本, 不改行为): F-01 标点 (44 处破折号 + 5 对全角引号), F-02 产物根目录指针化, F-03 方法 skill 定义收敛与启动句统一, F-04 maintain 授权节改指 create, F-07 benchmark 权限边界收敛, F-09 GHERKIN 禁令收敛, F-14 ADR 破折号与示例路径标注. F-13 复审后改判为可接受, 不改. F-23 frontmatter YAML 冒号问题已修, 并给 check_skill.py 加了同类拒绝.
2. 已完成 (语义重排): F-05 类型映射收口, F-06 反模式改正向边界, F-10 标题结构统一, F-11 第 4 步完成标准, F-12 降级信号去重. F-08 并入 F-16.
3. 已完成 (第 3 批, 我先逐项裁决后执行): F-15 按方案 B 披露制图与航行步骤; F-16 与 F-08 一起披露 verify-change 第 7, 8 步与 code-review 的 reviewer 任务简述; F-17 只对齐证据用词, 不新建真相源; F-18 三处补冲突裁定; F-19 与 F-20 补完成标准, 指针触发条件与不产出交付物声明; F-21 两个 description 改纯触发措辞. F-22 保留硬护栏, TEMPLATES 的重复表述待裁决.

每批改完用 `writing-for-llm/check_skill.py` 复跑受影响文件; 涉及调用关系时按仓库 README 口径人工核对调用语句.

## 6 复核记录

```
uv run python ~/.agents/skills/writing-for-llm/check_skill.py <每个 SKILL.md>
  -> 25/25 OK
相对链接 + 标题锚点扫描 (workflow/**/*.md, 排除 codebase-map)
  -> 0 断链; 3 个示例占位 (UBIQUITOUS_LANGUAGE_FORMAT.md 的 contexts/*.md)
非 ASCII 标点扫描 (破折号, 全角引号, 句号等)
  -> 修后 0; navigate/tests/visual/README.md 6 个句号属测试夹具, 未动
绝对路径扫描
  -> 0 (use-sandbox-worktree 的容器固定路径与 PROVENANCE 的 /tmp 命令均已声明)
跨文件同句扫描 (>=22 字, 排除代码块)
  -> 已消除: "完成标准见 verification-contract" 6 次, create/maintain 授权节逐字重复;
     保留: 6 个入口文件同一句 domain-awareness 加载步骤 (各自上下文的加载动作, 非定义重复)
H1 统计
  -> 修后 25 个 SKILL.md 各 1 个目的名 H1; decision-ledger 模板代码块内的 1 处不计
严格 YAML 扫描 (yaml.safe_load, 仓库所有 *.md 的 frontmatter)
  -> 活跃 SKILL.md 0 失败; docs/changes 下 5 个历史证据夹具故意保留坏 frontmatter
```

第 3 批 (2026-11-01) 复核:
```
check_skill.py (仓库内版本, 非安装版) 25/25 OK
相对链接 + 标题锚点扫描 (workflow/**/*.md, 排除 codebase-map, 含 5 个新文件)
  -> 123 条, 0 断链
非 ASCII 标点扫描
  -> 仅 navigate/tests/visual/README.md 的 6 个句号 (测试夹具, 未动)
严格 YAML frontmatter 扫描 (yaml.safe_load, 排除 docs/changes 历史夹具)
  -> 0 失败
H1 统计
  -> 25 个 SKILL.md 各 1 个 H1, 无异常
跨文件同句扫描 (>=22 字, 排除代码块)
  -> 新披露文件与主文件无逐字重复的完成标准; 既有保留项不变
行数
  -> navigate/SKILL.md 129 -> 89, 新增 reference/MAPPING.md 20 与 reference/VOYAGE.md 22
  -> verify-change/SKILL.md 136 -> 106, 新增 reference/SCENARIO-CHECK.md 30 与 reference/EVIDENCE.md 26
  -> code-review/SKILL.md 109 不变 (任务简述移出, 输入清单保留)
  -> domain-awareness/SKILL.md 19, domain-modeling/deliberate/codebase-design 各补一句
tests
  -> tests/test_env_docs.py 11 项直接经 unittest 全过 (根 conftest 无 podman, pytest 收集期失败, 见 §0)
  -> navigate 的 3 条 SKILL.md 文本断言改指 reference/MAPPING.md
```
