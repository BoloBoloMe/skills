# ISSUE-10 swt resume: fail-closed 恢复 (带 DECIDE gate)

## 父级

- `../roadmap/MILESTONE-12.md`; `../EXECUTION-M12.md`
- `../DECISIONS.md`: D011 (fail-closed/无自动重启), D026 (收据), D030 (CLI 级 DECIDE gate + 授权母体校验), D032 (禁 clear+apply), D033 (retired 拒绝)
- `../milestone-04/MILESTONE-04-findings.md`: F-M04-02 (netns 重建规则全失 → start 后立即注入)
- 前置 ISSUE-09 (retired 写入方), ISSUE-06 (apply --merge)

## 执行(Execution)

- [x] 已实现

## 要构建什么

`swt resume --repo <主仓> [--name <容器名>] [--confirm]`:

1. 前置: runtime 存在 (无 → exit 2); 目标容器选定 (多容器 --name, 缺省唯一); 目标容器 retired → exit 2 (唯一出路 terminate, D033); runtime 记录授权母体分支 ≠ 主仓 config 当前例外 → exit 2 (D030 防错位拉起).
2. DECIDE gate (D030): 检测到可恢复对象 (exited 容器 / stale daemon / 表缺规则) → exit 1 DECIDE (kind=`resume`, 列将执行的动作清单; 收据指纹 = 容器 podman-id + 授权母体分支); `--confirm` 重跑 → 指纹比对 → 执行. 全部就绪无可恢复对象 → exit 0 幂等 no-op (不 DECIDE).
3. fail-closed 序列 (F-M04-02 修订时序): 收 stale daemon (孤儿 kill 并记录) → `podman start` 容器 → daemon 重拉 (按 runtime 记录的地址/端口策略重预选) → **start 后立即 nft 重注入** (按 runtime 登记的网络参数 apply --merge; 禁 clear+apply, D032) → daemon probe + ssh BatchMode 校验 → 校验通过前不宣告就绪 (镜像 CMD 仅 sshd 无自动负载, 顺序精神保全) → STATE 全就绪.
4. 端口: 跨 stop/start 稳定 (F006), 被占 → start 失败 exit 3 PARTIAL 透传, 不自动换.
5. 失败清理: 无破坏动作; 任一步失败 exit 3 可重入.

## 允许范围

- 修改 `swt.py`, `tests/test_swt_m12.py`; 本 ISSUE 文件
- /tmp 夹具; 测试现场经 swt birth/switch 搭建

## 禁止范围

- 禁止重建容器; 禁止动母体 ref; 禁止自动换端口
- 禁止 clear+apply 序列 (D032); 禁止 resume retired 容器
- EXECUTION-M12 全局禁止范围全部适用

## TDD 切片

- TS-501 主链: birth → `podman stop` (netns 随之拆, 规则全失) → resume → exit 1 DECIDE (列动作: 收 stale daemon/start/重注入/校验) → --confirm 重跑 → exit 0; 外部断言: 容器 running, daemon 新进程存活, nft 表含该容器规则 (重注入证据), ssh 通, 容器内 git fetch 经 daemon 通 (probe).
- TS-502 DECIDE 指纹: DECIDE 后 `podman rm`+重建同名容器 (podman-id 变) → --confirm 重跑 → 重新 DECIDE.
- TS-503 retired 拒绝: switch 走后对旧容器 resume → exit 2 文案指向 terminate.
- TS-504 授权错位: 手改 config 例外为另一分支 → resume → exit 2.
- TS-505 幂等: 全就绪时 resume → exit 0 no-op, 无 DECIDE, 无 daemon 重拉.
- TS-506 stale daemon: 手工留孤儿 daemon (kill 容器保留 daemon) → resume 先杀并记录 → 全链收敛.
- TS-507 多容器共享表: 同母体两容器, stop 其一 (表含兄弟规则) → resume 该容器 → 兄弟规则原样在 (无 clear+apply 窗口), 两容器规则共存.
- TS-508 端口被占: stop 后占位其宿主端口 → resume --confirm → start 失败 exit 3 PARTIAL 透传原生报错; 释放后重跑收敛.

## 验证入口

`uv run --with pytest pytest tests/test_swt_m12.py` 全绿.

## 停止条件

需要改 D011/D030/D032/D033 语义时停止上报.
