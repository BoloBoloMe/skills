---
name: navigate
description: 当目的地说不清或实现路线未知时, 领航至目的地, 先制图, 再航行.
disable-model-invocation: true
---

开始前, 调用 `domain-awareness` skill 感知领域模型.

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

每个 Milestone 非 HITL 即 AFK: HITL 必须与我现场来回对话才能关闭, 代理替我作答即违规; AFK 由代理独立驱动.

**种类**:

- research (AFK): 委派子代理独立探索, 产出分析文件. **何时创建**: 决策在等一个藏在当前工作目录之外的事实 (文档, API, 知识库等), 须先暴露; 或等一个无处可查的结论, 须先做实验测出.
- prototype (HITL): 调用 `prototype` skill 与我做粗糙原型, 提升讨论保真度, 产出原型文件. **何时创建**: 问题是 "它应该是什么样子/如何运行" 时. 可交互有反馈的原型隐含着很多文字说不清楚的隐性知识信息, 你应该积极使用原型, 提高设计的清晰度.
- deliberate (HITL): 调用 `deliberate` skill 盘问我, 固化决策. 调用时按 [产物结构](TEMPLATES.md) 指定产物根目录. **何时创建**: 需要决策, 且选项/取舍无法靠 research 暴露事实或靠 prototype 提升保真度直接看清, 须逐条盘问我. 默认类型.
- task (AFK/HITL): AFK 非编码任务直接处理; AFK 编码任务则调用 `tdd-as-orchestra` skill 来处理; HITL 需要我在场协作才能完成的操作. **何时创建**: 目的地要求实际完成的工作, 包括决策前疏通讨论的手工活, 决策后的实施与验证.
- acceptance (HITL): 固定的终点前验收 Milestone, 先由代理汇集别人已产出的证据, 后与我现场逐项确认. **何时创建**: 制图时创建, 不与普通 task 混用.

**完成标准**:

- research: 分析文件已写, Milestone 全部考察点已覆盖.
- deliberate: 盘问闭环; 决策已按需写入对应文件.
- prototype: 原型文件已写, 足以支撑后续决策.
- task: 工作已完成, 结果事实已记录.
- acceptance: 每项验收标准都有逐项证据且我已逐项确认通过, 才能关闭.

Milestone 详情 (标题/状态/类型/阻塞于/问题/产物/关闭摘要) 只存在于 ROADMAP.json 的 `milestones` 下, 不再有独立文件.

## 验收终点

每张 Roadmap 从制图起保留唯一的终点前 `acceptance` Milestone. 它依赖所有通往目的地的已知工作; 后续探明必要工作时追加依赖, 在未知海域厘清前不提前领取. 验收最后关闭, 然后才能正式交付. 单会话无需制图时也须验收, 不能把没有路线图当成跳过确认的理由.
实施或产物定稿前按 [验收标准](ACCEPTANCE-GUIDE.md#验收标准) 与我对齐; 领取验收时按 [证据与确认](ACCEPTANCE-GUIDE.md#证据与确认) 只汇集别人已产出的证据, 不自己运行或制造, 再由我逐项确认. 关键结论缺证据且我尚未决定如何处理时, 暂停生成最终页面. 只有逐项确认通过才能关闭验收; 关闭摘要记录结果和报告路径.

## 读写纪律

ROADMAP.json 的一切读写只经守门脚本 `workflow/navigate/scripts/roadmap.py`, 三个操作:

- 读指定字段: `uv run python workflow/navigate/scripts/roadmap.py query <file> <path>`
- 写指定字段: `uv run python workflow/navigate/scripts/roadmap.py save <file> <path> <content>`
- 删除整个文件: `uv run python workflow/navigate/scripts/roadmap.py delete <file>`

`<file>` 指路线图文件 `docs/changes/<feature-slug>/roadmap/ROADMAP.json`. `<path>` 用点分隔, 数字段为数组下标, 下标等于数组长度即追加; 完整 path 语法与字段说明见 [产物结构](TEMPLATES.md). 脚本 stdout 输出单行 JSON, 退出码 0 成功 / 1 失败; 失败时读 `error` 字段修正后重试.

**明文禁令**: llm 禁用 read/write/edit 工具直接触碰 ROADMAP.json — 不得读取, 创建, 修改或删除该文件; 内容一律经上面的脚本进出. 脚本是 JSON 正确性的守门员: 非法枚举值, 缺失必填字段, 坏引用, 越界下标都会被拦截并返回错误.

**旧格式重建**: 现场出现 `ROADMAP.md` 或 `MILESTONE-NN.md` (旧版路线图格式) 时, 用 read 工具读旧文件, 再经脚本把内容重建为 ROADMAP.json; 不提供迁移命令, 一次性重建即可. 旧格式的 "范围外" 区段重建为 `off_course`, "未决迷雾" 区段重建为 `unknown_seas`.

## 调用模式

- **制图**: 无 ROADMAP.json → 走 [制图 Roadmap](#制图-roadmap).
- **航行**: 已有 ROADMAP.json → 走 [航行 Roadmap](#航行-roadmap).

制图和航行永不同会话进行.

## 制图 Roadmap

我带着想法进行调用.

1. **确定目的地. ** 与我敲定这次旅程最终要得到什么, 到哪一步才算完成 (包括是否需要实际实施), 必须是高清晰度目标; 不够清晰就调用 `grilling` skill 盘问我 `目标是什么`, 不深入 `如何做到` 的实现细节, 不使用 *反方攻击*, 直到目标清晰度足够为止. 向我展示你对目的地和完成边界的理解, 等待我确认. 逐项用例在细节明朗后按 [验收标准](ACCEPTANCE-GUIDE.md#验收标准) 确认, 此处不凭空预写.
   完成标准: 目的地及完成边界已被几句话高清晰度描述, 且我已确认.
2. **侦查方向. ** 从广度入手, 全面梳理: 不限单一方向, 辐射整个空间, 选定几个你认为最具价值的方向, 每个方向都派遣一名子代理研究可行性/成本/收益, 多个子代理时并行执行; 向我展示每个方向的研究结论, 每个方向都附上你的看法, 等待我选定方向. 我否决全部方向 → 回 step 1 重敲目的地. 各方向研究结论在 step 4 记入 ROADMAP.json 的 `notes`.
   完成标准: 每个方向都有明确的研究结论, 且我已选定方向.
3. **描绘边界. ** 在我选定的方向上, 找出所有待办事项和现在可采取的第一步. 若没发现任何未知海域, 则航路已清晰, 全程一次会话即可完成, 不需要地图: 停下来, 询问我希望如何继续; 继续时仍须在实施或产物定稿前确认验收标准, 并在正式交付前验收. 需要地图时, 即使验收细节尚待确定, 也已知必须有验收 Milestone.
   完成标准: 发现不需要地图; 或发现需要地图且至少一个工作 Milestone 可精确表述, 其余不确定项在 step 4 写入 `unknown_seas`.
4. **绘制地图. ** 经守门脚本把地图写入 ROADMAP.json: 顶层 `title`, `destination` (写明我确认的完成边界), `notes` (含被选方向结论与未选方向排除理由), `milestones` (每个里程碑经 `save <file> milestones.<id> <JSON对象>` 整体创建, 含 `title`/`type`/`question`, 需要阻塞时再 `save <file> milestones.<id>.blocked_by <JSON数组>`), `unknown_seas`, `off_course`. 同时创建固定的验收 Milestone, 并在其他已知工作建好后设置它的 `blocked_by`; 尚未明确的工作以后探明时再补阻塞, 不能因尚有未知海域就提前验收. 前沿, 已关闭决策, 阻塞关系均不落盘, 由上述数据推导, 见 [产物结构](TEMPLATES.md). 写完后起展示服务: `uv run python workflow/navigate/scripts/web_server.py start` 拿到 stdout 的 `url`, 把 `url` 拼上 `?roadmap=<ROADMAP.json 的绝对路径>` 交付给我, 由我在浏览器查看地图.
   完成标准: ROADMAP.json 已由脚本写入且 `query` 校验可读; 浏览器 URL 已交付.
5. **确认与修订. ** 等我在浏览器查看后表态. 有异议 → 经脚本修订对应字段 → 重新交付 URL 让我重看, 直到我确认. 我确认后才进入 step 6. 确认动作在落盘之后, 提交之前.
   完成标准: 我已明确确认地图.
6. **提交. ** 仅在 step 5 我已确认且工作目录被 git 管理时执行. 禁止提交无关改动. 提交信息使用实际路径: `doc: 绘制地图 docs/changes/<feature-slug>/roadmap`.
   完成标准: 已提交本次 ROADMAP.json; 或确认当前目录非 git 仓库/用户未确认/存在归属冲突而跳过提交, 且原因已告知我.
7. **停止. ** 制图独占一个会话, 禁止在本会话开始解决 Milestone.
   完成标准: 路线图已交付, 本会话没有领取 Milestone.

## 航行 Roadmap

我带着路线图进行调用. 始终用里程碑 id (形如 `milestone-01`) 指代 Milestone, 禁用裸编号. 每完成一轮 (单个 Milestone, 或一批并行的) 就停下来, 等待我的进一步提示.

### 航行步骤

1. **加载索引. ** 经 `query` 读取 `destination`, `notes`, `milestones`. 不展开 Milestone 正文细节. 核对已确认的完成边界及固定验收 Milestone; 旧图已有 `task` 型验收时, 经守门脚本将其 `type` 改为 `acceptance`, 不再新增一个; 旧图没有验收节点时, 先核实旧图的目的地与完成边界是否经我确认; 不清楚就先问我, 再补上验收节点并接入所有已知的必要工作, 然后领取前沿.
   完成标准: 已知当前目的地, 完成边界和前沿 (前沿 = 未关闭且 `blocked_by` 全部已关闭的里程碑, 由数据推导); 验收已在终点前.
2. **选前沿认领. ** 按顺序领取前沿的第一个 Milestone; 若前沿还有与它互相独立的 AFK Milestone, 一并领取: 独立即无阻塞关系, 不触碰同一文件, 这样的 AFK 工作串行排队纯属浪费, 并行是免费提速. 验收 Milestone 只有其他必要工作均完成, `unknown_seas` 已厘清且验收标准已确认时才能领取, 不能因阻塞列表暂时为空而提前领取. 每个领取的 Milestone 经 `save <file> milestones.<id>.status '"进行中"'` 标记认领.
   完成标准: 领取的 Milestone 状态均已改为进行中; 每个未领取的前沿 Milestone 都能说出原因 (HITL, 不独立, 或验收尚未具备开始条件).
3. **放大解决. ** 按 Milestone 类型分流, 需要时经 `query` 读取被阻塞者的上下文或已关闭 Milestone 的产物. 本轮领取了多个 → 每个 AFK Milestone 委派一名子代理同时开工; HITL 逐个与我进行. 验收按 [证据与确认](ACCEPTANCE-GUIDE.md#证据与确认) 先汇集别人已产出的证据, 后由我逐项确认, 未确认前保持进行中.
   完成标准见 [Milestone](#milestone).
4. **收口产物. ** 按 Milestone 类型确认产物归属: research 分析文件; deliberate 决策/领域文档; prototype 按它自己的规则管理产物; task 完成证据或代码提交; acceptance 验收报告和逐项证据. 产物链接经 `save <file> milestones.<id>.artifacts <JSON数组>` 记入 `artifacts`. 提交信息: 下游 skill 有规定则用其规定; 否则 `doc: <milestone-id> <产物简述>`.
   完成标准: 本 Milestone 产物已提交或已有可追溯链接; 无独立产物/非 git 仓库时已记录原因.
5. **记录关闭. ** `save <file> milestones.<id>.close_summary '"<摘要>"'` 写入关闭摘要 → `save <file> milestones.<id>.status '"已关闭"'`. 前沿随状态变化自动推导, 无需手工落盘.
   完成标准: 关闭摘要与状态已落地; 下一个 Milestone 可从前沿正确识别.
6. **探明海域. ** 解决结果探明了某片海域 → 经 `save <file> unknown_seas <更新后的JSON字符串数组>` 从未知海域移除, 并 `save <file> milestones.<new-id> <JSON对象>` 写成新 Milestone (需要阻塞时补 `blocked_by`), 将新 Milestone 加入验收的 `blocked_by`, 加入前沿; 发现 Milestone 在目的地之外 → 经 `save <file> off_course <更新后的JSON对象数组>` 划入歧路. 若新增工作或验收返工影响已进行中的验收, 保持验收未关闭, 补齐工作与证据后再请我确认.
   完成标准: `unknown_seas` 每项已判断; 该写成 Milestone 的已创建; 验收仍位于所有必要工作之后; 前沿和歧路已同步.
7. **提交路线图. ** 提交 ROADMAP.json. 提交信息: `doc: 更新路线图 <milestone-id>`; 批量并行时列出本轮全部里程碑 id.
   完成标准: Roadmap 变更已提交; 或确认非 git 仓库而跳过; 验收已关闭才正式交付, 否则停下等待下一轮.
