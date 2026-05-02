---
asset_id: hilp-hile-gsd-lite-archive-manifest-v1
artifact_name: stage-7/archive-manifest
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-archive
created_from: stage-6/execution-handoff@v1
last_event: archive-generated
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: docs/changes/增强HILP与HILE轻量执行治理/planning/assets/06-规划资产归档_archive-manifest@v1.md
asset_link: [06-规划资产归档_archive-manifest@v1.md](./06-规划资产归档_archive-manifest@v1.md)
---

# 规划资产归档阶段

## asset_ref

`stage-7/archive-manifest@v1 [state=archived｜中文状态=已归档]`

## 当前是否需要审批

无需审批。

## 作用

标明本次变更的最终阅读入口、最终有效资产、历史过程资产和后续重审入口；不改变任何已批准资产状态。

## 最终阅读入口

1. [05-执行交接_execution-handoff@v1.md](./05-执行交接_execution-handoff@v1.md)
2. [03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
3. [02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)

## 最终有效资产

| 阶段 | asset_ref | 文件 |
|---|---|---|
| 方案设计与审批阶段 | `stage-3/design-choice@v1 [state=approved｜中文状态=已批准]` | [02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md) |
| 实施蓝图阶段 | `stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]` | [03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md) |
| 执行交接阶段 | `stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]` | [05-执行交接_execution-handoff@v1.md](./05-执行交接_execution-handoff@v1.md) |

## 支撑上下文资产

| 资产 | 说明 |
|---|---|
| [manifest.md](../manifest.md) | 当前变更目录 live manifest |
| [_current/当前已批准.md](../_current/当前已批准.md) | 当前有效批准集合 |
| [_current/当前待审.md](../_current/当前待审.md) | 当前待审入口，本包中为无待审资产 |

## 历史过程资产

| 资产 | 说明 |
|---|---|
| [02-design-choice@v1-review.md](../review-pack/02-design-choice@v1-review.md) | 设计审批审核包 |
| [03-implementation-blueprint@v1-review.md](../review-pack/03-implementation-blueprint@v1-review.md) | 蓝图审批审核包 |

## 后续重审入口

若后续执行中出现以下情况，应回到 HILP 变更重审阶段：

- 需要修改 allowed_files 之外的文件。
- 发现 execution_unit 缺字段。
- context_packet 引用失效资产。
- must_haves 无法验证。
- 需要改变接口、数据形状、验证口径、发布顺序或禁止越界项。
- 第二次同类失败。
- 新事实推翻已批准设计或蓝图前提。

## 归档边界

- 本归档只整理当前变更目录内的规划资产。
- 不修改已批准设计和已批准蓝图状态。
- 不移动文件。
- 不生成根目录 `CURRENT.md`。
- 不覆盖 `_current/` 文件。
