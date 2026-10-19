# greet-cli 产品验收报告 (独立验收, 单轮)

## 1. 输入

- 被验项目: `/tmp/orchestra-01/e-checked-docs` (greet-cli)
- 目标提交: `2e868d17fa9c3f9d907546faa476db9fe64df97b` (HEAD, 唯一提交)
- 判据来源: `docs/changes/greet-cli/PRODUCT.md`, 验收标准节带确认标记 `<!-- confirmed-flow: v1 -->`, 只含 AC-001-1 / AC-002-1 两个场景; 业务规则 BR-001 / BR-002 作为原文判据.
- 版本前提: `git status --porcelain` 为空; `--ignored` 仅 `.agents/` (被 .gitignore 忽略, 非产品文件). 工作区与目标提交一致.
- 技术材料 (TECHNICAL.md / EXECUTION.md) 仅用于取运行命令与约束, 不当产品判据.

## 2. 证据目录

- 实际路径: `/tmp/orchestra-01/evidence-greet-cli/v-2e868d1/` (仓库外)
- 外置原因: 项目自带 `check_changes.py` 只允许 `docs/changes/<slug>/` 含 PRODUCT.md, TECHNICAL.md, EXECUTION.md 三个文件, 多出即失败. 已用仓库副本试验确认: 放入证据文件后退出码 1, 报 `unexpected ['EVIDENCE.md']`.
  - `check_changes-baseline.out`: 退出码 0
  - `check_changes-with-evidence.out`: 退出码 1
- 因此本轮报告与原始输出都写在仓库外, 不进入构建, 测试发现或 `check_changes.py` 的扫描范围.

## 3. 逐项结果

环境: Python 3.14.7, 运行时间 2026-10-19T17:56:28+08:00 (`environment.txt`).

| 编号 | 操作/命令 | 实际结果 | 证据位置 | 时间/版本 | 结论 |
|---|---|---|---|---|---|
| AC-001-1 (默认问候, G-001/BR-001) | `python3 greet.py --name Ada` | stdout 十六进制 `48656c6c6f2c20416461210a`, 即 `Hello, Ada!` 加换行; stderr 空; 退出码 0 | `scenarios/AC-001-1.stdout`, `.stderr`, `.exit` | 2026-10-19T17:56:28+08:00, 提交 2e868d1 | 通过 |
| AC-002-1 (大声问候, G-001/BR-001) | `python3 greet.py --name Ada --shout` | stdout 实际为 `Hello, Ada!` (十六进制 `48656c6c6f2c20416461210a`), 期望 `HELLO, ADA!`; stderr 空; 退出码 0 | `scenarios/AC-002-1.stdout`, `.stderr`, `.exit` | 同上 | 失败 |

补充核对 (业务规则原文, 非验收场景):

| 编号 | 操作/命令 | 实际结果 | 证据位置 | 结论 |
|---|---|---|---|---|
| BR-002 (仅标准库) | 解析 greet.py 的 import; `python3 -c` 查 `sys.stdlib_module_names` | 只导入 `argparse`, `sys`, 两者均为标准库; 仓库内无 requirements/pyproject 依赖文件 | `environment.txt` 同目录命令行输出, 见第 4 节 | 通过 |
| BR-001 (Hello 开头, `, ` 连接, `!` 结尾) | 由 AC-001-1 实际输出核对 | `Hello, Ada!` 符合, 但 `--shout` 下未转大写属于 AC-002-1 失败范围 | 同上 | AC-001-1 范围内通过; 大写变更未实现 |

## 4. 关键原始记录

- AC-002-1 实际 stdout: `Hello, Ada!` (期望 `HELLO, ADA!`), 说明 `--shout` 对输出无效果; 这是本轮实际运行观察, 非代码推断.
- 依赖核对命令: `python3 -c "import ast; ..."` 输出 `['argparse', 'sys']`; `argparse`/`sys` 在 `sys.stdlib_module_names` 中均为 True.
- 语法检查 `python3 -m compileall -q greet.py` 退出码 0 (仅作辅助; 生成的 `__pycache__` 已删除, 仓库已恢复为起始状态).

## 5. 覆盖范围与非产品判据注明

- 覆盖: PRODUCT.md 全部 2 个验收场景 + BR-002; 未验证项: 无.
- 失败项: AC-002-1, 唯一原因是 `--shout` 未生效.
- 不属产品判据, 本轮不判通过/失败:
  - TECHNICAL.md 要求把参数解析拆到 `lib/args.py`; 实际仓库无 `lib/` 目录. 这是内部代码划分, 交回既有技术评审/执行验证.
  - EXECUTION.md TASK-02/TASK-03 标记 `[x]`, 但 AC-002-1 在最终版本上仍失败. 勾选状态不作证据.
- 收尾: 除本次证据目录 (`/tmp/orchestra-01/evidence-greet-cli/v-2e868d1/`) 的输出外, 源码与 Spec 未变.
