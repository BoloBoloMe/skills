## 执行(Execution)

- [x] 已实现

## 要构建什么

浏览器生命周期管理和导航操作: 定义 `OperationResult` 数据类型, 实现 `Browser` 上下文 (启动/停止 headless Chromium), 实现 `navigate(url)` 操作. 这是整个 skill 的最薄端到端切片 — 证明 browser 能启动, 执行一个操作, 返回结构化结果, 然后安全关闭.

此切片适合 AFK: 所有设计决策已确认, 无需产品/API 决策, 仅涉及基础设施搭建.

## 相关决策

D001, D003, D004, D005, D006, D007, D008, D009, D011, D016

## 允许范围

- `browser_agent/result.py` — OperationResult 及其子类
- `browser_agent/browser.py` — Browser 类, 封装 Playwright sync_api 启动/停止/context 管理
- `browser_agent/operations.py` — 仅 `navigate(url, timeout=30.0)` 函数
- `pyproject.toml` — 依赖声明 (`playwright`)
- `tests/test_navigate.py` — navigate 操作测试

## 禁止范围

- 不实现 navigate 以外的任何操作 (click, type, extract 等)
- 不实现定位器 `_locator.py`
- 不编写集成测试 (留给 ISSUE-04)

## 验证入口

```bash
pytest tests/test_navigate.py -v
```

测试至少覆盖:
- 启动 browser, navigate 到 `https://example.com`, 返回 `OperationResult(success=True)`, 停止 browser
- navigate 到无效 URL, 返回 `OperationResult(success=False)` 且 error 非空
- 超时场景: navigate 到慢速页面, timeout=1s, 返回 success=False

## 风险提示

- Playwright 首次运行时需下载 Chromium 浏览器二进制 (~150MB), 网络环境可能影响
- 部分 CI 环境需额外安装系统依赖 (libgbm, libnss3 等), 需在文档中说明

## 停止条件

- 如果 Playwright sync_api 的行为与 D009 假设冲突 (如某些必需功能仅 async API 提供)
- 如果需要修改 D001-D010 中任何 `必须遵守` 的决策

## 适合 AFK 的原因

所有架构决策 (引擎选择, 同步 API, 返回类型, 超时策略) 已在 DECISIONS.md 中明确. 本切片仅实现已决策的基础设施, 不涉及新的产品/API 取舍.

## 验收标准

- [ ] `from browser_agent import navigate` 可导入
- [ ] `navigate("https://example.com")` 返回 `OperationResult(success=True, url="https://example.com")`
- [ ] `navigate("not-a-valid-url")` 返回 `OperationResult(success=False)`
- [ ] Browser 在操作完成后正确关闭, 无残留进程

## 被阻塞于

无 - 可以立即开始
