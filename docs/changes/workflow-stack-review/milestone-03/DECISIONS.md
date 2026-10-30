# PoC 执行与 demo 兼容策略决策账本

产物根目录: `docs/changes/workflow-stack-review/milestone-03/`.
所属里程碑: milestone-03. 本账本记录已确认决策, 不代表改造已实施; 实施归 milestone-04.
确认来源: 2026-10-30 本轮 Q1 至 Q19 的盘问, 我在最后一轮明确回答「结束盘问」. 盘问按 grilling 决策树推进五轮, 每轮前沿独立于未定项.
原始对话可读出处: `/home/bolo/.pi/agent/sessions/--home-bolo--/2026-10-30T13-42-24-526Z_01a18d0c-200e-74b3-8803-a7c359b289a3.jsonl`. 核对时只取用户正文与盘问题目, 不搬运模型推理或作者自评; 信箱来信不作为我的产品决策.
上游权威输入: `../milestone-01/DECISIONS.md` 当前有效条目, 其中 D005 (PoC 交付有条件的实测结论) 与 D006 (demo 是演示用途) 是本账本的直接前提. 本账本不改变 D001-D013, 只补 milestone-03 遗留的承接, 兼容与枚举问题.
本轮涉及文件均为只读核查: `workflow/prototype/SKILL.md`, `LOGIC.md`, `UI.md`; `workflow/navigate/{SKILL.md,TEMPLATES.md,scripts/roadmap.py,web/index.html,tests/visual/render_checks.py}`; `README.md`; `general/writing-for-llm/SKILL.md`. 未修改任何文件, 未安装, 未运行同步.

## 决策

### D001 里程碑类型 prototype 与同名 skill 一并改名 demo, 不留旧名别名
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 我在 Q1 选择 A. `workflow/prototype/` 改为 `workflow/demo/`, frontmatter `name: demo`, description 重写为演示用途 (旧句 "构建一次性原型回答设计问题 — 逻辑验证或 UI 外观" 与新定位不符). `roadmap.py` 的 `TYPE_VALUES` 用 `demo` 替换 `prototype`; 网页类型标签改为 `演示`. 不收 `prototype` 作别名: 我核实仓库内没有任何 ROADMAP.json 使用该类型 (F001), 旧图读取没有实际需求, 保别名只增加校验分支和文档债务. 历史文件不改名: 既有 `docs/changes/<slug>/prototypes/` 产物目录, 旧格式 `ROADMAP.md`/`MILESTONE-NN.md`, 历史提交里的 `prototype/<slug>` 分支名一律原样保留, 因为它们属于已完成变更的一手材料, 不是活跃约定.
- 依赖事实: F001, F002, F003
- 预计影响: `workflow/demo/` (含 LOGIC.md, UI.md), `roadmap.py` 类型枚举, `web/index.html` 的类型元数据/图例/星球视觉分支, `tests/visual/render_checks.py`, `navigate/SKILL.md` 四处 (类型条目, 完成标准, 收口产物, deliberate 条目里点名 prototype 那句), `navigate/TEMPLATES.md` 枚举行, `README.md` 技能表.
- 实际影响: 尚未实施, 由 milestone-04 落地.

### D002 新名字落实到路径与分支: 三种子形态的存放位置照旧, 只把 prototype 这个词换成 demo
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 我在 Q13 选择 A, 并在 Q8/Q10/Q11 反复纠正 "不要把产物写死放在 demos/". 现行设计不是单一目录, 而是三个子形态各按场景落位, 改造保留这套落位逻辑, 只做词面替换: 子形态 C (无前端项目) 目录 `docs/changes/<feature-slug>/prototypes/<prototype-name>/` → `demos/<demo-name>/`; 子形态 A (贴现有页面) 文件仍在 `src/` 宿主页面附近, 前缀 `prototype.` → `demo.`, 取数与 `?variant=` 机制不变; 子形态 B (新页面) 路由 `/prototype/<name>` → `/demo/<name>`, 多文件子目录 `prototype/` → `demo/`; 一次性分支 `prototype/<feature-slug>` → `demo/<feature-slug>`. 只有名字变化, 位置规则, 子形态判定顺序, 前缀作用都不变.
- 依赖事实: F003
- 预计影响: `workflow/demo/SKILL.md` 的路径约定句, `LOGIC.md` 与 `UI.md` 的路径/前缀/路由/分支措辞.
- 实际影响: 尚未实施.

### D003 demo 是可保留回看的演示材料, 不再是一律丢弃的一次性代码
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 我在 Q5 选择 C, 在 Q8 选择 A. demo 的定位从 "回答问题的一次性代码" 改为 "让人看清指定样子, 行为或过程的演示材料", 不进入产品, 不承诺交付. 旧的规则 1 "从诞生就注定被丢弃" 改为 "不进入产品, 不承诺交付"; 演示材料按 D002 的路径约定留存, 可事后回看, 不再默认用后删除. 规则 6 "验证止于冒烟, 其余由我驱动" 改写为 "验证止于能演示, 其余由我驱动": 演示是否达意只有我驱动才暴露, 实现瑕疵会在我操作时顺路浮现. 规则 5 的捕获改为记录演示了什么, 想让我据此判断什么, 材料位置, 以及相关 issue 的指针. 依据是我在 Q5 明确选择去掉一次性定位, 且 Q8 选择保留回看.
- 依赖事实: F003; milestone-01 D006
- 预计影响: `workflow/demo/SKILL.md` 的定位句与规则 1/5/6; `LOGIC.md` 第 5 步 "合并主干前由人类清理"; `UI.md` 的清理与归档句.
- 实际影响: 尚未实施.

### D004 demo skill 只管造演示材料, 不管用现成成品演示, 正文不提 PoC
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 我在 Q9 选择 A, 并在 Q7 之后明确纠正 "demo 不用关心 PoC, 连提都不要提". demo skill 的范围收窄为 "怎么造演示材料": 逻辑/状态类走单页交互, 外观类走多变体切换 (Q10=A, 分支判据不变). 拿已交付的 MVP 或线上系统演示时不调用本 skill — 直接跑成品即可, 没有材料要造也没有一次性文件要清. 展示 PoC 结果同样不在 demo 侧加任何要求: 不做证据引用, 不做未证实标注, 不提 PoC 字样; PoC 的结论与证据留在 poc 里程碑自己的产物里 (见 D008). 这样 demo 侧没有跨里程碑耦合, 也避免演示材料被当成可行性结论的背书.
- 依赖事实: F003; milestone-01 D005, D006
- 预计影响: `workflow/demo/SKILL.md` 的适用范围句; `navigate/SKILL.md` 的 demo 类型条目 (承接 "可演示现成成品" 与 "演示不新增交付承诺" 两句边界, 不涉及 PoC 证据).
- 实际影响: 尚未实施.

### D005 demo 类型的创建条件扩到 "需要让人看清某个样子/行为/过程"
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 我在 Q15 选择 A. `navigate/SKILL.md` 里 demo 的 **何时创建** 从 "问题是它应该是什么样子/如何运行" 扩为 "问题是它应该是什么样子, 如何运行, 或需要让人看清某个样子/行为/过程以便讨论". 理由是 Q9=A 已把 "演示现成成品" 留在类型边界内, 创建条件不覆盖这个场景会让类型条目自相矛盾. 可交互有反馈的演示隐含着文字说不清的隐性知识, 仍应积极使用. HITL 属性不变 (旧 prototype 同样是 HITL, 演示的判断只有我在场才成立).
- 依赖事实: F003
- 预计影响: `navigate/SKILL.md` 的 demo 类型条目与完成标准 (见 D006).
- 实际影响: 尚未实施.

### D006 demo 的完成标准: 我看过并能据此判断, 材料按路径约定落位
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 我在 Q11 选择 A, 并对 Q17 明确纠正: 完成标准写成 "演示已做, 我看过并能据此判断要讨论的事", 不提固定目录也不额外要求留档或记录. 造了材料就按 D002 的路径约定各放各位; 用现成成品演示时没有任何材料, 直接跑成品, 完成标准照旧只要求我看过并能判断. 我否定了 "必须在 `demos/` 留档" 与 "用成品也要补一份说明进 demos/" 两种写法, 理由是把路径写死会给不该留材料的场合制造空产物, 也让标准从 "能否判断" 偏移到 "文件在不在".
- 依赖事实: F003
- 预计影响: `navigate/SKILL.md` 的 demo 完成标准句; 浏览器页面在类型说明上的措辞.
- 实际影响: 尚未实施.

### D007 多变体演示的完整变体集进 demo 分支备查, 不合并主干
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 我在 Q16 选择 A. 子形态 A/B 的完整变体集仍提交到 `demo/<feature-slug>` 分支, 胜出变体融入工作分支的真实代码; 与该名称冲突时追加时间戳. 旧规则里 "用完即删" 的部分取消: 分支保留备查, 满足 D003 的可回看要求, 也不合并主干 (变体代码是在演示约束下写的, 无测试, 最少错误处理, 直接进主干是负担). 子形态 A 必须贴在真实页面里的理由不变: 空路由会隐藏设计问题, 真实数据与周边元素才暴露它们, 把变体集挪到 `docs/changes/` 会丧失这个价值.
- 依赖事实: F003
- 预计影响: `workflow/demo/UI.md` 第 6 步 (归档与清理), `SKILL.md` 规则 5 的归档句.
- 实际影响: 尚未实施.

### D008 PoC 是独立的 navigate 里程碑类型, AFK, 不新建 skill
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 我在 Q2 选择 A. `roadmap.py` 的类型枚举增加 `poc`; `navigate/SKILL.md` 增加 poc 类型条目与完成标准, 正文写清: 交付在明确条件和判据下可行/不可行的结论及真实实验依据, 依据要能让人复查所测方案, 待回答问题, 实验条件, 判据, 实际操作与结果, 结论适用范围; 环境或权限导致未完成实测时记未证实, 保持未完成, 不报不可行. 这几条直接承接 milestone-01 的 D005, 不在 navigate 里另立新定义. AFK: 实验由代理独立驱动, 不需要我在场. 不新建 `workflow/poc/` skill: D005 已把概念边界定得足够细, navigate 条目装得下, 新增 skill 是多一处长期维护的入口而方法收益没有证据.
- 依赖事实: F005; milestone-01 D005
- 预计影响: `roadmap.py` 类型枚举, `navigate/SKILL.md` 类型条目与完成标准, `TEMPLATES.md` 枚举行, `web/index.html` 类型元数据与图例, `tests/visual/render_checks.py` 类型清单.
- 实际影响: 尚未实施.

### D009 poc 未证实或我主动放弃时, 由我裁决终止并解除验收依赖, 不新增状态枚举
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 我在 Q3 选择 B. 默认行为仍是 "未证实保持未完成"; 只有我在场明确裁决终止时, 该 poc 里程碑才记关闭, close_summary 写 "未证实即终止, 不构成可行性结论", 同时把它从终点验收的 `blocked_by` 移除, 并在 `off_course` 记一条原因. 代理不得自行这么判, 不得把 "环境长期拿不到" 当作自行脱身的理由 — 环境缺口属于向我报告的阻塞, 不是实现缺陷, 也不是范围外的歧路. 不新增 `已取消` 状态: 现有三种状态的校验与渲染都稳定, 而终止是有出处的个例, 用关闭摘要加 off_course 已经能如实记录.
- 依赖事实: F008; milestone-01 D005
- 预计影响: `navigate/SKILL.md` 的 poc 条目 (未证实与终止的处置), 终点验收的关系说明.
- 实际影响: 尚未实施.

### D010 poc 的粒度与执行路径
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 我在 Q19 确认的三句, 按 writing-for-llm 的正向陈述写成: (1) poc 默认一个会话做完一个里程碑, 直接给出可行/不可行结论与依据; (2) 一个会话做不完时, 拆成多个 poc 里程碑, 用依赖串起来, 每个里程碑各自收口一个结论; (3) 若某段工作的实质是交付产品代码而不是验证方案, 它就不是 poc, 属于 task. 第 3 句是我给出的原文, 其余两句经我确认. 理由: 产品编码交付那条链路 (spec 到可执行 issue 再到多人派工) 是为交付准备的, 套在一次实验上成本远大于收益; 单个 poc 过大时按结论边界拆分, 比在同一里程碑里堆多个实验更能保住 "结论可复查".
- 依赖事实: F005, F007; 本账本 D008
- 预计影响: `navigate/SKILL.md` 的 poc 条目.
- 实际影响: 尚未实施.

### D011 research 只管工作目录之外已有的外部事实, 实验结论归 poc
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 我在 Q4 选择 A, 在 Q12 选择 A. `research` 的 **何时创建** 只留 "决策在等一个藏在当前工作目录之外的事实 (文档, API, 知识库, 别人的代码), 须先暴露"; 原有 "或等一个无处可查的结论, 须先做实验测出" 整句删除, 因为该场景已由 poc 承接 (D008). 同时在 research 条目写清 "工作目录内的事实就地查, 不单立里程碑": 当前正在做的里程碑自己查证内部事实并写进它的产物, 查影响面用 blast-radius, 查领域用 domain-awareness; 需要单独立项才查得清的内部调查, 通常说明里程碑划错了. 这样的界线一眼能分 (问题藏在库里 vs 问题只能靠跑), 而 "顺手试跑" 这类中间态在现场判不准.
- 依赖事实: F004, F005
- 预计影响: `navigate/SKILL.md` 的 research 类型条目.
- 实际影响: 尚未实施.

### D012 网页上 demo 与 poc 各自独立外观, poc 标签英文 PoC 中文 实验
- 状态: 当前有效
- 约束性: 可调整
- 内容: 我在 Q14 选择 "视觉选 A", 并指定 "不同里程碑类型的星球视觉应保持区分度", 标签英文用 `PoC`, 中文用 `实验`. `web/index.html` 因此新增 poc 类型元数据与独立星球外观 (不与 demo 共用), demo 沿用 prototype 现有的卫星外观只换类型键与标签 `演示`. 独立外观是我明确要求区分度的直接落地; 标签 `PoC` 与对话中的既有说法一致, 中文 `实验` 与 "验收" 不撞词.
- 依赖事实: F002
- 预计影响: `web/index.html` 的 `TYPE_META`, 图例, 星球视觉分支与配色表; `tests/visual/render_checks.py` 类型清单.
- 实际影响: 尚未实施.

### D013 本次改名与新增类型记一条 ADR
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 我在 Q18 选择 A, 新建 `docs/adr/0024-demo-poc-milestone-types.md`, 写明 demo 取代 prototype, poc 为新增类型, 以及旧名的处置边界 (旧分支/旧目录只作为历史存在). 理由: 旧分支名与旧目录会长期留在历史里, 后来人会同时看到 `prototype/<slug>` 旧分支和 demo skill 并存; 没有一条 ADR 说明来源, 只能靠翻 `docs/changes/` 考古. 这与 milestone-01 "本变更概念不额外创建 ADR" 不冲突: 那里记的是词汇定义, 这里记的是跨工具, 跨文档的命名与枚举约定, 属于难以逆转的长期结构. ADR 本身由 milestone-04 落地.
- 依赖事实: F002; docs/adr 现有编号到 0023
- 预计影响: `docs/adr/0024-demo-poc-milestone-types.md`.
- 实际影响: 尚未实施.

## 事实

### F001 仓库内没有任何 ROADMAP.json 使用过 prototype 类型
- 状态: 当前有效
- 来源: 本轮 `grep -rn '"prototype"' --include=ROADMAP.json docs/` 无命中; `git worktree list` 只有一个工作树, 无其他分支携带旧数据.
- 内容: 只有旧格式 `docs/changes/swt-cross-host-access/roadmap/MILESTONE-02.md` 等历史文件提到原型/`prototype` 类型, 它们不由 `roadmap.py` 解析. 因此改名不需要数据迁移, 也不需要读兼容层; D001 "不收旧别名" 以此为依据.

### F002 改名与新增类型要同步的技术与文档点
- 状态: 当前有效
- 来源: 本轮直接读取: `workflow/navigate/scripts/roadmap.py:35`, `workflow/navigate/web/index.html` (TYPE_META/图例/星球视觉/配色), `workflow/navigate/TEMPLATES.md:31,88`, `workflow/navigate/SKILL.md:36,37,45,108`, `workflow/navigate/tests/visual/render_checks.py:30,61`, `README.md:54`.
- 内容: `TYPE_VALUES` 一行; 网页类型元数据 (label/color), 图例 SVG 与文字, 星球外观分支, 配色表键; 模板与 SKILL 的枚举行, 类型条目, 完成标准, 收口产物句, deliberate 条目里 "无法靠 prototype 提升保真度" 一句; 渲染测试的类型清单与一个 prototype 用例; README 技能表一行. 该清单来自本轮阅读, 不声称穷尽; milestone-04 实施时仍须自行复查.

### F003 旧 prototype skill 的现有内容与留存约定
- 状态: 当前有效
- 来源: 本轮只读通读 `workflow/prototype/SKILL.md`, `LOGIC.md`, `UI.md` (工作区提交 c834440 版本).
- 内容: SKILL.md 定义 "原型是回答一个设计问题的一次性代码", 分 logic/UI 两分支, 通用规则 1-6 (注定被丢弃并标记, 一条命令运行, 默认不持久化, 暴露状态, 完成后捕获, 验证止于冒烟). LOGIC.md 要求单文件自包含 HTML, 状态机或纯函数作为可移植核心, 原型放 `docs/changes/<feature-slug>/prototypes/<prototype-name>/`, 合并主干前由人类清理. UI.md 分子形态 A (贴现有页面, `prototype.` 前缀, `?variant=`), B (一次性路由 `/prototype/<name>`), C (无前端项目时降级为独立 HTML), 变体集进一次性分支 `prototype/<feature-slug>`, 胜出变体融入真实代码, 失败变体与 switcher 删除. D001-D007 以此为改造对象.

### F004 research 类型现有文本含实验半句
- 状态: 当前有效
- 来源: `workflow/navigate/SKILL.md:35`.
- 内容: 现文 "决策在等一个藏在当前工作目录之外的事实 (文档, API, 知识库等), 须先暴露; 或等一个无处可查的结论, 须先做实验测出." 后半句是 D011 要删除并交给 poc 的部分.

### F005 仓库现状: 无 poc 承接, 无既有演示约定
- 状态: 当前有效
- 来源: 本轮 `grep -rni poc` 与 `grep -rn demo` 结果; `ls workflow/` 无 poc 目录.
- 内容: "PoC" 在活跃 skill 正文中零命中, 只出现在本变更的决策账本, ROADMAP 问句与历史 docs/changes; "demo" 只命中测试夹具里的容器名 `swt-demo`. "演示" 在活跃正文只有 `workflow/to-execution/SKILL.md:32` "完成的切片本身可以演示", 那是切片可观察性描述, 不是交付物约定. 所以新增 poc 类型与 demo 改写在仓库侧没有旧正文冲突, 只有 navigate 自身要改.

### F006 本次改动只在仓库内, 不改已安装 skills
- 状态: 当前有效
- 来源: 仓库 `AGENTS.md`; 本变更 notes 的环境条目; `docs/identity.md` 的容器事实.
- 内容: 宿主上实际生效的仍是已安装的 `prototype` skill (`~/.agents/skills/` 只读并跟随宿主), 本变更不运行 `sync-to-pi.py`. 因此改造完成后, 仓库内 `demo`/`poc` 与安装目录不一致是已知状态, 安装另算, 不在本次完成边界内, 也不能拿来当已验证安装效果的证据.

### F007 writing-for-llm 禁止否定式引导
- 状态: 当前有效
- 来源: `general/writing-for-llm/SKILL.md` 的 "引导词" 节 (否定与反向激活), 我在 Q19 明确指出按该规范写.
- 内容: 提示应正向陈述目标行为, 禁令只在无法正向表述的硬护栏处保留, 且须配正向目标; 提及不存在或不使用的东西会把注意力引过去. D010 第 3 句因此按我给的原文写成正向归属表述, 不写成 "不走某 skill". milestone-04 改写 navigate 正文时同样适用.

### F008 现有验收与终止处置只有三种状态
- 状态: 当前有效
- 来源: `workflow/navigate/TEMPLATES.md` 的 milestones 成员字段; `workflow/navigate/SKILL.md` 的 "验收终点" 与航行步骤 6; milestone-01 的 F008.
- 内容: 状态枚举只有 待处理/进行中/已关闭, 没有取消; 必要工作以 `blocked_by` 阻塞终点验收; 歧路 (off_course) 指目的地之外主动排除的工作. 因此 "未证实即终止" 只能表达为关闭摘要加 off_course 记录加解除验收依赖 (D009), 不能假装存在取消状态.

## 领域文档归属与后续边界

本轮复用 `docs/language/UBIQUITOUS_LANGUAGE.md` 与 milestone-01 账本的领域感知; 共享概念仍以 milestone-02 新建的 `software-engineering-consensus` skill 为唯一维护位置, 本账本不复制其词条正文. D013 的 ADR 记命名与枚举约定, 不重记词义.
本账本不替 milestone-04 决定实现细节 (具体文案, 函数名, 视觉代码), 也不替 milestone-06 的流程接口裁决; milestone-04 仍须按 navigate 的验收标准在实施前和我对齐可观察标准. 终点验收仍由 milestone-08 汇集证据并逐项确认; 本里程碑关闭只表示决策已固化.
