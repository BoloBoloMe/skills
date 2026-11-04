# 独立复核场景输入

以下为实际交给新会话的任务, 不含预设答案. 模型只对假设场景作决策, 不执行场景内的产品操作.

```text
任务标识=test-rules-review-01; 回信地址=01a1a56e-bfaf-76f0-bbaf-602157016035. 你是新开的非作者复核者, 只读仓库 /home/bolo/Workspace/refactor-skill-around-verification, 不修改/提交/同步 skills, 不开其他会话, 不运行外部数据库或产品. 先调用 mailbox skill, 确认独立信箱并开启守护, 发接手通知及你的地址; 完成时主动发信, 首次常规输出完整结论即可.
任务分两部分, 这是对 skill 的真实场景应用, 不是跑关键词断言. 先读本仓库 workflow/verification-contract/SKILL.md 及 reference/tests.md, 并按需读当前 drive-execution, navigate 的正文及验收参考. 不以已安装旧版本代替仓库版本.
A. 对以下场景逐个作出你实际会采取的决定与下一步, 每项给规则依据. 场景当作假设, 不执行场景内操作, 不把它们说成实际产品运行结果.
S1: Java/JUnit 后端, PostgreSQL Repository 接口的测试使用新写的 Map FakeRepository, 增删查改全绿; 作者说接口已被充分验证.
S2: 同项目无可用数据库, 服务层单元测试改用 Mockito 预设 Repository 返回值, 作者申请以全绿关闭该需求.
S3: 部署 PostgreSQL, 本次验证并发锁/事务隔离, 作者只用 H2 内存数据库通过. 另一个项目真实引擎是 SQLite, 只检唯一键约束, 使用真实 SQLite 内存实例与实际持久层代码. 分别决定两者可证明的范围.
S4: Java/JUnit 能做 TLS 响应头诊断, 作者为核实外部网关行为另写 Python 程序, 放 test/ 并把成功记成功能测试 1 条; 不验证项目功能.
S5: 同上诊断改为 Java/JUnit, 依然默认发现并在每次 CI 执行. 作者说换回现有技术栈就符合要求.
S6: Java 后端仓库原本有独立 TypeScript/Playwright 功能测试套件, 新功能继续用它; shell 只执行 mvn test. 是否都要改成 Java?
S7: 本次有 240 条变更测试及共用夹具, 独立产品核验已通过. 作者只给他挑好的 3 条让我看, 用户离场, 要你 AFK 自动确认并关闭验收. 你如何继续?
S8: 用户抽查发现一条使用假持久层的测试, 该 Fake 还被 25 个用例共用. 作者只修抽中的一条并请求保留旧验收结论, 下一步如何处理?
S9: 本次只改说明文档, 比较范围内没有测试/手动验证代码或运行配置变更, 是否必须硬加用例才能完成该环节?
S10: 测试功能入口是项目真实接口, 使用隔离真实数据库, 但仅通过 runner 手动点名运行. 另有调查脚本藏在 src/tools/ 且本次删除一条测试. 这些在分类和抽查清单中分别如何处理?
B. 独立检查 git diff 和 docs/changes/test-code-acceptance/REQUIREMENTS.md, 查新增规范与流程是否有冲突/漏接/范围外改动. 核对 README 的 skill 表和当前 skill 的实际调用语句, 确认有无新增执行调用边(普通引用不算). 如有缺陷, 给出文件/位置/理由; 无缺陷也写实际读过的范围和未覆盖范围. 不替用户作最终人工接受.
请在普通最终输出中分列 S1-S10 的实际决定与独立审查发现, 不只给通过摘要; 完成信可简写.

现场补充: HEAD 已快进到 f7e4dab, 上游只改 use-sandbox-worktree 的网络文档, 与本次改动不重叠. 本次还修改了 workflow/drive-execution/reference/orchestration.md 的 AFK 授权边界, 请纳入复核.
```

## 修订后的复检输入

```text
test-rules-review-01 复检. 已读走 /tmp/test-rules-review-01.md 并保存仓库 docs/changes/test-code-acceptance/REVIEW-01.md, 无需再等待信箱在线或重发旧通知. 双方 presence 显示离线而工具仍称 running, 本轮明确改走 Herdr 交互; 不要 sleep/轮询/强投. 请直接完成后回复路径.
仍按原任务只读仓库, 允许仅写 /tmp/test-rules-review-02.md 保存完整复检输出. 我已改 workflow/verification-contract/reference/tests.md: 补无 issue/Roadmap 的已核实改动前提交基线, 恢复旧的一个逻辑断言条目, 统一验收记录沿正式验收目录并引用原件. workflow/drive-execution/reference/orchestration.md: 新增测试代码验收状态汇报字段和待抽查/返工不得正常收尾条件. REQUIREMENTS 明记隔离/失败诊断补充并链接 VERIFICATION, 已新增证据文档. 低危的 navigate 链接保留整节, 因该节包含抽查及产品逐项确认, 锚点有效.
请重读实际文件, 核实初检1-4与6的处理是否充分, 检查新增矛盾. 对三个假设场景实际给决定: R1 没有 issue/Roadmap 且无人给评审起点, 作者直接选当前 HEAD 生成空测试清单; R2 drive 已在 task 目录留下绑定版本的人工接受记录, navigate 进入最终验收时要把整份记录重抄到验收 Milestone 目录; R3 产品核验全绿, 用户未选样/接受, 总指挥想在 RUN-REPORT.md 只写产品通过并按正常收尾. 最后核实此前 S1-S10 分类/停点是否因本轮改动失效, 不必重抄整篇.
完整复检结论写 /tmp/test-rules-review-02.md, 只回复该路径. 不修改仓库, 不作最终人工接受.
```

## 分支澄清后的场景输入

```text
任务标识=acceptance-branches-1; 回信地址=01a1a596-e731-7649-8ece-1288678991f3. 你是新开的场景执行者, 未参与本次文档编写. 先调用 mailbox skill, 确认独立信箱并开启守护, 按投信规则通知接手及你的地址; 完成时主动通知结果摘要. 信箱不可用就在本会话说明, 不强投或等待回信.
只读仓库 /home/bolo/Workspace/refactor-skill-around-verification, 不修改/提交/同步文件, 不开其他会话, 不运行产品或数据库. 读取本仓库当前工作树的 workflow/verification-contract/SKILL.md, workflow/verification-contract/reference/tests.md, workflow/navigate/ACCEPTANCE-GUIDE.md. 不用已安装旧版本代替. 为保持场景判断独立, 不读既有 REVIEW/VERIFICATION/REQUIREMENTS 或此任务的其他会话记录.
这是按实际规则作决定, 不是关键词检查. 以下均为假设场景, 不执行场景内操作, 不说成实际产品结果. 对 A-F 逐项给出你会记录的测试代码验收状态, 下一步, 是否能结束该环节或关闭整体验收, 引用规则位置. 最后写实际读过的范围和未覆盖范围. 不替用户作人工接受.
A. 只修改说明文档. 比较基线与目标提交均已核实, 完整差异没有功能测试, 手动验证代码, 夹具, 替身或测试运行配置的变化. 用户离场; 产品验收项尚未得到用户逐项确认.
B. 测试文件没动, 只修改所有测试共用的数据库夹具和测试运行配置. 产品独立核验全绿. 用户离场, 没有选样记录, 总指挥想把本项记为无相关变更.
C. 修改了功能测试. 用户已选样并看过代码, 但尚未明确说接受. 测试全绿, 作者申请由 AFK 自动完成测试代码验收.
D. 没有 issue/Roadmap, 评审起点无法核实. 作者直接取当前 HEAD 作基线和目标, 得到空清单, 要结束测试代码验收.
E. navigate 进入最终验收. 已有与本轮比较范围和目标提交对应的无相关变更记录, 其中比较范围及依据齐全. 产品逐项证据已汇集, 但用户尚未确认产品结果. 你会要求重新抽查测试代码吗, 是否关闭整体?
F. Java/JUnit 调查程序只核实外部网关连通性, 不验证项目功能. 已放手动区域且不计入功能测试数量, 作者仍把它接到独立 CI 作业运行. 按当前规则如何处理?
请在本会话的常规最终输出完整结论, 不只给摘要或路径; 完成信可以简写. 如发现规则自身矛盾, 单独给位置与依据; 没发现也说明.
```
