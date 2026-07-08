# 决策账本: access-web-optimization

本 feature 改造 `access-web` skill 的浏览器会话模型, 从进程内单例升级为跨工具进程的 CDP 持久会话, 并补齐 escape hatch 与生命周期管理. 盘问于 2026-07-07 闭合, 共 13 条决策.

跨 feature 替代关系: 本 feature 的 D001/D002/D009 替代 `browser-agent-skill` 账本的 D017 (进程级单例) 与 D018 (崩溃不自动恢复). 旧账本的状态变更待单独确认后执行.

## D001: 跨进程浏览器共享用 CDP 直连, 不引入 controller HTTP 进程

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 用 Chromium 内置 CDP (`connect_over_cdp`) 跨进程共享浏览器. 不引入常驻 controller HTTP 进程, 不引入 `OperationBackend`/`LocalBackend`/`ControllerBackend` 抽象. 所有工具进程拿到真实 Playwright `Page`, `operations`/`_locator`/`_structure` 不改.
- 理由: Playwright 原生支持 `connect_over_cdp`. controller 方案需新定义 HTTP API + 序列化 + 进程生命周期 + 跨平台脱离, 复杂度高; 且工具进程本就装有 Playwright, controller "client 不依赖 Playwright" 的唯一优势不成立.
- 替代: `browser-agent-skill/D017` 的 "进程内单例" 限制; PRD 的 controller + OperationBackend 方案.
- 预计影响: `browser_agent/browser.py`, `browser_agent/session.py` 改为 CDP 连接; 不新增 `controller.py`/`providers.py`.
- 实际影响 (ISSUE-02 a1): `browser.py` — `Browser._launch_detached()` 用 `subprocess.Popen` 启 Chromium, `Browser.start()` 用 `connect_over_cdp` 连接. `session.py` — `get_session()` 改为 metadata 驱动. 无 `controller.py`/`providers.py`. 测试: `tests/test_detached_session.py::test_new_process_connects_to_existing_page`. 审查: 无 blocker, N1(孤儿Chromium) 已修复.
- 相关 issue: ISSUE-02

## D002: Chromium 以脱离式子进程启动, 不用 launch_persistent_context 持有

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 首次启动用 `subprocess.Popen` 脱离式启动 Chromium 二进制 (传 `--user-data-dir` + `--remote-debugging-port=N`), 所有进程 (含首次) 用 `connect_over_cdp` 连接. 不用 `launch_persistent_context` 持有浏览器生命周期.
- 理由: `launch_persistent_context` 启动的 Chromium 是 Playwright driver 子进程, 工具进程退出 → driver 退出 → Chromium 被杀 (Windows 上 job object 连坐), CDP 端口消失, 跨进程共享不成立. 脱离式启动让 Chromium 成为独立常驻进程, 不认工具进程为父.
- 预计影响: `browser.py` 新增 detached launch 分支; 跨平台脱离 flags (Windows `creationflags=DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP`, POSIX `start_new_session=True`); metadata 记 pid.
- 实际影响 (ISSUE-02 a1): `browser.py` — `Browser._launch_detached()` 用 `subprocess.Popen` + `creationflags=DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP`(NT) / `start_new_session=True`(POSIX), 传 `--user-data-dir` + `--remote-debugging-port`. metadata 记 pid. 测试: `tests/test_detached_session.py::test_persistent_profile_reuses_cookie_across_starts`. Windows job object 未连坐 (Chromium 存活).
- 相关 issue: ISSUE-02

## D003: 会话标识 = sha256(cwd)[:16], 产物全部进系统临时目录

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: `session-key = sha256(canonicalize(cwd))[:16]`. 产物根 = `tempfile.gettempdir()/access-web/<session-key>/`, 含 `browser.json`, `profile/`, `artifacts/{screenshots,downloads,logs}/`. 不在 cwd 写任何文件.
- 理由: 用户要求产物全进临时目录, 跨平台运行时探测. cwd 哈希确定性推导标识, 无需 `session.id` 文件, 不污染工作目录. pi 不注入 `PI_SESSION_ID` 到工具子进程环境 (已查证), 故标识从 cwd 推导.
- 预计影响: `browser_agent/config.py` 探测 tempdir + 计算 session-key + 读写 metadata.
- 实际影响 (ISSUE-01 a1): `browser_agent/config.py` — `compute_session_key()`, `get_runtime_info()`, `get_session_paths()`, `BrowserConfig` (session_root/browser_json/profile_dir/artifacts_dir 等路径). 测试: `tests/test_config.py` — `test_compute_session_key_is_stable_for_same_cwd`, `test_compute_session_key_differs_for_different_cwd`, `test_get_session_paths_under_tempdir`, `test_browser_config_paths_are_under_tempdir`. 审查: correctness 无 blocker, decision-boundary 无 blocker.
- 相关 issue: ISSUE-01, ISSUE-02

## D004: 接受重启丢失登录态 (profile 在 temp, 不保证跨重启)

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: profile 存放系统临时目录, OS 重启/temp 清理后登录态丢失, 需重新登录. 不做跨重启持久登录.
- 理由: session 级语义 (pi 会话内复用) 自洽; 持久 profile 体积大, 不污染 home. 跨重启保登录若将来需要, 加 `--persist-profile` 选项指向 home 缓存即可, 不必现在做.
- 预计影响: 无额外代码; `browse.md` 文档说明语义.
- 相关 issue: ISSUE-05

## D005: 单一 session/CDP 模式, 砍 local 模式

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 只保留 session 模式 (脱离式 Chromium + CDP). 不保留进程内 local 模式, 不引入 `ACCESS_WEB_MODE` 开关. 现有测试重写为通过 session API 打真实 headless 浏览器, 保留 L1 断言.
- 理由: local 模式唯一理由是迁就旧测试手段 (patch `Browser.start` + `set_content`); 用户决定不迁就. 砍 local 简化架构, 测试走生产路径覆盖更强.
- 替代: PRD/proposal 的双模式 (local/controller) 设计.
- 预计影响: `Browser` 只剩 detached+CDP 一条路径; `conftest.py` 重写为真实 headless fixture; 删除 patch `Browser.start` 的测试手段.
- 实际影响 (ISSUE-02 a1): `browser.py` — `Browser` 仅一条 CDP 路径, 无 `chromium.launch` 分支. `conftest.py` — 真实 headless fixture, 专用 session-key. 4 个测试移除 `Browser.start` mock, 改为 `page.set_content`/`page.route`. 无 `ACCESS_WEB_MODE`. 审查: 代码搜索无 `ACCESS_WEB_MODE`.
- 相关 issue: ISSUE-02

## D006: 测试策略 — 真实 headless 浏览器, 专用 session-key, fixture cleanup

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 测试通过 session API 驱动真实 headless Chromium, `page.set_content` 注入, `page.route` mock. 测试用专用 session-key (临时 cwd), fixture teardown 调 `cleanup_browser_session`. 不靠 `reset_session` 隔离.
- 理由: 走生产 CDP 路径, 覆盖强于 mock; 专用 session-key 避免污染用户真实 session.
- 预计影响: `browse/tests/conftest.py` 重写; 现有 4 个测试文件改 harness; CI 需 `playwright install chromium`.
- 实际影响 (ISSUE-02 a1): `conftest.py` — autouse fixture 切 cwd 到 `tmp_path`, teardown 调 `cleanup_browser_session` + `reset_session`. 4 个测试改用 `page.set_content`/`page.route`. 新增 `test_detached_session.py` (5 tests). 48 测试通过.
- 相关 issue: ISSUE-02

## D007: 新增 L2 escape hatch — evaluate_js + network_json

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 新增 `evaluate_js(script)` 在当前页面执行任意 JS, 不加沙箱; `network_json(url, method, body, headers)` 用 `context.request` 发 HTTP, 自动带 cookie, 不受 CORS. 不做 `page_text`/`selector_text` (`evaluate_js` 严格强于两者).
- 理由: `evaluate_js` 一个通用 escape hatch 覆盖 SPA 数据提取 (定位 → 操作 → 等渲染 → 提取 JS 对象); `network_json` 覆盖带 cookie 的 API 查询 (Grafana datasource proxy). 不加沙箱因 agent 自用, 与 `cdp_send` 同级.
- 关系: 作为 `browser-agent-skill/D002` (语义化高层操作) 的有意例外, L1 仍语义化.
- 预计影响: `operations.py` 新增两函数; `result.py` 新增 `EvalResult`/`NetworkResult`; `__init__.py` 导出.
- 实际影响 (ISSUE-04 a1): `operations.py` — `evaluate_js()` (无沙箱), `network_json()` (context.request 带 cookie). `result.py` — `EvalResult`, `NetworkResult`. 测试: `tests/test_escape_hatches.py` (9 tests). CDP 连接上 context.request 已确认可用. 审查: 无 blocker.
- 相关 issue: ISSUE-04, ISSUE-05

## D008: 新增 L3 裸 CDP — cdp_send

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 新增 `cdp_send(method, params)` 发原始 CDP 命令, 用于 browser 级操作 (性能指标/新 tab/网络劫持).
- 理由: L1+L2 做不到的 5% 场景留 escape hatch, 避免 agent 遇 undefined behavior 无路可走. 成本极低 (`page.context.new_cdc_session(page).send(...)` 一行).
- 预计影响: `operations.py` 新增 `cdp_send`; `result.py` 新增 `CdpResult`.
- 实际影响 (ISSUE-04 a1): `operations.py` — `cdp_send()` (new_cdp_session.send). `result.py` — `CdpResult`. 测试: `tests/test_escape_hatches.py`. CDP 连接上 new_cdp_session 已确认可用 (contract 写 new_cdc_session, 实际 API 为 new_cdp_session). 审查: 无 blocker.
- 相关 issue: ISSUE-04

## D009: 生命周期命令语义 — reset/stop/cleanup

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: `reset_session()` 仅弃当前进程内 Session 句柄, 不碰 Chromium/profile. `stop_browser_session()` 读 metadata pid 杀 Chromium (Windows `taskkill /F /PID`, POSIX `os.kill` SIGTERM), **保留 profile**. `cleanup_browser_session()` = stop + `rmtree` session 目录. `connect_over_cdp` 失败 → 用同 profile 重 launch (自愈, 登录态在).
- 理由: stop 保留 profile 是 stop 与 cleanup 的本质区别 (关浏览器但不登出 vs 彻底清理). pid 杀最可靠, 不依赖 Playwright CDP close 语义. 自愈覆盖 Chromium 被外部杀掉的场景.
- 替代: `browser-agent-skill/D018` (崩溃不自动恢复) — 新设计在 connect 失败时自愈重 launch.
- 预计影响: `session.py` 新增 stop/cleanup; `config.py` 提供 pid 读写.
- 实际影响 (ISSUE-02 a1): `session.py` — `reset_session()` 仅弃句柄, `stop_browser_session()` 杀 Chromium 保留 profile, `cleanup_browser_session()` = stop + rmtree. `browser.py` — `Browser.start()` 自愈: CDP 端口不可达 → 同 profile 重 launch. 测试: `test_self_heal_after_killing_chromium_keeps_cookies`, `test_different_session_keys_are_isolated`. N1 修复: `_launch_detached` 启动前杀旧孤儿 Chromium.
- 相关 issue: ISSUE-02, ISSUE-03

## D010: status() 返回字段, 不自动截图, 不做 bring_to_front

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: `status()` 返回 `alive/url/title/pid/headed/cdp_port/profile_dir/pages`. 不自动截图. 不做 `bring_to_front`.
- 理由: `alive` 双检 (pid + CDP 端口) 避免僵尸误判; 截图非必要 (用户否定); `bring_to_front` 跨平台不可靠, PRD 已列范围外.
- 预计影响: `operations.py` 新增 `status`; `result.py` 新增 `StatusResult`.
- 实际影响 (ISSUE-03 a1): `operations.py` — `status()` (alive 双检 pid+CDP), `cookies()`. `result.py` — `StatusResult` (8 字段), `CookiesResult`. `__init__.py` — 导出 status/cookies/StatusResult/CookiesResult. 测试: `tests/test_lifecycle.py` (5 tests). 审查: 无 blocker. 不自动截图, 无 bring_to_front.
- 相关 issue: ISSUE-03

## D011: 不设独立 doctor 命令, 探测+失败诊断进 config.py

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 不设独立 `doctor` 命令. 环境探测 (OS/`sys.executable`/tempdir/chromium 二进制) 烘焙进 `config.py`, 定位/装失败时抛带修复命令的精确错误.
- 理由: 探测本就是 `config.py` 启动副产物, 复用即可; 独立 doctor 增 API 面但用户痛点是 "失败时怎么修", 精确错误已解决. YAGNI.
- 预计影响: `config.py` 探测 + 错误诊断; 不新增 `doctor` 操作.
- 实际影响 (ISSUE-01 a1): `browser_agent/config.py` — `get_runtime_info()` (OS/python_executable/tempdir), `ChromiumNotInstalledError` (含 `<sys.executable> -m playwright install chromium` 修复命令), `BrowserConfig.locate_chromium_binary()` (探测失败时抛异常). 未新增 `doctor` 操作. 测试: `tests/test_config.py::test_get_runtime_info`, `test_chromium_not_installed_error_message_contains_command`.
- 相关 issue: ISSUE-01

## D012: CDP 端口分配 + Chromium 二进制定位

- 状态: 当前有效
- 约束性: 可调整
- 决策: 端口自绑 socket 到 0 取空闲端口, 传 `--remote-debugging-port=N`, connect 失败重试. Chromium 二进制路径首次用 transient `sync_playwright()` 读 `p.chromium.executable_path`, 缓存 `browser.json`.
- 理由: 自绑端口简单无 race (重试兜底); 不用 `=0`+解析 stderr (脱离式进程 stderr 捕获困难). `executable_path` 经 Playwright 定位最可靠, 缓存避免重复起 driver.
- 预计影响: `config.py` 端口分配 + 二进制定位 + 缓存.
- 实际影响 (ISSUE-01 a1): `browser_agent/config.py` — `allocate_cdp_port()` (自绑 socket 端口 0), `BrowserConfig.locate_chromium_binary()` (缓存优先 → transient `sync_playwright()` 读 `p.chromium.executable_path` → 写 `browser.json`). 测试: `tests/test_config.py::test_allocate_cdp_port_returns_bindable_port`, `test_locate_chromium_binary_returns_existing_path`, `test_locate_chromium_binary_caches_to_metadata`. 审查 note: TOCTOU race 已知可接受, connect 失败重试属 ISSUE-02 职责.
- 相关 issue: ISSUE-01

## D013: Grafana/Loki 专用查询辅助 — 范围外 (P2)

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 本次不做 Grafana/Loki 专用查询辅助函数, 不做批量 trace 查询模板, 不做产物自动清理 (`cleanup --older-than`). 列为 P2 后续.
- 理由: 聚焦通用浏览器会话与 escape hatch; 专用辅助依赖具体数据源, 后续按需补.
- 预计影响: 无; `browse.md` 说明范围外.
- 相关 issue: ISSUE-05
