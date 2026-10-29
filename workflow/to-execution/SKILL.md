---
name: to-execution
description: 将 Product/Technical Spec 拆成 LLM 可执行的 Execution Spec 和垂直切片 issues.
disable-model-invocation: true
---

开始前, 调用 `domain-awareness` skill 感知当前工作目录的领域模型, 调用 `verification-contract` skill 确定每个 issue 的变更类型, 验证方式与证据.

# 检查权威输入

产物根目录下是否已有 `PRODUCT.md` 和 `TECHNICAL.md`? 缺任一份先调用 `to-spec` skill 生成, 再继续.
权威输入定义全部意图, 代码事实只验证可行性和既有形状. 权威输入之间如有冲突, 或需要新增/改变决策内容时, 调用 `deliberate` skill 敲定并固化, 再继续.

# 目标

把变更拆成多个单会话可容纳的垂直切片 `ISSUES`, 再用 `EXECUTION.md` 记录任务全局视角. 每个 issue 在一个全新的上下文窗口中交付, 执行 agent 沿 `EXECUTION.md` 的任务图领取, 于是单个会话的上下文上限不再截断整个变更.

# 输出

本 skill 的产物统称为 Execution Spec, 只供 LLM 使用, 我不会阅读它们:

`<产物根目录>/EXECUTION.md`
`<产物根目录>/issues/ISSUE-<NN>-<slug>.md`, 从 `ISSUE-01` 连续编号.

产物根目录约定为 `docs/changes/<feature-slug>/`; 我调用时另行指定则按指定, 除此之外不再确认. `<slug>` 用小写 kebab-case 短语概括该 issue 的交付内容, 如 `gatekeeper-read-write`.

# 起草垂直切片

把工作拆成 **tracer bullet** issues. 只有端到端可独立验证的切片, 才能让全新上下文窗口中的执行 agent 无需折返追问. 垂直切片规则:

- 每个切片都必须能从真实入口独立验证, 并能在全新上下文窗口内独立交付, 无需查阅本 issue 之外的材料. 它走过哪些层不规定
- 完成的切片本身可以演示
- 只有当前切片无法在保持边界和验证的前提下推进时, 才创建阻塞它的预重构 issue

为每个 issue 写出 **blocking edges**: 哪些其他 issues 必须先完成, 这个 issue 才能开始. 没有 blockers 的 issue 可以立即开始.

**宽重构是垂直切片的例外**: 一次机械改动 (重命名列, 改共享符号类型) 的 blast radius 扩散到整个代码库, 没有切片能独立保持绿色. 遇到这类变更时读 [refactor-expand-contract.md](refactor-expand-contract.md), 按其中的扩展-收缩序列拆分.

起草完成标准: 每个 AC 被至少一个拟议 issue 覆盖或明确说明无需执行任务; PRODUCT.md `业务规则` 节中标 (审计) 的断言必须进覆盖矩阵并有承接条目 (人工验证或 issue); TECHNICAL.md 非功能要求/安全策略中的验证性要求均有承接; TECHNICAL.md 模块接口的每条不变量/错误模式, 要么有 TC 承接, 要么在所属 issue 的 `验证入口` 节写明不用自动化测试的理由, 实际验证方式及通过标准; 每个切片能从真实入口独立验证且可独立交付; 每条 blocker 都是前置 issue 完成后本 issue 才能开始的真实依赖, 且 blocker 图无环; 宽重构已按 refactor-expand-contract.md 拆分或明确不适用.

# 固化 Execution Spec 和 issues

拆分内容不送人工审核: 通过起草完成标准自检后直接固化, 产物根目录按约定落盘. 按模板生成拆分出的 issues, 再生成引用真实 issue 路径的 `EXECUTION.md`. 按依赖顺序编号. 确需编写自动化测试时才分配 TC (测试用例) 编号, 不因有 AC 就生成 TC. 已采用的 TC 编号全局唯一, 各 issue 自行编号, 无需集中分配: 覆盖某 AC 的主用例与 AC 同号 (`AC-005 -> TC-005`); 已确认且确需自动化的其他要求或同一 AC 的额外用例用 `TC-<issue 两位编号>-<两位序号>`, 如 ISSUE-02 的第一条额外用例为 `TC-02-01`. 不从编号规则反推要补用例. 信源与决策的引用路径按实际位置解析, 不假设它们位于产物根目录.
存在相关 DECISIONS.md 时, 每个 issue 单向引用相关决策 ID, 见 issue 模板的 相关决策 节. 引用只从产物指向账本: DECISIONS.md 是权威信源, 产物是派生视图, 账本不记录产物引用. 不新增或改变决策内容. 无相关决策时 issue 写"无".
不复制 PRODUCT.md/TECHNICAL.md 的正文, 只引用稳定 ID (AC/BR/G/NG) 或与模板逐字一致的固定节名, 以及执行所需摘要. 全局允许范围, 禁止范围, 完成定义, 验证策略只在 `EXECUTION.md` 写一次; issue 的对应节只写本 issue 的增量, 与全局相同就写"同全局".

完成标准: 
`EXECUTION.md` 任务图中的每个引用可解析, 每个 AC/BR 和实际采用的 TC 都能在覆盖矩阵中追溯到验证入口;
每个实施 issue 有代码定位提示, `验证契约` 声明一种或多种变更类型及对应范围和证据要求, 并有可执行的验证入口; 确需新增自动化测试时, 接缝与用例写在该 issue 的验证入口里. 纯核验 issue 用纯核验模板, 只填核验栏目, 写明验证入口, 通过标准和完成证据; 宽重构特例写明原因, 共享 integration branch 与局部证据;
决策引用单向完整: 每个 issue 的 相关决策 节引用真实存在的决策 ID, 或已明确无相关决策.

使用下方模板写 `EXECUTION.md`.

```markdown
# <变更标题> Execution Spec
## 权威输入与决策引用
- Product Spec: `<PRODUCT.md 实际路径>`
- Technical Spec: `<TECHNICAL.md 实际路径>`
- 决策引用 (只读, 非意图来源): `<DECISIONS.md 实际路径>` 或"无"
## 评审起点
- 首次派工前由 `drive-execution` 填入完整提交号与核实依据; 此前写"待填".
## 全局允许范围
- 以 TECHNICAL.md 模块划分末尾的模块/目录边界为准, 列可修改的模块, 目录, 文件模式或行为范围.
## 全局禁止范围
- 不可修改的模块, API, schema, 行为或 PRODUCT.md 非目标 (NG-NNN).
## 完成定义
- build/lint/test/benchmark/人工验证及通过标准. 每轮合并后跑本轮受影响的检查; 全部 issues 集成后跑一次完整测试套件. 涉及共享底层或高风险迁移时, 写明在哪个节点提前跑全套及理由. 确实不适用时写明理由和替代验证.
## 验证策略
- 每个 AC 与标 (审计) 的 BR 有验证入口. 按已调用的 `verification-contract` skill 选择适用的变更类型, 确定对应范围并安排各类型需要的验证; 无测试环境或可复查数据位置时写阻塞, 不安排生产测试. 采用自动化测试时, 接缝与适配器取自 TECHNICAL.md 测试接缝映射表, 不因每个 AC 都有映射就逐条生成测试.
- 实施 issue 的验证要求和所需证据覆盖全部已选类型; 确需自动化测试时把接缝与用例写进各 issue 的验证入口. 纯核验 issue 用纯核验模板.
## 任务图
- ISSUE-01: `issues/ISSUE-01-<slug>.md`; 覆盖: AC-001; 依赖: 无.
## 覆盖矩阵
- AC-001 -> ISSUE-01 -> 验证入口 (采用测试时加 TC-001).
- BR-003 (审计) -> 人工验证: <验证方式及通过标准>. 或承接为 issue: BR-003 -> ISSUE-02 -> 验证入口.
- 非功能要求 (TECHNICAL.md 节锚) -> ISSUE-02 -> 验证入口.
## 全局风险和停止条件
- 需要改变 PRODUCT/TECHNICAL/DECISIONS 时停止.
- 需要扩大允许范围或触碰禁止范围时停止.
- Spec 与代码事实冲突或无法提供完成证据时停止.
```

使用下方模板写每个 issue.

```markdown
## 父级
- `../EXECUTION.md`
## 执行
- [ ] 已完成
## 要交付什么
实施结果.
## 覆盖依据
- Product: `<PRODUCT.md 实际路径>`, AC-001; 准备类 issue 无 AC 时写 G-001/NG-001/BR-001.
- Technical: `<TECHNICAL.md 实际路径>`, <节名> (如 模块接口/接缝与依赖/非功能要求; 无对应节则写"无")
## 相关决策
- `<DECISIONS.md 实际路径>`: D001. 无则写"无".
## 允许范围
本 issue 相对 `EXECUTION.md` 全局允许范围的增量; 与全局相同写"同全局".
## 禁止范围
本 issue 特有的禁止项; 与全局相同写"同全局".
## 代码定位提示
实施任务写入口文件, 相关模块, 已有测试位置和必要阅读顺序. 只写定位线索, 不写逐文件实现计划.
## 验证契约
- 变更类型: <行为变更 / 结构变更 / 缺陷修复 / 性能改进 / 非行为改动, 可多选; 判据见 verification-contract skill>.
- 对应范围: <各类型对应的交付结果和改动范围>.
- 验证要求/证据: <逐类写明验证要求和所需证据, 覆盖全部已选类型; 实际结果记入下方交付证据节>.
## 验证入口
事先写可复跑的操作, 环境/输入及通过标准; 不采用测试覆盖某条 TECHNICAL.md 不变量/错误模式时在此写明理由.
## 交付证据
执行后填写实际操作, 脱敏后的结果及可复查的材料位置; 它们要对应验证契约和验证入口.
## 风险提示 (按需)
有已知高风险点才写; 否则整节省略.
## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
## 验收标准
- [ ] 与覆盖依据一致的可观察标准.
## Integration 特例 (条件保留)
仅当本 issue 属于宽重构的不可独立领取序列时保留, 否则整节省略: 共享 integration branch, 本 issue 的局部完成证据, 最终整合验证 issue 的引用.
## 被阻塞于
- ISSUE 引用. 无则写"无".
```

只核验, 不修改成品的 issue 用下方纯核验模板: 只填核验栏目, 不套改动契约, 不新增实施分类.

```markdown
## 父级
- `../EXECUTION.md`
## 执行
- [ ] 已完成
## 要核验什么
本次要确认的结果, 及其对应的 AC/BR/非功能要求.
## 覆盖依据
- Product: `<PRODUCT.md 实际路径>`, AC-001 或 G-001/BR-001.
- Technical: `<TECHNICAL.md 实际路径>`, <节名; 无则写"无">
## 相关决策
- `<DECISIONS.md 实际路径>`: D001. 无则写"无".
## 代码定位提示
相关入口位置, 只写定位线索.
## 验证入口
事先写可复跑的操作, 环境/输入及通过标准.
## 完成证据
执行后填实际操作, 脱敏后的结果及可复查材料位置, 对应验证入口与通过标准.
## 风险提示
已知高风险点和防护.
## 停止条件
需要改变任一 Spec, 决策或核验范围时停止.
## 适合 AFK 的原因
无需进一步产品/API/架构决策的证据. 不适合时写明 HITL 原因.
## 验收标准
- [ ] 与验证入口和通过标准一致的可观察结论.
## 被阻塞于
- ISSUE 引用. 无则写"无".
```
