# workflow-stack-review milestone-06 决策账本

打包裁决三处流程接口的决策与事实. 编号沿用本仓库先例: 各里程碑账本独立命名空间, 本文件 D001 起, F001 起. milestone-01 账本仍是工程共识的权威来源, 本文件只记本里程碑裁决.

验收标准: ../ACCEPTANCE.md 的 AC-06-01 至 AC-06-08, 已经我逐项确认.

## 决策

### D001 实验边界收敛到 blast-radius
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: benchmark-checklist 与 blast-radius 各自的 "一次性实验的边界" 收敛为一处: 完整边界唯一维护在 blast-radius (它本就是调查方法源头, benchmark 已声明 "沿用 blast-radius 的证据级别与授权边界", 单向依赖 benchmark→blast 已存在). benchmark-checklist 删除重复的调查方法/授权边界条目, 改为指针, 只保留满足既有分界句 "只规定测量实验条件, 不重写调查方法" 的测量特有条款. 已否决收进 verification-contract/SAFETY.md: 实验边界一半不是安全语义 (非正式 TC 标记, 内部函数证明边界, 新正式测试交回流程), 塞进安全底线唯一维护处会混淆职责; 已否决保持两处只对齐措辞: 重复仍在, 将来还会漂移. 两份 reference/PROVENANCE.md 相关行同步, 不改历史决策原文.
- 依赖事实: F001, F002
- 预计影响: workflow/benchmark-checklist/SKILL.md, workflow/blast-radius/reference/PROVENANCE.md, workflow/benchmark-checklist/reference/PROVENANCE.md; 实施在 milestone-07

### D002 旧行为影响复查设门槛
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: drive-execution 的旧行为影响复查节点从每轮必做改为门槛触发. 免做条件: 整轮全部 issue 均为非行为改动或纯核验, 且评审起点到当前集成提交的差异不触碰共享接口/数据格式/跨模块路径. 免做时在 EXECUTION.md 执行记录留一行免做理由; 其余情况照做, IMPACT-REVIEW.md 只在实做轮产出. "节点顺序不可跳过" 措辞同步收窄为门槛命中时不可跳过. 门槛判定只用两个现成事实: issue 验证契约的类型声明与差异触碰面, 不引入 "受影响入口有无测试覆盖" 这类需再分析一轮才知的判据 (避免循环分析). 不整体删除节点: 每轮必做对纯文档/核验轮是空转, 但 issue 级验证契约罩不到声明外老行为的三个已知网眼 (未声明的老调用方无测试, 单 issue 检查全绿但集成组合坏, 新测试只锁新行为不锁旧行为), 影响复查是这三洞的专职网.
- 依赖事实: F003, F004
- 预计影响: workflow/drive-execution/SKILL.md; 约束 milestone-04 执行时的流程

### D003 IMPACT-REVIEW.md 读者定位为流程内 llm
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: IMPACT-REVIEW.md 是给流程内 llm 的工作文件, 不是给人的报告. 读者为 drive-execution 总指挥 (读后分流: 明确实现破坏拆返工 ISSUE, 此为现行机制非新增; 产品取舍报缺口交用户裁决) 与下一轮影响复查审核者 (核对上轮记录闭环, 这是 "保留每轮记录, 不覆盖旧轮次" 的用途). 明确不作为 code-review 或 verify-change 的输入判据: 它不是 spec, 混入 Spec 轴会污染判据来源; verify-change 全量验收不按风险裁剪, 调查报告混进验收材料有把已排除项当安全证明的漂移风险. 保留 "它是调查报告, 不新增产品判据". 用户可审计阅读, 但正文不承担给人看的定位. 术语用 drive-execution 既有角色名 总指挥/审核者, 用户口头 "指挥家/指挥会话" 正名为 总指挥, 不造新词.
- 依赖事实: F005, F006
- 预计影响: workflow/drive-execution/SKILL.md

### D004 验收统一口径, 单句边界落 navigate
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 验收只有一个含义: 交付物满足确认过的判据. 手段差异来自交付物形态而非验收含义: 判据能在真实入口重复执行的, 派 verify-change 按已确认 PRODUCT.md 执行 (重机制, 防作者自证); 不能的, 由到达确认 (navigate 的 acceptance 里程碑) 汇集他人已产出证据, 用户逐项确认. 落点: workflow/navigate/SKILL.md 验收终点节, 用单句可判真假边界表述, 按交付物类型枚举的写法禁止 (writing-for-llm 冗余枚举禁令, 用户点名适用). verify-change 不回指 navigate. 验收指南现有转正规则 (只有 ACCEPTANCE.md 时 verify-change 按输入缺口停下, 先把标准转正进 PRODUCT.md 再验收) 与口径一致, 不动. 不收 "验收" 词条: 统一口径在 skill 正文唯一维护, 词汇表再收一条即第二处同义文本, 正是本里程碑要消的冗余; 且收录门槛写明一眼自明的词不主动收录. 已否决废 ACCEPTANCE.md 一律 PRODUCT.md: 文本交付没有可实跑入口, 只能写文件内容断言, 等于换文件名而白背 gherkin 形式和用不上的多考生实跑机制.
- 依赖事实: F007, F008
- 预计影响: workflow/navigate/SKILL.md

### D005 调用边不做自动校验, 维护规则进 README 给维护者
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 不新增调用边校验测试. 理由: 自动从正文提取调用边已知脆弱 (引用/分工声明/重新派活按口径不是边, 自然语言分不清); 半自动 (人工清单+测试校验) 会使 milestone-07 变成编码任务, 按现行规则要先补 drive-execution 输入 (规格/EXECUTION/issues), 等于再造一个准备段; 调用边变化频率低且每次变更本就有非作者复核兜底. 维护规则落 README 调用关系口径行旁, 面向仓库维护者 (维护本仓库的 llm): 调用边变更时人工核对调用图与 skill 正文, 并经非作者复核. 规则不写入任何 skill 正文, software-engineering-consensus 不收 (它是词条库且要过收录门槛).
- 依赖事实: F009
- 预计影响: README.md

### D006 删除 general/grill-me
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 删除 general/grill-me/ 目录及 README 通用技能表对应行. 理由: 真实已安装 skills 本就没有 grill-me, 仓库留存是残留; 其功能 (domain-awareness + grilling 两调) 与 workflow/deliberate (同两调 + decision-ledger 落账 + opposing-viewpoint 反方) 重复, 无落盘的轻量场景由 grilling 直接覆盖; general 与 workflow 目录是分类不是分层, 反向调用本身不违规, 违规的是保留无效重复. 两份 PUBLIC 无引用, 历史决策文档 (docs/changes/上下文管理优化/DECISIONS.md) 按惯例不改.
- 依赖事实: F010
- 预计影响: general/grill-me/ (删除), README.md

## 事实

### F001 两节实验边界的重叠与既有分界
- 状态: 当前有效
- 来源: workflow/benchmark-checklist/SKILL.md 与 workflow/blast-radius/SKILL.md 本轮逐节核对
- 内容: 两节各 7-8 条, 约 6 条实质相同 (非正式 TC 标记与授权范围, 只动独立脚本与临时数据不改产品源码/测试/配置, 内部函数证明不等于成品入口, 改冻结目标停下报缺口, 新正式测试交回既有确认流程, 接缝由实现者决定). 差异: benchmark 版多 "停自己启动的后台进程并留数据留存位置" 一条. benchmark 版已含分界句 "影响调查的一次性证明脚本, 沿用 blast-radius 的证据级别与授权边界. 本节只规定测量实验条件, 不重写调查方法", 单向依赖 benchmark→blast 已存在; 安全部分两边均已是指向 verification-contract/SAFETY.md 的指针.

### F002 SAFETY.md 的职责边界
- 状态: 当前有效
- 来源: workflow/verification-contract/SAFETY.md 节标题 (环境/原始数据/写入与授权/删除与不可逆操作/脱敏/无人值守红线)
- 内容: SAFETY.md 收所有 skill 共用的安全要求. 实验边界中的授权/清理/数据保留语义已经由指针抵达, 无需搬移.

### F003 影响复查现行规则每轮必做
- 状态: 当前有效
- 来源: workflow/drive-execution/SKILL.md 执行循环
- 内容: 现行文本: 全部 ISSUES 合并且整体验证通过后, 双轴评审前, 派未参与实现与修复的审核者, 从评审起点到当前集成提交核对差异追查既有入口/调用方与旧行为; 共享接口/数据格式/跨模块路径变更调 blast-radius 深查; 报告写入 IMPACT-REVIEW.md 逐轮保留; 返工合并后对新集成提交重做. "节点顺序不可跳过. 旧行为影响复查与评审未收敛不核验" — 对任何类型的集成轮一律适用, 无门槛.

### F004 验证契约按类型强制, 但网由作者声明
- 状态: 当前有效
- 来源: workflow/verification-contract/SKILL.md 五类型定义
- 内容: 行为变更逐条真实运行承诺行为; 结构变更要求改前确定须保持的公开接口与旧行为并建立可重复检查, 前后对比, 类型检查 lint 不能单独证明行为未变; 缺陷修复要求红态出现与修复后同一检查通过. 验证契约 "只承担执行者自证". 网的内容由作者在拆分 issue 时声明, 罩不到声明范围外的老调用方, 集成组合效应与新测试不锁旧行为三种情况.

### F005 IMPACT-REVIEW.md 的唯一生产者与唯一提及处
- 状态: 当前有效
- 来源: 本轮 grep workflow/general/pi 全部 md
- 内容: 唯一生产者与唯一提及处是 workflow/drive-execution/SKILL.md 旧行为影响复查步骤. 自述 "它是调查报告, 不新增产品判据". code-review 的 Spec 轴判据来源按序查找 spec/issues 契约, 不含它; verify-change 判据只取已确认 PRODUCT.md, 全量必验清单不按风险裁剪.

### F006 drive-execution 的角色名
- 状态: 当前有效
- 来源: workflow/drive-execution/SKILL.md 分工节
- 内容: 角色名为 总指挥 (只分配任务, 不亲自写代码, 不亲自审核实现细节) 与 审核者 (审核他人劳动成果, 向总指挥反馈审核报告); 影响复查由未参与实现与修复的审核者执行. verify-change 另有 "验收指挥者" 称谓, 属另一 skill 的另一角色, 不混用.

### F007 两个验收机制的机制事实
- 状态: 当前有效
- 来源: workflow/verify-change/SKILL.md, workflow/navigate/SKILL.md, navigate 验收指南 (ACCEPTANCE-GUIDE.md)
- 内容: verify-change 是独立产品验收流程: 判据只认带确认标记 `<!-- confirmed-flow: vN -->` 的 PRODUCT.md, 全量抄场景为必验清单, 派非作者验收者实跑, 无 PRODUCT.md 按输入缺口停下. navigate 的 acceptance 里程碑不出题不派工, 汇集别人已产出证据交用户逐项确认. 验收指南已定: 证据由 verify-change 产出时判据只能是 PRODUCT.md, 只有 ACCEPTANCE.md 时先转正再验收; 出现 PRODUCT.md 后以它为准. 本次旅程无 PRODUCT.md 且 note-4 明确不验证模型遵从率, verify-change 对本旅程无从运行.

### F008 writing-for-llm 冗余枚举禁令
- 状态: 当前有效
- 来源: general/writing-for-llm/SKILL.md ## 冗余枚举
- 内容: 用一串括注例子替概括词界定外延是冗余枚举, 两头都坏 (概括词对未列项从不变准, 列出项意图降级成清单). 测试法: 逐个删掉括号里的项, 概括词含义不变即冗余; 删了含义就变是分支, 提到正文独立成条. 治法: 换边界清楚的词或动词短语, 必要时才用一个例子并写出理由; 目标是 `概括 (项/项/项)` → 一句能判真假的边界. 用户在 D004 裁决时点名适用, 本账本与 AC 按此自查.

### F009 调用边口径已认可但无校验
- 状态: 当前有效
- 来源: README.md 调用关系口径行 (AC-05-05 落地), 路线图 note-3
- 内容: 口径: 调用图只画执行调用; 权威引用, 分工声明, 条件引用产物, 重新派活不算调用边. 仓库当前无任何调用边校验测试.

### F010 grill-me 的现状与重复关系
- 状态: 当前有效
- 来源: general/grill-me/SKILL.md, workflow/deliberate/SKILL.md, 真实安装 skills 目录清单, 本轮 grep
- 内容: grill-me 全文一行: 调 domain-awareness 感知领域模型, 调 grilling 盘问; disable-model-invocation, 仅用户手动触发. deliberate 为同两调 + decision-ledger 落账 + 落盘后独立反方攻击. 真实已安装 skills 目录无 grill-me (有 grilling). 仓库引用仅 README 通用技能表一行与自身; 两份 PUBLIC 无引用; docs/changes/上下文管理优化/DECISIONS.md 有历史提及 (记录 "grill-me 不做任何委派"), 历史不改.
