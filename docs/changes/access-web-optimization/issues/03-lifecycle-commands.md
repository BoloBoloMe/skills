## 父级

`docs/changes/access-web-optimization/CONTRACT.md`

## 执行(Execution)

- [ ] 已实现

## 要构建什么

新增浏览器生命周期管理操作: `status()` 返回 `alive/url/title/pid/headed/cdp_port/profile_dir/pages` (`alive` 双检 pid + CDP 端口); `stop_browser_session()` 读 metadata pid 杀 Chromium (Windows `taskkill /F /PID`, POSIX `os.kill` SIGTERM), 保留 profile; `cleanup_browser_session()` = stop + `rmtree` session 目录; `reset_session()` 仅弃当前进程内 Session 句柄; `cookies()` 返回当前 context 所有 cookies. 此切片适合 AFK: 语义已由 D009/D010 钉死.

## 相关决策

D009, D010

## 允许范围

`browse/browser_agent/operations.py`, `result.py`, `__init__.py`, `session.py` (新增 stop/cleanup 实现), 对应测试.

## 禁止范围

不得改 L1 操作签名/返回类型, 不得改 `_locator.py`/`_structure.py`/`scrape/`. `status` 不得自动截图, 不得做 `bring_to_front`. `stop` 不得删 profile.

## 验证入口

`cd browse && pytest` 新增测试: `status` 返回字段齐全且 `alive` 正确; `stop` 后 Chromium 进程消失但 profile 目录存在 (重新启动仍登录); `cleanup` 后 session 目录不存在; `reset_session` 不影响 Chromium; `cookies` 返回当前 cookies.

## 风险提示

`taskkill`/`os.kill` 跨平台 pid 杀需处理进程已退出的情况 (不抛). pid 来自 metadata, 若 metadata 缺失则视为未运行.

## 停止条件

若按 pid 杀无法可靠终止脱离式 Chromium (跨平台), 停止并上报. 不得超出本 issue 边界.

## 适合 AFK 的原因

D009/D010 已钉死命令语义与字段, 无决策点.

## 验收标准

- [ ] `status` 返回 8 个字段, `alive` 双检 pid + CDP 端口.
- [ ] `stop_browser_session` 杀 Chromium, profile 目录保留.
- [ ] `cleanup_browser_session` 杀 Chromium 并删整个 session 目录.
- [ ] `reset_session` 不影响 Chromium 进程与 profile.
- [ ] `cookies` 返回 context cookies 列表.
- [ ] 不自动截图, 无 `bring_to_front`.

## 被阻塞于

- `docs/changes/access-web-optimization/issues/02-detached-cdp-session.md`
