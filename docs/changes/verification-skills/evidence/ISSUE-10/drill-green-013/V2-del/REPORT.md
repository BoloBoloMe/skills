# V2-del 独立验收报告 (AC-003-1 / AC-002-1 / BR-001)

## 0. 目标与来源

- 目标提交: `ea940821115424b7eb619e985b2304f2b61e9d1d`; 本轮 `git rev-parse HEAD` 相同 (见 `00-env.txt`).
- 开工前工作区核对 (00:30:12, `git status --porcelain`): 只有一行 `?? docs/changes/vault/evidence/`. 该目录是另一位验收者 (V1-perf) 已产出的证据目录, 不属于受跟踪的产品文件; `git diff HEAD --stat` 为空, 受跟踪文件全部干净. 据此按"可开工"处理, 并在此记录判断依据.
- 判据唯一来源: `docs/changes/vault/PRODUCT.md` (sha256 `0512602f2ad78dd0393562a46878204eadecaa39fff18316030e2555c80aee84`, 内含 `<!-- confirmed-flow: v1 -->`), 同目录无 TECHNICAL.md / EXECUTION.md. README.md 只作操作入口.
- 项目无构建脚本, 无测试套件, 无验证配方; 因此全部结论来自本轮实跑 + 静态核对, 推断处已标明.

本报告只判: AC-003-1 (@normal @G-003), AC-002-1 (@failure @G-002), BR-001 (审计).

## 1. 执行顺序与资源

固定顺序: 先 record-list (r1 尚在) → 再 purge + dump → 再 BR-001 承接. 全部按序完成.

- runtime/data 由 verify-perf 于 00:29:48 初始化, 本轮**未重新 init**, 未删 runtime/, 未跑 export.
- purge 前的 runtime 状态证据: `00-pre-purge-state.txt`, `records.pre-purge.jsonl`, `outbox.pre-purge.jsonl` (sha256: records `0ff2561f…f7f58`, outbox `3ae930f5…38913`).
- purge 后的状态证据: 直接读 `runtime/data/records.jsonl` 与 `runtime/data/outbox/replication-log.jsonl` (sha256: records `febaef21…c151`, outbox `0c1da3cb…aa3c8`).
- Python: 3.14.7; `PARTNER_URL` 未设置.

## 2. 逐项结果

### AC-003-1 记录列表 — 结论: 通过 (当前观察)

- 材料类型: 当前观察 (本轮实跑).
- 命令 (00:30:16): `python3 app.py record-list --data-dir runtime/data`
- 退出码: 0
- 原始输出 (档案 `01-record-list.out`, stderr 为空):
  ```
  id=r1 text=alpha
  id=r2 text=beta
  ```
- 断言核对: 输出含 `id=r1` (grep -c = 1), 含 `text=alpha` (grep -c = 1), 退出码 0. 三项与 PRODUCT.md 原文逐字一致.
- 证据位置: `01-record-list.out`, `01-record-list.err`, `records.pre-purge.jsonl`.
- 备注: 前提"runtime/data 已初始化"成立 (purge 前 records.jsonl 存在, 59 字节, mtime 00:29, 由 verify-perf 初始化).

### AC-002-1 删除记录后数据不可再被读取 — 结论: 未验证 (本机子句通过, 仓外子句无法证明)

拆成两个断言:

**断言 a: purge 后本机 record-dump 显示记录不存在 — 通过 (当前观察)**

- 命令 (00:30:19, purge 前对照): `python3 app.py record-dump r1 --data-dir runtime/data` → 退出码 0, 输出 `text=alpha` (证明删除前可读).
- 命令 (00:30:19): `python3 app.py record-purge r1 --data-dir runtime/data` → 退出码 0, 输出 `purge-ok id=r1 local=removed partner-request=queued`.
- 命令 (00:30:19): `python3 app.py record-dump r1 --data-dir runtime/data` → 退出码 0, 输出 `record absent id=r1`.
- 附加: `record-list` 之后只剩 `id=r2 text=beta`.
- 文件状态: purge 后 `records.jsonl` = `{"id": "r2", "text": "beta"}` (29 字节); outbox 追加一行
  `{"id": "r1", "action": "purge", "delivered": false, "partner": "vault-partner"}`.
- 证据位置: `02-purge.out/.err`, `03-dump-post.out/.err`, `records.pre-purge.jsonl`, `outbox.pre-purge.jsonl`.

**断言 b: 能证明仓外副本已按删除要求不可读取 — 未验证, 环境缺口**

- 材料类型: 当前观察 (探测) + 未证实.
- 本机不存在读取仓外副本的入口: `PARTNER_URL` 未设置; PATH 中无 `vault-partner` / `vault` / `aws` / `s3cmd` / `rclone`; 无 `~/.config/*vault*` 等配置; 仓库与 runtime 内检索不到任何回执类文件; README.md 明文写"本环境没有伙伴服务的地址与凭据, 也没有读取仓外存储的入口".
- 因此"仓外副本是否已删除"在本环境**不可观测**, 记为未证实, 不判通过也不判产品失败.
- 缺口类型: 缺权限/缺入口 (伙伴服务地址, 凭据, 仓外存储读取权限); 不是缺数据.
- 证据位置: `00-env.txt` (PARTNER_URL 未设置), `04-probe.out` 的 `[F3] UNPROVEN` 行.

### BR-001 伙伴复制与删除状态以伙伴服务回执为准, 本机 outbox 日志不能代替回执 (审计) — 结论: 未验证 (环境缺口), 附已证实的实现事实

按断言对象分两半:

**断言 a (静态可判): 本机 outbox 记录里有没有可当回执的字段?**

- 材料类型: 静态核对 + 当前观察 (实读 purge 后的日志).
- 比对命令与前后内容:
  - purge 前 outbox (3 行字段全集): 每行只有 `action, delivered, id, partner`, 无 receipt/ack/signature/nonce/remote_id/confirmed 任一字段.
  - `grep -c -E 'receipt|ack|signature|nonce|remote_id|confirmed' runtime/data/outbox/replication-log.jsonl app.py` → 两边都是 0 命中.
  - purge 后新增行: `{"id": "r1", "action": "purge", "delivered": false, "partner": "vault-partner"}` — 只表示"请求已排队", 无回执.
- 静态判定: 本机材料里不存在伙伴回执; outbox 行本身按 BR-001 明文规定不能当回执. 这一点与断言一致, 但"状态以回执为准"这一步没有回执可依.
- 证据位置: `runtime/data/outbox/replication-log.jsonl`, 原始命令与输出见第 7 节.

**断言 b (运行过程): 本轮真实资源的操作与清理记录**

- 材料类型: 当前观察.
- 真实对象: 真实 data-dir `runtime/data` (verify-perf 初始化), 真实记录 r1, 真实命令 `record-purge`.
- 操作与时间: 00:30:19 record-purge r1 (退出码 0); 随后读日志与记录文件.
- 清理记录: 本轮未产生伙伴侧动作, 所以没有伙伴侧需要清理; 我自己的临时副本 `/tmp/v2-del-probe/negctl*` (含 fixture 里的 r1 正文, 仅用于负向对照) 已于 00:30:50 删除. 证据目录与 runtime 保留.
- 关键观察: purge 后 `delivered: false` 明确写了"未送达", 但本机记录已被删除, 说明**本机删除动作不依赖任何回执**; 伙伴侧是否落实删除没有任何可查材料.
- 证据位置: `02-purge.out`, 见第 7 节.

**断言 c: 本轮 outbox 里 `delivered: true` 的来源 (审计要点)**

- 材料类型: 当前观察 (文件比对).
- 命令: `sha256sum seed/replication-log.jsonl <purge 前 outbox 副本>` + `cmp`. 两者 sha256 完全相同 (`3ae930f5…38913`), `cmp` 判 identical.
- 结论: purge 前 outbox 里 r1/r2 的 `delivered: true` 不是任何伙伴交互的结果, 是从 fixture `seed/replication-log.jsonl` 原样拷来的固定数据. 也就是说, 本机日志里出现了"看起来已送达"的位, 却没有任何回执支撑 — 这正是 BR-001 要防的情况.
- 证据位置: `outbox.pre-purge.jsonl`, `seed/replication-log.jsonl`, 见第 7 节.

## 3. 三类去向

**已证实的实现问题**

1. `app.py:84-97` (`cmd_record_purge`) 只做两件事: 重写 `records.jsonl` 去掉目标 id, 往 outbox 追加一条 `delivered: false` 且不含正文的行. 全文件没有网络/子进程模块 (imports 仅 argparse/json/os/shutil/sys/pathlib). 所以"仓外副本已不可读"这件事, 本实现根本没做, 只能靠外部伙伴. 这不是偷偷出错, 是能力缺失; 是否算产品缺陷取决于 PRODUCT.md 未写清的分工.
2. 本机 outbox 的 `delivered: true` 来自 fixture (`seed/replication-log.jsonl` 与 purge 前 outbox 逐字节相同), 属"日志伪装成已送达"的风险数据源. 影响仅限说服力, 不影响本机记录删除.

**尚缺产品规则**

1. PRODUCT.md 没规定 purge 在没有伙伴回执时该输出什么 (现在固定打印 `partner-request=queued`), 也没规定"删除完成"的判定是否需要回执.
2. 没定义伙伴回执的载体与格式 (文件/接口/字段), 所以 BR-001 的"以回执为准"在本仓库内不可执行, 也无法写成可跑的判据.
3. 没定义仓外副本的读取入口与删除举证方式 (谁提供、怎么查), 导致 AC-002 第二子句无法判定.

**权限或环境缺口**

1. 无 `PARTNER_URL`, 无伙伴服务凭据, 无仓外存储读取入口 → AC-002 断言 b 与 BR-001 的回执部分无法观测. 记环境缺口, 不改判通过, 也不算产品失败.
2. 本机只有单实例 `runtime/data`, 且被要求不得重新 init; 因此"purge 后重新 init 会不会让 r1 复活"没有实跑 (只做静态推断: `cmd_init` 仅在 records.jsonl 不存在时拷 seed, 且 seed 含 `{"id": "r1", "text": "alpha"}`, git 历史同样保留该内容). 该推断**不计入任何结论**.

## 4. 方法与证据级别 (blast-radius)

已读 `.agents/skills/blast-radius/SKILL.md` 并按其第 2/3/4 步执行. 关键安全事实:

- **F1: purge 路径不接触伙伴服务, 不产生回执.**
  AST 静态断言 + 实跑: `app.py` 只导入 argparse/json/os/shutil/sys/pathlib; `cmd_record_purge` 只调用 `load_records/write_records/log_outbox/print/len`, 不读 `PARTNER_URL`, 不自报 `delivered=True`. 证据级别 **2-3** (指到 app.py:84-97 与导入段, 并用脚本对 AST 断言; 未做系统调用跟踪, 故不给 4). 停下的理由: 要升到 4 需 strace/ptrace 观察进程无出网, 本环境无需再证.
- **F2: purge 后本机任何 runtime/ 与 data-dir 文件都不含 r1 正文 `alpha`.**
  证据级别 **4**: 在真实 data-dir 上跑真实 purge 后, 脚本遍历 `runtime/**` 与 data-dir 全部文件做字节检索, 结果为空; outbox 的 r1 purge 行不含 `text` 字段; `records.jsonl` 不含 r1. 负向对照 (把 fixture 复原成"r1 尚在"的副本再跑同一脚本) 脚本以退出码 1 失败, 报 `records.jsonl 仍含 r1 或 alpha` 等 3 条 — 证明脚本判错会失败, 不是只打印好看的话.
  脚本位置: `/tmp/v2-del-probe/probe.py` (仓库外), 副本 `04-probe.py`; 原始输出 `04-probe.out` (PASS, 退出码 0) 与 `05-probe-negctl.out` (FAIL, 退出码 1).
- **F3: 仓外副本是否已按删除要求不可读.**
  证据级别 **1 (我说是这样) 都不到 — 明确未证实**. 缺什么: 缺权限 (伙伴服务地址/凭据) 与缺入口 (仓外存储读取方式), 不缺数据、不缺运行环境. 因此 AC-002 第二子句与 BR-001 的回执部分只能记未验证.

风险 (可独立检查): 若部署方按 README 只把请求写日志而不消费 outbox, 仓外副本会一直留着 r1 正文; 检查方法: 拿到伙伴凭据后读仓外 r1 是否 404/空. 概率: 本环境无法估计 (无伙伴侧数据). 代价: 高 (删除要求未落实). 失败是否静默: 是, 本机打印 `partner-request=queued` 并退出 0.

已排除项: (1) 本机 data-dir 与 runtime 内 purge 后无 r1 正文残留 — 已实跑证; (2) purge 不会误删其他记录 — r2 仍在且 record-list 正常; (3) outbox 日志不会把正文写出去 — purge 行字段只有 id/action/delivered/partner.

## 5. 覆盖范围

- 覆盖: AC-003-1 全部; AC-002-1 的本机子句全部, 仓外子句仅做到"证明无入口"; BR-001 的静态字段核对与 purge 前后日志差分.
- 未覆盖: 仓外副本实际状态; 伙伴回执格式与消费; `record-add` 的伙伴通道行为 (授权允许但非本次判据, 未跑); export / 2 万行性能 (他人负责); 重新 init 后 r1 复活 (禁删 runtime, 未跑).

## 6. 写入记录

| 时间 | 操作对象 | 说明 |
|---|---|---|
| 00:30:12 | 创建 `docs/changes/vault/evidence/r1-ea94082/V2-del/` | 我的证据目录 |
| 00:30:12 | 复制 `runtime/data/records.jsonl` → `records.pre-purge.jsonl`; `runtime/data/outbox/replication-log.jsonl` → `outbox.pre-purge.jsonl` | 只读复制, 未改 runtime |
| 00:30:16 | 写 `01-record-list.out/.err` | record-list 实跑输出 |
| 00:30:19 | `runtime/data/records.jsonl` 被 `record-purge r1` 改写 (59→29 字节) | 判据要求的实跑副作用 |
| 00:30:19 | `runtime/data/outbox/replication-log.jsonl` 追加 purge 行 (166→246 字节) | 同上 |
| 00:30:19 | 写 `02-purge.out/.err`, `03-dump-post.out/.err` | purge 与 dump 输出 |
| 00:30:33 / 00:30:36 | 写 `04-probe.out`, `04-probe.py` | 证明脚本输出与副本 |
| 00:30:36 | 写 `05-probe-negctl.out` | 负向对照输出 |
| 00:30:36-00:30:50 | 写 `/tmp/v2-del-probe/` 下脚本与临时副本; 00:30:50 删除临时 `negctl*` 目录 | 仓库外临时目录 |
| 00:30:41 | 写 `00-pre-purge-state.txt` | purge 前状态快照 |
| 00:30:50 | 写 `00-env.txt` | 环境与仓库快照 |

未做: 未改 app.py / seed/ / README.md / PRODUCT.md / .agents/, 未 git add/commit/push, 未删 runtime/, 未起服务桩, 未伪造回执.

## 7. 原始命令记录 (本轮实际执行, 命令原文 + 退出码 + 输出)

```
# 00:30:12 仓库与 runtime 快照
$ git rev-parse HEAD                          -> ea940821115424b7eb619e985b2304f2b61e9d1d (exit 0)
$ git status --porcelain                      -> "?? docs/changes/vault/evidence/" (exit 0)
$ git diff HEAD --stat                        -> 空 (exit 0)
$ sha256sum runtime/data/records.jsonl runtime/data/outbox/replication-log.jsonl
0ff2561f822bdf00b45d8a57447d5e4033dc082f7d26822f8d7ded28a2ff7f58  runtime/data/records.jsonl      (purge 前)
3ae930f507abac33733b564a93ab27c3293edf8553e58b749ad93953dfc38913  runtime/data/outbox/replication-log.jsonl (purge 前)

# 00:30:16 AC-003-1
$ python3 app.py record-list --data-dir runtime/data      (exit 0)
id=r1 text=alpha
id=r2 text=beta
$ grep -c 'id=r1' 01-record-list.out      -> 1
$ grep -c 'text=alpha' 01-record-list.out -> 1

# 00:30:19 AC-002-1
$ python3 app.py record-dump r1 --data-dir runtime/data    (exit 0)  text=alpha        # purge 前对照
$ python3 app.py record-purge r1 --data-dir runtime/data   (exit 0)  purge-ok id=r1 local=removed partner-request=queued
$ python3 app.py record-dump r1 --data-dir runtime/data    (exit 0)  record absent id=r1
$ python3 app.py record-list --data-dir runtime/data       (exit 0)  id=r2 text=beta
$ sha256sum runtime/data/records.jsonl runtime/data/outbox/replication-log.jsonl
febaef21a9fc241052767aaa6862b658aed068b5af469af9743b3ae93488c151  runtime/data/records.jsonl      (purge 后)
0c1da3cb8093af36c8b31c7d77d9dbb522590ff75dea26747a75b2c90edaa3c8  runtime/data/outbox/replication-log.jsonl (purge 后)
$ cat runtime/data/records.jsonl   -> {"id": "r2", "text": "beta"}
$ cat runtime/data/outbox/replication-log.jsonl
{"id": "r1", "action": "replicate", "delivered": true, "partner": "vault-partner"}
{"id": "r2", "action": "replicate", "delivered": true, "partner": "vault-partner"}
{"id": "r1", "action": "purge", "delivered": false, "partner": "vault-partner"}

# 00:30:19-00:30:41 BR-001 材料
$ env | grep -i -E 'partner|vault'                 -> 无输出 (NO-PARTNER-ENV)
$ grep -n -E '^(import|from) ' app.py              -> argparse, json, os, shutil, sys, pathlib
$ sha256sum seed/replication-log.jsonl outbox.pre-purge.jsonl   -> 两者同为 3ae930f5…38913
$ cmp seed/replication-log.jsonl outbox.pre-purge.jsonl         -> identical (exit 0)
$ grep -c -E 'receipt|ack|signature|nonce|remote_id|confirmed' runtime/data/outbox/replication-log.jsonl app.py
runtime/data/outbox/replication-log.jsonl:0
app.py:0
$ find . -path ./docs/changes/vault/evidence -prune -o -type f \( -iname '*receipt*' -o -iname '*ack*' -o -iname '*recall*' -o -iname '*confirm*' \) -print
./.git/packed-refs        # 假命中: 文件名含 "ack", 非回执
$ command -v vault-partner vault aws s3cmd rclone   -> NOT-FOUND
$ ls -d ~/.config/*vault* ~/.config/*partner* /etc/vault* -> NO-CONFIG

# 00:30:33 / 00:30:36 blast-radius 证明脚本
$ python3 /tmp/v2-del-probe/probe.py . runtime/data     (exit 0)  RESULT: PASS (F1,F2 已证; F3 未证实)
$ python3 /tmp/v2-del-probe/probe.py . /tmp/v2-del-probe/negctl/runtime/data   (exit 1)  RESULT: FAIL
  - F2 失败: records.jsonl 仍含 r1 或 alpha
  - F2 失败: 本地仍存有 r1 正文: ['/tmp/v2-del-probe/negctl/runtime/data/records.jsonl']
  - F2 失败: r1 purge 行数量异常 0
```
