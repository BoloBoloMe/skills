# access-web skill 优化提案

## 背景

本次使用 `access-web` 的交互浏览模式访问 Grafana 日志系统, 场景包括:

- 打开需要登录的 Grafana Explore URL.
- 用户在可见 Chromium 窗口中手动登录.
- 登录后复用同一浏览器会话读取页面内容.
- 通过 Grafana datasource proxy 查询 Loki 日志 JSON.
- 批量查询多个 trace ID, 汇总创建订单失败原因.

过程中暴露出一些可以沉淀到 skill 的问题和改进点.

## 遇到的问题

### 浏览器会话生命周期绑定错误

设计决策: 浏览器会话应在 pi 会话结束前持续有效. 用户登录态, cookies, 当前页面, browser context 等状态应绑定到 pi 会话, 而不是绑定到某一次 Python 工具进程.

当前实现中, `browse/browser_agent/session.py` 使用模块级单例 `_SESSION`, 并通过 `atexit` 清理 browser. 这导致 session 只在单个 Python 进程内有效. 一旦 agent 通过 shell 启动的 Python 命令退出, 浏览器和登录态就会丢失.

这与 `access-web` 的交互浏览语义冲突. 对于登录, 点击, 截图, 后续继续操作等任务, 用户预期是同一个 pi 会话内浏览器状态持续存在.

改进方向:

- 引入 pi-session scoped browser controller.
- 每个 pi 会话拥有独立 browser session id 和 artifact/session 目录.
- 浏览器 controller 作为长驻进程运行, 生命周期到 pi 会话结束或显式 stop.
- browser context 使用 persistent user data dir, 保存 cookies/localStorage/sessionStorage.
- 后续 `navigate/click/extract/screenshot` 通过 controller 复用同一 context/page.
- `reset_session` 只重置当前 pi 会话的浏览器, 不影响其他 pi 会话.
- 异常退出后, 下次操作应能根据 session metadata 判断 controller 是否存活, 必要时重启并复用 persistent profile.

验收:

- 用户登录一次后, 同一 pi 会话内后续工具调用不需要重新登录.
- Python 工具进程退出不影响浏览器状态.
- 同时打开多个 pi 会话时, 浏览器 session 互相隔离.
- pi 会话结束或显式 cleanup 后, controller 和临时 profile 可被清理.

本次临时方案 `pi_browser_control.py` 可视为正确架构的原型: 常驻 controller + per-session state. 后续需要产品化生命周期管理, session id, profile dir, cleanup 和并发隔离.

### headed 浏览器可见性需要明确验证

第一次启动后服务端状态显示已经打开登录页, 但用户没看到窗口. 后续重启后用户才看到.

可能原因:

- headed browser 启动在不同桌面/session 上.
- 浏览器窗口被遮挡或焦点不在前台.
- 启动方式和 shell 环境影响 GUI 显示.

建议:

- 启动 headed 模式后立即截图, 状态中返回 `pid/url/title/screenshotPath`.
- 提供 `bring_to_front` 或显式提示用户查看任务栏.
- 启动失败或用户看不到窗口时, 支持 fallback 到系统默认浏览器打开 URL.

### 路径策略不能硬编码为某个系统目录

本次出现过:

- `write` 写入 `/tmp/pi_browser_control.py`, bash 执行时解析到 Windows Temp 下找不到脚本.
- Python 进程里 `Path('/tmp/pay_logs')` 实际落到 `D:\tmp\pay_logs`, bash `/tmp/pay_logs` 不存在.

根因不是应该固定换成某个 Windows 目录, 而是 skill 不应预设当前环境的路径语义. agent 需要先探测当前系统环境, 再决定路径策略.

建议:

- browse 模式启动前先执行环境探测: OS, shell 类型, `sys.executable`, `tempfile.gettempdir()`, cwd, home, Python 管理方式, path 风格, bash/MSYS/WSL 映射.
- 所有临时目录通过 Python 标准库或系统环境计算, 不在 skill 文档中硬编码具体地址.
- 选定路径后写入 session metadata, 后续脚本/截图/日志都从 metadata 读取, 不重复推断.
- 对 agent 输出同时给出 tool 可读路径和人类可读路径. 如果存在 bash/MSYS 映射, 由环境探测结果转换.
- 禁止把 `/tmp`, `%LOCALAPPDATA%`, `/var/tmp` 等作为跨平台默认假设. 它们只能是某次环境探测后的候选结果.

### bash 环境中 `python` 不一定在 PATH

交互中直接执行 `python` 可用, 但 `nohup python ...` 失败:

```text
nohup: failed to run command 'python': No such file or directory
```

后续使用绝对路径成功:

```text
C:\Users\L9214\AppData\Roaming\uv\python\cpython-3.13.5-windows-x86_64-none\python.exe
```

建议:

- skill 运行时记录当前解释器 `sys.executable`.
- 常驻子进程使用 `sys.executable` 启动, 不依赖 PATH.
- 文档中避免假设 `python` 在所有 shell 子环境可见.

### JSON 中 Windows 路径转义容易失败

调用截图接口时, JSON body 中 Windows 路径反斜杠转义错误导致服务端 `JSONDecodeError`.

建议:

- 控制 API 支持不传 path 时自动保存到默认路径.
- 客户端统一用 `json.dumps` 生成请求 body, 不手写 JSON 字符串.
- API 支持 forward slash 路径或路径别名, 如 `{ "pathName": "latest-screenshot" }`.

### 页面语义提取对复杂 SPA 不够稳定

Grafana Explore 是复杂 SPA. `extract_text("main")` 只提取到 `Skip to main content`.

更有效的方法:

- 使用 screenshot 观察可视日志.
- 对 Grafana datasource proxy API 直接查询 Loki JSON.
- 对 `<pre>` 提取 JSON 后解析.

建议:

- 为常见 SPA 增加 `page_text`, `locator_text(css)`, `evaluate_js` 这类低层接口.
- `get_page_structure` 默认元素数较少, 可以支持更完整的可访问树/DOM 文本导出.

## 可复用脚本

### 常驻浏览器控制服务

本次临时脚本位置:

```text
C:\Users\L9214\AppData\Local\Temp\pi_browser_control.py
```

作用:

- 启动可见 Chromium.
- 打开指定 URL.
- 持有同一 browser/page, 保留用户登录态.
- 在 `127.0.0.1:51237` 提供控制接口.

已验证可用的全局 Python 启动方式:

```bash
BROWSER_HEADED=true \
PI_BROWSER_URL='https://example.com' \
PI_BROWSER_PORT=51237 \
nohup /c/Users/L9214/AppData/Roaming/uv/python/cpython-3.13.5-windows-x86_64-none/python.exe \
  /tmp/pi_browser_control.py \
  > /tmp/pi_browser_control_global.log 2>&1 &
```

状态检查:

```bash
curl -s http://127.0.0.1:51237/status
```

返回示例:

```json
{"ok": true, "url": "https://example.com/", "title": "Example Domain"}
```

建议将该脚本产品化到 skill 中, 不再放临时目录.

推荐接口:

- `GET /status`: 返回 pid, url, title, headed, profileDir.
- `GET /structure`: 返回页面结构.
- `POST /navigate`: 跳转 URL.
- `POST /extract`: 按描述或 selector 提取文本.
- `POST /screenshot`: 保存截图并返回路径.
- `POST /evaluate`: 执行只读 JS, 用于复杂 SPA 文本提取.
- `POST /close`: 主动关闭浏览器和控制服务.

安全约束:

- 只监听 `127.0.0.1`.
- 默认禁止任意文件写入, screenshot path 限制在 skill temp dir.
- `evaluate` 默认只读, 或明确标记高风险.

### Loki 批量查询模式

本次有效路线不是逐条操作 Grafana UI, 而是复用登录 cookie 访问 Grafana datasource proxy:

```text
/api/datasources/proxy/uid/<datasourceUid>/loki/api/v1/query_range
```

查询参数:

- `query`: `{job="test-middle-platform/cz-pay-center"}|="<traceId>"`
- `start`: now-6h 的纳秒时间戳.
- `end`: now 的纳秒时间戳.
- `limit`: `5000`.
- `direction`: `BACKWARD`.

建议沉淀一个 `grafana_loki_query_range` 辅助函数:

输入:

```json
{
  "baseUrl": "https://test-sg-monitor.changzhi.top",
  "datasourceUid": "eef933e7-e08a-4b58-917f-6c2321733537",
  "job": "test-middle-platform/cz-pay-center",
  "contains": "c-0817ebe9-e4c2-45ac-a82c-035ca9e5f8ad",
  "range": "now-6h",
  "limit": 5000
}
```

输出:

- 原始 Loki JSON.
- 按时间排序的 `.log` 文本.
- 命中行数.
- 错误关键词摘要.

这样能显著减少对 Grafana UI 的依赖.

## 建议改造方案

### 阶段 1: 依赖和环境自检

新增 `doctor` 或在首次 browse 前自动检查:

- Python 可执行路径.
- `playwright` 是否可导入.
- Chromium 是否已安装.
- headed 模式是否能启动.
- 当前 OS/path 映射信息.

失败时输出精确修复命令.

验收:

- 全局 Python 已安装时不重复安装.
- 缺少 Chromium 时提示 `python -m playwright install chromium`.
- 输出 `sys.executable` 和 browser cache 路径.

### 阶段 2: pi 会话级持久浏览器

将临时 HTTP 控制服务正式纳入 skill, 作为 pi-session scoped browser controller.

关键点:

- 使用 `sys.executable` 启动 controller 进程.
- 使用 `config.py` 探测并计算出的 session dir, 不在业务逻辑中硬编码目录.
- 每个 pi 会话独立 user data dir, cookie/localStorage/sessionStorage 随 pi 会话保留.
- 支持 `start/status/stop/restart`.
- 工具函数不直接创建临时 browser, 而是连接当前 pi 会话的 controller.
- controller 异常退出后, 下次操作可根据 metadata 重启并复用 profile.

验收:

- 用户登录后, 同一 pi 会话内后续命令不丢 cookie.
- Python 工具进程退出不影响浏览器状态.
- 重复调用 `navigate/extract/screenshot` 不重新打开浏览器.
- 多个 pi 会话的浏览器状态互相隔离.
- `stop` 能清理 controller 进程, 显式 cleanup 能清理 profile 和 artifacts.

### 阶段 3: 复杂页面提取能力

新增低层 API:

- `extract_page_text()`: 返回 `document.body.innerText`.
- `extract_selector_text(selector)`.
- `evaluate_js(script, readonly=True)`.
- `network_json(url, method='GET')`: 在浏览器上下文里带 cookie 请求 API.

Grafana/Loki 这种页面优先使用 `network_json`, 避免 UI 不稳定.

验收:

- Grafana Explore 可直接查询 Loki API 并解析 JSON.
- SPA 页面无需依赖 accessible name 才能提取正文.

### 阶段 4: 环境感知的路径和产物管理

不要在 skill 中指定固定产物目录. 启动时先探测环境, 再计算本次 pi 会话的 session root.

探测项:

- `platform.system()` 和 `os.name`.
- `sys.executable` 和 Python 管理方式, 如 uv/mise/system python.
- `tempfile.gettempdir()`, `Path.home()`, 当前 cwd.
- 当前 shell 是否为 bash/MSYS/Git Bash/WSL/PowerShell.
- Python native path 与 shell path 是否同一命名空间.

产物目录由 `config.py` 根据探测结果生成, 并写入 `status.json`:

- screenshots.
- downloaded files.
- extracted json/text.
- browser logs.
- control service pid/status.

验收:

- 不硬编码 Windows/Linux/macOS 专属目录作为默认值.
- 所有工具返回 canonical absolute path.
- 如果 agent 需要在 bash 中读取文件, 同时返回 shell-compatible path.
- 同一会话内所有操作复用 metadata 中的路径, 不重复猜测.
- 不再出现 `/tmp` 指向不一致导致找不到文件.

## 对本次 Grafana 日志任务的经验沉淀

对于 Grafana + Loki 查询, 推荐流程:

1. 用 headed 浏览器打开 Explore URL.
2. 用户登录.
3. 通过 `/status` 确认已进入 Grafana.
4. 从 URL 或页面配置中提取 datasource uid.
5. 使用 browser context 访问 datasource proxy 的 Loki API.
6. 保存原始 JSON 和排序后的 log 文本.
7. 用关键词和结构化字段提取失败原因.

本次关键词有效:

```text
Something is wrong
CREATE_ORDER_EXCEPTION_MESSAGE
HttpLoggingInterceptor
ControllerAspect - Return
ERROR
Exception
AMOUNT_INVALID
CONTRACT_INVALID
ONBOARD_ERROR
```

本次可复用错误归因规则:

- `HttpLoggingInterceptor - {"msg":...,"code":...}` 通常是三方响应.
- `CreatePayerMaxOrderServiceImpl - Something is wrong!{...}` 是创建 PayerMax 订单失败的直接摘要.
- `CREATE_ORDER_EXCEPTION_MESSAGE` 的 `content` 字段可作为告警内容.
- 若没有三方响应, 查看同 trace 的 ERROR 行和按 `orderId` 补查上下文.
- `selectOne() ... found: 2` 表示本地配置/数据重复, 不是三方返回.

## 清理策略

建议 skill 后续将浏览器脚本, 日志 JSON, 截图等产物统一登记到 session artifact 目录, 并提供:

```bash
access-web cleanup --older-than 7d
access-web cleanup --session <id>
```

## 源码级改造提案

### 当前源码结论

`browse/browser_agent/browser.py` 当前职责是直接启动 Playwright:

- `Browser.start()` 调用 `sync_playwright().start()`.
- 根据 `BROWSER_HEADED=true` 决定 headless/headed.
- 使用 `chromium.launch()` 创建非持久 browser.
- 使用 `browser.new_context()` 创建内存 context.
- 使用 `context.new_page()` 创建单页.
- `Browser.stop()` 关闭 context/browser/playwright.

`browse/browser_agent/session.py` 当前职责是进程内单例:

- `_SESSION` 是模块级全局变量.
- `get_session().page` 懒创建 `Browser`.
- `atexit.register(_cleanup)` 在 Python 进程退出时关闭浏览器.
- 文件注释明确写着 `进程内单例`, `内存 profile`, `不写磁盘`.

`browse/browser_agent/operations.py` 当前直接依赖 `get_session().page`:

- `navigate/click/type/extract/structure/scroll/wait/screenshot` 都在当前进程里拿 Playwright `Page` 对象操作.
- 返回类型来自 `result.py`, 目前是 dataclass, API 简单稳定.

测试当前大量 patch `Browser.start` 注入 HTML 或 route mock. 这说明 `Browser.start` 是现有测试 seam, 改造不能直接删除本地 Browser 模式.

### 目标架构

保留当前 public API 和返回 dataclass, 但把 `get_session().page` 背后的实现从进程内 `_SESSION` 改成可插拔 page provider.

建议新增 4 个模块:

```text
browser_agent/config.py
browser_agent/controller.py
browser_agent/client.py
browser_agent/providers.py
```

职责:

- `config.py`: 探测系统环境, 解析 pi session id, 计算 artifact 根目录, headed/headless, port/pid/profile 路径.
- `controller.py`: 长驻浏览器控制进程, 持有 Playwright browser/context/page.
- `client.py`: 当前工具进程中的轻量 HTTP client, 负责连接 controller.
- `providers.py`: 定义 `PageProvider` 抽象, 提供 `LocalPageProvider` 和 `ControllerPageProvider`.

### 生命周期模型

session key 应来自 pi 会话, 不应随机每次生成. 推荐优先级:

1. 环境变量 `PI_SESSION_ID` 或 pi harness 提供的会话 ID.
2. 环境变量 `PI_CONVERSATION_ID`.
3. fallback: 当前工作目录 + 父进程树 hash, 仅用于本地测试.

目录结构由环境探测结果决定. Windows 上可能类似下面这样, 但这只是示例, 不是硬编码默认:

```text
<sessionRoot>\
  controller.pid
  controller.port
  status.json
  profile\
  artifacts\
    screenshots\
    downloads\
    logs\
```

`profile\` 用于 Playwright persistent context, 保存 cookies/localStorage/sessionStorage. `artifacts\` 用于截图, 下载, 提取结果, 控制器日志. `<sessionRoot>` 必须写入 metadata, 后续所有进程通过 metadata 读取.

### Browser 改造

`Browser` 仍保留, 但改为支持两种启动方式.

当前:

```python
self._browser = self._playwright.chromium.launch(headless=headless)
self._context = self._browser.new_context()
self._page = self._context.new_page()
```

建议新增 persistent 参数:

```python
class Browser:
    def __init__(self, user_data_dir: str | None = None, headed: bool | None = None):
        self._user_data_dir = user_data_dir
        self._headed = headed
```

启动逻辑:

```python
if self._user_data_dir:
    self._context = self._playwright.chromium.launch_persistent_context(
        self._user_data_dir,
        headless=headless,
        accept_downloads=True,
    )
    self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
else:
    self._browser = self._playwright.chromium.launch(headless=headless)
    self._context = self._browser.new_context(accept_downloads=True)
    self._page = self._context.new_page()
```

注意: persistent context 没有单独的 `Browser` 句柄, stop 时关闭 context 即可.

### Session 改造

`session.py` 不应再直接持有进程内 `_SESSION` 作为默认实现. 建议改成 facade:

```python
def get_session() -> Session:
    return Session(provider=get_default_provider())
```

provider 选择:

- 测试环境或 `ACCESS_WEB_MODE=local`: `LocalPageProvider`, 保持现在行为.
- 默认交互浏览: `ControllerPageProvider`, 连接 pi-session controller.

`reset_session()` 语义也要拆分:

- `reset_session()`: 重置当前工具进程 facade/cache, 不杀 controller.
- `stop_browser_session()`: 显式停止当前 pi 会话 controller.
- `cleanup_browser_session()`: 停止 controller 并删除 profile/artifacts.

这样避免测试 fixture 里的 `reset_session()` 误删用户登录态.

### Controller API

把本次临时 `pi_browser_control.py` 正式化, 但不要直接用临时代码原样落库. 推荐 API:

```text
GET  /status
POST /navigate
POST /click
POST /type
POST /extract
POST /structure
POST /scroll
POST /wait
POST /screenshot
POST /page_text
POST /selector_text
POST /evaluate
POST /network_json
POST /close
```

返回 JSON 应和 `result.py` dataclass 字段一致, 例如:

```json
{"success": true, "error": null, "url": "https://example.com"}
```

`/network_json` 很关键: 它应该在浏览器上下文里执行 `fetch`, 自动携带当前登录 cookie, 用于 Grafana datasource proxy 这类场景.

示例请求:

```json
{
  "url": "https://test-sg-monitor.changzhi.top/api/datasources/proxy/uid/.../loki/api/v1/query_range?...",
  "method": "GET",
  "timeout": 60
}
```

### Operations 改造

`operations.py` 保持函数名和返回类型不变. 但每个函数内部不要直接假设拿到 Playwright `Page`.

建议路径:

1. `provider = get_page_provider()`.
2. 如果 provider 是 local, 调用当前 Playwright 逻辑.
3. 如果 provider 是 controller, 调用 `client.py` HTTP API.
4. 将 JSON 响应映射回 `NavigateResult/OperationResult/ExtractResult/ScreenshotResult/StructureResult`.

这样可以保留现有测试, 同时新增 controller 集成测试.

### 测试计划

保留现有测试:

- `test_navigate.py`
- `test_interaction.py`
- `test_extraction.py`
- `test_integration.py`

这些测试应在 `ACCESS_WEB_MODE=local` 下继续通过.

新增测试:

1. `test_browser_persistent_context.py`
   - 使用临时 `user_data_dir` 启动 Browser.
   - 设置 cookie/localStorage.
   - stop 后重新 start.
   - 验证 cookie/localStorage 仍存在.

2. `test_controller_lifecycle.py`
   - start controller.
   - status 返回 pid/port/profileDir.
   - navigate 后退出当前 client 进程.
   - 新 client 再 status, URL 仍保留.
   - close 后 pid 不存在.

3. `test_session_scoping.py`
   - 模拟两个 `PI_SESSION_ID`.
   - 分别 navigate 到不同页面.
   - 验证状态互不影响.

4. `test_network_json.py`
   - mock 一个需要 cookie 的接口.
   - 浏览器先设置 cookie.
   - `/network_json` 请求能携带 cookie 并返回 JSON.

5. `test_reset_semantics.py`
   - `reset_session()` 不关闭 controller.
   - `stop_browser_session()` 关闭 controller.
   - `cleanup_browser_session()` 删除 profile/artifacts.

### 兼容策略

短期不要破坏现有调用方式:

```python
from browser_agent import navigate, click_element, extract_text
```

新增导出:

```python
from browser_agent import status
from browser_agent import stop_browser_session
from browser_agent import cleanup_browser_session
from browser_agent import page_text
from browser_agent import selector_text
from browser_agent import network_json
```

`browse.md` 也要更新:

- 明确浏览器会话生命周期绑定 pi 会话.
- 说明登录态在 pi 会话内保持.
- 说明 `reset_session` 和 `stop/cleanup` 区别.
- 说明 artifacts 路径.
- 说明 Grafana/Loki 这类 API 查询优先用 `network_json`.

### 迁移步骤

1. 新增 `config.py`, 负责环境探测, 路径策略, session id 计算, 加单元测试.
2. 改造 `Browser` 支持 `launch_persistent_context`, 保持旧行为默认不变.
3. 新增 `controller.py` 和 `client.py`, 先覆盖 `status/navigate/screenshot/page_text`.
4. 在 `operations.py` 增加 provider 分支, 默认仍可通过环境变量回退 local.
5. 扩展 controller API 到 click/type/extract/structure/scroll/wait.
6. 新增 `network_json`, 替代复杂 SPA 的 UI 文本抓取.
7. 更新 `browse.md` 和 tests.
8. 最后把默认模式切到 controller.

## 优先级

P0:

- 依赖自检.
- 使用 `sys.executable`.
- 持久浏览器控制服务.
- `stop/status` 管理.

P1:

- 统一 Windows 临时目录.
- 环境感知路径策略和 screenshot/artifact 路径规范.
- `page_text/selector_text/evaluate`.

P2:

- Grafana Loki 专用查询辅助.
- 批量 trace 查询和错误摘要模板.
- 产物自动清理.

## 预期收益

- 登录态可稳定复用, 不需要每次重新登录.
- 依赖和浏览器环境问题可在任务开始前被明确诊断.
- 对 Grafana/SPA 的提取更可靠.
- 跨 OS/shell/Python 管理方式的路径问题减少.
- 日志分析任务可以从截图驱动升级为结构化 JSON 驱动.
