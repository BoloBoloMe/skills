# greet-cli 独立产品验收报告 (round 1)

## 版本前提

- 目标提交: `612f1ea907e9cda398b14a08faa80dbb48e49b6c` (分支 main, "初始化问候工具与三份 spec")
- 验收开始前 `git status --porcelain` 输出为空, 工作区与目标提交一致 (已跟踪的 greet.py, README.md, docs 三份 spec 均无未提交改动, 无未跟踪产品文件)
- 运行环境: Python 3.14.7, 时间 2026-10-19T17:54:33+08:00 (见 `env.txt`)
- 本报告结论只覆盖上述提交; 验收期间没有源文件或 Spec 变化, 未重跑
- 证据目录: `docs/changes/greet-cli/evidence-612f1ea-r1/`
- 影响判断: 项目无测试框架, 无构建脚本, 无测试发现配置 (仓库仅 README.md, greet.py, docs/, .gitignore); README 里唯一的检查命令 `python3 -m compileall -q greet.py` 只指向 greet.py, 不扫描 docs/. 因此证据目录放在仓库内不会进入构建, 测试发现或运行输入, 未外置

## 判据来源

- `docs/changes/greet-cli/PRODUCT.md`, `验收标准` 节 gherkin 块, 确认标记 `<!-- confirmed-flow: v1 -->` 存在
- 逐字采用 AC-001-1, AC-002-1 两个场景 (含场景编号, 命令, 期望输出)
- 业务规则 BR-001 (问候语格式), BR-002 (只依赖标准库, 审计) 作为补充核对项, 单列在下方
- `TECHNICAL.md` / `EXECUTION.md` 只用于取运行命令 (`python3 greet.py ...`) 和环境约束, 不作为通过条件

## 逐项结果

| 编号 | 实际操作/命令 | 实际运行结果 | 证据位置 | 时间/版本 | 结论 |
| --- | --- | --- | --- | --- | --- |
| AC-001-1 默认问候 | `python3 greet.py --name Ada` | 标准输出 `Hello, Ada!` (带换行), 退出码 0; 与期望完全一致 | `ac-001/cmd.txt`, `ac-001/stdout.txt`, `ac-001/stderr.txt` (空), `ac-001/exit_code.txt`, `ac-001/run.log` | 612f1ea, Python 3.14.7, 2026-10-19T17:54 | 通过 |
| AC-002-1 大声问候 | `python3 greet.py --name Ada --shout` | 标准输出 `Hello, Ada!`, 退出码 0; 期望是 `HELLO, ADA!`, 实际输出不是全大写 | `ac-002/cmd.txt`, `ac-002/stdout.txt`, `ac-002/stderr.txt` (空), `ac-002/exit_code.txt`, `ac-002/run.log` | 612f1ea, Python 3.14.7, 2026-10-19T17:54 | 失败 |

失败原因 (来自本轮实际观察): 加 `--shout` 后 stdout 字节内容与不加时完全相同 (`Hello, Ada!`), 全大写转换没有生效. 该判断基于运行结果, 不依赖读代码. 仅从代码可推断 `greet()` 忽略 `shout` 参数 (`greet.py` 第 7-8 行), 这条属推断, 不作为判据.

## 业务规则补充核对

| 编号 | 实际操作 | 实际结果 | 证据位置 | 结论 |
| --- | --- | --- | --- | --- |
| BR-001 问候语格式 | 由 AC-001-1 的实际输出核对 (固定 `Hello` 开头, 后接 `, ` 与姓名, `!` 结尾) | `Hello, Ada!` 符合格式 | `ac-001/stdout.txt` | 通过 (仅覆盖 AC-001-1 这一组输入; 其他姓名未验证) |
| BR-002 仅标准库 | `grep -nE '^(import|from) ' greet.py`; `git ls-files` 查依赖清单; `python3 -m compileall -q greet.py` | 仅 `import argparse`, `import sys`; 无 requirements/pyproject/setup.py/Pipfile 类依赖清单; compileall 退出码 0 | `supplement/imports_audit.log`, `supplement/compileall.log` | 通过 (审计项, 非 gherkin 场景) |

compileall 产生的 .pyc 通过 `PYTHONPYCACHEPREFIX=/tmp/orchestra-01/pycache-audit` 写到仓库外, 未在仓库内留下 `__pycache__`.

## 非产品判据事项 (不判通过/失败)

- `TECHNICAL.md` 模块接口要求把参数解析拆到 `lib/args.py` 并由 `greet.py` 调用. 本轮仓库中不存在 `lib/args.py` (`git ls-files` 与目录列表均无). 这属内部代码划分, 按验收边界交回既有技术评审与执行验证, 本轮不判.
- `EXECUTION.md` 任务图把 TASK-02 (`--shout` 全大写) 标为 `[x]`. 该勾选状态不作为证据: 本轮在最终提交上实跑 AC-002-1 失败, 故该场景记为失败.
- 未做的事: 未改产品代码/配置/测试, 未提交, 未推送, 未开 PR. 无正式人工验收结论, 本报告不是正式验收.

## 覆盖范围

- 覆盖: 目标提交 612f1ea 上的 AC-001-1, AC-002-1 两个已确认场景, 各自实际运行一次; 另做 BR-001 格式核对 (仅 Ada 输入) 与 BR-002 标准库审计
- 未覆盖: 其他姓名/异常参数 (缺 `--name`, 空姓名, 非 ASCII 姓名), `--help` 行为, 多语言 (NG-001 明确非目标), 性能与并发
- 未验证项: 无额外未验证场景; 两条 gherkin 场景均已实跑, 结论分别为通过与失败

## 收尾

- 除本次证据目录 `docs/changes/greet-cli/evidence-612f1ea-r1/` 的输出外, 源码与 Spec 未变. 不声称整个工作区干净: 该证据目录本身就是相对起始提交 612f1ea 的新增未跟踪文件 (`git status --porcelain` 只显示 `?? docs/changes/greet-cli/evidence-612f1ea-r1/`)
- 汇总: AC-001-1 通过, AC-002-1 失败
