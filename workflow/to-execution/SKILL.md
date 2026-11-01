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

产物根目录按 `software-engineering-consensus` skill 的 产物根目录 词条确定; 我调用时另行指定则按指定, 除此之外不再确认. `<slug>` 用小写 kebab-case 短语概括该 issue 的交付内容, 如 `gatekeeper-read-write`.

# 起草垂直切片

把工作拆成 **tracer bullet** issues. 只有端到端可独立验证的切片, 才能让全新上下文窗口中的执行 agent 无需折返追问. 垂直切片规则:

- 每个切片都必须能从真实入口独立验证, 并能在全新上下文窗口内独立交付, 无需查阅本 issue 之外的材料. 它走过哪些层不规定
- 完成的切片本身可以演示
- 只有当前切片无法在保持边界和验证的前提下推进时, 才创建阻塞它的预重构 issue

为每个 issue 写出 **blocking edges**: 哪些其他 issues 必须先完成, 这个 issue 才能开始. 没有 blockers 的 issue 可以立即开始.

**宽重构是垂直切片的例外**: 一次机械改动 (重命名列, 改共享符号类型) 的 blast radius 扩散到整个代码库, 没有切片能独立保持绿色. 遇到这类变更时读 [refactor-expand-contract.md](refactor-expand-contract.md), 按其中的扩展-收缩序列拆分.

起草完成标准:

- 每个 AC 被至少一个拟议 issue 覆盖, 或明确说明无需执行任务.
- PRODUCT.md `业务规则` 节中标 (审计) 的断言都进覆盖矩阵并有承接条目 (人工验证或 issue).
- TECHNICAL.md 非功能要求与安全策略中的验证性要求均有承接.
- TECHNICAL.md 模块接口的每条不变量与错误模式, 要么有 TC 承接, 要么在所属 issue 的 `验证入口` 写明不用自动化测试的理由, 实际验证方式及通过标准.
- 每个切片能从真实入口独立验证, 可独立交付并能演示. 预重构 issue 与纯核验/非行为改动类 issue 不适用可演示判据, 改用承接 AC/BR 或核验入口证明价值.
- 每条 blocker 都是前置 issue 完成后本 issue 才能开始的真实依赖, blocker 图无环.
- 宽重构已按 refactor-expand-contract.md 拆分或明确不适用.

# 固化 Execution Spec 和 issues

拆分内容不送人工审核: 通过起草完成标准自检后直接固化, 产物根目录按约定落盘. 按 [模板](TEMPLATES.md) 生成拆分出的 issues, 再生成引用真实 issue 路径的 `EXECUTION.md`. 按依赖顺序编号. 确需编写自动化测试时才分配 TC (测试用例) 编号, 不因有 AC 就生成 TC. 已采用的 TC 编号全局唯一, 各 issue 自行编号, 无需集中分配: 覆盖某 AC 的主用例与 AC 同号 (`AC-005 -> TC-005`); 已确认且确需自动化的其他要求或同一 AC 的额外用例用 `TC-<issue 两位编号>-<两位序号>`, 如 ISSUE-02 的第一条额外用例为 `TC-02-01`. 不从编号规则反推要补用例. 信源与决策的引用路径按实际位置解析, 不假设它们位于产物根目录.
存在相关 DECISIONS.md 时, 每个 issue 单向引用相关决策 ID, 见 issue 模板的 相关决策 节. 引用只从产物指向账本: DECISIONS.md 是权威信源, 产物是派生视图, 账本不记录产物引用. 不新增或改变决策内容. 无相关决策时 issue 写"无".
不复制 PRODUCT.md/TECHNICAL.md 的正文, 只引用稳定 ID (AC/BR/G/NG) 或与模板逐字一致的固定节名, 以及执行所需摘要. 全局允许范围, 禁止范围, 完成定义, 验证策略只在 `EXECUTION.md` 写一次; issue 的对应节只写本 issue 的增量, 与全局相同就写"同全局".

完成标准:
`EXECUTION.md` 任务图中的每个引用可解析, 每个 AC/BR 和实际采用的 TC 都能在覆盖矩阵中追溯到验证入口;
每个实施 issue 有代码定位提示, `验证契约` 声明一种或多种变更类型及对应范围和证据要求, 并有可执行的验证入口; 确需新增自动化测试时, 接缝与用例写在该 issue 的验证入口里. 纯核验 issue 用纯核验模板, 只填核验栏目, 写明验证入口, 通过标准和完成证据; 宽重构特例写明原因, 共享 integration branch 与局部证据;
决策引用单向完整: 每个 issue 的 相关决策 节引用真实存在的决策 ID, 或已明确无相关决策.

使用 [模板](TEMPLATES.md) 写 `EXECUTION.md` 与每个 issue; 模板给出节名与节序, 逐字照抄.

只强制 issue 的 `验证契约`, `验证入口`, `交付证据` 三节; `允许范围` 与 `禁止范围` 在有增量或特有禁止项时写, 与全局相同则省略; 其余节按需保留, 没有内容就整节删掉, 不写 "无" "不适用" 占位.
只核验, 不修改成品的 issue 用模板里的纯核验版本: 只填核验栏目, 不套改动契约, 不新增实施分类.
