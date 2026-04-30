asset_id: hilp-dual-skill-pressure-test
artifact_name: stage-test/skill-pressure-test
version: v2
state: archived
state_label: 已归档
owner_skill: hilp-skill-pressure-test
created_from: stage-test/skill-pressure-test@v1 [state=archived｜中文状态=已归档]
last_event: interactive-dry-run-completed
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/hilp/测试HILP规划与执行技能/assets/90-协议压力测试_pressure-test@v2.md
asset_link: [90-协议压力测试_pressure-test@v2.md](./90-协议压力测试_pressure-test@v2.md)

# 协议压力测试阶段

## 这个阶段要做什么
验证 HILP 规划技能与 HILP 执行技能是否会正确分流、阻断、审批、重审和保存资产；本资产记录对 v1 虚拟用例的交互干跑结果。

## 已保存资产
- 文件链接：[90-协议压力测试_pressure-test@v2.md](./90-协议压力测试_pressure-test@v2.md)
- asset_ref：`stage-test/skill-pressure-test@v2 [state=archived｜中文状态=已归档]`
- 当前状态：已归档（`archived`）
- 当前是否需要审批：无需审批（`no-approval`）
- 上一版：[90-协议压力测试_pressure-test@v1.md](./90-协议压力测试_pressure-test@v1.md)
- live manifest：[manifest.md](../manifest.md)

## 测试场景
- 名称：虚拟 Notes CLI 设置格式迁移，覆盖规划到执行的双 Skill 串联。
- 测试模式：交互干跑。
- 输入：按 v1 资产中的 7 步脚本重放。
- 预期目的：验证规划门控、审批绑定、执行交接入口、执行范围纪律和新事实回退。

## 预期行为
- 预期阶段：初始分流 → 需求对齐与事实求证 → 方案设计与审批 → 实施蓝图 → 执行交接 → 规划资产归档 → 执行入口检查 → 执行计划 → HILP 重审回退。
- 预期治理模式：strict。
- 预期阻断点：有阻断项；缺事实、缺明确批准、蓝图不确定、缺有效执行交接、执行中出现蓝图外文件均应阻断。
- 预期资产状态变化：
  - `stage-3/design-choice@v1 [state=ready-for-human-decision｜中文状态=待人工裁决]` → 明确批准后 `approved｜中文状态=已批准`。
  - `stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]` → 明确批准后 `approved｜中文状态=已批准`。
  - `stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]` 可作为有效执行交接记录。
  - 发现蓝图外同步插件后，受影响的下游虚拟资产进入 `needs-revision｜中文状态=待修订`。

## 实际行为
- 取证方式：交互干跑；未创建真实业务仓库，未修改生产代码，未产出真实业务蓝图。
- 实际阶段：按脚本重放时，路由结果为初始分流 → 需求对齐与事实求证 → 方案设计与审批 → 实施蓝图 → 执行交接 → 规划资产归档 → 执行入口检查 → 执行计划 → HILP 重审回退。
- 实际治理模式：strict。
- 实际阻断点：有阻断项，且均按预期触发。
- 实际资产状态变化：本压力测试资产 `stage-test/skill-pressure-test@v2 [state=archived｜中文状态=已归档]` 已落盘；虚拟业务资产仅在干跑中模拟状态变化，不落盘为真实规划资产。

## 干跑步骤与判定

| 步骤 | 注入输入 | 预期阶段 | 实际阶段 | 阻断判定 | 结果 |
|---|---|---|---|---|---|
| 1 | 只给“迁移 settings 到 preferences”，缺兼容窗口与回滚边界 | 需求对齐与事实求证阶段 | 需求对齐与事实求证阶段 | 有阻断项：关键事实不足 | 通过 |
| 2 | 补充 30 天兼容窗口、只读旧文件、回滚路径，并选择适配器双读单写 | 方案设计与审批阶段 | 方案设计与审批阶段 | 先待人工裁决，明确绑定当前设计版本后可批准 | 通过 |
| 3 | 用户说“按这个直接开工”，但还没有已批准蓝图 | 实施蓝图阶段或阻断执行 | 阻断执行，要求先形成并批准蓝图 | 有阻断项：缺已批准蓝图 | 通过 |
| 4 | 明确批准 `stage-4-5/implementation-blueprint@v1` | 执行交接阶段 | 执行交接阶段 | 无阻断项，前提是蓝图确定性检查通过 | 通过 |
| 5 | 执行交接成功落盘且入口检查无阻断项 | 规划资产归档阶段 | 规划资产归档阶段 | 无阻断项；自动尝试归档 | 通过 |
| 6 | 切换到执行技能，请求写执行计划 | 执行入口检查阶段 → 执行计划阶段 | 执行入口检查阶段 → 执行计划阶段 | 无阻断项；接受有效但已归档的执行交接资产 | 通过 |
| 7 | 发现蓝图外 `src/sync/settingsBridge.ts` 也读取旧配置 | HILP 重审回退 | HILP 重审回退 | 有阻断项：蓝图外文件与新事实 | 通过 |

## 偏差分析
- 偏差 1：未发现路由偏差。
- 偏差 2：未发现资产状态语义偏差。
- 偏差 3：未发现执行入口语义偏差；执行交接资产为 `archived｜中文状态=已归档` 时仍可被接收，符合规则。
- 根因：不适用。

## 修订建议
- 建议修改的位置：暂无必须修改项。
- 建议补充或删减的规则：建议把“执行交接资产可为已归档但设计/蓝图不可为已归档”的对照样例加入长期回归。
- 建议新增的测试样例：
  1. 蓝图为 `ready-for-approval｜中文状态=待审批` 时请求执行，应拒绝。
  2. 设计资产为 `archived｜中文状态=已归档` 时请求执行，应拒绝。
  3. 执行交接成功但归档写入失败，应报告归档失败且不推翻执行交接。

## 总结
本次交互干跑结论：通过。两个 HILP skills 在该虚拟用例中表现符合预期；结论范围仅限规则级干跑，不等同于真实仓库实现、测试命令或代码审查通过。
