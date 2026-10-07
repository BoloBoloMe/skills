# review-session skill 决策账本

本账本是 milestone-04 (写出 `general/review-session/SKILL.md`) 的权威输入. 记录本次盘问确认的决策与所依赖的事实, 不写成摘要.

## 决策

### D001 交付范围与交付物
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 本任务的交付物只有 `general/review-session/SKILL.md` 与 `README.md` 通用技能列表新增一行. 不加契约测试, 不为该 skill 单独建决策文档. 本文档所在的 `docs/changes/review-session-skill/` 是路线图过程目录, 不计入 skill 交付物. 理由: 用户把"落盘与跟踪机制"和"沉淀通用移植约定"划为目的地之外 (见 ROADMAP `off_course`); 本次目标是复刻 matt retro, 不是给 skill 加工程配套.
- 依赖事实: F001, F009
- 预计影响: `general/review-session/SKILL.md` (新建), `README.md` (通用技能列表)
- 实际影响: 待实现
- 需要调整: 无

### D002 frontmatter 形态
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: `name: review-session`; `disable-model-invocation: true` (由用户主动调用, 模型不主动触发); `description: 复盘一次会话, 按类别给出 agent 环境的改进候选, 默认当前会话.` description 只写一行人类摘要, 不堆触发词 (translate-a-skill 对用户调用型 skill 的规定: 设 `disable-model-invocation: true` 时 description 只写一行). 理由: 源版即 `disable-model-invocation: true` 的 `/retro`, pi 里对应 `/skill:review-session` (F010). 它由用户主动调用, 常用于困难会话结束时 (不限于结束时刻); 默认复盘当前会话, 也可指定任意历史会话 (语义照源版).
- 依赖事实: F001, F010
- 预计影响: `general/review-session/SKILL.md` 的 frontmatter
- 实际影响: 待实现
- 需要调整: 无

### D003 保留源版结构与 7 个类别, 类别名中文化
- 状态: 已替代 (→ D014)
- 约束性: 不适用 (已替代)
- 内容: 正文保留源版的 4 个步骤 (先读写作指南 → 读指定会话原始记录 → 按 7 类找改进候选 → 按严重度列出候选), 保留 7 个改进类别, 每类的 `_Use when_` 触发条件一个不删, 所有强度词 (`must`/`never`/`only`/`at most` 等) 强度守恒. 类别名译成中文: Navigation→导航, Automated checks→自动检查, Coding standards→编码规范, Global AGENTS.md→全局 AGENTS.md, Tool economy→工具开销, No-ops→空操作, Information access→信息获取; 不附英文原文. 理由: 目的地是复刻 matt retro 的行为语义; 用户要求中文, 且仓库词表 (writing-for-llm) 已用 `空操作` 等中文术语, 用中文类别名与仓库既有语言一致.
- 依赖事实: F001, F007
- 预计影响: `general/review-session/SKILL.md` 正文
- 实际影响: 待实现
- 需要调整: 无

### D004 指向目标运行时不存在实体的引用替换映射
- 状态: 已替代 (→ D014)
- 约束性: 不适用 (已替代)
- 内容: 逐条替换源版里在 pi 中不存在的实体, 其余照译:
  - `writing-for-agents` (skill) → 引用写法"调用 `writing-for-llm` skill" (仓库对应 skill).
  - `reviewer agent` / `implementation agent` → `审核者` / `执行者` (定义见 `workflow/tdd-as-orchestra/SKILL.md`).
  - `CLAUDE.md`/`AGENTS.md` → `AGENTS.md`, 并注明含全局 `~/.pi/agent/AGENTS.md` 与仓库级 `AGENTS.md`.
  - Skill 工具 → 直接读对应 skill 的 `SKILL.md`.
  理由: 源版有些引用在 pi 里不存在, 直译会诱发幻觉调用 (writing-for-llm 的"反向激活"); 替换成 pi 里真实存在的东西是本次目的地的硬要求.
- 依赖事实: F001, F007, F008
- 预计影响: `general/review-session/SKILL.md` 正文与 Reference
- 实际影响: 待实现
- 需要调整: 无

### D005 编码规范类 (Coding standards) 的落点
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 把源版的 `CODING_STANDARDS.md` 泛化为"仓库中给评审者读的规范文档 (如 `CODING_STANDARDS.md` / `CONTRIBUTING.md`, 无则提议新建)", 不钉死文件名. 保留源版判据: 机械违规 (固定句式, 禁用 API, 导入形状, 文件位置规则) 一律做成确定性检查 (仓库自身 linter 规则 / pre-commit hook / CI job / 测试, 取该仓库语言与既有护栏下最便宜者); 只有真正靠判断的规范 (跨文件一致性, "与周围风格一致" 之类) 才写进规范文档. 理由: 用户指出 `CODING_STANDARDS.md` 用途不明; 查明它并非任何 skill 自带, 而是仓库里存放"判断题式规范"的约定文件, 由评审阶段读取, 不进实现者上下文, 若仓库已有其它规范文档 (如 `CONTRIBUTING.md`), 沿用同一路径 (F002). 兼容并包 (把源版列出的多种机检方式都保留), 同时不绑死文件名与栈.
- 依赖事实: F002, F006, F007
- 预计影响: `general/review-session/SKILL.md` 的 Coding standards 类
- 实际影响: 待实现
- 需要调整: 无

### D006 自动检查类 (Automated checks) 不绑技术栈
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 源版"先读仓库自己的 check 命令 (`package.json` / 构建工具的 lint/check 脚本, CI workflow)"里的 JS 专属表述改为通用表述: "读仓库自己的检查入口 (任务/构建脚本, 测试命令, CI 配置), 按仓库实际语言与工具". 保留两条源版判据: (a) 已有检查却没接线或坏了, 发现是"接上它"而不是"重造"; (b) 完全没有护栏 (无 pre-commit 也无 CI 跑 lint/类型/测试) 本身就是发现, 不是中性默认. 理由: 用户要求 skill 不能绑死某一种技术栈, 而源版只面向前端项目; 通用表述对任何语言成立, 且不点名本仓库路径 (`tests/run` 之类), 避免平台/栈细节过期.
- 依赖事实: F001, F005
- 预计影响: `general/review-session/SKILL.md` 的 Automated checks 类
- 实际影响: 待实现
- 需要调整: 无

### D007 步骤 2 的最小 pi 会话访问契约
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 步骤 2 (读会话原始记录) 不内联 pi 的目录字面量, 命令细节与字段清单, 但必须写明最小访问契约: (a) 默认分析当前会话, 指定历史会话时按 pi 的会话标识/会话头定位; (b) pi 把会话保存为日志记录, 复原读的是其中的消息与工具记录; (c) 访问细节可压成一句运行时指针, 不扩写成流程. 理由: 用户先定"不内联 pi 细节/不绑平台" (Q7, Q12=a), 独立反方子代理 (gpt-5.6-sol) 攻击指出这与"候选必须追溯回会话"(D008) 及目的地"给出真候选"内部冲突; 用户 Q9 也承认"skill 只需关心 pi 是如何管理会话的". 折中为最小契约: 承认 pi 会话机制与定位口径, 但不把会过期的路径/命令钉进 skill. 反方结论: "平台无关"≠"没有访问契约", 删掉边界不换来可移植性. 评估: 反方成立, 故修订 Q12=a 为最小契约.
- 依赖事实: F004, F003
- 预计影响: `general/review-session/SKILL.md` 步骤 2
- 实际影响: 待实现
- 需要调整: 无

### D008 候选输出形态: 只列不落盘, 且必须可追溯
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: skill 只把改进候选按严重度列出给用户, 不落盘, 不改代码; 由用户挑选后才谈落地. 每条候选附: 类别 + 会话里的具体出处 (哪次会话的哪一刻) + 建议动作; 建议动作必须指向真实存在的文件或机制 (F009). 把"每条候选都能追溯回会话的某一刻, 不是通用最佳实践"写成候选的完成标准. 理由: 源版步骤 4 只说 "Present these candidates to the user"; matt 官方 retro 说明明写 "Every candidate must come from the session's own record" 与 "Every candidate points back to a specific moment in the session, not a generic best practice", 并点名最常见的批评就是 agent 会 "invent generic advice to fill its categories" (F003). 用户 Q10=a 采纳, 依据即 matt 官方说明, 非自行加料. 只列不落盘由用户先前 Q6=a 决定 (落盘与跟踪属目的地之外, 见 ROADMAP `off_course`).
- 依赖事实: F001, F003, F009
- 预计影响: `general/review-session/SKILL.md` 步骤 4
- 实际影响: 待实现
- 需要调整: 无

### D009 找不到指定会话时如实报告
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 找不到用户指定的会话 (例如已被清理或用户记错) 时, 如实说明无法分析, 不用别的会话或关键词命中冒充目标会话. 该约束是通用表述, 不绑平台. 理由: 源版没有明写; milestone-01 查到的 pi 清理边界 (F004) 与"按关键词命中冒充会话身份"是真实风险; 补一条通用诚实约束不违反"不内联 pi 细节".
- 依赖事实: F004
- 预计影响: `general/review-session/SKILL.md` 步骤 2
- 实际影响: 待实现
- 需要调整: 无

### D010 Navigation 类用仓库既有词"指针"
- 状态: 当前有效
- 约束性: 可调整
- 内容: 源版 Navigation 类里的 "navigation pointer" 用仓库既有术语"指针"/"上下文指针" (`general/writing-for-llm/SKILL.md` 已定义), 保证两个 skill 说同一件事. 理由: 术语一致, 避免同义异名.
- 依赖事实: F007
- 预计影响: `general/review-session/SKILL.md` 的 Navigation 类
- 实际影响: 待实现
- 需要调整: 无

### D011 Reference 两段都保留并本地化
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 源版 Reference 的两段都保留: (a) `Implementation vs Review` — 用 D014 的 `执行者`/`审核者`, 语义照搬 (实现者上下文压力最大, 审核者压力最小, 故编码规范应由审核者施加), 这是整套归责的支点; (b) `Files` — 本地化保留: `CLAUDE.md`/`AGENTS.md` 按 D014 处理 (两者都保留, 不合并), `CODING_STANDARDS.md` 按 D005 泛化, Docs 段照译, Skills 段的 `writing-for-agents` 换成 `writing-for-llm`. 理由: Files 段是"为什么 AGENTS.md 要节俭"的设计依据, 删掉会丢上下文; 用户 Q4 采纳保留.
- 依赖事实: F001, F007
- 预计影响: `general/review-session/SKILL.md` 的 Reference
- 实际影响: 待实现
- 需要调整: 无

### D012 平台无关的边界: 折中
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 保留跨工具通用或本仓库既有的实体系 (`AGENTS.md`/`CLAUDE.md`; `执行者`/`审核者`; 引用写法"调用 `writing-for-llm` skill"); 泛化 pi 独有的路径与技术栈细节 (会话目录/命令, `package.json`, 本仓库 `tests/run` 等). 不把 skill 写成跨所有 agent 平台的抽象 (那样会丢锚), 也不把 pi 路径钉死. 理由: 用户 Q9=b; 本 skill 就住在 pi/skills 生态, `AGENTS.md` 已是多工具通行约定, `执行者`/`审核者` 是仓库共享语言; 而路径/栈细节会过期. 注意: 会话访问是 pi 运行时事实, 非某技术栈假设, 故 D007 仍保留最小会话契约.
- 依赖事实: F007, F008
- 预计影响: `general/review-session/SKILL.md` 全文
- 实际影响: 待实现
- 需要调整: 无

### D013 严重度排序照源版, 不自行发明判据
- 状态: 当前有效
- 约束性: 可调整
- 内容: 保留源版"按严重度排列候选"一句, 不自己发明严重度判据; 至多补一句"排序是初稿, 可被推翻". 理由: 复刻优先, 源版未定义判据; matt 官方说明也承认 "Treat the severity order as a first draft too". 用户 S1 采纳.
- 依赖事实: F001, F003
- 预计影响: `general/review-session/SKILL.md` 步骤 4
- 实际影响: 待实现
- 需要调整: 无

### D014 上下文文件与引用映射 (替代 D003, D004)
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 整体替代 D003 与 D004, 落实用户对 `CLAUDE.md` 与全局路径的异议:
  - 正文保留源版 4 步 + 7 个改进类别 + 每类 `_Use when_` 触发条件一个不删 + 强度词 (`must`/`never`/`only`/`at most` 等) 强度守恒.
  - 7 个类别名中文化: 导航, 自动检查, 编码规范, 全局 AGENTS.md / CLAUDE.md, 工具开销, 空操作, 信息获取. 原第 4 类 `Global AGENTS.md` 因同时支持 `CLAUDE.md` 而改名为 `全局 AGENTS.md / CLAUDE.md` (正文覆盖仓库级与全局两个作用域). 不附英文原文.
  - 不再把 `CLAUDE.md` 并入 `AGENTS.md`: pi 同时把 `AGENTS.md` 与 `CLAUDE.md` 当上下文文件加载 (F011), 故 skill 读/分析两者都认, 提到全局上下文文件时写 `AGENTS.md / CLAUDE.md`.
  - 不写死 pi 全局路径: 只写 `全局 AGENTS.md / CLAUDE.md` 与 `仓库级 AGENTS.md / CLAUDE.md`, 不出现 `~/.pi/agent/AGENTS.md` 字面量.
  - 引用映射: `writing-for-agents`→引用写法"调用 `writing-for-llm` skill"; `reviewer agent`/`implementation agent`→`审核者`/`执行者` (定义见 `workflow/tdd-as-orchestra/SKILL.md`); Skill 工具→直接读对应 skill 的 `SKILL.md`.
  理由: pi 实际支持 `CLAUDE.md` (F011), 把它当"不存在的实体"替换掉是错误前提; 全局路径会随 agent 目录设置变化, 写死会过期 (用户明确要求不写死).
- 依赖事实: F001, F007, F008, F011
- 预计影响: `general/review-session/SKILL.md` 全文
- 实际影响: 待实现
- 需要调整: 无 (尚未实现, 实现时以本决策为准)

## 事实

### F001 源版 retro skill 的内容与位置
- 状态: 当前有效
- 来源: `https://github.com/mattpocock/skills/blob/main/skills/engineering/retro/SKILL.md` (main 分支, 已抓取全文); 官方说明 `docs/engineering/retro.md`
- 内容: 源版 4 步: (1) 调 `writing-for-agents` skill 拿写作风格; (2) 读用户指定会话的原始来源 (会话日志), 未指定则默认当前会话; (3) 按 7 个类别找改进候选; (4) 按严重度列给用户. 7 类: Navigation, Automated checks, Coding standards, Global AGENTS.md, Tool economy, No-ops, Information access, 每类带 `_Use when_`. Reference 两段: Implementation vs Review, Files. frontmatter: `name: retro`, `description: "Conduct a retrospective on a coding session."`, `disable-model-invocation: true`.

### F002 `CODING_STANDARDS.md` 的性质
- 状态: 当前有效
- 来源: matt 官方 retro 说明 `docs/engineering/retro.md` ("My setup mentions `CODING_STANDARDS.md` and I don't have one. Where does it come from?")
- 内容: 没有任何 skill 自带 `CODING_STANDARDS.md`. 首次出现只有判断成分的规范时, retro 提议创建; 用户接受后由 code-review 读取. 若仓库已有其它规范文档 (如 `CONTRIBUTING.md`), 可沿用同一路径. 它在评审阶段读, 不进实现者上下文.

### F003 matt 官方 retro 说明的关键约束
- 状态: 当前有效
- 来源: `https://raw.githubusercontent.com/mattpocock/skills/main/docs/engineering/retro.md`
- 内容: (a) "Every candidate must come from the session's own record"; (b) "Every candidate points back to a specific moment in the session, not a generic best practice"; (c) 常见批评是 agent 会 "invent generic advice to fill its categories"; (d) "Treat the severity order as a first draft too"; (e) 只提议不落盘 ("retro only proposes. Nothing changes until you pick a candidate"); (f) 它改环境不改代码; (g) 标准归评审者不归实现者, 永不写进 AGENTS.md.

### F004 pi 会话日志的事实
- 状态: 当前有效
- 来源: `docs/changes/review-session-skill/milestone-01/findings.md` (源码与实测)
- 内容: pi 默认把会话存到 `~/.pi/agent/sessions/<cwd 编码目录>/*.jsonl`; 目录名由 cwd 去头 `/` 后把 `/`,`\\`,`:` 换成 `-`, 两端加 `--`; 文件名是 `<ISO 时间戳>` + `_<session id>`; 首行 `type: "session"` header 含 id/timestamp/cwd/version; `thinking`/`toolCall` 是 message content block, 工具结果是 `message.role: "toolResult"`; 30 天是硬清理上限 (`pi/extensions/session-prune.ts` STALE_SESSION_DAYS=30, `fs.rm` 不可恢复, 无清单日志). 本次 D007 只吸收"pi 把会话存成日志记录, 按会话标识/会话头定位, 默认当前会话"这一层, 不内联路径与命令.

### F005 pi 与本仓库的检查与护栏实况
- 状态: 当前有效
- 来源: `docs/changes/review-session-skill/milestone-02/findings.md`
- 内容: pi 有 `tool_call`/`user_bash` 扩展拦截点; 本仓库 `pi/extensions/` 有 3 个门禁 (git-operation-gate, filesystem-operation-gate, python-operation-hook) 但当前未加载; 当前全局扩展无工具拦截; 无 pre-commit, 无 CI 工作流, 无活动 Git hook; 检查入口是 `tests/run` (按未提交改动面选套件, `--fast`/`--all`) + `pytest.ini` (快层 `-m "not e2e"`, 慢层 e2e, 串行); `tests/run` 的映射比 `tests/README.md` 声明的窄; 全局 `~/.pi/agent/AGENTS.md` 与仓库根 `AGENTS.md` 是两个作用域, 通常一起进入 prompt, 都是提示词约束不是硬安全边界.

### F006 本仓库没有 CODING_STANDARDS.md
- 状态: 当前有效
- 来源: 仓库根 `find . -iname 'CODING_STANDARDS*' -o -iname 'CONTRIBUTING*'` 无输出
- 内容: 本仓库当前无 `CODING_STANDARDS.md` 也无 `CONTRIBUTING.md`. 故 D005 采用"无则提议新建"的口径.

### F007 仓库既有术语与相关 skill
- 状态: 当前有效
- 来源: `docs/language/UBIQUITOUS_LANGUAGE.md`; `general/writing-for-llm/SKILL.md`; `workflow/tdd-as-orchestra/SKILL.md` 第 13-14 行
- 内容: `general/writing-for-llm/SKILL.md` 已定义 `空操作`, `上下文负载`, `指针`/`上下文指针` 等术语 (仓库词表 `docs/language/UBIQUITOUS_LANGUAGE.md` 收的是仓库基建术语, 不含这些); `执行者`/`审核者` 定义在 `workflow/tdd-as-orchestra/SKILL.md` (`执行者` = 真正干活的角色, `审核者` = 审核别人劳动成果并向总指挥反馈); `workflow/code-review` 已定义 Standards 轴读仓库规范来源 (`CODING_STANDARDS.md`/`CONTRIBUTING.md`/`AGENTS.md`/lint 配置) 并始终携带 Fowler 坏味道基线.

### F008 pi 的技能与子代理机制
- 状态: 当前有效
- 来源: pi 文档与工具表; 本仓库 `AGENTS.md` (全局)
- 内容: pi 没有内置 `Skill` 工具, skill 以读对应 `SKILL.md` 的方式调用; pi 没有内置子代理工具, 本仓库约定"在 pi 里开子代理 = 在 herdr 开新会话" (`workflow/code-review` 第 4 步已自带"运行时不支持子 agent 就父会话依次跑"的降级). 故按 D014 把源版的 Skill 工具引用改成直接读 `SKILL.md`.

### F009 目的地与已关闭调查的指针
- 状态: 当前有效
- 来源: `docs/changes/review-session-skill/roadmap/ROADMAP.json` (destination, notes, milestones, off_course; 经守门脚本读写)
- 内容: 目的地 (到达时的样子, 非当前事实; 该文件尚未创建) = 仓库里有一份已提交的 `general/review-session/SKILL.md` (中文, 步骤/7 类/2 段 Reference, 强度词逐条对应, 指向 pi 外界的引用都换成 pi 里真实存在的东西), 用户同步到 pi 后在真实会话上跑通一次, 候选按严重度排序且都指向真实存在的文件或机制. 已关闭: milestone-01 (会话日志读法), milestone-02 (仓库检查与护栏). `off_course`: 搬 matt 其它 skill / 沉淀通用移植约定; 候选的落盘与跟踪机制. `unknown_seas`: 7 类是否够用, 待 milestone-05 实跑证据.

### F010 pi 的 skill 调用方式
- 状态: 当前有效
- 来源: pi 文档 `docs/skills.md:45,53`, `docs/settings.md:156` (`enableSkillCommands`), `docs/slash-commands.md:58`
- 内容: pi 把 skill 注册为 `/skill:<name>` 命令 (`enableSkillCommands` 控制是否出现在命令发现里, 手动输入始终可用); `disable-model-invocation: true` 的 skill 只能由用户显式 `/skill:<name>` 调用. 故 `review-session` 的调用是 `/skill:review-session`; 源版的 `/retro` 不再对应. 源版正文本身未提 `/retro`, 故 skill 正文无需写入调用方式.

### F011 pi 的上下文文件
- 状态: 当前有效
- 来源: pi 文档 `docs/configuration.md` (Context files 小节); `docs/changes/review-session-skill/milestone-02/findings.md` 3.1
- 内容: pi 从 agent 目录, 当前工作目录及父目录加载上下文文件; `AGENTS.md` 与 `CLAUDE.md` 都被识别并进入 prompt; `AGENTS.override.md` 只替换同目录的 `AGENTS.md`/`CLAUDE.md`. 故 skill 应同时支持两者, 不必把 `CLAUDE.md` 替换成 `AGENTS.md`.
