## 父级
- `../EXECUTION.md`
## 执行
- [ ] 已完成
## 要交付什么
`workflow/navigate/SKILL.md` 的类型语汇按已确认口径重写: demo 条目接住"可以演示现成成品", poc 成为独立 AFK 类型且只写流程语 (交付定义用指针), research 收窄到工作目录之外的事实并补就地查与指派, task 承接"需实测但结论描述现状"的工作, deliberate 那处 `prototype` 换成演示, 完成标准与收口产物同步.

具体:
1. research 条目何时创建: 只留"决策在等一个藏在当前工作目录之外的事实 (文档, API, 知识库等), 须先暴露"; 删掉"或等一个无处可查的结论, 须先做实验测出". 同条目补一段: 工作目录内的事实就地查, 不单立里程碑; 查影响面用 `blast-radius`, 查领域用 `domain-awareness`; 需要单独立项才查得清的内部调查通常说明里程碑划错了.
2. demo 条目 (原 prototype 条目): 点名 `demo` skill, 产出演示材料; 何时创建扩为"问题是它应该是什么样子, 如何运行, 或需要让人看清某个样子/行为/过程以便讨论"; 写明拿已交付的成品或线上系统演示也归 demo, 演示活动不新增产品交付承诺; HITL 属性不变.
3. 新增 poc 条目, 位置紧接 demo 条目之后, 只有四部分且不加第五个小节:
   - 何时创建: 问题是某个技术方案能否做成, 需要真实实验才能判定. 同一部分里写拆分判据与归属: 一个结论能一次收口就一个里程碑; 出现多个可分别收口的结论才拆成多个并用依赖串起来, 每个里程碑各收口一个结论; 单个结论跨多个会话时保持进行中继续推进, 不拆里程碑, 会话规模只作经验不作判据; 实质是交付产品代码的工作归 task.
   - 完成标准: 结论与依据已写进本里程碑自己的产物.
   - 收口产物: poc 的产物是它自己里程碑里的结论与依据.
   - 终止处置: 未证实默认保持未完成; 只有仓库主人裁决终止时才把该里程碑记关闭, 关闭摘要写"未证实即终止, 不构成可行性结论"及原因, 并按裁决把它从终点验收的依赖里移除, 不记成歧路.
   - 指针句: "交付什么"的定义与"未证实"的词义指向 `workflow/software-engineering-consensus/SKILL.md` 的 PoC 词条; 条目内不复述可行/不可行结论与可复查依据的定义 (BR-005).
4. 完成标准节: demo 那行改为"演示已做, 我看过并能据此判断要讨论的事"; 新增 poc 一行 (与条目同口径); research, deliberate, task, acceptance 四行不动.
5. 收口产物 (航行步骤 4): `prototype` 分项改为 demo 按它自己的规则管理产物; 补 demo 的成品演示情形: 产物可以为空, 关闭摘要记一行"演示了什么, 看的是哪个版本"; 补 poc 分项: 产物是本里程碑的结论与依据.
6. task 条目何时创建补指派: 需要实测才能得出结论, 但结论是描述现状的工作归 task, 例如压测现有链路或采性能基线.
7. deliberate 条目的 "无法靠 prototype 提升保真度" 改为 "无法靠演示提升保真度", 该条目不再出现 `prototype`.
8. 正文里其余中文"原型"词面随条目改为"演示材料", 只改与类型定位相关的句子, 不动航行步骤的流程与命令.
## 覆盖依据
- Product: `../PRODUCT.md`, AC-007, AC-008, AC-009, AC-011, AC-012, AC-013, AC-016 (navigate 部分), AC-020, AC-021, AC-022, BR-005.
- Technical: `../TECHNICAL.md`, 模块划分 (navigate 类型语汇条目), 模块接口 (指针与不复述的不变量).
## 相关决策
- `../../milestone-03/DECISIONS.md`: D004 (demo skill 只管造材料, 成品演示不调用), D005 (demo 创建条件扩张), D011 (research 只留外部事实, 补就地查与指派), D014 (终止只记关闭摘要, 不用 off_course), D015 (拆分判据是结论边界), D016 (poc 只写流程语, 交付物用指针), D017 (完成标准与成品演示一行摘要), D018 (需实测但描述现状归 task).
- `../../milestone-01/DECISIONS.md`: D005 (PoC 交付有条件边界的实测结论), D006 (demo 不新增产品交付承诺), D007 (迭代只属于 MVP, poc/demo 不使用迭代概念).
## 允许范围
- `workflow/navigate/SKILL.md`: 类型条目, 完成标准节, 收口产物步骤, 以及为对齐词面必须动的句子.
## 禁止范围
- 不改 `TEMPLATES.md`, `roadmap.py`, `web/index.html`, `render_checks.py`, `workflow/demo/` (其它 issue 的活).
- 不加状态枚举, 不用 `off_course` 记 poc 终止, 不提"已取消"状态 (D014).
- 不在 navigate 复述 PoC 交付定义或改 `workflow/software-engineering-consensus/SKILL.md`.
- 不写"迭代"用于 poc 或 demo; 不给 poc 加第五个小节 (拆分判据与归属并入何时创建).
## 代码定位提示
- 入口: `workflow/navigate/SKILL.md` 的 Milestone 种类节 (research 35 行, prototype 36 行, deliberate 37 行, task 38 行), 完成标准节 (43-47 行), 航行步骤 4 收口产物 (108 行).
- 对照读: `workflow/software-engineering-consensus/SKILL.md` 的 PoC 词条 (指针目标, 只读不改); `../PRODUCT.md` 的 AC-007 到 AC-013, AC-020 到 AC-022.
- 阅读顺序: 先读 navigate 现状三处, 再读 PRODUCT 的对应 AC, 再落笔; 落笔后跑 check_skill 与下面第 2 到 8 步的 grep.
## 验证契约
- 变更类型: 行为变更.
- 对应范围: 代理据以新建里程碑与收口的类型语汇 (何时创建, 完成标准, 收口产物, 终止处置), 属于改变实际操作的提示词.
- 验证要求/证据: 逐条对照 AC-007 到 AC-013, AC-016 (navigate 部分), AC-020 到 AC-022 的可观察断言, 每条留 grep 输出或原文摘录; 给 check_skill.py 的 OK; 给"无 prototype, 无无处可查, 无冒烟, 无 off_course 用于 poc"的反向 grep 零命中; 给指针目标路径存在性核对.
## 验证入口
```bash
# 1 文档机检
uv run python general/writing-for-llm/check_skill.py workflow/navigate/SKILL.md
#    通过标准: 输出 OK, 退出 0

# 2 AC-012 / AC-022 research 条目
grep -n '无处可查\|须先做实验测出' workflow/navigate/SKILL.md   # 通过标准: 零命中
grep -n '工作目录之外\|就地查\|blast-radius\|domain-awareness\|里程碑划错' workflow/navigate/SKILL.md
#    通过标准: 何时创建只留外部事实一种; 就地查段落含指派与"划错了"的判断

# 3 AC-008 / AC-009 demo 条目与成品演示
grep -n 'demo' workflow/navigate/SKILL.md
#    通过标准: 何时创建含"是什么样子, 如何运行, 或需要让人看清某个样子/行为/过程";
#    含"已交付的成品或线上系统演示也归 demo"与"不新增产品交付承诺";
#    完成标准写"演示已做, 我看过并能据此判断要讨论的事";
#    收口产物写成品演示产物可为空, 关闭摘要记"演示了什么/哪个版本"; 无强制 demos/ 留档要求

# 4 AC-007 / AC-011 / AC-020 / AC-021 poc 条目
sed -n '/^- poc/,/^- task/p' workflow/navigate/SKILL.md
#    通过标准: 只有何时创建/完成标准/收口产物/终止处置四部分, 无第五小节; AFK 标注;
#    何时创建含结论边界拆分与"会话规模只作经验"与"实质是交付产品代码的工作归 task";
#    指针句指向 workflow/software-engineering-consensus/SKILL.md 的 PoC 词条;
#    终止处置含未证实默认保持未完成/亲裁才记关闭/关闭摘要原文/移出终点验收依赖/不记成歧路
grep -n 'off_course' workflow/navigate/SKILL.md    # 通过标准: 仅出现在歧路节, 不在 poc 条目内

# 5 AC-013 task 指派与 AC-016 deliberate
grep -n '压测\|性能基线\|描述现状' workflow/navigate/SKILL.md    # 通过标准: task 条目有该指派与例子
grep -n 'prototype' workflow/navigate/SKILL.md                  # 通过标准: 零命中
grep -n '无法靠演示提升保真度' workflow/navigate/SKILL.md        # 通过标准: 命中 deliberate 条目

# 6 BR-005 指针不复述
grep -n '可行/不可行\|可复查依据' workflow/navigate/SKILL.md
#    通过标准: 命中处只作指针或流程语引用, 没有展开定义; 与 consensus 词条原文逐句比对无复述段落

# 7 全局残留
grep -rn 'prototype' workflow/navigate/SKILL.md README.md workflow/demo/    # 通过标准: 零命中
```
## 交付证据
执行后填写: 每条 grep 的输出与结论, 改后条目原文摘录 (poc 四部分, demo 两处, research 两段), check_skill 输出, 材料位置 `/tmp/m9-04-03/`.
## 风险提示
- AC-011 与 AC-021 的字面张力 (复查报告 N-1): 指针句覆盖"交付什么"的定义与"未证实"词义, "未证实默认保持未完成"等流程句落在终止处置小节. 这样两句都能字面成立, 且 AC-011 第三句"没有复述定义"仍成立. 若落笔时两者无法并存, 停下上报, 不自行改 Spec.
- 报告 N-2 (D011 展开里"当前正在做的里程碑自己查证内部事实并写进它的产物"半句) 不在任何 AC 的断言里, 本 issue 不补, 以避免超出已确认口径.
- poc 条目容易被写成五个小节, 或把交付定义整段抄进来; 两者都直接违反 G-004/AC-011.
## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
## 验收标准
- [ ] research 何时创建只剩外部事实一种情形, 并有就地查段落与 blast-radius / domain-awareness 指派.
- [ ] demo 条目接住现成成品演示且不新增交付承诺; 完成标准与成品演示关闭摘要一行写清.
- [ ] poc 条目只有四部分, AFK 标注, 拆分判据与产品代码归属并入何时创建, 未证实默认句在终止处置, 交付定义只留指针.
- [ ] task 条目有"需实测但结论描述现状"的指派; deliberate 条目写"无法靠演示提升保真度".
- [ ] 全文无 prototype; check_skill OK.
## 被阻塞于
- `ISSUE-02-demo-skill-rename-rewrite.md` (demo 条目点名新 skill 名, 改名落地后正文才不会有指向不存在 skill 的中间态)
