# 组 A 验收结果 (问候: AC-001-1, AC-001-2)

## 环境核对 (执行前)

- 项目 cwd: `/tmp/orchestra-03/green-two-groups`
- `git rev-parse HEAD` 实际输出: `ceda596ed3a3e96d4348a466a98c5d1c625921dd`
  -> 与目标提交一致, 继续执行.
- `git status --porcelain` 实际输出: `?? docs/changes/tool-cli/acceptance-v1-ceda596/`
  -> 只有本轮验收目录未跟踪, 无其它改动.
- 解释器: `python3 -V` = `Python 3.14.4`; 系统中 `python3` 可直接调用.
- 判据来源核对: 已比对 `docs/changes/tool-cli/PRODUCT.md` 中 AC-001-1 / AC-001-2 两段, 与 BRIEF-groupA.md 引用文字逐字一致 (含命令与期望输出). 本次只按这两段判定.

## 结果

| 编号 | 材料类型 | 命令与退出码 | 实际结果 | 证据文件 | 时间 | 结论 |
|---|---|---|---|---|---|---|
| AC-001-1 | 当前观察 | `python3 tool.py greet --name Ada` / 退出码 0 | stdout 12 字节 = `b'Hello, Ada!\n'`; stderr 0 字节 | `docs/changes/tool-cli/acceptance-v1-ceda596/groupA-greet/AC-001-1.log` | 2026-10-19T20:33:46+08:00 | 通过 (见差异说明 D-1) |
| AC-001-2 | 当前观察 | `python3 tool.py greet --name Ada --shout` / 退出码 0 | stdout 12 字节 = `b'HELLO, ADA!\n'`; stderr 0 字节 | `docs/changes/tool-cli/acceptance-v1-ceda596/groupA-greet/AC-001-2.log` | 2026-10-19T20:33:46+08:00 | 通过 (见差异说明 D-1) |
| AC-001-1 / AC-001-2 | 当前观察 (重复) | 同上两条, 各再跑 3 次 / 每次退出码均 0 | 6 次输出逐字节相同: `b'Hello, Ada!\n'` 与 `b'HELLO, ADA!\n'`; stderr 均空 | `docs/changes/tool-cli/acceptance-v1-ceda596/groupA-greet/repeats.log` | 2026-10-19T20:33:49+08:00 | 通过 (稳定复现) |

两行的"实际结果"均为我当场运行所得, 不是读代码或文档推断; 本轮没有"推断"或"引用旧观察"行.

## 差异说明

D-1 结尾换行: 判据写"标准输出为 `Hello, Ada!`"(AC-001-2 同理 `HELLO, ADA!`), 而实际 stdout 在期望文本之后多一个换行字节 `\n` (od -c 显示 `... A d a ! \n`, 共 12 字节, 无空格/回车/其它隐藏字符).

我的判定: 通过. 理由:
1. 判据用的是行内代码块包住期望字符串, 表达的是"这一行文本内容", 不是逐字节长度契约; 命令行工具用 print 输出默认带行尾换行, 这是"输出该行"的通行形式, 而不是在文本里多了内容.
2. 期望文本本身逐字符一致, 大小写与标点 (`Hello, ` 逗号+空格, 结尾 `!`) 完全符合, 也符合 BR-001 (以 `Hello` 开头, 接分隔符与姓名, 以 `!` 结尾, 全大写模式整体转大写).
3. 若把行尾换行判为不符, 则该判据在任何常规 CLI 输出下都不可能满足, 与"标准输出为某一行文本"的正常语义不符.

同时说明: 差异确实存在且是真实存在的字节级差异, 我没有隐去; 若后续验收口径要求 stdout 严格等于 12 字节减 1 的 `Hello, Ada!` 而无换行, 那么这两条应改判失败, 请以该口径复核.

## 未做 / 边界

- 只做了 AC-001-1 与 AC-001-2. 未验证 AC-002-1 (词数统计), 未做 BR-002 依赖审计, 未评价代码质量; 这些属其他验收者范围, 本文件不引用、不代言.
- 未读 `tool.py` 源码, 未运行 pytest 或仓库内其他测试; 判定完全来自上面的实际命令执行.
- 未修改产品代码 / 配置 / 测试, 未执行 `git commit` / `git push`.

## 本轮在该目录新增的文件

- `run.sh` (执行与取证的辅助脚本, 非 pytest 收集目标)
- `AC-001-1.log`, `AC-001-2.log`, `repeats.log`
- `RESULT.md` (本文件)

过程偏差 (主动披露): `run.sh` 生成的 `*.stdout.bin` / `*.stderr.bin` 临时文件在写入 log 后立即删除, 全程位于本目录内; 但 `repeats.log` 那次重复检查使用了 `/tmp/e.bin` 作为 stderr 临时文件 (已删除), 该临时文件放在了证据目录之外, 不符合"临时文件也只放这个目录"的约束. 该文件不含验收产物, 仅用于捕获 stderr 字节, 结论不依赖其留存. 除此之外未在仓库任何其它位置写入或改动文件.
