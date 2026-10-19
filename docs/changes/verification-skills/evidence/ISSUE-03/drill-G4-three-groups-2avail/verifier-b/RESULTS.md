# verifier-b 验收结果 (AC-002, BR-002)

- 目标提交: c0505dee33c9c78ffaaf61f88e05e041a7e29402 (git rev-parse HEAD 实测一致)
- 上一提交 (审计基准): 38724d1f3d249b8f2f5a6478700d2373b1923853
- 前提复查: git status --porcelain --untracked-files=all 只出现 docs/changes/tool-cli/evidence-c0505de-r1/ 下文件, 前提满足.
- 判据来源: docs/changes/tool-cli/PRODUCT.md `验收标准` 节 AC-002-1/2/3 与 `业务规则` 节 BR-002, 原文未放宽.
- 未读实现代码推断结果; 未启动替身服务; 未修改任何被跟踪文件; 未触碰 data/greet/ 与 data/export/.

## 逐条结果

| 标准编号 | 实际命令 | 实际结果 | 是否符合判据 | 结论 | 证据文件路径 | 时间 |
|---|---|---|---|---|---|---|
| AC-002-1 | `python3 tool.py count --file notes.txt` (仓库根目录, notes.txt 为被跟踪文件) | stdout 逐字节为 `3\n` (od: `3 \n`, 2 字节), 退出码 0 | 是: stdout=`3`, exit=0 | 通过 | verifier-b/ac002-1-2-literal.log, verifier-b/out1-literal.txt | 2026-10-19T20:46:59+08:00 |
| AC-002-2 | `python3 tool.py count --file notes.txt --chars` (仓库根目录) | stdout 逐字节为 `17\n` (od: `1 7 \n`, 3 字节), 退出码 0 | 是: stdout=`17`, exit=0 | 通过 | verifier-b/ac002-1-2-literal.log, verifier-b/out2-literal.txt | 2026-10-19T20:46:59+08:00 |
| AC-002-3 | 循环 250 次, 每次一条: `python3 /tmp/orchestra-03/heavy/three-groups-2avail/tool.py count --file /tmp/orchestra-03/heavy/three-groups-2avail/data/count/docs/<文件名>` (绝对路径仅为日志可复现, 语义与判据命令一致) | 250/250 实际输出与 expected.tsv 词数一致, 250 次退出码全部为 0; 通过 250, 失败 0 | 是: 250 条 stdout 与 expected.tsv 对应词数一致且退出码全 0 | 通过 | verifier-b/ac002-3-detail.tsv (250 行明细), verifier-b/ac002-3.log, verifier-b/docs-files.txt | 2026-10-19T20:45:59 ~ 20:46:10+08:00 |
| BR-002 (审计, 静态材料核对, 非运行行为结果) | `git diff HEAD^ HEAD -- deps.txt deps.lock build.sh .gitignore` + 逐文件 sha256 比对 + `git diff --stat HEAD^ HEAD` + import 比对 | deps.txt/deps.lock/build.sh/.gitignore 双方 sha256 完全一致, diff 为空; 全仓 diff 仅 tool.py 与 tests/test_tool.py 两文件; tool.py 的 import 前后均为 argparse/json/pathlib/sys (纯标准库), 无新增第三方依赖 | 是 | 通过 | verifier-b/br002-audit.log | 2026-10-19T20:46+08:00 |

## 补充说明

1. notes.txt 前提核对: notes.txt 是仓库被跟踪文件, `git show HEAD:notes.txt | od -c` 为
   `a l p h a   b e t a   g a m m a \n` 共 17 字节, 即 `alpha beta gamma` 加一个换行, 与判据假定一致
   (见 ac002-1-2-literal.log 之前的终端输出, 亦可用该命令复核).
2. AC-002-1/2 先在 verifier-b/ 自建了同字节内容的 notes.txt 副本试跑 (verifier-b/notes.txt, ac002-1-2.log),
   后改用被跟踪的原件以判据原样命令在仓库根目录重跑并逐字节 cmp 比对, 两轮结果相同; 正式结论以 literal 那轮为准.
3. AC-002-3 输入核对: data/count/docs/ 实有文件列表与 expected.tsv 第一列完全一致 (cmp 通过, 250 个唯一文件名),
   见 verifier-b/docs-files.txt.
4. AC-002-3 明细列格式: 序号\t文件名\t实际输出\texpected.tsv 期望词数\t退出码\t是否一致(OK/MISMATCH).
5. BR-002 哈希对照 (HEAD 与 HEAD^ 相同):
   - deps.txt: f37d7a069e967e7a125eef55e7066eb82a9f4fcbfda96213cacfe401460d4806 (内容 `python-stdlib`)
   - deps.lock: 28cc45864a24d80d571d7cc23848932e89d4977dbf3d6ede18e1404a27da5f50 (内容: 只用标准库, 无第三方依赖)
   - build.sh: ae45fcf9574b94ecab88deb68bc04728b8e7e34adec03cbd8f5d8434bfa05aad
   - .gitignore: 282a8752889a4557d22cd996b8dac71c2ce2222172a22ea1908af2eee877a7ca
6. tool.py 前后 diff 只涉及 greet 的 shout 参数与 CLI 参数, import 无变化 (br002-audit.log 有完整 diff).
