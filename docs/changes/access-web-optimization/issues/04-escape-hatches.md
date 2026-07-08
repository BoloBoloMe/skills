## 父级

`docs/changes/access-web-optimization/CONTRACT.md`

## 执行(Execution)

- [x] 已实现

## 要构建什么

新增三层 escape hatch: `evaluate_js(script)` 在当前页面执行任意 JS, 不加沙箱, 返回 `EvalResult`; `network_json(url, method, body, headers)` 经 `context.request` 发 HTTP, 自动带 cookie, 不受 CORS, 返回 `NetworkResult`; `cdp_send(method, params)` 经 `page.context.new_cdc_session(page).send(...)` 发原始 CDP, 返回 `CdpResult`. 此切片适合 AFK: 接口已由 D007/D008 钉死, 但需事实验证 CDP 连接上 `context.request`/`new_cdc_session` 可用.

## 相关决策

D007, D008

## 允许范围

`browse/browser_agent/operations.py`, `result.py`, `__init__.py`, 对应测试.

## 禁止范围

不得做 `page_text`/`selector_text`. 不得给 `evaluate_js` 加沙箱. 不得改 L1/`_locator`/`_structure`/`scrape/`.

## 验证入口

`cd browse && pytest` 新增测试: `evaluate_js("document.querySelector('#app').innerText")` 返回文本; async JS 等待后返回; 写 `window.__x` 再读回. `network_json` 在 context 设 cookie 后请求, 验证携带 cookie. `cdp_send("Target.getTargets")` 返回 dict.

## 风险提示

若 CDP 连接 (`connect_over_cdp`) 得到的 context 上 `.request` 或 `new_cdc_session` 不可用 (抛 `AttributeError`/`Error`), 停止退回 `grill-with-docs` 重定 `network_json`/`cdp_send` 实现路径 — 这是 CONTRACT 未确认假设.

## 停止条件

若 `context.request`/`new_cdc_session` 在 CDP 连接上不可用, 停止并上报, 不得自行改 API 决策. 不得超出本 issue 边界.

## 适合 AFK 的原因

D007/D008 已钉死接口与沙箱策略. 唯一风险是 Playwright API 可用性, 属事实验证, 失败时停止上报而非自行决策.

## 验收标准

- [ ] `evaluate_js` 执行同步/异步 JS, 返回结果, 无沙箱.
- [ ] `network_json` 经 `context.request`, 自动带 context cookie, 不受 CORS.
- [ ] `cdp_send` 发原始 CDP 命令, 返回 dict.
- [ ] 不存在 `page_text`/`selector_text`.

## 被阻塞于

- `docs/changes/access-web-optimization/issues/02-detached-cdp-session.md`
