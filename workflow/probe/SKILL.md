---
name: probe
description: 当任务超出单会话容量时, 绘制并遍历决策调查 Roadmap.
disable-model-invocation: true
---

开始前, 调用 `domain-awareness` skill 感知领域模型.
我有一个模糊的想法, 但体量太大了 — 一个 agent 会话装不下, 而且前方迷雾重重: 从这里到目的地的路径还看不清. 你要做的是找路, 不是直奔目的地.
Probe 把路径画成一张本地 markdown Roadmap — 按阻塞关系组织的决策调查索引, 指向逐个 Milestone. 你遍历 Roadmap, 逐个关闭 Milestone, 直到路线清晰. 不限领域.

## 规划, 而非执行

Probe 不直接产出决策 — 它组织 Milestone 的调查和关闭流程 (类型处理见下). Roadmap 清空时, 所有必要的调查, 决策, 原型和执行前置工作都已完成, 路径清晰.
`task` 是唯一涉及执行的 Milestone 类型, 但它不直接抵达目的地 — 只是搬开挡在决策前面的石头 (比如开通权限, 迁移数据, 看清 API 形状).

## 调用方式

两种模式:
**绘制 Roadmap**: 我带着模糊想法来. 自检 → 定目的地 → 广度扫描 → 创建 ROADMAP.md + MILESTONE-NN.md + 阻塞连线图.
**遍历 Roadmap**: 我带着 ROADMAP.md 来. 加载索引 → 按相位选前沿认领 → 按类型分流处理 → 记录关闭 → 转化迷雾 → 相位推进. 我不指定 Milestone 时, 按角色优先级 散雾 > HITL > 终端 选前沿.

绘制和遍历永远不在同一个会话中进行.

## 战争迷雾

Roadmap 刻意不画满 — 看不清的东西不要硬画. 活跃 Milestone 之外全是战争迷雾: 隐约感到前面还有决策等着, 但因为眼下的问题还没关, 它们的具体形状还无法确定. 每关一个 Milestone, 它前面的迷雾就退开一步, 露出可以明确写出来的新 Milestone. 一步一步推, 直到目的地完全清晰.
ROADMAP.md 的未决迷雾区段存的就是这些模糊视图 — 疑似的问题, 待回访的区域. 都在范围内, 只是不够清晰, 还不能写成 Milestone.
**怎么判断是迷雾还是 Milestone?** 看现在能不能精确说出问题是什么 — 不是看能不能回答. 能说清 → 写成 Milestone, 哪怕还被阻塞着. 说不清 → 放进未决迷雾. 别把迷雾预切成 Milestone 大小: 它的粒度更粗, 前沿推到那里时, 一块迷雾可能变成多个 Milestone, 也可能发现根本不是问题.
未决迷雾不含已关闭决策, 活跃 Milestone 和范围外.

## 范围外

迷雾只向目的地聚拢. 目的地决定了工作范围, 因此超出目的地的工作就超出了范围 — 主动排除, 它不是 *迷雾*. 范围外永不转化, 除非重新划定目的地, 而且那已经是新任务.
如果后来发现某个 Milestone 其实在目的地之外 (最初画错了范围, 或是某个解决结果把它推出去的), 就关掉它, 在范围外区段记一笔: 关掉的原因. 不放进已关闭决策 — 划范围不是路线上的步骤.

## 绘制 Roadmap

没有 ROADMAP.md 时走这条分支.

1. **确定目的地.** 跟我确定这次 Probe 最终要得到什么结果, 必须是一个高清晰度的目标, 如果你认为还不够清晰, 就设计问题盘问我, 直到你认为清晰度足够为止. 一次只问我一个问题, 并给出你的推荐答案, 一次问多条问题会让我眩晕.
   完成标准: 目的地已被几句话高清晰度地描述.
2. **描绘边界.** 再次进行全面梳理, 这次要从广度入手: 不要局限于某个单一方向, 而是要辐射整个空间, 找出所有待办事项以及现在可以采取的第一步. 如果这样一来没有发现任何迷雾, 说明通往目的地的道路已经清晰, 这意味着整个过程足够短, 一次会话即可完成, 那么你就不需要地图了, 停下来, 询问我希望如何继续.
   完成标准: 发现不需要地图, 或者发现需要地图且至少有一个 Milestone 可以精确表述; 其余不确定项已写入未决迷雾.
3. **绘制地图.** 调用 `adaptive-presentation` skill 用 HTML 的形式向我汇报 Roadmap. 路线, 目的地, 边界, 迷雾, 范围外, 里程碑... 它们很适合呈现在 "地图" 上. 大胆一点, 你可以真的画一张信息丰富的地图来呈现它们. 
   完成标准: 打开浏览器窗口展示 Roadmap HTML.
4. **落盘.** 询问我是否确认落盘, 我说 `是` → 按 [TEMPLATES.md](TEMPLATES.md) 创建 ROADMAP.md 和 MILESTONE-NN.md, 画阻塞连线图; 我说 `不`  → 等待我的下一步指示.
   完成标准: ROADMAP.md 六区段完整; 每个 Milestone 文件头三字段正确; 连线图反映阻塞关系; 前沿列表准确.
5. **停止.** 画地图是一整个会话的事, 别在这个会话里开始解决 Milestone.

## 遍历 Roadmap

已有 ROADMAP.md 时走这条分支. 始终用文件名指代 Milestone, 不用裸编号.

### 相位与角色

遍历按相位推进, 形态为轮次 `(散雾抽干 → HITL 连做)* → 准入 → 终端 AFK 抽干`. 准入是 HITL 性质的独立过渡相位, 承 HITL 启终端; 生成执行计划 (调 `to-execution-spec`) 与执行计划 (终端段调 `afk`) 必须在不同会话. 每个 Milestone 的相位角色在选前沿时从 (类型, 阻塞图) 派生, 不存字段:
- research → 散雾
- deliberate / prototype → HITL
- task (HITL 模式) → HITL
- task (AFK 模式) → 阻塞图中有下游依赖它, 或关闭会退迷雾 → 散雾; 否则 (spec-gated afk 编码, 无下游) → 终端; 意不定默认 散雾

散雾段 = AFK 散雾 (research + 有下游的 AFK task); HITL 段 = deliberate/prototype + HITL task; 准入段 = HITL 过渡 (为前沿所有终端 Milestone 生成 execution-spec, 见 [终端段准入](#终端段准入)); 终端段 = spec-gated 无下游 afk 编码 task (终端指轮次末位, 非抵达目的地). 角色随图变化自动重算 (转化迷雾给某 Milestone 挂新下游 → 终端降级散雾), 不影响已关闭的.

取舍依据: 散雾段前置 (多为 AFK research) 把藏在迷雾里的 HITL 尽早显形, 摊到我在场一次清掉, 避免我离场后被散雾结果召回.

### 遍历步骤

1. **加载索引.** 读取 ROADMAP.md 的目的地, 前沿列表, 阻塞连线图, 笔记. 不展开 Milestone 正文.
   完成标准: 已知当前目的地和前沿.
2. **选前沿认领.** 我指定了就用它 (跨相位 override); 没指定按角色优先级 散雾 > HITL > 终端 选. 散雾段: 认领前沿全部散雾, 并行派发子代理 (≤3); HITL 段: 认领前沿第一个 HITL; 终端段: 认领前沿第一个终端. 改文件头 `状态: 进行中`.
   完成标准: 当前相位的 Milestone 已认领.
3. **放大解决.** 按 Milestone 类型分流, 需要时读取被阻塞者的上下文或已关闭 Milestone 的产物.
   完成标准见 [Milestone 类型处理](#milestone-类型处理).
4. **记录关闭.** Milestone 文件头改 `状态: 已关闭` → ROADMAP 已关闭决策追加摘要+链接 → 更新前沿 → 更新连线图. deliberate 生成 spec 时, 链接须含产出的 `docs/changes/<feature-slug>/` 路径, 供终端段准入定位. 父会话只收摘要 + 产物链接 + 索引更新; 重上下文留在子代理产物文件, 父保持精瘦.
   完成标准: 所有文件更新已落地; 下一个 Milestone 可从前沿正确识别.
5. **转化迷雾.** 解决结果让某块迷雾变清晰了? 从迷雾移除, 写成 MILESTONE-NN.md, 加入前沿. 发现某个 Milestone 在目的地之外? 划入范围外. 给已存在 Milestone 挂了新下游 → 其角色按派生规则重算.
   完成标准: 未决迷雾每项已判断; 该转化的已创建 Milestone; 前沿和范围外已同步.
6. **相位推进.** 按当前相位决定下一步, 不逐个停:
   - 散雾段: 前沿仍有散雾 → 回 step 2 继续抽干; 散雾抽干 → 前沿有 HITL 则召唤我进 HITL 段, 前沿只剩终端则召唤我进准入段 (二者皆主动停).
   - HITL 段: 关一个后问我 "要继续吗". 是且前沿仍有 HITL → 回 step 2; 否 → 落盘停, 等我回来. HITL 抽干 → 进准入段.
   - 准入段: 执行 [终端段准入](#终端段准入); 完成后落盘停, 等我回来 — 终端段须在新会话重载执行 (生成计划与执行计划会话分离).
   - 终端段: 单 worker 逐个调用 `afk` skill, 前沿仍有终端 → 回 step 2 连做; 抽干 → 遍历结束.
   - 硬停 (任何相位): 关闭解锁了当前相位没预期的 HITL → 停, 召唤我开新一轮 HITL 段; 子代理不可恢复失败 → 停, 报告; 上下文预算阈值 → 落盘, 新会话重载继续.
   完成标准: 已按相位推进到下一认领, 或触发硬停落盘, 或遍历结束.

### 终端段准入

准入段在 HITL 抽干后执行一次 (若无终端 Milestone 则跳过, 遍历结束). 终端段内 `转化迷雾` 新造出终端编码 Milestone → 硬停落盘; 我回来后新开计划会话补跑本准入 (仅该 feature), 再落盘交新执行会话, 不在 AFK 中 grilling.

前提: 前沿终端 Milestone 都是 spec-gated afk 编码任务 (终端段定义), 其上游 deliberate 已关闭或 spec 现成.

1. 归组. 在会话中与我确认每个前沿终端 Milestone 对应的 feature 路径 (`docs/changes/<feature-slug>/`) — 候选含已关闭 deliberate 在 ROADMAP 记录的路径和现存 `docs/changes/*/` 目录. 一个终端 Milestone 对应一个 feature. 归不上的 (无对应 feature, 或对应 feature 缺 `PRODUCT.md`/`TECHNICAL.md`) 标为缺 spec.
2. 守底. 缺 spec 的终端 Milestone 不进终端段 — 报告缺口, 为其开 deliberate Milestone 回 HITL 段, 准入中止.
3. 生成执行计划 (HITL). 我仍在场, 按 feature 逐个调用 `to-execution-spec` skill (其 step 4 grilling 在会话中确认切片). 每个 feature 产出 `EXECUTION.md` + issues + `afk-running/` 步骤文件. `deliberate` 在 probe 内已跳过 `to-execution-spec`, 由本步骤接管.
4. 入索引. 把每个终端 Milestone → feature 路径的确认映射, 连同各 feature 的 `EXECUTION.md`/issues/`afk-running/` 路径, 记入 ROADMAP 笔记, 保持 ROADMAP 只做索引. 终端 Milestone 尚未关闭, 不写入已关闭决策.
5. 准入完成, 落盘. 终端段在新会话重载执行; 单 worker 逐个 Milestone 调 `afk` 时, 按 ROADMAP 笔记中的映射定位该 Milestone 所属 feature 的根目录 `afk-running/` (满足 `afk` 路径推断).

完成标准: 前沿每个终端 Milestone 所属 feature 的 execution-spec 产物齐备; ROADMAP 笔记已记映射与产物路径, 供新执行会话定位; 缺 spec 的已回 HITL; 准入会话与终端段执行会话分离.

### Milestone 类型处理

每个 Milestone 非 HITL 即 AFK: HITL 须经与我现场来回对话才能关闭, 代理不得替我作答 (盘问代理自问自答即违规); AFK 由代理独立驱动.

- **research** (AFK): 委派子代理独立探索, 产出分析文件. **何时创建**: 决策在等一个事实, 而该事实藏在当前工作目录之外 (文档, 第三方 API, 本地知识库等), 须先暴露出来.
- **deliberate** (HITL): 停止并请我调用 `deliberate` skill 盘问; 产出 spec + decisions + 领域模型 + ADR. **何时创建**: 默认情形 — 要敲定一个决策, 其选项/取舍无法单靠 research 暴露事实或靠 prototype 提升保真度直接看清, 须与我逐条盘问.
- **prototype** (HITL): 跟我协作做粗糙原型 — 大纲/草稿/桩代码, 提升讨论保真度. **何时创建**: 关键问题是 "它应该是什么样子" 或 "它应该如何运行", 靠语言说不清, 需要一个可反应的具体物件才能继续讨论.
- **task** (AFK/HITL): AFK 非编码任务委派子代理; AFK 编码任务见下; HITL 跟我协作. **何时创建**: 某件手工活必须在决策之前发生 — 无可决策/原型/研究, 但讨论被它卡住直到做完 (开通权限以判断 API, 迁移数据以看清形状). 唯一 "做" 而非 "决策" 的类型, 靠解锁决策而非抵达目的地立足.

**research 完成标准**: 分析文件已写, Milestone 中所有考察点已被覆盖.
**deliberate 完成标准**: deliberate 盘问闭环; 已确认决策已按需要写入 DECISIONS.md/领域语言/ADR; 如我选择生成 Spec, 对应 Spec 已落盘.
**prototype 完成标准**: 原型文件已写, 足以支撑后续决策.
**task 完成标准**: 工作已完成, 结果事实已记录 (凭证, URL, 行号等).

**task 的 AFK 编码分支**: 工作内容涉及编写/修改代码时, 必须调用 `afk` skill, 不得直接委派裸子代理写代码. `afk` 按已确认 Execution Spec 执行, 调用前须满足其触发门禁 (PRODUCT/TECHNICAL/EXECUTION/issue 已确认可读); 门禁不满足则不进入 AFK — 先补齐 Spec 或回退 HITL 与我协作. 跳过 `afk` 直接委派子代理属于违规, 即使代码能跑通也不算完成.

### 并发模型

散雾段并行, 上限 3 个. HITL 段一次一个. 准入段按 feature 逐个调 `to-execution-spec` (HITL). 终端段单 worker 逐个连做 (遵守 `afk` skill 单 worker 约束). 不设超时; 失败后最多重试一次, 仍失败触发硬停.

### AFK 到 HITL 切换

已并入相位推进 (step 6): research 解锁新 HITL 后, 散雾抽干再召唤我进 HITL 段, 不再逐个征询 "要在当前会话继续吗".

## 产物结构

完整模板见 [TEMPLATES.md](TEMPLATES.md). 概要:

- ROADMAP.md: 目的地 / 笔记 / 已关闭决策 / 前沿 / 未决迷雾 / 范围外 / 阻塞连线图. 它是索引 — 不复述 Milestone 详情, 只摘要+链接.
- MILESTONE-NN.md: 状态 / 类型 / 阻塞于 / 问题. 答案不写回 Milestone 正文 — 写入独立产物文件, 由 ROADMAP 已关闭决策链接.
