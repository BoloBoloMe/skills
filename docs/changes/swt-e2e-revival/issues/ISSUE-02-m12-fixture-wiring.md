## 父级
- `../EXECUTION.md`
## 执行
- [x] 已实现
## 要构建什么
把 `tests/test_swt_m12.py` 的真容器 birth 用例接回可跑状态, 并让它们与宿主桌面解耦:
1. `SwtBirthFixture` (及其子类) 的 birth 路径必须显式选定 agent 模板: 用 ISSUE-01 的夹具模板 (名字由 `SWT_AGENT_TEMPLATES_DIR` 与夹具共同决定) 补上 `--agent-template <name>`; 需要几次调用 (先 DECIDE 再带答复) 就按现夹具的既有风格来, 不要改断言意图.
2. 夹具启动 ISSUE-01 的本机假网关与假 Key, 保证模板安装能过.
3. 与宿主桌面解耦: 夹具默认把 `WAYLAND_DISPLAY` 指到一个不存在的名字 (例如 `wayland-absent`) 再起 swt 子进程, 使 `swt.py host_wayland_socket()` 返回 None, 从而不再受宿主 socket 权限 0775 影响. 允许留一个显式开关 (环境变量) 让个别真需要桌面直通的用例回到真实值, 但默认必须是不直通.
4. `tests/README.md` 与 `tests/run` 的说明/映射按实际改动同步 (例如 m12 真容器前置条件从"必须先建好镜像"改成"镜像 + 模板夹具", 以及 wayland 的默认行为).
## 覆盖依据
- `../EXECUTION.md` 完成定义节
- `tests/test_swt_m12.py` 的 `SwtFixture`/`SwtBirthFixture` (`birth_ready`, `run_swt`, 约 680-760 行), `tests/conftest.py`
- `scripts/swt.py` 的 `--agent-template` 决策闸 (约 3179-3196, 3480) 与 wayland 闸 (约 3149-3151)
## 相关决策
- `../../swt-container-env-docs/UNAUTHORIZED_DECISIONS.md` UD-015
## 允许范围
- `tests/test_swt_m12.py`; `tests/conftest.py`; `tests/README.md`; `tests/run`
## 禁止范围
- `scripts/` 下任何文件; 既有断言的意图 (不得为了让用例变绿而放宽/删除断言); 镜像构建 (用 ISSUE-01 建好的镜像); 用户真实资源
## 代码定位提示
- `SwtFixture.run_swt` / `SwtBirthFixture.birth_ready` (约 720-735 行): 现在传 `--image localhost/swt-m03:latest --mode whitelist --allow 127.0.0.1 --new-mother` 等, 没有 `--agent-template`
- `TestTS201BirthChain.test_birth_decides_then_builds_complete_chain` (约 803-830 行): 先跑一次拿 DECIDE, 再带参数重跑; 这是"如何回答决策"的现成范式
- `tests/run` 的 `RULES`/`PARALLEL`: 改 m12 的跑法或前置条件时同步 README (映射的唯一真相源是 README)
## TDD 切片
- TS-001:
  接缝: 接缝 2 (真容器), 由 m12 既有用例承载.
  测试用例: `TestTS201BirthChain.test_birth_decides_then_builds_complete_chain` 全过 (含容器内三份提示词 = 留档拼装产物, ~/docs/ 四份与留档一致, ro 追加写被拒).
  先写的失败测试: 现状该用例在第 825 行 `assertEqual(0, result.returncode)` 失败, stdout 为 agent-template 的 DECIDE.
  最小绿色实现范围: 夹具补 `--agent-template` + 假依赖 + 不直通 wayland.
  不得测试: 断言之外的新行为.
  覆盖: 真容器 birth 链.
- TS-002:
  接缝: 接缝 2.
  测试用例: 整套 `uv run --no-project python -m unittest tests.test_swt_m12 -v` 跑完, 失败集合为空 (允许的例外见下).
  先写的失败测试: 现状 48 项失败.
  最小绿色实现范围: 同 TS-001, 加上逐类排查剩余失败.
  不得测试: 无.
  覆盖: 真容器验收全链.
- TS-003:
  接缝: 夹具本身.
  测试用例: 夹具默认行为下 `swt.py host_wayland_socket()` 在子进程里返回 None (宿主 socket 权限不再影响测试); 且夹具退出后没有遗留容器/网关进程.
  先写的失败测试: 现状夹具沿用宿主 WAYLAND_DISPLAY.
  最小绿色实现范围: 夹具改环境变量 + 清理逻辑.
  不得测试: 宿主真实 socket 状态.
  覆盖: 与宿主桌面解耦.
## 验证入口
- `uv run --no-project python -m unittest tests.test_swt_m12 -v` (整套)
- `uv run --with pytest python -m pytest -m "not e2e" -q` 失败集合不超过既有 8 项
- 收工现场 `podman ps -a` 为空; 无遗留 git daemon / socat / 假网关进程
## 风险提示
- xdist 并行下真容器会抢资源: 若并行跑不稳, 允许在 `tests/run` 里把 m12 的并行数下调, 但必须在 README 记录原因
- 有些用例可能本来就依赖"桌面直通 ok"的路径 (display 门禁类). 这类用例若因不直通而失败, 逐条列出并在夹具里给它们显式打开真实直通 (或标注环境不适用), 不得删断言
- 别把"假网关"起在固定端口上抢占用户端口; 用 `free_port` 风格
## 停止条件
- 需要改 `scripts/` 才能过; 或失败根因指向 swt.py 真 bug (不是夹具面) 时, 停下报告, 不擅自改产品代码
- 需要用户真实凭据/网关/宿主权限时停下
## 适合 AFK 的原因
- 路线锁定, 夹具面封闭; 剩余工作是从失败清单里逐条排查夹具缺口
## 验收标准
- [ ] m12 整套真容器用例跑通 (例外逐条列出); 夹具默认不直通桌面; 无残留进程与容器; 快层不回归
## 被阻塞于
- ISSUE-01

## 遗留 (2026-10-14)
- TestReviewP3ImageFreshness::test_rebirth_reports_newer_candidate_digest 仍红: 模板化后重入固定模板的 born 容器不再复算 newer-available, 且换镜像被守卫拒绝; 能力在 swt.py:4700 那条路径仍在. 根因在产品面, 按停止条件未改 scripts/, 待用户裁决.
