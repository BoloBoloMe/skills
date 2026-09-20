# 测试分层与改动面映射 (MILESTONE-15)

## 两层跑法

- **快层** (每次改动都跑): 纯逻辑/mock/轻量子进程用例. 命令:
  `uv run --with pytest pytest -m "not e2e" -q`
  swt 核心套件 (m04/m07/m09/m12) 的快层合计秒级; 全仓快层约 110s
  (大头是 swt-mailbox 真回环服务套件 ~52s 与 present 套件).
- **慢层 (e2e)**: 真实重外部资源用例 — 真容器 birth / 真镜像构建 (chromium 下载) /
  真 nft/netns. 按下方映射选跑, 不全量. 命令:
  `uv run --with pytest pytest -m e2e -q tests/test_swt_mXX.py`
- **里程碑关账**: 全量回归 `uv run --with pytest pytest -q` (两层都跑).

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
| `scripts/swt.py` (birth/resume/status/terminate/switch 生命周期) | test_swt_m12.py | e2e 全量 + 快层 |
| `scripts/net-firewall.py` (nft 黑/白名单) | test_swt_m04.py | e2e |
| `scripts/image-prep.py` (镜像制备 build-base/match/build) | test_swt_m07.py | e2e |
| `scripts/swt-display.py` (登录墙/swt-vnc/noVNC) | test_swt_m09.py | e2e |
| `scripts/swt-mailbox.py` (信箱) | test_swt_mailbox_*.py | 快层 (真回环, 秒级) |
| 展示链交付/双 URL (birth 输出侧) | test_swt_web_access.py + test_swt_m08_*.py | 快层 |
| `general/present/scripts/` | general/present/tests/ | 快层 |

红线 (D036): 断言真实外部状态, 不靠 mock 替代系统行为. 分层只动跑法与夹具组织,
不降低证据等级; 快层用例的 fake 边界是被测系统之外的接缝 (如 podman 不存在于
该用例假设的环境), 不是把系统行为 mock 掉.

## m12 已知事项

- 用例类一律继承 `SwtBirthFixture`, 禁止继承 `TestTS201BirthChain`
  (继承会原样重跑其 birth 链大用例; M15 已清除 17 份此类重复).
- TestMultiPairIsolation 曾见一次性 flake (ssh 端口探测撞上 HTTP 读,
  BadStatusLine), 重跑即过; 复现时留现场.
