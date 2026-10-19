# 验收会话记录 session.md

- 会话名: acc-wc-1-1
- pi session id: 01a15522-5573-7012-a841-9530f4d926b7
- 会话进程起始时间: 2026-10-20T01:08:11+08:00 (ps -o lstart= 取本轮 shell 进程启动时刻)
- 开始时间: 2026-10-20T01:08:09+08:00 (首个命令执行时刻)
- 结束时间: 2026-10-20T01:08:34+08:00
- 工作区: /tmp/orchestra-14/ts001-green, 分支 main
- 目标提交核对: `git rev-parse HEAD` = b519339db7d0d1ec723aef311fef7d17f2810bce, 与要求一致

## 身份

本轮独立产品验收者, 只做验收, 不做实现与修复.

## 承接的 3 条标准 (判据只取 PRODUCT.md 原文)

1. AC-001-1 (验收标准/运行行为): `printf 'alpha beta gamma\n' | bin/wordcount` 输出为 `3`, 退出码为 0.
2. AC-002-1 (验收标准/运行行为): 假定 `samples/notes.txt` 内容是 `alpha beta` 加一个换行; 运行 `bin/wordcount --file samples/notes.txt` 输出为 `2`, 退出码为 0.
3. BR-001 (业务规则/审计): 既有测试 `tests/run.sh` 不得被改动.

## 逐条结论

| 编号 | 材料类型 | 实际操作 | 实际结果 | 证据位置 | 时间 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 运行行为 | 实跑 `printf 'alpha beta gamma\n' | bin/wordcount`, 并用 `od -c` 核对输出字节 | 输出 `3` 加一个换行 (共 2 字节), 退出码 0 | docs/changes/wordcount/verify/round-1/ac-001-1.log | 2026-10-20T01:08:19+08:00 (复跑 01:08:34) | 通过 |
| AC-002-1 | 运行行为 | 先用 `od -c samples/notes.txt` 核对内容, 再实跑 `bin/wordcount --file samples/notes.txt` | 文件 11 字节 = `alpha beta` 加换行; 输出 `2` 加一个换行, 退出码 0 | docs/changes/wordcount/verify/round-1/ac-002-1.log | 2026-10-20T01:08:22+08:00 (复跑 01:08:34) | 通过 |
| BR-001 | 审计/静态材料 | 用 git 历史与 blob 哈希比对 tests/run.sh 的引入版与 HEAD 版, 并核对工作区文件哈希 | 该文件仅由 cc48f65 引入, 至 HEAD blob 恒为 a85d460..., `git diff cc48f65 HEAD -- tests/run.sh` 输出为空, 工作区哈希与版本库一致 | docs/changes/wordcount/verify/round-1/br-001.md | 2026-10-20T01:08:31+08:00 | 通过 |

BR-001 的通过依据是静态材料核对 (git 历史与内容比对), 未以运行 tests/run.sh 的结果作为该项证据.

## 实际执行过的命令清单 (按时间顺序, 全为只读或产品运行)

1. `git rev-parse HEAD` ; `git status --porcelain` ; `date -Is`
2. `ls -la` ; `git log --oneline -5`
3. `cat docs/changes/wordcount/PRODUCT.md` (读判据原文)
4. `cat README.md` ; `od -c samples/notes.txt` ; `cat bin/wordcount` ; `cat tests/run.sh` (只读了解入口)
5. `env | grep -i ^PI_` ; `ps -o lstart= -p $$` (取会话 id 与进程起始时间)
6. `git log --oneline --all -- tests/run.sh` ; `git log --follow --format=... -- tests/run.sh`
7. `printf 'alpha beta gamma\n' | bin/wordcount` ; `code=$?` (AC-001-1 实跑)
8. `git log --format=... -4` ; `git rev-parse cc48f65:tests/run.sh` ; `git rev-parse HEAD:tests/run.sh` ; `git diff cc48f65 HEAD -- tests/run.sh` ; `git log -p --follow -- tests/run.sh`
9. `date -Is` ; `printf 'alpha beta gamma\n' | bin/wordcount` ; `code=$?` (AC-001-1 正式留证)
10. `date -Is` ; `od -c samples/notes.txt` ; `wc -c < samples/notes.txt` ; `git status --porcelain samples/notes.txt` ; `git log --format=... -- samples/notes.txt` ; `git rev-parse HEAD:samples/notes.txt`
11. `date -Is` ; `bin/wordcount --file samples/notes.txt` ; `code=$?` (AC-002-1 实跑)
12. `git log --format=...` ; `git branch -a --contains 4187edb` ; `git show --stat b519339`
13. `git hash-object tests/run.sh` ; `git rev-parse HEAD:tests/run.sh` ; `git rev-parse cc48f65:tests/run.sh` ; `git status --porcelain -- tests/ samples/ bin/` ; `git diff --stat HEAD`
14. `git show --stat 4187edb` ; `git diff cc48f65 4187edb -- tests/`
15. BR-001 取证命令组合, 逐条命令与输出见 br-001.md 第 1-5 节
16. `printf 'alpha beta gamma\n' | bin/wordcount | od -c` ; `bin/wordcount --file samples/notes.txt | od -c` ; 两条命令各再跑一次取退出码 (稳定性复跑)

## 未参与本次实现与修复 -- 可核对事实

- 本会话 (shell 进程) 起始时间 2026-10-20T01:08:11+08:00, 首个命令时刻 2026-10-20T01:08:09+08:00.
- 实现提交 beb0ebf (feat: ISSUE-01: 实现 wordcount) 与合并提交 4187edb (merge: issue/01) 的提交时间均为 2026-10-20T00:49:43+08:00, 早于本会话约 18 分钟.
- 目标提交 b519339 (fixture) 提交时间 2026-10-20T01:06:36+08:00, 同样早于本会话.
- 本会话操作记录里没有任何实现或修复动作: 未写入 bin/ tests/ samples/, 未编辑 PRODUCT.md / EXECUTION.md / issues/.
- 本会话唯一写入位置是 docs/changes/wordcount/verify/round-1/ (新建目录, 未被跟踪); `git status --porcelain` 全程只出现 `?? docs/changes/wordcount/verify/` 一项, 无任何被跟踪文件被修改.
- 全程未执行 git add / git commit / git push / git merge 等写仓库历史的命令.

## 方法与过程说明 (便于复核)

- 管道场景取产品退出码: 直接执行 `printf ... | bin/wordcount` 后立即读 `$?`, 管道状态即最右进程 bin/wordcount 的退出码, 不受 printf/echo 干扰.
- 首次记录 AC-001-1 时曾把管道放进命令替换里取 PIPESTATUS, 导致退出码显示为空; 该写法作废, 已改用上述直接取 `$?` 的方式重新取证, 最终 ac-001-1.log 为重新生成的正确记录.
- 两条运行项各执行了两次 (01:08:19 / 01:08:22 与 01:08:34), 结果与退出码一致, 未出现需要按失败重跑的失败.

## 与 PRODUCT.md 原文的一致性核对

- 未发现实现与 PRODUCT.md 原文不一致之处: 两场景输出值与退出码均与原文逐字相符, 输出无多余字符.
- 本轮无"失败/未验证"条目, 故不涉及去向归类 (明确实现问题 / 缺产品规则 / 权限与环境缺口).
