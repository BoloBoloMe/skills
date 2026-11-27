# 全程盘问对齐与编号汉化 Execution Spec

## 权威输入与决策引用
- Product Spec: `PRODUCT.md`, SHA256 `c8823e0edf27e86a05f81acf89e5fea6027db3524afd6c88512326cda3e239d5`.
- Technical Spec: `TECHNICAL.md`, SHA256 `e825dd5799fb6fa725216e140a3a1bb240b868753bf6c850ccfc615f39340f1e`.
- 验证方案: `VERIFICATION-PLAN.md`, v3, 已确认, SHA256 `7c4c450f1bfdf630f133f20435b9000cd76ab76a06c5538b1fa4f9a15fc49583`.
- 决策引用 (只读, 非意图来源): `DECISIONS.md`, 决策40, 决策41, 决策42.
- 规格优先于决策账本. 不新增或改变决定. 当前草稿不修改正式规格或路线图.

## 评审起点
- 评审起点: 9e8dd1dfe92b3b446c88c2cb8fce33cb0c67a77a. 核实依据: 该提交是 improve 分支当前顶端 (milestone-07 派工前最新提交; 前一提交 73f70636948ecfde2009a30d0b65ec1268700233 为 milestone-06 交付后状态); 本变更此前提交均为规格/方案/拆分文档, 其后无实施提交. 差异与旧编号范围审计基线 182ff1846d0ed310b7f4ed308366d36f6e74b412 不变.
- 实施前摘要: 安装目录只读摘要已于派工前取得 (231 个文件的 SHA256 清单, 含 workflow/to-spec, workflow/verify-change, workflow/navigate 下 23 个相关文件), 存于证据根 `pre-impl-snapshot/skills-manifest.sha256`.
- 差异与旧编号范围核对按验证方案使用基线 `182ff1846d0ed310b7f4ed308366d36f6e74b412` 到最终目标提交. 评审起点仍由 `drive-execution` 在派工前核实并填写.

## 执行记录
- milestone-07 评审门槛判定: 旧行为影响方向实做. 依据: 三份 issue 验证契约均声明行为变更, 实际差异触碰公开 CLI 契约 (ac-draft.py 移除 --review 与 promote 契约改动), skill 流程条文及跨文件调用说明 (navigate/ACCEPTANCE-GUIDE/README), 属共享接口与跨模块路径. 首轮无 IMPACT-REVIEW.md, 由未参与实现的独立审核者新建. 评审起点 9e8dd1dfe92b3b446c88c2cb8fce33cb0c67a77a, 集成提交 1bc15f612c10aa6e68e33587a01cd2de1ede2fe4 (证据归档 7dea2143e00dcda8c9385a5881f36ba017648088).
- milestone-07 派工前登记: 仓库外专用证据根绝对路径 `/home/bolo/evidence/to-spec-grilling-and-chinese-ids` (决策41); 实施前安装目录只读摘要已取得并留存于该证据根. 实施按轮追加记录.
- milestone-07 集成 (合并提交 `9eedb3a`, `f9bfe71`, `1dfc38a`): 三切片按编号顺序 `--no-ff` 合并到 `improve`, 无冲突, 文件不重叠. 切片顶端: issue/01 `1e64e6c` (代码 `fd26618`, `8ce78be`; 工单 `3229525`, `1e64e6c`), issue/02 `b260081`, `34ae059`, issue/03 `70ae157`.
- 切片检查结果简列: ISSUE-01 run5 绑定最终提交复跑 39 passed + 39 subtests (exit 0), `check_skill.py workflow/to-spec/SKILL.md` OK/0, 42 场景条文对照无遗留缺口; ISSUE-02 非作者核对 21 场景 43 条预期无已证实缺陷 (4 条非阻塞疑点), `check_skill.py workflow/verify-change/SKILL.md` OK/0; ISSUE-03 局部核对 (验收25 两场景, 验收41 本 issue 部分, 规则11) 通过, `check_skill.py workflow/navigate/SKILL.md` OK/0.
- 全量 `uv run pytest` 未验证: 本容器未装 Podman (`podman: command not found`), 完成定义要求的隔离环境不具备, 交调用方处理.
- 集成检查 (`integration/run1`): `uv run --with gherkin-official pytest workflow/to-spec/tests` 39 passed, exit 0; 完整差异内 3 个改动 `SKILL.md` (to-spec/verify-change/navigate) 逐个 `check_skill.py` 均 OK, exit 0; 规则12 范围审计无新违规, milestone-01 的 9 文件汉化未回退; 实施后安装目录摘要 231 文件与实施前逐一同值 (0 差异).
- 证据归档: `evidence/m07-1bc15f612c10aa6e68e33587a01cd2de1ede2fe4/` (绑定集成提交 A `1bc15f6`), 1211 文件, 与仓库外证据根逐文件同值; 密钥样字符串扫描 0 命中.

## 全局允许范围
- `workflow/to-spec/` 中本次相关流程,模板,Gherkin 纪律,`check-ac.py`,`check-tech.py`,`ac-draft.py` 及 `workflow/to-spec/tests/`.
- `workflow/verify-change/` 中当前流程与复验说明.
- `workflow/navigate/SKILL.md`, `workflow/navigate/ACCEPTANCE-GUIDE.md`, 仓库根目录 `README.md`.
- `workflow/decision-ledger/`, `workflow/to-execution/` 及 `general/` 中的编号规则只读审查; 仅在对照基线后发现本规格直接要求且 milestone-01 尚未完成的具体缺口时, 才在该命中范围内改动. 不重复执行编号汉化.
- 按 `VERIFICATION-PLAN.md` 在仓库外的本变更专用目录制作合成验证材料. 验证原件及索引按该方案在正式实施收尾时放入产物根下绑定目标提交的证据目录.

## 全局禁止范围
- 不修改 `PRODUCT.md`, `TECHNICAL.md`, `VERIFICATION-PLAN.md`, `DECISIONS.md`, `roadmap/ROADMAP.json`, milestone-01 历史评审或历史快照.
- 不修改任何已安装的 agent skill, 不在仓库外修改技能副本. 所有产品技能改动只落本仓库.
- 不改 deliberate 的独立四步语义, 不迁移历史产物或重写历史引用, 不为旧正文编号,`review_id` 或 `--review` 保留兼容行为.
- 不试跑真实需求, 不新增盘问专用记录文件/章节/格式, 不新增服务,依赖或未授权的共享资源.
- 不把 milestone-12 的用户审改,milestone-13 的集成或 milestone-08 的独立验证塞进本轮 issues, 不以通知代替产品验收.

## 完成定义
- 三个 issue 均完成, 各自的变更和证据符合 issue 的验证契约. `workflow/to-spec/tests/` 从完整候选提交通过 `uv run pytest workflow/to-spec/tests`.
- 全部切片集成后, 从完整最终差异生成改动 `SKILL.md` 清单, 逐个以 `uv run python general/writing-for-llm/check_skill.py <路径>` 检查并通过, 留清单,命令,输出和退出码. 局部 issue 只对本分支实际改动的 skill 作局部检查, 不提前声称最终清单完整.
- issues 集成到同一完整提交后, 在具备 Podman 和所需依赖的隔离环境运行 `uv run pytest`, 留全量收集范围和原始结果. 不用 `--noconftest` 单文件结果替代全量, 既有失败不豁免,不擅自修范围外项目. 依赖或环境缺失时报告未验证并交调用方处理.
- 三个 issue 全部合并后, 由未参与相关文档修改的评审者读取实际候选 `workflow/to-spec/SKILL.md`, `workflow/verify-change/SKILL.md`, `workflow/navigate/SKILL.md`, `workflow/navigate/ACCEPTANCE-GUIDE.md` 和根 `README.md`, 按权威规格交叉核对调用关系,确认语义和相互引用. 对 README 涉及的完整调用段及相邻说明作非作者复核, 留位置,依据,结论和未覆盖范围. issue 内的局部核对只依据固定规格, 不声称旧候选条文已与尚未完成的 issue 一致.
- milestone-07 全切片集成后, 对基线 `182ff1846d0ed310b7f4ed308366d36f6e74b412` 到该轮集成提交的完整旅程差异作范围核对. 全量审查 `workflow/` 与 `general/` 正文编号规则和历史命中, 逐项分类例外并复用 milestone-01 已完成的9文件汉化及 `REVIEW-milestone-01.md`, 不生成重复改造. 核对该轮完整改动清单,未改历史产物/引用及全部审计要求. milestone-13 纳入用户改动后更新差异和最终清单, 按影响补做自测/评审, 再交 milestone-08.
- 安装目录只读摘要分两次留证: 调度方须在首轮任何产品修改前安排取得实施前摘要; 实施后摘要由全切片集成检查补取, 与实施前范围和时间对应. 未能追溯的历史时段如实列缺口, 不假定已观察或未变化.
- milestone-07 完成原实施必要自测,集成和代码评审后停止, 等用户在 milestone-12 亲自查看并调整实际 skill, 再明确通知已完成审阅. 无修改也须明确通知. 不开始最终独立验证.
- 用户审改后的集成由 milestone-13 按实际改动更新改动清单和审计范围, 对受影响内容补自测和评审, 并更新最终改动 `SKILL.md` 清单及对应格式检查. 最后 milestone-08 才由未参与实现,修复,用户审改集成的另一会话, 对最终完整提交按已确认方案独立验证. milestone-09 由用户终点验收, 并由用户选样完成人工测试代码抽查. 这些节点不属于本执行拆分的 issue.
- 正式交付前按 `../../../workflow/verification-contract/reference/tests.md` 的规则准备全旅程测试代码变更清单和证据. 是否有相关测试代码变更,抽样和接受由 milestone-09 按实际差异处理, 不由作者预先代选或代验收.

## 验证策略
- 变更类型以行为变更为主. 技能条文会改变实际操作, 不能按普通文档免检. 采用既有 `workflow/to-spec/tests/` 栈, 对长期需要保护的公开 CLI 行为补齐或更新最少的功能测试; 只通过公开 CLI,真实 gherkin 解析器,真实隔离文件和可观察输出检查行为. 不以私有函数测试或全套测试通过代替真实入口验证. 测试名称和预期值描述外部行为, 不绑定内部调用顺序.
- 本轮产品流程条文按已确认方案从候选文本逐条语义对照, 不用真实需求试跑. CLI 场景从公开入口实际启动进程, 参数按目标版本公开帮助核实, 输入为合成隔离文件. 方案指定的原子替换和并发时序须留下外部进程/文件系统事件证据, 无法证明窗口命中则记未验证.
- 各 issue 只将自己的候选条文与固定权威规格核对. 全部切片合并后必须对真实的 to-spec,verify-change,navigate/ACCEPTANCE-GUIDE 和 README 作一次跨文件集成核对, 确认术语,调用关系,确认边界和交叉引用相符; README 的完整相关段落由非作者复核. 不能把尚未集成的旧条文当作已核实的相互一致事实.
- `VERIFICATION-PLAN.md` 的70行产品核对和3项工程检查共73行全部承接到下方覆盖矩阵. 最终产品独立验证在 milestone-08 执行, 本 Execution Spec 不把开发自测当成其结论.
- 自动化用例只在确需长期回归时安排. 用例19至用例24分别保护公开预览,转正,参数移除,失败/并发输入,编号对账和 AC-024 的七种违规输入; 不因其他 AC 有编号就创建额外用例. 每条用例的输入,实际命令,预期与证据在 ISSUE-01 中界定.
- 所有运行输出使用脱敏合成材料. 按决策41在派工前登记仓库外专用证据根的实际绝对路径, 每次复跑用新子目录并保留旧原件. 不触碰生产数据,用户数据,正式规格或已安装技能. 原件写入清单,可访问性及脱敏按方案复核; 不自动清理原件.

## 任务图
- ISSUE-01: `issues/ISSUE-01-tospec-flow-and-cli.md`; 覆盖: 验收1-24(@AC-001至@AC-024), 验收26-30(@AC-026至@AC-030), 规则1-15; 依赖: 无.
- ISSUE-02: `issues/ISSUE-02-verify-change-method-flow.md`; 覆盖: 验收31-40(@AC-031至@AC-040), 验收41(@AC-041)中的 verify-change 与 REVERIFY 部分, 规则16-22; 依赖: 无.
- ISSUE-03: `issues/ISSUE-03-navigate-readme-alignment.md`; 覆盖: 验收25(@AC-025), 验收41(@AC-041)中的 navigate 与 README 部分; 依赖: 无.
- 三项任务接口已由权威规格固定, 可以独立领取. 没有以文件重叠或先后编号构造 blocker.

## 覆盖矩阵

| 来源 | 承接 issue | 验证入口与对应检查 |
| --- | --- | --- |
| 验收1-验收8(@AC-001至@AC-008), 验收11(@AC-011), 验收26-验收28(@AC-026至@AC-028) | ISSUE-01 | 对 `workflow/to-spec/SKILL.md` 及必要账本/交接调用条文逐项语义核对: 一句话提问,免问边界,同判定去重,事实确认,闭环清单与明确确认,跨话题/全部模板节,续问进度及明确节奏. 同号的 normal/failure/edge 均逐条承接. |
| 验收9-验收18(@AC-009至@AC-018), 验收29-验收30(@AC-029至@AC-030) | ISSUE-01 | 对账本反方,独立检查,分流修文/补问,审计归档,整组失败处理和脱敏/专用预览目录逐条核对, 包括所有同号 failure/edge. |
| 验收19-验收24(@AC-019至@AC-024) | ISSUE-01 | 从 `ac-draft.py`, `check-ac.py`, `check-tech.py` 公开 CLI 对合成材料实跑. AC-024 的七个例子分别构造,分别运行,分别留输入/输出/退出码, 不以一个汇总失败替代. |
| 验收25(@AC-025) | ISSUE-03 | 核对 navigate 对规格盘问,机械转正和终点验收的说明, 并对照 deliberate 原有独立四步和非 to-spec 调用关系. 两个场景分别核对. |
| 验收31-验收40(@AC-031至@AC-040) | ISSUE-02 | 对 verify-change 设计与执行/复验条文逐项语义核对, 包括每个 AC 的 normal/failure/edge,特殊输入,附条件与方法未知分支. 不以方案文字自证. |
| 验收41(@AC-041) | ISSUE-02, ISSUE-03 | ISSUE-02 核对 verify-change 与 REVERIFY; ISSUE-03 核对 navigate 和 README. 按同一条原场景检查来源,版本,确认与只补问变化决定的语义一致. |
| 规则1-规则8, 规则13-规则14 | ISSUE-01 | 对应上列 to-spec 流程文本入口, 核查用户亲答范围,场景生成,账本事实关系,分阶段确认,检查依据,修正分流,审计材料,不得替用户验收,原始答复最小化及两文件交付条件. |
| 规则9(审计) | ISSUE-01 | 对 to-spec 及配套材料逐项检查: 不设问题数量上限, 不把样张估算或精力参考写成上限. |
| 规则10(审计) | ISSUE-01, ISSUE-02 | 对 to-spec,verify-change,账本/交接引用和新增文件差异逐项检查: 无盘问专用记录格式, 免问不留痕, 现有领域维护与 handoff 规则仍适用. |
| 规则11(审计) | ISSUE-01, ISSUE-03, 全局集成检查 | issue 局部遵守仓库内修改和 deliberate 边界; 全切片集成后核对完整改动清单,历史文件/引用及 milestone-01 范围. 调度方在首轮产品修改前取得安装目录只读摘要, 集成时补取实施后摘要; 未观察时段列缺口. |
| 规则12(审计) | ISSUE-01, 全局集成检查 | ISSUE-01 实施并验证本分支编号格式和两种公开 CLI 回归. 全切片集成后再从基线到最终提交搜索 `workflow/` 与 `general/` 现行规则和历史命中, 逐项分类并核对中文编号/无前导零,固定节序,拉丁三位标签,`ISSUE-01` 及 milestone/history 例外. 不重做 milestone-01 汉化. |
| 规则15(审计) | ISSUE-01, ISSUE-03 | 差异与候选条文核对解析库,会话工具,展示服务复用情况, 确认未新增服务或外部数据依赖. |
| TECHNICAL.md 模块划分,模块接口和关键流程中的 to-spec 部分 | ISSUE-01 | 候选 to-spec 条文语义核对, 三份临时材料,草稿检查,机械转正/复制及失败保留路径检查; CLI 输出,文件原文和公开错误路径实跑. |
| TECHNICAL.md 模块划分,模块接口和关键流程中的 verify-change 部分 | ISSUE-02 | 候选 verify-change 条文语义核对: 输入边界,验证方式盘问,独立反方/成文检查,覆盖表,修订与复验. |
| TECHNICAL.md 模块划分,模块接口和关键流程中的 navigate/README 部分 | ISSUE-03 | ISSUE-03 局部按固定规格核对自己的候选条文. 三个 issue 合并后, 由全局集成检查交叉核对真实的 to-spec,verify-change,navigate/ACCEPTANCE-GUIDE 和 README 条文, README 由非作者复核. |
| TECHNICAL.md 脚本/文件约定与错误模式 | ISSUE-01 | `ac-draft.py` 公开 CLI 核验 JSON,成功/失败码,输入原文,正式目标保护,运行期间输入变化和原子替换; `check-ac.py` 核验 Gherkin/标签/编号/标记; `check-tech.py` 核验固定必备节,节名,节序和既有退出结果. |
| TECHNICAL.md 接缝与依赖 | ISSUE-01, ISSUE-02, ISSUE-03 | 分别核对 CLI 文件接缝及真实解析器,会话/handoff,present 展示入口和调用文档. 按既有依赖类别验证, 不替换内部模块或文件系统持久操作. |
| TECHNICAL.md 安全策略 | ISSUE-01, ISSUE-02 | 核对只传必要且脱敏的答复材料,展示只挂专用预览目录, 按 verification-contract 安全底线使用仓库外合成材料和保留原件. |
| VERIFICATION-PLAN.md 产品表70行 | ISSUE-01, ISSUE-02, ISSUE-03 | 所有场景行按 AC 组逐项映射到上表, 同号场景的每个 normal/failure/edge 均核对. AC-024 的七个例子各自实跑. 五条审计规则分别映射到规则9,10,11,12,15. |
| VERIFICATION-PLAN.md 工程检查: `workflow/to-spec/tests` | ISSUE-01 | 目标提交运行 `uv run pytest workflow/to-spec/tests`, 留依赖版本,收集清单,输出和退出码. |
| VERIFICATION-PLAN.md 工程检查: 仓库 `pytest.ini` 全量 | 全局完成定义 | ISSUE 集成后的同一完整提交在具备 Podman 的隔离环境运行 `uv run pytest`; 留完整清单与结果, 不使用 `--noconftest` 代替. |
| VERIFICATION-PLAN.md 工程检查: `check_skill.py` | 全局集成检查 | 全切片合并后从完整目标差异列出全部变更 `SKILL.md`, 每个文件逐一执行公开格式检查. 局部 issue 结果不替代最终清单. |
| milestone-01 编号汉化回归及完整差异审计 | 全局集成检查 | 对照 `REVIEW-milestone-01.md` 和已知9个文件, 检查基线到最终目标的完整差异,现行编号规则和历史例外. 不重做已完成汉化, 不以历史测试通过替代本次目标提交回归. |

## 全局风险和停止条件
- 已确认产品结果,范围,验收,安全约束,兼容承诺和固定技术选择不得改变. 新增或改变要求/决定时停止并交回既有确认流程.
- 发现输入不足,规格冲突,验证方法本身未知或真实入口不可观察时, 报具体缺口并停止相关 issue. 方法已知但资源暂缺可按已确认方案列条件, 执行缺条件记未验证, 不降标准.
- 并发保护须由真实公开 CLI 和外部进程完成, 留可复查时序. 不可证明实际处于校验后/替换前窗口时记未验证.
- 文件重叠只作为合并争用风险协调, 不作为 blocker. CLI 共用运行目录须使用不同隔离子目录, 不覆盖既有证据.
- 已安装技能目录仅取只读摘要, 不作修改. 调度方在首轮任何产品修改前安排取得实施前摘要, 全切片集成检查取得实施后摘要并按范围,时间比较. 不能追溯的历史时段明确记缺口, 不假定已观察或未变化.
- 生产环境,用户数据,无关文件,已有证据,正式规格,历史快照或已安装技能若可能被触碰, 立即停止并按现有授权规则处理.
