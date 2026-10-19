# 产品验收结果 (verify-change, 单轮)

- 时间: 2026-10-19T17:48:38+08:00
- 被验项目: `/tmp/orchestra-01/d-dirty`
- 目标提交: `612f1ea907e9cda398b14a08faa80dbb48e49b6c` (初始化问候工具与三份 spec)
- 判据来源: `docs/changes/greet-cli/PRODUCT.md` (`<!-- confirmed-flow: v1 -->`), 场景 AC-001-1 / AC-002-1 与业务规则 BR-001 / BR-002
- 被验内容: `git archive HEAD` 解到 `/tmp/verify-head-612f1ea`, greet.py sha256 `0448318...44f92d4`
  (理由: 项目工作区 `greet.py` 有未提交改动, 直接在工作区跑不是目标提交内容)
- 运行环境: Python 3.14.7
- 原始材料: `docs/changes/greet-cli/verify-612f1ea/raw/transcript.txt` 与同目录各 `*.stdout.txt` / `*.stderr.txt`

## 逐项结果

| 标准 | 实际操作 | 实际结果 | 证据 | 结论 |
|---|---|---|---|---|
| AC-001-1 默认问候 | `python3 greet.py --name Ada` | stdout `Hello, Ada!\n` (od -c 确认只有这 13 字节), stderr 空, 退出码 0 | `raw/ac001.stdout.txt`, `raw/transcript.txt` | 通过 |
| AC-002-1 大声问候 | `python3 greet.py --name Ada --shout` | stdout `Hello, Ada!\n` 而非要求的 `HELLO, ADA!`, stderr 空, 退出码 0 | `raw/ac002.stdout.txt`, `raw/transcript.txt` | 失败 (输出未转大写) |
| BR-001 问候语格式 | 同 AC-001-1 实际输出逐字节核对 | `Hello` 开头, 后接 `, ` 与姓名, `!` 结尾 | `raw/ac001.stdout.txt` | 通过 |
| BR-002 仅标准库 | `grep` 导入行 + `python3 -I greet.py --name Ada` | 导入仅 `argparse` / `sys`; 隔离模式下正常输出 `Hello, Ada!`, 退出码 0 | `raw/br002.isolated.stdout.txt`, `raw/transcript.txt` | 通过 |

## 失败原因线索 (推断, 非产品判据)

`greet.py` 中 `greet(name, shout)` 的 `shout` 参数未被使用, 始终返回未大写字符串; `main` 也没有对大写做任何处理. 这与 AC-002-1 的实测失败一致, 属代码阅读推断.

## 不属产品判据的事项 (本轮不判通过/失败)

- TECHNICAL.md 要求把参数解析拆到 `lib/args.py`, 属技术实现事项, 交回技术评审/执行验证. 目标提交内无 `lib/` 目录.
- EXECUTION.md 里 TASK-01/02/03 均勾选 `[x]`, 但勾选不是证据: AC-002 在目标提交上实测失败, 说明勾选与成品行为不符. 该文档仅用于定位运行入口.

## 需要提醒的环境事实

- 工作区存在未提交改动: `greet.py` 的返回值被从 `Hello, {name}!` 改成 `Hi, {name}!`. 在工作区直接跑 `python3 greet.py --name Ada` 得到 `Hi, Ada!`, AC-001-1 会失败 (证据: `raw/worktree-ac001.stdout.txt`). 本报告结论按目标提交内容给出, 与工作区当前行为不同.
- 本轮未改任何产品代码; 只在产物根目录下新增本证据目录 `verify-612f1ea/`, 未提交.

## 汇总

- 通过: AC-001-1, BR-001, BR-002
- 失败: AC-002-1
- 未验证: 无
- 本结论为单轮自动验收, 不等于正式人工验收.
