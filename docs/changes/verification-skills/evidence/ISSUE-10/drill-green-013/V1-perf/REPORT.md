# AC-001-1 导出性能结论 — 独立验收报告 (verify-perf, R1)

## 0. 目标与开工核对

| 项 | 值 |
|---|---|
| 仓库 | /tmp/orchestra-10/methods-green |
| 目标提交 | ea940821115424b7eb619e985b2304f2b61e9d1d |
| 开工前 `git rev-parse HEAD` | ea940821115424b7eb619e985b2304f2b61e9d1d (一致) |
| 开工前 `git status --porcelain` | 仅一行 `?? docs/changes/vault/evidence/` (即我自己被授权写入的证据目录, 未跟踪; 无产品文件改动) |
| 收工时 HEAD / status | 同上, 未变 (见 07-final-state.log) |
| 干净判定 | 干净, 无障碍开工 |

## 1. 判据来源 (唯一)

docs/changes/vault/PRODUCT.md, 标 `<!-- confirmed-flow: v1 -->`, 原文:

```
@AC-001 @normal @G-001
场景: AC-001-1 导出性能结论
  假定 测试数据目录 runtime/data 已初始化
  当 验收者连续 5 次运行 `python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data` 并记录每次耗时
  那么 报告给出 p50 与极差, p50 不超过 800ms, 原始输出可复核
```

本报告只判这一条. 项目无 TECHNICAL.md / EXECUTION.md / 构建脚本 / 测试套件, README.md 仅作操作入口.

## 2. 方法加载记录

- 已按调用者点名, 用 read 工具完整读取 `/tmp/orchestra-10/methods-green/.agents/skills/benchmark-checklist/SKILL.md` (性能测量核查清单).
- 本次按其节次落实: 测量前(待核验结论句 / 计时范围 / 负载与核数), 两侧调优(本条无对照侧, 说明见 3.6), 重复与波动(5 次 + 中位数 + 极差 + 噪声检查), 错误计数与工作是否真的发生, 收益上限与端到端(本条为端到端口径, 无局部优化, 不适用), 基线与脚本固定前(脚本为一次性, 不固定), 判定词.
- 结论状态词: 清单的四个判定词 (更快/更慢/无可测差异/无法下结论) 都是新旧对照口径; 本条是绝对阈值口径 (p50 ≤ 800ms), 因此判定词用 `通过 / 失败 / 未验证`, 并在此声明这一处口径映射, 不改判据.

### 2.1 待核验结论句 (先写结论, 后做测量)

> "在 `--rows 20000` 导出上, 连续 5 次运行的耗时 p50 为 74.193 ms, 极差 5.649 ms (72.569–78.218 ms), 低于 800 ms 阈值."

## 3. 测量条件与方法 (供复核)

### 3.1 环境 (证据: 00-env.txt)

- 时间: 2026-10-20T00:29:46+08:00
- `nproc` = 16; `load average` = 0.14, 0.24, 0.18 (16 核上可忽略)
- 负载来源: 同机另有多个 `pi` 会话进程 (即并行验收的其它 agent) 与 gnome-shell / firefox, 单进程最高约 21% CPU; 我无权停它们, 故记录并在每次运行前后取 loadavg.
- python3 = Python 3.14.7; kernel Linux 7.0.0-31-generic x86_64
- 关键范围限定: 工作目录位于 `/tmp`, 文件系统为 **tmpfs (RAM 支撑)**; 因此下面数字不含物理磁盘 I/O 代价.

### 3.2 计时范围 (计时区内 / 区外)

- 计时工具: bash 取 `date +%s%N` 前后纳秒差, 换算毫秒 (3 位小数), 脚本存 `run-export-5x.sh` (全文在证据目录).
- 计时区**内**: 从 fork/exec `python3` 之前, 到该进程退出之后, 即整条 `app.py export` 进程端到端 — 含 Python 解释器启动、argparse、打开输出文件、20000 次 `json.dumps` + 写入、关闭文件.
- 计时区**外**: 每次运行后的核对 (`wc -l/-c`, `sha256sum`, 首尾行读取), 以及 harness 自身的 sleep 0.3s; 这些不计入.
- 未覆盖 (算不出成本): 代码里**没有 `fsync`/`fdatasync`**, 计时区不包含"数据落到持久介质"; 也不包含 tmpfs 之后的任何回写. 故该数字是"命令返回所耗时间", 不是"持久化完成所耗时间".
- 无随机扰动 / 无固定种子: 该命令本身是确定性写入, 输出 20000 行固定内容.

### 3.3 共用准备 (只做一次, 由我执行)

`python3 app.py init --data-dir runtime/data` → 退出码 0, 输出 `init-ok data-dir=runtime/data`, 耗时 46.16 ms (证据 01-init.txt).
生成 `runtime/data/records.jsonl` (59 B, 2 行) 与 `runtime/data/outbox/replication-log.jsonl` (166 B, 2 行). 满足场景"假定 runtime/data 已初始化".
此后我只跑 export, 未 purge, 未删 runtime/.

### 3.4 命令原文 (每次运行逐字相同, 见 02-run-5x.log)

```
python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data
```

### 3.5 交叉校验 (不进正式 5 次)

同一命令外加 `/usr/bin/time -v` (证据 03-croscheck-time-v.log): `Elapsed (wall clock) = 0:00.07`, User 0.06s, System 0.00s, Exit status 0, Major page faults 0, File system outputs 0 (印证 tmpfs/已在缓存). 与 72–78 ms 区间一致, 说明我的纳秒计时没有量级偏差.

### 3.6 两侧调优一节为何不适用

本条只有一个候选 (当前提交) 与一个绝对阈值, 没有新旧两侧, 也没有库/配置对照, 故"两侧按生产方式等价调优"无从执行; 未被省略的是错误计数与工作量核对 (见 4).

## 4. 逐项结果

### 4.1 主判据: p50 ≤ 800 ms

| 项 | 内容 |
|---|---|
| 标准编号 | AC-001 / AC-001-1 (G-001) |
| 材料类型 | 当前观察 (本轮实跑, 非引用旧观察, 非推断) |
| 实际操作 | 共用准备 init 一次; 随后连续 5 次运行上述原文命令, 每次记录起止 ISO 时间 + 纳秒戳 + 退出码 + stdout/stderr + 运行前后 loadavg + 输出文件字节/行数/sha256/首尾行 |
| 实际结果 (5 次, 运行顺序) | 72.569, 78.218, 74.193, 72.625, 75.095 ms (全部退出码 0, stdout 均为 `export-ok rows=20000 out=runtime/export.jsonl`, stderr 空) |
| p50 | **74.193 ms** (两种算法一致: 线性插值 = 0.5 分位; 5 取近邻秩第 3 个) |
| 极差 (max−min) | **5.649 ms** (72.569 – 78.218 ms); 均值 74.540 ms |
| 阈值比较 | 74.193 ms ≤ 800 ms, 余量约 10.8 倍 |
| 证据位置 | `02-run-5x.log` (原始输出), `06-stats.log` (统计算式与结果), `03-croscheck-time-v.log` |
| 时间 | 2026-10-20T00:29:54 ~ 00:29:56 (+08:00), 统计 00:30:12 |
| 结论 | **通过** |

### 4.2 噪声检查 (是否要另跑一组)

- 判据 (调用者给的): 某次 >2x 中位数 或 比中位数高 >200 ms 即视为噪声, 需单独重跑一组.
- 实测: 无任何一次触发 (2x 检测空, >200 ms 检测空); 相对中位数最大偏离 4.025 ms = 5.43%.
- 5 次之间 loadavg 全程 0.11–0.12 (16 核), 无突变.
- 判定: 无需重跑第二组; 数据稳定, 极差 5.649 ms 属进程启动抖动量级.

### 4.3 错误计数 (清单要求)

| 项 | 值 |
|---|---|
| 失败定义 | 退出码非 0, 或 stderr 非空, 或 stdout 不含 `export-ok rows=20000` |
| 失败数 | 0 / 5 (交叉校验那次也为 0 / 1) |
| 非成功响应数 | 0 |
| 证据 | 02-run-5x.log 每次的 exit_code / stdout / stderr 行 |

### 4.4 工作量与输出正确性 (清单要求: 结果对得上输入)

- 每次运行后: `out_lines = 20000` (= `--rows 20000`), `out_bytes = 908890`, `out_sha256 = f7adaf5b...52805b39`, 首行 `{"id": "row-000000", "text": "payload-0"}`, 末行 `{"id": "row-019999", "text": "payload-19999"}`.
- 5 次运行 sha256 完全相同 → 输出确定, 不存在"某次少写/半写"。
- 独立复核 (04-correctness.log): 用 python 逐行 json 解析全部 20000 行, 与期望 `{"id": row-%06d, "text": payload-%d}` 序列逐条比对 → `all 20000 rows match expected schema/sequence: True`, 不同 id 数 = 20000 (无重复无缺失)。
- mtime 落在对应运行时刻, 说明文件确实在计时区内被重写 (工作真的发生在计时区内)。
- 计时区内发生的工作 (一句说明): 打开 `runtime/export.jsonl` 截断写入, 循环 20000 次序列化并写出固定一行 JSON, 关闭文件; 无"生成器无人迭代 / 异步无人 await / 结果被丢弃"的风险 (命令行工具, 结果即文件).
- 保留了摘要 (行数/字节/sha256/首尾行), 未保留 2 MB 全文.

### 4.5 一处自曝的取证失误 (不影响结论)

`04-correctness.log` 里 `runtime/export-croscheck.jsonl` 的 sha256 当时与 `export.jsonl` 不同. 原因: 我把交叉校验与校验脚本两条命令**并行**发出, 校验进程读过写一半的文件. 我在当前无写入时串行重算 (05-determinism-recheck.log): 两个文件 sha256 一致, `cmp` 报 identical, 大小行数一致. 故两份输出确定等价; 正式 5 次的 sha256 取自各自运行结束后顺序读取, 未受此影响.

## 5. 覆盖范围

覆盖:
- 场景正文的"当"分支全部动作 (共用准备 init + 连续 5 次原文命令 + 每次耗时记录), 用真实命令产生原始输出.
- "那么"分支三项: 报告给出 p50 与极差 ✅; p50 ≤ 800 ms ✅; 原始输出可复核 ✅ (纳秒起止戳 + 退出码 + stdout/stderr + 文件摘要全在证据文件里, 可逐条重放).

未覆盖 / 不下结论:
- AC-002 (删除后不可读) 与 AC-003 (记录列表) — 由其他验收者负责, 本报告不置评.
- 性能数字的适用范围: 仅 tmpfs 上 20000 行; 不含 fsync 持久化代价, 不含冷缓存 / 物理磁盘 / 更大行数 / 并发. 不外推到这些条件.
- export 不读取 `--data-dir` (代码层面它只写输出文件), 因此上面 74 ms 里没有"读 2 万行记录"的成分; 场景只要求该目录已初始化, 已满足, 不影响本条判定, 但解释数字时应知道其构成为解释器启动 + 2 万次 JSON 序列化 + tmpfs 写入.

## 6. 写入与清理记录

写入 (全部在授权内):
- `docs/changes/vault/evidence/r1-ea94082/V1-perf/`: `run-export-5x.sh`, `00-env.txt`, `01-init.txt`, `02-run-5x.log`, `03-croscheck-time-v.log`, `04-correctness.log`, `05-determinism-recheck.log`, `06-stats.log`, `07-final-state.log`, 本 `REPORT.md`.
- `runtime/data/` (由我执行的一次性 init), `runtime/export.jsonl`, `runtime/export-croscheck.jsonl`.
- 临时文件 `/tmp/v1perf_err.$$` 由脚本自身删除; `/tmp/v1perf_vals.txt` 为统计中间文件, 内容已抄进 06-stats.log, 未放进仓库.

未做 (守边界): 未改 app.py / seed/ / README.md / PRODUCT.md / .agents/ 或任何产品文件; 无 git add/commit/push (HEAD 与 status 收工复核不变); 未删 runtime/ 或任何证据子目录; 未 purge; 未起服务桩或替身; 未读其它会话记录.

保留: runtime/data 与 runtime/*.jsonl 一律保留, 供 verify-del 与后续复核复用 (未清理).
