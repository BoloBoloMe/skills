# 验收报告 G1: greet

- 目标提交: `c0505dee33c9c78ffaaf61f88e05e041a7e29402` (HEAD, `git rev-parse HEAD` 核对)
- 执行时间: 2026-10-19T12:44:17Z 至 2026-10-19T12:44:41Z (UTC)
- 环境: Python 3.14.7, 工作目录 `/tmp/orchestra-03/heavy/three-groups-3avail`
- 判据: `docs/changes/tool-cli/PRODUCT.md` 的 AC-001-1, AC-001-2, AC-001-3 原文
- 只读约束: 未改源码, 配置, 测试, data/; 新增文件仅在本证据目录. 验收后 `git status --porcelain` 仅显示 `?? docs/changes/tool-cli/evidence-c0505de/`, `git diff --stat` 为空.
- 材料类型说明: 下列结论全部基于**当前观察** (本轮命令输出). 本轮未引用旧观察, 未作推断, 无未运行项.

## 逐项结论

| 标准编号 | 材料类型 | 实际操作 (命令) | 实际结果 | 证据位置 | 时间 (UTC) | 结论 |
|---|---|---|---|---|---|---|
| AC-001-1 默认问候 | 当前观察 | `python3 tool.py greet --name Ada` | stdout 字节为 `Hello, Ada!\n` (od 核对), stderr 为空, 退出码 0 | `docs/changes/tool-cli/evidence-c0505de/greet/raw/ac001-1.meta`, `ac001-1.stdout`, `ac001-1.stderr` | 2026-10-19T12:44:19Z - 12:44:20Z | 通过 |
| AC-001-2 全大写问候 | 当前观察 | `python3 tool.py greet --name Ada --shout` | stdout 字节为 `HELLO, ADA!\n` (od 核对), stderr 为空, 退出码 0 | `docs/changes/tool-cli/evidence-c0505de/greet/raw/ac001-2.meta`, `ac001-2.stdout`, `ac001-2.stderr` | 2026-10-19T12:44:20Z | 通过 |
| AC-001-3 批量问候 250 个姓名 | 当前观察 | `bash` 循环: 对 `data/greet/names.txt` 每一行执行 `python3 tool.py greet --name <该行姓名>`, 共 250 次 | 250/250 条 stdout 去尾换行后与 `Hello, <姓名>!` 完全一致, 250 条退出码均为 0, 250 个 stderr 均为空; 另做独立复核 250/250 通过 | `docs/changes/tool-cli/evidence-c0505de/greet/raw/ac001-3/results.tsv` (逐条 序号/姓名/expected/actual/退出码/stderr), `raw/ac001-3/001.stdout` 至 `250.stdout` 与同名 `.stderr`, `raw/ac001-3.meta`, `raw/ac001-3.recheck` | 2026-10-19T12:44:26Z - 12:44:37Z; 独立复核 12:44:41Z | 通过 |

## 核对细节

### AC-001-1

```
$ python3 tool.py greet --name Ada
Hello, Ada!
$ echo $?
0
```

`od -c` 结果: `H e l l o ,   A d a ! \n`. 标准输出内容与判据一致, 末尾换行是 CLI 正常打印行为.

### AC-001-2

```
$ python3 tool.py greet --name Ada --shout
HELLO, ADA!
$ echo $?
0
```

`od -c` 结果: `H E L L O ,   A D A ! \n`.

### AC-001-3

- 输入核对: `wc -l data/greet/names.txt` = 250, ASCII, 无空行, 无首尾异常字符, 去重后仍为 250 个姓名; 内容为 `Person001` 至 `Person250`, 每行一个.
- 逐条结果文件 `raw/ac001-3/results.tsv` 共 250 条数据行; 汇总: `total_lines_processed: 250`, `pass: 250`, `fail: 0`.
- 独立复核 (`raw/ac001-3.recheck`): 直接重读 TSV 并逐字节比对每个 `NNN.stdout`, 结果为 `tsv_rows=250 tsv_ok=250 tsv_bad=0`, `stdout_files_checked=250 bad=0`, 且每个 stdout 恰好 1 行, 250 个 stderr 文件全部为空.
- 失败样例: 本轮无失败, 故无失败样例可保留.

## 未验证缺口

- 无. 分到的 3 项均有本轮实际运行证据, 全部通过.
- 说明: 本轮仅覆盖分到的 AC-001-1/2/3; 其余 AC-002, AC-003 不在本报告范围.
