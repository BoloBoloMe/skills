# probe skill 术语从 Backlog/Item 改为 Roadmap/Milestone

probe skill 把大任务拆成一张本地 markdown 索引 + 逐个决策调查节点. 原术语 Backlog/Item 偏 agile 待办列表语义, 与该 skill "绘制并遍历从战争迷雾到目的地的路径" 的定位不符. 改为 Roadmap/Milestone, 对齐 "路线图 + 里程碑" 的找路隐喻.

改名映射 (保持原大小写风格):
- 概念: `Backlog`→`Roadmap`, `Item`→`Milestone`, `item`→`milestone`
- 文件标识符: `BACKLOG.md`→`ROADMAP.md`, `ITEM-NN.md`→`MILESTONE-NN.md`

范围: `workflow/probe/SKILL.md` + `workflow/probe/TEMPLATES.md` (同属 probe skill 契约, 半改会破坏内部一致性). `description` frontmatter 一并更新.

附带移除:
- `docs/changes/probe-skill/` — probe skill 的设计历史存档, 通篇用旧术语. 改名后成为旧术语孤儿; 其描述的设计推导已完成并固化进现行 SKILL.md/TEMPLATES.md, 保留只会制造新旧术语并存的困惑.
- `docs/handoff/2026-07-19-probe-skill.md` — 该历史目录的交接单, 是唯一引用源. 链接目标已删, 一并移除避免断链.

接受的影响: probe skill 的设计推导过程不再可追溯. 可接受, 因为推导结论已固化进 skill 本体, 历史存档的留存价值低于术语一致性带来的可读性收益.
