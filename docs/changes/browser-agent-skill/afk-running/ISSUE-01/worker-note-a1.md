# ISSUE-01 Worker 实现记录

## 改动入口

新建独立 Python package `browser-agent/`, 位于 repo 根目录.

### 文件清单

| 文件 | 用途 |
|------|------|
| `browser-agent/pyproject.toml` | 项目元数据, `requires-python >= 3.9`, 依赖 playwright, test extra 含 pytest |
| `browser-agent/browser_agent/__init__.py` | 公开导出: navigate, OperationResult, NavigateResult |
| `browser-agent/browser_agent/result.py` | OperationResult (基类) 和 NavigateResult (子类), dataclass, success/error/url 字段 |
| `browser-agent/browser_agent/browser.py` | Browser 类: 封装 sync_playwright, 启动/停止 Chromium, context 管理, context manager 协议 |
| `browser-agent/browser_agent/operations.py` | navigate(url, timeout=30.0) 函数, 每次调用创建/销毁 Browser 实例, 返回 NavigateResult |
| `browser-agent/tests/test_navigate.py` | 3 个测试用例 |

### 设计要点

- Browser 每次实例化创建独立的 sync_playwright 连接 + Chromium 实例 (D011)
- 默认 headless, `BROWSER_HEADED=true` 切换 headed (D004)
- navigate 在 finally 块中停止 Browser, 确保异常/成功路径均清理
- 所有 Playwright 异常被捕获, 转为 NavigateResult(success=False, error=...), 符合 D008
- page.goto 的 Playwright 超时单位为 ms, 代码内部 `timeout * 1000` 转换

## 验证入口及结果

### 测试命令

```bash
cd browser-agent
PYTHONPATH=. python3 -m pytest tests/test_navigate.py -v
```

### 测试结果

```
3 passed in 2.37s
```

- `test_navigate_returns_navigate_result` — 导航到 example.com, 返回 NavigateResult(success=True, url="https://example.com")
- `test_navigate_invalid_url_returns_failure` — 导航到无效 URL, 返回 NavigateResult(success=False, error 非空)
- `test_navigate_timeout_returns_failure` — 导航到 httpbin.org/delay/10, timeout=1.0s, 返回 NavigateResult(success=False)

### 手动验收

```python
from browser_agent import navigate
print(navigate('https://example.com'))
# NavigateResult(success=True, error=None, url='https://example.com')
```

### 残留进程检查

无 Playwright Chromium 残留进程 (Steam/VS Code Chromium 进程不相关).

## 风险/阻塞

- 无阻塞.
- Playwright 系统依赖 (libgbm, libnss3 等) 在 Bazzite (Fedora Kinoite) 上已预装, 无需额外 install-deps.
- 其他环境可能需要 `playwright install-deps chromium` 作为前置步骤 (已在 Contract 未确认假设中说明).

## 决策偏离说明

无偏离. 所有实现严格遵循 CONTRACT.md 和 DECISIONS.md 中 ISUUE-01 相关决策 (D001, D003, D004, D005, D006, D007, D008, D009, D011, D016).

## TDD 证据

- RED: tests/test_navigate.py 先于实现编写, 首次运行因 ModuleNotFoundError 失败
- GREEN: 逐文件实现 browser_agent 各模块, 3 个测试全部通过
- 未执行 REFACTOR: 当前代码量小, 无重复或需要抽象的部分

## 测试策略说明

- 使用真实 httpbin.org/delay/10 测试超时场景 (Contract 允许集成测试使用稳定公开页面)
- example.com 测试导航成功场景
- 无效 URL 字符串测试错误返回路径

## 相关决策影响

无新增决策, 无需要更新的决策.