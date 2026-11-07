---
name: navigate
description: 模糊目的地的领航流程, 对齐目的地, 绘制路线图, 逐个里程碑航行.
disable-model-invocation: true
---

# 领航

开始前, 调用 `domain-awareness` skill 感知当前工作目录的领域模型.

## 使命

我的想法很模糊: 目的地还说不清, 实现路线也看不清, 前方还是未知海域.
你是领航员, 任务是 *把我带到目的地*. 你领航, 我随行: 旅程是我的, 有些航段只有我在场才能走过. 
领航按三段展开: 确定目的地, 与我对齐这次旅程要抵达哪里, 定义怎样算抵达; 制图, 画出 按阻塞关系组织的 Milestone 索引 Roadmap; 航行, 逐个关闭 Milestone, 经我验收通过后正式交付.
Navigate 不替我做产品决策, 只组织 Milestone 的调查, 决策, 实施与关闭流程; 验收通过前不得宣称抵达或正式交付.

## 未知海域

Roadmap 刻意不画满: 看不清的绝不硬画. 活跃 Milestone 之外全是未知海域: 隐约感到前面有决策等着, 但眼下问题未关, 形状无法确定. 每关一个 Milestone, 未知海域便探明一片, 露出可明确写出的新 Milestone; 步步推进, 直到目的地完全清晰.
ROADMAP.json 的 `unknown_seas` 字段 (字符串数组) 存的就是这些模糊视图 (疑似问题, 待回访区域): 在边界内, 但不够清晰, 尚不能写成 Milestone.
**未知海域还是 Milestone?** 只看现在能否精确说出问题是什么, 不看能否回答. 能说清 → 写成 Milestone, 哪怕仍被阻塞; 说不清 → 进 `unknown_seas` 字段. 禁止把未知海域预切成 Milestone 大小: 它粒度更粗, 前沿推到那里时, 一片海域可能裂成多个 Milestone, 也可能发现根本不是问题.
`unknown_seas` 不含已关闭决策, 活跃 Milestone 和歧路.

## 歧路

未知海域只向目的地聚拢. 目的地决定边界, 边界之外的工作即歧路, 主动排除, 它不是*未知海域*. 歧路永不转化, 除非重划目的地, 而那是新旅程.
发现某 Milestone 其实在目的地之外 (最初边界画错, 或被解决结果推出去) → 关掉它, 在 `off_course` 字段记一笔关闭原因 (`{what, reason}`); 不进已关闭决策: 划边界不是路线上的步骤.
旧 Roadmap 文件中的 "范围外" 区段即歧路, 对应现在的 `off_course` 字段, 历史产物同义读取.

## Milestone

每个 Milestone 非 HITL 即 AFK: HITL 必须与我现场来回对话才能关闭, 你替我作答即违规; AFK 由你独立驱动.

**种类**:

- research (AFK): 委派子代理独立探索, 产出分析文件. **何时创建**: 决策在等一个藏在当前工作目录之外的事实, 须先暴露. 工作目录内的事实就地查, 不单立里程碑; 查影响面用 `blast-radius`, 查领域用 `domain-awareness`; 需要单独立项才查得清的内部调查通常说明里程碑划错了.
- demo (HITL): 调用 `demo` skill 制作演示材料, 提升讨论保真度; 是否造材料, 产物归属与保留规则都在该 skill 与 `software-engineering-consensus` 的 demo 词条. **何时创建**: 问题是 "它应该是什么样子, 如何运行", 或需要让人看清某个样子/行为/过程以便讨论时. 可交互有反馈的演示材料隐含着很多文字说不清楚的隐性知识信息, 你应该积极使用演示材料, 提高设计的清晰度.
- poc (AFK): 实验由你独立驱动, 不需要我在场. **何时创建**: 问题是某个技术方案能否做成, 需要真实实验才能判定. 拆分判据与归属: 一个结论能一次收口就一个里程碑; 出现多个可分别收口的结论才拆成多个, 用依赖串起来, 每个里程碑各收口一个结论; 单个结论跨多个会话时保持进行中继续推进, 不拆里程碑, 会话规模只作经验, 不作判据; 实质是交付产品代码的工作归 implementation. **完成标准**: 结论与依据已写进本里程碑自己的产物. **终止处置**: 未证实默认保持未完成; 只有我裁决终止时才把该里程碑记关闭, 关闭摘要写 "未证实即终止, 不构成可行性结论" 及原因, 并按裁决把它从终点验收的依赖里移除, 不记成歧路. "交付什么"的定义与 "未证实"的词义指向 `software-engineering-consensus` skill 的 PoC 词条, 本条目不复述可行/不可行结论与可复查依据的定义.
- deliberate (HITL): 调用 `deliberate` skill 盘问我, 固化决策. 调用时按 [产物结构](TEMPLATES.md) 指定产物根目录. **何时创建**: 需要决策, 且选项/取舍无法靠 research 暴露事实或无法靠演示提升保真度直接看清, 须逐条盘问我. 默认类型.
- spec (HITL): 调用 `to-spec` skill, 把已确认的产品与技术决策整理为权威规格. **何时创建**: 决策已有依据, 需要交付供下游使用的 `PRODUCT.md` 与 `TECHNICAL.md`. 新的产品取舍仍交 deliberate, 不由规格整理代答.
- verification-plan (HITL): 调用 `verify-change` skill 的设计验证方案方式. **何时创建**: 已有已确认且足以设计验证的权威输入, 需要在实施前确认验证步骤与证据要求.
- execution-plan (AFK): 调用 `to-execution` skill, 交付执行拆分, 不开始实施. **何时创建**: 两份规格和已确认的验证方案齐备, 需要拆成可独立执行与验证的切片.
- implementation (AFK): 调用 `drive-execution` skill, 完成实施, 合并, 开发验证与代码评审及评审返工. **何时创建**: 已明确授权按执行拆分改变成品, 包括产品代码与配置, 不以是否写代码划分. 不包含成品独立验证.
- verification (AFK): 按 [独立验证与返工](reference/VERIFICATION.md) 另起未参与实现与修复的独立会话, 调用 `verify-change` skill 的执行验证方案方式. **何时创建**: 成品已提交, 验证方案已确认且仍适用, 需要对明确版本独立验证或复验. 只产结果和证据, 不修复产品, 不代我验收.
- task (AFK/HITL): 直接处理具体操作, 需要我现场协作时为 HITL. **何时创建**: 目的地要求的一次性操作, 如准备讨论材料, 取得授权, 准备数据, 手工操作或采现状基线. 规格整理, 验证方案, 执行拆分, 成品实施与独立验证分别用专门类型. 压测现有链路描述的是现状, 归 task 而非 poc; 临时写测量脚本不改变归属, 交付长期使用的测量功能则归 implementation.
- acceptance (HITL): 固定的终点前验收 Milestone, 用于按已确认判据与证据同我逐项确认是否接受交付. **何时创建**: 制图时创建, 不与普通 task 混用.

**完成标准**:

- research: 分析文件已写, Milestone 全部考察点已覆盖.
- deliberate: 盘问闭环; 决策已按需写入对应文件.
- demo: 演示已做, 我看过并能据此判断要讨论的事.
- poc: 结论与依据已写进本里程碑自己的产物.
- spec: 两份权威规格已交付, 验收标准已由我确认, 必要检查通过且无待裁决缺口.
- verification-plan: 固定修订号的 `VERIFICATION-PLAN.md` 已由我明确确认, 来源仍适用.
- execution-plan: `EXECUTION.md` 与 issues 齐备, 覆盖, 验证入口和依赖检查通过.
- implementation: 集成提交, issue 开发验证证据与评审结论齐备, 无未处理的实施问题或待裁决缺口; 不等待独立验证报告才收尾.
- verification: 报告绑定目标提交和方案修订号, 必验项逐项有结果与相应证据或明确缺口, 发现项已按 [独立验证与返工](reference/VERIFICATION.md) 分流; 报告完成不等于成品达标.
- task: 操作已完成, 结果事实与证据已记录.
- acceptance: 每项必验标准都有可复查证据且我已逐项确认通过, 并已按 [测试代码人工抽查验收](../verification-contract/reference/tests.md#测试代码人工抽查验收) 的适用分支完成单列核对, 才能关闭.

**收口产物**: research 分析文件; deliberate 决策/领域文档; demo 按它自己的规则管理产物, 拿已交付的成品或线上系统演示时产物可以为空, 关闭摘要记一行 "演示了什么, 看的是哪个版本"; poc 本里程碑的结论与依据; spec 两份权威规格; verification-plan 已确认的验证方案; execution-plan 执行拆分与 issues; implementation 集成提交, 开发证据与评审记录; verification 独立验证报告与原件; task 操作证据; acceptance 验收报告和逐项证据. 实际产物链接写入 `milestones.<id>.artifacts`, 不把预期文件当成已有产物.

Milestone 详情只存在于 ROADMAP.json 的 `milestones` 下, 不再有独立文件. 按交付结果选类型, 不把每个辅助 skill 都变成里程碑; 只画当前能精确表述的工作, 已有合格产物直接复用, 不强制每次走完整条链.

**输入与输出目录**: 每个里程碑记录 `inputs` (所需内容与可追溯来源) 和 `output_dir` (传给下游 skill 的产物根目录), 字段规则见 [产物结构](TEMPLATES.md). `blocked_by` 只表示等待谁完成, 不能代替输入清单. 同一交付单元的多个里程碑共用一个产物根目录, 不再按里程碑编号强制分目录; 不同交付单元可以不同. 无输入显式写 `[]`, 无独立产物目录写 `null` 并说明原因; 需要落盘的下游 skill 必须取得实际目录. 制图时可写预期输入, 领取时核实材料, 确认状态和适用版本, 缺失就受阻. 旧图缺这些字段时按实际材料补齐后再领取, 不猜来源或目录.

典型依赖为 `spec -> verification-plan -> execution-plan -> implementation -> verification -> acceptance`. 辅助准备, 领域感知与风险调查通常随所属里程碑进行, 只有存在可独立关闭的结果时才单立节点.

## 验收终点

验收是我依据已确认标准和对应证据决定是否接受交付. 验证报告和 Milestone 关闭都不能替代我的明确决定.

每张 Roadmap 从制图起保留唯一的终点前 `acceptance` Milestone. 它依赖所有通往目的地的已知必要工作; 后续探明必要工作时追加依赖. 其他必要工作完成, `unknown_seas` 已厘清, 验收标准已确认后, 才能领取验收; 具体条件见 [航行步骤](reference/VOYAGE.md#航行步骤) 第 2 步. 单会话无需制图时也须正式验收, 不能把没有路线图当成跳过确认的理由.

领取验收时, 按 [证据与确认](ACCEPTANCE-GUIDE.md#证据与确认) 向我逐项展示已确认标准及对应证据, 并记录我的明确决定. 你不替我判定是否接受; 证据缺失或必验项失败时, 验收不得关闭, 需要补工作时新增阻塞验收的工作 Milestone. 按 [测试代码人工抽查验收](../verification-contract/reference/tests.md#测试代码人工抽查验收) 的适用分支完成单列核对后, 且所有必验项均由我确认通过, 才能关闭验收并正式交付. 关键结论缺证据且我尚未决定如何处理时, 暂停生成最终页面; 关闭摘要记录我的决定和验收报告路径.

## 读写纪律

ROADMAP.json 的一切读写只经守门脚本 `<skill 目录>/scripts/roadmap.py` (`<skill 目录>` 指本 SKILL.md 所在目录, 不依赖 cwd), 三个操作:

- 读指定字段: `uv run python <skill 目录>/scripts/roadmap.py query <file> <path>`
- 写指定字段: `uv run python <skill 目录>/scripts/roadmap.py save <file> <path> <content>`
- 删除整个文件: `uv run python <skill 目录>/scripts/roadmap.py delete <file>`

`<file>` 指路线图文件 `docs/changes/<feature-slug>/roadmap/ROADMAP.json`. `<path>` 用点分隔, 数字段为数组下标, 下标等于数组长度即追加; 完整 path 语法与字段说明见 [产物结构](TEMPLATES.md). 脚本 stdout 输出单行 JSON, 退出码 0 成功 / 1 失败; 失败时读 `error` 字段修正后重试.

守门脚本是 JSON 正确性的守门员: 非法枚举值, 缺失必填字段, 坏引用, 越界下标都会被拦截并返回错误, 所以 ROADMAP.json 的内容一律经上面的脚本进出.

**旧格式重建**: 现场出现 `ROADMAP.md` 或 `MILESTONE-NN.md` (旧版路线图格式) 时, 用 read 工具读旧文件, 再经脚本把内容重建为 ROADMAP.json; 不提供迁移命令, 一次性重建即可. 旧格式的 "范围外" 区段重建为 `off_course`, "未决迷雾" 区段重建为 `unknown_seas`.

## 展示服务

展示页的常驻实例有固定身份: 运行时目录与端口由 `scripts/display_serve.sh` 写死, 网段经转发桥供浏览器长期轮询; 具体值用 `status` 查, 不在文档里复述. 只经该脚本管理: `ensure` 复原/拉起 (服务死了用它一条命令复原回固定地址, 桥零操作自愈), `status` 查看, `start`/`stop` 供复原与演练.
- 展示目录与端口归展示实例专属: 其他会话不在该目录运行 `web_server.py start/stop`, 不占用展示端口.
- **收工不 stop 展示服务**: 它服务浏览器的长期轮询, 停了页面即断; 会话收工清单不含它, 复原交给 `ensure`.
- 实验与测试用独立运行时目录 (`NAVIGATE_WEB_RUNTIME_DIR`) 与一次性端口 (`NAVIGATE_WEB_PORT` 或随机端口), 不碰展示目录与端口.

## 调用模式

- **制图**: 无 ROADMAP.json → 走 [制图 Roadmap](reference/MAPPING.md).
- **航行**: 已有 ROADMAP.json → 走 [航行 Roadmap](reference/VOYAGE.md).

制图和航行永不同会话进行.
