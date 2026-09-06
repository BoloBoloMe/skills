# ISSUE-11 D036 等价矩阵收口 + e2e-smoke 退役 + TECHNICAL 字面修补

## 父级

- `../roadmap/MILESTONE-12.md` (完成判据原文)
- `../EXECUTION-M12.md` 覆盖矩阵节
- `../DECISIONS.md`: D036 (等价矩阵全绿才删 e2e-smoke; 断言独立外部状态)
- 前置 ISSUE-05..10 全部关闭

## 执行(Execution)

- [ ] 已实现

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

(实现时逐条填写: 条目 → 用例号 → 外部状态断言方式 → 结论)

## 停止条件

矩阵出现无法补齐的缺口 (swt 行为与 M03 证据无法等价) → 停止上报, e2e-smoke 保留.
