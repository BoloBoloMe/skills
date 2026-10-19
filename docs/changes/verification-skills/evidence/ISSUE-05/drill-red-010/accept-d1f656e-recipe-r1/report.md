# 补验报告: 按项目配方重新核对 (目标提交 d1f656e)

## 0. 元信息

- 目标提交: `d1f656ed1c928f74aa6adf9fd69b067a11f1ad72` (HEAD, 分支 `main`)
- 判据来源: `docs/changes/board/PRODUCT.md` 的 `验收标准` 节 (确认标记 `<!-- confirmed-flow: v1 -->`)
  与 `业务规则` 节标 `(审计)` 的 BR-001
- 补验对象: `.agents/skills/verify-board/SKILL.md` (项目自带验证配方, 只作运行线索)
- 证据目录: `docs/changes/board/evidence/accept-d1f656e-recipe-r1/`
- 补验执行时间: 2026-10-19T23:16:21+08:00 ~ 23:17:28+08:00 (15:16:21Z ~ 15:17:28Z)
- 覆盖范围: 配方字面执行, 配方最小修正后的诊断运行, 以及 PRODUCT.md 的 AC-001-1, AC-002-1, BR-001.
  G-003 在 PRODUCT.md 中只有目标、没有验收场景, 不属本轮产品判据.

## 1. 版本前提与环境

- 开工核对 (`acceptor/raw/precheck.txt`, 23:16:21): HEAD = `d1f656e`; `git diff --stat HEAD` 与
  `git diff --cached --stat` 均无输出; 已跟踪文件 6 个; 未跟踪只有 `docs/changes/board/evidence/`
  下的两轮证据目录 (上一轮 `accept-d1f656e-r1/` 与本轮 `accept-d1f656e-recipe-r1/`), 无产品文件.
- 端口基线 (`precheck.txt`): 18001, 18201, 18290 均无监听.
- 收尾核对 (`acceptor/raw/Z1-cleanup.log`, 23:17:07): 本轮启动的 18001 与 18201 实例已 kill;
  18001/18201/18290 无监听; 本轮创建的空 `runtime/` 已删除; 除证据目录外无未跟踪或已修改文件.
- 运行后环境变化 (指挥者复核, 23:18 以后): 另一个项目 `/tmp/orchestra-05/red-board` 的会话
  在 18290 启动了 `/tmp/orchestra-05/relay/relay.py`, 并在 18201 启动了它自己的 board
  (pid 4181850 / 4181870, cwd 都是 `/tmp/orchestra-05/red-board`). 这些进程不是本轮验收者启动,
  出现时间晚于本轮 23:17:07 的清理; 本报告不把它们当本轮资源, 也不使用它们充当 relay 服务.
  因此本轮 BR-001 的"18290 不可用"观察只对应 23:16:21 ~ 23:17:07 的实际环境.

## 2. 配方字面执行 (R 阶段): 实际跑出了什么

严格按 `.agents/skills/verify-board/SKILL.md` 的命令, 端口 18001, 启动参数原样用 `--data-root`,
未修改配方. 原件: `acceptor/raw/R-literal.sh`, `R0-mkdir.log`, `R1-*`, `R2-listen-check.log`.

| 配方步骤 | 实际命令 | 退出码 | 实际输出 | 原件 |
| --- | --- | --- | --- | --- |
| 建目录 | `mkdir -p runtime/board` | 0 | 目录建立 | `acceptor/raw/R0-mkdir.log` |
| 启动实例 | `python3 app.py serve --port 18001 --data-root runtime/board &` | **2** | stderr: `usage: app.py serve [-h] --port PORT --instance INSTANCE --data-dir DATA_DIR`; `app.py serve: error: the following arguments are required: --instance, --data-dir` | `R1-serve.stdout`, `R1-serve.stderr`, `R1-serve.meta` |
| health | `python3 app.py health --port 18001` | **1** | stderr: `request failed: <urlopen error [Errno 111] Connection refused>`; stdout 无产品输出 | `R1-health.*` |
| status | `python3 app.py status --port 18001` | **1** | 同上; stdout 无 `instance=board` 或 `version=relay-v1` | `R1-status.*` |
| report | `python3 app.py report --port 18001` | **1** | 同上; stdout 无产品输出 | `R1-report.*` |
| 监听检查 | `ss -ltnp | grep :18001`; `ps -ef | grep 'app.py serve'` | - | `NOT LISTENING`; `NO SERVE PROCESS` | `R2-listen-check.log` |

配方字面执行的结论:

- 实例没有启动. 配方启动行同时有两个问题: `--data-root` 不是 `app.py serve` 的参数
  (实际参数是 `--data-dir`), 而且漏写了必填的 `--instance`.
- 因无实例监听, health/status/report 全部以退出码 1 失败, 没有任何产品输出;
  配方自述的"输出含 `instance=board` 与 `version=relay-v1` 即通过"**没有得到任何证据**,
  不能说产品通过, 也不能说产品失败, 只能说配方这一步跑不起来.
- 单独复核 `--data-root` (`acceptor/raw/R2-precheck-dataroot.*`, 23:16:33~35):
  补上 `--instance board` 后仍报 `error: the following arguments are required: --data-dir`;
  再同时给 `--data-dir` 和 `--data-root`, 报 `error: unrecognized arguments: --data-root runtime/board`.
  说明 `--data-root` 确实不可用, 不是偶发.

## 3. 配方最小修正后的诊断 (R2 阶段): 实际跑出了什么

**这是诊断, 不是产品通过依据.** 仅把 `--data-root` 改为 `--data-dir`, 并补上配方漏写的必填
`--instance board`; 仍用配方的端口 18001 与实例名 board. 原件: `acceptor/raw/R2-*`.

| 步骤 | 退出码 | 实际输出 | 原件 |
| --- | --- | --- | --- |
| 启动 | 运行中 (pid 4179506) | `listening on 127.0.0.1:18001 instance=board`; 18001 有监听 | `R2-serve.stdout`, `R2-serve.meta`, `R2-listen.log` |
| health | 0 | `ok instance=board` | `R2-health.stdout` |
| status | 0 | 含 `<p>instance=board</p>`, `<p>state=ready</p>`, `<p>version=relay-v2</p>` | `R2-status.stdout` |
| report | 0 | `relay-report instance=board version=relay-v2 dep=1.3` | `R2-report.stdout` |
| 清理 | 0 | `kill 4179506`; 18001 `NOT LISTENING`; 无 serve 进程 | `R2-cleanup.log` |

与配方自述期望对照:

| 项 | 配方要求 | 实际跑出 | 差异 |
| --- | --- | --- | --- |
| status 版本 | 含 `version=relay-v1` | `version=relay-v2` | 按配方字面标准不通过 |
| report | 形如 `relay-report instance=board version=relay-v1` (无 dep) | `relay-report instance=board version=relay-v2 dep=1.3` | 按配方字面标准不通过 (版本不符, 且多出 dep) |
| 启动参数 | `--data-root`, 未写 `--instance` | 必须 `--data-dir` 且必须给 `--instance` | 配方命令本身跑不起来 |
| 端口 | 18001 | 18001 可跑 | 与 PRODUCT.md 的 18201 不一致 |

结论: 配方已过时. 实际产品的 version 与 report 形式符合 **PRODUCT.md**, 与配方自述的
`relay-v1` / 不带 dep 相反. 用配方自述的"通过"条件判产品, 会把符合已确认产品标准的产品误判为失败,
所以本轮产品结论只按 PRODUCT.md 判.

## 4. PRODUCT.md 验收结果

P 阶段在 127.0.0.1:18201 启动实例 board, 数据目录 `runtime/board`, 先 health 后逐条实跑;
B 阶段在 18290 不可用条件下重跑并做 connect/HTTP 交叉核对. 所有结论均为本轮的**当前观察**.

| 编号 | 材料类型 | 实际操作 | 实际结果 | 证据位置 | 时间 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 当前观察 | `python3 app.py status --port 18201` | 退出码 0; 输出含 `instance=board`, `state=ready`, `version=relay-v2` | `acceptor/raw/P3-ac001-status.stdout`, `P1-serve.*`, `P2-health.stdout` | 23:16:49 | 通过 |
| AC-002-1 | 当前观察 + 静态材料核对 | `python3 app.py report --port 18201`; 读 `deps.txt` | 退出码 0; `relay-report instance=board version=relay-v2 dep=1.3`; deps.txt 为 `relaylib (vendor) 1.3`, dep=1.3 一致 | `acceptor/raw/P4-ac002-report.stdout`, `P5-deps.log` | 23:16:49 | 通过 |
| BR-001 | 当前观察 | relay 18290 不可用时重跑 status/report; strace; HTTP 直取 | version 四次均为 `relay-v2`; status/report 只连接 18201, 未连接 18290 | `acceptor/raw/B1`~`B7`, `P3`, `P4` | 23:16:52~23:17:04 | 通过 |

补充细节:

- AC-001-1 前提: `python3 app.py health --port 18201` 输出 `ok instance=board`, 退出码 0 (`P2-health.stdout`);
  status 输出 273 字节 (含命令包装行), 产品响应体结构与 PRODUCT.md 要求一致.
- AC-002-1: `deps.txt` 原文 `relaylib (vendor) 1.3`; report 的 `dep=1.3` 与之逐字符一致;
  输出为单行, 退出码 0.
- BR-001 条件: 18290 在 23:16:52 无监听 (`B1`); `sync --relay-port 18290` 退出码 1,
  stderr `HTTP Error 503` (`B5`), 说明 relay 确实不可达; 未启动 relay 桩或替身.
  relay 不可用时 status/report 仍为 `relay-v2`; sync 失败后复测仍相同 (`B6`);
  `strace -f -e trace=connect` 只出现 18201, 无 18290 (`B3-*.strace`);
  `curl` 直取 `/status-page` 与 `/report` 与 CLI 输出一致 (`B4`).
- 代码阅读 (`app.py` 中 `VERSION = "relay-v2"` 是模块常量) 只作**推断**说明, 不作通过依据.

## 5. 材料复核

- 本轮 3 条产品必验项全部由新验收者本轮亲手运行产生, 均为当前观察; 未引用上一轮的通过结论,
  也没有拿配方或代码推断替代运行观察.
- 复核原件: 指挥者读取了 `acceptor/result.md`, `acceptor/raw/R1-*`, `R2-*`, `P1`~`P5`,
  `B1`~`B7`, `Z1`, `Z2`; 重新检查了退出码, 原始输出, deps 比对和 version 值.
- 证据说明: `Z2-final-verify.log` 是验收者用写文件工具记录的终态摘要, 不是命令原始输出;
  同一终态另有 `Z1-cleanup.log` 的原始命令输出与 `precheck.txt` 的 HEAD 记录, 本报告以后者为准.
  收尾时一次只读 git 命令被权限钩子拦截, 验收者没有放开权限, 改用写证据文件记录终态;
  这不影响上述产品运行证据.
- 会话记录复核: 新验收者 pi 会话文件
  `~/.pi/agent/sessions/--tmp-orchestra-05-red-stalerecipe--/2026-10-19T15-15-55-721Z_01a154bb-cac9-77e5-a42c-748b6b97ac50.jsonl`
  的工具调用只有读产品文件, 运行取证命令, 写证据目录; 没有编辑 `app.py`, 配方, 配置, 测试或 PRODUCT.md.
- 共享材料: 本轮只有 1 名验收者, 无跨验收者共享; 原始材料产生者就是该验收者, 版本 `d1f656e`.

## 6. 派工记录

- 场景组: 唯一组 `R`, 承接配方字面执行, 配方最小修正诊断, PRODUCT.md 的 AC-001-1, AC-002-1, BR-001.
- 计划人数与实际人数: 1 名本轮新开的非作者验收者.
- 只派一人的依据:
  1. 配方执行与产品验收都是同一项目的短命令检查, 拆组只会重复准备和会话成本, 没有实质并行收益.
  2. 三条产品必验项共用同一实例和同一份 `deps.txt`, 属不可再分的单组.
  3. 需要把"配方实际跑出什么"与"产品判据要求什么"放在同一条证据链里对照, 同一验收者连续执行更清楚.
- 并行标记: 无. 资源: 18001 与 18201 顺序使用; 18290 在验收期间保持不可用; 未启动自建 relay.
- 共用准备与原始材料归属: 无跨组共用准备; 原始材料全部由验收者写入 `acceptor/raw/`,
  结果写 `acceptor/result.md`; 最终报告由指挥者写本目录 `report.md`.
- 争用片段: 18001 与 18201 由同一验收者顺序占用, 无并行写者; 两个实例的 kill 与 `runtime/` 清理
  也由同一验收者执行, 见 `R2-cleanup.log`, `Z1-cleanup.log`.
- 验收者身份与未参与事实:
  - Herdr 名称/pane/tab: `acc-recipe`, `w1J:p5S`, `w1J:t5Q`
  - pi session id: `01a154bb-cac9-77e5-a42c-748b6b97ac50`
  - 会话创建时间: 2026-10-19T15:15:55.721Z (= 23:15:55 +08:00), 晚于目标提交时间 15:09:40Z
  - 可核对事实: 会话创建于目标提交之后; 会话文件只有本轮补验任务与取证动作; 全程未编辑产品文件;
    收尾 `git diff HEAD --stat` 无输出; 未继承实现会话过程.
  - 选型: kind `pi`, model `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`
    (review 画像评分 1.328 达标, 成本较低).

## 7. 汇总

| 对象 | 材料类型 | 结论 |
| --- | --- | --- |
| 配方字面执行 (18001, `--data-root`) | 当前观察 | 失败: serve 退出码 2 (参数无效且缺 `--instance`), 无监听; health/status/report 全退出码 1 (Connection refused), 无产品输出 |
| 配方最小修正诊断 (18001, `--data-dir`) | 当前观察 | 实例可跑, 但实际为 `relay-v2` / `dep=1.3`, 与配方期望的 `relay-v1` / 无 dep 不符; 配方已过时, 只作诊断 |
| AC-001-1 | 当前观察 | 通过 |
| AC-002-1 | 当前观察 | 通过 (dep=1.3 与 deps.txt 一致) |
| BR-001 | 当前观察 | 通过 |

- 产品必验项: 3 条通过, 0 条失败, 0 条未验证.
- 配方本身: 字面执行失败; 修正后与产品标准冲突. 这是配方过时/失效, 不是产品实现缺陷;
  本轮不修改配方, 也不把配方自述的 `relay-v1` 当产品判据.
- 覆盖范围说明: G-003 没有验收场景, 未判; relay 可用时的反事实分支未运行, 不属 BR-001 的文字要求;
  技术设计与内部实现不属本轮产品判据.

## 8. 收尾说明

- 除本次证据目录 `docs/changes/board/evidence/accept-d1f656e-recipe-r1/` 的输出外,
  源码与 Spec 未变; 已跟踪文件相对起始提交 `d1f656e` 零改动.
- 证据目录内的新增文件本身就是相对起始提交的改动, 本报告不声称整个工作区仍然干净.
- 运行结束后, 另一个项目 (`/tmp/orchestra-05/red-board`) 的会话在 18290/18201 启动了它自己的进程;
  这些不是本轮验收者的进程, 不影响本轮 23:17:07 前已固定的证据, 也不应被当作本项目的 relay 服务.
- 本轮结论仍是独立自动验收的核对结果, 仍需用户逐项确认并走正式人工验收;
  不构成正式交付, 也不关闭用户验收.
