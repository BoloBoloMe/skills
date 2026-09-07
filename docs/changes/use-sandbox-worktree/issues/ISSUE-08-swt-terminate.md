# ISSUE-08 swt terminate: 按容器终结 + 脏检查 + 审计

## 父级

- `../roadmap/MILESTONE-12.md`; `../EXECUTION-M12.md`
- `../DECISIONS.md`: D012 (脏阻塞+母体自决), D026 (收据), D028 (--force 独立+先审计), D029 (按容器粒度+脏口径+TOCTOU), D031 (多容器), D032 (nft remove)
- `../UNAUTHORIZED_DECISIONS.md`: U-002/U-003 (audit.jsonl)/U-008
- 前置 ISSUE-07 (birth 供测试搭现场), ISSUE-06 (remove)

## 执行(Execution)

- [x] 已实现

## 要构建什么

`swt terminate --repo <主仓> [--name <容器名>] [--force]`:

1. 前置: 容器存在 (无 → exit 2); `--name` 缺省 = 该母体唯一容器, 多容器缺省 → exit 2 列候选 (D029).
2. 脏检查 (D029 口径): ssh 可达 → 容器内 `git status --porcelain` (含未跟踪) + 容器 HEAD vs 主仓 `refs/heads/<母体分支>` 的 `merge-base --is-ancestor` 双向判定 (纯 behind 不算脏; ahead/diverged 算脏); ssh 不可达/容器已停 → unknown **视同脏**; STATE/DECIDE 文案给 ahead/behind/diverged 关系与计数.
3. 脏 → exit 1 DECIDE (kind=`terminate-dirty`, 收据指纹含容器 podman-id + 脏计数, D026); DECIDE 文案要求用户确认容器内 agent 已停手 (TOCTOU 残余, D029); `--force` 重跑 → 重查脏比对指纹, 变了重新 DECIDE.
4. `--force` 执行前写 audit.jsonl (判决快照: 时间/容器/podman-id/脏概要/decision-id, D028).
5. 成功: `podman rm -f` → kill 该容器 daemon (runtime 记录 PID + 兜底 pgrep 发现) → net-firewall `remove --container-ip` → runtime 清除该容器段 (最后一个容器 → 母体级资源仅闲置, runtime 保留母体/config 记录, stage 回 idle) → STATE 注明母体保留路径. 主仓 config 不动.
6. 幂等: 部分残留 (容器已灭 daemon 还在等) 重跑收敛, 不报错于 "已不存在".

## 允许范围

- 修改 `swt.py`, `tests/test_swt_m12.py`; 本 ISSUE 文件
- /tmp 夹具与 records-root; 测试现场经 swt birth 搭建

## 禁止范围

- 绝不删母体目录/ref; 无 --force 绝不碰脏容器; 不动主仓 config
- 多容器时禁止按母体一次拆光 (D029)
- 禁 clear+apply (D032)

## TDD 切片

- TS-301 干净终结: birth → 容器内 push 干净 → terminate → exit 0; 外部断言: 容器灭 (`podman ps -a`), daemon 灭 (pgrep), nft 表无该 saddr (单容器 → 整表消失), 母体目录与 ref 留存, runtime 无该容器段, STATE 含母体路径.
- TS-302 脏阻塞: 容器内未 commit 改动 (含未跟踪文件) → terminate exit 1 DECIDE 列脏明细; 容器/daemon/nft 全保留.
- TS-303 未 push commit: 容器内 commit 不 push → DECIDE 计数正确 (ahead N); 容器内 push 后重跑 terminate → exit 0.
- TS-304 behind 不算脏: 母体经 host 侧推进 (模拟 host 在主仓操作使母体 ref 超前容器 HEAD) → terminate exit 0 无 DECIDE.
- TS-305 diverged 算脏: 两侧各有提交 → DECIDE relation=diverged.
- TS-306 已停容器视同脏: `podman stop` 后 terminate → exit 1 DECIDE unknown 视同脏; --force 后成功.
- TS-307 ssh 不可达视同脏: running 但断 ssh (删 authorized_keys) → DECIDE.
- TS-308 --force 审计: audit.jsonl 追加一行含时间/容器/podman-id/脏概要/decision-id; 收据消费不可复用 (再次 --force 需新 DECIDE).
- TS-309 指纹漂移: DECIDE 后容器内再制造改动 → --force 重跑 → 重查发现脏计数变 → 重新 DECIDE (旧答案不套新状态, D026).
- TS-310 多容器: 同母体两容器 → terminate --name 其一 → 兄弟容器/daemon/nft 规则不受影响 (nft 表内兄弟 saddr 原样在); 缺省 --name → exit 2 列候选.
- TS-311 幂等重入: 杀进程模拟中途崩 (容器已 rm daemon 残留) → 重跑 terminate 收敛 exit 0.
- TS-312 最后一个容器终结后母体闲置: runtime 母体/config 记录保留, stage 非 born; status 可见.

## 验证入口

`uv run --with pytest pytest tests/test_swt_m12.py` 全绿.

## 停止条件

需要改 D012/D028/D029 语义时停止上报.

## 复核补钉 (评审后总指挥裁决, 详见 UNAUTHORIZED_DECISIONS U-010..U-012)

- daemon 为主仓级共享, terminate 仅最后容器收 (本文件第 5 步字面随之修订).
- 执行顺序实为 nft remove → rm → 收 daemon (先断网再删).
- 脏检查 fetch 走 `refs/swt-probe/mother` 暂存命名空间, 不动容器 origin/<branch> (status 只读性保全).
