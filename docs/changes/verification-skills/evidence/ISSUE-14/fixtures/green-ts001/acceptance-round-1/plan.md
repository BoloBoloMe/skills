# verify-change 派工计划 (round-1)

- 目标提交: b519339db7d0d1ec723aef311fef7d17f2810bce (main, `git rev-parse HEAD` 核对一致)
- 判据来源: `docs/changes/wordcount/PRODUCT.md`, `验收标准` 节带 `<!-- confirmed-flow: v1 -->`
- 产物根: `docs/changes/wordcount/`
- 本轮证据目录: `docs/changes/wordcount/verify/round-1/` (新建, 无旧证据覆盖)

## 第 3 步: 证据目录影响判断

仓库内文件清单 (git ls-files): 只有 `bin/wordcount`, `samples/notes.txt`, `tests/run.sh`, `README.md`, `docs/**`, `.agents/skills/**`. 没有 Makefile, 构建脚本, CI 配置, 包管理清单, 也没有会扫描 `docs/` 的测试发现机制; `tests/run.sh` 只按固定路径调用 `bin/wordcount` 与 `samples/notes.txt`.
结论: 写入 `docs/changes/wordcount/verify/round-1/` 不会进入构建, 测试发现或运行输入, 证据可留在仓库内. 该目录只新增验收输出.

## 第 1 步: 必验清单 (3 条)

| 编号 | 来源 | 判据原文要点 |
| --- | --- | --- |
| AC-001-1 | 验收标准 @AC-001 @normal @G-001 | `printf 'alpha beta gamma\n' \| bin/wordcount` 输出 `3`, 退出码 0 |
| AC-002-1 | 验收标准 @AC-002 @normal @G-002 | `bin/wordcount --file samples/notes.txt` 输出 `2`, 退出码 0; `samples/notes.txt` 内容为 `alpha beta` 加一个换行 |
| BR-001 | 业务规则 (审计) | 既有测试 `tests/run.sh` 不得被改动 |

## 第 4 步: 分组与人数

- 分组: 单一场景组 G-1, 承接 AC-001-1, AC-002-1, BR-001 全部 3 条. 3 条都无法再拆成互不争用资源的组: 全部落在同一仓库, 同一 `bin/wordcount`, 同一 `samples/notes.txt`, 同一 `tests/run.sh`, 拆开只重复同一份准备 (同一工作区, 同一版本核对), 无并行收益.
- 组间资源: 唯一可隔离维度是场景本身, 但两条 AC 各只需一条命令, 同仓同入口, 不构成独立实例/端口/数据目录, 按技能"拆开后仍互相占用同一份资源时只派一人"处理.
- 可用非作者人数: 本轮可新开验收者数量充足 (herdr 内可开新 tab), 但按收益只派 1 人.
- 计划人数: 1 人 (验收者 `acc-wc-1-1`, tab `S-acc-wc-1-1`).
- 共用准备: 由该验收者一人完成 (核对 HEAD, 工作区状态, `tests/run.sh` 与样例内容), 不做重复准备.
- 原始材料归属: 该验收者; 写入 `docs/changes/wordcount/verify/round-1/` 下.
- 争用写入片段: 无. 本轮全部为只读检查 (命令只读执行产品入口与 git 查询), 不需要写测试资源.
- 方法技能: AC-001-1/AC-002-1 是功能正确性, 无性能结论需求, 不含未证实的删除类安全假设, 不安排 benchmark-checklist / blast-radius.

## 材料来源分配

| 编号 | 材料来源 | 说明 |
| --- | --- | --- |
| AC-001-1 | 本轮实跑 | 无适用的旧观察 (review/round-1.md 是代码评审结论, 非产品验收观察) |
| AC-002-1 | 本轮实跑 | 同上 |
| BR-001 | 本轮静态核对 | `tests/run.sh` 历史比对; 静态材料结果, 不是运行行为结果 |

## 第 5 步: 写入授权

- 需要写测试资源的项: 无. AC-001-1/AC-002-1 用仓库已有 `samples/notes.txt`, BR-001 为静态比对, 均不新建/修改测试资源, 因此不需要向用户申请写入批准.
- 允许的写入: 仅 `docs/changes/wordcount/verify/round-1/` 下的验收输出文件.
- 禁止: 改产品代码, `bin/`, `tests/`, `samples/`, `docs/changes/wordcount/PRODUCT.md`, `EXECUTION.md`, `issues/`; 禁止 git commit/push/merge.

## 第 6 步: 派工

- 验收者: `acc-wc-1-1` (pi, `--model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high -a`, cwd `/tmp/orchestra-14/ts001-green`)
- 未参与事实: 会话创建时间晚于全部实现/修复/合并提交 (beb0ebf, 4187edb, 720db42 均 2026-10-20 00:49:43; 目标提交 b519339 01:06:36); 不继承实现会话; 操作记录只含验收命令.
- 每组开始/结束时间由该验收者自记, 指挥者核对.
