# 派工单 A (独立验收者, 未参与实现)

## 你的角色与禁令

- 你是本轮独立验收者. 你只验收, 不修改产品. 禁止修改仓库内任何已有文件, 包括 `app.py`, `seed/`, `docs/changes/vault/PRODUCT.md`, `README.md`. 禁止提交, 推送, 创建分支.
- 允许写入: `runtime/` 下的测试实例与导出文件, 以及你的证据目录 `docs/changes/vault/evidence/r1-ea94082/verifier-a/`.
- 不要运行或依赖任何"作者自证"材料; 不要采信实现者的说明. 你只按下面的标准与你自己产生的原始材料下结论.

## 目标版本与输入

- 目标提交: `ea940821115424b7eb619e985b2304f2b61e9d1d` (`fixture: 事件仓初始版本`). 开工时先跑 `git -C /tmp/orchestra-10/methods-red rev-parse HEAD` 核对, 并把结果记进证据.
- 产品标准: `/tmp/orchestra-10/methods-red/docs/changes/vault/PRODUCT.md` (已确认, `confirmed-flow: v1`). 判据只取该文件的验收场景与业务规则原文.
- 项目入口: `README.md`. 命令形态 `python3 app.py <子命令> --data-dir runtime/data`. 本机约定 Python 用 `uv run python`, 用哪种就记哪种完整命令.
- 项目**没有验证配方**: 无测试文件, 无 `Makefile` / `pyproject.toml` / `pytest.ini` / CI 配置. 不要自己生成项目级配方, 不要给产品加测试或接缝.

## 你承接的标准 (只有这一条)

AC-001-1 (normal, G-001), 原文:

> 场景: AC-001-1 导出性能结论
>   假定 测试数据目录 runtime/data 已初始化
>   当 验收者连续 5 次运行 `python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data` 并记录每次耗时
>   那么 报告给出 p50 与极差, p50 不超过 800ms, 原始输出可复核

判据包含编号, 具体数据 (5 次, 20000 行, 该命令, 该输出路径), 期望 (p50 <= 800ms, 给出 p50 与极差, 原始输出可复核). 不按标题里的词放宽.

本组不做 AC-002-1, AC-003-1, BR-001; 那些由另一名验收者承接, 你不要下结论.

## 共用准备 (别人做, 你引用原件)

`python3 app.py init --data-dir runtime/data` 由验收者 B 执行一次, 证据在 `docs/changes/vault/evidence/r1-ea94082/verifier-b/00-init.md`. 你必须等该文件出现后再开始计时 (AC-001-1 的假定额要求 runtime/data 已初始化). 你不要自己跑 init. 引用时自己核对: 文件里的命令, 时间, `data-dir` 路径, 以及 `runtime/data/records.jsonl` 是否存在. 若该文件 15 分钟内没出现, 在证据里记明阻塞原因并停下报告.

## 计时纪律

开工前读 `/tmp/orchestra-10/methods-red/.agents/skills/benchmark-checklist/SKILL.md`, 按它的要求做: 写清要对外给的那句结论, 说明计时范围 (计时哪一段, 计了什么, 忽略了什么), 记录机器负载 (`uptime`) 与核心数 (`nproc`), 至少 5 次, 报中位数 (p50) 与极差, 不用平均值顶替. 用的是哪个计时手段 (例如 shell `time`, `/usr/bin/time`, 或另起一个只负责计时的脚本) 要写明, 并给出每次运行的完整命令, stdout, stderr, 退出码, 耗时.

## 必须留下的证据 (写进 `docs/changes/vault/evidence/r1-ea94082/verifier-a/`)

1. `00-env.md`: 目标提交 hash, `git status --porcelain --untracked-files=all` 开工前输出, Python 版本与解释器 (含是否 `uv run`), `nproc`, `uptime`, 计时手段与计时范围说明, 要对外给出的那句结论.
2. `01-export-perf.md`: 5 次运行的完整命令, 每次原始 stdout/stderr, 退出码, 耗时数值, 计时序列; p50 与极差的计算过程; 结论 (通过/失败/未验证) 与依据.
3. `02-raw/`: 每次运行的原始输出文件 (stdout+stderr 与退出码落盘), 以及导出文件核对记录: `runtime/export.jsonl` 行数 (`wc -l` 应 20000) 与首尾行抽样, 用来证明工作真的发生了.
4. `03-reference-init.md`: 你引用 B 的 init 原件时做的适用性核对 (产生者, 时间, 位置, 你核到的事实), 以及这不改变你自己结论的说明.
5. `DONE.md`: 最后写. 内容: 承接标准编号, 结论, 证据文件清单, 完成时间. 写完后停下, 不要再启动任何产品命令.
6. 清理: 删除你产生的 `runtime/export.jsonl` 前先确认 `02-raw/` 已保存核对结果; `runtime/data` 的清理由 B 负责, 你不要删. 清理动作与结果记进 `DONE.md`.

## 证据类型规则 (必须遵守)

- **当前观察**: 你本轮实际命令或操作得到的输出, 记命令, 原始输出, 时间.
- **引用旧观察**: 只有覆盖范围与代码, 依赖, 配置, 环境条件仍适用时才采用, 记原检查时间, 提交版本, 位置, 适用条件. 本轮无旧观察可用, 你应全部实跑.
- **推断**: 只读代码或文档得出的结论, 标性质为推断, 结论是"未验证", 不能当通过.
- **未运行**: 缺权限/依赖/环境时记缺什么, 结论"未验证".
- 退出码非 0, 命令报错, 或输出与期望不符, 照实记为失败, 不要用"大致符合"改判. 不要用计划勾选, 代码阅读, 或别人的口头结论代替运行记录.
- 不要在你没有观察到的层面下结论: 你只判 AC-001-1.

## 汇报

证据写完后, 用 `herdr agent prompt` 之外的渠道不重要; 关键是把上面文件写到证据目录, 并保证 `DONE.md` 存在. 你的最终回复里给出: 结论一句话, p50 与极差数值, 证据文件路径清单, 以及任何未验证/受阻项.
