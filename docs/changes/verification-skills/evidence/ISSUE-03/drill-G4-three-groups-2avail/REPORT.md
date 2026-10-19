# 独立验收报告 (round r1)

- 目标提交 (完整标识): `c0505dee33c9c78ffaaf61f88e05e041a7e29402` (`feat: greet 支持全大写输出`, 提交时间 2026-10-19 20:40:42 +08:00)
- 判据来源: `docs/changes/tool-cli/PRODUCT.md`, `验收标准` 节 (`<!-- confirmed-flow: v1 -->`) 的 8 个场景原文 + `业务规则` 节审计规则 BR-002 原文
- 版本前提: 验收开始时与报告撰写时 `git rev-parse HEAD` 均为上述提交; `git status --porcelain --untracked-files=all` 去掉本轮证据目录后为空 (无已跟踪文件改动, 无其他未跟踪产品文件)
- 证据目录: `/tmp/orchestra-03/heavy/three-groups-2avail/docs/changes/tool-cli/evidence-c0505de-r1/`
- 覆盖范围: 本次变更只新增 `greet --shout`, 但按规则列全 PRODUCT.md 的全部场景与审计 BR, 共 9 项; 未覆盖项 0
- 结论: 8 个场景通过, 1 项审计 BR 通过 (静态材料核对); 失败 0; 未验证 0

## 必验清单逐项结果

材料类型说明: "当前观察" = 本轮验收者实际命令/操作产生的原件; "静态材料核对" = 提交内容比对, 非运行行为结果.

| 标准编号 | 材料类型 | 实际操作 / 引用信息 | 实际结果 | 证据位置 | 时间 / 版本 | 结论 |
|---|---|---|---|---|---|---|
| AC-001-1 默认问候 | 当前观察 | `python3 tool.py greet --name Ada` (仓库根) | stdout 原始 12 字节 `Hello, Ada!`+LF, stderr 空, 退出码 0; 与判据正文逐字节一致 (仅行尾 LF, 判据未禁止) | `verifier-a/ac001-1.stdout`, `.cmdlog`, `.exit`, `.stderr`; `verifier-a/commands.log` (od -c 原始转储) | 2026-10-19T20:44:58+08:00 @ c0505de | 通过 |
| AC-001-2 全大写问候 | 当前观察 | `python3 tool.py greet --name Ada --shout` (仓库根) | stdout 原始 12 字节 `HELLO, ADA!`+LF, stderr 空, 退出码 0; 与判据正文逐字节一致 (仅行尾 LF) | `verifier-a/ac001-2.stdout`, `.cmdlog`, `.exit`, `.stderr`; `verifier-a/commands.log` | 2026-10-19T20:44:58+08:00 @ c0505de | 通过 |
| AC-001-3 批量问候 250 姓名 | 当前观察 | 逐行读 `data/greet/names.txt` (250 行), 每行一次独立 `python3 tool.py greet --name <姓名>` 进程, 共 250 次, 用 `cmp` 逐字节比对 | 250/250 stdout = `Hello, <姓名>!`+LF, 退出码全 0, 失败 0, 耗时 10.243s; 明细 250 行, 序号 1..250 连续; 我核对了明细姓名列与 `data/greet/names.txt` 逐行一致 | `verifier-a/ac001-3.detail.tsv` (250 行), `ac001-3.summary.txt`, `run-batch-greet.sh` | 2026-10-19T20:45:14~20:45:24+08:00 @ c0505de | 通过 |
| AC-002-1 统计词数 | 当前观察 | 仓库根执行 `python3 tool.py count --file notes.txt`; 另核对 `git show HEAD:notes.txt` = `alpha beta gamma`+\n 共 17 字节 | stdout 原始 `3\n` (od -c `3 \n`, 2 字节), 退出码 0, `cmp` 命中 | `verifier-b/ac002-1-2-literal.log`, `out1-literal.txt`, `exp1.txt` | 2026-10-19T20:46:59+08:00 @ c0505de | 通过 |
| AC-002-2 统计字符数 | 当前观察 | 仓库根执行 `python3 tool.py count --file notes.txt --chars` | stdout 原始 `17\n` (od -c `1 7 \n`, 3 字节), 退出码 0, `cmp` 命中 | `verifier-b/ac002-1-2-literal.log`, `out2-literal.txt`, `exp2.txt` | 2026-10-19T20:46:59+08:00 @ c0505de | 通过 |
| AC-002-3 批量统计 250 文件 | 当前观察 | 按 `data/count/expected.tsv` 250 行逐条执行一次独立 `python3 <repo>/tool.py count --file <repo>/data/count/docs/<文件名>` (用绝对路径保证日志可复现, 语义与判据命令相同), 实际输出/期望/退出码逐条落盘 | 250/250 实际输出 = expected.tsv 词数, 退出码全 0, 失败 0; 明细 250 行; 我核对了明细 (文件名, 实际) 与 `expected.tsv` 逐行一致 | `verifier-b/ac002-3-detail.tsv`, `ac002-3.log`, `docs-files.txt`, `run-batch-count.sh` (执行命令逐字抄录), `supplement.log` | 2026-10-19T20:45:59~20:46:10+08:00 @ c0505de | 通过 |
| AC-003-1 JSON 导出 | 当前观察 | `python3 tool.py export --name Ada` (仓库根) | stdout 原始 43 字节 `{"name": "Ada", "greeting": "Hello, Ada!"}`+LF, 空格/引号/逗号逐字符核对, 退出码 0 | `verifier-a/ac003-1.stdout`, `.cmdlog`, `.exit`; `commands.log` od -c | 2026-10-19T20:45:01+08:00 @ c0505de | 通过 |
| AC-003-2 批量导出 200 姓名 | 当前观察 | 逐行读 `data/export/names.txt` (200 行), 每行一次独立 `python3 tool.py export --name <姓名>`, 共 200 次, 逐字节比对 | 200/200 stdout = `{"name": "<姓名>", "greeting": "Hello, <姓名>!"}`+LF, 退出码全 0, 失败 0, 耗时 8.206s; 明细 200 行; 我核对了明细姓名列与 `data/export/names.txt` 一致 | `verifier-a/ac003-2.detail.tsv`, `ac003-2.summary.txt`, `run-batch-export.sh` | 2026-10-19T20:45:25~20:45:33+08:00 @ c0505de | 通过 |
| BR-002 依赖/锁/构建材料与上一提交逐项一致 (审计) | 静态材料核对 (非运行行为结果) | 对比 `HEAD^`=`38724d1f3d249b8f2f5a6478700d2373b1923853` 与 `c0505de`: `git diff HEAD^ HEAD -- deps.txt deps.lock build.sh .gitignore`; 四文件 sha256 双方比对; `git diff --stat`; `tool.py` import 前后比对 | diff 为空; deps.txt `f37d7a06…4806`、deps.lock `28cc4586…6e50`、build.sh `ae45fcf9…5aad`、.gitignore `282a8752…a7ca` 双方完全相同; 全仓 diff 仅 `tool.py` 与 `tests/test_tool.py`; import 前后均为 argparse/json/pathlib/sys, 无新增第三方依赖 | `verifier-b/br002-audit.log` | 2026-10-19T20:46~20:47+08:00, `38724d1..c0505de` | 通过 (静态核对) |

我另外独立复核了: 上述 4 个材料文件的 sha256 与 `git diff --stat` 结果与 verifier-b 材料一致; 批量明细与源数据逐行 join 无差异; `git status` 仅本轮证据目录为新增.

## 需要读者注意的判读细节 (不改变结论, 但如实标明)

1. **行尾换行**: 三个单点场景的 stdout 都是"判据文本 + 一个 LF", 判据写"标准输出为 X"未要求无换行; 判据正文本身逐字节相等, 未靠去掉换行后"看起来像". 三名场景的原始字节均已留档, 读者可自行采用更严口径.
2. **AC-002-3 的命令形态**: verifier-b 用绝对路径调用 `tool.py` 与数据文件, 不是判据里字面的相对路径; 语义与参数一致, 已在材料中注明. 批量循环是内联命令执行, `run-batch-count.sh` 是按当时实际命令的逐字抄录 (材料已自我声明); 我把它与 verifier-b 会话记录里的实际命令原文做了比对, 两者一致.
3. **`PASS=0 FAIL=0 TOTAL=0` 一行**: 出现在 `verifier-b/ac002-3.log` 第 3 行, 是管道左侧子进程计数导致主 shell 读到初值 0 的回显, 不是另一轮 0 条运行; 250 次运行只有一轮 (20:45:59~20:46:10), 明细 250 行, 最终通过数由明细重算得出. 我按明细自行 join 校验, 结论不受该回显影响.
4. **非产品判据**: `TECHNICAL.md` 的 `python3 -m pytest -q` 与 `bash build.sh` 属技术验证入口, 本轮没有把它们的执行结果作为任何场景的通过条件; 实现代码结构, 测试接缝等事项不属产品判据, 本报告不评判.

## 派工记录

计划文件: `DISPATCH-PLAN.md` (同目录).

场景组划分与人数依据:

- 组 A (verifier-a): AC-001-1, AC-001-2, AC-001-3, AC-003-1, AC-003-2; 独占 `data/greet/`, `data/export/`
- 组 B (verifier-b): AC-002-1, AC-002-2, AC-002-3, BR-002; 独占 `data/count/`, git 历史比对
- 拆分收益: 两组输入数据互不共享; 无预构建 (build.sh 只 compileall tool.py), 两次会话没有重复准备成本; 批量子场景 (250 + 200 条 vs 250 条) 是主要耗时, 并行缩短墙钟时间
- 可用非作者验收者人数 2 (本轮授权上限 2), 计划人数 2 = min(有并行收益的组数 2, 可用人数 2); 未拆 3 组, 未只派 1 人

每名验收者:

| 验收者 | Herdr 会话 | pi session 标识 | 创建时间 (UTC) | 模型 / thinking | 承接标准 |
|---|---|---|---|---|---|
| verifier-a | tab `w1J:t49`, pane `w1J:p4B` | `01a15431-088b-707c-939b-1dc526e03f8e` | 2026-10-19T12:44:22Z | cli/deepseek-v4.1-flash-expires-on-0910 / high | AC-001-1, AC-001-2, AC-001-3, AC-003-1, AC-003-2 |
| verifier-b | tab `w1J:t4A`, pane `w1J:p4C` | `01a15431-1447-75a1-b68f-ebbc50315c92` | 2026-10-19T12:44:25Z | cli/glm-5.3-flash / high | AC-002-1, AC-002-2, AC-002-3, BR-002 |

未参与本次实现与修复的可核对事实:

- 两个会话文件创建时间 (12:44:22Z / 12:44:25Z) 均晚于目标提交时间 (2026-10-19 20:40:42+08:00 = 12:40:42Z);
- 两者都是本轮新开 tab, 会话记录首条用户消息是我发出的验收任务 (无实现或修复对话继承, 未使用 `--continue`/`--fork`/`--resume`);
- 会话记录里工具调用只有 `bash` 与 `write`; 三个 `write` 目标全部落在 `evidence-c0505de-r1/verifier-a|b/` 下, 未见对产品文件, 配置或测试的写操作; 我另行确认 `git status` 除证据目录外为空;
- 会话记录原件: `~/.pi/agent/sessions/--tmp-orchestra-03-heavy-three-groups-2avail--/2026-10-19T12-44-22-028Z_01a15431-088b-707c-939b-1dc526e03f8e.jsonl` 与 `...12-44-25-032Z_01a15431-1447-75a1-b68f-ebbc50315c92.jsonl`.

## 材料类型与复核说明

- 全部 9 项均以本轮"当前观察"或"静态材料核对"承接, 无推断项, 无未运行项, 未采用旧轮次观察.
- 我只核对验收者交回的原件, 没有代跑产品入口; 对材料的独立复核限于只读比对 (批量明细与源数据 join, 材料哈希, `git diff`/`git status`).
- 未发现摘要与原件的冲突; 第 2, 3 条判读细节已如实列出, 供读者自行核对原件.

## 收尾

- 除本次证据目录 `docs/changes/tool-cli/evidence-c0505de-r1/` 的输出外, 源码与 Spec 未变 (该目录未被 .gitignore 覆盖, 在 `git status` 中显示为本轮新增未跟踪文件, 这是验收留下的唯一痕迹).
- 本轮未提交, 未推送, 未开 PR.
- 本报告是独立验收结果, 仍需用户逐项确认并安排正式人工验收; 不构成正式交付, 也不关闭用户验收.
