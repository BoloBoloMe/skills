# 交互浏览

基于 Playwright 驱动 Chromium 的语义化浏览器操作. 浏览器以**脱离式子进程**启动, 绑定当前 pi 会话 (由 cwd 派生的 session-key 决定). 首次调用时懒启动, 工具进程退出后 Chromium 仍然存活, 同一会话内的后续工具调用自动复用同一浏览器, profile 与登录态.

**关键**: 同一工作目录共享同一个浏览器会话; 不同工作目录相互隔离. 整个会话只有一个浏览器窗口/一个默认标签页, `navigate` 在当前标签页跳转. 只有需要同时对比两个不同页面时才开新标签 (极少). 默认使用 `headless` 模式; 设置环境变量 `BROWSER_HEADED=true` 可切换到 headed 模式, 登录弹窗由人类操作.

## 生命周期与产物

### 绑定 pi 会话

- `session-key = sha256(canonicalize(cwd))[:16]`, 基于当前工作目录计算, 同 cwd 共享, 不同 cwd 隔离.
- 首次调用任意操作时, 以 `subprocess.Popen` 脱离式启动 Chromium (`--user-data-dir` + `--remote-debugging-port`), 并写入 `browser.json` 元数据.
- 之后无论工具进程是否退出, Chromium 继续在后台运行. 新的工具进程通过 CDP (`connect_over_cdp`) 连接并复用.
- 登录态, cookie, localStorage 等保存在 profile 中, 会话内保持, 不必重复登录.
- 若 Chromium 被外部杀死, 下次调用时会检测到 CDP 端口不可用, 自动使用同一 profile 重新启动 (自愈), 登录态仍然保留.

### 产物路径

所有产物写入系统临时目录:

```
tempfile.gettempdir()/access-web/
├── <session-key>/          # session 目录 (结构见下)
└── <session-key>.lock      # 启动/停止/清理互斥锁 (POSIX flock), 与 session 目录平级

<session-key>/:
├── browser.json          # 元数据: pid, cdp_port, profile_dir, chromium_binary
├── profile/              # Chromium 用户数据目录 (cookie/登录态)
├── cookies.json          # stop 时持久化的 cookie
└── artifacts/
    ├── screenshots/
    ├── downloads/
    └── logs/
```

- session 启动时自动创建 `artifacts/screenshots`, `artifacts/downloads`, `artifacts/logs`; POSIX 下 session 根目录权限设为 700 (含 cookie/登录态), Windows 跳过.
- **产物不写入 cwd**, 重启或系统清理临时目录后 profile 丢失, 登录态也随之丢失, 需重新登录.
- 不同 session-key 的目录完全隔离.

### 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `BROWSER_HEADED` | `true` 时使用有界面 Chromium, 适合需要人工登录/操作 MFA 的场景; `false`/`未设置` 时用 headless. | `false` |

## 运行方式

代码在仓库 `general/access-web/browse/` 目录, 是独立 uv 项目 (仅依赖 `playwright`, Python >= 3.9). 命令在 `browse/` 目录下执行 (相对仓库根). 依赖与浏览器安装:

```bash
cd browse/
uv sync                                        # 安装 Python 依赖
uv run python -m playwright install chromium   # 仅首次: 安装 Chromium
```

调用形态: 在 `browse/` 下用 `uv run python` 内联执行, 或写临时脚本后 `uv run python <脚本>`:

```bash
uv run python -c "
from browser_agent import navigate, extract_text
r = navigate('https://example.com')
print(r.success, r.url, r.error)
"
```

**注意**: session-key 由执行进程的 cwd 派生. 在 `browse/` 下运行时浏览器会话绑定 `browse/` 目录; 需要绑定其他工作目录时, 切到该目录后用 `uv run --project <browse/ 绝对路径> python ...` 调用.

## 快速开始

```python
from browser_agent import navigate, click_element, extract_text, screenshot

navigate("https://example.com")          # 打开页面
click_element("more information")        # 点击链接
text = extract_text("Example Domain")    # 提取文本
img = screenshot(path=None)              # 截图并落盘 artifacts/screenshots/, img.image 是 PNG bytes, img.path 是路径
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
| `navigate` | `navigate(url, timeout=30.0)` | `NavigateResult(success, error, url)`, url 为落地后真实 URL |
| `click_element` | `click_element(description, timeout=30.0)` | `OperationResult(success, error)` |
| `type_text` | `type_text(description, text, timeout=30.0)` | `OperationResult(success, error)` |
| `extract_text` | `extract_text(description, timeout=30.0)` | `ExtractResult(success, error, text)` |
| `screenshot` | `screenshot(path=None, full_page=True, timeout=30.0)` | `ScreenshotResult(success, error, image/path)`, path=None 时自动落盘 artifacts/screenshots/ |
| `scroll` | `scroll(direction, amount)` | `OperationResult(success, error)` |
| `wait_for_element` | `wait_for_element(description, state="visible", timeout=30.0)` | `OperationResult(success, error)` |
| `get_page_structure` | `get_page_structure(max_elements=500)` | `StructureResult(success, error, data)` |

### L2: Escape hatch

当 L1 语义化操作无法满足需求时使用, 谨慎处理.

```python
from browser_agent import evaluate_js, network_json
```

- `evaluate_js(script: str) -> EvalResult`  
  在当前页面执行任意 JavaScript, 不加沙箱, 返回 `EvalResult(result=..., error=...)`.

- `network_json(url, method="GET", body=None, headers=None) -> NetworkResult`  
  通过浏览器 `context.request.fetch` 发起 HTTP 请求, 自动携带当前 context 的 cookie, 可绕过 CORS 限制. `body` 为 `dict` 时自动序列化为 JSON, 若 headers 中尚无 Content-Type (大小写不敏感判断) 则自动补 `application/json`; `body` 为 `str` 时原样发送. 返回 `NetworkResult(status, body, headers, error)`.

### L3: 裸 CDP

```python
from browser_agent import cdp_send
```

- `cdp_send(method: str, params: dict | None=None) -> CdpResult`  
  通过 `page.context.new_cdp_session(page).send(...)` 发送原始 Chrome DevTools Protocol 命令, 用于 browser 级操作 (性能指标/新 tab/网络劫持等). 返回 `CdpResult(result=..., error=...)`; CDP session 用完即 detach, 命令成功但 detach 失败时保持 `success=True` 且 `error=None`, 问题记入 `warning` 字段 (仅此字段承载非致命善后告警).

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

先持久化当前 cookie 到 `cookies.json`, 优先经 CDP 优雅关闭让 profile 落盘, 再按 `browser.json` 中的 pid 杀掉 Chromium 进程 (Windows 用 `taskkill /F /PID`, POSIX 先 `SIGTERM` 等待退出, 超时再 `SIGKILL`), **保留 profile 目录**. stop 只杀进程, 自身不会隐式重启浏览器; 用于临时关闭浏览器但保留登录态, 之后调用任意操作时按同一 profile 重新启动, 无需重新登录.

### cleanup_browser_session

```python
cleanup_browser_session() -> None
```

先执行 `stop_browser_session`, 然后彻底删除 `tempfile.gettempdir()/access-web/<session-key>/` 目录 (profile, metadata, 产物全部清理); 平级的 `<session-key>.lock` 锁文件不删, 删除会让并发 cleanup+start 各持一把新锁, 双启同一 profile. 用于完全重置会话, 下次调用相当于全新启动.

### status

```python
status() -> StatusResult
```

- `status()` 的 `alive` 字段通过 **pid + CDP 端口双检**判断浏览器是否真正可用 (见 `probe`); 不启动浏览器, 不自动截图.

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

## 只读附加 (attach)

观察一个已运行的会话而不启动浏览器. 供展示类工具 (如 adaptive-presentation)
绑定任意 session 目录做只读观察; 全部函数无副作用: 不启动 Chromium,
不写 metadata, 不创建目录.

```python
from browser_agent import probe, attached_context, SessionProbe
```

- `probe(cwd: str | None = None) -> SessionProbe`  
  pid + CDP 端口双检存活, 返回 `SessionProbe(alive, pid, cdp_port, profile_dir)`;
  无 metadata 或 metadata 畸形时 `alive=False` 且字段为 None/原样摘录.
  `cwd` 用于绑定非当前目录的会话 (如展示会话的 session-dir).

- `attached_context(cwd: str | None = None) -> 上下文管理器`  
  只读附加到存活会话的默认 context; 会话未存活或无可用 context 时 yield `None`.
  CDP 连接失败抛异常, 由调用方决定语义. 内部遵守 "CDP 连接不调用
  `browser.close()`" 纪律 (close 会杀远端 Chromium), 仅释放本地句柄.

注意: 若当前进程已持有活跃 Session (本进程 operations 已连接浏览器),
优先复用 Session 页面 (见 `status()` 实现), 避免嵌套 sync_playwright 事件循环.

## 绑定非 cwd 会话目录

公开操作默认绑定进程 cwd 派生的会话. 需要绑定其他目录 (如展示会话的
session-dir) 时, 使用 `get_session(cwd=...)`:

```python
from browser_agent import get_session

page = get_session(cwd="/tmp/pi-presentation-xxx").page
```

`cwd` 参数仅在进程内首次调用 (单例尚未创建) 时生效; CLI 每进程一次调用
无坑, 库内换会话需先 `reset_session()`. 对会话做只读观察用上方的
`probe` / `attached_context`, 不要经 `get_session` (会隐式启动浏览器).

## 约束

- 带 `timeout` 参数的操作默认 30 秒, 参数可覆盖 (`scroll`, `get_page_structure` 无此参数).
- 所有公开操作不抛异常: 失败, 参数非法 (如 `scroll` 的 direction 非 `up`/`down`, `wait_for_element` 的 state 非 `attached`/`visible`/`hidden`, description 为空) 均返回 `success=False` + `error`.
- 仅依赖 `playwright` (sync API). Python >= 3.9.
- 测试: `uv run --extra test python -m pytest tests/ -q` (pytest 在 optional-dependencies 的 `test` extra 中, 需先装 Chromium).

可用能力以上方函数表为准.

## 完成标准

- L1 操作优先使用自然语言描述; 失败时检查 `result.success` 与 `result.error`.
- 需要登录时, headed 模式弹窗由人类完成; 登录态在同一会话内自动复用.
- 完全重置会话调用 `cleanup_browser_session`, 仅关闭浏览器但保留登录态调用 `stop_browser_session`.
