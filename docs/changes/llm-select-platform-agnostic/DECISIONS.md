# llm-select 平台无关重构 决策账本

## 决策

### D001 llm-select 平台无关: score.py 不读任何 agent 平台配置
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: llm-select 的 score.py 不再读取任何 agent 平台的配置 (pi 的 settings.json/auth.json/models-store.json/models.json/`PI_CODING_AGENT_DIR`), 只依赖 skill 自有的两份数据: 评分表 `llm-scores.json` (baseline + 各模型七维比率分) 与模型目录 `model-catalog.json` (cost/reasoning/thinking 支持档). 平台无关原则遵循 writing-for-llm 的环境无关要求 (路径/操作不写死平台, 用运行时解析). 理由: skill 要能跨平台复用, 不绑定 pi 特有能力; 候选/目录/凭证本质是平台相关的, skill 只读通用 schema 的自有数据.
- 依赖事实: F001, F002
- 预计影响: general/llm-select/score.py (数据源重写), general/llm-select/bootstrap.md, general/llm-select/SKILL.md
- 实际影响: general/llm-select/score.py; general/llm-select/bootstrap.md; general/llm-select/SKILL.md; tests/test_llm_select.py; ~/.agents/llm-select/model-catalog.json (运行时数据)

### D002 候选范围不写死, 交给调用方/LLM, 用 --scope 传入
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 候选范围 (scope) 不由 score.py 从平台配置推演, 缺省 = 评分表 models 的键; 传 `--scope` 时指定完整候选集 (glob, 空格/逗号分隔) 并替换缺省. 平台可用模型列表由调用方从各自平台的配置入口获取 (如 pi 读 settings.json 的 enabledModels / auth.json) 后传给 --scope. 理由: 不同 agent 平台候选差异大, 交给 LLM/调用方决定更通用; score.py 只做算分与渲染, 不承担平台推演.
- 预计影响: general/llm-select/score.py (resolve_scope, --scope), general/llm-select/SKILL.md
- 实际影响: general/llm-select/score.py; general/llm-select/SKILL.md
- 需要调整: (无 — 替换语义在实现与文档保持一致)

### D003 修一次做完全部审核发现 (高/中/级 bug + 平台无关)
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 一次完成平台无关重构与全部审核修复, 避免旧 schema 白改. 覆盖审核报告的 5 项高/中级 bug 与 6 项低级隐患, 外加零成本价格分封顶、bad-baseline 分流口径等.
- 预计影响: general/llm-select/score.py, bootstrap.md, SKILL.md, model-catalog-template.json (新增), tests/test_llm_select.py (新增)
- 实际影响: 见 D001/D002 实际影响, 且新增 model-catalog-template.json 与 tests/test_llm_select.py

### D004 免费模型价格分上封顶, 无效成本走 N/A
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 单位成本 (0.75×input + 0.25×output) 为 0 (cost 全零/免费) 的模型, 价格维上封顶分 PRICE_CAP=100 并标 [免费]; 单位成本缺失或无效 (无 input/output 或非数值) 的模型, 价格维置 N/A (走重归一化剔除). baseline 单位成本无效/免费时返回 None (bad-baseline). 理由: 旧逻辑把零成本模型价格分静默回落 1.0, 使免费模型在 cheap-batch 画像下排序被扭曲; kimi-coding/k3-256k 即如此 (本机已发生).
- 依赖事实: F003
- 预计影响: general/llm-select/score.py (unit_cost, price_scores, build_rows)
- 实际影响: general/llm-select/score.py

## 事实

### F001 平台无关前提
- 状态: 当前有效
- 来源: 用户陈述
- 内容: skill 要和具体平台无关 (writing-for-llm), 所有功能不能依赖 pi 特有的能力, 必须通用. 选型数据 (模型目录/价格/thinking 档) 本质平台相关, 由每台设备的 model-catalog.json 提供.

### F002 数据源指派
- 状态: 当前有效
- 来源: 用户陈述 (拍板 Q1=A)
- 内容: 采用彻底自持方案 — score.py 读 skill 自有的评分表 + model-catalog.json, 不再读任何平台配置/环境变量.

### F003 零成本价格 bug 实况
- 状态: 当前有效
- 来源: 子代理审核发现 + 本机验证
- 内容: kimi-coding/k3-256k 在 pi 配置中 cost 全为 0, 旧选型表显示 price 1 (与基准同价), 而它是 cheap-batch 画像 (price 权重 0.35) 下本应碾压级便宜的候选, 排序被扭曲.

### F004 审核发现清单
- 状态: 当前有效
- 来源: 子代理审核 (Standards 轴) + 复核
- 内容: 首轮审核提出 2 硬性 + 10 判断性发现, 复核子代理确认全部落实、无新违例, 结论可合入. 硬性: H1 (load_table 表非对象裸 traceback), H2 (resolve_scope 语义与文档分裂). 判断性: M1-M10 (措辞/去重/口径/孤儿链接/环境绑定测试等).
