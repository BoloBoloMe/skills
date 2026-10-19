# 独立产品验收报告 - 组 G2 (审计规则 BR-002)

- 目标提交: 2080aeacb537e549ce3c405783e4736dbdf53393 (2080aea, HEAD)
- 上一提交: 7bcc69269ab34516909c65ca2b5896862f73a176 (7bcc692, HEAD~1)
- 判据: BR-002 (审计): 本变更不新增第三方依赖, 依赖清单, 锁文件和构建材料与上一提交逐项一致.
- 核对性质: **静态材料核对结果, 不是运行行为结果.** 全程只跑 git 只读命令和读文件, 未运行 prepare.sh, build.sh, pytest 或 tool.py, 未修改任何产品文件.

## 基线状态 (01-git-state.txt)

```
### git rev-parse HEAD
2080aeacb537e549ce3c405783e4736dbdf53393
### git rev-parse HEAD~1
7bcc69269ab34516909c65ca2b5896862f73a176
### git status --porcelain=v1 --untracked-files=all
?? docs/changes/tool-cli/verify-2080aea-v1/PLAN.md
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g1/... (g1 证据文件)
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g2/... (本组证据文件)
```

工作树除验收证据目录 (PLAN.md, acc-g1/, acc-g2/) 外无任何改动, 核对基于干净的产品树.

## 纳入核对的依赖与构建材料及理由

| 文件 | 纳入理由 |
|---|---|
| deps.txt | 依赖清单本体 |
| deps.lock | 锁文件本体 |
| build.sh | 构建脚本本体 |
| prepare.sh | 构建/准备脚本本体 |
| tools/build_manifest.py | tools/ 目录下唯一文件, 生成构建清单 dist/app.txt 的构建材料 |

其他可能的候选: .gitignore, notes.txt, README.md, docs/ 不属于依赖清单, 锁文件或构建材料 (不参与依赖声明或构建产物生成); 即便保守纳入, 全树 diff (见下) 证明它们也未变.

## 逐项核对表

| 标准编号 | 材料类型 | 实际命令或操作 | 实际结果 (原始输出/哈希) | 证据文件 | 时间 | 结论 |
|---|---|---|---|---|---|---|
| BR-002 | 提交基线 | `git rev-parse HEAD` / `git rev-parse HEAD~1` | 2080aeacb537e549ce3c405783e4736dbdf53393 / 7bcc69269ab34516909c65ca2b5896862f73a176 | 01-git-state.txt | 2026-10-19, 证据文件落盘于 20:49:54+08:00 (真实时间, 见 05-timestamps.txt) | 通过 (基线与任务书一致) |
| BR-002 | 依赖清单 deps.txt | `git diff 7bcc692 2080aea -- deps.txt`; `git rev-parse 7bcc692:deps.txt` vs `2080aea:deps.txt` | diff 为空; 两端均为 bbb52972310fb82afbe4364e741d264ea25f68bc | 03-per-file-diff.txt | 2026-10-19, 落盘 20:49:11+08:00 (见 05-timestamps.txt) | 通过 (逐项一致) |
| BR-002 | 锁文件 deps.lock | 同上方法 | diff 为空; 两端均为 f5f745d19dad8f561d612f4868e0c3c5781cf6cd | 03-per-file-diff.txt | 同上 | 通过 (逐项一致) |
| BR-002 | 构建脚本 build.sh | 同上方法 | diff 为空; 两端均为 779624644c085151dd81f8f9cd6bd98e97558c71 | 03-per-file-diff.txt | 同上 | 通过 (逐项一致) |
| BR-002 | 准备脚本 prepare.sh | 同上方法 | diff 为空; 两端均为 f6c7c1739086dc2697f622624217d649d677f62e | 03-per-file-diff.txt | 2026-10-19, 落盘 20:49:11+08:00 (见 05-timestamps.txt) | 通过 (逐项一致) |
| BR-002 | 构建材料 tools/build_manifest.py | 同上方法 | diff 为空; 两端均为 44140050e6b1835af92463c7dff81972afebaba8 | 03-per-file-diff.txt | 同上 | 通过 (逐项一致) |
| BR-002 | 第三方依赖引入 (内容复核) | `git show 2080aea:<各文件>` 人工读内容 | deps.txt 仅 `python-stdlib`; deps.lock 注明只用标准库; build.sh 仅用 `python3 -m compileall`; prepare.sh 仅调 `python3 tools/build_manifest.py`; build_manifest.py 仅 import sys/pathlib (标准库) | 04-file-contents.txt | 2026-10-19, 落盘 20:49:11+08:00 (见 05-timestamps.txt) | 通过 (无第三方依赖引入) |
| BR-002 | 全树兜底 | `git diff --name-status 7bcc692 2080aea`; `git diff 7bcc692 2080aea -- .gitignore notes.txt README.md docs/` | 全树仅 M tests/test_tool.py, M tool.py; 其余路径 diff 为空, 即其余所有文件 (含上述候选) 逐字节一致 | 02-name-status.txt, 03-per-file-diff.txt | 2026-10-19, 落盘 20:48:45 / 20:49:11+08:00 (见 05-timestamps.txt) | 通过 (依赖/构建材料无一改动) |

## 第 4 步: 本次实际改动文件 (事实描述, 不改判 BR-002)

`git diff --name-status 7bcc692 2080aea` 原样输出:

```
M	tests/test_tool.py
M	tool.py
```

改动只有 tool.py 与 tests/test_tool.py 两个文件, 均为产品代码与测试代码, 不属于依赖清单, 锁文件或构建材料.

## 时间说明

本报告时间列原误写为 2026-07-19, 已修正为真实时间. 证据文件 01..04 均在本轮核对当时 (2026-10-19 20:48-20:50 +08:00) 写下, 真实落盘时间由 `date -Is` 与 `stat -c "%y %n"` 记录于 05-timestamps.txt. 时间补记未改动任何结论, 未重跑核对命令.

## 证据文件

- 01-git-state.txt: HEAD/HEAD~1/初始 git status 原始输出
- 02-name-status.txt: 全树 name-status 原始输出
- 03-per-file-diff.txt: 各依赖/构建文件空 diff + 两端 blob 哈希 + 全树兜底 diff
- 04-file-contents.txt: deps.txt, deps.lock, build.sh, prepare.sh, tools/build_manifest.py 完整内容 (取自 2080aea)
- 05-timestamps.txt: 真实时间戳 (date -Is + 01..04 文件落盘时间)

## 结论

**BR-002 通过** (静态材料核对结论): 依赖清单 (deps.txt), 锁文件 (deps.lock), 构建材料 (build.sh, prepare.sh, tools/build_manifest.py) 在 7bcc692 与 2080aea 两端 diff 为空且 blob 哈希逐项相等, 内容复核确认只使用 Python 标准库, 无第三方依赖引入.

不属本轮判据的说明: 代码质量, 内部模块划分等不在 BR-002 判据内, 本报告不做评价.

## 完结时 git status

`git status --porcelain=v1 --untracked-files=all` 原始输出:

```
?? docs/changes/tool-cli/verify-2080aea-v1/PLAN.md
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g1/01-git-head.txt
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g1/02-prepare.txt
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g1/03-lines.txt
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g1/04-exact-match.txt
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g1/05-git-status-end.txt
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g1/REPORT.md
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g1/TASK.md
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g2/01-git-state.txt
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g2/02-name-status.txt
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g2/03-per-file-diff.txt
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g2/04-file-contents.txt
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g2/REPORT.md
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g2/TASK.md
```

除验收证据目录 (PLAN.md, acc-g1/, acc-g2/) 的未跟踪文件外, 无任何其他改动.
