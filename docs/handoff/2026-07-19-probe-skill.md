# 交接: 创建 Probe Skill

## 必读推荐

- `docs/changes/probe-skill/PROBE.md` — Backlog 索引。目的地, 当前已关闭决策, 前沿列表, 迷雾, 范围外。
- `docs/changes/probe-skill/PROBE-01.md` — 当前前沿 Item (Research, AFK): 分析 wayfinder 中依赖 tracker 的机制点。
- `docs/changes/probe-skill/PROBE-02.md` — 阻塞 Item (Grilling, HITL): 确定 markdown 模板。
- `docs/changes/probe-skill/PROBE-03.md` — 阻塞 Item (Grilling, HITL): Probe SKILL.md 大纲。
- `docs/changes/probe-skill/HANDOVER.md` — 遍历操作指引: 加载/认领/解决/更新 Backlog 的步骤和规则。
- `../skills_from_mattpocock/skills/engineering/wayfinder/SKILL.md` — wayfinder 原始参考。PROBE-01 的分析对象。
- `/var/mnt/DATA/Workspace/skills/workflow/propose/SKILL.md` — propose skill。Probe 需与之衔接, 但修改 propose 在范围外。
- `/var/mnt/DATA/Workspace/skills/workflow/grilling/SKILL.md` — grilling skill。Probe 的 HITL Item (Grilling 类型) 会调用它。

## 路线图

**意图**: 博洛希望在其工作流 skill 体系中吸收 wayfinder 的核心能力 — 将超出一个 agent 会话容量的大块工作, 拆分为可独立解决的决策调查条目。

**里程碑**:

1. 博洛阅读了 wayfinder SKILL.md 和 grill-with-docs SKILL.md, 对比两者差异。
2. 博洛分析了 orchestrate 工作流体系, 确认 propose (深度优先, 单会话关闭决策) 和 wayfinder (广度优先, 跨会话拓扑管理) 是互补的。
3. 多次命名迭代 (Discovery → Inception → Spikes → Scout → Probe → 最终定名 **Probe**)。
4. 确定核心差异: wayfinder 贡献拓扑管理 (阻塞图/迷雾/并发认领/广度初扫), propose 贡献深度 (分支完成标准/认知校准/固化流程)。Probe = 焊接两者。
5. 决定用 wayfinder 自己的方法论来创建 Probe skill — 以 dogfooding 方式验证 wayfinder 是否值得借鉴。
6. 一轮广度优先盘问, 关闭 8 个决策: Item 类型保留全部四种; AFK agent 自闭环 / HITL 用户新会话; 两种模式保留; 自检放 Probe 自身; 命名简洁; 阻塞用文件头+Backlog 索引; 前沿由 Backlog 维护; 认领不需要。
7. 创建 Backlog (PROBE.md) 和 3 个 Item: `01 (AFK, 前沿) → 02 (HITL) → 03 (HITL)`, 落盘 `docs/changes/probe-skill/`。

**距离目的地**: 还有 3 个 Item 待解决, 阻塞链是线性的。最终产出是 `/workflow/probe/SKILL.md`。

## 当前认知上下文

- **未决迷雾**: (1) AFK 子代理结果解锁新 HITL item 时, 父会话如何感知和切换; (2) 遍历会话中吞吐量上限 — wayfinder 规定一次一个, 博洛期望 AFK 并行 + HITL 串行, 这个差异尚未调和。
- **已接受的不确定性**: Probe 的 markdown 模板细节 (PROBE-02 才确定); SKILL.md 最终结构和措辞 (PROBE-03 才确定)。
- **下一会话所需上下文**: 你是第一个遍历会话。只需解决 PROBE-01 (Research, AFK) — 读 wayfinder, 标注 tracker 依赖点, 给 markdown 替代方案。不需要和博洛交互。
