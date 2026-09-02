# Spec Skills 合并与改名 决策账本

## 决策

### D001 to-product-spec 与 to-technical-spec 合并为 to-spec
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: workflow/to-product-spec 与 workflow/to-technical-spec 合并为 workflow/to-spec; GHERKIN.md 与 check-ac.py 随迁, 内容零改动 (仅 GHERKIN.md 自指一行改名). 产物语义: 按已启用层面 (deliberate 中至少判定过一个问题归属的层面) 确定产物 — 产品层面写 PRODUCT.md, 技术层面写 TECHNICAL.md; 两层皆启用或层面信息缺失时两份都写 (spec 是下游执行的权威输入, 缺一份执行链就缺信源); 调用方指明产物范围时从其指明. 载体: 单 SKILL.md 内嵌两份模板, 结构 = 共享前言 (domain-awareness/grilling/产物根目录/ID 稳定连续) + Product Spec 节 (模板 + GHERKIN.md 指针 + check-ac.py 机检完成标准) + Technical Spec 节 (模板 + 完成标准). 理由: 两 skill 共享前言与盘问入口, 分开要记两个仅中间词不同的名字 (skills-review-improvements/PROPOSAL.md 发现 8 的记忆负担), 合并后主链缩为 probe -> deliberate -> to-spec -> to-execution -> tdd-as-orchestra. 已排除候选: (a) 每次调用强制两份都写 — 单层面变更多产一份无读者产物; (b) 完全由调用方指名 — 把层面判定责任推给调用方, 与 deliberate 语义脱节; (c) 模板拆附属文件 — 两模板合计不足百行, 拆文件多一次跳转, 收益不抵成本.
- 预计影响: workflow/to-spec/ (新建), workflow/deliberate/SKILL.md (调用方), workflow/to-execution-spec (连带改名, 见 D002)
- 实际影响: workflow/to-spec/{SKILL.md,GHERKIN.md,check-ac.py}; workflow/deliberate/SKILL.md; workflow/to-product-spec/ 与 workflow/to-technical-spec/ 已删除

### D002 to-execution-spec 改名 to-execution
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: workflow/to-execution-spec 改名 workflow/to-execution, 仅目录名与 frontmatter name 变化, 正文不动. 理由: 与 D001 合并后的命名对齐 (to-spec/to-execution 短名), 降低记忆负担.
- 预计影响: workflow/to-execution-spec/, workflow/probe/TEMPLATES.md (调用方)
- 实际影响: workflow/to-execution/SKILL.md; workflow/probe/TEMPLATES.md

### D003 存量文档旧名引用加注解不改正文
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 引用旧名的 4 份存量文档 (docs/changes/gherkin-ac/DECISIONS.md, docs/changes/gherkin-ac/PRODUCT.md, docs/changes/handoff/2026-09-02-gherkin-ac-execution.md, docs/changes/skills-review-improvements/PROPOSAL.md) 文首加一行改名注解 (旧名 -> 新名映射 + 本账本指针), 正文一律不改. 理由: 这些是已关闭变更或带日期的时点快照, 正文是历史记录, 改写失真; 注解使旧名可解析到新位置. 已排除候选: 全量替换 — 决策账本的"预计影响"等历史行会成事后改写.
- 预计影响: 上述 4 份文档
- 实际影响: 上述 4 份文档文首注解
