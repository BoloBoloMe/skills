# Verification Contract

## 适用时机

当 HILP 蓝图需要把测试承诺、验收口径或 execution_unit 的完成条件交接给 HILE 时，使用本契约。它只把已批准设计和已批准蓝图中的承诺结构化，不新增执行阶段判断。

## 核心对象

### Truths

Truths 是已批准资产中必须保持为真的事实、约束或决策。每条 Truth 必须绑定来源资产、章节或行文片段，并说明它保护的业务或治理边界。

### Artifacts

Artifacts 是能够证明 Truths 被实现或被遵守的产物。Artifact 可以是文件、配置、测试、文档段落、执行记录或人工检查记录，但必须有稳定路径或可复核标识。

### Key Links

Key Links 是 Truths 与 Artifacts 之间的证据链。每条 Key Link 必须说明哪个 Artifact 用哪一级验证证明哪个 Truth，避免把“已修改文件”误当作“已满足承诺”。

## must_haves 对照表

每个蓝图或 execution_unit 的 `must_haves` 必须使用下表结构记录。为保证 Markdown 预览能正确渲染，表格前后各保留一个空行，分隔行固定为 `|---|---|---|---|---|---|---|`，单元格内禁止出现未转义 `|`；需要列多项时用 `<br>`，不要在单元格里写 Markdown 列表。

| must_have_id | Truths | Artifacts | Key Links | 验证层级 | 完成标准 | 未覆盖风险 |
|---|---|---|---|---|---|---|
| MH-001 | 已批准设计或蓝图中的必须满足项 | 证明该项的文件、测试或记录 | Truth 与 Artifact 的映射说明 | 静态检查 / 命令执行 / 行为测试 / 人工检查 | 可复核的通过条件 | 无覆盖时必须写明并进入重审判断 |

约束：
- `must_haves` 不得包含待审批、草稿、待修订或已归档资产中的绑定性设计或蓝图内容。
- `must_haves` 不得留给 HILE 在执行阶段临场定义验收口径。
- 每个必须满足项至少有一条 Key Link；无法建立 Key Link 时，蓝图不得交接执行。
- 涉及 `execution_plan_contract` 时，Key Links 必须覆盖 `parallelization`、`parallel_group`、`parallel_eligible`、`file_domain`、`shared_state` 和 `verification_resources` 的静态证据，证明并行资格和验证资源不是由 HILE 临场补齐。

## Must-haves Verification Ladder

验证梯度从低到高为：

1. 静态检查：通过 grep、diff、schema lint、文档字段检查等方式确认结构、字段、路径或禁止项存在 / 不存在。
2. 命令执行：运行构建、测试、脚本或项目约定命令，并记录命令、退出码和输出摘要。
3. 行为测试：用复现用例、端到端路径或可观察行为证明 Truth 被满足，不能只证明文件被修改。
4. 人工检查：当自动证据不足以覆盖治理、审批、风险或语义一致性时，由执行者记录人工核验对象、依据和结论。

选择规则：
- 能用低层级完整证明的，不强制升层级。
- 低层级只能证明结构存在时，必须补充命令执行、行为测试或人工检查。
- 人工检查不能替代可运行命令；只能覆盖自动化无法证明的语义、审批和治理边界。

## 完成门槛

声明完成前必须同时满足：

- 每个 `must_haves` 项均有 Truths、Artifacts、Key Links 和对应验证层级。
- 已运行蓝图或 execution_unit 指定的验证命令，并记录退出码与输出摘要。
- 未覆盖风险已记录；若风险改变接口、数据形状、验证口径、发布顺序或禁止越界项，必须停止并进入重审。
- HILE 只核验已批准蓝图和执行交接摘录的验证承诺，不在执行阶段补做蓝图判断。
- 涉及并行调度时，完成证据必须能追溯到已批准 `execution_plan_contract` 中的 `parallelization`、`parallel_group`、`parallel_eligible` 和 `verification_resources`。
- 完成声明包含重审结论：`no-reapproval-needed` 或 `requires-reapproval`。
