# PRD Examples

Use these examples to calibrate output shape. Do not copy the sample content directly unless it matches the user's request. Preserve entity separation from `id-prefix-registry.md`: `FR-*` rows are buildable behavior, `EVT-*` rows belong in tracking specs, and `RISK-*` rows belong in risk registers.

## Example 1: Chinese Lite PRD from a short idea

**Input**

> 给订单列表加一个批量导出按钮。

**Output style**

```markdown
# Lite PRD：订单列表批量导出

## 1. 执行摘要
- 问题：运营人员需要从订单列表中批量导出订单数据，用于线下对账或分析；当前导出能力未明确。
- 方案：在订单列表增加批量选择与导出入口，支持按当前筛选条件或勾选订单导出。
- 主要用户：运营 / 财务 / 商家后台管理员。
- 预期结果：降低人工复制和临时取数成本。

## 2. 已确认事实、假设与待确认事项
| ID | 类型 | 内容 | 当前处理方式 | 决策影响 |
|---|---|---|---|---|
| ASM-001 | 假设 | 导出范围仅限当前用户有权限查看的订单 | 作为权限规则写入 | 影响数据安全与验收 |
| TBD-001 | 待确认 | 单次最大导出条数 | 暂按 5,000 条设计 | 影响性能、异步导出和提示文案 |

## 3. 范围
| 项目 | 范围 | 优先级 | 说明 |
|---|---|---|---|
| 勾选订单导出 | In | P0 | 支持用户选择订单后导出 |
| 按筛选条件导出 | In | P1 | 若成本高可延期 |
| 导出历史页 | Out | P2 | 本期不建设完整下载中心 |

## 4. 关键需求
| 需求 ID | 需求 | 优先级 | 验收 |
|---|---|---|---|
| FR-001 | 用户可在订单列表勾选多条订单并点击“导出” | P0 | AC-001 |
| FR-002 | 无订单被选中时，导出按钮置灰或提示先选择订单 | P0 | AC-002 |

## 5. 验收标准
| AC ID | 需求 ID | 场景 | 预期结果 |
|---|---|---|---|
| AC-001 | FR-001 | 用户勾选 2 条订单并点击导出 | 系统开始导出，导出内容仅包含这 2 条订单 |
| AC-002 | FR-002 | 用户未勾选订单点击导出 | 不触发导出，并提示“请先选择要导出的订单” |
```

## Example 2: Chinese PRD Review

**Input**

> 审查这份 PRD：我们要优化注册体验，让用户更容易完成注册。支持手机号注册，页面更流畅，上线后看转化率。

**Output style**

```markdown
## 评审结论
Needs revision（需修改）

当前方向合理，但还不能进入研发。主要问题是目标、范围、异常状态、验收标准和指标口径都不够明确。

## 阻塞项
| 问题 | 影响 | 为什么阻塞 | 必须修复 |
|---|---|---|---|
| “更容易完成注册”没有定义 | 设计和研发无法判断要优化哪些步骤 | 会导致方案发散 | 明确目标漏斗、目标用户、当前基线和期望提升方向 |
| 手机号注册规则缺失 | QA 无法验证，研发无法实现完整流程 | 涉及验证码、频控、错误提示、安全 | 补充手机号格式、验证码、重发、错误次数、风控规则 |

## 分维度评分
| 维度 | 分数 | 主要问题 |
|---|---:|---|
| 策略与背景 | 5/10 | 只有解决方案，没有现状和用户问题 |
| 范围控制 | 4/10 | 未说明是否包含验证码、第三方登录、已有账号绑定 |
| 可测试性 | 3/10 | 没有验收标准 |

## 建议改写片段
### 验收标准
| AC ID | 需求 ID | 场景 | 前置条件 | 操作 | 预期结果 |
|---|---|---|---|---|---|
| AC-001 | FR-001 | 新用户使用合法手机号注册 | 手机号未注册 | 输入手机号并获取验证码 | 系统发送验证码并进入验证码输入状态 |
```

## Example 3: AI Feature PRD with targeted safety sections

**Input**

> Write a PRD for an AI assistant that summarizes support tickets and suggests replies.

**Output style**

```markdown
# PRD: AI Support Ticket Summary and Reply Suggestions

## Executive summary
- Problem: Support agents spend time reading long ticket histories and drafting repetitive replies.
- Proposed solution: Generate a ticket summary and suggested reply, with agent review required before sending.
- PRD tier: Standard + targeted AI safety sections by default. Escalate to full Complex only if a second Complex anchor is confirmed, such as cross-functional compliance/security signoff, external partner integration, non-trivial rollback, or launch-critical automation.

## Confirmed facts, assumptions, and open questions
| ID | Type | Content | Current handling | Impact |
|---|---|---|---|---|
| ASM-001 | Assumption | AI suggestions are never auto-sent | Product rule | Reduces safety and brand risk |
| TBD-001 | Open question | Which ticket categories are eligible? | Needs policy decision | Affects rollout and evaluation |

## Functional requirements and targeted AI safety requirements
| Requirement ID | Requirement | Priority | Rationale |
|---|---|---|---|
| FR-001 | Generate a concise summary from the ticket thread | P0 | Core user value |
| FR-002 | Generate a suggested reply that agents can edit, accept, or discard | P0 | Human control is required |
| NFR-003 | Block or flag suggestions containing policy-sensitive claims | P0 | Safety and compliance risk |

## Evaluation and safety
| Area | Requirement | Metric / validation |
|---|---|---|
| Summary quality | Summary must preserve customer issue, latest status, and requested action | Human review pass rate |
| Reply safety | Suggestion must not invent refund, legal, or policy commitments | Safety review sample |
| Fallback | If model fails or confidence is low, show no suggestion and allow manual reply | AC-004 |
```

## Example 4: Single-section acceptance criteria

**Input**

> 只帮我写导出订单的验收标准。

**Output style**

```markdown
## 验收标准
| AC ID | 需求 ID | 场景 | 前置条件 | 操作 | 预期结果 | 测试说明 |
|---|---|---|---|---|---|---|
| AC-001 | FR-001 | 勾选订单后导出 | 用户有订单查看和导出权限，已勾选 2 条订单 | 点击“导出” | 系统生成仅包含所选订单的文件 | 校验文件行数与订单 ID |
| AC-002 | FR-002 | 无权限导出 | 用户无导出权限 | 进入订单列表 | 不展示导出按钮，直接访问导出接口应返回无权限错误 | 覆盖前端和接口权限 |
| AC-003 | FR-003 | 导出失败 | 用户触发导出后服务返回失败 | 点击“导出” | 展示失败提示，并允许用户重试 | 校验不产生重复下载任务 |
```

## Example 5: Standard PRD from meeting notes

**Input**

> Meeting notes: Support says users cannot find refund status. PM proposes adding refund progress to order detail. Eng says API has status but not ETA. Data wants click tracking.

**Output style**

```markdown
# PRD: Refund Progress on Order Detail

## Executive summary
- Problem: Users contact support because refund status is hard to find.
- Solution: Add refund progress module to order detail when a refund exists.
- Key constraint: Refund status is available, but ETA is not currently available from API.

## Confirmed facts, assumptions, and open questions
| ID | Type | Content | Current handling | Impact | Owner |
|---|---|---|---|---|---|
| FACT-001 | Confirmed fact | API has refund status | Use status in MVP | Enables P0 module |
| FACT-002 | Confirmed fact | API does not have ETA | Do not show ETA in MVP | Prevents misleading copy |
| TBD-001 | Open question | Exact status enum and copy | Needs eng/product confirmation | Affects UI and QA cases |

## Functional requirements
| Requirement ID | Requirement | Priority | Rationale |
|---|---|---|---|
| FR-001 | Show refund progress module on order detail when refund exists | P0 | Core discoverability value |
| FR-002 | Hide module when the order has no refund | P0 | Avoid irrelevant UI |
| FR-003 | Track module impression and click events | P1 | Needed for adoption measurement |

## Acceptance criteria
| AC ID | Requirement ID | Scenario | Expected result |
|---|---|---|---|
| AC-001 | FR-001 | Order has active refund | Refund progress module is visible with current status |
| AC-002 | FR-002 | Order has no refund | Refund progress module is not displayed |
| AC-003 | FR-003 | User opens order detail with refund module | `EVT-001` impression event is emitted once per page load |
```

## Example 6: Strategy clarification brief instead of PRD

**Input**

> 我们要进军高端企业市场，提高 ARR，帮我写 PRD。

**Output style**

```markdown
# Product Strategy Clarification Brief：高端企业市场机会

## 1. 机会假设
- 商业目标：提升高端企业客户 ARR。
- 当前缺口：输入尚未说明具体用户场景、产品行为、交付范围或购买/使用阻塞点，因此不适合直接写 PRD。

## 2. 目标客群假设
- ASM-001：目标客户可能是大型企业管理员、采购决策者或业务团队负责人。
- ASM-002：核心价值可能来自权限、审计、安全、集成、支持 SLA 或数据治理能力。

## 3. 关键证据缺口
| ID | 缺口 | 决策影响 |
|---|---|---|
| TBD-001 | 哪类高端企业客户流失或未转化 | 影响产品方向和优先级 |
| TBD-002 | 当前成交阻塞来自产品能力、价格、合规还是服务 | 决定是否进入 PRD |
| TBD-003 | 目标场景和使用角色 | 决定需求范围和验收标准 |

## 4. 下一步
先验证目标细分客户、购买阻塞和高频使用场景，再进入 PRD。
```

## Example 7: Data / tracking PRD

**Input**

> 只补注册漏斗埋点，包括打开注册页、提交手机号、验证码通过、注册成功。

**Output style**

```markdown
# Data PRD：注册漏斗埋点

## 执行摘要
- 目标：补齐注册漏斗关键事件，支持转化率分析和异常定位。
- 范围：仅定义埋点事件、参数、触发条件和验证方法，不改注册产品流程。

## 事件规格
| Event ID | Event name | Trigger condition | Parameters | Required | Privacy level | Validation method |
|---|---|---|---|---|---|---|
| EVT-001 | registration_page_viewed | 用户打开注册页且页面渲染成功 | source, device_type, app_version | Yes | Non-sensitive | 前端日志与页面 PV 对账 |
| EVT-002 | registration_phone_submitted | 用户提交手机号 | country_code, phone_hash, source | Yes | Sensitive-hashed | 校验手机号不明文上报 |
| EVT-003 | registration_otp_verified | 验证码校验通过 | verification_method, attempt_count | Yes | Sensitive-derived | 与验证码服务成功日志抽样对账 |
| EVT-004 | registration_completed | 注册成功并生成账号 | user_id_hash, source, elapsed_ms | Yes | Sensitive-hashed | 与新增用户表按小时对账 |

## 事件验收标准
| AC ID | Event ID | Scenario | Expected result |
|---|---|---|---|
| AC-001 | EVT-002 | 用户提交手机号 | 事件触发一次，手机号仅以 hash 形式上报 |
| AC-002 | EVT-004 | 用户注册成功 | 注册成功事件与新增用户记录可对账 |
```

## Example 8: Growth experiment PRD

**Input**

> 做一个新用户首单优惠弹窗 A/B test。

**Output style**

```markdown
# PRD：新用户首单优惠弹窗实验

## 实验假设
对新用户展示首单优惠弹窗，可以提升首单转化率；但可能增加关闭率或干扰浏览体验。

## 实验设计
| Item | Definition |
|---|---|
| Target population | 新注册且未下单用户 |
| Control | 不展示弹窗 |
| Variant A | 首页首屏展示首单优惠弹窗 |
| Primary metric | 新用户 7 日首单转化率 |
| Guardrail metrics | 弹窗关闭率、首页跳出率、投诉率 |
| Stop criteria | 任一 guardrail 明显恶化或埋点异常 |

## 关键需求
| Requirement ID | Requirement | Priority | Related event | Rationale |
|---|---|---|---|---|
| FR-001 | 实验仅命中新注册未下单用户 | P0 | EVT-001 | 保证人群准确性 |
| FR-002 | 用户关闭弹窗后本周期不再重复展示 | P0 | EVT-003 | 避免干扰 |

## 埋点规格
| Event ID | Event name | Trigger condition | Purpose |
|---|---|---|---|
| EVT-001 | first_order_popup_exposed | 用户命中实验并看到弹窗 | 计算曝光和实验触达 |
| EVT-002 | first_order_popup_clicked | 用户点击弹窗 CTA | 计算优惠点击转化 |
| EVT-003 | first_order_popup_closed | 用户关闭弹窗 | 监控干扰和关闭率 |
```

## Example 9: Platform / API PRD

**Input**

> 给外部合作方开放订单状态查询 API。

**Output style**

```markdown
# PRD：Partner Order Status API

## 执行摘要
- 目标：允许授权合作方查询其有权访问的订单状态。
- PRD 类型：Platform / API，因为涉及接口契约、鉴权、限流、错误模型和兼容性。

## API requirements and constraints
| Requirement ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-001 | Partner can query order status by order_id | P0 | 仅返回该 partner 授权订单 |
| NFR-001 | API p95 latency target must be confirmed | P1 | 未提供基线，暂列开放问题 |
| NFR-002 | API must enforce auth, rate limits, and audit logging | P0 | 防止越权和滥用 |

## Error model
| Error | Trigger | Response behavior |
|---|---|---|
| 401 | Missing or invalid auth | Return authentication error without order detail |
| 403 | Partner has no access to order | Return unauthorized without confirming order ownership |
| 429 | Rate limit exceeded | Return retry guidance |
```

## Example 10: Migration / refactor PRD

**Input**

> Replace the legacy search index while keeping user search behavior unchanged.

**Output style**

```markdown
# PRD: Search Index Migration

## Executive summary
- Goal: Replace the legacy search index without changing expected user search behavior.
- PRD tier: Complex if rollback, data validation, compatibility, or multi-team dependencies are non-trivial.

## Migration requirements
| Requirement ID | Requirement | Priority | Related data rule | Validation |
|---|---|---|---|---|
| FR-001 | Route eligible search traffic to the new index behind a feature flag | P0 | DATA-001 | Cohort-level traffic logs |

## Data validation rules
| Data rule ID | Rule | Priority | Validation |
|---|---|---|---|
| DATA-001 | New index results must be compared against legacy results for sampled queries | P0 | Diff report with agreed tolerance |

## Risk register
| Risk ID | Risk | Impact | Mitigation |
|---|---|---|---|
| RISK-001 | Ranking drift may reduce search success | Search quality may regress | Monitor no-result rate and click-through rate during rollout |

## Rollback
| Trigger | Rollback behavior | Owner |
|---|---|---|
| No-result rate or error rate exceeds agreed threshold | Disable feature flag and route traffic to legacy index | Search platform owner |
```

## Example 11: Deep PRD audit

**Input**

> Deep audit this PRD for payment refund automation.

**Output style**

```markdown
## Review Verdict
Not ready

## Release Blockers
| Issue | Impact | Why it blocks | Required fix | Owner |
|---|---|---|---|---|
| Refund reconciliation rules are missing | Can create payment/data-integrity errors | Payment-risk and data-integrity blockers prevent Ready | Define reconciliation source of truth, retry, idempotency, and exception handling | Product + Finance Eng |

## Traceability Audit
| Problem / goal | Requirement | AC | Event / metric | Gap |
|---|---|---|---|---|
| Reduce manual refund ops | Refund automation | Missing | Missing reconciliation metric | Cannot verify safe automation |

## Launch Gate Assessment
| Gate | Status | Blocker | Owner | Required evidence |
|---|---|---|---|---|
| Payment reconciliation | Blocked | Yes | Finance Eng | Sample reconciliation report and rollback test |
```
