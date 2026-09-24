## 父级
- `../EXECUTION.md`
## 执行
- [x] 已实现
## 要构建什么
展示服务骨架 `workflow/navigate/scripts/web_server.py`: CLI 子命令 start/status/stop, stdout 单行 UTF-8 JSON, 退出码 0/1. start 幂等 — 同 uid 已有存活实例则复用不起新进程, 返回其 URL; 否则以隐藏子命令 `__serve__` re-exec 自身起守护进程. 默认端口 39271, 被占时自动探测可用端口; 实际端口写入运行时文件, status 读之报告. 运行时文件 (pid/锁/端口) 放系统临时目录, 不进仓库; 目录位置经环境变量可覆盖 (测试隔离). 服务具备最小 HTTP 响应能力供判活 (完整端点归 ISSUE-04). stop 停止进程并清理运行时文件.
结尾: 适合 AFK — 进程生命周期模式由 D008/D010 定死, 且 present web_server.py (F002) 提供逐段可抄的实现先例.
## 覆盖依据
- Product: `docs/changes/navigate-roadmap-json/PRODUCT.md`, AC-008, AC-009, AC-010
- Technical: `docs/changes/navigate-roadmap-json/TECHNICAL.md`, 模块接口 (展示服务), 接缝与适配器, 测试接缝, 关键流程 (start 幂等与端口回退)
## 相关决策
- `docs/changes/navigate-roadmap-json/DECISIONS.md`: D008, D010, D015, D016
## 允许范围
- 新增 `workflow/navigate/scripts/web_server.py` (含包结构所需文件)
- 新增 `workflow/navigate/tests/`
- `pytest.ini` 追加 testpath `workflow/navigate/tests` (若 ISSUE-01 未加)
## 禁止范围
- 不动 `roadmap.py`, `web/`, `SKILL.md`, `TEMPLATES.md`, 其他 skill 目录 (尤其不修改 `general/present/`)
- 不实现 `/api/roadmap` 数据端点与空闲自退 (ISSUE-04)
- 不引入认证/TLS (NG-002); 不新增第三方依赖; 不复用 present 的服务进程
## 代码定位提示
- 逐段参照 `general/present/scripts/web_server.py`: 锁文件判活, `__serve__` re-exec 守护化, 端口探测, fcntl 锁, run_*/main() 分层
- 测试参照 `general/present/tests/test_web_server_lifecycle.py`, `test_web_server_fixed_port.py`, `test_web_server_cli.py` 的环境变量覆盖运行时目录 + 起真实实例模式
## TDD 切片
- TS-001:
  接缝: 环境变量覆盖运行时目录指向 tmp_path + 起真实实例 (TECHNICAL.md 测试接缝).
  测试用例: TC-008.
  先写的失败测试: `test_start_status_stop_cycle` — 脚本不存在, subprocess 报 FileNotFound.
  最小绿色实现范围: start (起守护进程, 写运行时文件, 返回 URL), status (读运行时文件报存活与端口), stop (停止并清理).
  不得测试: 守护进程内部线程结构.
  覆盖: AC-008.
- TS-002:
  接缝: 同上.
  测试用例: TC-009.
  先写的失败测试: `test_start_reuses_alive_instance` — 连续两次 start, 断言第二次返回相同 pid/端口, 进程列表无第二个实例.
  最小绿色实现范围: 锁文件判活 + 复用返回.
  覆盖: AC-009.
- TS-003:
  接缝: 同上.
  测试用例: TC-010.
  先写的失败测试: `test_port_conflict_falls_back` — 预先用 socket 占住 39271, start 后断言实际端口 != 39271 且 status 报告一致, 服务可用.
  最小绿色实现范围: 默认端口尝试 + 被占则探测可用端口 + 实际端口落运行时文件.
  覆盖: AC-010.
## 验证入口
- `uv run pytest workflow/navigate/tests/ -q` 全绿
- 手跑 start → status → 浏览器或 curl 访问返回的 URL 有 HTTP 响应 → stop, 再 status 报未运行
## 风险提示
- 判活不能只看 pid 文件存在 — pid 可能被复用, 须发真实请求确认响应
- 守护进程须脱离父进程生命周期 (测试进程退出后服务不连带死亡); 反之测试的 stop 必须能真正杀掉它
- 端口探测与实际绑定之间存在竞态, 绑定失败要能继续回退
## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
## 适合 AFK 的原因
生命周期行为全部定死于 D010, 且有 present 同构实现可逐段移植, 无待决策项.
## 验收标准
- [ ] AC-008: 首次 start 就绪并返回可访问 URL
- [ ] AC-009: 重复 start 复用既有进程, 不起第二实例
- [ ] AC-010: 39271 被占时自动换端口, status 报告实际端口
- [ ] 运行时文件在系统临时目录, 仓库工作区无污染 (D016)
- [ ] `uv run pytest workflow/navigate/tests/ -q` 全绿
## 被阻塞于
- 无
