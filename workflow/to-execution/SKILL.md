---
name: to-execution
description: 将 Product/Technical Spec 拆成 LLM 可执行的 Execution Spec 和垂直切片 issues.
disable-model-invocation: true
---

开始前, 调用 `domain-awareness` skill 感知当前工作目录的领域模型, 调用 `verification-contract` skill 确定每类 issue 的验证方式与证据.

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

把工作拆成 **tracer bullet** issues. 只有端到端可独立验证的切片, 才能让全新上下文窗口中的执行 agent 无需折返追问. 垂直切片规则 (tdd skill 的 横向/纵向切片 讲测试与实现的推进顺序, 与这里的层覆盖无关):

- 每个切片都走过本变更涉及的适用层的窄而 **完整** 路径, 例如 schema, API, UI, tests. 它是垂直切片, 不是单层切片
- 完成的切片本身可以演示, 或可独立验证
- 每个切片都让接受者在一个全新上下文窗口内完成, 无需查阅本 issue 之外的材料
- 只有当前切片无法在保持边界和验证的前提下推进时, 才创建阻塞它的预重构 issue

为每个 issue 写出 **blocking edges**: 哪些其他 issues 必须先完成, 这个 issue 才能开始. 没有 blockers 的 issue 可以立即开始.

**宽重构是垂直切片的例外**: 一次机械改动 (重命名列, 改共享符号类型) 的 blast radius 扩散到整个代码库, 没有切片能独立保持绿色. 遇到这类变更时读 [refactor-expand-contract.md](refactor-expand-contract.md), 按其中的扩展-收缩序列拆分.

起草完成标准: 每个 AC 被至少一个拟议 issue 覆盖或明确说明无需执行任务; PRODUCT.md `业务规则` 节中标 (审计) 的断言必须进覆盖矩阵并有承接条目 (人工验证或 issue); TECHNICAL.md 非功能要求/安全策略中的验证性要求均有承接; TECHNICAL.md 模块接口的每条不变量/错误模式, 要么有 TC 承接, 要么在所属 issue 的 `验证入口` 节写明验证方式, 不测理由及通过标准; 每个切片符合上述垂直切片规则; 每条 blocker 都是前置 issue 完成后本 issue 才能开始的真实依赖, 且 blocker 图无环; 宽重构已按 refactor-expand-contract.md 拆分或明确不适用.

# 固化 Execution Spec 和 issues

拆分内容不送人工审核: 通过起草完成标准自检后直接固化, 产物根目录按约定落盘. 按模板生成拆分出的 issues, 再生成引用真实 issue 路径的 `EXECUTION.md`. 按依赖顺序编号. TC (测试用例) 编号全局唯一且无需集中分配: 覆盖某 AC 的主用例与 AC 同号 (`AC-005 -> TC-005`), 同一 AC 的额外用例和审计 BR 用例从 `TC-101` 起顺序编号. 信源与决策的引用路径按实际位置解析, 不假设它们位于产物根目录. 
存在相关 DECISIONS.md 时, 每个 issue 单向引用相关决策 ID, 见 issue 模板的 相关决策 节. 引用只从产物指向账本: DECISIONS.md 是权威信源, 产物是派生视图, 账本不记录产物引用. 不新增或改变决策内容. 无相关决策时 issue 写"无".
不复制 PRODUCT.md/TECHNICAL.md 的正文, 只引用稳定 ID (AC/BR/G/NG) 或与模板逐字一致的固定节名, 以及执行所需摘要.

完成标准: 
`EXECUTION.md` 任务图中的每个引用可解析, 每个 AC/BR 和实际采用的 TC 都能在覆盖矩阵中追溯到验证入口;
每个实施 issue 有代码定位提示, 五类之一的 `验证契约` 及可执行的验证入口; 采用测试推进的 issue 还有测试切片. 纯核验任务注明没有实施改动, 写明验证入口与完成证据; HITL/integration 特例写明原因和局部证据;
决策引用单向完整: 每个 issue 的 相关决策 节引用真实存在的决策 ID, 或已明确无相关决策.

使用下方模板写 `EXECUTION.md`.

```markdown
# <变更标题> Execution Spec
## 权威输入与决策引用
- Product Spec: `<PRODUCT.md 实际路径>`
- Technical Spec: `<TECHNICAL.md 实际路径>`
- 决策引用 (只读, 非意图来源): `<DECISIONS.md 实际路径>` 或"无"
## 全局允许范围
- 以 TECHNICAL.md 模块划分末尾的模块/目录边界为准, 列可修改的模块, 目录, 文件模式或行为范围.
## 全局禁止范围
- 不可修改的模块, API, schema, 行为或 PRODUCT.md 非目标 (NG-NNN).
## 完成定义
- build/lint/test/benchmark/人工验证及通过标准. 完整测试套件默认在此要求, 只在合并节点跑一次; 确实不适用时写明理由和替代验证.
## 验证策略
- AC 与标 (审计) 的 BR 断言对应的验证方式与入口; 采用测试时, 接缝与测试适配器以 TECHNICAL.md 测试接缝映射表为唯一来源.
- 每个实施 issue 按 `verification-contract` skill 选择一类契约, 写清将交付的证据; 需要测试推进时给出测试切片. 纯核验任务写明核验入口和证据.
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
实施结果或纯核验任务的核验结果.
## 覆盖依据
- Product: `<PRODUCT.md 实际路径>`, AC-001
- Technical: `<TECHNICAL.md 实际路径>`, <节名> (如 模块接口/测试接缝/非功能要求; 无对应节则写"无")
## 相关决策
- `<DECISIONS.md 实际路径>`: D001. 无则写"无".
## 允许范围
可以修改的模块, 目录, 文件模式或行为范围.
## 禁止范围
明确不能修改的模块, API, schema, 行为或非目标.
## 代码定位提示
实施任务写入口文件, 相关模块, 已有测试位置和必要阅读顺序; 纯核验任务写相关入口位置. 只写定位线索, 不写逐文件实现计划.
## 验证契约
- 契约: <行为变更 / 结构变更 / 缺陷修复 / 性能改进 / 非行为改动, 五选一; 判据见 verification-contract skill>.
- 完成证据: <本 issue 须交付的可复核材料, 落点为下方交付证据节>.
- 纯核验任务: 无实施改动时略本节, 在验证入口写明核验内容和完成证据.
## 测试切片 (条件保留)
仅采用测试推进时保留本节; 其余在验证入口写明验证方式, 无需专门补一个空的测试切片.
- TS-001:
  接缝: TECHNICAL.md 测试接缝映射表中该 AC 对应的接缝与测试适配器; 结构变更可引用既有行为检查.
  测试用例: TC-001 或结构变更所用的既有检查入口.
  检查形态: 先红后绿 (缺陷修复, 或行为变更里锁行为的测试), 或先绿保绿 (结构变更的既有行为检查). 先红写预期失败原因; 先绿写它描述的是哪条既有行为.
  最小实现范围: 让该检查成立所需的最小改动范围.
  不得测试: 内部实现, 私有方法, 内部协作者调用次数或未确认用例.
  覆盖: AC-001.
## 验证入口
事先写可复跑的操作, 环境/输入及通过标准; 不采用测试覆盖某条 TECHNICAL.md 不变量/错误模式时在此写明理由.
## 交付证据
执行后填写实际操作, 脱敏后的结果及可复查的材料位置; 它们要对应验证契约和验证入口.
## 风险提示
已知高风险点和防护.
## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
## 适合 AFK 的原因
无需进一步产品/API/架构决策的证据. 不适合时写明 HITL 原因.
## 验收标准
- [ ] 与覆盖依据一致的可观察标准.
## Integration 特例 (条件保留)
仅当本 issue 属于宽重构的不可独立领取序列时保留, 否则整节省略: 共享 integration branch, 本 issue 的局部完成证据, 最终整合验证 issue 的引用.
## 被阻塞于
- ISSUE 引用. 无则写"无".
```
