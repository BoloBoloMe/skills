# HILP 人类审核视图：从这里开始

这套规划协议用于把复杂变更放进“人先判断、agent 后执行”的流程。人类审核员不需要阅读机器字段；只需要沿着文档链接确认：目标是否明确、事实是否可靠、方案是否值得批准、蓝图是否可执行、交接是否安全。

阅读顺序：

1. [术语和阅读方式](01-glossary-and-reading.md)
2. [何时进入正式流程](02-when-to-use-hilp.md)
3. [需求事实与方案审批](03-requirements-and-design.md)
4. [实施蓝图与执行交接](04-blueprint-and-handoff.md)
5. [变更重审与归档](05-reapproval-and-archive.md)
6. [批准命令速查](06-approval-commands.md)

快速参考：[一页速查](99-canonical-summary.md)

下一页：[术语和阅读方式](01-glossary-and-reading.md)

## v2.24 审核辅助材料

- 设计批准前使用 [设计审批检查表](checklists/design-approval-checklist.md)。
- 蓝图批准前使用 [蓝图审批检查表](checklists/blueprint-approval-checklist.md)。
- 执行交接前使用 [交接审核检查表](checklists/handoff-review-checklist.md)。
- 想看端到端最小样例，阅读 [standard change 示例](../examples/minimal-standard-change/README.md)。


## 术语阅读约定

人类视图优先使用中文主名，并在首次出现时保留英文括注；agent schema 字段保持 canonical English。


## 审核员快速路径

从 [00-reviewer-decision-tree.md](00-reviewer-decision-tree.md) 开始判断本次应给出什么结论，然后只打开当前 review target 对应的检查表。
