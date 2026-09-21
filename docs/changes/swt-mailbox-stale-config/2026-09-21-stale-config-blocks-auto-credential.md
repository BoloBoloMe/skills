# Bug 反馈: mesh 前旧配置迁移后挡住 D012 自动发放, 且旧 schema 不被新代码读取

- 日期: 2026-09-21
- 来源: 三机 (实际两机) mesh 信箱真跑准备阶段, 工作站首次 serve 启动发现
- 严重级: 中 (老用户首启信箱不可用, 但有明确报错面且易手工恢复)
- 状态: 已修复 (2026-09-21, 见文末修复记录)

## 现象

工作站 (mesh 前用过中心信箱时代取信) 首次 `swt-mailbox.py serve`:

- `GET /admin/stats` → `sessions: 0` — D012 承诺的零配置自动发放没有发生
- 自动写出的 `~/.agents/sandbox-worktree/mailbox.json` 实为迁移产物: `server` 指向老总信箱地址 (`192.168.131.194:38417`, mesh 前中心信箱所在), 字段名为旧 schema 的 `device`
- 该配置下取信/send 必然失败: 新代码 `load_credentials` 只认 `session` 字段

## 根因

三个机制互相打架:

1. `_migrate_legacy_config()` (D015): 老路径 `~/.config/swt/mailbox.json` 存在且新路径缺失 → `os.rename` 原样搬移 (保 mtime, 老路径删除), 不检查内容
2. `auto_credential()` (D012): 仅判 `cfg.exists()` → 迁移件占位后跳过自动发放
3. `load_credentials()`: 只认新 schema (`server` + `session` + `signing_key`) → 迁移件读不出凭证

净效果: 迁移件既挡住 D012, 又不被新代码接受, 信箱面全断.

## 触发面

仅 mesh 前配过取信的机器 (老路径有旧 schema 配置). 全新机器不受影响. 两台真机 (工作站/yoga) 均踩中, yoga 侧在首启前已手工排除.

## 当场处理 (2026-09-21 真跑现场)

旧配置改名归档 `mailbox.json.stale-pre-mesh` (0600 内容原样) + 重启 serve → 自动发放恢复 (`<hostname>-host` 正常注册). 两台机同一处理.

## 修复记录 (2026-09-21)

1. **`auto_credential()` 加可用性体检**: 新增 `_config_usable()` (判据与 `load_credentials` 同源: `server`/`session`/`signing_key` 齐全) — 配置存在但不可用 → `_archive_stale_config()` 归档挪开 (目标名冲突追加序号) + stderr 明示去向与原因, 随后 D012 正常发放. 不选择当场改写: 旧配置指向的服务器已不存在, 改写字段仍是坏地图, 挪开最干净.
2. **回归测试 TS-006** (`tests/test_swt_mailbox_cli_tools.py::test_stale_config_archived_and_reissued`): 旧 schema 配置 (device 字段 + 老总信箱地址) 下 serve 启动 → 恰一个 `<hostname>-host` session; 归档内容原样; 新配置新 schema/0600/server 指向本 serve.
3. **连带修测试基建环境泄漏** (`tests/conftest.py`): serve 缺省读真机 `~/.agents/sandbox-worktree/neighbors.json`, 真跑过的机器上该文件泄漏进测试, admin TS-003 (无邻居 404) / TS-004 (邻居计数) 在干净 `6c44e5c` 上即假失败. 修复: 夹具 env 设 `SWT_MAILBOX_NEIGHBORS` 指向夹具 workdir 隔离.

验证: 信箱面 57 项测试全绿 (含新增 TS-006).

## 附带发现 (记录未修)

取信端在 20s hold 长轮询中途断连 (如调用方超时/ssh 掉线), 服务端 `http.server` 会为该请求打印整屏 `BrokenPipeError` 堆栈. 无害 (ThreadingHTTPServer 每请求隔离, 服务不退), 但 serve 前台窗口噪音大. 候选小改进: `_json` 写回捕 `BrokenPipeError` 静默. 真跑实测中由 `timeout 8` 截断取信进程触发一次, 已人工确认无碍.
