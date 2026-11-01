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

- research (AFK): 委派子代理独立探索, 产出分析文件. **何时创建**: 决策在等一个藏在当前工作目录之外的事实 (文档, API, 知识库等), 须先暴露. 工作目录内的事实就地查, 不单立里程碑; 查影响面用 `blast-radius`, 查领域用 `domain-awareness`; 需要单独立项才查得清的内部调查通常说明里程碑划错了.
- demo (HITL): 调用 `demo` skill 制作演示材料, 提升讨论保真度; 是否造材料, 产物归属与保留规则都在该 skill 与 `software-engineering-consensus` 的 demo 词条. **何时创建**: 问题是 "它应该是什么样子, 如何运行", 或需要让人看清某个样子/行为/过程以便讨论时. 可交互有反馈的演示材料隐含着很多文字说不清楚的隐性知识信息, 你应该积极使用演示材料, 提高设计的清晰度.
- poc (AFK): 实验由你独立驱动, 不需要我在场. **何时创建**: 问题是某个技术方案能否做成, 需要真实实验才能判定. 拆分判据与归属: 一个结论能一次收口就一个里程碑; 出现多个可分别收口的结论才拆成多个, 用依赖串起来, 每个里程碑各收口一个结论; 单个结论跨多个会话时保持进行中继续推进, 不拆里程碑, 会话规模只作经验, 不作判据; 实质是交付产品代码的工作归 task. **完成标准**: 结论与依据已写进本里程碑自己的产物. **终止处置**: 未证实默认保持未完成; 只有我裁决终止时才把该里程碑记关闭, 关闭摘要写 "未证实即终止, 不构成可行性结论" 及原因, 并按裁决把它从终点验收的依赖里移除, 不记成歧路. "交付什么"的定义与 "未证实"的词义指向 `software-engineering-consensus` skill 的 PoC 词条, 本条目不复述可行/不可行结论与可复查依据的定义.
- deliberate (HITL): 调用 `deliberate` skill 盘问我, 固化决策. 调用时按 [产物结构](TEMPLATES.md) 指定产物根目录. **何时创建**: 需要决策, 且选项/取舍无法靠 research 暴露事实或无法靠演示提升保真度直接看清, 须逐条盘问我. 默认类型.
- task (AFK/HITL): AFK 非编码任务直接处理; AFK 编码任务则调用 `drive-execution` skill 来处理; HITL 需要我在场协作才能完成的操作. **何时创建**: 目的地要求实际完成的工作, 包括决策前疏通讨论的手工活, 决策后的实施与验证; 需要实测才能得出结论, 但结论是描述现状的工作也归 task, 例如压测现有链路或采性能基线.
- acceptance (HITL): 固定的终点前验收 Milestone, 先由你汇集别人已产出的证据, 后与我现场逐项确认. **何时创建**: 制图时创建, 不与普通 task 混用.

**完成标准**:

- research: 分析文件已写, Milestone 全部考察点已覆盖.
- deliberate: 盘问闭环; 决策已按需写入对应文件.
- demo: 演示已做, 我看过并能据此判断要讨论的事.
- poc: 结论与依据已写进本里程碑自己的产物.
- task: 工作已完成, 结果事实已记录.
- acceptance: 每项验收标准都有逐项证据且我已逐项确认通过, 才能关闭.

**收口产物**: research 分析文件; deliberate 决策/领域文档; demo 按它自己的规则管理产物, 拿已交付的成品或线上系统演示时产物可以为空, 关闭摘要记一行 "演示了什么, 看的是哪个版本"; poc 本里程碑的结论与依据; task 完成证据或代码提交; acceptance 验收报告和逐项证据. 产物链接写入 `milestones.<id>.artifacts`.

Milestone 详情 (标题/状态/类型/阻塞于/问题/产物/关闭摘要) 只存在于 ROADMAP.json 的 `milestones` 下, 不再有独立文件.

## 验收终点

验收只表示交付物满足确认过的判据; 判据能在真实入口重复执行时, 派 `verify-change` 按已确认 PRODUCT.md 执行, 否则由到达确认汇集他人已产出的证据并由我逐项确认.
每张 Roadmap 从制图起保留唯一的终点前 `acceptance` Milestone. 它依赖所有通往目的地的已知工作; 后续探明必要工作时追加依赖; 领取条件见 [航行步骤](reference/VOYAGE.md#航行步骤) 第 2 步. 验收最后关闭, 然后才能正式交付. 单会话无需制图时也须验收, 不能把没有路线图当成跳过确认的理由.
实施或产物定稿前按 [验收标准](ACCEPTANCE-GUIDE.md#验收标准) 与我对齐; 领取验收时按 [证据与确认](ACCEPTANCE-GUIDE.md#证据与确认) 只汇集别人已产出的证据, 不自己运行或制造, 再由我逐项确认. 关键结论缺证据且我尚未决定如何处理时, 暂停生成最终页面. 只有逐项确认通过才能关闭验收; 关闭摘要记录结果和报告路径.

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
