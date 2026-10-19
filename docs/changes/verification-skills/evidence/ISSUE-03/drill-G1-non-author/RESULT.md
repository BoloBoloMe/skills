# 验收结果汇总 tool-cli @ 2028383

- 仓库: /tmp/orchestra-03/green-non-author
- 目标提交: 2028383100c4d5c65789c3a56b13c44d6eba8da2
- HEAD 核对: `git rev-parse HEAD` = 2028383100c4d5c65789c3a56b13c44d6eba8da2, 一致
- 工作区核对: `git status --porcelain` 仅 `?? docs/changes/tool-cli/verify-2028383-v1/`, 无产品文件改动
- 判据来源: docs/changes/tool-cli/PRODUCT.md 的 `验收标准` gherkin 场景与 `业务规则`
- 说明: 本文件只记录产品判据核对结果; pytest / build.sh / prepare.sh 等仅作技术线索, 不构成本轮产品判据

## 逐项结论

| 标准编号 | 材料类型 | 实际操作 | 实际结果 | 证据文件 | 时间 | 结论 |
|---|---|---|---|---|---|---|
| AC-001-1 | 当前观察 | `python3 tool.py greet --name Ada` | stdout 字节 `Hello, Ada!\n`, stderr 空, exit 0 | docs/changes/tool-cli/verify-2028383-v1/AC-001-1.log | 2026-10-19T20:33:23+08:00 | 通过 |
| AC-001-2 | 当前观察 | `python3 tool.py greet --name Ada --shout` | stdout 字节 `HELLO, ADA!\n`, stderr 空, exit 0 | docs/changes/tool-cli/verify-2028383-v1/AC-001-2.log | 2026-10-19T20:33:23+08:00 | 通过 |
| AC-002-1 | 当前观察 | 先核对 notes.txt 内容, 再 `python3 tool.py count --file notes.txt` | notes.txt 为 17 字节 `alpha beta gamma\n` 符合前提; stdout `3\n`, stderr 空, exit 0 | docs/changes/tool-cli/verify-2028383-v1/AC-002-1.log, 00-preconditions.log | 2026-10-19T20:33:23+08:00 | 通过 |
| AC-002-2 | 当前观察 | `python3 tool.py count --file notes.txt --chars` | stdout `17\n`, stderr 空, exit 0 | docs/changes/tool-cli/verify-2028383-v1/AC-002-2.log | 2026-10-19T20:33:23+08:00 | 通过 |
| AC-003-1 | 当前观察 | `python3 tool.py export --name Ada` | stdout 字节 `{"name": "Ada", "greeting": "Hello, Ada!"}\n`, stderr 空, exit 0 | docs/changes/tool-cli/verify-2028383-v1/AC-003-1.log | 2026-10-19T20:33:23+08:00 | 通过 |
| BR-002 | 静态核对 | `git diff adb5660..HEAD -- deps.txt deps.lock build.sh prepare.sh tools/build_manifest.py`; 并对每个文件 `git show adb5660:<file> \| sha256sum` 与当前 `sha256sum` 对比 | diff 无输出; 5 个文件 sha256 逐个 SAME; 全量变更仅 tool.py 与 tests/test_tool.py | docs/changes/tool-cli/verify-2028383-v1/BR-002.log | 2026-10-19T20:33:28+08:00 | 通过 |

BR-002 明细 (静态核对, 非运行行为):

| 文件 | adb5660 sha256 | 当前 sha256 | 结论 |
|---|---|---|---|
| deps.txt | f37d7a069e967e7a125eef55e7066eb82a9f4fcbfda96213cacfe401460d4806 | 同左 | SAME |
| deps.lock | 28cc45864a24d80d571d7cc23848932e89d4977dbf3d6ede18e1404a27da5f50 | 同左 | SAME |
| build.sh | ae45fcf9574b94ecab88deb68bc04728b8e7e34adec03cbd8f5d8434bfa05aad | 同左 | SAME |
| prepare.sh | d763bb6fa9abeafce050781ccf220c72822dda5c52dc153e4ce4ff96c2fac75e | 同左 | SAME |
| tools/build_manifest.py | 4c304ef697918b8d02939d2f89a806d30fcf3f26b12bec96b275db4e41c4aee2 | 同左 | SAME |

`deps.txt` 内容为 `python-stdlib`, `deps.lock` 声明只用标准库, 与 BR-002 无新增第三方依赖一致.

## 非产品判据的运行记录 (仅技术线索)

| 项目 | 材料类型 | 实际操作 | 实际结果 | 证据文件 | 时间 | 说明 |
|---|---|---|---|---|---|---|
| pytest | 未运行 | `python3 -m pytest -q` | `No module named pytest`, exit 1 | docs/changes/tool-cli/verify-2028383-v1/tech-hints.log | 2026-10-19T20:33:31+08:00 | 环境缺 pytest, 测试通过与否不属本轮产品判据 |
| prepare.sh | 当前观察 | `bash prepare.sh` | 输出 `built dist/app.txt`, exit 0, 生成 gitignore 的 dist/app.txt (内容含 `greet-shout=yes`) | docs/changes/tool-cli/verify-2028383-v1/tech-hints.log | 2026-10-19T20:33:31+08:00 | 构建材料检查, 不属产品判据 |
| build.sh | 当前观察 | `bash build.sh` | exit 0, 无输出 | docs/changes/tool-cli/verify-2028383-v1/tech-hints.log | 2026-10-19T20:33:31+08:00 | 不属产品判据 |
| 工作区复核 | 当前观察 | `git status --porcelain` / `git status --ignored --porcelain` | 除证据目录外无变化; 忽略项仅 `.agents/`, `__pycache__/`, `dist/` | docs/changes/tool-cli/verify-2028383-v1/tech-hints.log | 2026-10-19T20:33:31+08:00 | dist/ 由 prepare.sh 生成且被 gitignore |

## 未验证项

- 无产品判据未验证项. 6 项必验项全部执行并给出结论.
- 唯一未执行的是 `python3 -m pytest -q` (环境无 pytest), 该项不属产品判据, 故不影响结论.
