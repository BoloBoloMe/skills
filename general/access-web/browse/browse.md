# 交互浏览

基于 Playwright 驱动 Chromium 的语义化浏览器操作. 浏览器以**脱离式子进程**启动, 绑定当前 pi 会话 (由 cwd 派生的 session-key 决定). 首次调用时懒启动, 工具进程退出后 Chromium 仍然存活, 同一会话内的后续工具调用自动复用同一浏览器、profile 与登录态.

**关键**: 同一工作目录共享同一个浏览器会话; 不同工作目录相互隔离. 整个会话只有一个浏览器窗口/一个默认标签页, `navigate` 在当前标签页跳转. 只有需要同时对比两个不同页面时才开新标签 (极少). 默认使用 `headless` 模式; 设置环境变量 `BROWSER_HEADED=true` 可切换到 headed 模式, 登录弹窗由人类操作.

## 生命周期与产物

### 绑定 pi 会话

- `session-key = sha256(canonicalize(cwd))[:16]`, 基于当前工作目录计算, 同 cwd 共享, 不同 cwd 隔离.
- 首次调用任意操作时, 以 `subprocess.Popen` 脱离式启动 Chromium (`--user-data-dir` + `--remote-debugging-port`), 并写入 `browser.json` 元数据.
- 之后无论工具进程是否退出, Chromium 继续在后台运行. 新的工具进程通过 CDP (`connect_over_cdp`) 连接并复用.
- 登录态、cookie、localStorage 等保存在 profile 中, 会话内保持, 不必重复登录.
- 若 Chromium 被外部杀死, 下次调用时会检测到 CDP 端口不可用, 自动使用同一 profile 重新启动 (自愈), 登录态仍然保留.

### 产物路径

所有产物写入系统临时目录:

```
tempfile.gettempdir()/access-web/<session-key>/
├── browser.json          # 元数据: pid, cdp_port, profile_dir, chromium_binary
├── profile/              # Chromium 用户数据目录 (cookie/登录态)
├── cookies.json          # stop 时持久化的 cookie
└── artifacts/
    ├── screenshots/
    ├── downloads/
    └── logs/
```

- **产物不写入 cwd**, 重启或系统清理临时目录后 profile 丢失, 登录态也随之丢失, 需重新登录.
- 不同 session-key 的目录完全隔离.

### 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `BROWSER_HEADED` | `true` 时使用有界面 Chromium, 适合需要人工登录/操作 MFA 的场景; `false`/`未设置` 时用 headless. | `false` |

## 快速开始

```python
from browser_agent import navigate, click_element, extract_text, screenshot

navigate("https://example.com")          # 打开页面
click_element("more information")        # 点击链接
text = extract_text("Example Domain")    # 提取文本
img = screenshot(path=None)              # 截图, img.image 是 PNG bytes
```

## 操作分层

本 skill 将浏览器能力分为三层, 从语义化高层操作到裸 CDP 逐渐递减:

### L1: 语义化操作

满足大多数网页自动化场景, 使用自然语言描述定位元素, 返回结构化结果.

```python
from browser_agent import (
    navigate, click_element, type_text, extract_text,
    screenshot, scroll, wait_for_element, get_page_structure,
)
```

| 函数 | 签名 | 返回 |
|---|---|---|
| `navigate` | `navigate(url, timeout=30.0)` | `NavigateResult(success, error, url)` |
| `click_element` | `click_element(description, timeout=30.0)` | `OperationResult(success, error)` |
| `type_text` | `type_text(description, text, timeout=30.0)` | `OperationResult(success, error)` |
| `extract_text` | `extract_text(description, timeout=30.0)` | `ExtractResult(success, error, text)` |
| `screenshot` | `screenshot(path=None, full_page=True, timeout=30.0)` | `ScreenshotResult(success, error, image/path)` |
| `scroll` | `scroll(direction, amount, timeout=30.0)` | `OperationResult(success, error)` |
| `wait_for_element` | `wait_for_element(description, state="visible", timeout=30.0)` | `OperationResult(success, error)` |
| `get_page_structure` | `get_page_structure(max_elements=500, timeout=30.0)` | `StructureResult(success, error, data)` |

### L2: Escape hatch

当 L1 语义化操作无法满足需求时使用, 谨慎处理.

```python
from browser_agent import evaluate_js, network_json
```

- `evaluate_js(script: str) -> EvalResult`  
  在当前页面执行任意 JavaScript, 不加沙箱, 返回 `EvalResult(result=..., error=...)`.

- `network_json(url, method="GET", body=None, headers=None) -> NetworkResult`  
  通过浏览器 `context.request.fetch` 发起 HTTP 请求, 自动携带当前 context 的 cookie, 可绕过 CORS 限制. `body` 为 `dict` 时自动序列化为 JSON 并设置 `Content-Type: application/json`. 返回 `NetworkResult(status, body, headers, error)`.

### L3: 裸 CDP

```python
from browser_agent import cdp_send
```

- `cdp_send(method: str, params: dict | None=None) -> CdpResult`  
  通过 `page.context.new_cdp_session(page).send(...)` 发送原始 Chrome DevTools Protocol 命令, 用于 browser 级操作 (性能指标/新 tab/网络劫持等). 返回 `CdpResult(result=..., error=...)`.

## 生命周期命令

```python
from browser_agent import (
    reset_session, stop_browser_session,
    cleanup_browser_session, status,
)
```

### reset_session

```python
reset_session() -> None
```

仅释放当前进程内的 `Session` 句柄, 不杀 Chromium, 不清理 profile. 下次操作会重建句柄并复用已有的浏览器会话. 用于在进程内重置连接而不丢失登录态.

### stop_browser_session

```python
stop_browser_session() -> None
```

根据 `browser.json` 中的 pid 杀掉 Chromium 进程 (Windows 用 `taskkill /F /PID`, POSIX 用 `SIGTERM`), **保留 profile 目录**. 用于临时关闭浏览器, 但希望保留登录态, 后续重新连接时无需重新登录.

### cleanup_browser_session

```python
cleanup_browser_session() -> None
```

先执行 `stop_browser_session`, 然后彻底删除 `tempfile.gettempdir()/access-web/<session-key>/` 目录 (profile、metadata、产物全部清理). 用于完全重置会话, 下次调用相当于全新启动.

### status

```python
status() -> StatusResult
```

返回当前会话状态, `alive` 字段通过 **pid + CDP 端口双检**判断浏览器是否真正可用. 不自动截图, 不调用 `bring_to_front`.

返回字段:

| 字段 | 说明 |
|---|---|
| `success` | 调用是否成功 |
| `alive` | 浏览器是否存活 (pid 与 CDP 端口均可用) |
| `url` | 当前页面 URL |
| `title` | 当前页面标题 |
| `pid` | Chromium 进程 pid |
| `headed` | 是否 headed 模式 (按 `BROWSER_HEADED` 环境变量) |
| `cdp_port` | CDP 调试端口 |
| `profile_dir` | profile 目录路径 |
| `pages` | 当前 context 中 page 数量 |

## cookies

```python
from browser_agent import cookies
cookies() -> CookiesResult
```

返回当前浏览器 context 中的所有 cookie.

## 约束

- 默认 30 秒超时, 参数可覆盖.
- 失败返回 `success=False` + `error`, 不抛异常.
- 仅依赖 `playwright` (sync API). Python >= 3.9.
- 测试: `cd browse && PYTHONPATH=. pytest tests/ -q` (需先 `python -m playwright install chromium`).

## 范围外 (P2 / 不做)

以下功能本次不做, 后续可能单独规划:

- Grafana/Loki 专用查询辅助函数、批量 trace 查询模板.
- 跨操作系统重启保持登录态 (profile 在临时目录, 重启后丢失).
- `bring_to_front` / 自动截图.
- `page_text` / `selector_text` 等专用文本提取 (可用 `evaluate_js` 替代).
- 独立的 `doctor` 命令.
- `cleanup --older-than` 等自动清理策略.

## 完成标准

- L1 操作优先使用自然语言描述; 失败时检查 `result.success` 与 `result.error`.
- 需要登录时, headed 模式弹窗由人类完成; 登录态在同一会话内自动复用.
- 完全重置会话调用 `cleanup_browser_session`, 仅关闭浏览器但保留登录态调用 `stop_browser_session`.
