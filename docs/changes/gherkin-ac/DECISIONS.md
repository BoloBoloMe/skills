# 产品验收标准 Gherkin 化与 workflow 元词汇表 决策账本

## 决策

### D001 PRODUCT.md 验收标准形式化为内嵌 Gherkin
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: to-product-spec 产物的 `验收标准` 节从自由文本 (给定/当/则句式) 改为真 Gherkin 语法, 以 ```gherkin 代码块内嵌于 markdown, 不产独立 .feature 文件. 理由: AC 已是 GWT 句式, 形式化为顺水推舟; 形式化使机检 (解析/标签/覆盖) 成为可能; 用户明确要求产物格式保持 markdown. 已排除候选: (a) 独立 .feature 文件 — 违反用户的 markdown 产物约束; (b) 散文 + 自研结构 lint (反方方案) — 评估不成立: 自研 lint 规则集是会漂移的元产物, Gherkin 是现成权威语法; LLM 对 Gherkin 有训练语料先验, 书写纪律随先验自带; 未来可执行层迁移从内嵌 Gherkin 是零成本抽取, 从结构散文是逐条重写.
- 依赖事实: F001, F005
- 预计影响: workflow/to-product-spec/SKILL.md, workflow/to-product-spec/GHERKIN.md
- 实际影响: 待实现后补记

### D002 单 Feature 块组织
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: `验收标准` 节含单个 ```gherkin 块: 首行 `# language: zh-CN`, 次行 `功能: <变更标题>`, 其后全部场景. 理由: 单块自身即完整可解析单元, 未来抽出即为合法 .feature. 已排除候选: 每 AC 独立块 — 缺 `功能:` 头, 不是合法 Gherkin 单元.
- 预计影响: workflow/to-product-spec/SKILL.md 模板
- 实际影响: 待实现后补记

### D003 AC 与场景基数: 1 AC = 1..N 场景
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 一个 AC 对应一至多个场景/场景大纲, 同 AC 的状态分支场景共用同一 `@AC-NNN` 标签; 不变量: 每场景恰好一个 `@AC` 标签; AC 的覆盖关系取其全部场景标签并集; 场景大纲计为一个场景. 理由: 反方攻击反驳一成立 — 原方案 1:1 双射与 deliberate 盘问的自然确认粒度相撞 (现实例: present-web-server AC-002 含三条状态分支), 落盘时拆 AC 等于在用户确认之外做语义切分, 违反"每项产品结论可追溯源头"; 1..N 形态解耦盘问粒度与落盘粒度, 且全部机检不变量保留.
- 依赖事实: F004
- 预计影响: workflow/to-product-spec/SKILL.md, workflow/to-product-spec/GHERKIN.md, check 脚本规则
- 实际影响: 待实现后补记

### D004 删除关键场景 (SC) 节, 并入 AC
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: PRODUCT.md 模板删除 `关键场景` 节, Gherkin 场景为唯一场景载体; 原 SC 的参与者由步骤主语承载, 类型 (正常/失败/边界) 由 `@normal/@failure/@edge` 标签承载. deliberate 盘问过程不变 (仍按正常/失败/边界推进), 落盘直接是场景. 理由: 形式化后 SC 与 AC 严重重叠, 双载体必发散, 违反单权威来源标准; 反方攻击对此点无异议.
- 预计影响: workflow/to-product-spec/SKILL.md 模板与完成标准
- 实际影响: 待实现后补记

### D005 zh-CN 关键字
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 场景使用官方 zh-CN 关键字: 假定/当/那么/而且/但是/背景/例子/场景/场景大纲/功能. `给定`/`则` 非官方关键字, 废弃. 已排除候选: 英文关键字 — 文档与步骤皆中文, 英文关键字造成语义断裂.
- 依赖事实: F001
- 预计影响: workflow/to-product-spec/SKILL.md 模板, GHERKIN.md
- 实际影响: 待实现后补记

### D006 步骤主语强制领域角色名词
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 步骤主语使用领域角色名词 (如 远程用户/agent/攻击者), 禁用代词 `我`. 理由: 场景自包含, 不依赖叙述视角; 与项目 ubiquitous language 对齐.
- 预计影响: workflow/to-product-spec/GHERKIN.md 书写纪律
- 实际影响: 待实现后补记

### D007 封闭标签集
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 只允许标签: `@AC-NNN` (每场景恰好一个) / `@G-NNN` `@US-NNN` `@BR-NNN` (覆盖关系, 每场景至少一个) / `@normal` `@failure` `@edge` (场景类型). 禁止自由标签, 由机检脚本强制. 理由: 开放标签是腐烂起点; 封闭集使机检完备.
- 预计影响: workflow/to-product-spec/GHERKIN.md, check 脚本
- 实际影响: 待实现后补记

### D008 禁用 规则:/Rule 关键字
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 不使用 Gherkin `规则:` (Rule) 关键字; BR 归属仅靠 `@BR-NNN` 标签表达. 理由: Rule 强制场景分组排序, 收益不抵约束. 该禁令由 check 脚本的关键字子集白名单机械化.
- 预计影响: workflow/to-product-spec/GHERKIN.md, check 脚本
- 实际影响: 待实现后补记

### D009 书写纪律与机检边界
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 场景书写纪律: 声明式步骤 (禁 UI 操作细节) / 每场景单个 When / Then 只写外部可观察结果 / 具体数据 / 步骤内禁条件逻辑 / `背景:` 慎用 (仅真正公共前提). 边界声明: 以上纪律无法机械化, 属 LLM 判断; 机检只覆盖解析/标签/覆盖/关键字子集. 两类规则本性不同, 不算漏洞.
- 预计影响: workflow/to-product-spec/GHERKIN.md
- 实际影响: 待实现后补记

### D010 非行为验收 (NB) 小节与执行层承接硬约束
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 审计式断言 (写不成刺激-响应行为者, 如"未引入认证/TLS") 不进 Gherkin 场景; PRODUCT.md 模板保留 `非行为验收` 散文小节, 稳定 ID `NB-NNN`; to-execution-spec 起草完成标准新增一条: 每个 NB 项必须进覆盖矩阵并有承接条目 (人工验证或 issue). 理由: 反方攻击反驳三成立 — 仅移出而无承接硬落点会使审计项退出覆盖矩阵, 成为无追踪自由断言; 现网 AC-008 型审计项当下是被矩阵追踪的, 不能开覆盖缺口. 转得了行为的断言 (如"重启后归零") 强制写成场景.
- 依赖事实: F004
- 预计影响: workflow/to-product-spec/SKILL.md 模板, workflow/to-execution-spec/SKILL.md 起草完成标准
- 实际影响: 待实现后补记

### D011 机检脚本形态与落点
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 新建 PEP 723 内联依赖脚本 (建议名 check-ac.py), 置于 workflow/to-product-spec/ 内随 skill 同步, `uv run` 执行; 依赖 gherkin-official; 校验四项: Gherkin parser 解析 / 标签封闭集与 @AC 唯一性 / 覆盖完整性 (每 AC 至少一个场景, 每场景至少一个覆盖标签) / 关键字子集白名单 (禁 Rule). 理由: 仓库无 pyproject.toml, 脚本须自含依赖; LLM 目检不可靠, 机械校验必须真脚本 (用户原则).
- 依赖事实: F002, F003, F006
- 预计影响: workflow/to-product-spec/check-ac.py
- 实际影响: 待实现后补记

### D012 机检单触发点, LLM 禁目检替代
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 机检唯一触发点 = to-product-spec 完成标准 (spec 编写方写完必须执行脚本通过才算完成). LLM (含子代理) 只允许调用脚本并汇报结果, 禁止目检解析/标签/覆盖. deliberate `检查产物` 保持纯语义校验, 不描述脚本行为. 历史: 原建议双触发点 (含 deliberate 检查产物执行脚本), 用户以 skill 边界裁定修正为单触发 — 落盘形式化与脚本校验是 spec skill 的职责, 不溢出到 deliberate.
- 依赖事实: F006, F010
- 预计影响: workflow/to-product-spec/SKILL.md 完成标准
- 实际影响: 待实现后补记

### D013 deliberate 零改动, 盘问保持自然语言
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: deliberate/SKILL.md 一字不改; 盘问全程自然语言, DECISIONS.md 记结论; AC 的 Gherkin 形式化仅发生在 to-product-spec 落盘时. 理由: 盘问中卡语法拖慢决策流速; 形式化是机械转换加机检, 不需要用户参与; skill 边界: deliberate 不关心 spec 落盘.
- 依赖事实: F010
- 预计影响: 无 (零改动)
- 实际影响: 待实现后补记

### D014 TECHNICAL spec 不动, EXECUTION 仅加 NB 承接一行
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: to-technical-spec 完全不动: 技术层不做 Gherkin 化. 理由: ROI 不成立 — Gherkin 的三方对齐收益在技术层不存在 (读者全开发者); 技术行为排列组合多, 场景维护成本线性增长; pytest 集成测试/Pact 式契约测试是更便宜等价物; 技术行为的权威载体已是测试代码, 再加 Gherkin 是双份编码, 违反单权威来源. TC 保留 Given/When/Then 散文句式作书写纪律. to-execution-spec 仅按 D010 加 NB 承接一条, 其余不动 (AC ID 不变, 引用链零涟漪).
- 预计影响: workflow/to-execution-spec/SKILL.md (一行)
- 实际影响: 待实现后补记

### D015 可执行层 defer
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 本期不写 step definitions, 不上可执行层; 触发条件 = 首个值得自动化回归的产品行为出现时再评估. 内嵌 Gherkin 设计保证届时零成本迁移 (块抽出即 .feature). 概念澄清 (会话中已对齐): step definitions 是仓库内测试胶水代码 (Gherkin 步骤文本 → 驱动函数的绑定表, 跨场景复用), 与 EXECUTION/issues 的任务切片无重叠; 若未来上可执行层, 它以"E2E 验收测试基建" issue 的实现产物身份出现. 理由: 胶水成本按项目付, 当前无回报.
- 预计影响: 无 (本期无动作)
- 实际影响: 待实现后补记

### D016 历史产物不回填
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: docs/changes/present-web-server/PRODUCT.md 等既有产物不回填新格式, 仅新变更启用. 理由: changes 是历史记录, 回填无收益有风险.
- 预计影响: 无
- 实际影响: 待实现后补记

### D017 dogfood 实例
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 本变更自产 docs/changes/gherkin-ac/PRODUCT.md, 用新格式 (Gherkin AC 块 + NB 小节) 编写, 作为模板与 check 脚本的首个试金石. 理由: 无实例的模板改动是盲改, 成本仅一份小文档.
- 预计影响: docs/changes/gherkin-ac/PRODUCT.md
- 实际影响: 待实现后补记

### D018 元词汇表全量并入本变更, 挂 domain-awareness
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: workflow 元词汇表 (workflow 系统自身的内定词汇定义) 并入本变更全量实施, 不做独立后续变更 (用户选定, 否决了折中方案"先建骨架"); 执行可在后续会话, 用子代理并行代工. 挂载: domain-awareness 新增参考文件 WORKFLOW_VOCABULARY.md (恒定返回) + SKILL.md 增加职责段; 语义分两层 — workflow 元词汇 (固定, 与目标仓库无关) 与项目领域感知 (探测目标仓库), 避免新增 skill, 保持单一维护点. 盘点方法: 子代理并行扫描 workflow/* skills 提取候选词 → 汇总定义 → 用户审. 格式沿用 UBIQUITOUS_LANGUAGE_FORMAT.md 模式 (**术语**/定义/_避免_). 收录标准: ≥2 个 skill 共用, 或单 skill 但定义非显然 (如 tracer bullet/前沿); 一眼自明的词不收. 全部 workflow skills 逐一加引用行接线.
- 依赖事实: F008
- 预计影响: workflow/domain-awareness/WORKFLOW_VOCABULARY.md, workflow/domain-awareness/SKILL.md, 全部 workflow/*/SKILL.md 接线
- 实际影响: 待实现后补记

### D019 决策引用路径化 (多账本)
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: to-product-spec 模板 `产品决策引用` 节改为路径限定引用格式 `<账本路径>: D001`, 支持多账本现实 (决策可跨会话产生多份账本, 见 F005); 与 to-execution-spec 既有规则"引用路径按实际位置解析, 不假设位于产物根目录"对齐. 理由: 现模板写单数 DECISIONS.md, 多账本下歧义.
- 依赖事实: F005
- 预计影响: workflow/to-product-spec/SKILL.md 模板
- 实际影响: 待实现后补记

### D020 权威输入优先级入元词汇表
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: "权威输入"词条进 WORKFLOW_VOCABULARY.md, 定义含优先级: spec 优先于决策账本 (理由: spec 是决策的提炼产物, 直接读账本费 token). to-execution-spec 信源顺序现状已是 spec 优先, 无需改; 本决策只负责把原则固化进词汇表.
- 依赖事实: F007
- 预计影响: workflow/domain-awareness/WORKFLOW_VOCABULARY.md
- 实际影响: 待实现后补记

### D021 to-product-spec 受众措辞修订
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 模板中"文档只供 LLM 使用"修订为"产品结果基线, 供 LLM 与人共用, 仍不要求阅读后确认". 理由: product-spec 定位是四方对齐 (三方+LLM); Gherkin 化后人可读性已是设计目标, 措辞应跟上; "不要求阅读后确认"的交互约定保留.
- 依赖事实: F005
- 预计影响: workflow/to-product-spec/SKILL.md
- 实际影响: 待实现后补记

### D022 实施清单
- 状态: 当前有效
- 约束性: 可调整
- 内容: 落地项与建议顺序: (1) workflow/to-product-spec/SKILL.md — 模板 (SC 删/AC gherkin 块/NB 小节/决策引用路径化/受众措辞) + 完成标准 (机检执行); (2) workflow/to-product-spec/GHERKIN.md — 语法子集/标签约定/书写纪律/反模式/校验方法; (3) workflow/to-product-spec/check-ac.py — 机检脚本; (4) docs/changes/gherkin-ac/PRODUCT.md — dogfood; (5) workflow/domain-awareness/WORKFLOW_VOCABULARY.md — 全量盘点; (6) workflow/domain-awareness/SKILL.md — 恒定返回职责; (7) 全部 workflow skills 接线引用; (8) workflow/to-execution-spec/SKILL.md — NB 承接一行; (9) `uv run python sync-to-pi.py` 同步. 约束性为可调整: 执行顺序与是否拆 issue 可调, 清单内容不可减.
- 预计影响: 如上列路径
- 实际影响: 待实现后补记

## 事实

### F001 官方 zh-CN Gherkin 关键字集
- 状态: 当前有效
- 来源: https://raw.githubusercontent.com/cucumber/gherkin/main/gherkin-languages.json (curl 读取)
- 内容: Given=假如/假设/假定 (不含"给定"); When=当; Then=那么 (不含"则"); And=而且/并且/同时; But=但是; Background=背景; Examples=例子; Feature=功能; Scenario=场景/剧本; ScenarioOutline=场景大纲/剧本大纲; Rule=规则.

### F002 仓库无 Python 项目文件
- 状态: 当前有效
- 来源: 命令 `cat pyproject.toml` / `ls *.py *.toml`
- 内容: 仓库根无 pyproject.toml, 仅 sync-to-pi.py. 新增 Python 工具须走 PEP 723 内联依赖, `uv run` 独立执行.

### F003 gherkin-official 可用且支持 zh-CN
- 状态: 当前有效
- 来源: https://pypi.org/pypi/gherkin-official/json; 反方子代理实测
- 内容: PyPI 存在官方 parser 包 gherkin-official 42.0.1; 实测正确解析 zh-CN 关键字 (功能/场景/假定/当/那么).

### F004 现存 PRODUCT.md 实例的 AC 形态
- 状态: 当前有效
- 来源: docs/changes/present-web-server/PRODUCT.md
- 内容: AC-001 打包两个行为 (正常+失败); AC-002 打包三条 GWT 链 (存活/进程死/文件缺失); AC-004 两条; AC-008 含四条断言且其中"无认证无 TLS 未意外引入"是代码审计断言, 非刺激-响应行为. 即: 多行为打包与非行为验收在现网是常态.

### F005 产物定位 (用户陈述)
- 状态: 当前有效
- 来源: 用户陈述
- 内容: 决策账本为固化决策供回溯, 决策可跨会话产生多份账本 (见 probe skill); spec 是从决策提炼并转述成特定风格的文档; product-spec 用于四方对齐 (业务/开发/测试三方 + LLM); technical-spec 关注系统设计 (架构/模块) + QA; to-execution-spec 是基于产品与系统设计细化的执行计划 (边界/切片).

### F006 机械校验必须真机械 (用户原则)
- 状态: 当前有效
- 来源: 用户陈述
- 内容: 所有机械校验必须写成脚本执行, 禁止 LLM 模拟机械.

### F007 权威输入优先级 (用户原则)
- 状态: 当前有效
- 来源: 用户陈述
- 内容: 工作流的权威输入应有优先级: 优先读 spec, 因为它是决策的提炼产物, 比直接读决策账本更省 token.

### F008 元词汇表需求 (用户陈述)
- 状态: 当前有效
- 来源: 用户陈述
- 内容: workflow skill 需要一套共同引用的元词汇表 — 工作流内定专有词汇的具体定义; 由一个公共 skill 维护, 其他 workflow skill 调用; 用户认为 domain-awareness 适合当这个 skill. 用户指示: 落地执行不在盘问会话内, 可用子代理代工.

### F009 领域感知结果
- 状态: 当前有效
- 来源: 读 docs/language/UBIQUITOUS_LANGUAGE.md 与 docs/adr/ (0001-0006)
- 内容: 本仓库词汇表仅覆盖 present-web-server 域 (常驻展示服务/挂载目录/扁平并集/遮蔽/控制面/内容面/远程模式), ADR 均为其他主题; 无 workflow spec 域的领域约束.

### F010 skill 边界裁定 (用户陈述)
- 状态: 当前有效
- 来源: 用户陈述
- 内容: deliberate 不关心 spec 落盘, 保留自然语言盘问; 形式化语言落盘是 spec skill 要遵守的, 不是 deliberate; 调用脚本校验产物也不是 deliberate 要描述的行为; 注意 skill 之间边界, 行为应落在正确 skill 里, 不要溢出.
