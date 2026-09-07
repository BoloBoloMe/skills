# ISSUE-09 swt switch: 换活动母体 (独立危险入口)

## 父级

- `../roadmap/MILESTONE-12.md`; `../EXECUTION-M12.md`
- `../DECISIONS.md`: D010 (原子序/不变量), D026 (收据含目标分支+全部受影响容器), D028 (独立入口不做聪明), D033 (旧容器 retired), D029 (脏检查口径复用)
- `../UNAUTHORIZED_DECISIONS.md`: U-005 (目标母体不存在两路)
- 前置 ISSUE-08 (脏检查/停容器实现复用)

## 执行(Execution)

- [x] 已实现

## 要构建什么

`swt switch --repo <主仓> --to <目标分支名原文> [--force]`:

1. 前置: 主仓存在; `--to` slug 化后 ≠ 当前活动母体 (相同 → exit 2); 无活动母体 → exit 2 指引直接 birth (switch 无对象).
2. 脏检查: 对旧母体**全部**容器逐个按 D029 口径 → 任一脏 → exit 1 DECIDE (kind=`switch-dirty`, 逐容器列明细; 收据指纹含全部受影响容器 podman-id 清单 + 各脏计数 + 目标分支); `--force` 重跑 → 重查比对.
3. 原子序 (D010): 停旧母体全部容器 (`podman stop`, 不删) → 收全部 daemon → nft remove 逐容器 → 校验目标 (U-005: ref 存在则查工作区干净, 脏 → exit 3 PARTIAL 人工路径; 不存在则直接换) → 改主仓 config hideRefs/uploadpack.hideRefs 例外分支为 `<新slug>` (只改例外行, 其余键不动; 改后 `--get-all` 断言恰为新例外) → runtime: 旧母体全部容器标 `retired:true` (D033), 授权母体字段换为新 slug, stage 更新 → STATE.
4. 失败清理: 停旧之后改例外之前失败 → exit 3 PARTIAL "授权域空窗", 文案列唯一恢复路径 (重跑 switch 或对旧母体 birth); --force 已答决策记 runtime, 重跑不再问 (D026 已答不重问).
5. 不做: 不删旧母体/旧容器; 不建新容器 (新区走 birth).

## 允许范围

- 修改 `swt.py`, `tests/test_swt_m12.py`; 本 ISSUE 文件
- /tmp 夹具; 测试现场经 swt birth 搭建

## 禁止范围

- 禁止删旧母体/旧容器 (存删用户自决, D012); 禁止自动建新容器
- 禁止脏检查未过动任何容器 (无 --force 时)
- EXECUTION-M12 全局禁止范围全部适用

## TDD 切片

- TS-401 主链 (目标母体已存在): birth 母体 A → host 侧另建干净母体 B worktree → switch --to B 原文 → exit 0; 外部断言: A 容器全 stopped 且仍在 (`podman ps -a`), A daemon 灭, nft 无 A 容器 saddr, config 例外 = B-slug (`--get-all` 独立断言), runtime 授权=B 且 A 容器 retired=true, STATE 如实.
- TS-402 目标母体不存在 (U-005): switch --to 新名 → exit 0, 例外指向新 slug, STATE target-mother-exists=false; 随后 birth 该名全链走通 (与 ISSUE-07 复用判定咬合).
- TS-403 脏阻塞: A 容器有未 push → switch exit 1 DECIDE 逐容器明细, 任何容器/config 未动; push 后重跑 exit 0.
- TS-404 --force: 脏 → DECIDE → --force → 成功且 audit.jsonl 登记; 收据一次性.
- TS-405 retired 可见: switch 后 status 列 A 容器 retired; A 容器 terminate (唯一出路) 仍走正常脏检查走通.
- TS-406 中途失败: 故障注入改 hideRefs 失败 (如预写冲突多值) → exit 3 PARTIAL 空窗文案含恢复路径; runtime 标记空窗; 重跑 switch 收敛.
- TS-407 前置: 无活动母体 → exit 2; --to = 当前活动母体 → exit 2.
- TS-408 多容器: A 母体两容器 → switch 全停全标 retired, 脏检查逐容器, 缺一脏即阻塞.

## 验证入口

`uv run --with pytest pytest tests/test_swt_m12.py` 全绿.

## 停止条件

需要改 D010/D028/D033 语义时停止上报.
