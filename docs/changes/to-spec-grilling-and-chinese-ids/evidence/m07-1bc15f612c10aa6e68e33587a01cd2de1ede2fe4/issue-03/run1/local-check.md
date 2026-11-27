# ISSUE-03 局部核对

按工单验证入口 1-3, 阅读实际候选段落, 用改前/改后差异核对保留项. 只以 `docs/changes/to-spec-grilling-and-chinese-ids/` 下的 `PRODUCT.md`, `TECHNICAL.md`, `VERIFICATION-PLAN.md` v3 为标准. 三份文件实测 SHA256 与 `EXECUTION.md:4-6` 一致, 见 `scope.log`. `DECISIONS.md:318-334` 仅用于了解本变更的取证安排. 候选位置相对仓库根. `candidate.patch` 保留局部条文原件差异.

| 项目和固定来源 | 候选位置 | 预期 | 实际与判断 |
| --- | --- | --- | --- |
| 入口1, 验收25 场景1: `PRODUCT.md:262-266`, `TECHNICAL.md:15-23,46-54,77-84`, `VERIFICATION-PLAN.md:96` | `workflow/navigate/SKILL.md:41,55,73-79`, `workflow/navigate/ACCEPTANCE-GUIDE.md:5-10,18-27`, `README.md:50,65` | 规格内盘问, 明确结束确认内容再写稿, 产品机械转正/技术机械复制, 无逐版读稿或读成文 Gherkin 的要求, 终点另验收. | 局部符合. navigate 把缺决定留在规格盘问, 两份正式规格经机检和独立检查后整组交付; 指南用正式产品判据, 不以草稿为确认入口. 终点仍由用户逐项按证据决定. |
| 入口1, 验收25 场景2: `PRODUCT.md:268-272`, `TECHNICAL.md:5,11,84`, `VERIFICATION-PLAN.md:97` | `workflow/deliberate/SKILL.md:9-18`, `workflow/navigate/SKILL.md:40-41,52`, `workflow/to-execution/SKILL.md:15`, `README.md:45,65` | 非 to-spec 调用者仍可独立调用 deliberate, 不把新规格流程反向替换进 deliberate, 四步不变. | 局部符合. deliberate 的盘问 -> 落盘 -> 反方攻击 -> 核实并收敛四步无差异. navigate 独立里程碑的执行调用与完成标准未改, to-execution 既有调用未改, README 保留独立入口. 仅核对本分支; 不提前核实 ISSUE-01 修改后的材料引用. |
| 入口2, 验收41: `PRODUCT.md:45,48,422-431`, `TECHNICAL.md:9,23-36,62-69,84`, `VERIFICATION-PLAN.md:23-25,123-124` | `workflow/navigate/SKILL.md:41-42,55-56`, `workflow/navigate/ACCEPTANCE-GUIDE.md:8,12-16`, `README.md:41,50-51,65` | 先确认权威输入, 再按方法盘问确认验证方案, 明确结束才成文, 独立检查后交付; 不要求整份阅读采纳. | 局部符合. 三文件共同明确先规格后方案, 用户明确结束的是方案盘问, 不拿规格确认或写完方案冒充本阶段确认. 未新增强制逐版或整份审阅. |
| 入口2, 验收41: `PRODUCT.md:47,367-379,427-431`, `TECHNICAL.md:34-36,64,84`, `VERIFICATION-PLAN.md:25,114-115,124` | `workflow/navigate/SKILL.md:56,71`, `workflow/navigate/ACCEPTANCE-GUIDE.md:14`, `README.md:67` | 执行/复验核实实际方案与来源, 按变化更新, 只补问新增或改变的验证决定, 有依据的转述错误修文并独立复查; 递增版本并追溯确认, 新轮绑定方案修订号和目标提交. | 局部符合. 三文件的复验说明不引入整份重确认; navigate 完成标准明确追溯来源/版本/确认/独立复查, navigate 与 README 明确新轮绑定. |
| 入口2, 验收边界: `PRODUCT.md:36,45,422-426`, `TECHNICAL.md:23,83-84`, `VERIFICATION-PLAN.md:123-124` | `workflow/navigate/SKILL.md:73-79`, `workflow/navigate/ACCEPTANCE-GUIDE.md:16,18-27`, `README.md:67` | 用户依已确认标准和对应证据逐项决定终点验收; 规格或方案确认, 代理检查和报告不能代替验收; 不泛化本变更的人工作业. | 局部符合. 原终点逐项确认、缺证或失败不关闭的规则保留, 三文件无用户审改等待, 里程碑通知放行或新增普遍强制条件. |
| 入口3, 规则11与范围: `PRODUCT.md:39,44`, `TECHNICAL.md:11,62-69`, `VERIFICATION-PLAN.md:127,129` | `candidate.patch`, `scope.log` | 产品修改仅限三个仓库内调用说明, deliberate/历史引用/既有依赖和服务不改. | 局部符合. 本任务无安装目录写入, 无新服务或依赖. 安装目录的全轮前后摘要和历史范围审计由父级补证, 本记录不声称观察了全部时段. |

## 待交接与边界

- `EXECUTION.md:36,46,75`: 全部切片合并后才交叉核对真实的 to-spec, verify-change, navigate, ACCEPTANCE-GUIDE 与 README. 非作者通读 README 完整相关调用段及相邻说明, 记录位置, 依据, 结论和未覆盖范围. 最终结果补回 `EXECUTION.md:15-16` 执行记录. 本 issue 不执行或等待此检查.
- 旧 `workflow/to-spec/SKILL.md` 和 `workflow/verify-change/SKILL.md` 仅作改前背景, 不按它们判断候选, 不声称与 ISSUE-01/02 一致. 未跑真实需求, 未做成品独立验证或用户验收, 未运行父级全量测试.
- 实际分支起点 `775b5a24cc06bea1ea719d78079e1e832ae2459a` 是 `EXECUTION.md:11` 记载起点 `9e8dd1dfe92b3b446c88c2cb8fce33cb0c67a77a` 的直接后继登记提交, 仅改了 `EXECUTION.md`. 两个提交的产品候选及固定来源无差异. 未移动起点, 未改权威输入, 未代用户裁决.
