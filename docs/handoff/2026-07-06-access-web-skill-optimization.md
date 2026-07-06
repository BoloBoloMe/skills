# access-web skill 优化交接

## 背景

用户下个会话重点: 接收当前工作区里的 `access-web` 改进提案, 并据此优化 skill 源码.

本次会话围绕 `access-web` 的交互浏览模式展开. 用户先要求打开一个需要登录的 Grafana Explore URL, 登录后让我分析 `test-middle-platform/cz-pay-center` 的 Loki 日志, 收集多个支付渠道创建订单失败原因. 使用过程中暴露出 `access-web` 当前浏览器会话生命周期, 依赖安装, 路径策略, SPA 提取能力等问题. 随后用户要求整理一份优化提案, 并多次修订提案方向.

## 必读推荐

1. `access-web-skill-optimization-proposal.md`: 当前工作区的主提案. 理由: 已记录问题复盘, 源码级改造提案, 目标架构, 迁移步骤, 测试计划. 下个 agent 应以此为优化 skill 的主输入.
2. `C:\Users\L9214\.pi\agent\skills\access-web\browse\browser_agent\session.py`: 理由: 当前核心生命周期问题所在地. 现实现为模块级 `_SESSION` + `atexit`, 注释明确为进程内单例, 内存 profile, 不写磁盘.
3. `C:\Users\L9214\.pi\agent\skills\access-web\browse\browser_agent\browser.py`: 理由: 当前 Playwright 启动逻辑所在地. 现使用 `chromium.launch()` + `new_context()`, 不是 persistent context.
4. `C:\Users\L9214\.pi\agent\skills\access-web\browse\browser_agent\operations.py`: 理由: 所有 public API 都直接依赖 `get_session().page`. 优化时需要保持函数名和 dataclass 返回类型, 内部改为 provider/controller 分派.
5. `C:\Users\L9214\.pi\agent\skills\access-web\browse\tests\*.py`: 理由: 现有测试大量 patch `Browser.start`, 说明 `Browser.start` 是测试 seam. 改造不能直接删除 local Browser 模式.
6. `C:\Users\L9214\AppData\Local\Temp\pi_browser_control.py`: 理由: 本次临时实现的常驻浏览器 controller 原型. 不建议原样落库, 但可参考其 HTTP 控制接口和复用登录态思路.

## 路线图

1. 起点: 用户给出 Grafana Explore URL, 要求打开需要登录的日志查询页面, 等用户手动登录后再继续操作.
2. 发现依赖问题: `access-web` 浏览器封装导入 Playwright 失败. 用户后来明确要求把 Playwright 安装到全局 uv Python, 因为这是 skill 必要组件. 已安装并验证全局 `playwright` 可用. 临时 venv 已清理.
3. 发现生命周期问题: 原封装只在单个 Python 进程内保留浏览器会话. 为了让用户登录后继续操作, 临时写了 `pi_browser_control.py`, 用常驻进程持有 browser/page, 通过 `127.0.0.1:51237` 控制.
4. 完成业务任务: 用户登录后, 通过 Grafana datasource proxy 的 Loki `query_range` API 批量查询 `cz-pay-center` 多个 trace ID, 保存日志, 汇总创建订单失败原因. 该业务结论不是下个 agent 的主要任务, 但证明 `network_json`/带 cookie API 查询比操作 Grafana UI 更可靠.
5. 初版提案: 在当前工作区创建 `access-web-skill-optimization-proposal.md`, 总结问题, 可复用脚本, Grafana/Loki 查询模式, 改造建议.
6. 删除已解决项: 用户指出提案里包含已解决问题. 已删除全局 Playwright 缺失和临时 venv 清理等已完成事项, 保留长期有价值的设计问题.
7. 明确核心设计决策: 用户强调浏览器会话应在 pi 会话结束前有效, 会话内容应持久化, 而不是绑定单个 Python 进程. 提案已升级为 `浏览器会话生命周期绑定错误`, 并提出 pi-session scoped browser controller.
8. 源码级研究: 已阅读 `browser.py`, `session.py`, `operations.py`, `_locator.py`, `_structure.py`, `result.py`, 以及测试. 提案中新增源码级改造方案: `config.py`, `controller.py`, `client.py`, `providers.py`, `LocalPageProvider`, `ControllerPageProvider`, `launch_persistent_context`, `network_json`, reset/stop/cleanup 语义拆分.
9. 路径策略修订: 用户不希望 skill 固定 Windows 临时目录, 而是指导 agent 先探测当前系统环境, 再按实际 OS/shell/Python 管理方式决定路径. 提案已改为环境感知路径策略, 禁止把 `/tmp`, `%LOCALAPPDATA%`, `/var/tmp` 作为跨平台默认假设.

距离目的地: 提案已足够作为实现蓝图. 剩余工作是实际修改 `access-web` skill 源码和测试, 重点在 pi 会话级持久 browser controller, persistent profile, provider 分派, 环境探测路径策略, 以及 `network_json` 等复杂 SPA/API 辅助能力.

## 当前状态

- 当前工作区: `D:/Workspace/ChangZhi/pmx-switch`.
- 当前工作区内主产物: `access-web-skill-optimization-proposal.md`.
- 当前工作区内本交接文档: `docs/handoff/2026-07-06-access-web-skill-optimization.md`.
- 全局 uv Python 已安装 Playwright. 这是当前环境状态, 不是提案待办.
- 非全局临时 venv 已删除.
- 本次临时浏览器 controller 脚本仍可能存在于 Windows Temp, 仅作参考原型.

## 关键约束

- 用户要求中文回复和中文文档, 标点使用 ASCII 半角.
- 不要把路径策略写死为 Windows 目录. 需要先探测运行环境, 再决定路径.
- 不要把浏览器生命周期绑定到 Python 工具进程. 目标生命周期是 pi 会话.
- 保持现有 public API 兼容, 如 `navigate`, `click_element`, `extract_text`, `screenshot` 等.
- 现有 tests 依赖 patch `Browser.start`, 改造时需要保留 local mode seam.
- `reset_session()` 不应再等价于清理用户登录态. 提案中已要求拆分 `reset_session`, `stop_browser_session`, `cleanup_browser_session`.

## 敏感信息处理

已遮蔽密码/API key 等敏感内容. 文档中保留的内部 URL, datasource uid, trace ID, 本地路径仅用于技术定位和复现上下文. 不包含用户凭据.
