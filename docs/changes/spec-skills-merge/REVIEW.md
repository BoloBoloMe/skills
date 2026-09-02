# Spec Skills 合并与改名 审核报告

- 审核对象: 工作区未提交改动 (相对 HEAD). 任务指定基线 a1546a8, 实际 HEAD 为 6a3dea3 (同信息 commit, 疑 rebase/amend); 两 commit 差异仅 4 份 use-sandbox/handoff 文档, 与被审对象零交集, 故以 6a3dea3 为基等价.
- 审核方法: `git status` + `git diff HEAD` 全量逐行核对; 旧文件原文用 `git show HEAD:<路径>` 取出, 与新文件机械 diff; 全仓 grep 旧名 (排除 .git/__pycache__); 对照 docs/changes/spec-skills-merge/DECISIONS.md, general/writing-for-llm 三份文档, workflow/decision-ledger/SKILL.md.
- 证据分级: 通过 = 机械核对无差异; 建议 = 不阻塞但值得改; 可忽略 = 记录在案不影响合并.

## A. 正确性

### A1 to-spec/SKILL.md 模板与完成标准逐字保留 — 通过

- 方法: 用 sed 抽取新旧两份模板块 (`<product-spec-template>`/`<technical-spec-template>` 全块) 机械 diff, 退出码均 0, 零差异.
- Product 完成标准 5 条与 Technical 完成标准 1 行逐字保留 (workflow/to-spec/SKILL.md:56-61, :133).
- 允许的差异逐一核实且仅限: 共享前言上收 (ID 稳定连续/产物根目录/信源收集句, 原文 "收集 PRODUCT.md 需要的信息" 泛化为 "收集产物需要的信息"), 目标行信息以括号收编 ("产品结果基线, 供 LLM 与人共用"/"技术契约, 只供 LLM 使用"), GHERKIN.md 指针与 "使用下方模板" 两行次序对调 (语义不变), 收尾汇报行合并为 "已生成的路径, PRODUCT.md 机检执行结果 (未产 PRODUCT.md 时省略), ...", 新增产物语义段 (L9). 无其他语义丢失/改动/错别字.

### A2 check-ac.py 零改动 / GHERKIN.md 仅一处改名 — 通过

- 方法: `git diff HEAD --stat` 显示 check-ac.py 为纯 rename (0 行差异); GHERKIN.md 手工 diff 仅 L3 自指一行 `to-product-spec` -> `to-spec`, 其余 112 行零差异.

### A3 to-execution 改名仅 name 一处 — 通过

- 方法: `git show HEAD:workflow/to-execution-spec/SKILL.md` 与工作区文件手工 diff, 仅 L2 `name: to-execution-spec` -> `name: to-execution`; 正文 137 行零差异. 目录名与 frontmatter name 一致, `disable-model-invocation: true` 保留.

### A4 4 份存量文档正文零改动 — 通过

- 方法: `git diff HEAD` 逐份核对, 每份均只 +2 行 (注解一行 + 空行), 无任何正文删改. gherkin-ac/PRODUCT.md 的 gherkin 块未受波及 (diff 只落在文首).
- 注解自身: 3 份在标题后 L3, PROPOSAL.md 在 L8 (头部元信息列表之后, 第一个章节之前) — 位置略不一致但未损伤原文结构, 可忽略.

### A5 旧名残留范围 — 通过

- 方法: 全仓 `grep -rn "to-product-spec|to-technical-spec|to-execution-spec"` (排除 .git/__pycache__). 残留仅出现于: 4 份带注解存量文档, 新账本 docs/changes/spec-skills-merge/DECISIONS.md. workflow/, README.md, tests/, pi/ 配置均无残留. 旧目录 to-product-spec/to-technical-spec/to-execution-spec 已不存在 (`ls` 验证).
- 新名引用侧完整: 调用方仅 deliberate/SKILL.md:58 与 probe/TEMPLATES.md:57 两处, 均已更新; 全仓无其他引用点 (check-ac 引用 grep 亦确认无第三方).

### A6 frontmatter 与 description — 通过

- to-spec: name 与目录一致; description 一行摘要 ("将已确认产品方案整理为产品结果基线 Product Spec, 将已确认设计整理为 LLM 使用的 Technical Spec."), 无冒号; disable-model-invocation: true 保留. to-execution 同 (description 未动).

### A7 deliberate 与 to-spec 产物语义衔接 — 通过

- deliberate/SKILL.md:58 "已启用层面 (至少判定过一个问题归属的层面) 对应的 `to-spec` 产物" 与 to-spec/SKILL.md:9 "层面 = deliberate 中至少判定过一个问题归属的层面" 定义一致 (deliberate 侧省 "deliberate 中" 属自指省略, 非矛盾); deliberate L64 "已启用层面对应的 spec 内容无缺口" 同口径.

### A8 唯一建议修

- **建议**: workflow/to-spec/SKILL.md:11 输出行 "输出为 `<产物根目录>/PRODUCT.md` 与 `<产物根目录>/TECHNICAL.md`" 为无条件双产物表述, 与 L9 按已启用层面定产物的语义存在张力 — 单层面变更时 LLM 可能因 L11 的字面 "与" 而多产一份. L9 是定义且在先, 风险低, 但改法便宜: 改为 "输出为层面启用的产物 (`<产物根目录>/PRODUCT.md` 与/或 `<产物根目录>/TECHNICAL.md`)" 一类. 证据: L9 vs L11.
- 对比之下, 收尾汇报行 (L151) 已用 "(未产 PRODUCT.md 时省略)" 处理了同一分支, 说明该分支真实存在, L11 是唯一未覆盖它的行.

## B. writing-for-llm 符合性 (to-spec/SKILL.md, 新账本, 4 行注解)

- **紧凑空行纪律 — 通过**: to-spec/SKILL.md 空行仅出现在章节边界/正文块与模板块边界, 完成标准列表内无空行; 新账本与注解同.
- **叙述视角 — 通过**: agent = 你 (隐含于指令句), 用户 = 我 ("盘问我", "告诉我", "不让我阅读后确认"); 注解为史志体, 不涉视角.
- **引导词/否定/反向激活 — 通过**: 保留 *tracer bullet* 等已有引导词 (随迁正文); 合并后单 SKILL.md 不提及任何已删除 skill 名, 无反向激活诱因; 禁令 ("禁止目检替代脚本" 等) 均为随迁原句且配有正向目标 (以脚本结果为准).
- **空操作猎杀 — 通过**: 新增文本 (目标行/产物语义/汇报行) 每句都改变默认行为 ("未产 PRODUCT.md 时省略" 直接改变汇报行为), 未检出相对默认行为无变化的句子.
- **重复/单一真相源 — 通过**: 模板/完成标准各只剩一份副本 (上收消除了前言重复); GHERKIN.md 仍是 Gherkin 细节唯一来源, SKILL.md 只留指针; "已启用层面" 定义在 deliberate 与 to-spec 各出现一次, 语义一致且各自服务本地分支, 属可接受 (锚定 deliberate, 不构成同一意义两处漂移风险).
- **指针措辞 — 通过**: GHERKIN.md 指针 ("唯一来源... 书写 验收标准 节前必读") 与 check-ac.py 机检触发点均为强措辞; 注解行的账本指针给出完整可解析路径.
- **description 与命名 — 通过**: to-spec/to-execution 均小写 kebab-case, 是合并后主链短名, 属用户真会说的词 (D001 理由即源于 PROPOSAL 发现 8 的记忆负担); description 已剥触发词, 纯摘要.
- **术语表一致性 — 通过**: GLOSSARY.md 仅定义 LLM/harness 两词; 相关文档对 LLM 的使用与之一致, 未出现 "AI/模型" 别名.

## C. 新账本质量 (对照 workflow/decision-ledger/SKILL.md)

- **编号连续 — 通过**: D001-D003 连续, 分命名空间.
- **内容完整带理由 — 通过**: 三条决策均含完整内容与理由; D001 含三个已排除候选, D003 含一个; 均有预计影响与实际影响 (实现后补记已填).
- **可忽略**: D002 (改名) 无已排除候选 — 账本模板并不单列该字段, 且改名候选空间近空, 不构成违规.
- **模板吻合 — 通过**: 标题 "<feature 名称> 决策账本" 句式, 状态/约束性字段取值均在模板枚举内; 无事实可记, 省略 事实 节属合理.

## 总评

逐行机械核对全部通过: 模板与完成标准逐字保留, 随迁文件零/单行改动, 存量文档正文未动, 旧名残留范围与决策完全吻合, 新账本符合账本模板. 唯一实质发现是 to-spec/SKILL.md L11 无条件双产物表述与 L9 产物语义的措辞张力 (建议修, 一行可解), 其余两条可忽略级观察 (注解位置不一致, D002 无排除候选) 不影响合并.
