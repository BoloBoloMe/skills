# G3 验收报告: export + BR-002 审计 (独立验收者)

- 目标提交: c0505dee33c9c78ffaaf61f88e05e041a7e29402 (HEAD, `git rev-parse HEAD` 实测一致)
- 上一提交 (BR-002 比对基线): 38724d1f3d249b8f2f5a6478700d2373b1923853
- 执行时间: 2026-10-19T20:44:16+08:00 至 2026-10-19T20:44:35+08:00 (见各日志首末行时间戳)
- 执行环境: Python 3.14.7, 工作目录 /tmp/orchestra-03/heavy/three-groups-3avail, 只读被验项目 (未改源码/配置/测试/data; `git status --porcelain` 仅显示本轮新增证据目录)
- 材料类型说明: "当前观察" = 本次实测; "静态材料核对" = git 内容比对, 非运行行为; "推断"/"未运行" 均不判通过.

## 逐项结论

| 标准编号 | 材料类型 | 实际操作 (命令) | 实际结果 | 证据位置 | 时间 | 结论 |
|---|---|---|---|---|---|---|
| AC-003-1 JSON 导出 | 当前观察 | `python3 tool.py export --name Ada` | 标准输出恰为 `{"name": "Ada", "greeting": "Hello, Ada!"}` (单行, 与判据逐字符一致), 退出码 0 | raw/ac-003-1.log | 2026-10-19T20:44:18+08:00 | 通过 |
| AC-003-2 批量导出 200 个姓名 | 当前观察 | 对 `data/export/names.txt` 每行执行 `python3 tool.py export --name <该行姓名>`, 逐条记录 序号/姓名/expected/actual/exit code 到 TSV; 再用 `awk -F'\t'` 比对 (判据: actual==expected 且 exit==0) | names.txt 实测 200 行 (无空行, 无空白字符行); TSV 200 行; 比对输出 `total=200 pass=200 fail=0`; `non_zero_exit_lines=0`; `blank_actual=0` | raw/ac-003-2-loop.log, raw/ac-003-2-results.tsv, raw/ac-003-2-summary.log | 2026-10-19T20:44:21+08:00 至 20:44:32+08:00 | 通过 |
| BR-002 不新增第三方依赖 (依赖清单/锁文件/构建材料与上一提交逐项一致) | 静态材料核对结果 (非运行行为) | `git diff 38724d1 c0505de -- deps.txt deps.lock build.sh`; `git diff --stat` 同上路径; `git diff --name-status 38724d1 c0505de`; `git diff --name-only 38724d1 c0505de -- deps.txt deps.lock build.sh`; 对两提交分别 `git rev-parse <rev>:<file>` 与 `git show <rev>:<file> \| sha256sum`; `git status --porcelain -- deps.txt deps.lock build.sh` | 三文件 diff 输出为空 (diff_exit=0, --stat 无输出); 变更文件清单仅 `M tests/test_tool.py`, `M tool.py`, 不含这三个文件 (--name-only 三文件交集为空); blob 与内容哈希两提交完全相同: deps.txt bbb5297… / f37d7a06…, deps.lock f5f745d… / 28cc4586…, build.sh 7796246… / ae45fcf9…; 工作区三文件哈希与 HEAD 一致, `git status` 对此三文件无输出 | raw/br-002-static.log, raw/br-002-worktree.log | 2026-10-19T20:44:32+08:00 至 20:44:35+08:00 | 通过 (静态材料核对结果, 非运行行为结论) |

## 补充观察 (不作为判据)

- 三文件当前内容: deps.txt 为 `python-stdlib`; deps.lock 为注释 "本工具只用 Python 标准库, 无第三方依赖."; build.sh 仅 `python3 -m compileall -q tool.py`. 见 raw/br-002-worktree.log.
- 变更仅涉及 tool.py 与 tests/test_tool.py, 与本次 export 命令实现 (tool.py 内 `export_payload` 使用 json.dumps 默认分隔符) 一致; 未对 greet/count 场景做任何验证 (不在本轮分派范围).

## 未验证与缺口

- 无未验证项. 三项判据均为当前观察或静态材料核对, 均已实际执行并留原始输出.
- 说明: 批量比对取 `actual` 为命令替换 `$(...)` 的值 (已剥离末尾换行), 判据要求的是"标准输出等于...", 剥离行尾换行不改变可见输出的逐字符一致性; 原始输出行完整保留在 raw/ac-003-2-results.tsv 的 actual 列.
- 本轮未使用任何自建服务桩/本地替身, 未运行 git checkout/commit 等改写命令.
