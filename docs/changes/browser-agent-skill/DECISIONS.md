# 决策账本: browser-agent-skill

## D001: 使用 Playwright 作为浏览器自动化引擎

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 以 `playwright` Python 库作为浏览器自动化底层, 不自己封装 CDP/WebDriver.
- 理由: Playwright 是 Python 生态中最成熟的浏览器自动化库, 原生支持 iframe/shadow DOM/网络拦截, 多浏览器 (Chromium/Firefox/WebKit), 维护活跃. 相比 Selenium 有更现代的 API 和更好的自动等待机制. 相比直接使用 CDP 省去大量协议层工作.
- 预计影响: `pyproject.toml` 新增 `playwright` 依赖; 所有 browser 操作实现直接或间接依赖 `playwright.sync_api`.
- 实际影响: `pyproject.toml` 声明 `dependencies = ["playwright"]`; `browser_agent/browser.py` 导入 `sync_playwright` / `Browser` / `BrowserContext` / `Page` / `Playwright`. (ISSUE-01 a1, verified)
- 相关 issue: ISSUE-01

## D002: Skill 对外暴露语义化高层操作, 不暴露原始 Playwright API

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: Skill 的公开接口是面向 agent 的语义操作 (如 `navigate`, `click_element`, `extract_text`), 而非 Playwright 原始 locator/page API. Agent 调用方不需要理解 CSS selector/XPATH 细节, Skill 内部负责将语义描述转为定位策略.
- 理由: Agent 的决策空间已经很大, 暴露原始定位器 API 会增加 agent 的认知负荷和出错概率. 语义化接口让 agent 以 "点击标有 '登录' 的按钮" 的方式思考, 而非 "用 CSS selector `.btn-login` 定位".
- 预计影响: 公开模块 (`browser_agent/__init__.py` 或 `browser_agent/operations.py`) 的函数签名使用语义参数; 内部 `_locator.py` 负责语义到定位器的转换.
- 实际影响: `browser_agent/operations.py` 新增 `click_element(description, timeout=30.0)` 和 `type_text(description, text, timeout=30.0)`. `browser_agent/_locator.py` 实现 `locate(page, description)` 三级回退定位. 公开 API 仅接收自然语言描述, 不暴露 Locator/Page. (ISSUE-02 a1, verified)
- 相关 issue: ISSUE-02

## D003: 每个操作原子化, 返回结构化结果

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 每个操作调用是原子的 (单次 browser interaction), 返回值是结构化 dataclass, 包含 `success: bool`, `error: Optional[str]`, 以及操作特定的 result 字段. 不依赖异常做正常流程控制.
- 理由: Agent 需要精确判断每个操作的结果来决策下一步. 结构化返回值比异常更容易被 agent 消费和推理. 原子化保证操作可组合, agent 可以自由编排操作序列.
- 预计影响: `browser_agent/result.py` 定义 `OperationResult` 基类和子类; 所有 operation 函数返回对应 result 类型.
- 实际影响: `browser_agent/result.py` 定义 `OperationResult(success, error)` 基类 + `NavigateResult(success, error, url)` 子类. `browser_agent/operations.py` 中 `navigate()` 返回 `NavigateResult`. (ISSUE-01 a1, verified)
- 相关 issue: ISSUE-01, ISSUE-02

## D004: 默认 headless 模式, 通过环境变量 `BROWSER_HEADED=true` 切换

- 状态: 当前有效
- 约束性: 可调整
- 决策: 默认以 headless 模式启动浏览器. 设置环境变量 `BROWSER_HEADED=true` 可切换到 headed 模式用于调试.
- 理由: Agent 运行环境通常是无人值守的服务端, headless 是合理默认. 环境变量是最简单的调试开关, 不引入额外配置复杂度.
- 预计影响: `browser_agent/browser.py` 中 `launch()` 调用读取 `BROWSER_HEADED` 环境变量.
- 实际影响: `browser_agent/browser.py` L27 `headless = os.environ.get("BROWSER_HEADED", "").lower() != "true"`. (ISSUE-01 a1, verified)
- 相关 issue: ISSUE-01

## D005: 每次 skill 调用创建新浏览器上下文, 不跨调用持久化会话

- 状态: 当前有效
- 约束性: 可调整
- 决策: 每次 agent 调用 skill 时创建新的 Playwright browser context, 调用结束后关闭. 不提供跨调用的 cookie/session 持久化.
- 理由: 会话持久化引入状态管理复杂性 (存储, 过期, 安全). 对于首个版本, 保持无状态设计降低复杂度. 后续如有需求可通过决策变更追加.
- 预计影响: `browser_agent/browser.py` 中 context 生命周期绑定到单次 skill 调用; 不引入 session store.
- 实际影响: `browser_agent/operations.py` 中 `navigate()` 每次创建 `Browser()` → 调用后 `finally: browser.stop()` 销毁. `browser_agent/browser.py` 无 session store. (ISSUE-01 a1, verified)
- 相关 issue: ISSUE-01

## D006: 每操作超时 30s, 可通过参数覆盖

- 状态: 当前有效
- 约束性: 必须遵守
- 约束说明: 每个操作必须有超时机制, 这是必须遵守的. 默认值 30s 和 `timeout` 参数属于可调整的实现细节, worker 可在不改变行为契约的前提下调整默认值.
- 决策: 每个操作有默认 30 秒超时, 操作函数接受 `timeout: float = 30.0` 参数. 超时返回 `success=False` 且 error 字段说明超时原因.
- 理由: Agent 的执行必须可预测地终止. 30 秒对大多数 web 操作足够, 同时防止无限等待. 参数化允许调用方针对慢速页面调整.
- 预计影响: 所有 operation 函数接受 `timeout` 参数; `browser_agent/browser.py` 中设置 Playwright 默认超时.
- 实际影响: `browser_agent/operations.py` `navigate(url, timeout=30.0)` → `page.goto(url, timeout=timeout * 1000)`. Playwright 默认超时未在 browser.py 全局设置. (ISSUE-01 a1, verified; 后续 issue 继续覆盖)
- 相关 issue: ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04

## D007: 首批支持的操作集合

- 状态: 当前有效
- 约束性: 可调整
- 决策: 首批 8 个操作: `navigate(url)`, `click_element(description)`, `type_text(description, text)`, `extract_text(description)`, `screenshot()`, `scroll(direction)`, `wait_for_element(description)`, `get_page_structure()`.
- 理由: 覆盖 agent 浏览网页的基本需求: 导航, 交互 (点击/输入), 信息提取, 视觉反馈, 等待, 页面结构理解. `get_page_structure()` 返回可访问性树摘要, 帮助 agent 理解页面布局.
- 预计影响: `browser_agent/operations/` 下对应 8 个模块或一个 `operations.py` 中的 8 个函数.
- 实际影响: `browser_agent/operations.py` 目前仅 `navigate()` 函数. 其余 7 个操作待 ISSUE-02/03/04 实现. (ISSUE-01 a1, partial)
- 相关 issue: ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04

## D008: 操作失败不抛异常, 统一走 OperationResult.success=False

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 所有操作在失败时返回 `OperationResult(success=False, error="原因")`, 不抛出异常. 只有编程错误 (如传入非法参数类型) 才允许抛 `TypeError`/`ValueError`.
- 理由: Agent 需要统一的错误处理路径. 异常会打断 agent 的控制流, 而结构化错误可以内联到 agent 的推理链中.
- 预计影响: 所有 operation 函数用 try/except 包裹 Playwright 调用; `browser_agent/errors.py` 定义错误消息常量.
- 实际影响: `browser_agent/operations.py` `navigate()` 用 `try/except Exception` 包裹全部 Playwright 调用. 测试验证 browser 启动失败 (RuntimeError) 被捕获, 返回 success=False. `browser_agent/errors.py` 未创建. (ISSUE-01 a1, verified)
- 相关 issue: ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04

## D009: 使用 Playwright sync API, 不引入 asyncio

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 使用 `playwright.sync_api` 而非 `playwright.async_api`. Skill 的函数签名保持同步.
- 理由: Agent 调用链通常是同步的, 引入 asyncio 会强制调用方也使用 async/await, 增加集成复杂度. Playwright sync API 功能与 async API 等价.
- 预计影响: `browser_agent/browser.py` 导入 `sync_playwright`; 所有操作函数定义为同步函数.
- 实际影响: `browser_agent/browser.py` 导入 `playwright.sync_api` 全部符号. `browser_agent/operations.py` `navigate()` 为同步函数. (ISSUE-01 a1, verified)
- 相关 issue: ISSUE-01, ISSUE-02

## D010: 元素定位策略: 优先 accessible name, 其次文本内容, 最后 CSS selector

- 状态: 当前有效
- 约束性: 可调整
- 决策: Agent 传入语义描述 (如 "登录按钮"), Skill 内部按以下优先级尝试定位: 1) `get_by_role` + accessible name 匹配; 2) `get_by_text` 文本内容匹配; 3) 作为 CSS selector 兜底. 以第一个命中为准.
- 理由: Accessible name 是最语义化的定位方式, 对 agent 最友好. 文本内容次之. CSS selector 作为最后手段确保总能定位, 但 agent 不应该依赖它.
- 预计影响: `browser_agent/_locator.py` 中实现三级回退定位逻辑.
- 实际影响: `browser_agent/_locator.py` 实现 `locate(page, description)` 函数: Level 1 依次尝试 get_by_role (16 种常见 role) + get_by_label + get_by_placeholder; Level 2 用 get_by_text; Level 3 用 page.locator 作为 CSS selector 兜底. 对含 role 后缀的描述 (如 "submit button") 自动提取潜在名称 (去 " button" 后缀) 提升匹配率. (ISSUE-02 a1, verified)
- 相关 issue: ISSUE-02

## D011: 并发调用时每次创建独立 Browser 实例

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: Browser 不为单例. 每次 skill 调用创建独立的 Playwright Browser 实例和 context, 调用结束后销毁. 不共享 Browser 实例.
- 理由: 独立实例保证隔离性 — 一个调用的超时/崩溃不影响其他调用. Playwright Browser 实例创建成本可接受 (~0.5-1s), 不引入共享状态管理复杂性. 替代方案 (Browser 池或单例) 增加连接管理和并发安全复杂度.
- 预计影响: `browser_agent/browser.py` 中 Browser 类每次实例化创建新 `sync_playwright` 连接; `__del__` 或 context manager `__exit__` 确保资源释放.
- 实际影响: `browser_agent/browser.py` `Browser.__init__` 仅设字段为 None. `start()` 创建 `sync_playwright` + Chromium + context + page. `stop()` 逐层关闭 (context→browser→playwright), 设字段为 None 防重复关闭. 支持 context manager 协议. (ISSUE-01 a1, verified)
- 相关 issue: ISSUE-01

## D012: scroll 操作语义

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: `scroll(direction, amount, timeout=30.0)`. direction ∈ {"up", "down"}. amount 为像素值, 正数表示沿 direction 方向滚动的距离. 使用 `window.scrollBy(0, amount)` 实现 (down 正值, up 负值).
- 理由: 像素是最精确的滚动单位, 对 agent 来说可计算. 视口百分比虽然直观但不同页面视口高度不同, 不可预测. Playwright 的 `page.evaluate("window.scrollBy")` 是可靠实现方式.
- 预计影响: `browser_agent/operations.py` 中 `scroll()` 函数签名和实现; 参数校验拒绝非法 direction.
- 实际影响: `browser_agent/operations.py` `scroll(direction, amount, timeout=30.0)`. 使用 `page.evaluate(f"window.scrollBy(0, {delta})")`. direction 校验抛 ValueError (编程错误). (ISSUE-04 a1, verified)
- 相关 issue: ISSUE-04

## D013: screenshot 操作语义

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: `screenshot(path=None, full_page=True, timeout=30.0)`. path 为 None 时返回 `bytes` (PNG 二进制) 内嵌于 OperationResult; 非 None 时写入指定路径并返回路径. 格式固定 PNG. full_page 控制截取整个页面 (含滚动区域) 还是仅视口.
- 理由: PNG 是无损格式, 适合 agent 视觉分析. 默认 full_page=True 因为 agent 通常需要完整页面上下文. 内存返回 (path=None) 避免临时文件管理开销.
- 预计影响: `browser_agent/operations.py` 中 `screenshot()` 函数; OperationResult 需支持 `bytes` 字段或专用 `ScreenshotResult` 子类.
- 实际影响: `browser_agent/operations.py` `screenshot(path=None, full_page=True, timeout=30.0)`. `browser_agent/result.py` 定义 `ScreenshotResult(success, error, image, path)`. path=None 返回 bytes 于 image 字段. (ISSUE-03 a1, verified)
- 相关 issue: ISSUE-03

## D014: get_page_structure 返回格式

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: `get_page_structure(max_elements=500, timeout=30.0)` 返回 `dict`: `{"url": str, "title": str, "elements": [{...}, ...], "truncated": bool}`. elements 取自 Playwright 可访问性树快照 (snapshot), 每元素含 `role`, `name`, `children` (递归, 但 depth ≤ 4). 超过 max_elements 时截断并标记 truncated=true.
- 理由: Dict 格式对 agent 最友好 (可直接 JSON 序列化, 或直接字典读取). 截断策略防止页面过大时返回数百 KB 数据阻塞 agent 推理. 深度限制 4 层覆盖大部分有意义的页面结构.
- 预计影响: `browser_agent/_structure.py` 负责 snapshot 解析和截断; OperationResult 需 `data: dict` 字段.
- 实际影响: `browser_agent/_structure.py` 通过 `page.evaluate()` JS DOM 提取实现 (Python Playwright 无 `page.accessibility`). `browser_agent/result.py` 定义 `StructureResult(success, error, data)`. `browser_agent/operations.py` `get_page_structure(max_elements=500, timeout=30.0)`. (ISSUE-03 a1, verified. 偏离: JS DOM 替代可访问性树, 因 Python API 不支持)
- 相关 issue: ISSUE-03

## D015: wait_for_element 语义

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: `wait_for_element(description, state="visible", timeout=30.0)`. state ∈ {"attached" (DOM 存在), "visible" (可见且非零尺寸), "hidden" (DOM 存在但不可见)}. 默认 "visible" 因为 agent 通常要等元素可交互.
- 理由: 三种状态覆盖 Playwright 原生 `wait_for` 的常用场景. 默认 visible 对齐 MDN 对 "可见" 的定义, 是最安全的等待语义.
- 预计影响: `browser_agent/operations.py` 中 `wait_for_element()` 函数, 使用 `_locator.py` 定位后调用 Playwright `element.wait_for(state=...)`.
- 实际影响: `browser_agent/operations.py` `wait_for_element(description, state="visible", timeout=30.0)`. 使用 `_locator.py` 定位, 然后 `locator.wait_for(state=...)`. state 校验抛 ValueError. (ISSUE-04 a1, verified)
- 相关 issue: ISSUE-04

## D016: Python 最低版本 3.9

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: `requires-python >= 3.9`. Playwright 要求 Python 3.8+, 选 3.9 作为最低版本因为 Python 3.8 已 EOL (2024-10).
- 理由: Python 3.9 提供了 `str.removeprefix`/`removesuffix`, PEP 585 泛型 (`list[str]` 替代 `List[str]`) 等改进, 减少实现复杂度. 不在本 skill 中支持 EOL 版本.
- 预计影响: `pyproject.toml` 声明 `requires-python = ">=3.9"`; CI 矩阵不应包含 3.8.
- 实际影响: `pyproject.toml` `requires-python = ">=3.9"`. (ISSUE-01 a1, verified)
- 相关 issue: ISSUE-01
