# Browser Agent Skill Contract

## 背景

为 AI agent 提供一个可通过 Python 函数调用操作浏览器的 skill. Agent 不需要理解 DOM/CSS selector/XPATH, 只需发出语义指令 (如"点击登录按钮"), skill 内部负责定位和交互. 底层使用 Playwright sync API.

## 目标

- 一个可安装的 Python package `browser-agent`, 暴露 8 个语义化浏览器操作函数
- 每个操作返回结构化 `OperationResult`, agent 可据此决策下一步
- 通过 pytest 测试套件验证全部操作在 headless Chromium 下正确执行

## 非目标

- 不做浏览器会话持久化 (cookies/sessions 不跨调用保留)
- 不做多标签页/多窗口管理
- 不做网络拦截/代理/请求修改
- 不做可视化录制/回放
- 不做 asyncio 支持

## 行为边界

- 每次 skill 调用创建独立 Browser 实例和 browser context, 调用结束后销毁. Browser 不为单例, 不跨调用共享.
- 默认 headless, 环境变量 `BROWSER_HEADED=true` 切换 headed
- 每操作默认超时 30s, 可通过参数覆盖. 超时返回 success=False 且 error 说明原因.
- 操作失败返回 `OperationResult(success=False, error=...)`, 不抛异常. 仅编程错误 (非法参数类型) 可抛 TypeError/ValueError.
- 元素定位使用三级回退: accessible name → 文本内容 → CSS selector. 多元素匹配时选第一个命中; 全部未命中返回 success=False.
- 仅支持同步调用
- `scroll(direction, amount)`: direction ∈ {"up", "down"}, amount 为像素值. 使用 window.scrollBy 实现.
- `screenshot(path=None, full_page=True)`: path 为 None 返回 bytes; 非 None 写入文件. 格式 PNG.
- `get_page_structure(max_elements=500)`: 返回 dict {url, title, elements, truncated}. 元素取自可访问性树, 深度 ≤ 4.
- `wait_for_element(description, state="visible")`: state ∈ {"attached", "visible", "hidden"}, 默认 visible.

## 决策引用

完整决策账本: `DECISIONS.md`

| ID | 约束摘要 |
|----|---------|
| D001 | Playwright 作为唯一浏览器引擎 |
| D002 | 对外暴露语义化操作, 不暴露原始 Playwright API |
| D003 | 操作原子化, 返回结构化 OperationResult |
| D004 | 默认 headless, BROWSER_HEADED 切换 |
| D005 | 不跨调用持久化会话 |
| D006 | 每操作默认 30s 超时, 可覆盖 |
| D007 | 首批 8 个操作: navigate, click_element, type_text, extract_text, screenshot, scroll, wait_for_element, get_page_structure |
| D008 | 操作失败不抛异常, 走 success=False |
| D009 | 仅 sync API, 不用 asyncio |
| D010 | 三级回退定位策略 |
| D011 | 并发调用时每次创建独立 Browser 实例 |
| D012 | scroll 语义: direction ∈ {up,down}, amount 像素值 |
| D013 | screenshot 语义: path 可选, 固定 PNG, full_page 控制截取范围 |
| D014 | get_page_structure 返回 dict, max_elements 截断, depth ≤ 4 |
| D015 | wait_for_element 语义: state ∈ {attached,visible,hidden} |
| D016 | requires-python >= 3.9 |

## 未确认假设

- 假设: Agent 调用方运行环境已安装 Chromium 浏览器
  影响: 如果未安装, `playwright install chromium` 需要作为前置步骤; 不属于本 skill 职责
  验证方式: 在 CI 环境或 Dockerfile 中预装; 文档说明前置依赖

- 假设: 目标网页不使用严格的反自动化检测
  影响: 部分网站可能检测到 Playwright 自动化特征并拒绝服务; 本 skill 不内置反检测
  验证方式: 测试时使用公开可访问的测试站点 (如 example.com, httpbin.org)

- 假设: 运行环境为 Linux x86_64, 且已安装 Playwright 所需的系统依赖 (libgbm, libnss3 等)
  影响: macOS/Windows 或缺少系统依赖时 `playwright` 无法启动 Chromium
  验证方式: CI 中预装 `playwright install-deps chromium`; 在 README 中列出系统依赖

- 假设: 运行环境有网络访问能力
  影响: 离线环境下 navigate 和所有网络相关操作均返回 success=False
  验证方式: 测试不假设网络可达性; 使用 Playwright route mock 做离线测试

## 代码边界提示

- 新建独立 Python package, 不修改 skills 仓库现有内容
- package 结构: 公开 API 层 (`operations.py`), 浏览器管理层 (`browser.py`), 定位策略层 (`_locator.py`), 可访问性树解析 (`_structure.py`), 结果类型层 (`result.py`)
- 依赖: 仅 `playwright`, 不引入 requests/httpx 等额外 HTTP 库. 测试可引入 `pytest` (test extra).
- python 版本: `requires-python >= 3.9` (见 D016)

## 允许范围

- 新建 package 内所有模块和测试文件
- `pyproject.toml` 中的依赖声明
- package 内的文档字符串和类型标注

## 禁止范围

- 不修改 skills 仓库中任何现有 `.md` 或 `.py` 文件 (但不包括 feature 目录 `docs/changes/browser-agent-skill/` 内的 DECISIONS.md — worker 需按 decision-ledger 规则更新实际影响)
- 不依赖 `playwright` 以外的第三方浏览器/HTTP 库
- 不暴露 Playwright 原生对象 (Page, Browser, Locator, BrowserContext) 到公开 API

## 验证入口

- 测试入口: `pytest tests/` — 测试套件启动 headless Chromium, 对本地测试页面或公开站点执行所有 8 个操作, 验证 OperationResult 正确性
- 手动验证: `python -c "from browser_agent import navigate; print(navigate('https://example.com'))"` 应返回 `OperationResult(success=True, url='https://example.com')`

## 风险和停止条件

- 需要产品/API/架构决策时停止: 若需新增操作类型或改变公共 API 签名, 需退回 `grill-with-docs`
- 需要扩大范围时停止: 若发现必须引入 asyncio, 会话持久化或多标签页才能满足 agent 使用场景
- 发现现有行为与 contract 冲突时停止: 若 Playwright 行为与三级回退定位策略预期不符
- CSS selector 兜底误匹配风险: 若 CSS selector 级频繁匹配到错误元素, 停止并上报, 需要新增消歧决策.
- 浏览器进程泄漏风险: 超时或异常可能绕过 context cleanup. 实现需确保 `__exit__` / `atexit` 清理; worker 发现无法保证时停止.
- get_page_structure 体积风险: 若实际测试发现 500 元素截断后仍过大 (>200KB), 停止并调整 D014 参数.

## 下游 issue 约束

- issue 必须按垂直切片拆分, 每条切片端到端可验证
- 切片顺序: 基础设施 (browser 启动/结果类型) → 单个操作 → 组合测试
- 每个 issue 的验收标准必须包含具体可执行的 pytest 命令或可观察行为
- 禁止在 issue 中写逐文件实现计划
- 测试策略: 优先使用 Playwright route mock (`page.route()`) 模拟页面, 避免依赖外部站点. 集成测试可用 example.com 等稳定公开页面.
