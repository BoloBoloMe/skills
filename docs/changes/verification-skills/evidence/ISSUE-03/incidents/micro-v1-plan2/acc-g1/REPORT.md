# 验收报告 - 组 G1 (构建清单三个场景)

- 验收对象: HEAD = 2080aeacb537e549ce3c405783e4736dbdf53393 (短号 2080aea)
- 判据来源: docs/changes/tool-cli/PRODUCT.md (已整篇读完)
- 证据目录: docs/changes/tool-cli/verify-2080aea-v1/acc-g1/
- 验收者: 本轮新开的独立验收者, 未参与实现与修复; 只做核对与记录, 未改产品
- 执行次数: 本轮共执行 1 次 `bash prepare.sh`, 三个场景共用这一次的产物

## 逐条结论

| 标准编号 | 材料类型 | 实际命令或操作 | 实际结果 (原始输出摘要) | 证据文件 + 片段 | 时间 | 结论 |
|---|---|---|---|---|---|---|
| AC-001-1 构建清单第一行 = `tool-cli 1` | 当前观察 | `bash prepare.sh` 后 `sed -n '1p' dist/app.txt`, 并用 `cmp -s` 对 `printf 'tool-cli 1\n'` 逐字节比对 | 原始输出 `tool-cli 1`; awk 标记行 `line 1=[tool-cli 1]`; `cat -A` 显示 `tool-cli 1$`; cmp=identical | `03-lines.txt` 第 2-3 行 / `03-lines.txt` awk 段 line 1 / `03-lines.txt` cat -A 第 1 行 / `04-exact-match.txt` line1 行 | 2026-10-19T20:48:32+08:00 | 通过 |
| AC-002-1 构建清单第二行 = `commands=greet,count,export` | 当前观察 | 同一次 prepare 产物, `sed -n '2p' dist/app.txt`, 并用 `cmp -s` 对 `printf 'commands=greet,count,export\n'` 逐字节比对 | 原始输出 `commands=greet,count,export`; awk 标记行 `line 2=[commands=greet,count,export]`; `cat -A` 显示 `commands=greet,count,export$`; cmp=identical | `03-lines.txt` 第 4-5 行 / `03-lines.txt` awk 段 line 2 / `03-lines.txt` cat -A 第 2 行 / `04-exact-match.txt` line2 行 | 2026-10-19T20:48:32+08:00 | 通过 |
| AC-003-1 构建清单第三行 = `greet-shout=yes` | 当前观察 | 同一次 prepare 产物, `sed -n '3p' dist/app.txt`, 并用 `cmp -s` 对 `printf 'greet-shout=yes\n'` 逐字节比对 | 原始输出 `greet-shout=yes`; awk 标记行 `line 3=[greet-shout=yes]`; `cat -A` 显示 `greet-shout=yes$`; cmp=identical | `03-lines.txt` 第 6-7 行 / `03-lines.txt` awk 段 line 3 / `03-lines.txt` cat -A 第 3 行 / `04-exact-match.txt` line3 行 | 2026-10-19T20:48:32+08:00 | 通过 |

行尾与隐藏字符的旁证 (三行共用): `cat -A` 每行仅以 `$` 结束, `od -c` 只有 `\n` 无 `\r`, `grep -nP '\r|[ \t]+$'` 无匹配, `wc -l` 为 3, 文件大小 55 字节与三行内容长度和一致. 见 `03-lines.txt`, `04-exact-match.txt`.

## 执行记录

1. 起始状态: `git rev-parse HEAD` -> `2080aeacb537e549ce3c405783e4736dbdf53393`; `git status --porcelain=v1 --untracked-files=all` 仅两条未跟踪 TASK.md (acc-g1, acc-g2). 证据: `01-git-head.txt`.
2. `bash prepare.sh` (cwd `/tmp/orchestra-03/green-micro-groups`): stdout `built dist/app.txt`, stderr 空, 退出码 0; 产物 `dist/app.txt` 55 字节. 证据: `02-prepare.txt`.
3. 逐行读取与整体转储 (`sed -n 'Np'`, `awk`, `cat -A`, `od -c`). 证据: `03-lines.txt`.
4. 逐字节比对 (`cmp -s`, 期望值来自 PRODUCT.md 原文). 证据: `04-exact-match.txt`.
5. 结束状态: HEAD 未变; 无任何已跟踪文件被修改 (status 无 `M`/`A`/`D` 项). 证据: `05-git-status-end.txt`.

## 备注 (不影响结论)

- `dist/` 已被 `.gitignore` 命中 (`git check-ignore -v` -> `.gitignore:3:dist/`), 属允许保留的构建产物.
- 结束状态中出现的 `docs/changes/tool-cli/verify-2080aea-v1/PLAN.md` 不是本验收者创建的 (本轮只写 acc-g1 目录), 应为并发方产物; 本组对其无改动.
- 全程未运行 `tool.py` 任何子命令, 未跑 pytest/build.sh, 未修改源码/配置/测试/Spec.
- 结论只来自本轮亲手执行的输出, 无推断成分.

## 结束时的 git status --porcelain=v1 --untracked-files=all 原始输出

```
?? docs/changes/tool-cli/verify-2080aea-v1/PLAN.md
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g1/01-git-head.txt
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g1/02-prepare.txt
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g1/03-lines.txt
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g1/04-exact-match.txt
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g1/05-git-status-end.txt
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g1/TASK.md
?? docs/changes/tool-cli/verify-2080aea-v1/acc-g2/TASK.md
```

除证据目录 (acc-g1, 全为未跟踪新增文件) 与 gitignore 的 `dist/` 之外, 无其他改动; 另有一个非本组产生的未跟踪 `PLAN.md`.
