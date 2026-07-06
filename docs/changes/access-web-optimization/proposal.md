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

- 利用 CDP (Chrome DevTools Protocol) 实现跨进程浏览器共享. Playwright 原生支持 `connect_over_cdp()`, 任何进程连上同一 CDP WebSocket 即可操控同一 browser/context/page.
- 每个 pi 会话指定独立 `user_data_dir` (persistent profile), cookies/localStorage/sessionStorage 落盘保存.
- 首次调用: `launch_persistent_context(user_data_dir, args=["--remote-debugging-port=N"])`, 写入 metadata (端口/目录).
- 后续调用: 从 metadata 读到 CDP 端口 → `connect_over_cdp()` 直接获取已有 browser 和 context, 不重新启动.
- browser 进程由 Chromium 自身管理, 没有额外的 controller 进程. Python 工具进程退出不影响 browser.
- `reset_session()` 只断开当前进程的 Playwright 连接, 不影响 browser 进程.
- browser 挂掉后: 下次 `connect_over_cdp` 失败 → 用同一 `user_data_dir` 重新 `launch_persistent_context`, profile 保留登录态.

验收:

- 用户登录一次后, 同一 pi 会话内后续工具调用不需要重新登录.
- Python 工具进程退出不影响浏览器状态.
- 同时打开多个 pi 会话时, 浏览器 session 通过不同 `user_data_dir` 和 CDP 端口互相隔离.
- pi 会话结束或显式 cleanup 后, browser 进程和 profile 可被清理.

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

### CDP 跨进程浏览器共享

本次临时的 `pi_browser_control.py` 用一个独立 HTTP 进程做了中转. 更简洁的方案是直接利用 Chromium 内置的 CDP (Chrome DevTools Protocol) — Playwright 原生支持跨进程连接, 不需要中间层.

Playwright CDP 连接机制:

```python
# 首次: 启动 Chromium 并暴露 CDP 端口
from playwright.sync_api import sync_playwright

browser = chromium.launch_persistent_context(
    user_data_dir,
    headless=False,
    args=["--remote-debugging-port=9222"],
)
# 写入 metadata: {"cdp_port": 9222, "profile_dir": user_data_dir}

# 后续: 新进程直接连接已有 browser
browser = chromium.connect_over_cdp("http://127.0.0.1:9222")
context = browser.contexts[0]   # cookies/localStorage 都在
page = context.pages[0]          # 当前页面
```

无需额外进程, 无需 HTTP API 定义和序列化. `operations.py` 中的 `_locator`, `_structure` 拿到的仍然是真实 Playwright `Page` 对象, 完全不做改动.

安全约束:

- CDP 端口仅监听 `127.0.0.1`, 不接受外部连接.
- 端口号写入 metadata, 每次随机分配避免冲突.

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

利用 CDP 实现跨进程浏览器共享, 取代临时 HTTP 控制服务.

关键点:

- 每个 pi 会话分配独立 `user_data_dir` (persistent profile), cookies/localStorage/sessionStorage 落盘.
- 首次调用: `launch_persistent_context(user_data_dir, args=["--remote-debugging-port=N"])`, 写入 metadata (端口, profile 路径, session id).
- 后续调用: 从 metadata 读到 CDP 端口 → `connect_over_cdp()` 获取已有 browser, 不重新启动.
- 支持 `status/stop/cleanup`:
  - `status()`: 通过 metadata 和服务端 CDP 端口检测 browser 是否存活.
  - `stop_browser_session()`: 通过 CDP 发送 `Browser.close`, 清理 browser 进程.
  - `cleanup_browser_session()`: stop + 删除 profile 和 artifacts 目录.
- `reset_session()`: 断开当前进程的 Playwright 连接, 不关 browser. 下次调用自动 reconnect.
- browser 异常退出后: `connect_over_cdp` 抛异常 → 用同一 `user_data_dir` 重新 launch, 登录态不失.
- 不使用 `subprocess.Popen` 管理额外进程, 不依赖 `nohup`/`start_new_session`.

验收:

- 用户登录后, 同一 pi 会话内后续命令不丢 cookie.
- Python 工具进程退出不影响浏览器状态.
- 重复调用 `navigate/extract/screenshot` 不重新打开浏览器.
- 多个 pi 会话的浏览器状态通过不同 profile 和端口互相隔离.
- `stop` 能关闭 browser 进程, `cleanup` 能清理 profile 和 artifacts.

### 阶段 3: 三层函数体系

agent 最擅长写代码 → 看结果 → 改代码的快速迭代. 函数设计应匹配这个模式: 简单操作一击完成, 复杂场景给一个 JS escape hatch, 极端情况给裸 CDP.

```
┌──────────────────────────────────────────────┐
│ L1 语义函数   navigate, click, extract,       │  ← 80% 日常操作
│               get_page_structure,              │
│               screenshot, scroll, wait         │
├──────────────────────────────────────────────┤
│ L2 escape     evaluate_js(script)             │  ← 15% 复杂 SPA
│   hatch       network_json(url, method, body) │     带 cookie API
├──────────────────────────────────────────────┤
│ L3 裸 CDP     cdp_send(method, params)        │  ← 5% browser 级操作
│                                                │     调试/性能/新 tab
└──────────────────────────────────────────────┘
```

**L1 语义函数** (已有, 不动):

- `navigate(url)` — 打开/跳转.
- `click_element(description)` — 语义定位 + 点击.
- `type_text(description, text)` — 语义定位 + 输入.
- `extract_text(description)` — 语义定位 + 提取.
- `get_page_structure()` — DOM 可访问树.
- `screenshot(path=None)` — 截图.
- `scroll(direction, amount)` — 滚动.
- `wait_for_element(description, state)` — 等待.

**L2 escape hatch** (新增):

- `evaluate_js(script)`: 在浏览器当前页面执行任意 JS. **不限制读写**. agent 可以用它一站式完成: 定位 → 操作 → 等待 SPA 渲染 → 提取数据 → 返回. 完全替代"新增一堆特殊提取函数"的需求.
- `network_json(url, method, body)`: 通过 Playwright `context.request` (APIRequestContext) 在浏览器上下文发起 HTTP, 自动共享 cookie, 不受 CORS 限制. 不推荐 `page.evaluate(fetch)` 因为跨域 CORS 拦截.

**L3 裸 CDP** (新增):

- `cdp_send(method, params=None)`: 发送原始 Chrome DevTools Protocol 命令. L1+L2 都做不到时使用 (如 `Performance.getMetrics`, `Emulation.setGeolocationOverride`).

**browser 管理** (新增):

- `status()` — url, title, headed, tabs 列表, profile dir.
- `cookies()` — 当前 context 所有 cookies.
- `stop_browser_session()` — CDP `Browser.close`.
- `cleanup_browser_session()` — stop + 删 profile 和 artifacts.
- `reset_session()` — 断开当前进程连接 (测试用 local 模式则停 browser).

**agent 使用模式**:

1. 先用 L1. 有语义函数就用, 一键完成.
2. L1 不够 (数据在 JS 对象不在 DOM, 需要复杂交互序列): 用 `evaluate_js` 一把完成.
3. evaluate_js 做不了跨域请求: 用 `network_json`.
4. 需要 browser 级操作 (开 tab, 性能, 网络): 用 `cdp_send`.
5. 不要用 `evaluate_js` 模拟点击/输入, 除非语义定位失败. 语义定位更稳定 (Playwright auto-wait + retry).

验收:

- Grafana SPA 可先用 `evaluate_js` 探测 `Object.keys(window)`, 找到 `__grafana_initial_state` 后直接提取 JSON.
- Grafana Loki 查询用 `network_json` 直接访问 datasource proxy API 并解析 JSON.
- SPA 页面无需依赖 accessible name 才能提取正文.
- agent 有 undefined behavior 可通过 `cdp_send` 自行探索, 不依赖我们预封装的函数.

### 阶段 4: 环境感知的路径和产物管理

不要在 skill 中指定固定产物目录. 启动时先探测环境, 再计算本次 pi 会话的 session root.

探测项:

- `platform.system()` 和 `os.name`.
- `sys.executable` 和 Python 管理方式, 如 uv/mise/system python.
- `tempfile.gettempdir()`, `Path.home()`, 当前 cwd.
- 当前 shell 是否为 bash/MSYS/Git Bash/WSL/PowerShell.
- Python native path 与 shell path 是否同一命名空间.

产物目录由 `config.py` 根据探测结果生成, 并写入 `browser.json`:

- screenshots.
- downloaded files.
- extracted json/text.
- browser logs.
- browser pid/port/status.

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
3. 通过 `status()` 确认已进入 Grafana.
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

保留当前 public API 和返回 dataclass. 改动集中在 `Browser` 和 `session` 两层, `operations/_locator/_structure/result` 不动.

建议新增 1 个模块:

```text
browser_agent/config.py
```

改动 1 个模块, 保留其余:

```text
browser_agent/browser.py    ← 改造: +persistent context / +connect_over_cdp
browser_agent/session.py    ← 轻微改造: metadata 驱动连接
browser_agent/_locator.py   ← 不动
browser_agent/_structure.py ← 不动
browser_agent/operations.py ← 不动 (仍通过 session.page 拿 Page)
browser_agent/result.py     ← 不动
```

不新增:

- `controller.py` — Chromium 自身就是 controller (通过 CDP).
- `client.py` — Playwright 自身就是 client (`connect_over_cdp`).
- `providers.py` — 不需要 backend 抽象, 所有进程都用同样的 Playwright API 拿到真实 `Page` 对象.

职责:

- `config.py`: 探测系统环境, 解析 pi session id, 计算 artifact 根目录, profile 路径, 分配 CDP 端口, 读写 metadata 文件.
- `browser.py`: `Browser` 类增加 `launch_persistent_context` 分支和 `connect_over_cdp` 分支, 根据 metadata 自动选择.
- `session.py`: `get_session()` 逻辑: 读 metadata → 尝试 connect → 失败则 launch 并写 metadata.

### 生命周期模型

**session key**: 来自 pi 会话. 推荐优先级:

1. 环境变量 `PI_SESSION_ID` 或 pi harness 提供的会话 ID.
2. 环境变量 `PI_CONVERSATION_ID`.
3. fallback: 当前工作目录 + 父进程树 hash, 仅用于本地测试.

**metadata 文件**: 位于 `<sessionDir>/browser.json`, 内容:

```json
{
  "cdp_port": 9222,
  "profile_dir": "<sessionDir>/profile",
  "session_id": "...",
  "created_at": "...",
  "status": "running"
}
```

任何进程进入时先读 metadata. 如果 `cdp_port` 可连通则 connect; 否则 launch 并更新 metadata.

**目录结构** (由 `config.py` 计算, 不硬编码):

```text
<sessionDir>/
  browser.json       ← metadata
  profile/            ← Playwright persistent user_data_dir
  artifacts/
    screenshots/
    downloads/
    logs/
```

`profile/` 用于 persistent context, 保存 cookies/localStorage/sessionStorage. `artifacts/` 用于截图, 下载, 提取结果.

### Browser 改造

`Browser` 仍保留, 改为支持三种模式, 按参数自动选择:

1. **local (现有, 测试用)**: `user_data_dir=None, cdp_port=None` — 走当前 `chromium.launch()`.
2. **persistent local (本地调试)**: `user_data_dir=xxx, cdp_port=None` — 走 `launch_persistent_context`, 不暴露 CDP.
3. **persistent + CDP (交互浏览)**: `user_data_dir=xxx, cdp_port=xxx` — 走 `launch_persistent_context` + `--remote-debugging-port`, 写 metadata.

新增类方法:

```python
class Browser:
    def __init__(self, user_data_dir: str | None = None,
                 cdp_port: int | None = None, headed: bool | None = None):
        ...

    @classmethod
    def connect(cls, cdp_port: int) -> "Browser":
        """通过 CDP 连接已有 browser, 复用 context 和 page."""
        ...

    def status(self) -> dict:
        """返回 {url, title, pid, headed, profile_dir}."""
        ...
```

`connect()` 内部:

```python
browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
context = browser.contexts[0]
page = context.pages[0] if context.pages else context.new_page()
```

`stop()` 已有多层 None 保护, persistent context 分支无需 `Browser.close()`, 只需关 context.

### Session 改造

`session.py` 不再用模块级 `_SESSION` 进程内单例. 改为查询 metadata 决策:

```python
def get_session() -> Session:
    meta = config.read_metadata()
    if meta and _cdp_alive(meta.cdp_port):
        return Session(Browser.connect(meta.cdp_port))
    else:
        browser = Browser(
            user_data_dir=config.profile_dir(),
            cdp_port=config.allocate_port(),
            headed=config.is_headed(),
        )
        browser.start()
        config.write_metadata(cdp_port=config.allocate_port(), ...)
        return Session(browser)
```

`reset_session()`:

- 断开当前进程 Playwright 连接 (browser.stop() 仅关 context, 不关 Chromium 进程).
- local 模式 (`ACCESS_WEB_MODE=local`): 仍停 `Browser` (保持现状, conftest autouse fixture 测试隔离).
- 会话模式: 只清当前进程 cache, 不停 Chromium.

`stop_browser_session()`: 通过 CDP `Browser.close` 关闭 Chromium 进程.
`cleanup_browser_session()`: stop + 删除 profile 和 artifacts 目录.

### Operations 改造

现有 8 个 L1 函数不动. 新增 5 个 L2+L3+管理函数:

```python
def evaluate_js(script: str) -> EvalResult:
    """在浏览器当前页面执行任意 JS, 返回结果."""
    page = get_session().page
    result = page.evaluate(script)
    return EvalResult(success=True, data=result)

def network_json(url: str, method="GET", body=None,
                 headers=None) -> NetworkResult:
    """以浏览器 context 身份发 HTTP, 自动携带 cookies."""
    session = get_session()
    ctx = session._browser._context  # or session.context
    resp = ctx.request.fetch(url, method=method, data=body, headers=headers)
    return NetworkResult(success=True, status=resp.status, body=resp.body(),
                         json=resp.json() if resp.headers.get("content-type") == "application/json" else None)

def cdp_send(method: str, params: dict | None = None) -> dict:
    """发送原始 CDP 命令."""
    page = get_session().page
    cdp = page.context.new_cdp_session(page)
    return cdp.send(method, params)

def status() -> StatusResult:
    """返回 {url, title, headed, profile_dir, cdp_port, pages[]}."""
    ...

def cookies() -> list[dict]:
    """当前 context 所有 cookies."""
    ...
```

`_locator.py` 和 `_structure.py` 不动, 仍直接拿 Playwright `Page`. CDP 方案保证所有进程拿到的就是真实 `Page` 对象.

### 测试计划

保留现有测试 (在 `ACCESS_WEB_MODE=local` 下继续通过):

- `test_navigate.py`
- `test_interaction.py`
- `test_extraction.py`
- `test_integration.py`

新增测试:

1. `test_browser_persistent_context.py`
   - 使用临时 `user_data_dir` 启动 Browser.
   - 设置 cookie/localStorage.
   - stop 后重新 start.
   - 验证 cookie/localStorage 仍存在.

2. `test_cdp_connect.py`
   - 用 `launch_persistent_context` + CDP 端口启动 browser.
   - 在新 Python 进程中 `connect_over_cdp`.
   - 验证第二个进程拿到同一 page, URL 一致.
   - 第一个进程退出后, browser 仍在 (第二个进程可继续操作).

3. `test_cdp_reconnect_after_browser_death.py`
   - 启动 CDP browser.
   - 手动 kill Chromium 进程.
   - 验证 `connect_over_cdp` 抛异常.
   - 用同一 `user_data_dir` 重新 launch, 验证 cookie 仍存在.

4. `test_session_scoping.py`
   - 两个不同 `user_data_dir` + 不同 CDP 端口.
   - 分别 navigate 到不同页面.
   - 验证状态互不影响.

5. `test_network_json.py`
   - 浏览器设置 cookie.
   - `context.request` 发请求, 验证携带 cookie.

6. `test_evaluate_js.py`
   - 设置 `page.set_content("<div id='app'>hello</div>")`.
   - `evaluate_js("document.querySelector('#app').innerText")` 返回 `"hello"`.
   - `evaluate_js("await new Promise(r => setTimeout(r, 100)); return 'done'")` 验证 async.
   - `evaluate_js("window.__test = 42; return window.__test")` 验证写+读.

### 兼容策略

短期不要破坏现有调用方式:

```python
from browser_agent import navigate, click_element, extract_text
```

新增导出:

```python
# L2 escape hatch
from browser_agent import evaluate_js
from browser_agent import network_json

# L3 裸 CDP
from browser_agent import cdp_send

# browser 管理
from browser_agent import status
from browser_agent import cookies
from browser_agent import stop_browser_session
from browser_agent import cleanup_browser_session
```

`browse.md` 更新:

- 明确浏览器会话生命周期绑定 pi 会话.
- 说明登录态在 pi 会话内保持.
- 给出三层函数一览和选择指南:
  ```markdown
  ## 选择哪个函数
  1. 先看 L1: 你的意图能不能用一个语义函数完成? → 直接调.
  2. L1 不够: 页面是 SPA, 数据不在 DOM 而在 JS 对象里?
     → evaluate_js("JSON.stringify(window.__data)") 一把拿到.
  3. evaluate_js 做不了跨域请求? → network_json.
  4. 需要 browser 级操作 (性能/网络/新 tab)? → cdp_send.
  5. 不要用 evaluate_js 模拟点击/输入, 除非语义定位失败.
     语义定位更稳定 (有 auto-wait 和 retry).
  ```
- 说明 `reset_session`/`stop_browser_session`/`cleanup_browser_session` 区别.
- 说明 artifacts 路径.

### 迁移步骤

1. 新增 `config.py`, 负责环境探测, 路径策略, session id 计算, 加单元测试.
2. 改造 `Browser`: 加 `user_data_dir`/`cdp_port` 参数, `launch_persistent_context` 分支, `connect()` 类方法. 旧行为 (`Browser()` 无参) 保持.
3. 改造 `session.py`: `get_session()` 改为 metadata 驱动 (try connect → fallback launch). `reset_session` 按 mode 分支. 加 `stop_browser_session`/`cleanup_browser_session`.
4. conftest.py 设 `ACCESS_WEB_MODE=local` (或 `pyproject.toml` `[tool.pytest.ini_options]` env), 确保现有 4 个测试文件在 local 模式下运行, patch `Browser.start` 仍生效. 此步在步骤 5 前完成.
5. `__init__.py` 新增导出: `evaluate_js`, `network_json`, `cdp_send`, `status`, `cookies`, `stop_browser_session`, `cleanup_browser_session`. 更新 `browse.md` (含三层选择指南).
6. 新增 `evaluate_js`/`network_json`/`cdp_send` 操作实现.

## 优先级

P0:

- 依赖自检.
- 持久浏览器 (CDP `connect_over_cdp` + `launch_persistent_context`).
- `status/stop/cleanup` 生命周期管理.

P1:

- 环境感知路径策略和 artifact 路径规范.
- `evaluate_js`, `network_json`, `cdp_send` escape hatches.

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
