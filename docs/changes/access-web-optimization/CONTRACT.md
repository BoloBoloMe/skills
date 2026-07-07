# access-web 持久浏览器与跨平台优化 Contract

## 背景

`access-web` skill 的 `browse` 子命令当前用进程内 Playwright 单例 (`session.py` D017), 工具进程退出即丢浏览器与登录态. 本变更将其升级为脱离式 Chromium + CDP 跨进程共享, 补齐 escape hatch (`evaluate_js`/`network_json`/`cdp_send`) 与生命周期管理 (`status`/`stop`/`cleanup`), 并把产物统一到系统临时目录. `scrape` 子命令不依赖 `browser_agent`, 不在范围内.

## 目标

- 同 cwd 内, 用户登录一次后, 后续工具调用复用同一浏览器会话与 cookie, 不重新登录.
- 工具进程退出后 Chromium 存活, 下次工具调用 `connect_over_cdp` 复用.
- `evaluate_js`/`network_json`/`cdp_send` 可用; `network_json` 自动携带浏览器 context cookie, 不受 CORS.
- `status`/`stop_browser_session`/`cleanup_browser_session` 可用; `stop` 关浏览器但保留 profile, `cleanup` 彻底清理.
- 所有产物 (profile/artifacts/metadata) 在 `tempfile.gettempdir()` 下, cwd 不留文件.
- 现有 8 个 L1 操作行为与返回类型不变, 测试在真实 headless 浏览器下通过.

## 非目标

- 不做 Grafana/Loki 专用查询辅助, 不做批量 trace 模板, 不做 `cleanup --older-than` 自动清理 (P2).
- 不保证跨 OS 重启的登录态 (profile 在 temp).
- 不保留 local 模式, 不引入 `ACCESS_WEB_MODE` 开关.
- 不设独立 `doctor` 命令.
- 不做 `bring_to_front`, `status` 不自动截图.
- 不做 `page_text`/`selector_text`.

## 行为边界

- 会话标识 = `sha256(canonicalize(cwd))[:16]`; 同 cwd 共享, 不同 cwd 隔离.
- 首次启动: 脱离式 `subprocess.Popen` 启 Chromium (`--user-data-dir` + `--remote-debugging-port`), 写 metadata (pid/port/profile_dir). 所有进程 (含首次) `connect_over_cdp`.
- Chromium 被外部杀掉 → `connect_over_cdp` 失败 → 用同 profile 重 launch, 登录态保留 (自愈).
- `reset_session()`: 仅弃当前进程内 Session 句柄, 不碰 Chromium/profile.
- `stop_browser_session()`: 按 metadata pid 杀 Chromium (Windows `taskkill /F /PID`, POSIX `os.kill` SIGTERM), 保留 profile.
- `cleanup_browser_session()`: stop + `rmtree` session 目录.
- `status()`: 返回 `alive/url/title/pid/headed/cdp_port/profile_dir/pages`, `alive` 双检 pid + CDP 端口.
- `evaluate_js(script)`: 执行任意 JS, 不加沙箱, 返回 `EvalResult`.
- `network_json(url, method, body, headers)`: 经 `context.request`, 带 cookie, 返回 `NetworkResult`.
- `cdp_send(method, params)`: 裸 CDP, 返回 `CdpResult`.
- OS 重启/temp 清理后 profile 丢失, 需重新登录.
- L1 操作签名与返回 dataclass 不变; 失败返回 `success=False`, 不抛异常 (继承 `browser-agent-skill/D008`).
- headed/headless 沿用 `BROWSER_HEADED` 环境变量.

## 决策引用

完整决策账本: `docs/changes/access-web-optimization/DECISIONS.md`.

- D001: CDP 直连, 无 controller HTTP 进程, 无 OperationBackend.
- D002: 脱离式 `subprocess.Popen` 启 Chromium, 不用 `launch_persistent_context` 持有.
- D003: session-key = `sha256(cwd)[:16]`, 产物进 `tempfile.gettempdir()`.
- D004: 接受重启丢登录态.
- D005: 单一 session/CDP 模式, 砍 local.
- D006: 测试打真实 headless, 专用 session-key, fixture cleanup.
- D007: L2 = `evaluate_js` + `network_json`, 不做 `page_text`/`selector_text`, 不加沙箱.
- D008: L3 = `cdp_send`.
- D009: reset/stop/cleanup 语义, stop 保留 profile, connect 失败自愈.
- D010: `status` 字段, 不自动截图, 不做 bring_to_front.
- D011: 不设 doctor, 探测+诊断进 `config.py`.
- D012: 端口自绑 socket, 二进制经 `executable_path` 缓存.
- D013: Grafana/Loki P2 范围外.

## 未确认假设

- 假设: CDP 连接 (`connect_over_cdp`) 得到的 `BrowserContext` 上 `.request` (APIRequestContext) 与 `page.context.new_cdc_session(page)` 在 Python Playwright 中可用.
  影响: `network_json` 与 `cdp_send` 的实现路径. 若不可用, 需退回 `page.evaluate(fetch)` (受 CORS) 或其他方案, 属设计实现冲突, 需退回 `grill-with-docs`.
  验证方式: 实现时用 `playwright.sync_api` 连接一个已启 CDP 的 Chromium, 调 `context.request.fetch` 与 `new_cdc_session`, 观察是否抛 `AttributeError`/`Error`.

## 代码边界提示

- `browse/browser_agent/config.py` (新增): 环境探测, session-key 计算, tempdir/session 目录, 端口分配, Chromium 二进制定位与缓存, metadata 读写, pid 读写.
- `browse/browser_agent/browser.py`: 改为 detached launch + `connect_over_cdp`, 删除进程内 `chromium.launch` 路径.
- `browse/browser_agent/session.py`: 改为 metadata 驱动 (try connect → fallback launch), 新增 `stop_browser_session`/`cleanup_browser_session`, `reset_session` 仅弃句柄.
- `browse/browser_agent/operations.py`: 新增 `evaluate_js`/`network_json`/`cdp_send`/`status`/`cookies`; L1 不动.
- `browse/browser_agent/result.py`: 新增 `EvalResult`/`NetworkResult`/`CdpResult`/`StatusResult`/`CookiesResult`.
- `browse/browser_agent/__init__.py`: 导出新函数与结果类型.
- `browse/browser_agent/_locator.py`, `_structure.py`: 不动.
- `browse/tests/conftest.py` + 4 个测试文件: 重写 harness 为真实 headless, 保留 L1 断言.
- `browse/browse.md`: 更新生命周期/语义/三层函数说明.

## 允许范围

- `browse/browser_agent/` 下 `config.py`(新增), `browser.py`, `session.py`, `operations.py`, `result.py`, `__init__.py`.
- `browse/tests/` 下 `conftest.py` 与现有 4 个测试文件.
- `browse/browse.md` 文档.
- `browse/pyproject.toml` 仅在确需时调整 (预期不新增运行时依赖).

## 禁止范围

- `scrape/` 任何文件 (范围外, 不依赖 `browser_agent`).
- `browse/browser_agent/_locator.py`, `_structure.py` (D001: 零改动).
- L1 操作函数签名与现有返回 dataclass (`NavigateResult`/`ExtractResult`/`ScreenshotResult`/`StructureResult`/`OperationResult`).
- 新增运行时依赖 (无 `http.server` 服务, 无 fastapi, 无 psutil; 仅 `playwright` + stdlib).
- 引入 `ACCESS_WEB_MODE`/local 模式/`OperationBackend`/`controller.py`/`providers.py`.
- 用 `launch_persistent_context` 作为浏览器生命周期持有者.
- 在 cwd 写任何文件.
- `page_text`/`selector_text`/`doctor`/`bring_to_front`/status 自动截图/Grafana-Loki 辅助/`cleanup --older-than`.

## 验证入口

- `cd browse && pytest` (需先 `python -m playwright install chromium`), 现有 4 个测试文件在真实 headless 下通过.
- 新增测试覆盖: persistent profile 跨 start 复用, CDP 跨进程连同一 page, Chromium 被杀后自愈重 launch, 不同 session-key 隔离, `network_json` 带 cookie, `evaluate_js` 同步/异步/读写.
- 手动验收: headed 模式登录一次, 退出工具进程, 再次调用 `navigate` 不要求重新登录.

## 风险和停止条件

- 若"未确认假设"中 `context.request`/`new_cdc_session` 在 CDP 连接上不可用, 停止, 退回 `grill-with-docs` 重定 `network_json`/`cdp_send` 实现路径.
- 若脱离式 Chromium 在 Windows 上仍被父进程 job object 连坐杀掉, 停止, 退回 `grill-with-docs` 重定启动机制.
- 需要扩大范围 (如被迫引入 local 模式或 controller) 时停止.
- 发现现有 L1 行为与 contract 冲突时停止.

## 下游 issue 约束

- `config.py` (探测/路径/端口/二进制/metadata) 必须先于 `browser.py`/`session.py` 改造.
- `browser.py` + `session.py` 改造必须先于新增 `operations` (escape hatch 依赖 session 拿到 CDP 连接的 context).
- 测试 harness 重写 (`conftest.py`) 必须先于或同于 L1 测试迁移, 否则现有测试无法运行.
- `browse.md` 文档更新可在所有代码改动完成后.
- 任何 issue 不得修改 `_locator.py`/`_structure.py`/`scrape/`.
