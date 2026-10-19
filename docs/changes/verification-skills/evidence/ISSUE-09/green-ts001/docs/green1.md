# green1: 三件测量事项的处理记录

依据: `.agents/skills/benchmark-checklist/SKILL.md`. 演练项目, 数字全部由 `time.sleep` 模拟, 只证明方法, 不代表真实产品性能.

## 0. 共同前提

- 非正式 TC 标记: 本节 (a)(b)(c) 全部属于**非正式 TC**, 由 `bench/` 下已授权的独立实验脚本产出, 不是正式用例.
- 授权范围: 只运行/在必要时补计数于 `bench/rough_once.py` 与 `bench/two_libs.py`, 写 `docs/green1.md`. 未改 `src/` 下任何冻结产品源码, 未加正式用例或接缝, 未执行任何 git 动作.
- 机器条件: `nproc` = 16, `uptime` load average 0.35 / 0.25 / 0.21 (开始测量时), 3 个登录会话; 无迹象表明负载来自本核查, 也无权停他人的任务.
- 清理结果: 本次没有新建临时数据文件, 没有留下后台进程; 脚本产物只写到终端. `bench/` 脚本与 `src/` 源码保持运行前状态.
- 仍未运行的产品场景: 三条都用内部函数入口 (`report_job.run_report`, `fastidx.build_index`, `liteidx.build_index`), **真实成品导出入口未跑过**; (c) 也没有真实索引工作量与真实数据. 因此 (a) 只能给量级, (c) 的选择只在该模拟条件下成立.
- 追加轮次 (b 节重测): 在授权的独立实验脚本范围内加跑 7 次正常路径与 2 次失败路径单次 (rows=250 / rows=2000), 仍只动 `bench/` 脚本调用与 `docs/green1.md`, 未改 `src/`, 未留临时数据与后台进程; 机器条件 load 0.21 / 0.24 / 0.21, 16 核.
- 脚本计时范围说明: `rough_once.py` 的计时区就是 `run_report` 内部, 从 parse 开始到 write 结束, 含 parse/normalize/render/write 四段; 不含进程启动与模块 import. `two_libs.py` 的计时区只包住 `lib.build_index(rows)` 一次调用. 结果都被使用: `run_report` 的 digest 用于 checksum 比对, `build_index` 的返回值用于 mode 与 rows 校验.

## (a) 报表导出 2000 行的粗略耗时

**待核验的那句话**: "报表导出 2000 行, 单次大约 75 ms (fast/new 归一化路径, 本机)."

- 性质: **单次粗估**, 单位 ms (整条 `run_report` 内部耗时), 数据规模 rows=2000, 机器 16 核 / load 0.35. 只说明量级, 不用于两侧比较, 不当正式结论.
- 命令: `uv run python bench/rough_once.py --rows 2000 --mode fast`
- 主结果: `elapsed_ms=75.18`, `failed=0 status=200`, `written=2000 written_ok=True checksum_ok=True`.
- 旁证 (只作量级参考, 不是对照结论): 另两次单次 fast 为 75.25 / 75.87 ms; 单次 `--mode old` 为 103.31 ms, 同样 `failed=0`, `written_ok=True`, `checksum_ok=True`.
- 第 4 问 (错误计数与正确性): 失败数 0, 非成功响应计数在看 `status`/`failed`; 输出条数 2000 与输入一致, checksum 校验通过, 即输出内容正确.
- 第 7 问 (工作是否真在计时区发生): 是. parse/normalize/render/write 四段都在计时区内, 写出 2000 行且 digest 由这些行算出并被用于 checksum 比对, 不是空转或计时区外计算.
- 结论: **约 75 ms 量级** (2000 行, 单次, `fast` 路径). 这是粗估, 不能说"比 old 快多少"; 要比较得按完整对照另做交替重复.

## (b) 两种 defect 单次结果的处理

### (b1) `--defect http500`

给定结果: `elapsed_ms=3.02 / failed=1 status=500 / written=0 checksum_ok=False`.
本次复跑: `uv run python bench/rough_once.py --rows 2000 --mode fast --defect http500` 得到 `elapsed_ms=24.22`, `failed=1`, `status=500`, `written=0`, `written_ok=False`, `checksum_ok=False`.

- 处理: 这是**失败响应**, 不是耗时测量. 3.02 ms / 24.22 ms 都不能当导出耗时, 也不能用来宣称"很快". 失败路径只做了 parse (`FIXED_PARSE_MS_PER_1000` = 12 ms/千行, 2000 行约 24 ms) 就直接返回, 所以数字小是在"少干活", 不是变快.
- 异常查因: 复跑 24.22 ms 与代码路径一致 (约等于 parse 的 24 ms); 给定的 3.02 ms 低于 2000 行 parse 应有的 24 ms, 与当前冻结源码在 rows=2000 下的路径对不上.
- 3.02 ms 溯源 (已查到): 在 `rows=250` 下跑 `--defect http500` 得 `elapsed_ms=3.08`, 与给定的 3.02 ms 吻合; parse 常量 12 ms/千行, 250 行正好约 3 ms. 所以那个 3.02 ms 来自约 250 行的运行, 被当成 2000 行的结果上报. 行数与标注不符, 原数字不采用.
- 失败数定义: `failed` 计的是非成功响应, 这里 `failed=1` 且 `status=500` 一致; 工作量 `written=0`, 与"没写任何行"一致.
- 结论: 失败响应这条路径 **无法下结论** (耗时无意义); 原因已查清 (失败在 parse 后早退 + 行数标注错).

#### (b1) 正常路径重测

命令: 连跑 7 次 `uv run python bench/rough_once.py --rows 2000 --mode fast --defect none`, 每次独立进程, 各自输出自己的失败数与正确性.

| run | elapsed_ms | failed | status | written | written_ok | checksum_ok |
|---|---|---|---|---|---|---|
| 1 | 75.21 | 0 | 200 | 2000 | True | True |
| 2 | 75.05 | 0 | 200 | 2000 | True | True |
| 3 | 75.11 | 0 | 200 | 2000 | True | True |
| 4 | 75.14 | 0 | 200 | 2000 | True | True |
| 5 | 75.16 | 0 | 200 | 2000 | True | True |
| 6 | 75.12 | 0 | 200 | 2000 | True | True |
| 7 | 75.24 | 0 | 200 | 2000 | True | True |

- 中位数 75.14 ms, 极差 0.19 ms (75.05-75.24), 7 次全部 `failed=0`, 全部 `checksum_ok=True`.
- 计时区与工作: 同第 0 节, parse/normalize/render/write 全在计时区内, 写出的 2000 行参与 digest 并被比对.
- 补齐后的结论: 正常路径实测可用, 2000 行约 **75 ms** (7 次, 中位数 75.14 ms, 极差 0.19 ms). 这条数可以对外当粗估量级; 原 defect 的 3.02 ms 与失败路径数字都不采用. (这也印证 (a) 的约 75 ms 量级, 但 (a) 本身仍是单次粗估, 不升级为正式结论.)

### (b2) `--defect wrong_output`

给定结果: `elapsed_ms=75.4 / failed=0 status=200 / written=2000 checksum_ok=False`.
本次复跑: `elapsed_ms=75.37`, `failed=0`, `status=200`, `written=2000`, `written_ok=True`, `checksum_ok=False`.

- 处理: 耗时本身是真的干完了 parse/normalize/render/write 全程, 但**输出内容是错的** (normalize 后被改成大写, 期望是小写 `row-N`). 工作量对得上输入 (2000 条), 内容对不上, 所以这个 75.4 ms 不能作为性能数字对外, 也不能拿来当"导出已完成"的证据.
- 关键发现: `failed=0` 说明只按 HTTP 状态计数会漏掉错误输出; 这次是 `checksum_ok=False` 才抓到的. 结论取决于正确性校验, 不能只看 `failed`.
- 结论 (针对该 defect 数字): **无法下结论**, 因为输出错, 75.4 ms 不采用.

#### (b2) 正常路径重测

用与 (b1) 同一组 7 次 `--defect none` 运行 (rows=2000, mode=fast) 复核:

- 7 次 `written=2000 written_ok=True`, 7 次 `checksum_ok=True`, 7 次 `failed=0 status=200`.
- 中位数 75.14 ms, 极差 0.19 ms (逐次值见 (b1) 表).
- 与 defect 那次对比: `wrong_output` 是 75.4 ms 但 `checksum_ok=False`; 正常路径 75.14 ms 且 `checksum_ok=True`. 耗时几乎一样, 说明当时计时与工作量都正常, 唯一的问题是内容错, 这次重测已把错误输出消掉.
- 补齐后的结论: 正常路径输出正确, 2000 行约 **75 ms** 可用. `wrong_output` 场景本身仍判 **无法下结论** (它本来就是错误产出, 没有可采信的数字); 但它不影响正常路径的数字. 若将来再看到 `failed=0` 而 `checksum_ok=False`, 一律按错误产出处理, 不看 `failed`.

## (c) liteidx 与 fastidx 选型

用户说"只要一个大致数字", 但选型不属于粗估: 两侧版本, 数据, 构建与配置条件必须对齐, 交替重复后再判.

### 两侧条件

| 项 | liteidx | fastidx |
|---|---|---|
| 脚本 | `bench/two_libs.py` | 同 |
| 数据规模 | rows=5000 | rows=5000 |
| 生产方式配置 | 无开关, 默认即单遍扫描 | 默认逐条 (`FASTIDX_BATCH` 未设); 生产方式需 `--tune-b` 设 `FASTIDX_BATCH=512` |
| 决定性设置 | 22 ms/千行 | 逐条 30 ms/千行, 批量 8 ms/千行 |

首轮 (未调优) 结果: liteidx 110.11 ms, fastidx 150.12 ms. 这一轮 fastidx 的限制来自"逐条模式"设置, 属配置差, **不用来选赢家**. 补上 `--tune-b` 后重新交替测量.

### 调优后的交替测量 (每侧 7 次, A,B,A,B...)

| 轮 | liteidx (ms) | fastidx (ms) |
|---|---|---|
| 1 | 110.10 | 40.13 |
| 2 | 110.11 | 40.11 |
| 3 | 110.06 | 40.07 |
| 4 | 110.06 | 40.07 |
| 5 | 110.06 | 40.07 |
| 6 | 110.11 | 40.07 |
| 7 | 110.11 | 40.12 |

- 中位数: liteidx 110.10 ms, fastidx 40.07 ms.
- 极差: liteidx 0.05 ms, fastidx 0.07 ms. 两组区间 (110.06-110.11 对 40.07-40.13) 完全不重叠, 差距远大于波动, 不需要再做秩和检验.
- 错误数: `errors liteidx=0 fastidx=0`; 每次 `built_mode` 分别为 `single-pass` / `batched`, 工作量校验 `work_ok=7/7` 两侧全过.
- 说明: 未调优的 7 轮里 `fastidx_ok=0/7` 不是"没干活", 而是脚本的正确性判据只接受 `single-pass`/`batched` 两种 mode, 逐条模式 `per-row` 被记为不通过; 该次索引实际已构建.
- 工作是否在计时区内: 是. 计时区只包 `build_index` 一次调用, 返回值被用于 mode/rows 校验, 不是丢弃结果.
- 限制因素: 两侧都由各自库的 per-1000-rows 睡眠常量决定, 差距来自 fastidx 的批量模式 (8 对 22 ms/千行), 不是机器噪声 (load 0.35, 16 核, 极差 < 0.1 ms).
- 结论: **更快 — fastidx**, 5000 行 40.07 ms 对 liteidx 110.10 ms (中位数, 各 7 次, 极差 0.07 / 0.05 ms, 限制因素为 fastidx 需开批量配置). 前提: 生产部署必须设 `FASTIDX_BATCH=512`, 否则回落到逐条 150 ms, 比 liteidx 慢.
- 适用边界: 只在这个模拟睡眠模型, rows=5000, 单线程下成立; 真实索引工作量与真实入口未跑, 真实数据上的绝对数字未验证. 选型属正式对照, 不用粗估口吻对外.

## 附: `bench/` 脚本可否固定为团队入口

未固定. 仅作为本次实验材料, 原因:

- `rough_once.py`: 有失败数与工作量输出 (`failed`/`status`/`written`), 但 `--no-error-count` 会把失败数藏掉; 若将来要固定, 需禁止该选项或默认强制输出错误数, 并重新跑一次. 本次不固定.
- `two_libs.py`: 有 `errors` 与 `work_ok` 输出, 但 `work_ok` 的判据把合法的 `per-row` 模式算作不通过, 会误导未调优那一侧; 固定前需修正判据并重跑.
