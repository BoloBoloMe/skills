# HILP 审批状态一致性问题复查

## 结论

原复盘指出的“批准事件未原子更新目标资产自身 front matter 与正文状态，只更新 manifest、review-pack 和 _current 入口”的问题，在当前仓库的 HILP skills 中仍然存在，且有多处规则会继续诱导该问题复发。

检查范围：

- `human-in-loop-planning/SKILL.md`
- `human-in-loop-planning/references/event-action-rules.md`
- `human-in-loop-planning/references/handoff-contracts.md`
- `human-in-loop-planning/references/blueprint.md`
- `human-in-loop-planning/references/execution-handoff.md`
- `human-in-loop-planning/references/archive.md`
- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/hilp-handoff-intake.md`

## 原问题是否仍存在

仍存在。

证据：

1. `human-in-loop-planning/SKILL.md:87-109` 将 `manifest.md` 定义为状态权威，并在审核完成时只要求更新 manifest、关闭审核包、更新 `_current/当前待审.md` 和 `_current/当前已批准.md`，未要求同步修改目标资产文件的 front matter 与正文状态。
2. `human-in-loop-planning/references/event-action-rules.md:81-88` 的 Human Approval Granted 规则虽然写了“将该资产状态改为 approved”，但具体必需动作只点名 manifest、审核包和 `_current/`，没有列出目标资产 front matter、正文 `asset_ref`、当前状态、是否需要审批、下一步等必须同步字段。
3. `human-in-loop-planning/references/event-action-rules.md:329-333` 明确写成“审核通过时 ... live manifest 中目标资产当前状态变为 approved”，且 `_current/当前已批准.md` “不改变正式资产正文”。这会继续支持“manifest 已批准、资产正文仍待审批”的不一致状态。
4. `human-in-loop-planning/references/handoff-contracts.md:262-264` 同样只要求人工批准通过时关闭审核包、更新 manifest 和 `_current/`，未要求目标资产同步。
5. `human-in-loop-planning/references/handoff-contracts.md:357` 规定 `asset_ref` 状态优先从 manifest 读取，未要求与资产文件自身 front matter / 正文状态交叉校验。

因此，原复盘的技能改进要求目前没有真正落到规则中。

## 两个 HILP skills 中的其他类似问题

### 1. 审批不通过 / needs-revision 也存在同类非原子更新风险

`event-action-rules.md:331-332` 和 `handoff-contracts.md:263-264` 对审核不通过只要求审核包关闭、manifest 改为 `needs-revision`，未要求目标资产 front matter、正文 `asset_ref`、当前状态说明和 `_current/当前已批准.md` 一起清理或校验。结果可能出现 manifest 已待修订，但资产正文仍为已批准或待审批。

### 2. 已批准上游失效时缺少跨资产一致性传播清单

`event-action-rules.md` 的上游失效规则只抽象说明下游资产进入 `needs-revision`，没有明确同步哪些对象：目标资产 front matter、正文引用、manifest、review-pack、`_current/当前已批准.md`、执行交接引用链。已批准集合可能保留失效资产。

### 3. 分层蓝图包成员审批状态存在同类风险

`event-action-rules.md:83-104` 要求分层蓝图包同步到 manifest 和全部包内成员，但未明确“全部包内成员”的 front matter、正文 `asset_ref`、主蓝图 manifest 成员清单、成员自身审核包和 `_current/当前已批准.md` 必须一致。分层包可能出现主 manifest 已批准，子蓝图文件自身仍待审批。

### 4. 下游入口只检查“引用为 approved”，缺少文件自身状态校验

`blueprint.md:42-56`、`execution-handoff.md:34-45` 和 `archive.md` 的入口条件均依赖 approved asset_ref / manifest 链路，没有强制读取上游资产文件自身并核对 front matter 与正文状态。规划层仍可能把不一致资产继续封装给下游。

### 5. execution skill 的入口阻断规则未固化原复盘要求

`human-in-loop-execution/references/hilp-handoff-intake.md:26-31` 只要求核对设计、蓝图 asset_ref 状态和执行交接字段，没有明确：必须读取实际设计 / 蓝图资产文件；必须比较 manifest、执行交接引用、front matter、正文 `asset_ref`；不一致时必须阻断并输出固定恢复建议。因此执行层当前规则没有完整保留复盘中要求的恢复提示。

## 建议修正

1. 在 planning 的批准事件中明确原子写入对象：目标资产 front matter、目标资产正文状态块、manifest、review-pack、`_current/当前待审.md`、`_current/当前已批准.md`。
2. 删除或改写“`_current/当前已批准.md` 不改变正式资产正文”的歧义表述，改为“不改变内容语义，但必须同步同一版本资产的状态元数据和状态摘要”。
3. 在 `handoff-contracts.md` 增加“状态一致性强制校验”：同一 asset_ref 在资产 front matter、正文 `asset_ref`、manifest、review-pack、当前入口中必须一致，不一致不得进入蓝图、执行交接或归档。
4. 在 blueprint、execution-handoff、archive 入口加入读取上游实际文件并交叉校验的要求。
5. 在 execution intake 加入固定阻断恢复建议：回到 HILP 变更重审，执行“审批状态一致性修复”；若用户批准事实明确，不生成新内容版本，只同步同一版本状态字段和当前入口。
