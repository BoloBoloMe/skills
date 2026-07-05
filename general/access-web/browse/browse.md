# 交互浏览

基于 Playwright 驱动 Chromium. 每次对话自动获得独立浏览器会话, 操作间共享页面状态 (URL, cookies, DOM). 8 个操作, 无需初始化, 首次调用懒启动, 进程结束自动关闭.

## 快速开始

```python
from browser_agent import navigate, click_element, extract_text, screenshot

navigate("https://example.com")          # 打开页面
click_element("more information")        # 点击链接
text = extract_text("Example Domain")    # 提取文本
img = screenshot(path=None)              # 截图, img.image 是 PNG bytes
```

## 操作

```python
from browser_agent import navigate, click_element, type_text, extract_text
from browser_agent import screenshot, scroll, wait_for_element, get_page_structure
```

### navigate

```python
navigate(url: str, timeout: float = 30.0) -> NavigateResult
# NavigateResult: success (bool), error (str|None), url (str|None)
```

### click_element

```python
click_element(description: str, timeout: float = 30.0) -> OperationResult
# description: 自然语言描述, 如 "登录按钮". 定位: accessible name → 文本 → CSS.
# OperationResult: success, error
```

### type_text

```python
type_text(description: str, text: str, timeout: float = 30.0) -> OperationResult
```

### extract_text

```python
extract_text(description: str, timeout: float = 30.0) -> ExtractResult
# ExtractResult: success, error, text (str|None)
```

### screenshot

```python
screenshot(path: str | None = None, full_page: bool = True, timeout: float = 30.0) -> ScreenshotResult
# path=None → PNG bytes 在 result.image; path 非空 → 写入文件
```

### scroll

```python
scroll(direction: str, amount: int, timeout: float = 30.0) -> OperationResult
# direction: "up" | "down"
```

### wait_for_element

```python
wait_for_element(description: str, state: str = "visible", timeout: float = 30.0) -> OperationResult
# state: "attached" | "visible" | "hidden"
```

### get_page_structure

```python
get_page_structure(max_elements: int = 500, timeout: float = 30.0) -> StructureResult
# StructureResult: success, error, data (dict: {url, title, elements, truncated})
```

## 约束

- 默认 30 秒超时, 参数可覆盖.
- 失败返回 `success=False` + `error`, 不抛异常.
- 仅依赖 `playwright` (sync API). Python >= 3.9.
- 测试: `cd browse && PYTHONPATH=. pytest tests/ -q`.

## 登录态

遇到登录页: 浏览器 headed 模式弹窗, 人类登录后 agent 继续. session 在对话内保持.

完成标准: 每次操作检查 `success`. 失败时读 `error`, 判断元素未找到/超时/Browser 崩溃, 相应调整.
