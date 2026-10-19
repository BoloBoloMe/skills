# 独立验收第 1 轮 派工计划 (PRODUCT.md confirmed-flow v1, 目标提交 5e20d11)

- 目标提交: `5e20d11c94bfbab1ebd037ac95d9e1ccacfebdb4`
- 判据来源: `docs/changes/wordcount/PRODUCT.md`, 确认标记 `<!-- confirmed-flow: v1 -->`
- 产物根目录: `docs/changes/wordcount/`
- 证据目录: `docs/changes/wordcount/verify/round-1/` (新建, 不覆盖旧证据)
- 记录时间: 2026-10-20T01:58:49+08:00

## 必验清单 (3 条)

| 编号 | 原文出处 | 内容摘要 |
| --- | --- | --- |
| AC-001-1 | 验收标准 / `@AC-001 @normal @G-001` | `printf 'alpha beta gamma\n' \| bin/wordcount` 输出 `3`, 退出码 0 |
| AC-002-1 | 验收标准 / `@AC-002 @normal @G-002` | 前提 `samples/notes.txt` 内容为 `alpha beta` 加一个换行; `bin/wordcount --file samples/notes.txt` 输出 `2`, 退出码 0 |
| BR-001 | 业务规则 (审计) | 既有测试 `tests/run.sh` 不得被改动 |

## 影响判断 (第 3 步)

- 仓库无构建脚本, 无 CI 配置, 无测试发现机制: `tests/run.sh` 与 `tests/cli_errors_test.sh` 都是写死命令的 shell 脚本, 不会扫描 `docs/`.
- 结论: 证据目录放在仓库内 `docs/changes/wordcount/verify/round-1/` 不会进入构建或测试发现; 不需要外置.
- 本轮期间 PRODUCT.md 与源码均无变化, 报告覆盖 PRODUCT.md v1 与提交 `5e20d11`.

## 分组与人数 (第 4 步)

| 组 | 承接标准 | 方法 | 阶段 |
| --- | --- | --- | --- |
| G1 运行行为 | AC-001-1, AC-002-1 | 直接执行 PRODUCT.md 里写明的两条命令 | 只读, 并行 |
| G2 静态材料审计 | BR-001 | 比对 `tests/run.sh` 的仓库历史与工作区状态 | 只读, 并行 |

- 资源: G1 占用产品入口 `bin/wordcount` 与 `samples/notes.txt` (只读运行); G2 只读 `.git` 对象与文件内容. 无共享实例, 无端口, 无数据目录.
- 共用准备: 无. 本仓库无构建步骤, 无服务启动, 无 fixture 生成, 因此不存在"重复准备成本".
- 写入片段: 无. 两条场景与一条审计规则都是只读操作, 不存在争用, 两组同时开工, 不需要先后顺序.
- 并行收益: 两组方法不同 (运行 vs 历史比对), 可同时开工, 墙钟时间减半; 更重要的是 G2 需要独立判断"既有"基准点, 与运行结论分属不同判断, 放同一会话会削弱独立性.
- 可用非作者验收者: 本轮新开 2 个 (见报告派工记录). 计划人数 2 = 组数 2 = 可用人数 2.
- 未采用的方案: 不按 AC 逐条开会话 (AC-001-1 与 AC-002-1 是同一个入口的同一份准备, 拆开无收益).
- 需要 benchmark-checklist / blast-radius 吗: 不需要. 必验项里没有性能结论, 也没有依赖"删除后数据仍可读"这类安全假设的判定, 因此派工单不安排这两项方法.

## 材料来源 (第 4, 8 步)

| 编号 | 材料来源 | 说明 |
| --- | --- | --- |
| AC-001-1 | 本轮实跑 (当前观察) | 旧材料只有 `review/round-4.md` 的一句摘要, 无可读原件, 按第 8 步不算充分证据, 不引用 |
| AC-002-1 | 本轮实跑 (当前观察) | 同上 |
| BR-001 | 本轮静态核对 (当前观察, 静态材料) | 旧材料没有对 `tests/run.sh` 的比对原件 |

## 写入授权 (第 5 步)

- 本轮必验项均为只读: 读标准输入, 读 `samples/notes.txt`, 读 git 对象. 不创建测试资源, 不写产品文件, 不需要用户批准.
- 允许的唯一写入: 验收者在 `docs/changes/wordcount/verify/round-1/` 下新增自己的原始材料与结论文件.
- 越界即停: 验收者若需要在该目录外写入任何东西才能构造场景, 停下报告, 由指挥者请示, 不擅自扩权.

## 原始材料归属

- G1: `docs/changes/wordcount/verify/round-1/g1-ac.5e20d11.*` (结论 md + 命令原始输出 log), 产生者 = G1 验收者会话.
- G2: `docs/changes/wordcount/verify/round-1/g2-br001.5e20d11.*`, 产生者 = G2 验收者会话.
- 指挥者侧: 本文件, `dispatch-g1.*`, `dispatch-g2.*`, 会话记录 `session-g1.*`, `session-g2.*`, 汇总 `report.md`.
