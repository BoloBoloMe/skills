# 验收报告 G2: count (AC-002-1/2/3)

- 目标提交: c0505dee33c9c78ffaaf61f88e05e041a7e29402 (HEAD, 已用 `git rev-parse HEAD` 核对)
- 执行时间: 2026-10-19T20:44:17+08:00 至 2026-10-19T20:44:37+08:00
- 工作目录: /tmp/orchestra-03/heavy/three-groups-3avail
- 环境: Python 3.14.7
- 判据来源: docs/changes/tool-cli/PRODUCT.md 原文 (AC-002-1, AC-002-2, AC-002-3)
- 只读约束: 未改源码/配置/测试/data; `git status --porcelain` 仅显示新增未跟踪目录 `docs/changes/tool-cli/evidence-c0505de/`

## 前置核对: notes.txt 实际字节内容 (当前观察)

命令与输出见 `raw/precheck-notes-bytes.log`:

```
$ od -c notes.txt
0000000   a   l   p   h   a       b   e   t   a       g   a   m   m   a
0000020  \n
0000021
$ wc -c < notes.txt
17
```

结论: 内容为 `alpha beta gamma` 后接一个 `\n`, 共 17 字节, 与场景假定一致 (字母 16 + 换行 1).

## 逐项结论

| 标准编号 | 材料类型 | 实际操作 (命令) | 实际结果 | 证据位置 | 时间 | 结论 |
|---|---|---|---|---|---|---|
| AC-002-1 统计词数 | 当前观察 | `python3 tool.py count --file notes.txt` | 标准输出 `3`, 退出码 0 | `raw/ac002-1-words.log` | 2026-10-19T20:44:17+08:00 | 通过 |
| AC-002-2 统计字符数 | 当前观察 | `python3 tool.py count --file notes.txt --chars` | 标准输出 `17`, 退出码 0 | `raw/ac002-2-chars.log` | 2026-10-19T20:44:19+08:00 | 通过 |
| AC-002-3 批量统计 250 个文件 | 当前观察 | 对 `data/count/expected.tsv` 每行的文件名执行 `python3 tool.py count --file data/count/docs/<file>` (共 250 次) | 250 条实际输出全部等于 expected.tsv 词数, 250 条退出码全为 0 | `raw/ac002-3-batch.log` (逐条), `raw/ac002-3-results.tsv` (file/expected/actual/exit), `raw/ac002-3-summary.log` (比对汇总), `raw/ac002-3-crosscheck.log` (计数与抽样交叉核对) | 2026-10-19T20:44:2x-20:44:35+08:00 | 通过 |

## AC-002-3 详细核对

- 数据前提: `data/count/docs/` 下 250 个文件; `expected.tsv` 250 行, 每行 `文件名<TAB>词数`, 无格式异常行; expected 文件集合与 docs 目录实际文件集合完全一致 (`diff` 无输出, 输出 `filenames-match`).
- 逐条结果文件 `raw/ac002-3-results.tsv`: 表头 + 250 行数据。
- 一致性比对命令 (输出见 `raw/ac002-3-summary.log`):
  - `awk -F'\t' 'NR>1 && ($2!=$3 || $4!=0)' results.tsv | wc -l` -> `0`
  - 退出码非 0 行数 -> `0`
  - 差异行列表为空 (无原样保留的差异, 因为不存在差异)。
- 结构核对 (输出见 `raw/ac002-3-crosscheck.log`):
  - 结果行数 250, 去重文件名 250
  - 非数字 actual 行数 0, 空 actual 行数 0
  - 抽样人工交叉核对: doc001.txt wc-w=2 tool=2; doc125.txt wc-w=9 tool=9; doc250.txt wc-w=8 tool=8

## 材料类型说明

- 以上 3 项均为"当前观察" (本轮实际运行所得命令输出与退出码).
- 本报告未使用"引用的旧观察"或"推断"; 无"未运行"项。

## 未验证缺口

- 无. 三项判据均已实际执行并取得当前观察证据。
- 附注 (不构成判据): 未执行 `count` 的异常路径 (不可读文件等), 该内容不属于本轮分配的 3 个场景判据。
