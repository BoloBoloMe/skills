# access-web skill 持久浏览器与跨平台优化

## 问题陈述

当前 `access-web` skill 在交互浏览场景 (如登录 Grafana 后批量查询日志) 中存在以下问题:

1. **浏览器会话随 Python 进程退出而丢失**. 每次工具调用创建新的浏览器实例, 用户登录态 (cookies/localStorage/sessionStorage) 无法跨工具调用保持. 用户需要反复登录, 严重降低交互效率.
2. **headed 浏览器可见性不确定**. 启动后窗口可能被遮挡或未出现在用户桌面, 没有可靠的状态反馈机制.
3. **路径语义依赖硬编码假设**. 代码隐含假设 `/tmp` 等 Unix 路径可用, 在 Windows + MSYS/Git Bash 环境下频繁出现路径找不到的错误.
4. **复杂 SPA 页面提取不稳定**. 对 Grafana Explore 等 SPA, 语义提取命中率低, 缺乏直接访问数据源 API 的能力.
5. **浏览器管理缺乏生命周期**. 没有 start/status/stop/cleanup 管理命令, 异常退出后无恢复机制.

## 解决方案

将浏览器会话从"进程内单例"升级为"pi 会话级长驻服务".

核心思路: 引入 pi-session scoped browser controller 进程, 持有 Playwright browser context, 使用 persistent user data dir 保存登录态. 工具进程通过 HTTP client 连接到 controller, 不再直接持有浏览器.

同时补齐: 环境探测与跨平台路径策略, 低层页面提取 API (page_text/selector_text/network_json), 浏览器生命周期管理命令, 以及操作级抽象后端 (`OperationBackend`) 使 local 和 controller 两种模式可切换.

## 用户故事

1. 作为一名需要登录 Grafana 查看日志的开发者, 我想要在 pi 会话内登录一次后所有后续工具调用自动复用登录态, 以便不再重复登录操作.
2. 作为一名使用 Windows + Git Bash 的开发者, 我想要 skill 自动探测系统环境并给出正确的路径, 以便不会因为 `/tmp` 指向不一致而找不到文件.
3. 作为一名需要在 headed 模式下确认浏览器状态的开发者, 我想要 `status` 命令返回 pid/url/title/screenshotPath, 以便快速判断浏览器是否正常启动并可见.
4. 作为一名需要从 Loki 数据源批量提取 JSON 日志的开发者, 我想要 `network_json` 直接带 cookie 查询 API, 以便绕过复杂 SPA UI, 获取结构化数据.
5. 作为一名需要管理浏览器生命周期的开发者, 我想要 `stop` 和 `cleanup` 命令显式控制浏览器进程和 artifact 目录, 以便在任务结束后释放资源.
6. 作为一名在多个 pi 会话中并行工作的开发者, 我想要各会话的浏览器状态互相隔离, 以便不同任务的登录态不互相污染.
7. 作为一名运行现有测试的开发者, 我想要测试继续在 local 模式下通过, 以便改造不破坏已有功能.
8. 作为一名遇到 SPA 页面提取失败的开发者, 我想要 `page_text` 和 `selector_text` 低层 API 绕过 accessible name 定位, 以便稳定提取页面正文.

## 关键取舍

- **双模式架构 (local/controller)**: 保留进程内 Playwright local 模式作为测试和简单场景的默认, 交互浏览使用 controller 模式. 两个模式通过 `OperationBackend` 抽象统一, `LocalBackend` 内部用 Playwright Page, `ControllerBackend` 用 HTTP client. 不暴露 `Page` 对象到 controller client 侧.
- **persistent context 代替普通 context**: 使用 `chromium.launch_persistent_context()` + `user_data_dir` 持久化 cookies/localStorage. stop 时关闭 context 即可 (persistent 无独立 Browser 句柄).
- **controller 用 `context.request` 而不是 `page.evaluate(fetch)`**: `network_json` 实现使用 Playwright `APIRequestContext`, 自动共享 context cookie 且不受浏览器 CORS 限制.
- **路径策略由 config 模块统一探测**: 启动时探测 OS/shell/Python/临时目录, 生成 `status.json` 记录所有路径, 后续进程读取 metadata 不再重复猜测.
- **测试隔离保留**: `reset_session` 在 local 模式下仍停止 Browser (保持测试隔离), controller 模式下只清 client facade cache. 测试通过 `ACCESS_WEB_MODE=local` 环境变量锁定 local 模式.
- ****`_locator.py`/`_structure.py` 保留在 `browser_agent/` 包内**: controller 进程 import 复用, client 侧仅 `LocalBackend` 使用. 定位/提取在 controller 进程完成, client 收发语义请求和结果.

## 未确认假设

| # | 假设 | 影响范围 | 验证方式 |
|---|---|---|---|
| H1 | pi harness 注入 `PI_SESSION_ID` 环境变量作为会话标识 | session key 优先级, 多会话隔离 | 向 pi 确认是否注入; 若无, fallback 用 cwd 下 `.access-web/session.id` 存 uuid |
| H2 | controller 进程可在 pi 会话结束时被自动清理 | cleanup 策略 | 确认 pi 是否有会话结束 hook; 若无, 依赖用户显式 `cleanup` 或定时清理 |
| H3 | controller 用 stdlib `http.server` 足够, 无需新增依赖 | 依赖管理 | 验证现有 Python 版本 http.server 能力, 复杂场景可后期换 fastapi |
| H4 | persistent user data dir 在 Windows 下的路径长度不超限 | profile 目录选择 | 探测 `tempfile.gettempdir()` + `Path.home()`, 验证实际路径长度 |

## 范围外

- 不做 Grafana/Loki 专用查询辅助函数, 它作为 P2 后续补充, 不在此 PRD 范围内.
- 不做批量 trace 错误摘要模板, 它不在此 PRD 范围内.
- 不做产物自动清理 (cleanup --older-than), 它不在此 PRD 范围内.
- 不做 `bring_to_front` 显式窗口聚焦功能, 以截图反馈替代, 它不在此 PRD 范围内.

## 补充说明

- `browse.md` 需同步更新: 明确浏览器生命周期绑定 pi 会话, 登录态跨工具调用保持, `reset_session`/`stop`/`cleanup` 语义区别, `network_json` 优先于 UI 提取的使用场景.
- 迁移分 9 步执行, 关键顺序: config → Browser persistent → controller/client → provider 分支 (默认 local) → 扩展 API → network_json → conftest 锁定 local → 文档/tests → 切默认 controller. 步骤 7 (conftest 锁定) 必须在步骤 9 (切默认) 之前完成.
- controller 测试 (`test_controller_lifecycle.py` 等) 需 `@pytest.mark.integration` + `--run-integration` opt, 默认跳过, 避免 CI 无 headed 环境导致挂.
- controller 进程启动用 `subprocess.Popen` 跨平台脱离 (`creationflags=DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP` on Windows, `start_new_session=True` on POSIX), 不依赖 shell `nohup`.
- `screenshot` controller 模式下需支持两种返回: `path=None` 返回 base64 (client 解码为 image bytes), `path` 非空返回路径.
