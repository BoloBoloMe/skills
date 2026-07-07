## 父级

`docs/changes/access-web-optimization/CONTRACT.md`

## 执行(Execution)

- [ ] 已实现

## 要构建什么

更新 `browse/browse.md`: 浏览器生命周期绑定 pi 会话 (脱离式 Chromium, 跨工具调用存活), 登录态在会话内复用, 产物在系统临时目录且重启丢失, 三层函数 (L1 语义 / L2 `evaluate_js`+`network_json` / L3 `cdp_send`) 选择指南, `reset_session`/`stop_browser_session`/`cleanup_browser_session` 区别, `status` 字段, 范围外说明 (Grafana/Loki P2, 跨重启登录, bring_to_front). 此切片适合 AFK: 纯文档, 行为已由前序 issue 实现.

## 相关决策

D004, D007, D013

## 允许范围

`browse/browse.md`.

## 禁止范围

不得改任何代码. 不得描述未实现的行为.

## 验证入口

人工核对文档与已实现行为一致: 生命周期/三层函数/命令区别/产物路径/范围外.

## 风险提示

无已知额外风险.

## 停止条件

若发现已实现行为与前序 issue 验收不一致, 停止并上报. 不得超出本 issue 边界.

## 适合 AFK 的原因

纯文档同步, 无决策点.

## 验收标准

- [ ] 文档说明浏览器绑定 pi 会话, 跨工具调用复用登录态.
- [ ] 三层函数选择指南齐全.
- [ ] reset/stop/cleanup 区别明确.
- [ ] 产物 temp 语义与重启丢登录说明存在.
- [ ] 范围外项列出.

## 被阻塞于

- `docs/changes/access-web-optimization/issues/02-detached-cdp-session.md`
- `docs/changes/access-web-optimization/issues/03-lifecycle-commands.md`
- `docs/changes/access-web-optimization/issues/04-escape-hatches.md`
