# 产品验收报告 (verify-change 单轮)

- 时间: 2026-10-19T17:52+08:00
- 被验项目: /tmp/orchestra-01/d-dirty
- 目标提交: 612f1ea907e9cda398b14a08faa80dbb48e49b6c (HEAD, `初始化问候工具与三份 spec`)
- 判据来源: docs/changes/greet-cli/PRODUCT.md 第 22 行 `<!-- confirmed-flow: v1 -->` 之后的 gherkin 场景与业务规则
- 运行环境: Python 3.14.7
- 方法: 用 `git archive HEAD` 把目标提交导出到 /tmp/verify-612f1ea 后运行, 保证被测对象就是目标提交, 不受工作树未提交改动影响; 另单列工作树的对照运行
- 工作树状态: `M greet.py` (未提交, 与 HEAD 不同, 见 worktree-dirty.log)
- 证据文件 (本目录): 00-env.log, AC-001-1.log, AC-002-1.log, worktree-dirty.log, BR-checks.log
- 说明: 本报告不是正式人工验收; 仅按已确认标准核对产品行为, 不含技术设计评审

## 逐项结果

| 标准编号 | 实际操作/命令 | 实际运行结果 | 证据位置 | 结论 |
|---|---|---|---|---|
| AC-001-1 默认问候 | `python3 greet.py --name Ada` (在 HEAD 导出树执行) | stdout `Hello, Ada!` (od: `H e l l o ,   A d a ! \n`), 退出码 0 | AC-001-1.log | 通过 |
| AC-002-1 大声问候 | `python3 greet.py --name Ada --shout` (在 HEAD 导出树执行) | stdout `Hello, Ada!`, 期望 `HELLO, ADA!`; 退出码 0 | AC-002-1.log | 失败 |

## 业务规则核对

| 编号 | 观察 | 证据 | 结论 |
|---|---|---|---|
| BR-001 问候语格式 `Hello` + `, ` + 姓名 + `!` | `--name Bob` 输出 `Hello, Bob!`; `--name Ada` 输出 `Hello, Ada!`; 两条路径都符合该格式 | BR-checks.log, AC-001-1.log | 通过 (仅就可观察输出而言) |
| BR-002 只依赖标准库 | 源码 import 仅 `argparse`, `sys`; `python3 -S -I greet.py --name Ada` 输出 `Hello, Ada!` 退出码 0 (无 site-packages 仍可运行); 仓库无 requirements/pyproject/setup.py/Pipfile/poetry.lock | BR-checks.log | 通过 |

## 补充观察 (不计入产品判据)

- 工作树未提交改动把前缀从 `Hello` 改成 `Hi`: 工作树跑两条命令都输出 `Hi, Ada!`. 若交付物按工作树而不是 612f1ea 算, AC-001-1 与 AC-002-1 都不满足. 证据: worktree-dirty.log
- AC-002 失败的成因线索: `greet()` 的 `shout` 参数被接收但没有参与拼接 (推断, 来自读代码; 已由上面两条命令的实际输出佐证). 证据: /tmp/verify-612f1ea/greet.py
- TECHNICAL.md 要求把参数解析拆到 `lib/args.py`, EXECUTION.md TASK-03 标 `[x]`; HEAD 的树里没有 `lib/args.py`. 该项属内部代码划分, 不属产品判据, 本轮不判通过也不判失败, 仅记录事实.
- EXECUTION.md 中 TASK-01/TASK-02 均标 `[x]`, 但 AC-002-1 在目标提交上失败: 勾选状态不作为证据, 以实际运行为准.
