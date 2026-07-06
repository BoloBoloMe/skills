# access-web skill 优化提案审核

审核对象: `proposal.md` (同目录)
审核依据: `access-web` skill 源码 `C:\Users\L9214\.pi\agent\skills\access-web\browse\`
审核日期: 2026-07-06

## 结论

大方向可行, 架构与源码现状吻合. 但有 9 处落地细节缺失或需修正, 其中 A/B/C 三处不修正会导致改造后测试挂或功能不达预期. 建议动手前先补 A/B/C/D 四项到提案.

## 源码核对

核对提案对现状的描述与实际源码是否一致.

| 提案描述 | 源码位置 | 结论 |
|---|---|---|
| `session.py` 模块级 `_SESSION` + `atexit`, `Session` 包装 `Browser` | `browser_agent/session.py` | 一致 |
| `browser.py` `chromium.launch()` + `new_context()` + `new_page()` | `browser_agent/browser.py` | 一致 |
| `stop()` 有 `if self._browser is not None` 保护 | `browser.py:stop` | 一致, persistent 分支可安全加入 |
| `operations.py` 8 函数全走 `get_session().page` | `browser_agent/operations.py` | 一致 |
| `result.py` dataclass 继承链 `NavigateResult(OperationResult)` | `browser_agent/result.py` | 一致 |
| tests patch `Browser.start` 注入 `set_content`/`route`, conftest autouse `reset_session()` | `browse/tests/*.py`, `conftest.py` | 一致, `Browser.start` 确是 seam |
| `_locator.py`/`_structure.py` 直接依赖 Playwright `Page` | `browser_agent/_locator.py`, `_structure.py` | 一致, 但提案未提归属迁移, 见 F |

## 需修正项

按严重度排序. 高严重度三项不修正将直接导致改造失败或测试挂.

### A. `reset_session` 一刀切 "不杀 controller" 会破坏 local 测试隔离 [高]

**位置**: 提案 "Session 改造" 节, `reset_session()` 语义拆分.

**问题**: `conftest.py` autouse fixture 每个测试前后调 `reset_session()`. 提案规定 reset 只清 facade 不停 controller. 但 local 模式下若 reset 不停 browser, 测试间浏览器残留, 隔离失效, 现有 4 个测试文件的 patch 上下文会互相污染.

**修正**: `reset_session` 按 mode 分支.
- local 模式: 仍停 `Browser` (保持现状, 测试隔离).
- controller 模式: 只清 client facade cache, 不停 controller.

### B. conftest 未锁定 `ACCESS_WEB_MODE=local` [高]

**位置**: 提案 "迁移步骤" 步骤 8 "切默认到 controller".

**问题**: 切默认后, 现有 4 个测试文件 patch `Browser.start` 走 local 路径, 默认 controller 模式下 patch 不生效 (controller 不经过 `Browser.start`), 全部失败. 提案说 "测试应在 local 下继续通过" 但没写在哪设环境变量.

**修正**: 迁移步骤 7 必须包含 conftest.py 设 `ACCESS_WEB_MODE=local` (或 `pyproject.toml` `[tool.pytest.ini_options]` env), 在步骤 8 切默认前落地.

### C. `network_json` 用 `page.evaluate(fetch)` 受 CORS 限制 [高]

**位置**: 提案 "Controller API" `/network_json`, "阶段 3" `network_json`.

**问题**: 提案说 "在浏览器上下文执行 fetch 携带 cookie". 同源 Grafana proxy 可行, 跨域 API 会被浏览器 CORS 拦截, 无法通用.

**修正**: 改用 Playwright `context.request` (APIRequestContext) 或 `page.request`, 自动共享 context cookie 且不受 CORS. 这是更稳的实现路径, 提案应明确写为首选方案.

### D. provider 命名 `PageProvider`/`get_page_provider()` 误导 [中]

**位置**: 提案 "目标架构" `providers.py`, "Operations 改造" 步骤 1.

**问题**: `_locator.locate(page, description)` 需要真实 `Page` 对象, controller 模式无法返回 `Page`. 提案命名暗示 provider 返回 Page, 但实际需操作级分派, 否则 `_locator` 无法在 client 侧运行.

**修正**: 接口改为 `OperationBackend` (或 `Backend`), 方法对应每个操作 (`click`/`extract_text`/`structure`/...). `LocalBackend` 内部用 Playwright + `_locator`/`_structure`, `ControllerBackend` 用 HTTP client. 不暴露 `Page`.

### E. controller 模式 `screenshot(path=None)` 返回 bytes 需 base64 [中]

**位置**: 提案 "Controller API" `/screenshot`.

**问题**: 当前 `screenshot(path=None)` 返回 `ScreenshotResult.image: bytes`. 提案 `/screenshot` 只说 "保存并返回路径", 与 bytes 语义冲突, controller 模式下 `path=None` 无路径可返回.

**修正**: controller `/screenshot` 支持两种返回.
- `path=None`: 返回 base64, client 解码成 `ScreenshotResult.image: bytes`.
- `path` 非空: 写文件返回 path, client 填 `ScreenshotResult.path`.

### F. `_locator.py`/`_structure.py` 归属未说明 [中]

**位置**: 提案 "目标架构" 新增模块列表, "Operations 改造".

**问题**: controller 侧需复用定位与结构提取逻辑, 提案未提这两个模块如何共享.

**修正**: 两个模块保留在 `browser_agent/` 包内, controller 进程 import 使用; client 侧仅 `LocalBackend` 用. 与 D 一并处理.

### G. controller 启动需 `subprocess.Popen` 跨平台脱离, 非依赖 `nohup` [中]

**位置**: 提案 "可复用脚本" 启动示例, "阶段 2" 关键点.

**问题**: 提案示例用 `nohup` (MSYS 语义), Windows 原生无此命令. 落库需跨平台脱离父进程.

**修正**: `client.py` 启动 controller 用 `subprocess.Popen`, Windows `creationflags=DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP`, POSIX `start_new_session=True`. 不依赖 shell `nohup`.

### H. session id 来源 `PI_SESSION_ID` 未验证 [中]

**位置**: 提案 "生命周期模型" session key 优先级.

**问题**: 提案假设 pi harness 暴露 `PI_SESSION_ID`, 但未确认. fallback "cwd+父进程 hash" 在同目录多会话下冲突, 隔离不稳.

**修正**: 先向 pi 确认是否注入会话标识. 若无, 改用 well-known location (如 cwd 下 `.access-web/session.id`) 存 uuid, 首次生成后续复用, 显式 cleanup 时删除.

### I. controller 测试需标记 slow/integration [低]

**位置**: 提案 "测试计划" 新增测试 2~5.

**问题**: `test_controller_lifecycle.py` 等需真实 Chromium + HTTP server, 慢且 CI 可能无 headed 环境.

**修正**: 加 `@pytest.mark.integration` + conftest `--run-integration` opt, 默认跳过.

## 可行点确认

以下提案点经核对源码后确认可行, 无需修正.

- `Browser` 加 `user_data_dir`/`headed` 参数 + `launch_persistent_context` 分支: 可行. `stop()` 现有 None 保护兼容 persistent 分支; 测试 `Browser()` 无参调用仍可 (参数有默认值).
- persistent context 无 `Browser` 句柄, stop 关 context: 提案已正确处理.
- `__init__.py` 新增导出 `status`/`stop_browser_session`/`cleanup_browser_session`/`page_text`/`selector_text`/`network_json`: 可行, 直接加.
- `pyproject.toml` 无新依赖: 可行, controller 用 stdlib `http.server` 即可.
- 迁移步骤顺序 (config -> Browser persistent -> controller/client -> provider 分支默认 local -> 扩展 API -> network_json -> 文档/tests -> 切默认): 顺序合理, 补 A/B 后可执行.
- `browse.md` 更新: 可行. 现文档已说 "对话内保持", 与 pi 会话级语义一致, 需补 reset/stop/cleanup 区别和 `network_json` 优先用例.

## 建议动作

1. 将 A/B/C/D 四项补入 `proposal.md` 对应章节, 再进入实现. (推荐)
2. 不修订提案, 直接在实现时按本审核结果处理, 风险是提案与实现偏离.
3. 先向 pi 确认 H (session id 来源), 再决定是否修订.
