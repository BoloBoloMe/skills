# test-rules-review-01 复核原始结论

复核者: 新开的非作者复核者, 独立信箱 `01a1a579-9aeb-70ac-ab38-ad766c9a9610` (守护 running=true, 与 `01a1a56e-bfaf-76f0-bbaf-602157016035` 互发成功).
授权: 只读仓库 `/home/bolo/Workspace/refactor-skill-around-verification`; 未改/未提交/未同步 skill, 未开其他会话, 未跑外部数据库或产品, 未运行仓库测试.
复核对象: `HEAD=f7e4dab` (已核: 只合并 use-sandbox-worktree 网络文档, 与本次不重叠) + 工作区 9 个改动文件 + 新增 `docs/changes/test-code-acceptance/REQUIREMENTS.md`.
性质: 这是对 skill 文本的真实场景应用审查, 场景 S1-S10 均按假设处理, 未执行场景内操作, 未把场景当成实际产品运行结果.

## A. S1-S10 决定与规则依据

### S1 Java/JUnit, PostgreSQL Repository 测试用新写 Map FakeRepository, 全绿, 作者称接口已充分验证
- 决定: 不接受该需求为已验证, 也不接受"接口已充分验证".
- 依据: `workflow/verification-contract/SKILL.md:20` 持久层不得替换; `reference/tests.md:12` 明写 `FakeRepository` 用 Map 存取再读回只证明 Fake 正确; `tests.md:13` 测上层行为也要真实持久层.
- 下一步: 要求用真实 PostgreSQL 隔离实例 (加载实际 schema/迁移) 从真实入口重跑增删查改; 拿不到环境就记未验证+所缺条件. 该 Fake 建议删除以免被再次当证据; 若保留只能标注"只验证 Fake 自身".

### S2 无可用数据库, 服务层单测改用 Mockito 预设 Repository 返回值, 申请全绿关闭
- 决定: 拒绝关闭.
- 依据: `tests.md:10` 不论叫单元测试还是集成测试, 不论直接测 Repository/DAO 还是上层服务, 都禁 mock/stub/自写内存假实现/预设结果; `SKILL.md:21` 关键依赖未验证不能报通过; `SKILL.md:22` 缺环境报未验证.
- 下一步: 该需求记未验证并列所缺条件 (隔离 PG); 搭起来后按真实调用链验证. 不用"全绿"充当交付证据.

### S3 两个持久层场景分开判
- PG 并发锁/事务隔离只用 H2: 不通过. H2 不能证明 PG 方言/锁/事务 (`tests.md:14`). 必须换真实 PG 隔离实例; H2 结果只能用于与引擎差异无关的部分, 且边界写清.
- 真实 SQLite 内存实例 + 实际持久层代码, 只检唯一键约束: 可接受. 范围 = 应用代码与该 schema 在该引擎下的唯一键约束行为 (`tests.md:12-14` 真内存库不是自写假实现). 边界须写明不证明磁盘持久性/重启/多进程并发/其他引擎语义; 部署引擎若不是同一 SQLite, 结论不外推.

### S4 Python 诊断放 test/, 记 1 条功能测试, 不验证项目功能
- 决定: 分类错误, 不计入功能测试通过数, 也不能证明项目功能.
- 依据: `tests.md:6` 手动验证代码定义 (即使 JUnit/pytest 或放 test/ 也不算功能测试); `tests.md:7` 同类验证优先既有技术栈 (Java 能做却另写 Python 属违规); `tests.md:4` 功能测试须验证系统真实功能.
- 下一步: 改判为手动验证代码; 保留则放手动区域 (如 `test/manual/`), 写目的/命令/环境/判据/结论边界, 不接默认发现与 CI; 或用 Java/JUnit 重写仍按手动验证归类; 一次性按 `tests.md:9` 不提交, 跑完清理.

### S5 同上改 Java/JUnit, 默认发现且每次 CI 跑, 作者称换回技术栈即符合要求
- 决定: 仍不接受. 技术栈一条满足, 分类与隔离两条仍违反.
- 依据: `tests.md:6` 手动验证代码"不接入默认测试发现或 CI, 不混入功能测试用例/通过数量"; 不能自动排除时用既有分组/标签显式隔离.
- 下一步: 移出手动区域或加显式隔离; 不占功能测试计数; 不把每次 CI 跑外部网关诊断当功能证据 (外部依赖不稳, 也不测项目功能).

### S6 Java 仓库已有独立 TS/Playwright 功能套件, shell 只跑 mvn test, 是否都要改 Java
- 决定: 不改写. Playwright 套件属项目既有独立测试平台, 照常复用 (`tests.md:7`); "Java 后端"不是强制同语言的依据.
- 缺口: `mvn test` 跑不到 TS 套件, 完整测试套件会漏; 须把 `npm/playwright` 入口写进 issue 验证入口与完成定义, 在合并/交付节点实跑.

### S7 240 条变更测试, 只给挑好的 3 条, 用户离场, 要 AFK 自动确认并关闭验收
- 决定: 拒绝自动确认, 拒绝关闭验收, 拒绝代选样本.
- 依据: `tests.md:100` 样本由用户选, 未在场记待验收, "不自行选完再宣称我已接受"; `SKILL.md:62` 作者自检/评审/全绿都不能代替; `drive-execution/reference/orchestration.md:79` 正式人工验收与测试代码抽查的选样/接受不在 AFK 授权内; `navigate/ACCEPTANCE-GUIDE.md:25` 未确认项保持未通过.
- 下一步: 按评审起点到目标提交汇集完整清单 (含删除/移动/夹具/替身/运行配置, 不只搜 test/), 绑定目标提交与原始证据, 落盘并记待验收; 可建议优先看持久层/共用夹具/手动验证代码, 抽多少由用户定; 独立产品核验通过只作旁证, 不能顶替抽查.

### S8 抽查命中假持久层, 该 Fake 被 25 个用例共用, 作者只修一条并求保留旧验收结论
- 决定: 拒绝只修样本; 受影响范围的旧验收结论作废.
- 依据: `tests.md:102` 发现问题须查整份清单同类写法及共用夹具全部使用处, 不只修样本; 修复复跑后由用户定复抽范围. 未受影响的已确认结果可注明依据沿用, 但这里 25 处共用 Fake 全部受影响, 不属"未受影响".
- 下一步: 要作者列出该 Fake 全部 25 个使用处, 逐个换真实持久层或重新分类, 复跑受影响检查, 出新提交+新清单+结果; 用户确认/复抽前保持待验收.

### S9 本次只改说明文档, 比较范围内无测试/手动验证代码或运行配置变更
- 决定: 不必硬加用例; 该环节不虚构抽查.
- 依据: `SKILL.md:51` 非行为改动选直接相关检查, 无适用检查就说明核对内容及原因; `SKILL.md:62` 与 `tests.md:100` 无相关代码变更时记录范围与理由, 不为验收硬加测试; `tests.md:103` 无既有记录时单独留档.
- 下一步: 记录比较范围+理由, 做文档相关检查 (相对链接, 命令可执行, 与实现一致). 反向提醒: 改 skill/提示词会改变实际操作, 按 `SKILL.md:51` 不属非行为改动, 本次仓库改动即属行为变更.

### S10 功能测试走真实入口+隔离真实库但只手动点名; `src/tools/` 藏调查脚本; 本次删一条测试
- 功能测试: 仍算功能测试 (手动执行不改变身份, `tests.md:6`), 但"仅手动点名"是防退化缺口; 须在清单与完成定义写清执行入口与运行节点并实跑, 长期应接回项目既有测试入口 (`tests.md:3`).
- `src/tools/` 脚本: 属手动验证代码/一次性调查, 不算功能测试. 长期保留则移手动区域并写目的/命令/判据/边界, 不接默认发现/CI; 一次性按 `tests.md:9` 不提交, 跑完清理; 不能藏 `src/` 冒充产品代码.
- 删除的测试: 清单必须列删除项并写失去的验证与替代位置 (`tests.md:99`); 同时按 `code-review/SKILL.md:53` 判是否触碰旧行为, 复跑受影响检查.
- 分类/抽查清单: 两者分别进"手动验证代码"段与"删除项"段, 必须出现 (清单要求覆盖 `test/` 之外); 未抽查部分标未抽查.

## B. 独立审查发现

### 实测/阅读范围
- `git diff` (工作区 vs f7e4dab) 全部 9 个文件逐 hunk 读完; 新增 `REQUIREMENTS.md` 全文; `README.md` 技能表; `workflow/verify-change/SKILL.md`; `verification-contract/SAFETY.md`; `navigate/TEMPLATES.md`; `to-execution/TEMPLATES.md`; `software-engineering-consensus/SKILL.md` 相关词条; 改动文件全部相对链接用脚本核存在性与新锚点.
- 机械核对: README 链接的 skill 与实际 `*/SKILL.md` 双向差集均为 0; 新增链接目标文件全部存在; 新锚点 (`#测试代码人工抽查验收`, `#持久层不得用替身`, `#证据与确认`) 均命中.
- 调用边: diff 中未新增"调用 `X` skill"执行语句; 新增读取都是 reference 文档 (按 `README.md:11` 口径不算调用边). `verify-change` 未改, 未加测试代码判据, 与 REQUIREMENTS 落点一致; 未新增 skill, 未新增路线图类型, 未改 README 表也能成立.
- 一致性: 持久层禁令/替身边界/技术栈/手动分类在 SKILL, tests.md, code-review, ACCEPTANCE-GUIDE 间无相互矛盾; AFK 新限制与 `SAFETY.md:37-43` 红线互补不冲突; drive-execution 的 HITL 门与 navigate 验收的"已有接受记录直接引用"能衔接.

### 缺陷/漏接 (按严重度)
1. 中: `workflow/drive-execution/reference/orchestration.md:22` 停止并汇报的六项格式未更新. 新增测试代码验收是硬门槛, 但报告没有对应项, 也没把"待验收"纳入"未验证必验项不按正常收尾". 风险: 按格式写全也可能漏报该门状态, 与 `drive-execution/SKILL.md:54` "停止并记待验收"缺少落点. 建议在核验结果或缺口与待决处加一项.
2. 中低: `workflow/verification-contract/reference/tests.md:99` 清单基线只写"评审起点到目标提交", 而 `评审起点` 只在有 `EXECUTION.md` 的 drive-execution 流程里定义 (`drive-execution/SKILL.md:23`), `SKILL.md:62` 又要求"无 issue/无 Roadmap 时同样执行". 单会话直接改动 (如本次) 没有回退基线. 建议补"以用户指定基线/本轮变更起点为准".
3. 中低: `tests.md:37-39` 好测试条目新增"每个测试围绕一个行为; 可断言多个结果字段""数据和状态隔离""失败能指向目标行为", 并把旧的"只有一个逻辑断言"放宽. 这三条不在 `REQUIREMENTS.md` 的三条已确认要求与落点内, 属未记录的范围外改动, 且实质改变抽查判定口径 (旧规则会把多断言判成坏测试). 未发现与其他文档冲突, 需用户确认是否纳入.
4. 低: 记录位置口径分叉. `tests.md:103` 要求"产物根目录的验收记录中单列", `ACCEPTANCE-GUIDE.md:22` 要求验收材料随验收 Milestone 产物, 而 navigate 下产物根目录是该 task 里程碑子目录, 两者可能不同目录. 后果: ACCEPTANCE-GUIDE 的"已有接受记录直接引用"可能找不到指针. 建议明确"在验收报告中引用清单/接受记录路径".
5. 很低: `workflow/navigate/SKILL.md:51` 链接到 `ACCEPTANCE-GUIDE.md#证据与确认` 整节, 没有指向测试代码验收那一段的独立锚点, 读者需自行定位.
6. 低 (记录缺口): `docs/changes/test-code-acceptance/REQUIREMENTS.md` 只写验证约定, 未落本仓库自身的交付证据/复核记录位置; 本次改动按 `SKILL.md:51` 属"改变实际操作"的行为变更, 需要真实运行记录. 仓库内目前没有该记录文件, 需用户定放哪 (本次复核者不写仓库).

### 无问题/范围外核对
- 未发现对旧变更产品标准, ADR, README 技能表的越界改动; 无新增 skill/脚本/路线图类型.
- `REQUIREMENTS.md` 落点声明与实现一致 (发现 3 的未记录条目除外).
- 未发现新增执行调用边, 故 README 表无需改也能成立.

### 未覆盖范围 (如实标)
- 未运行仓库 pytest (mailbox/swt/navigate 等) 与任何产品; 未真实执行 drive-execution/navigate 流程; 只做改动文件的相对链接存在性/锚点核对, 未做全站渲染锚点检查; 未读 `docs/changes` 历史文档全文与 `docs/adr` 全文; 未审 `agent-prompts/`, `pi/` 树; 未验证 sync 后安装版行为; 未作最终人工接受, 不代替逐项产品验收.
