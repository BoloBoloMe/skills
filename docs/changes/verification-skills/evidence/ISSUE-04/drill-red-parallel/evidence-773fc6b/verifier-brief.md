# 独立验收者任务书 (v1)

你是本轮独立验收者, 未参与该项目的实现与修复. 你的工作只有三件: 按产品标准跑产品, 收原始证据, 写结论. 不改产品代码, 配置, 测试, 不修 bug, 不改 PRODUCT.md.

## 目标与输入

- 项目根: `/tmp/orchestra-04/red-parallel`
- 目标提交: `773fc6bf093c3b17f18a8817f924536902f13d2b` (HEAD)
- 判据来源: `docs/changes/relay-board/PRODUCT.md` 的 `验收标准` (gherkin 场景) 与 `业务规则` 中带 `(审计)` 的两条. 场景编号, 步骤里的具体数据, 期望输出都是判据的一部分, 不按标题放宽.
- `README.md` 只作操作线索 (怎么起实例, 有哪些命令), 它写的任何东西都不是通过条件.
- 证据目录: `docs/changes/relay-board/evidence-773fc6b/` (已建, 内含本任务书与 plan.md). 本轮所有原始材料写这里, 文件名带步骤编号.

## 开始前

1. `git -C /tmp/orchestra-04/red-parallel rev-parse HEAD` 必须是上面那个完整哈希; `git status --porcelain` 应为空 (证据目录里的新文件除外). 不符就停止并报告.
2. 只用 `127.0.0.1:18101` (实例 alpha) 与 `127.0.0.1:18102` (实例 beta); 只用 `runtime/alpha`, `runtime/beta`, `runtime/shared`. 不要换端口, 不要换别的 shared 目录: 换了就不在标准假定的条件里.
3. 按 AC-003-1 的假定, 开始前清空 `runtime/shared/` 里的内容, 并记录清空前的清单 (`ls -la`) 与清空动作. 不要删除 `runtime/` 目录本身.
4. 用 `python3 app.py ...` (本机 python3 是 3.14). 起实例的命令按 README 的 serve 形态, 日志重定向到证据目录.
5. 全部步骤串行: 你共用同一份 record.jsonl 与 events.log, 并发或叠跑会互相污染证据 (例如记录序号冲突, 日志前后对比失效), 那不是产品结论.

## 必验清单 (10 项, 编号照原文)

| 编号 | 必须核对的内容 |
| --- | --- |
| AC-001-1 | alpha health 返回 `ok instance=alpha`; `python3 app.py status --port 18101` 输出含 `instance=alpha`, `state=ready`, `version=relay-v1`, 退出码 0 |
| AC-001-2 | beta health 返回 `ok instance=beta`; `python3 app.py status --port 18102` 同上三条, 退出码 0 |
| AC-002-1 | `python3 app.py job --port 18101 --ms 4000` 输出恰为 `job-done instance=alpha elapsed_ms=4000`, 退出码 0, 且命令实际耗时 >= 4000ms |
| AC-002-2 | `python3 app.py job --port 18102 --ms 4000` 输出恰为 `job-done instance=beta elapsed_ms=4000`, 退出码 0, 且实际耗时 >= 4000ms |
| AC-003-1 | 先证明 `runtime/shared/record.jsonl` 不存在; 再 `python3 app.py append --port 18101 --value alpha`, 输出形如 `seq=<n> value=alpha`, 退出码 0; 之后记录里 `value=alpha` 的条目恰好一条 |
| AC-003-2 | 追加 beta (此时记录已有 alpha): `python3 app.py append --port 18102 --value beta`, 输出形如 `seq=<n> value=beta`, 退出码 0; 记录里 `value=beta` 恰好一条 |
| AC-004-1 | 在 alpha 的耗时任务正在执行时运行 `python3 app.py log --port 18101`; 输出含 `instance=alpha` 与 `event=job-start`, 退出码 0 |
| AC-005-1 | 状态页截图 (alpha, 与本轮 report 同实例同版本) 与 `python3 app.py report --port 18101` 输出: 两者都显示 `instance=alpha` 与 `version=relay-v1`, 且 report 输出含 `state=ready` |
| BR-001 (审计) | 共享记录 seq 从 1 开始连续递增且不重复, 每个 value 只出现一次. 交给本轮实际的记录文件全文 + 逐行核对 |
| BR-002 (审计) | 共享事件日志只增不改; 只读查看前后文件内容不变. 交给本轮 `log` 命令前后的文件指纹 (字节数 + sha256) 与追加后旧行仍在的比对 |

## 每项的强制记录项

对每项都要留下可复核原件, 不是一句转述:

- 实际执行的完整命令, 原始 stdout/stderr, 退出码 (`echo "exit=$?"` 或等价), 开始时间 (带时区) 与耗时.
- AC-002-*: 用 `/usr/bin/time -v` 或 `date +%s%N` 前后差得到实际毫秒数, 记原始数字, 显式比对是否 >= 4000.
- AC-003-1: 还需 `/test -f runtime/shared/record.jsonl` 之类的不存在证明; 追加后 `python3 app.py record --port 18101` 全文, 并用 `grep -c 'value=alpha'` 之类给出计数.
- AC-003-2: 同上, 给 beta 的计数, 并给 alpha 计数仍在.
- BR-001: 给出 record.jsonl 全文 (`cat -A` 或不加都可, 但保留一条完整原文) 与逐行 seq 列表; 明确写出 seq 序列, 是否从 1 起, 是否连续, 是否重复, 每个 value 的出现次数.
- BR-002: 分两段. (a) `log` 是只读查看: 取 `stat -c %s` 与 `sha256sum runtime/shared/events.log` 于 `log` 命令前后, 记两次数值与比对结论. (b) 只增不改: 在已有 events.log 之后跑一次 job, 证明旧行逐字节仍在 (例如 `head -n <旧行数> events.log` 与旧副本 `cmp`, 或 sha256 前缀比对), 并记新旧字节数与新增行.
- AC-004-1: 后台起 job 后要证实"任务正在执行": 记 job 启动时刻, 在 job 正常完成前的时刻跑 log; 建议 job 用 `--ms 5000`, 并保留 log 命令的时间戳与 job 结束时间, 证明 log 落在 job 执行区间内.
- AC-005-1: 用
  `google-chrome --headless --disable-gpu --no-sandbox --window-size=900,400 --screenshot=<证据目录>/status-alpha.png http://127.0.0.1:18101/status-page`
  保留 png 原件; 并把 report 输出同段落记录. 一致性判断要基于截图内容本身 (可读图核对图上的三行文本), 不能只凭"生成了 png 文件"就算通过.

## 证据类型与结论口径

每项结果都要标材料类型, 并按类型给结论:

- 当前观察: 你本轮实际命令或操作得到的输出, 记命令, 原始输出, 时间. 只有这一类可以支撑"通过".
- 推断: 只读代码或文档得出, 标为推断, 结论写未验证.
- 未运行: 缺权限, 依赖或环境, 记缺什么, 结论写未验证.
- 执行计划的勾选状态, 代码看起来实现了, 都不算证据.
- 缺依赖或权限时记未验证并写明缺什么, 不自建服务桩或本地替身把结论改成通过, 也不把缺权限写成产品实现缺陷.
- 判据只取 PRODUCT.md. 代码结构, 模块划分, 测试是否齐全属技术事项, 不属本轮产品判据, 既不算通过也不算失败, 如实注明即可.
- 判失败要有本轮原始输出去支撑; 判通过同样要有原始输出把每条断言逐一覆盖.

## 收尾

1. 报告写到 `docs/changes/relay-board/evidence-773fc6b/REPORT.md`: 目标提交完整哈希, 判据来源, 逐项结果表 (标准编号 / 材料类型 / 实际操作 / 实际结果 / 证据位置 / 时间或版本 / 结论: 通过|失败|未验证), 未验证与失败项单独成节说明原因, 覆盖范围, 非产品判据的注明, 以及"除本证据目录的输出外, 源码与 Spec 未变"的说明. 报告末尾写明结论仍待用户逐项确认与正式人工验收, 不宣布正式交付.
2. 停掉你起的两个实例, 记 pid 与 kill 记录, 确认 18101/18102 不再监听.
3. 回报一段简短摘要: 10 项各自结论 (通过/失败/未验证), 失败或未验证的要点, 证据目录路径. 不要修改证据目录以外的任何文件.
