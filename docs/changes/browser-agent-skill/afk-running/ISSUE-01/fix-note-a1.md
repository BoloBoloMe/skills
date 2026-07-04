# ISSUE-01 Fix Note (Attempt 1)

## 修复项

### R1: 移除未使用的 `field` import

- 文件: `browser-agent/browser_agent/result.py` L3
- 修改: `from dataclasses import dataclass, field` → `from dataclasses import dataclass`
- 验证: grep 确认 `field` 在 `result.py` 中无引用; 测试全部通过

### R2: 超时测试改用 `page.route()` mock

- 文件: `browser-agent/tests/test_navigate.py`
- 修改: `test_navigate_timeout_returns_failure` 不再依赖 `httpbin.org/delay/10`
- 实现: 通过 `patch.object(Browser, "start")` 在 `start()` 后注入 `page.route("**/*", lambda route: None)`, route handler 不做 fulfill/abort/continue, 使请求挂起, 触发 `page.goto` 超时
- 验证: 测试通过, 返回 `success=False, error` 非空; 无外部网络依赖

### R3: 补充 browser 启动失败场景测试

- 文件: `browser-agent/tests/test_navigate.py`
- 新增: `test_navigate_browser_start_failure`
- 实现: `patch.object(Browser, "start", side_effect=RuntimeError("chromium not found"))`
- 验证: `navigate()` 返回 `success=False`, `error` 含 `"chromium not found"`, 不抛异常

### R4: `pyproject.toml` 添加 `[build-system]`

- 文件: `browser-agent/pyproject.toml`
- 新增:
  ```toml
  [build-system]
  requires = ["setuptools"]
  build-backend = "setuptools.build_meta"
  ```
- 验证: `pyproject.toml` 语法有效, pytest 正常读取 config

## 验证结果

```bash
cd browser-agent && PYTHONPATH=. /usr/bin/python3 -m pytest tests/test_navigate.py -v
```

```
4 passed in 2.40s
```

- `test_navigate_returns_navigate_result` PASSED
- `test_navigate_invalid_url_returns_failure` PASSED
- `test_navigate_timeout_returns_failure` PASSED (mock)
- `test_navigate_browser_start_failure` PASSED (new)

残留 chromium 进程: 无

## 未修项 (不在本次范围)

- `NavigateResult.url` 语义 (deferred): 成功路径仍返回输入 url, 非最终 url
- `browser.py` stop() 异常静默 (deferred)
- 其余 recommended 发现项均已修复

## 风险/阻塞

无. 4 项修复全部通过验证, 无范围扩大, 未引入新依赖.