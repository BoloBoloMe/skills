---
name: probe
description: 当任务超出单会话容量时, 绘制并遍历决策调查 Roadmap.
disable-model-invocation: true
---

开始前, 调用 `domain-awareness` skill 感知领域模型.

## 使命

我的想法庞大模糊, 单会话装不下, 前方迷雾重重. 你的任务是*寻路*, 不是直奔目的地: 先把路径画成 Roadmap — 按阻塞关系组织的 Milestone 索引 — 再遍历它, 逐个关闭 Milestone, 直到路线清晰.
Probe 不直接产出决策, 只组织 Milestone 的调查与关闭流程; Roadmap 清空时, 所有必要的调查, 决策, 原型和执行前置工作都已完成, 路径清晰.

## 两种模式

- **绘制**: 无 ROADMAP.md → 走 [绘制 Roadmap](#绘制-roadmap).
- **遍历**: 已有 ROADMAP.md → 走 [遍历 Roadmap](#遍历-roadmap).

绘制和遍历永不同会话进行.

## 战争迷雾

Roadmap 刻意不画满 — 看不清的绝不硬画. 活跃 Milestone 之外全是战争迷雾: 隐约感到前面有决策等着, 但眼下问题未关, 形状无法确定. 每关一个 Milestone, 迷雾退一步, 露出可明确写出的新 Milestone; 步步推进, 直到目的地完全清晰.
ROADMAP.md 的未决迷雾区段存的就是这些模糊视图 — 疑似问题, 待回访区域: 在范围内, 但不够清晰, 尚不能写成 Milestone.
**迷雾还是 Milestone?** 只看现在能否精确说出问题是什么 — 不看能否回答. 能说清 → 写成 Milestone, 哪怕仍被阻塞; 说不清 → 进未决迷雾. 禁止把迷雾预切成 Milestone 大小: 它粒度更粗, 前沿推到那里时, 一块迷雾可能裂成多个 Milestone, 也可能发现根本不是问题.
未决迷雾不含已关闭决策, 活跃 Milestone 和范围外.

## 范围外

迷雾只向目的地聚拢. 目的地决定范围, 超出目的地的工作即范围外 — 主动排除, 它不是*迷雾*. 范围外永不转化, 除非重划目的地, 而那是新任务.
发现某 Milestone 其实在目的地之外 (最初范围画错, 或被解决结果推出去) → 关掉它, 在范围外区段记一笔关闭原因; 不进已关闭决策 — 划范围不是路线上的步骤.

## Milestone

每个 Milestone 非 HITL 即 AFK: HITL 必须与我现场来回对话才能关闭, 代理替我作答即违规; AFK 由代理独立驱动.

**种类**:
- research (AFK): 委派子代理独立探索, 产出分析文件. **何时创建**: 决策在等一个藏在当前工作目录之外的事实 (文档, 第三方 API, 本地知识库等), 须先暴露.
- deliberate (HITL): 调用 `deliberate` skill 盘问我, 固化决策. **何时创建**: 默认情形 — 决策的选项/取舍无法靠 research 暴露事实或靠 prototype 提升保真度直接看清, 须逐条盘问. 决策域含高风险全新 module/interface 形状且无实现知识支撑时, 先立 spike 型 task 阻塞本 Milestone — 立 Milestone 时不知届时是否选 HILT, 故按形状风险判断, 不以 HILT 为条件.
- prototype (HITL): 调用 `prototype` skill 与我做粗糙原型, 提升讨论保真度, 产出原型文件. **何时创建**: 关键问题是 "它应该是什么样子/如何运行", 语言说不清, 需要可反应的具体物件才能继续讨论.
- task (AFK/HITL): AFK 非编码任务委派子代理; AFK 编码见下; HITL 与我协作. **何时创建**: 必须在决策前完成的手工活 — 无需决策/原型/研究, 但讨论在它完成前被卡住. 唯一 "做" 而非 "决策" 的类型, 靠解锁决策立足, 不直接抵达目的地 — 只搬开挡在决策前的石头 (开通权限, 迁移数据, 看清 API 形状).

**完成标准**:
- research: 分析文件已写, Milestone 全部考察点已覆盖.
- deliberate: 盘问闭环; 决策已按需写入对应文件; 我选择生成 Spec 时, Spec 已落盘.
- prototype: 原型文件已写, 足以支撑后续决策.
- task: 工作已完成, 结果事实已记录.

**task 的 AFK 编码分支**: 涉及编写/修改代码时, 必须调用 `afk` skill, 禁止委派裸子代理写代码 — 即使代码跑通也不算完成. `afk` 按已确认 Execution Spec 执行, 调用前须过其触发门禁 (PRODUCT/TECHNICAL/EXECUTION/issue 已确认可读); 门禁不满足则不进 AFK — 先补齐 Spec 或回退 HITL 与我协作.

## 绘制 Roadmap

1. **确定目的地.** 与我敲定这次 Probe 最终要得到什么, 必须是高清晰度目标; 不够清晰就设计问题盘问我, 直到清晰度足够. 一次只问一个问题并给出推荐答案 — 一次问多条会让我眩晕.
   完成标准: 目的地已被几句话高清晰度描述.
2. **描绘边界.** 全面梳理, 从广度入手: 不限单一方向, 辐射整个空间, 找出所有待办事项和现在可采取的第一步. 若没发现任何迷雾, 则道路已清晰, 全程一次会话即可完成, 不需要地图 — 停下来, 询问我希望如何继续.
   完成标准: 发现不需要地图; 或发现需要地图且至少一个 Milestone 可精确表述, 其余不确定项已写入未决迷雾.
3. **绘制地图.** 调用 `adaptive-presentation` skill 用 HTML 向我汇报 Roadmap. 路线, 目的地, 边界, 迷雾, 范围外, 里程碑都适合呈现在 "地图" 上 — 大胆画一张信息丰富的真地图.
   完成标准: 浏览器窗口已打开展示 Roadmap HTML.
4. **落盘.** 询问我是否确认落盘: `是` → 按 [TEMPLATES.md](TEMPLATES.md) 创建 ROADMAP.md 和 MILESTONE-NN.md, 画阻塞连线图; `不` → 等待我的下一步指示.
   完成标准: ROADMAP.md 六区段完整; 每个 Milestone 文件头三字段正确; 连线图反映阻塞关系; 前沿列表准确.
5. **停止.** 绘制独占一个会话, 禁止在本会话开始解决 Milestone.

## 遍历 Roadmap

始终用文件名指代 Milestone, 禁用裸编号.

### 相位与角色

遍历按相位推进, 形态为轮次 `(散雾抽干 → HITL 连做)* → 准入 → 终端 AFK 抽干`. *准入*是 HITL 性质的独立过渡相位; 生成执行计划 (调 `to-execution-spec` skill) 与执行计划 (调 `afk` skill) 必须分属不同会话. 每个 Milestone 的相位角色在选前沿时从 (类型, 阻塞图) 派生, 不存字段:

- research → 散雾
- deliberate / prototype → HITL
- task (HITL 模式) → HITL
- task (AFK 模式) → 有下游依赖或关闭会退迷雾 → 散雾; 否则 (spec-gated afk 编码, 无下游) → 终端; 意不定默认散雾

散雾段 = research + 有下游的 AFK task; HITL 段 = deliberate/prototype + HITL task; 准入段 = HITL 过渡, 为前沿所有终端 Milestone 生成 execution-spec, 见 [终端段准入](#终端段准入); 终端段 = spec-gated 无下游 afk 编码 task (终端指轮次末位, 非抵达目的地).
角色随图变化自动重算 (转化迷雾挂新下游 → 终端降级散雾), 不影响已关闭的.

### 遍历步骤

1. **加载索引.** 读取 ROADMAP.md 的目的地, 前沿列表, 阻塞连线图, 笔记. 不展开 Milestone 正文.
   完成标准: 已知当前目的地和前沿.
2. **选前沿认领.** 我指定了就用它 (跨相位 override); 未指定按角色优先级 散雾 > HITL > 终端 选. 散雾段认领前沿全部散雾并行派发子代理; HITL 段认领第一个 HITL; 终端段认领第一个终端. 改文件头 `状态: 进行中`.
   完成标准: 当前相位的 Milestone 已认领.
3. **放大解决.** 按 Milestone 类型分流, 需要时读取被阻塞者的上下文或已关闭 Milestone 的产物.
   完成标准见 [Milestone](#milestone).
4. **记录关闭.** Milestone 文件头改 `状态: 已关闭` → ROADMAP 已关闭决策追加摘要+链接 → 更新前沿 → 更新连线图. deliberate 生成 spec 时, 链接须含产出的 `docs/changes/<feature-slug>/` 路径, 供终端段准入定位. 父会话只收摘要+产物链接+索引更新, 重上下文留在子代理产物文件, 父保持精瘦. 终端 Milestone 关闭时, 摘要须列出其 feature 的 `afk-running/final-report.md` 中的实现发现和重构候选, 供我判断是否按 step 5 转化为新 Milestone.
   完成标准: 所有文件更新已落地; 下一个 Milestone 可从前沿正确识别.
5. **转化迷雾.** 解决结果让某块迷雾变清晰 → 从迷雾移除, 写成 MILESTONE-NN.md, 加入前沿; 发现 Milestone 在目的地之外 → 划入范围外.
   完成标准: 未决迷雾每项已判断; 该转化的已创建; 前沿和范围外已同步.
6. **相位推进.** 按当前相位决定下一步, 不逐个停:
   - 散雾段: 前沿仍有散雾 → 回 step 2 继续抽干; 抽干 → 前沿有 HITL 则召唤我进 HITL 段, 只剩终端则召唤我进准入段 (二者皆主动停).
   - HITL 段: 关一个后问我 "要继续吗". 是且前沿仍有 HITL → 回 step 2; 否 → 落盘停, 等我回来. 抽干 → 进准入段.
   - 准入段: 执行 [终端段准入](#终端段准入); 完成后落盘停, 等我回来 — 终端段须在新会话重载执行.
   - 终端段: 单 worker 逐个调 `afk` skill, 前沿仍有终端 → 回 step 2 连做; 抽干 → 遍历结束.
   - 硬停 (任何相位): 关闭解锁了当前相位未预期的 HITL → 停, 召唤我开新一轮 HITL 段; 子代理不可恢复失败 → 停, 报告; 上下文预算阈值 → 落盘, 新会话重载继续.
   完成标准: 已推进到下一认领, 或触发硬停落盘, 或遍历结束.

### 终端段准入

HITL 抽干后执行一次; 无终端 Milestone 则跳过, 遍历结束. 终端段内 `转化迷雾` 新造终端编码 Milestone → 硬停落盘; 我回来后新开计划会话补跑本准入 (仅该 feature), 再落盘交新执行会话, 不在 AFK 中 grilling.
前提: 前沿终端 Milestone 都是 spec-gated afk 编码任务, 其上游 deliberate 已关闭或 spec 现成.

1. 归组. 与我确认每个前沿终端 Milestone 对应的 feature 路径 (`docs/changes/<feature-slug>/`) — 候选含已关闭 deliberate 在 ROADMAP 记录的路径和现存 `docs/changes/*/` 目录. 一个终端 Milestone 对应一个 feature. 归不上的 (无对应 feature, 或对应 feature 缺 `PRODUCT.md`/`TECHNICAL.md`) 标为缺 spec.
2. 守底. 缺 spec 的终端 Milestone 不进终端段 — 报告缺口, 为其开 deliberate Milestone 回 HITL 段, 准入中止.
3. 探针判断. 对每个归上的 feature: 涉及全新 module/interface 形状且其 deliberate 未选 HILT 时, 说明接口在零实现知识下被冻结的风险, 建议先回 HITL 段开 spike 型 task Milestone (一次性探针代码, 产物: 接口草图+测试清单候选). 我采纳 → 登记入前沿, 本 feature 准入中止, spike 关闭后重跑本准入 (仅该 feature); 我跳过 → 继续, 在 ROADMAP 笔记记录知情跳过. 形状已由 HILT, 既有代码, 机器契约或 spike 产物支撑 → 直接继续, 不建议.
4. 生成执行计划 (HITL). 我仍在场, 按 feature 逐个调 `to-execution-spec` skill (其 step 4 grilling 在会话中确认切片数量上限, 首 issue, 粗轮廓和重切授权边界; 后续 issue 由 afk 在授权内随实现物化). 每个 feature 产出 `EXECUTION.md` + 首 issue + `afk-running/` 步骤文件. `deliberate` 在 probe 内已跳过 `to-execution-spec`, 由本步骤接管.
5. 入索引. 把每个终端 Milestone → feature 路径的确认映射, 连同各 feature 的 `EXECUTION.md`/issues/`afk-running/` 路径, 记入 ROADMAP 笔记, 保持 ROADMAP 只做索引. 终端 Milestone 尚未关闭, 不写入已关闭决策.
6. 落盘. 终端段在新会话重载执行; 单 worker 逐个 Milestone 调 `afk` 时, 按 ROADMAP 笔记映射定位该 Milestone 所属 feature 根目录的 `afk-running/` (满足 `afk` 路径推断).

完成标准: 前沿每个终端 Milestone 所属 feature 的 execution-spec 产物齐备; ROADMAP 笔记已记映射与产物路径, 供新执行会话定位; 缺 spec 的已回 HITL; 需 spike 的已回 HITL 或已记录知情跳过; 准入会话与终端段执行会话分离.

### 并发模型

散雾段并行, 上限 5. HITL 段一次一个. 准入段按 feature 逐个调 `to-execution-spec` (HITL). 终端段单 worker 逐个连做, 遵守 `afk` skill 单 worker 约束; 不设超时, 失败后最多重试一次, 仍失败触发硬停.

## 产物结构

模板见 [TEMPLATES.md](TEMPLATES.md). ROADMAP.md 是索引 — 不复述 Milestone 详情, 只摘要+链接; 答案不写回 Milestone 正文, 写入独立产物文件, 由已关闭决策链接.
