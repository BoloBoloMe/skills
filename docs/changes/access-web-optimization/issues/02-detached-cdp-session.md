## 父级

`docs/changes/access-web-optimization/CONTRACT.md`

## 执行(Execution)

- [x] 已实现

## 要构建什么

将浏览器会话从进程内单例改为脱离式 Chromium + CDP 跨进程共享. `browser.py` 用 `subprocess.Popen` 脱离式启 Chromium (`--user-data-dir` + `--remote-debugging-port`, Windows `DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP`, POSIX `start_new_session=True`), 所有进程 `connect_over_cdp` 拿真实 `Page`. `session.py` 改为 metadata 驱动: 读 metadata → CDP 端口可连则 connect → 否则 detached launch 并写 metadata; `connect_over_cdp` 失败时用同 profile 重 launch (自愈). `conftest.py` 重写为真实 headless fixture (专用 session-key, teardown `cleanup`), 4 个现有测试改 harness (经 session API `page.set_content`/`page.route`), 保留全部 L1 断言. 端到端: navigate 跨进程复用, 浏览器存活于工具进程退出. 此切片适合 AFK: 决策已闭合, 实现路径明确.

## 相关决策

D001, D002, D003, D005, D006, D009

## 允许范围

`browse/browser_agent/browser.py`, `browse/browser_agent/session.py`, `browse/tests/conftest.py`, `browse/tests/test_navigate.py`, `test_interaction.py`, `test_extraction.py`, `test_integration.py`. 可新增测试文件.

## 禁止范围

不得改 `_locator.py`/`_structure.py`/`operations.py` 的 L1 签名与返回类型, 不得改 `result.py` 的现有 dataclass, 不得改 `scrape/`. 不引入 `ACCESS_WEB_MODE`/local 模式/`OperationBackend`/`launch_persistent_context` 持有. 不新增运行时依赖.

## 验证入口

`cd browse && pytest` (需 `python -m playwright install chromium`). 现有 4 测试在真实 headless 通过. 新增: persistent profile 跨 start 复用 cookie, 新进程 `connect_over_cdp` 拿同一 page, kill Chromium 后自愈重 launch 且 cookie 在, 不同 session-key 隔离.

## 风险提示

脱离式 Chromium 在 Windows 上可能仍被父进程 job object 连坐杀掉 — 若验证发现工具进程退出后 Chromium 死亡, 停止退回 `grill-with-docs` 重定启动机制.

## 停止条件

若脱离式启动无法让 Chromium 存活, 或 `connect_over_cdp` 拿不到带 cookie 的 context, 停止并上报 (属 D001/D002 实现冲突). 不得超出本 issue 边界.

## 适合 AFK 的原因

架构决策 D001/D002/D005/D006 已闭合, 无进一步产品/API/架构决策点. 唯一风险 (job object) 属事实验证, 失败时停止上报而非自行决策.

## 验收标准

- [ ] 工具进程退出后 Chromium 存活, 新进程 `connect_over_cdp` 复用同一浏览器与 profile.
- [ ] 同 cwd 跨调用复用 cookie; 不同 cwd (不同 session-key) 隔离.
- [ ] Chromium 被外部杀掉后, 下次调用自愈重 launch, 登录态保留.
- [ ] 现有 4 个测试在真实 headless 下通过, L1 断言全保留.
- [ ] 无 `ACCESS_WEB_MODE`/local 分支.

## 被阻塞于

- `docs/changes/access-web-optimization/issues/01-config-module.md`
