# 任务书: 独立产品验收 - 组 G1 (构建清单三个场景)

你是本轮新开的独立验收者, 未参与本次实现与修复. 只做核对与记录, 不改产品.

## 现场

- 项目目录: /tmp/orchestra-03/green-micro-groups (当前 cwd)
- 目标提交: 2080aeacb537e549ce3c405783e4736dbdf53393 (HEAD), 短号 2080aea
- 判据来源: docs/changes/tool-cli/PRODUCT.md (先完整读一遍)
- 你的证据目录: docs/changes/tool-cli/verify-2080aea-v1/acc-g1/ (只往这里写文件)

## 你承接的标准 (逐字照原文, 不得放宽)

场景: AC-001-1 构建清单第一行
  假定 值班同学已运行 `bash prepare.sh` 生成 `dist/app.txt`
  当 值班同学读取 `dist/app.txt` 的第一行
  那么 内容为 `tool-cli 1`

场景: AC-002-1 构建清单第二行
  假定 值班同学已运行 `bash prepare.sh` 生成 `dist/app.txt`
  当 值班同学读取 `dist/app.txt` 的第二行
  那么 内容为 `commands=greet,count,export`

场景: AC-003-1 构建清单第三行
  假定 值班同学已运行 `bash prepare.sh` 生成 `dist/app.txt`
  当 值班同学读取 `dist/app.txt` 的第三行
  那么 内容为 `greet-shout=yes`

步骤里的具体数据 (行号, 期望字符串) 都是判据的一部分. 内容必须逐字符比对, 大小写, 逗号, 空格, 结尾多余字符都算差异.

## 怎么做

1. 先记录 `git rev-parse HEAD` 与 `git status --porcelain=v1 --untracked-files=all` 的原始输出, 把起始状态存进证据目录.
2. 执行 `bash prepare.sh`, 记完整命令, 原始 stdout/stderr, 退出码.
3. 逐行读取 `dist/app.txt` 第 1, 2, 3 行 (例如 `sed -n '1p'`, `sed -n '2p'`, `sed -n '3p'` 或 `awk`), 每行保留原始输出; 再整体保存 `cat -A dist/app.txt` 或 `od -c dist/app.txt`, 用于证明行尾与空格没有隐藏差异.
4. 每条场景单独给结论. 三个场景可以共用同一次 prepare.sh 产物, 但结论逐条成行.
5. 只允许跑上面这些命令. 不要运行 tool.py 的任何子命令, 不要跑 pytest 或 build.sh, 不要修改任何已跟踪文件 (源码, 配置, 测试, Spec 都不许改). `dist/` 是 gitignore 的构建产物, 可留.

## 证据与报告怎么写

把命令输出原样落到证据文件 (例如 01-git-head.txt, 02-prepare.txt, 03-lines.txt), 并在 TASK 结果里逐项列出:

标准编号 | 材料类型 (当前观察 / 引用的旧观察 / 推断 / 未运行) | 实际命令或操作 | 实际结果 (原始输出摘要, 不是转述) | 证据文件路径 + 行号或片段 | 时间 | 结论 (通过/失败/未验证)

硬性要求:
- 你的结论只能来自你本轮亲手跑出的输出 (当前观察). 读代码猜结论算推断, 结论必须写 未验证, 不能算通过.
- 不许拿任何计划文件的勾选状态当证据.
- 不许自行补标准, 不许把 TECHNICAL.md 的要求当产品判据 (它只提供操作线索).
- 完结时把本报告写成 docs/changes/tool-cli/verify-2080aea-v1/acc-g1/REPORT.md, 并在回复里给出: 每条标准一行结论, 以及你用的证据文件路径.
- 最后附一行 `git status --porcelain=v1 --untracked-files=all` 原始输出, 说明除证据目录与 dist/ 之外有无其他改动.
