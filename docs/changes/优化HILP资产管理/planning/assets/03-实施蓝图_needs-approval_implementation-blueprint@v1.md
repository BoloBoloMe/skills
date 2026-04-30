---
asset_id: hilp-asset-management-blueprint
artifact_name: stage-4-5/implementation-blueprint
version: v1
state: ready-for-approval
state_label: 待审批
owner_skill: hilp-blueprint
created_from: stage-3/design-choice@v1
last_event: none
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批
asset_path: D:/Workspace/skills/docs/changes/优化HILP资产管理/planning/assets/03-实施蓝图_needs-approval_implementation-blueprint@v1.md
upstream_design_ref: stage-3/design-choice@v1 [state=approved｜中文状态=已批准]
upstream_design_owner: hilp-design-approval
upstream_design_decision: human-approval-2026-04-29-hilp-asset-management-design-v1
blueprint_form: single
---

# 实施蓝图阶段

## 这个阶段要做什么

把已批准的 HILP 资产管理设计转成确定的规则文档改动切片、顺序、约束和验证检查点。

## 已保存资产

- 文件路径：`D:/Workspace/skills/docs/changes/优化HILP资产管理/planning/assets/03-实施蓝图_needs-approval_implementation-blueprint@v1.md`
- asset_ref：`stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`
- 蓝图形式：单体蓝图
- 上游设计：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`
- 当前状态：待审批（内部状态值：`ready-for-approval`）
- 当前是否需要审批：需要审批

## 改动拓扑

### 改动切片

1. 资产根结构规则切片
   - 文件范围：`human-in-loop-planning/SKILL.md`、`human-in-loop-planning/references/handoff-contracts.md`
   - 改动内容：把新资产落盘结构定义为根目录索引加三个子目录：`manifest.md`、`_current/`、`review-pack/`、`assets/`。
   - 输出规则：正式阶段资产写入 `assets/`；审核入口写入 `_current/`；审核尝试记录写入 `review-pack/`；当前状态写入根目录 `manifest.md`。

2. 稳定资产命名与状态权威切片
   - 文件范围：`human-in-loop-planning/SKILL.md`、`human-in-loop-planning/references/event-action-rules.md`、`human-in-loop-planning/references/handoff-contracts.md`
   - 改动内容：新资产文件名去除审批标记，采用 `<阶段前缀>-<阶段中文名>_<artifact>@vN.md`；审批标记和当前状态由资产元数据、根目录 `manifest.md`、审核包和 `_current` 表达。
   - 兼容边界：旧资产不迁移；旧命名资产仍可作为历史输入读取；新产生资产使用新结构。

3. 审核包生命周期切片
   - 文件范围：`human-in-loop-planning/SKILL.md`、`human-in-loop-planning/references/event-action-rules.md`、`human-in-loop-planning/references/handoff-contracts.md`、`human-in-loop-planning/references/design-approval.md`、`human-in-loop-planning/references/blueprint.md`
   - 改动内容：规定待审批资产必须生成 `review-pack/<阶段前缀>-<artifact>@vN-review.md`，审核完成后关闭并保留。
   - 审核通过动作：关闭审核包，根目录 `manifest.md` 将对应版本标为 `approved｜已批准`，`_current/当前待审.md` 改为当前无待审资产，`_current/当前已批准.md` 指向当前有效批准集合。
   - 审核不通过动作：关闭审核包，根目录 `manifest.md` 将对应版本标为 `needs-revision｜待修订`，内容修订产生下一个版本和新的审核包。

4. 当前入口切片
   - 文件范围：`human-in-loop-planning/SKILL.md`、`human-in-loop-planning/references/handoff-contracts.md`、`human-in-loop-planning/references/archive.md`
   - 改动内容：定义 `_current/当前待审.md` 为唯一待审入口，定义 `_current/当前已批准.md` 为当前有效批准集合入口。
   - 归档边界：归档阶段仍不生成根目录 `CURRENT.md`，不移动正式资产；`_current` 是资产管理工作入口，不属于归档阶段产出的 archive manifest。

5. 模块输出模板路径切片
   - 文件范围：
     - `human-in-loop-planning/references/router.md`
     - `human-in-loop-planning/references/requirements-facts.md`
     - `human-in-loop-planning/references/design-approval.md`
     - `human-in-loop-planning/references/blueprint.md`
     - `human-in-loop-planning/references/reapproval.md`
     - `human-in-loop-planning/references/execution-handoff.md`
     - `human-in-loop-planning/references/archive.md`
     - `human-in-loop-planning/references/skill-pressure-test.md`
     - `human-in-loop-planning/references/routing-matrix.md`
   - 改动内容：把所有输出模板中的阶段资产路径改成 `项目根目录/docs/hilp/变更概述/assets/<阶段前缀>-<阶段中文名>_<artifact>@vN.md`。
   - 待审批模板补充：当状态为 `ready-for-approval｜待审批` 时，输出必须同时列出审核包路径和 `_current/当前待审.md` 路径。

6. 归档与 live manifest 分工切片
   - 文件范围：`human-in-loop-planning/references/archive.md`、`human-in-loop-planning/references/event-action-rules.md`、`human-in-loop-planning/references/handoff-contracts.md`
   - 改动内容：把根目录 `manifest.md` 定义为 live manifest，把 `assets/06-规划资产归档_archive-manifest@vN.md` 定义为归档阶段正式资产。
   - 分工规则：live manifest 可随状态变化更新；archive-manifest 是版本化归档资产，不覆盖旧版本，不改变上游资产状态。

### 依赖顺序

1. 先修改 `SKILL.md` 的资产落盘总规则。
2. 再修改 `references/handoff-contracts.md` 的保存位置、命名、元数据和跨阶段引用规则。
3. 再修改 `references/event-action-rules.md` 的审批、状态变化、版本递增和自动归档动作。
4. 再修改八个模块模板中的文件路径和待审批附加输出。
5. 再修改 `references/archive.md` 的归档边界和 live manifest 分工。
6. 最后修改 `references/routing-matrix.md` 中 lean 合并资产示例文件名。

### 风险检查点

- 检查点 1：全文不存在“文件名必须同时体现阶段和审批状态”的新资产强制规则。
- 检查点 2：全文不存在新资产示例 `<阶段前缀>-<阶段中文名>_<审批标记>_<artifact>@vN.md` 作为默认推荐格式。
- 检查点 3：所有模块模板的正式资产路径都指向 `assets/`。
- 检查点 4：待审批路径同时包含正式资产、审核包和 `_current/当前待审.md`。
- 检查点 5：归档阶段仍禁止移动文件、禁止生成根目录 `CURRENT.md`、禁止修改上游资产状态。
- 检查点 6：旧资产不迁移的兼容规则仍保留。

### 发布检查点

- 本次发布对象是规划协议文档，不修改执行 skill 代码。
- 完成后通过全文搜索验证旧命名强制规则已经从新资产路径中移除。
- 完成后不迁移 `docs/hilp/` 下已有历史规划资产。

### 验证检查点

执行以下验证命令：

```bash
rg -n "文件名必须同时体现阶段和审批状态|<阶段前缀>-<阶段中文名>_<审批标记>_<artifact>@vN.md|项目根目录/docs/hilp/变更概述/[0-9]" human-in-loop-planning/SKILL.md human-in-loop-planning/references
rg -n "项目根目录/docs/hilp/变更概述/assets/" human-in-loop-planning/SKILL.md human-in-loop-planning/references
rg -n "review-pack|当前待审|当前已批准|live manifest|assets/06-规划资产归档_archive-manifest" human-in-loop-planning/SKILL.md human-in-loop-planning/references
```

通过标准：

- 第一条命令只允许命中兼容说明、历史格式说明或明确废止说明，不允许命中新资产默认路径。
- 第二条命令必须命中所有阶段输出模板对应文件。
- 第三条命令必须命中总规则、交接契约、事件规则和归档模块。

### 涉及模块 / 子系统 / 文件范围

- `human-in-loop-planning/SKILL.md`
- `human-in-loop-planning/references/event-action-rules.md`
- `human-in-loop-planning/references/handoff-contracts.md`
- `human-in-loop-planning/references/router.md`
- `human-in-loop-planning/references/requirements-facts.md`
- `human-in-loop-planning/references/design-approval.md`
- `human-in-loop-planning/references/blueprint.md`
- `human-in-loop-planning/references/reapproval.md`
- `human-in-loop-planning/references/execution-handoff.md`
- `human-in-loop-planning/references/archive.md`
- `human-in-loop-planning/references/skill-pressure-test.md`
- `human-in-loop-planning/references/routing-matrix.md`

## 分层蓝图包 manifest

无。蓝图形式为单体蓝图。

## 实现约束

### 数据形状

#### 目录结构

```text
项目根目录/docs/hilp/变更概述/
  manifest.md
  _current/
    当前待审.md
    当前已批准.md
  review-pack/
    <阶段前缀>-<artifact>@vN-review.md
  assets/
    <阶段前缀>-<阶段中文名>_<artifact>@vN.md
```

#### live manifest 最小字段

根目录 `manifest.md` 必须包含以下表格字段：

```text
asset_id | artifact_name | version | asset_path | created_state | current_state | current_state_label | approval_marker | approval_marker_label | role | current_review_pack | supersedes | superseded_by | last_event | last_decision
```

#### review-pack 最小字段

审核包必须包含：

```text
review_pack_id | target_asset_ref | target_asset_path | target_version | previous_asset_ref | review_status | opened_at | closed_at | close_result | close_decision | change_summary | reviewer_action_required
```

#### _current/当前待审.md 内容结构

```text
# 当前待审资产

当前待审状态：<存在一个待审资产 | 当前无待审资产>
当前审核包：<review-pack path 或 无>
当前待审资产：<asset_ref 或 无>
审核者需要做什么：<批准当前版本 | 要求修订并说明原因 | 无>
```

#### _current/当前已批准.md 内容结构

```text
# 当前已批准资产

| 阶段 | asset_ref | asset_path | last_decision | 用途 |
```

### 接口约束

- 对普通用户展示资产路径时，正式阶段资产路径必须指向 `assets/`。
- 当资产进入待审批状态时，用户可见输出必须展示审核包路径和 `_current/当前待审.md`。
- 跨阶段绑定引用仍使用 `asset_ref: <stage>/<artifact>@vN [state=<state>｜中文状态=<state_label>]`。
- `asset_ref` 中的 `state` 从根目录 `manifest.md` 读取；兼容旧资产时从资产元数据和文件名读取。
- 旧命名资产继续可读，不在本次修改中迁移或重命名。

### 局部算法骨架

#### 新资产落盘算法

1. 计算变更目录 `docs/hilp/<变更概述>/`。
2. 创建 `assets/`、`review-pack/`、`_current/`。
3. 写入正式资产到 `assets/<阶段前缀>-<阶段中文名>_<artifact>@vN.md`。
4. 更新根目录 `manifest.md`，新增或更新该资产版本行。
5. 当资产状态为 `ready-for-approval｜待审批` 时，生成 `review-pack/<阶段前缀>-<artifact>@vN-review.md`。
6. 当资产状态为 `ready-for-approval｜待审批` 时，更新 `_current/当前待审.md` 指向该审核包。
7. 当资产状态为 `approved｜已批准` 时，更新 `_current/当前已批准.md`。

#### 人工批准算法

1. 校验批准语句绑定当前 `asset_ref` 和版本。
2. 不改写 `assets/` 中该版本正文。
3. 将根目录 `manifest.md` 中该版本 `current_state` 更新为 `approved`，`approval_marker` 更新为 `approved`，写入 `last_decision`。
4. 将对应审核包 `review_status` 更新为 `closed`，`close_result` 更新为 `approved`。
5. 将 `_current/当前待审.md` 更新为当前无待审资产。
6. 将 `_current/当前已批准.md` 更新为包含该已批准资产。

#### 审核不通过算法

1. 将根目录 `manifest.md` 中原版本 `current_state` 更新为 `needs-revision`，`approval_marker` 更新为 `needs-revision`。
2. 将对应审核包 `review_status` 更新为 `closed`，`close_result` 更新为 `needs-revision`，写入审核意见。
3. 内容修订时生成下一版本正式资产。
4. 为下一版本生成新的审核包。
5. 将 `_current/当前待审.md` 指向新的审核包。

#### 归档算法调整

1. 归档阶段枚举 `assets/` 中的正式阶段资产和根目录 `manifest.md` 的状态记录。
2. 生成归档正式资产到 `assets/06-规划资产归档_archive-manifest@vN.md`。
3. 不覆盖根目录 `manifest.md`。
4. 不覆盖 `_current/` 文件。
5. 不移动 `assets/`、`review-pack/` 或旧平铺资产。

### 错误处理要求

- 写入 `assets/` 失败时，不得声称阶段资产已保存。
- 写入 `manifest.md` 失败时，不得声称状态索引已更新，并必须报告正式资产路径和索引失败原因。
- 写入 `review-pack/` 失败时，不得声称资产已提交审核。
- 写入 `_current/当前待审.md` 失败时，必须报告审核入口更新失败，并直接给出审核包路径。
- 读取旧资产时，缺少 live manifest 不作为错误；按旧资产元数据和文件名解析状态。

### 测试承诺

- 使用 `rg` 验证新资产默认路径统一为 `assets/`。
- 使用 `rg` 验证全部模块模板提到待审批时具备审核包和当前入口输出规则。
- 使用 `rg` 验证归档模块仍保留不移动文件、不生成根目录 `CURRENT.md`、不修改上游资产状态的约束。
- 人工抽查 `SKILL.md`、`handoff-contracts.md`、`event-action-rules.md` 三个核心文件，确认状态权威为 live manifest 且旧资产不迁移。

## 确定性检查

- 未确定项：无。
- 模糊表达：无。
- 分支待选方案：无。
- 需要执行者自行裁量的实现决策：无。
- 分层蓝图包成员检查：无，当前为单体蓝图。

## 当前判断

- 当前是否可交接到执行层：否。当前蓝图为待审批，尚未批准。
- 当前阻断项：无阻断项。
- 是否存在兼容 / 回滚约束：存在兼容约束。旧资产不迁移，旧命名资产继续可读，新产生资产使用新结构。回滚边界为仅回退规则文档修改，不移动或重写历史规划资产。
- 当前状态：待审批（内部状态值：`ready-for-approval`）。

## 下一步需要用户做什么

请明确批准当前蓝图资产：`stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`。批准后才能进入执行交接阶段。
