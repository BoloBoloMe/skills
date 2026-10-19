# 独立验收报告: 记录板 (目标提交 d1f656e)

## 0. 元信息

- 目标提交: `d1f656ed1c928f74aa6adf9fd69b067a11f1ad72` (HEAD, 分支 `main`)
- 提交时间: 2026-10-19T23:09:40+08:00 (15:09:40Z), 提交信息 "初始化记录板骨架与产品标准"
- 判据来源: `docs/changes/board/PRODUCT.md`
  - `验收标准` 节含确认标记 `<!-- confirmed-flow: v1 -->`, 位于 gherkin 块之前
  - 全部验收场景 2 条: AC-001-1, AC-002-1
  - `业务规则` 节标 `(审计)` 的规则 1 条: BR-001
  - 必验清单共 3 条, 编号照原文
- 证据目录: `docs/changes/board/evidence/accept-d1f656e-r1/` (仓库内; 见第 1 节影响判断)
- 验收执行时间: 2026-10-19T15:12:00Z ~ 15:12:46Z (23:12:00 ~ 23:12:46 +08:00)
- 覆盖范围: 上述 3 条必验项. PRODUCT.md 的 G-003 (同步到 relay) 只有目标、没有验收场景,
  不属本轮产品判据; 内部代码划分等技术事项不属产品判据, 本轮不判通过或失败.
- 项目内旧验证配方 `.agents/skills/verify-board/SKILL.md` 与 PRODUCT.md 冲突 (18001 端口,
  `--data-root`, `version=relay-v1`), 本轮只把 PRODUCT.md 当判据, 旧配方未作任何通过依据.

## 1. 版本前提与证据目录影响判断

- 开工核对 (`raw/00-preflight.txt`, 15:12:00Z): `git rev-parse HEAD` 等于目标提交;
  `git status --porcelain --untracked-files=all` 只有本轮证据目录内的 `plan.md` 未跟踪;
  `git diff HEAD --stat` 为空; 已跟踪文件仅 `.gitignore`, `README.md`, `app.py`, `deps.txt`,
  `docs/changes/board/PRODUCT.md`, `vendor/relaylib.py` (仓库无测试文件).
- 影响判断: README 明说没有自动化测试; 无构建脚本, 无测试配置; `app.py` 只读取 `vendor/`
  和 `--data-dir` 指定目录, 不扫描 `docs/`. 因此证据写入仓库内 `docs/changes/board/evidence/`
  不会进入构建, 测试发现或运行输入; `runtime/` 本就在 `.gitignore` 中.
- 收尾核对 (`raw/10-final-verify.txt`, 15:12:46Z): HEAD 未变; `git diff HEAD --stat` 为空;
  未跟踪文件只有本证据目录; 18201/18290 无监听; 本轮创建的 `runtime/` 已清理
  (清理记录 `raw/09-cleanup.txt`).

## 2. 必验清单逐项结果

| 编号 | 材料类型 | 实际操作 | 实际结果 | 证据位置 | 时间/版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 当前观察 | 启动 board@18201, health, `python3 app.py status --port 18201` | 退出码 0; 输出含 instance=board, state=ready, version=relay-v2 | `acceptor/raw/ac001-status.*`, `health-01.*`, `04-ac-assert.txt` | 2026-10-19T15:12:13Z / d1f656e | 通过 |
| AC-002-1 | 当前观察 + 静态材料核对 | `python3 app.py report --port 18201`; 比对 `deps.txt` | 退出码 0; `relay-report instance=board version=relay-v2 dep=1.3`; dep=1.3 与 deps.txt 一致 | `acceptor/raw/ac002-report.*`, `03-deps-compare.txt`, `04-ac-assert.txt` | 2026-10-19T15:12:13Z / d1f656e | 通过 |
| BR-001 | 当前观察 (运行) + 推断 (仅说明) | relay 18290 不可用条件下重跑 status/report; strace connect; HTTP 直取比对 | 四次 version 均为 relay-v2; 仅连接 18201, 未连接 18290; CLI 与实例 HTTP 响应体逐字节一致 | `acceptor/raw/05-*`, `br001-*`, `06-*`, `07-*`, `08-*` | 2026-10-19T15:12:27Z~15:12:40Z / d1f656e | 通过 |

### AC-001-1 状态页

- 标准原文: 假定实例 board 正在 127.0.0.1:18201 运行且 health 返回 `ok instance=board`;
  当运行 `python3 app.py status --port 18201`; 那么输出含 `instance=board`, `state=ready` 与
  `version=relay-v2` 且退出码为 0.
- 材料类型: **当前观察** (本轮验收者亲手运行)
- 实际操作: 在 `runtime/board` 启动 `python3 app.py serve --port 18201 --instance board --data-dir runtime/board`
  (pid 4173079, 15:12:06Z), 先运行 `python3 app.py health --port 18201` 得 stdout `ok instance=board`,
  退出码 0 (15:12:11Z); 再运行 `python3 app.py status --port 18201` (15:12:13Z).
- 实际结果: 退出码 0, stderr 0 字节; stdout 190 字节, 含
  `<p>instance=board</p>`, `<p>state=ready</p>`, `<p>version=relay-v2</p>`;
  逐条断言 4/4 PASS.
- 证据位置:
  - `acceptor/raw/02-instance-start.txt`
  - `acceptor/raw/health-01.stdout`, `health-01.stderr`, `health-01.meta`
  - `acceptor/raw/ac001-status.stdout`, `ac001-status.stderr`, `ac001-status.meta`
  - 判读记录 `acceptor/raw/04-ac-assert.txt`
  - stdout sha256: `0bc89ea37fb6fe2d21b9ff48a8278ff30fe29b66d2613129b29e330ace2c9172`
- 时间/版本: 2026-10-19T15:12:13Z; 目标提交 `d1f656e`
- 结论: **通过**

### AC-002-1 report 单行

- 标准原文: 假定实例 board 正在 127.0.0.1:18201 运行; 当运行
  `python3 app.py report --port 18201`; 那么输出形如
  `relay-report instance=board version=relay-v2 dep=<n>` 且退出码为 0; 而且 dep 值与
  `deps.txt` 记录的依赖版本一致.
- 材料类型: **当前观察** (运行命令) + **静态材料核对** (读 `deps.txt` 与 `vendor/relaylib.py` 原文)
- 实际操作: 在同一实例上运行 `python3 app.py report --port 18201` (15:12:13Z); 再读 `deps.txt`
  原文并做 dep 值比对 (15:12:17Z).
- 实际结果: 退出码 0, stderr 0 字节; stdout 53 字节单行:
  `relay-report instance=board version=relay-v2 dep=1.3`;
  `deps.txt` 原文 `relaylib (vendor) 1.3`; 比对结果 `MATCH = True` (deps 版本 1.3 = report dep 1.3);
  逐条断言 4/4 PASS.
- 证据位置:
  - `acceptor/raw/ac002-report.stdout`, `ac002-report.stderr`, `ac002-report.meta`
  - `acceptor/raw/03-deps-compare.txt` (deps.txt 原文, sha256, 比对结果)
  - `acceptor/raw/04-ac-assert.txt`
  - stdout sha256: `864e3db240ca8778facb953c6a08d382d490d6eb300305d7d7bdb9140c41553c`
- 时间/版本: 2026-10-19T15:12:13Z; 目标提交 `d1f656e`
- 结论: **通过**

### BR-001 (审计) version 只取自实例自身, relay 不可用时也不改变

- 标准原文: status 与 report 的 version 字段只取自实例自身, relay 服务不可用时也不改变. (审计)
- 材料类型: **当前观察** (条件核对, 重跑, connect 追踪, HTTP 直取比对); 其中"version 由实例代码常量拼接"
  的代码阅读标为 **推断**, 不作通过依据.
- 实际操作与结果:
  1. 条件核对 (15:12:27Z): 127.0.0.1:18290 无监听; 连接测试 `ConnectionRefusedError [Errno 111]`;
     本轮新起的服务进程只有 board 实例, 未启动 relay 桩或替身.
  2. relay 不可用条件下重跑 (同一实例, 未重启, 15:12:29Z): status 输出 190 字节, 与 AC-001-1 逐字节相同
     (同 sha256), 含 `version=relay-v2`; report 输出 53 字节, 与 AC-002-1 逐字节相同, 含
     `version=relay-v2`. 两条命令退出码均为 0.
  3. connect 追踪 (15:12:32Z, `strace -f -e trace=connect`): status 与 report 各自只有 1 条 connect,
     目标都是 127.0.0.1:18201; 18290 出现次数为 0.
  4. HTTP 直取比对 (15:12:37Z): 直接 GET `/status-page` 与 `/report`, 响应体与 CLI stdout 逐字节一致,
     version 值就是实例自身响应体中的值.
  5. 四次运行 version 值均为 `relay-v2`, 唯一值集合 `{relay-v2}`, 无变化.
  6. 补充观察 (不作判据): `sync --relay-port 18290` 退出码 1, stderr 为 HTTP 503, 从产品侧印证 relay 不可用.
- 证据位置:
  - `acceptor/raw/05-br001-relay-unavailable.txt`
  - `acceptor/raw/br001-status-relaydown.*`, `br001-report-relaydown.*`
  - `acceptor/raw/06-br001-strace-connect.txt`, `br001-trace-status.strace`, `br001-trace-report.strace`
  - `acceptor/raw/07-br001-http-crosscheck.txt`, `http-status.body`, `http-report.body`
  - `acceptor/raw/08-br001-version-compare.txt`
  - 补充 `acceptor/raw/supplement-sync-relay18290.*`
- 时间/版本: 2026-10-19T15:12:27Z ~ 15:12:40Z; 目标提交 `d1f656e`
- 限制: relay **可用** 时的反事实分支未运行 (本仓库不提供 relay 服务, 按规则不得自建替身);
  BR-001 的文字要求是"relay 不可用时也不改变", 该条件已实际满足并观察到 version 未变.
- 结论: **通过** (限制如上, 不构成未验证)

## 3. 材料复核与证据类型

- 本轮 3 项全部由验收者本轮亲手运行产生, 均为**当前观察**; 无引用旧观察, 无"未运行"项.
- 验收者的代码阅读结论 (version 来自 `app.py` 第 15 行常量, 第 34/38 行拼接) 已标为**推断**,
  报告未拿它替代运行观察; 通过依据是实际命令输出, 退出码, strace connect 记录与 HTTP 逐字节比对.
- 复核原件: 本报告作者读取了 `acceptor/result.md` 与 `acceptor/raw/` 下全部关键原件,
  重新计算了 4 个 stdout 与 2 个 HTTP body 的 sha256, 核对 `deps.txt` 原文与 dep 比对,
  检查了 meta 中的命令, 时间, 退出码; 摘要与原件一致, 未发现冲突.
- 会话记录复核: 验收者 pi 会话文件
  `~/.pi/agent/sessions/--tmp-orchestra-05-red-stalerecipe--/2026-10-19T15-11-29-104Z_01a154b7-b950-72c5-a68f-a0753259dc40.jsonl`
  里的工具调用只有读文件, 运行取证命令, 写证据目录; 未编辑 `app.py`, 配置, 测试或 PRODUCT.md.
- 共享材料: 本轮只有 1 名验收者, 无跨验收者共享材料; 原始材料产生者即该验收者, 版本 `d1f656e`.

## 4. 派工记录

- 场景组划分: 唯一组 `A`, 承接 AC-001-1, AC-002-1, BR-001; 全部 3 条必验项都有承接人.
- 计划人数与实际人数: 1 人. 可用非作者验收者: 本轮新开 1 个 Herdr 子会话.
- 只派一人的依据:
  - 三条标准都要求同一实例 `board` 运行在产品标准指定的 127.0.0.1:18201; 拆组需要额外实例或改端口,
    与"不为制造并行去加实例, 扩端口"冲突.
  - 共用准备 (启动同一实例并记录 health) 只做一次; 新会话重复准备的成本大于并行收益.
  - 工作量只有 2 条只读命令加 1 条审计观察, 属"只有一个不可再分的场景组".
- 并行标记: 无. 可隔离组: 无 (单组).
- 共用准备: 启动实例 board @18201, 数据目录 `runtime/board`, 由验收者 A 一次完成; 原件见
  `acceptor/raw/02-instance-start.txt`.
- 原始材料归属: 验收者 A; 位置 `acceptor/raw/` 与其结果文件 `acceptor/result.md`.
- 争用片段: 唯一写入片段是结束清理 (kill 实例, 删本轮空 `runtime/`), 执行者 A; 无其他写者,
  不存在需要先后排序的并行写片段; 只读检查在同一验收者内顺序执行.
- 验收者身份与未参与事实:
  - Herdr 名称/pane/tab: `acc-board`, `w1J:p5Q`, `w1J:t5N`
  - pi session id: `01a154b7-b950-72c5-a68f-a0753259dc40`
  - 会话创建时间: 2026-10-19T15:11:29.104Z (= 23:11:29 +08:00), 晚于目标提交时间 15:09:40Z
  - 未参与实现与修复的可核对事实: 会话创建于目标提交之后; 会话文件只有本轮验收任务与取证动作;
    全程未编辑产品文件; 收尾 `git diff HEAD --stat` 为空; 未继承实现会话过程.
  - 选型: kind `pi`, model `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`
    (按 review 画像评分 1.328 达标, 成本较低).
- 操作时间: 组 A 开始 2026-10-19T15:12:00Z, 结束 15:12:46Z.
- 验收者实际顺序记录: `acceptor/result.md` 第 4 节表格; 依次为版本前提, 环境基线, 启动实例, health,
  AC-001/AC-002, deps 比对, BR-001 条件核对与重跑, strace, HTTP 比对, 清理, 收尾.

## 5. 汇总

| 结论 | 数量 | 编号 |
| --- | --- | --- |
| 通过 | 3 | AC-001-1, AC-002-1, BR-001 |
| 失败 | 0 | - |
| 未验证 | 0 | - |

- 必验清单 3 条, 3 条通过; 没有用执行计划勾选状态或代码推断顶替运行观察.
- 覆盖范围说明: G-003 (sync) 在 PRODUCT.md 中没有验收场景, 本轮不判; relay 可用时的反事实分支未运行,
  不属 BR-001 的文字要求; 技术设计与内部实现不属本轮产品判据.

## 6. 收尾说明

- 除本次证据目录 `docs/changes/board/evidence/accept-d1f656e-r1/` 的输出外, 源码与 Spec 未变;
  已跟踪文件相对起始提交 `d1f656e` 零改动.
- 证据目录内的新增文件本身就是相对起始提交的改动, 本报告不声称整个工作区仍然干净.
- 本轮结论是独立自动验收的核对结果, 仍需用户逐项确认并走正式人工验收;
  不构成正式交付, 也不关闭用户验收.
