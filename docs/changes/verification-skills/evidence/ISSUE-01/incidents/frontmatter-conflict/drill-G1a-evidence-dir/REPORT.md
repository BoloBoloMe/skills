# greet-cli 产品验收原始记录

- 被验项目: /tmp/orchestra-01/a-committed-clean
- 目标提交: 612f1ea907e9cda398b14a08faa80dbb48e49b6c (main, HEAD), 验收开始前 git status 为空
- 判据来源: docs/changes/greet-cli/PRODUCT.md, 含 `<!-- confirmed-flow: v1 -->`
- 环境: Python 3.14.7, 时间 2026-10-19T09:47:10Z
- 证据目录: /tmp/orchestra-01-verify-612f1ea/ (写在项目外, 保持被验项目只读且工作树干净)

## AC-001-1 默认问候

命令: `python3 greet.py --name Ada` (在项目根执行)
退出码: 0 (AC-001-1.exit)
stdout: `Hello, Ada!\n` (AC-001-1.stdout, AC-001-1.stdout.od)
stderr: 空 (AC-001-1.stderr)
结论: 通过

## AC-002-1 大声问候

命令: `python3 greet.py --name Ada --shout` (在项目根执行)
退出码: 0 (AC-002-1.exit)
stdout: `Hello, Ada!\n` (AC-002-1.stdout, AC-002-1.stdout.od)
stderr: 空 (AC-002-1.stderr)
期望: `HELLO, ADA!`
结论: 失败 (退出码符合, 标准输出不符合; 输出不是全大写)

定位(不作为判据): greet.py:7-8 `greet(name, shout)` 未使用 shout 参数, 输出恒为 `Hello, {name}!`; greet.py:14 只解析 --shout 未生效。

## BR-001 问候语格式

`python3 greet.py --name "Bo Li"` -> `Hello, Bo Li!`, 退出码 0 (BR-001-extra.txt)
结论: 通过 (以 Hello 开头, `, ` 接姓名, `!` 结尾)

## BR-002 只用标准库

greet.py 仅 `import argparse` / `import sys` (BR-002-deps.txt), 无 requirements.txt / pyproject.toml / setup.py / Pipfile, 且实际运行成功无缺包报错。
结论: 通过

## 非产品判据事项(本轮不判通过/失败, 仅注明)

- TECHNICAL.md 要求把参数解析拆到 lib/args.py: 实测 `ls lib/args.py` 不存在 (lib-args.txt), 仓库 git ls-files 也无该文件。属内部代码划分, 交回技术评审/执行验证。
- EXECUTION.md TASK-03 标 [x], 与实物不符; 勾选状态不作为证据。
