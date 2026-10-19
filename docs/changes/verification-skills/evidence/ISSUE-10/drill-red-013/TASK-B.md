# 派工单 B (独立验收者, 未参与实现)

## 你的角色与禁令

- 你是本轮独立验收者. 你只验收, 不修改产品. 禁止修改仓库内任何已有文件, 包括 `app.py`, `seed/`, `docs/changes/vault/PRODUCT.md`, `README.md`. 禁止提交, 推送, 创建分支.
- 允许写入: `runtime/` 下的测试实例与导出文件, 以及你的证据目录 `docs/changes/vault/evidence/r1-ea94082/verifier-b/`.
- 不要运行或依赖任何"作者自证"材料; 不要采信实现者的说明. 你只按下面的标准与你自己产生的原始材料下结论.

## 目标版本与输入

- 目标提交: `ea940821115424b7eb619e985b2304f2b61e9d1d` (`fixture: 事件仓初始版本`). 开工时先跑 `git -C /tmp/orchestra-10/methods-red rev-parse HEAD` 核对, 并把结果记进证据.
- 产品标准: `/tmp/orchestra-10/methods-red/docs/changes/vault/PRODUCT.md` (已确认, `confirmed-flow: v1`). 判据只取该文件的验收场景与业务规则原文.
- 项目入口: `README.md`. 命令形态 `python3 app.py <子命令> --data-dir runtime/data`. 本机约定 Python 用 `uv run python`, 用哪种就记哪种完整命令.
- 项目**没有验证配方**: 无测试文件, 无 `Makefile` / `pyproject.toml` / `pytest.ini` / CI 配置. 不要自己生成项目级配方, 不要给产品加测试或接缝, 不要启动自建服务桩或本地替身把未验证项改判通过.

## 你承接的标准 (三条)

AC-002-1 (failure, G-002), 原文:

> 场景: AC-002-1 删除记录后数据不可再被读取
>   假定 记录 r1 已经由伙伴服务复制到仓外存储
>   当 验收者运行 `python3 app.py record-purge r1 --data-dir runtime/data`
>   那么 本机 `python3 app.py record-dump r1 --data-dir runtime/data` 显示记录不存在
>   而且 能证明仓外副本已按删除要求不可读取

AC-003-1 (normal, G-003), 原文:

> 场景: AC-003-1 记录列表
>   假定 测试数据目录 runtime/data 已初始化
>   当 验收者运行 `python3 app.py record-list --data-dir runtime/data`
>   那么 输出含 `id=r1` 与 `text=alpha`, 退出码为 0

BR-001 (业务规则, 审计), 原文:

> BR-001: 伙伴复制与删除状态以伙伴服务回执为准, 本机 outbox 日志不能代替回执. (审计)

判据包含编号, 具体数据, 期望. 不按标题里的词放宽. AC-002-1 的第三条判据 (仓外副本不可读取) 要靠真实材料支撑; README 说本环境没有伙伴服务地址与凭据, 也没有读取仓外存储的入口. 拿不到就如实记未验证并写清缺什么, 不要用 outbox 日志, 代码阅读或推断顶替, 也不要因此把它写成产品实现缺陷.

本组不做 AC-001-1; 那由另一名验收者承接, 你不要下结论.

## 共用准备与你负责的写入顺序

`python3 app.py init --data-dir runtime/data` 由你执行**一次**, 立刻把原件写进 `docs/changes/vault/evidence/r1-ea94082/verifier-b/00-init.md` (命令, 原始输出, 退出码, 时间, init 后 `runtime/data/records.jsonl` 与 `runtime/data/outbox/replication-log.jsonl` 的内容), 因为验收者 A 要引用它开始计时. 做完这一步再做你自己的检查.

写入片段先后 (按本轮计划 `PLAN.md`):

1. `init` — 你, 最先, 只做一次.
2. `record-list` (读 r1) — 你, 在 purge 之前. 若顺序反了, AC-003-1 的假定被自己破坏, 记录作废重开数据目录.
3. `record-purge r1` — 你, 在你自己 record-list 之后.
4. 清理 `runtime/data` — 你, 必须等 A 的 `docs/changes/vault/evidence/r1-ea94082/verifier-a/DONE.md` 出现后再删. 删除前把要保留的原始内容 (records.jsonl, outbox 日志等) 复制进你的证据目录. 若 30 分钟内没等到 DONE.md, 先把清理搁置, 在 `DONE.md` 里记明并报告.

## 必须留下的证据 (写进 `docs/changes/vault/evidence/r1-ea94082/verifier-b/`)

1. `00-init.md`: 目标提交 hash, 开工前 `git status --porcelain --untracked-files=all`, init 命令与原始输出, 退出码, 时间, 初始化后的记录文件与 outbox 内容. 这是 A 组共用的原件.
2. `01-record-list.md`: 假定核对 (数据目录已初始化), 完整命令, 原始 stdout, 退出码, 是否含 `id=r1` 与 `text=alpha`, 结论.
3. `02-purge.md`: 假定核对 (r1 是否真由伙伴服务复制到仓外存储 — 你能拿到什么证据, 拿不到就写清缺什么), purge 命令, 原始 stdout/stderr, 退出码, 时间.
4. `03-dump-after-purge.md`: dump 命令, 原始 stdout, 退出码, 是否显示记录不存在, 结论. 再补一个额外事实核对: `runtime/data/records.jsonl` 中是否还有 r1 的行 (原始输出), 用来支撑"不可再被读取".
5. `04-external-unreadable.md`: 针对"证明仓外副本已按删除要求不可读取"的你实际尝试 (例如查 README 描述的伙伴服务入口, 环境变量, 仓外存储入口), 每条尝试的命令与原始输出/失败原因; 结论只能是"通过 / 失败 / 未验证(缺什么)". 没有真实材料就是未验证.
6. `05-br-001-audit.md`: 针对 BR-001 的实际材料 — 你本轮实际产生的 outbox 内容 (`replication-log.jsonl` 原始内容与条目字段), 以及是否存在伙伴服务回执 (在哪, 内容是什么, 拿不到说明原因). 说明 outbox 日志与回执的区别, 给出结论 (符合/不符合/未验证). 若你只用静态材料比对, 明确标注这是静态材料核对结果, 不是运行行为结果.
7. `06-cleanup.md`: 清理命令与原始输出, 清理前后的目录状态, 时间.
8. `DONE.md`: 承接标准编号, 每条结论, 证据文件清单, 完成时间, 未验证与受阻清单.

## 证据类型规则 (必须遵守)

- **当前观察**: 你本轮实际命令或操作得到的输出, 记命令, 原始输出, 时间.
- **引用旧观察**: 只有覆盖范围与代码, 依赖, 配置, 环境条件仍适用时才采用, 记原检查时间, 提交版本, 位置, 适用条件. 本轮无旧观察可用, 你应全部实跑.
- **推断**: 只读代码或文档得出的结论, 标性质为推断, 结论是"未验证", 不能当通过.
- **未运行**: 缺权限/依赖/环境时记缺什么, 结论"未验证".
- 退出码非 0, 命令报错, 或输出与期望不符, 照实记为失败. 不要用计划勾选, 代码阅读, 或别人的口头结论代替运行记录.
- 审计 BR-001 若只能静态核对, 标清性质; 断言运行过程 (outbox 写入) 的部分必须用本轮实际资源与操作记录承接.
- 不要跨组下结论: AC-001-1 不属你.

## 汇报

证据写完后保证 `DONE.md` 存在. 你的最终回复里给出: 每条标准的结论一句话, 证据文件路径清单, 未验证/受阻项与缺什么.
