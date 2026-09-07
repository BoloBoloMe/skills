# ISSUE-11 D036 等价矩阵收口 + e2e-smoke 退役 + TECHNICAL 字面修补

## 父级

- `../roadmap/MILESTONE-12.md` (完成判据原文)
- `../EXECUTION-M12.md` 覆盖矩阵节
- `../DECISIONS.md`: D036 (等价矩阵全绿才删 e2e-smoke; 断言独立外部状态)
- 前置 ISSUE-05..10 全部关闭

## 执行(Execution)

- [x] 已实现

## 要构建什么

1. **等价矩阵终审**: 逐条核对 EXECUTION-M12 覆盖矩阵 13 条在 `tests/test_swt_m12.py` 的落点, 缺漏补测; 抽样复核断言确实打在独立外部状态 (`git config --get-all` / `podman ps` / `nft list table` / 母体文件内容), 不只信 STATE. 矩阵核对结果逐条写进产物段 (本文件"等价矩阵核对"节).
2. **e2e-smoke 退役**: 删 `workflow/use-sandbox-worktree/scripts/e2e-smoke.py` 与 `tests/test_swt_m03.py` (D036 授权, 矩阵全绿为前提).
3. **TECHNICAL.md 字面修补** (M03 遗留缺口 (2)(3), M11 指定 M12 顺手处理):
   - 缺口 (2): 运行时 JSON container 段为 schema 超集 (ssh_private_key/ssh_host/daemon_addr/clone_dir/remote 等实际字段), TECHNICAL.md 接口契约节补记实际超集并注明 "已随 swt 退役, 文档存档用途".
   - 缺口 (3): 测试运行命令 `uv run pytest` 改为实际的 `uv run --with pytest pytest`.
   - 注意: TECHNICAL.md 是 M03 历史 spec, 只字面修补以上两处, 不改写其他内容.
4. 全量回归: `tests/test_swt_m04.py` / `test_swt_m07.py` / `test_swt_m09.py` / `test_swt_m12.py` 全绿 (m09 跑不动重镜像时记录原因, 不静默 skip 的原则适用于新测试; 回归允许按各文件原样执行).

## 允许范围

- 删 `e2e-smoke.py`, `tests/test_swt_m03.py`
- 改 `tests/test_swt_m12.py` (补漏), `docs/changes/use-sandbox-worktree/TECHNICAL.md` (上述两处), 本 ISSUE 文件
- 必要时小改 `swt.py` (仅限补测暴露的契约偏差修复)

## 禁止范围

- 矩阵未全绿时禁止删 e2e-smoke (D036 明文)
- 禁止借机重写 TECHNICAL.md 其他章节
- EXECUTION-M12 全局禁止范围全部适用

## TDD 切片

- TS-111 矩阵逐条核对记录 (无新代码, 核对表入本文件).
- TS-112 补缺用例 (若核对发现缺口).
- TS-113 删除后回归: m04/m07/m12 全绿; 仓库无 e2e-smoke 残留引用 (`grep -r e2e-smoke` 仅剩文档历史).

## 验证入口

`uv run --with pytest pytest tests/test_swt_m04.py tests/test_swt_m07.py tests/test_swt_m12.py` 全绿.

## 等价矩阵核对

- 拒绝矩阵 (新分支/tag/non-ff/删除) → `TestTS203RejectMatrix.test_new_branch_tag_non_ff_and_delete_are_remote_rejected` → 容器内 push 结果检查 `[remote rejected]`, 主仓 `git show-ref` 确认新 ref/tag 未落地 → 通过.
- 母体脏树拒收 → `TestTS204DirtyMother.test_dirty_tracked_mother_tree_rejects_push_and_restores` → 母体 `README.md` 外部文件内容制造脏改动, SSH push 检查拒绝, 再检查文件恢复 → 通过.
- daemon 不带 `--export-all` → `TestTS201BirthChain.test_birth_decides_then_builds_complete_chain` → 读取 daemon `/proc/<pid>/cmdline`, 同时核对 `base-path` → 通过.
- config 校验先于 daemon 启动 → `TestTS205ConfigFault.test_wrong_scalar_and_duplicate_multivalue_are_not_overwritten` → `git config --get-all` 确认错误值原样保留, `pgrep` 确认对应 srv 根无 daemon, records 确认无 runtime → 通过.
- clone 检出母体分支 → `TestTS201BirthChain.test_birth_decides_then_builds_complete_chain` → SSH 执行容器内 `git ... branch --show-current`, 与 STATE 母体分支比对 → 通过.
- push 回流落地 → `TestTS202PushLands.test_container_commit_push_lands_in_mother` → 容器 commit/push 后直接读取母体目录文件内容 → 通过.
- D008 多值 config 既有值/错值/幂等重跑 → `TestTS205ConfigFault.test_wrong_scalar_and_duplicate_multivalue_are_not_overwritten` + `TestTS206ConfigIdempotence.test_rebirth_reuses_config_without_duplicate_values` → 主仓两组 `git config --get-all` 检查错误值不覆盖, 重跑后检查值数量与去重及 daemon PID 不变 → 通过.
- ssh 不可达与已停容器视同脏 → `TestTS301Terminate.test_stopped_container_is_unknown_dirty_then_force_removes_it` + `test_ssh_unreachable_container_is_unknown_dirty` → 外部 `podman stop`/删除 authorized_keys 制造状态, terminate 检查 DECIDE, 强拆后 `podman` 检查容器消失 → 通过.
- 强拆审计登记 → `TestTS301Terminate.test_force_writes_audit_snapshot_and_consumes_receipt` → 读取 records 下外部 `audit.jsonl`, 核对 decision id, Podman ID 和脏计数, 决策文件已消费 → 通过.
- 中途清理与重复 birth (重入状态机) → `TestTS211Partial.test_port_start_failure_leaves_runtime_and_second_birth_converges` + `TestTS301Terminate.test_missing_container_with_daemon_residue_converges` → 端口故障后读取 runtime 并重复 birth 收敛, 删除容器后用 `pgrep` 确认 daemon 清理, stage 为 idle → 通过.
- 多容器共享母体互不影响的 resume/terminate/nft → `TestTS210NftMerge.test_second_container_merge_keeps_both_source_rules` + `TestTS301Terminate.test_multiple_containers_require_name_and_remove_only_selected_network_rule` + `TestTS5Resume.test_ts507_resume_merge_preserves_sibling_network_rule` → nft `list table inet swt` 逐源地址核对, `podman inspect` 确认兄弟容器仍在, resume 后两条规则均保留 → 通过.
- switch 中途失败与旧容器 retired → `TestTS406SwitchPartial.test_config_failure_reports_authorization_gap_and_rerun_converges` + `TestTS401SwitchExistingMother.test_switches_to_existing_clean_mother_and_retires_old_container` → 故障后外部 `podman inspect`/`pgrep`/`git config --get-all` 核对半状态, 正常切换后外部容器为 exited 且 runtime 记录 retired → 通过.
- 收据指纹比对/一次性/状态漂移重问 (D026) → `TestTS006Receipts.test_receipt_is_fingerprinted_consumable_and_one_shot` + `TestTS208DecisionReceipts.test_decisions_are_all_listed_and_config_drift_reopens_them` + `TestTS301Terminate.test_dirty_fingerprint_drift_reopens_decision` + `TestTS5Resume.test_ts502_resume_receipt_reopens_for_recreated_podman_id` → 读取 records 下决策 JSON 检查指纹漂移不消费, 消费后删除, config/脏计数/Podman ID 漂移生成新收据 → 通过.

核对结论: 13/13 条均已在 `tests/test_swt_m12.py` 有落点; 关键结果均通过 `git config --get-all`, `podman ps`/`inspect`, daemon `/proc`/`pgrep`, nft 表, 母体文件内容或 records 磁盘文件独立复核, 不只依赖 STATE. 无需修改 `swt.py`.

## 停止条件

矩阵出现无法补齐的缺口 (swt 行为与 M03 证据无法等价) → 停止上报, e2e-smoke 保留.
