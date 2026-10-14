# 测试分层与改动面映射 (MILESTONE-15/16)

## 默认入口: tests/run

**小改不再付全量** — `tests/run` 按 git 未提交改动面选跑受影响套件:

- `tests/run` — 改动面选跑 (m12 自动并行 -n 12, ~40s; 其他套件串行)
- `tests/run --fast` — 只跑受影响套件的快层 (秒级)
- `tests/run --all` — 全量串行回归 (里程碑关账口径)
- `tests/run <pytest 参数>` — 原样直通

## 两层跑法

- **快层**: 纯逻辑/mock/轻量子进程用例. 命令:
  `uv run --with pytest pytest -m "not e2e" -q`
  swt 核心套件 (m04/m07/m09/m12) 的快层合计秒级; 全仓快层约 110s
  (大头是 mailbox 真回环服务套件 ~52s 与 present 套件).
- **慢层 (e2e)**: 真实重外部资源用例 — 真容器 birth / 真镜像构建 (chromium 下载) /
  真 nft/netns. 按下方映射选跑, 不全量. m12 真容器前置条件见
  「m12 真容器前置条件」节. 命令:
  `uv run --with pytest pytest -m e2e -q tests/test_swt_mXX.py`
- **里程碑关账**: 全量回归 `tests/run --all` (两层都跑, 串行).

## e2e 归层规则 (tests/conftest.py 实施)

满足任一即 e2e, 新用例按此自我归类:

1. 类名以 `E2E` 结尾 (m07/m09 约定);
2. 继承链含 `SwtBirthFixture` (m12 真 birth);
3. 显式表 `_E2E_CLASS_TABLE` (类名不含 E2E 但创建真实重外部资源:
   m04 的 netns/nft/pasta 类, m12 的 TestTS004Containers/TestS2ContainerDirty).

判据一句话: 创建真实容器/镜像/netns/nft 即 e2e; fake 边界 (fake run/fake bin/
mock env) 与纯函数归快层.

## 改动面 → 必跑套件映射

| 改动面 | 必跑 | 层级 |
| --- | --- | --- |
| `scripts/swt.py` (birth/resume/status/terminate/switch 生命周期) | test_swt_m12.py + test_swt_llm_select_mount.py | e2e 全量 + 快层 |
| `scripts/net-firewall.py` (nft 黑/白名单) | test_swt_m04.py | e2e |
| `scripts/image-prep.py` (镜像制备 build-base/match/build) | test_swt_m07.py | e2e |
| `scripts/swt-display.py` (登录墙/swt-vnc/noVNC) | test_swt_m09.py | e2e |
| `mailbox/scripts/mailbox.py` (信箱, 独立 skill) | test_mailbox_*.py | 快层 (真回环, 秒级) |
| 展示链交付/双 URL (birth 输出侧) | test_swt_web_access.py + test_swt_m08_*.py | 快层 |
| `general/present/scripts/` | general/present/tests/ | 快层 |

红线 (D036): 断言真实外部状态, 不靠 mock 替代系统行为. 分层只动跑法与夹具组织,
不降低证据等级; 快层用例的 fake 边界是被测系统之外的接缝 (如 podman 不存在于
该用例假设的环境), 不是把系统行为 mock 掉.

## m12 真容器前置条件 (E2E-ISSUE-02)

- 镜像 `localhost/swt-m03:latest` 须带 agent-template 契约 2
  (label `run.sandbox-worktree.agent-template-contract=2`); 只需镜像, 不需要真
  模板/真 Key/真网关.
- 夹具 `SwtFixture.setUp` 自动拉起 `FakeAgentTemplate`
  (`tests/fixtures/agent_template_harness.py`): 临时模板根 + 假模板 (名
  `fixture-gateway`) + 假 Key (600 临时文件) + 本机模拟网关 (随机空闲端口,
  绑 0.0.0.0). 模板根经 `SWT_AGENT_TEMPLATES_DIR` 交给 swt 子进程; 退出时
  关网关/删临时根. 真容器 `--agent-template fixture-gateway` 由 `run_swt`
  自动补上, 既有 DECIDE 用例不受影响 (hostname/network-mode 照旧会出 DECIDE).
- 与宿主桌面解耦: 夹具默认把 `WAYLAND_DISPLAY=wayland-absent` 写进 swt 子进程
  (以及测试进程) 环境, 使 `swt.py host_wayland_socket()` 返回 None, 不再受宿主
  socket 权限 0775 影响. 确需真桌面直通的用例设 `SWT_TEST_ALLOW_HOST_DISPLAY=1`
  回到真实值 (默认不设).
- SSH: 夹具起 swt 子进程与 ssh_run 一律清掉 `SSH_AUTH_SOCK` 并加
  `IdentitiesOnly=yes`; 宿主 agent 注入过多密钥会触发 ssh
  "Too many authentication failures" 使容器 clone 失败.

## m12 跑法 (E2E-ISSUE-02 改串行, 原 MILESTONE-16 并行)

E2E-ISSUE-02 后 m12 真 birth 要走容器内客户端检查 (pi/codex/kimi, 单个 45s 超时)
与假网关; 并行时多容器抢资源会出现客户端检查超时/网关不可达, 且 6080 竞态下
夹具 birth 重试会撞新模板 guard ("容器 ID 与创建记录不同"). 故 `tests/run`
选中 m12 时改为**串行** (原 -n 12, ~40s; 现 ~9min). 需要并行试跑时手动:
`uv run --with pytest --with pytest-xdist pytest tests/test_swt_m12.py -n 4 -q`
(实测 -n 4 仍有上述两类偶发; 串行是唯一稳定口径)
(里程碑关账全量回归仍走串行: `tests/run --all`)

并行安全前提 (保留, 新用例仍须遵守):

- 容器名必须带夹具后缀 (`-{self.root.name[-6:]}`); birth 缺省 --name 由夹具按
  分支+后缀自动派生, 禁止硬编码固定容器名.
- 6080 是全局唯一偏好端口: 常规用例不得断言必须拿到 6080. 验证偏好用 TS201 的
  采样断言模式, 验证回落用 TS210 的重试构造模式.
- swt 探 6080 与 pasta 绑定间存在产品级 TOCTOU 竞态: birth/resume 的 6080 竞态
  PARTIAL 由夹具 `_invoke_swt` 自动消化 (birth rm 重建 / resume 重开收据重试),
  新用例不要自行断言这两类竞态 PARTIAL 的形态; ts508 类自造端口冲突断言不受
  影响 (端口非 6080).
- 会话级兜底 (conftest sessionfinish) 清理 swt-m12-test-* 孤儿进程 (git daemon/
  socat 桥) 与会话内新建匿名卷; 跨轮泄漏用 `podman volume ls` / `pgrep -af 'git
  daemon.*swt-m12-tes[t]'` 核查.

## m12 已知事项

- 用例类一律继承 `SwtBirthFixture`, 禁止继承 `TestTS201BirthChain`
  (继承会原样重跑其 birth 链大用例; M15 已清除 17 份此类重复).
- M15 基线轮的 TestMultiPairIsolation flake (BadStatusLine 读 ssh banner) 根因
  已修 (M16, swt identity_probe 容忍非 HTTP 应答, U-018).
- E2E-ISSUE-02 遗留 1 项红: `TestReviewP3ImageFreshness.
  test_rebirth_reports_newer_candidate_digest`. 根因在产品面 (不在夹具): 模板
  birth 重入在 stage=born 时提前返回 `已就绪 (固定模板未重装)`, 不再调
  `mark_newer_available`, 故 STATE.image.newer-available 恒 false; 且模板创建
  已把镜像 digest 固定, "重入换镜像" 被拒. 未改产品代码, 留待裁决.
