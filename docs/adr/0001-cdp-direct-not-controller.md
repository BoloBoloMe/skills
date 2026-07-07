# 跨进程浏览器共享用 CDP 直连, 不引入 controller HTTP 进程

`access-web` skill 需要浏览器会话跨工具进程保持 (登录态/页面). PRD 提出引入常驻 controller HTTP 进程 + `OperationBackend` 抽象, client 侧通过 HTTP 收发语义请求. 我们改为直接用 Chromium 内置 CDP: 每个工具进程 `connect_over_cdp` 同一 Chromium, 拿到真实 Playwright `Page`, `operations`/`_locator`/`_structure` 零改动. 不新增 controller 进程, 不新增 backend 抽象.

工具进程本就装有 Playwright, controller "client 不依赖 Playwright" 的优势不成立; 而 controller 方案要新定义 HTTP API + 序列化 + 进程生命周期管理, 复杂度显著更高. CDP 是 Playwright 官方支持的跨进程共享方式.

## 后果

所有进程都用同一套 Playwright API 拿真实 `Page`, 不存在 local/controller 两套 backend. 后果是浏览器生命周期不再由某个 Python 句柄独占 — 见 ADR-0002 的脱离式启动方案.
