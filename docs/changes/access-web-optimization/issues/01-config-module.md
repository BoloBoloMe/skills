## 父级

`docs/changes/access-web-optimization/CONTRACT.md`

## 执行(Execution)

- [ ] 已实现

## 要构建什么

新增 `browser_agent/config.py`: 运行时探测 OS / `sys.executable` / `tempfile.gettempdir()`, 计算 session-key = `sha256(canonicalize(cwd))[:16]`, 在 `<tempdir>/access-web/<session-key>/` 下规划 `browser.json` / `profile/` / `artifacts/{screenshots,downloads,logs}/`, 自绑 socket 分配 CDP 端口, 经 transient `sync_playwright()` 读 `p.chromium.executable_path` 定位 Chromium 二进制并缓存到 metadata, 提供 metadata (pid/port/profile_dir/created_at/status) 读写. 配套单元测试. 不启动浏览器. 此切片适合 AFK: 纯 stdlib + Playwright 路径探测, 无产品/API 决策.

## 相关决策

D003, D011, D012

## 允许范围

`browse/browser_agent/config.py` (新增) 及其单元测试 (如 `browse/tests/test_config.py`).

## 禁止范围

不得启动浏览器或修改 `browser.py`/`session.py`/`operations.py`/`_locator.py`/`_structure.py`/`result.py`/`__init__.py`/`scrape/`. 不得在 cwd 写文件. 不得新增运行时依赖.

## 验证入口

`cd browse && pytest tests/test_config.py` (或等价路径). 覆盖: session-key 对同 cwd 稳定/不同 cwd 不同, tempdir 跨平台探测, 端口分配返回可用端口, metadata 写入后读回一致, 二进制定位返回存在的路径.

## 风险提示

`p.chromium.executable_path` 需 transient playwright driver, 仅首次调用, 之后读缓存. 若 Chromium 未装, 抛带修复命令 (`<sys.executable> -m playwright install chromium`) 的精确错误.

## 停止条件

若发现 `tempfile.gettempdir()` 在目标平台行为异常, 或二进制定位无可靠 API, 停止并上报. 不得超出本 issue 边界.

## 适合 AFK 的原因

纯环境探测与路径计算, 无产品行为/API/架构决策点, 单元测试可完全确定正确性.

## 验收标准

- [ ] `config.py` 提供 session-key 计算, tempdir/session 目录规划, 端口分配, 二进制定位, metadata 读写.
- [ ] 同 cwd 多次调用返回同一 session-key; 不同 cwd 返回不同.
- [ ] 产物路径全部在 `tempfile.gettempdir()` 下, cwd 无文件.
- [ ] Chromium 未装时抛带修复命令的错误.
- [ ] 单元测试通过.

## 被阻塞于

无 - 可以立即开始
