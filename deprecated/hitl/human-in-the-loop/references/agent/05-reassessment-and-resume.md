# 重评估与恢复

`planning/reassessment@vN` 用于记录失败分析、新事实、范围或验证影响、失效判断与后续路由。它不是批准目标，也不需要固定批准命令。

## 触发场景

- approved asset 发生 hash 漂移；
- 出现影响范围、设计、蓝图或验证契约的新事实；
- Plan / Runbook 生成时发现仓库观察与已批准资产冲突；
- 执行中发生范围越界、验证失败或停止条件命中；
- 恢复执行时发现仓库状态与 unit-summary 或 Plan / Runbook 不一致。

HTML 模板缺失、payload 注入失败或 HTML hash 不一致等 human-view 链路问题默认是阻塞修复，不自动生成 reassessment。

## 自动失效

如果证据表明 design、blueprint 或 implementation-package 已失效，agent 必须先写入 `planning/reassessment@vN`。需要历史化既有资产时，必须使用 `archive_asset.py --state retired|failed|superseded|closed` 移入 `agent/archive/` 并同步 registry；不得手工只改 manifest 状态。短期阻塞但仍当前有效的资产可标记为 `blocked`。这只是安全停止，不是批准新方案。

## 断点恢复入口

恢复时按以下顺序读取：

1. 根 `manifest.yaml`；
2. active Plan / Runbook；
3. 最新 unit-summary；
4. strict 下的最新 ledger；
5. 最新 verification；
6. 当前仓库状态。

恢复前必须重新检查 asset-check、仓库漂移、allowed-files gate 和 unit 依赖。若当前仓库状态与稳定资产不一致，必须阻塞并生成 reassessment。
