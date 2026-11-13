# workflow-stack-review milestone-10 决策账本

裁决执行哲学转向: 实现走最短交付路径, 交付物出来后从真实入口端到端验证闭环, 修复后重跑, 循环到闭环; 拆任务按垂直切片; 判据重心从过程是否按规定走移到交付物经真实运行确实达到要求. 本文件只出决策, 实施并入 milestone-07 与 milestone-11. 不追溯 milestone-04 与 milestone-09. 编号沿用本仓库先例: 各里程碑账本独立命名空间, 本文件 D001 起, F001 起.

验收标准: ../ACCEPTANCE.md 的 AC-10 各项, 已经我确认 (2026-10-31).

2026-10-31 独立反方 (未参与盘问与落盘) 提交 13 项发现, 我逐项核实全部成立, 无一驳回; 其中需要改决策的条目已按 decision-ledger 新建 ID 并标旧条已替代. 反方报告见 `OPPOSITION.md`.

## 决策

### D001 删除 tdd skill, 写法细节迁入 verification-contract
- 状态: 已替代 (→ D011)
- 约束性: 必须遵守
- 内容: 删除 `workflow/tdd/` (SKILL.md, tests.md, mocking.md) 与 README 技能表对应行. 理由: 红态取证纪律已在 verification-contract 缺陷修复节与 diagnosing-bugs 阶段 1 更权威地存在; 该 skill 的红绿步骤 (先写失败测试 → 先跑它 → 改最少代码 → 复跑) 属于规定实现过程, 与本里程碑的最短交付路径冲突; 全仓库无任何 skill 正文调用它 (F001), 删除后无悬空引用. 保留细节: `tests.md` (好/坏测试, 测试只看行为) 与 `mocking.md` (替身只在系统边界) 原样迁为 `workflow/verification-contract/reference/tests.md` 与 `reference/mocking.md`, 迁入时只修正自指句与相对链接 (F003), 不重写规则; verification-contract 正文在"按需自动化"条加一行按需指针: 需要写自动化测试时再读这两份, 不进每次调用的必读正文.
- 依赖事实: F001, F002, F003, F009
- 预计影响: `workflow/tdd/` (删除), `workflow/verification-contract/SKILL.md`, `workflow/verification-contract/reference/tests.md` 与 `reference/mocking.md` (新增), `README.md`; 实施在 milestone-07

### D002 何时不写自动化测试的判断并入缺陷修复节
- 状态: 已替代 (→ D012)
- 约束性: 必须遵守
- 内容: 把 tdd 的"何时用 / 不要用"收成一句放进 verification-contract 缺陷修复节: 能用低成本测试取证就用测试; 需要新建测试设施, 只能靠脆弱 mock, 环境耗时过长, 复现条件不清或要改动大量无关测试数据时, 改用定向脚本, 命令或日志断言取证, 并在交付证据里写明为什么没用测试. 理由: 这是"本次用什么取证"的判断, 缺陷修复的验证权威在 verification-contract; diagnosing-bugs 是硬 bug 诊断手法, 放它会漏掉轻量 bug. tdd 里"我或调用方明确要求先写失败测试"一条不收: 我的现场指令本身优先, 不需要 skill 复述.
- 依赖事实: F002
- 预计影响: `workflow/verification-contract/SKILL.md` 缺陷修复节; 实施在 milestone-07

### D003 垂直切片收词条进软件工程共识
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: `workflow/software-engineering-consensus/SKILL.md` 新增词条, 文本经我确认:

  **垂直切片 (tracer bullet)**:
  一次交付的工作切片, 本身端到端走通, 能从真实入口独立验证, 完成时即可演示. 切片穿过哪些层不构成判据.
  _避免_: 水平切片 (按层或按模块分期, 单期完成时演示不出任何完整结果), 任务分解

  理由: to-execution 已强制该切法 (F004), 但词条库没有, 模型拿不到这个先验; 按 D013 收录门槛 (我明确要求的概念按确认定义收录) 收录. 中文主词括注英文引导词, 与表内中文主词一致, 又借预训练先验.
- 依赖事实: F004, F008
- 预计影响: `workflow/software-engineering-consensus/SKILL.md`; 实施在 milestone-07

### D004 to-execution 完成标准加端到端可交付, 宽重构留例外
- 状态: 已替代 (→ D013)
- 约束性: 必须遵守
- 内容: 在 to-execution 起草完成标准的可判项列表加一条: 每个切片本身能端到端交付并能演示; 宽重构仍按 `refactor-expand-contract.md` 的扩展-收缩序列拆分, 端到端交付与演示由整合切片承担. 现有"垂直切片规则"与"每片须从真实入口独立验证"保留, 不重复改写. 理由: 缺的是自检时可判的一条, 水平分层这类错法只靠人发现; 加进完成标准而非 issue 模板, 避免第三处重复同一要求.
- 依赖事实: F004, F008
- 预计影响: `workflow/to-execution/SKILL.md`; 实施在 milestone-07

### D005 边开发边实跑改写为具体闭环, 唯一维护在 verification-contract
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 把 verification-contract 共用底线的"边开发边实跑"从笼统表述改成具体闭环: 实现走最短路径, 先产出能跑的可验证版本; 从真实入口对该版本跑端到端; 发现问题后修复, 再对同一端到端重跑, 既确认修复也暴露新问题, 循环到闭环; 不必等全部实现完成或启动无关部分, 只对实际跑过的范围下结论. 理由: 原文"随开发进度运行当前已实现的部分, 从当前可用入口验证"读起来无法落地, 我要的就是快速实现, 尽早验证, 修复再验证. 只写这一处 (drive-execution 步骤 1 已强制调用 verification-contract, F006), 不在 drive-execution 复制同义文本; 第二处同义文本正是 milestone-06 D004 要消的冗余. 2026-10-31 反方核实后收窄: 唯一维护的范围是**闭环机制** (时点与循环), 不是"真实入口/端到端"概念的全局唯一; 该概念在 F014 所列四处仍活跃, 本次不改, 也不声称概念级唯一.
- 依赖事实: F005, F006, F014
- 预计影响: `workflow/verification-contract/SKILL.md` 共用底线; 实施在 milestone-07

### D006 行为变更的端到端证据优先
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: verification-contract 行为变更节的完成证据补一句: 优先从真实使用入口端到端验证, 分层测试与自动化测试作补充, 不用它们代替端到端结论; 环境不可得时按既有口径报未验证缺口, 不用弱证据充抵. 理由: 现行证据要求只说"一条真实运行记录", 没限定入口层级, 单元级测试可以冒充; 这一条是把"判据重心在交付物"落到行为变更上.
- 依赖事实: F005
- 预计影响: `workflow/verification-contract/SKILL.md` 行为变更节; 实施在 milestone-07

### D007 结构变更与缺陷修复的做法句改证据口径
- 状态: 已替代 (→ D014)
- 约束性: 必须遵守
- 内容: 把两节的"做法"从规定步骤改成证据要求: 结构变更的交付证据须含改前与改后同一检查在相同输入和条件下的结果 (改前就应通过), 类型检查与 lint 不能单独证明行为未变; 缺陷修复的交付证据须含红态真实出现过的记录, 修复后同一检查通过, 原始场景复跑. 与 ADR 0023 "把先建立检查再改翻译成交付证据须含改前结果"对齐, 该 ADR 当时只落到 to-spec, verification-contract 没跟上. "调用 diagnosing-bugs" 指针与"红态必须先出现"的结论要求保留不动.
- 依赖事实: F005, F007
- 预计影响: `workflow/verification-contract/SKILL.md` 结构变更节与缺陷修复节; 实施在 milestone-07

### D008 mock 谨慎的理由落 verification-contract 共用底线
- 状态: 已替代 (→ D015)
- 约束性: 必须遵守
- 内容: 在"替身只在系统边界"后补一句理由与禁令: 过度 mock 会在真实实现之外攒出脆弱测试并掩盖真实行为; 不禁用 mock, 但不为速度 mock 实现细节. 关键依赖未经真实调用须说明未验证范围是既有条款, 不新增. 唯一维护处, 不另设词条.
- 依赖事实: F005
- 预计影响: `workflow/verification-contract/SKILL.md` 共用底线; 实施在 milestone-07

### D009 drive-execution 只加作者自跑与独立核验的分工
- 状态: 已替代 (→ D016)
- 约束性: 必须遵守
- 内容: 在独立核验节点写清: 作者侧端到端验证属开发回路内的自我纠错, 只用于发现和确认问题, 不作为验收证据, 也不得当作独立核验材料复用; 交付与否只由 verify-change 另起独立会话按已确认 PRODUCT.md 判定. 实现节不复制 D005 的闭环文本. 现有"核验只产证据, 不产验收结论"与"另起独立会话"措辞保留.
- 依赖事实: F006
- 预计影响: `workflow/drive-execution/SKILL.md` 独立核验节点; 实施在 milestone-07

### D010 新写 ADR 0025 记执行哲学, 说明替代关系
- 状态: 已替代 (→ D017)
- 约束性: 必须遵守
- 内容: 新增 `docs/adr/0025-shortest-delivery-path-end-to-end-loop.md`, 记本次执行哲学: 实现走最短交付路径, 不规定过程 (不强制先写测试或红绿顺序); 可验证版本出来后从真实入口端到端验证闭环, 修复后重跑同一端到端; 拆任务按垂直切片, 每片可独立端到端交付; 判据重心在交付物经真实运行达到要求; mock 谨慎; 环境不可得时报缺口不充抵. 文中写明它取代 ADR 0022 的 TDD 表述与 ADR 0023 中"tdd 重写为缺陷修复专用"的具体动作 (tdd 已删除), 旧 ADR 与历史变更文档原文不改. 理由: 仓库惯例是新文件记新决定 (ADR 0024, 0020 同理); 不写则半年后没人知道 tdd 为何消失.
- 依赖事实: F007
- 预计影响: `docs/adr/0025-shortest-delivery-path-end-to-end-loop.md` (新增); 本里程碑内完成

### D011 tdd 只迁 tests.md, mocking.md 有意丢弃
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 替代 D001 的迁移方式. 删除 `workflow/tdd/`, 只把 `tests.md` (好/坏测试, 测试只看行为) 迁为 `workflow/verification-contract/reference/tests.md`, 迁入时只修正自指句与相对链接. `mocking.md` 不迁移, 理由: 系统边界规则已在 verification-contract 共用底线条唯一维护, 两份并存会产生三处同谈 mock 且已有"数据库 (有时可以)"与"优先测试数据库"的微差; 其"为易于 mock 而设计"(依赖注入, SDK 风格接口) 属设计期的接口形态, 归 TECHNICAL.md 接缝与依赖节及写代码时的判断, 不属验证 skill. 丢弃后 verification-contract 正文在"按需自动化"条加一行指针指向 `reference/tests.md`.
- 依赖事实: F001, F002, F003, F009, F013
- 预计影响: `workflow/tdd/` (删除), `workflow/verification-contract/reference/tests.md` (新增), `workflow/verification-contract/SKILL.md`, `README.md`; 实施在 milestone-07
- 需要调整: D003 不受影响; 无其他引用方

### D012 修 bug 的链条对所有 bug 一样, 不分大小
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 替代 D002. 所有 bug 都走同一条链: 复现 → 定位原因 → 制定修复方案 → 执行修复 → 验证修好且没改坏. 没有"小修可以少走几步"的分类; 区别只在取证手段 (能用便宜测试就用测试, 不能用就用既有命令, 真实入口操作或日志). tdd 的"何时别用测试"清单里可留的判断并入这条: 需要新建测试设施, 只能靠脆弱 mock, 环境耗时过长, 只在生产特殊状态出现, 复现条件不清或要改动大量无关测试数据时, 改用非测试手段取证, 并在交付证据写明为什么没用测试. tdd 步骤 4 的两条判断一并留下: 先跑失败检查要确认失败原因是目标问题而非环境或测试代码自身, 意外通过先怀疑检查没覆盖症状. 我原 D002 里"小修可用脚本"的表述撤回: 那是把手段差异误说成规模差异.
- 依赖事实: F002, F015
- 预计影响: `workflow/verification-contract/SKILL.md` 缺陷修复节, `workflow/fix-bugs/SKILL.md` (改名后); 实施在 milestone-07 与 milestone-11

### D013 to-execution 就地改既有完成标准, 不新增同义条
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 替代 D004. 不新增完成标准条目, 就地改现有那条: 由"每个切片能从真实入口独立验证且可独立交付"改为"能从真实入口独立验证, 可独立交付并能演示"; 同条补例外: 预重构 issue (F017) 与纯核验/非行为改动类 issue 不适用可演示判据, 它们以承接 AC/BR 或核验入口的方式证明价值. 宽重构例外的现有说明不变. 理由: 现有条目与垂直切片规则已覆盖九成, 新增第二条同义条违反 milestone-06 D004 的消冗规矩; 而按字面要求全部切片可演示会误杀 to-execution 自己允许的预重构与准备类 issue.
- 依赖事实: F004, F008, F017
- 预计影响: `workflow/to-execution/SKILL.md` 起草完成标准; 实施在 milestone-07

### D014 结构变更改证据口径, 缺陷修复改走链条指针
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 替代 D007. 结构变更节: 删去"做法: 改前确定…建立可重复运行的行为检查"这类步骤句, 改成证据要求: 交付证据须含改前与改后同一检查在相同输入/条件下的结果, 改前就应通过; 类型检查与 lint 不能单独证明行为未变. 缺陷修复节: 完成证据现行文本已满足要求, 不改 (反方 O12: 我原 D007 的这半节是复述不是决策); "做法"句只把"调用 diagnosing-bugs"换成按 fix-bugs 的链条执行 (D012), 并补"补跑受影响范围"的证据要求 (D018).
- 依赖事实: F005, F007, F016
- 预计影响: `workflow/verification-contract/SKILL.md` 结构变更节与缺陷修复节; 实施在 milestone-07
- 需要调整: 缺陷修复节的 skill 名随 D019 改名

### D015 mock 谨慎只加理由句, 不再加清单
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 替代 D008. 在 verification-contract 共用底线"替身只在系统边界"后只补理由与禁令: 过度 mock 会在真实实现之外攒出脆弱测试并掩盖真实行为; 不禁用 mock, 但不为速度 mock 实现细节, 也不为让复现跑起来把内部逻辑换成假货. 不复制边界清单 (清单仍唯一在共用底线), 不另设词条. 原 D008"唯一维护处"的说法作废: 它只保证新句落点唯一, 现在清单也只在底线一处.
- 依赖事实: F005, F013
- 预计影响: `workflow/verification-contract/SKILL.md` 共用底线; 实施在 milestone-07

### D016 作者材料只作对照, 不作任何必验项通过依据
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 替代 D009. drive-execution 独立核验节点写明: 作者侧端到端验证记录属开发回路内的自我纠错材料, 在独立核验里只作对照, 不作任何必验项的通过依据; 关键真实路径的结论只取独立核验者本轮实跑. 这与现行 verify-change 第 4 与第 8 步一致 (作者日志/截图/自测只作对照, 不替代实跑), 因此**不改 verify-change**. 我原 D009 的"不得复用"措辞过宽, 作废.
- 依赖事实: F006, F015
- 预计影响: `workflow/drive-execution/SKILL.md` 独立核验节点; 实施在 milestone-07

### D017 ADR 0025 补齐取代范围
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 替代 D010 的取代声明部分. ADR 0025 除已写的"取代 ADR 0022 的 TDD 表述与 ADR 0023 中 tdd 重写动作"外, 补明它也取代 ADR 0023:12 末尾"退回新增功能默认写测试的旧口径"半句 (该半句与现行 tdd SKILL.md"新增功能不走本 skill"、INVENTORY 与本次不强制先写测试的裁决均相反, 按笔误处理, 原文不改). ADR 0025 同时补记修 bug 链条与 fix-bugs 定位 (D012) 与手段优先级 (D018).
- 依赖事实: F007, F015
- 预计影响: `docs/adr/0025-shortest-delivery-path-end-to-end-loop.md`; 本里程碑内完成

### D018 怎么保证没改坏, 以及手段优先级
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: (1) 修复后由未参与修复的复核者独立审查有没有改坏别处: 核对修复差异, 按复现指向的路径追调用方与合作方, 必要时跑项目既有检查或真实入口 (可选, 不强制跑自动化测试), 涉及共享接口/数据格式/跨模块路径时调 `blast-radius` 深查; (2) 复核结论写明检查了什么, 用了什么手段, 覆盖不到的写缺口, 不宣称"没改坏". 手段优先级 (按我 2026-10-31 的要求): 能靠代码库自身技术栈与既有入口做到的, 不用脚本; 顺序为 既有测试/既有开发命令/既有 CLI 入口 → 真实入口操作 → 必要时才写一次性临时脚本, 且不提交进仓库, 跑完清理, 交付证据只留可复跑命令与结果; 不在代码库新增专用脚本.
- 依赖事实: F015
- 预计影响: `workflow/verification-contract/SKILL.md` 缺陷修复节, `workflow/fix-bugs/SKILL.md`; 实施在 milestone-11

### D019 diagnosing-bugs 改名 fix-bugs
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: `workflow/diagnosing-bugs/` 改名为 `workflow/fix-bugs/`, skill name 与目录名一致, description 相应改为修 bug 时调用. 连带改活跃引用 (verification-contract 缺陷修复节, README 技能表, 其他 skill 正文中的调用语句, 以及本账本与 ADR 的新增表述); 历史变更文档与既有验收证据不改. 同时修正该 skill 的自述: 删去"本 skill 是一种诊断手段, 不是必经步骤"的说法, 改为"修 bug 的统一链条见 verification-contract 缺陷修复节; 本 skill 是这条链在难 bug 上的详细手法, 阶段 3/4 可省, 复现与验证不可省".
- 依赖事实: F015, F018
- 预计影响: `workflow/diagnosing-bugs/` → `workflow/fix-bugs/`, 引用方见内容; 实施在 milestone-11

### D020 fix-bugs 补两环: 修复方案与没改坏
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 在 fix-bugs 的阶段链里补两环: (a) 制定修复方案: 根因确定后先写清方案再动手, 方案含改动点, 影响范围, 备份与回滚考虑; 按 G1 条件决定是否先给我审 — 触发审核的六条: 改变对外可观察行为或既有约定 (接口, 数据格式, 配置项, 错误语义, 默认值); 要动共享接口, 跨模块路径或数据迁移; 有多条可行路线且取舍靠产品判断, 或要放弃现有功能; 触碰安全, 权限, 删除与数据保留语义; 隔离环境造不出复现, 需要生产数据, 生产插桩或新权限; 与已确认 spec 或决策冲突需改标准. 一句话: 只有"纯修错, 不动对外行为, 不超边界, 不碰安全"才由代理自行修. (b) 验证没改坏: 修复后由未参与修复的复核者独立审查受影响面, 手段按 D018 自选 (不强制跑自动化测试), 覆盖不到的写缺口, 并在阶段 6 清理前完成.
- 依赖事实: F015
- 预计影响: `workflow/fix-bugs/SKILL.md`; 实施在 milestone-11

### D021 fix-bugs 的三角色分工
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 调用 fix-bugs 的会话是调度方, 只分派与收口, 不亲自复现不写代码; 下设三角色: 诊断者 (在真实路径上复现, 最小化, 定位根因; 交付根因报告, 可复跑的复现命令或步骤, 复现环境的真实程度说明 — 哪些真实依赖, 哪些替身, 有无缺口; 不修), 修复者 (按根因定方案并修, 按 G1 决定是否先给我审, 修后跑复现命令, 原始场景与受影响基线), 复核者 (未参与前两步, 独立复跑复现与受影响检查, 核对替身没越界, 出报告). 简单 bug 允许把诊断者与修复者合成一人, 复核者不可省. 理由: 与 drive-execution 的总指挥/执行者/审核者同构, 角色再少就没人独立复核, 再多就是为拆而拆.
- 依赖事实: F015, F018
- 预计影响: `workflow/fix-bugs/SKILL.md` 与 `reference/`; 实施在 milestone-11

## 事实

### F001 tdd 没有 skill 调用方
- 状态: 已变更 (→ F011)
- 来源: 全仓库检索 `tdd` 于 `workflow/*/SKILL.md`, `workflow/*/reference/*.md`, `agent-prompts/`, `pi/`
- 内容: 命中仅在 `workflow/tdd/` 自身, `README.md` 第 56 行技能表, `general/writing-for-llm/SKILL-MECHANICS.md` 举例 (把 tdd 当引导词样例), 以及历史变更文档. 没有 skill 正文调用 tdd.

### F002 tdd 与既有 skill 的三处重叠
- 状态: 当前有效
- 来源: 逐节对照 `workflow/tdd/SKILL.md`, `workflow/diagnosing-bugs/SKILL.md`, `workflow/verification-contract/SKILL.md`
- 内容: 红态纪律在两个既有 skill 里都有 (verification-contract 缺陷修复节要求红态真实出现过并调用 diagnosing-bugs; diagnosing-bugs 阶段 1 核心就是构建能变红的紧凑循环); "测试只看行为"与"替身只在系统边界"已在 verification-contract 共用底线. tdd 的独有内容只有三样: 红绿步骤顺序, 何时别用测试的清单, 两份写法细节参考. 反方 O7 补正: 独有内容还有"意外通过先怀疑覆盖"与"排除环境或测试代码自身故障"两条判断, 现已并入 D012.

### F003 两份参考文件只含写法细节与自指句
- 状态: 当前有效
- 来源: `workflow/tdd/tests.md`, `workflow/tdd/mocking.md`
- 内容: tests.md 只有好/坏测试示例 (集成式, 实现细节, 同义反复); mocking.md 开头是"若尚未读过 verification-contract skill, 先调用它判断是否需要替代服务; 已读则沿用共用底线", 后面是系统边界清单与依赖注入/SDK 风格接口建议. 迁入 verification-contract 目录后该自指句必须改写; 反方 O4 指出其边界清单与 v-c 底线近乎逐字相同且已有微差, 因此 mocking.md 改为不迁移 (D011).

### F004 to-execution 已经强制垂直切片
- 状态: 当前有效
- 来源: `workflow/to-execution/SKILL.md` 起草垂直切片节与起草完成标准
- 内容: 正文已有"把工作拆成 tracer bullet issues", "每个切片都必须能从真实入口独立验证, 并能在全新上下文窗口内独立交付", "完成的切片本身可以演示", "宽重构是垂直切片的例外: ... 按 refactor-expand-contract.md 的扩展-收缩序列拆分". 起草完成标准的可判项里没有"端到端可交付并可演示"这一条. 反方 O2 补正: 完成标准已有"每个切片能从真实入口独立验证且可独立交付", 规则里已有"可演示", 真正增量只有"可演示进清单", 故 D013 改为就地改既有条而不新增.

### F005 verification-contract 待改的四段原文
- 状态: 当前有效
- 来源: `workflow/verification-contract/SKILL.md`
- 内容: (1) 共用底线"边开发边实跑": "涉及运行行为时, 在隔离测试环境随开发进度运行当前已实现的部分和必要的真实依赖, 从当前可用入口验证. 不必等整个功能完成或启动无关部分, 只对实际跑过的范围下结论."; (2) 共用底线"替身只在系统边界": 列出可替换的外部 API, 数据库, 时间与随机性, 有时文件系统, 与不可替换的自有模块, 内部协作者; (3) 行为变更: "做法: 逐项验证本次承诺的全部行为. 完成证据: 每条承诺行为一条真实运行记录, 含命令/操作, 输入, 实际输出与预期对比."; (4) 结构变更: "做法: 改前确定本次重构须保持的公开接口和旧行为, 用已有测试, 命令或脚本建立可重复运行的行为检查. 完成证据: 改前版本及相同输入/条件下的前后结果."; (5) 缺陷修复: "做法: 调用 diagnosing-bugs skill. 它要求先有能变红的检查; 检查是否为自动化测试由你按成本决定, 可用脚本, curl 或定向命令代替."; (6) 缺陷修复完成证据: "红态真实出现过的记录 (命令与失败输出), 修复后同一检查通过, 原始场景复跑结果, 留下的可复跑方式及检查缺口; 有关联的复现或修复提交时, 记录提交号."

### F006 drive-execution 的现有边界
- 状态: 已变更 (→ F012)
- 来源: `workflow/drive-execution/SKILL.md`, `workflow/drive-execution/reference/orchestration.md`
- 内容: 步骤 1 强制调用 verification-contract 核对各变更类型的验证要求与完成证据; 实现节点要求执行者按 issue 声明的验证契约实现并验证; 独立核验节点要求另起独立会话调用 verify-change, 且"核验只产证据, 不产验收结论". 正文无"端到端"字样; 端到端只在 reference 里出现为"全部 issues 集成后运行完成定义要求的整体验证, 含一次完整测试套件".

### F007 ADR 0022/0023 的 tdd 表述与仓库 ADR 惯例
- 状态: 当前有效
- 来源: `docs/adr/0022-per-issue-verification-contract.md`, `docs/adr/0023-verification-only-workflow.md`, `docs/adr/0020`, `docs/adr/0024`
- 内容: 0022 写"TDD 不再是每个 issue 的必经步骤, 采用自动化测试也不等于采用 TDD; 仅在决定用测试驱动开发时进入红绿循环"; 0023 写"tdd 重写为缺陷修复专用, 修 bug 且有低成本测试方法时才用", 同段末尾还有"退回「新增功能默认写测试」的旧口径"半句 (与现行 skill 与本次裁决相反). ADR 无 Status 字段, 惯例是新文件记新决定并在正文说明替代关系 (0020 取代早期方案, 0024 改名 prototype), 旧文件不改.

### F008 收录门槛与词条表格式
- 状态: 当前有效
- 来源: `docs/changes/workflow-stack-review/milestone-01/DECISIONS.md` D013, `workflow/software-engineering-consensus/SKILL.md`
- 内容: 收录门槛: 我明确要求加入的概念按确认定义收录; 代理主动提议的新词先过旧门槛 (至少两个 skill 共用, 或单 skill 但定义不显然) 再交我审定. 词条格式为加粗主词 + 一段定义 + `_避免_` 行; 现有词条 MVP, PoC, demo, 迭代都是中文主词.

### F009 verification-contract 目录现状
- 状态: 当前有效
- 来源: `ls workflow/verification-contract/`
- 内容: 只有 `SKILL.md` 与 `SAFETY.md`, 没有 `reference/` 目录; 迁入 tests.md 需新建目录. SKILL.md 里 SAFETY 指针用同目录相对路径.

### F010 历史变更文档已把 tdd 红绿降级
- 状态: 当前有效
- 来源: `docs/changes/verification-first-workflow/INVENTORY.md`
- 内容: 记有"先红后绿, 先写失败测试 | 做 | 降 (缺陷修复分支下可选)", "测试不绑实现, 通过公开接缝观察 | 验 | 移入 verification-contract", "接缝定义与测试放置 | 验 | 移入 verification-contract", "「需要 tdd 时必须调用 tdd skill」| 做 | 删". 删除 tdd 是那次降级的最后一步, 历史文档不改.

### F011 tdd 检索的完整命中 (修正 F001)
- 状态: 当前有效
- 来源: 反方报告 O11 与本轮复跑 `rg -i '\btdd\b'` (排除 `docs/changes/**`, `docs/adr/**`, vendor)
- 内容: 命中 `README.md:56`, `general/writing-for-llm/SKILL-MECHANICS.md:21` (命名举例), `workflow/tdd/SKILL.md` 自身, 以及 `tests/test_env_docs.py:3` 与 `tests/test_swt_list.py:11` 两处历史 docstring (「TDD 切片见 …」). 后两处是历史 issue 的测试注释, 不是 skill 调用, 不属活跃引用. 结论不变: 无 skill 正文调用 tdd.

### F012 drive-execution 全目录无"端到端"字样 (修正 F006)
- 状态: 当前有效
- 来源: `rg '端到端' workflow/drive-execution/` (反方 O11 与本轮复跑, 退出码 1)
- 内容: `workflow/drive-execution/` 含 reference 目录零命中"端到端". `orchestration.md:64` 的原句是"全部 issues 集成后运行 `EXECUTION.md` 完成定义要求的整体验证, 含一次完整测试套件", 表达整体验证概念, 不含"端到端"一词. F006 原表述"端到端只在 reference 里出现"错误.

### F013 mocking.md 与 v-c 底线重复及微差
- 状态: 当前有效
- 来源: `workflow/tdd/mocking.md:5-16` 与 `workflow/verification-contract/SKILL.md` 替身条逐字对照 (反方 O4)
- 内容: 两份边界清单近乎逐字相同 (可替换: 外部 API, 数据库, 时间随机性, 文件系统; 不可替换: 自己的模块, 内部协作者); 差异是 mocking.md 写"数据库 (有时可以, 但优先用测试数据库)", 底线写"数据库 (优先测试数据库)". mocking.md 后半"为易于 mock 而设计"给依赖注入与 SDK 风格接口建议, 属设计期接口形态.

### F014 真实入口/端到端概念的四处活跃表述
- 状态: 当前有效
- 来源: 反方 O13, 本轮逐行核对
- 内容: `workflow/software-engineering-consensus/SKILL.md:12` (MVP 词条: 验证按已确认标准从真实使用入口进行), `workflow/to-execution/SKILL.md:29` 与 `:31` (端到端可独立验证, 完成的切片可演示), `workflow/benchmark-checklist/SKILL.md:100` (微结果旁须附用户端到端路径实测), `workflow/drive-execution/reference/orchestration.md:64` (整体验证). 这些与 D005/D006 不矛盾; 本次不改, 也不声称概念级唯一维护.

### F015 diagnosing-bugs 的六阶段与相对五步链的缺口
- 状态: 当前有效
- 来源: `workflow/diagnosing-bugs/SKILL.md` 全文, 本轮逐阶段核对
- 内容: 阶段 1 构建能变红的紧凑循环 (含"没造出能变红的命令不进阶段 2"), 阶段 2 复现 + 最小化, 阶段 3 可证伪假设并先给我看, 阶段 4 单变量插桩, 阶段 5 修复与复验 (同一检查通过 + 原始场景复跑), 阶段 6 清理 (插桩移除, 保留可复跑命令). 缺口: 无"制定修复方案"环 (阶段 5 直接应用修复); 无"跑受影响相邻检查确认没改坏"要求; 开头"本 skill 是一种诊断手段, 不是必经步骤"与我 2026-10-31 确认的"所有 bug 都走同一条链"相悖. 反方 O8 指出 v-c 缺陷修复节的"做法: 调用 diagnosing-bugs"是义务语气, 与该自述冲突.

### F016 v-c 缺陷修复完成证据已是现行文本
- 状态: 当前有效
- 来源: `workflow/verification-contract/SKILL.md` 缺陷修复节 (F005 第 6 条)
- 内容: 现行完成证据已含红态记录, 修复后同一检查通过, 原始场景复跑, 可复跑方式与检查缺口. 反方 O12 指出我原 D007 的缺陷修复半节与此逐点相同, 属复述; D014 因此只保留结构变更半节的内容改动.

### F017 to-execution 允许的预重构与准备类 issue
- 状态: 当前有效
- 来源: `workflow/to-execution/SKILL.md:33` 与 issue 模板"覆盖依据"节
- 内容: 允许"只有当前切片无法在保持边界和验证的前提下推进时, 才创建阻塞它的预重构 issue"; 模板允许"准备类 issue 无 AC 时写 G-001/NG-001/BR-001". 这两类天然不产出可演示结果; milestone-04 已产出的 ISSUE-05 (ADR 记录, 非行为改动) 与 ISSUE-06 (纯核验) 即实例. 故 D013 必须为它们补例外.

### F018 调用 diagnosing-bugs 的活跃引用点
- 状态: 当前有效
- 来源: 本轮 `rg 'diagnosing-bugs'`
- 内容: 活跃引用在 `workflow/verification-contract/SKILL.md` 缺陷修复节与 `README.md` 技能表; `workflow/tdd/SKILL.md` 另有引用但该 skill 本次删除. 改名 fix-bugs 时须同步这两处, 历史变更文档与既有验收证据不改.
