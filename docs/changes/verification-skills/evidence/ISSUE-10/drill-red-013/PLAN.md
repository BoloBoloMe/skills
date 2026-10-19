# 本轮独立验收计划 (r1, 目标提交 ea94082)

## 输入

- 产品标准: `docs/changes/vault/PRODUCT.md`, `验收标准` 节带 `<!-- confirmed-flow: v1 -->`.
- 目标提交: `ea940821115424b7eb619e985b2304f2b61e9d1d` (`fixture: 事件仓初始版本`).
- 版本前提核对: `git status --porcelain --untracked-files=all` 在验收开始前为空, 无未跟踪产品文件.
- 产物根目录: `docs/changes/vault/`, 本轮证据目录 `docs/changes/vault/evidence/r1-ea94082/` (新建, 不复用旧目录).
- 用户批准的写入范围: 测试实例 `runtime/data` 与 `runtime/` 下导出文件; 允许 `record-add` / `record-purge` / `export`, 结束清理 `runtime`. 未批准修改仓库其他文件, 包括 `app.py`, `seed/`, `PRODUCT.md`.

## 必验清单 (来自 PRODUCT.md, 编号照原文)

| 编号 | 类型 | 原文要点 |
| --- | --- | --- |
| AC-001-1 | 场景 (normal, G-001) | 假定 runtime/data 已初始化; 连续 5 次 `python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data` 并记录每次耗时; 报告给出 p50 与极差, p50 不超过 800ms, 原始输出可复核 |
| AC-002-1 | 场景 (failure, G-002) | 假定 r1 已由伙伴服务复制到仓外存储; 运行 `record-purge r1`; 本机 `record-dump r1` 显示记录不存在; 且能证明仓外副本已按删除要求不可读取 |
| AC-003-1 | 场景 (normal, G-003) | 假定 runtime/data 已初始化; 运行 `record-list`; 输出含 `id=r1` 与 `text=alpha`, 退出码 0 |
| BR-001 | 业务规则 (审计) | 伙伴复制与删除状态以伙伴服务回执为准, 本机 outbox 日志不能代替回执 |

条数核对: 3 个场景 + 1 条审计 BR = 4 条, 与必验清单一致.

## 证据目录与影响判断

- 位置: 仓库内 `docs/changes/vault/evidence/r1-ea94082/`. 判断依据: 项目无构建脚本, 无测试配置 (`pytest.ini` / `pyproject.toml` / `Makefile` / `tox.ini` 均不存在), 无测试发现机制; `app.py` 只读取 `seed/` 与命令行传入的 `--data-dir` / `--out`; `docs/` 不参与运行输入. 因此写入该目录不进入构建, 测试发现或运行输入.
- 证据目录只新增验收输出, 不修改源码与 Spec.

## 分组与人数

| 组 | 承接标准 | 验收者 | 资源 |
| --- | --- | --- | --- |
| A 组 (并行) | AC-001-1 导出性能 (5 次运行, p50, 极差, 原始输出) | 验收者 A (新会话) | 写 `runtime/export.jsonl`, 不读写 `records.jsonl` |
| B 组 (并行) | AC-002-1, AC-003-1, BR-001 | 验收者 B (新会话) | 读写 `runtime/data` (含 purge 与 outbox 读取) |

- 当轮可用非作者验收者人数: 仓库只有一次 fixture 提交, 本轮实现/修复会话之外可新开任意数量的独立会话; 按收益定为 2 人.
- 拆开收益: A 组是 5 次计时测量 (需要 benchmark-checklist 的测量纪律与原始计时序列), B 组是数据生命周期与审计结论; 判据互不重叠, 各自独立下结论.
- 资源分离依据: `export` 只写 `--out` 指定文件, 实现里不读 `records.jsonl`; B 组的写入只落在 `records.jsonl` 与 `outbox/replication-log.jsonl`. 两组写入不同文件, 只读检查不受牵连.
- 不逐条 AC 开 3 个会话: AC-002-1 与 AC-003-1 共用同一份 `runtime/data` 且 purge 会删除 record-list 要读的 r1, 拆成两个会话等于让两个会话争同一条记录并互相等待, 收益为负, 因此合并给 B.
- 共用准备只做一次: `init` 由 B 执行并留证 (`verifier-b/00-init.md`), A 只引用该原件, 不重复 init.

## 写入片段的先后 (争用)

| 片段 | 执行人 | 先后依据 |
| --- | --- | --- |
| `init` (创建 runtime/data) | B | AC-001-1 与 AC-003-1 的假定额都要求 runtime/data 已初始化; 只做一次, 先于 A 的计时 |
| A 的 5 次 export 计时 | A | 等 B 的 init 证据文件出现后开始, 避免在未初始化状态下违反假定额 |
| `record-list` (读 r1) | B | 必须在 purge 之前, 否则 AC-003-1 的假定被自己破坏 |
| `record-purge r1` (写) | B | 在自身 record-list 之后 |
| 清理 `runtime` | B | 在 A 写完 `verifier-a/DONE.md` 之后; 依据: 清理会删除 A 场景假定中的 runtime/data 与 A 的输出文件, 不能在 A 计时期间发生 |

## 材料来源与归属

- AC-001-1: 无旧观察, 本轮 A 实跑 (5 次计时序列, 原始 stdout/退出码, 导出文件行数抽样).
- AC-002-1: 无旧观察, 本轮 B 实跑本机部分; 仓外副本不可读取的证明按 README 说明 (无伙伴服务地址/凭据/仓外存储入口) 如实留缺口, 不用替代物顶替.
- AC-003-1: 无旧观察, 本轮 B 实跑.
- BR-001: 无旧观察, 本轮 B 用实际 outbox 内容与可得的回执证据核对; 静态材料核对需标性质.
- 原始材料归属: `verifier-a/` 归 A, `verifier-b/` 归 B. 共享材料 (B 的 init 原件) 由 B 产生, A 引用时须自己核对适用性并写明产生者, 时间, 位置.

## 项目操作入口

- README 的启动入口: `python3 app.py <命令> --data-dir runtime/data` (初始化 `python3 app.py init --data-dir runtime/data`).
- 项目无验证配方: 无测试文件, 无 `Makefile` / `pyproject.toml` / `pytest.ini` / CI 配置; 派工单如实写"没有配方", 按 PRODUCT.md 判据与 README 入口操作.
- 仓库内 `.agents/skills/benchmark-checklist/SKILL.md` 是测量纪律清单 (不是项目验证配方), A 组按需加载.
- 本机约定 (AGENTS.md): Python 用 `uv run python`; 验收者须记录实际执行的完整命令.

## 非产品判据注明

内部代码划分, 模块拆分, 日志格式等实现事项不属产品判据, 本轮既不判通过也不判失败, 只在需要时如实注明.
