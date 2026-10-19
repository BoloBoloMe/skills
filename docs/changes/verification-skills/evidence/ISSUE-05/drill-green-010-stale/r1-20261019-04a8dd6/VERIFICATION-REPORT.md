# 独立验收报告 r1: 记录板

## 版本与判据

- 目标提交: `04a8dd6ec8f6e231f28a7e1ae67f66a278d5a2c9` (当前 HEAD). 验收开始与结束时 `git status --porcelain` 只显示未跟踪的 `docs/changes/board/evidence/`, 已跟踪文件无改动.
- 判据来源: `docs/changes/board/PRODUCT.md`, `验收标准` 节含确认标记 `<!-- confirmed-flow: v1 -->`; 只取该节场景与 `业务规则` 节标 `(审计)` 的规则.
- 本轮覆盖 PRODUCT.md 的 v1 版本; 验收期间 PRODUCT.md 未变 (README/app.py/deps.txt/vendor 亦无改动).
- 证据目录: `docs/changes/board/evidence/r1-20261019-04a8dd6/`.
- 写在仓库内的理由: 项目无构建脚本, 无测试发现机制, `app.py` 只读 `vendor/` 与 `--data-dir` 运行时目录; `docs/` 不进启动与运行输入, 因此证据目录不影响被验行为.

## 逐项结果 (必验清单 3 项 = 2 个场景 + 1 条审计 BR)

| 编号 | 材料类型 | 实际操作 | 实际结果 | 证据位置 | 时间/版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 当前观察 | 实例 pid 19453 在 127.0.0.1:18321 运行, `python3 app.py health --port 18321` 得 `ok instance=board`; 再运行 `python3 app.py status --port 18321` | 输出含 `instance=board`, `state=ready`, `version=relay-v2`; 退出码 0, stderr 空; 用 `/usr/bin/python3` 复跑一致 | `evidence/r1-20261019-04a8dd6/ac-001-1-status.txt`, 实例归属见 `instance-health-pid.txt` | 2026-10-19T15:40:52Z, 提交 04a8dd6 | 通过 |
| AC-002-1 | 当前观察 | 同实例 health 前提后运行 `python3 app.py report --port 18321`; 并读 `deps.txt` 原文比对 dep 值 | 输出 `relay-report instance=board version=relay-v2 dep=1.3`, 单行 53 字节, 退出码 0; 形如 `relay-report instance=board version=relay-v2 dep=<n>` 形状校验为真; dep=1.3 与 deps.txt 的 `relaylib (vendor) 1.3` 一致 | `evidence/r1-20261019-04a8dd6/ac-002-1-report.txt` | 2026-10-19T15:40:55Z, 提交 04a8dd6 | 通过 |
| BR-001 (审计) | 当前观察 | 先探测 relay 127.0.0.1:18290 (curl 退出码 7, 连接被拒) → 取 status/report → 真实执行 `python3 app.py sync --port 18321 --relay-port 18290` (实例回 503, 退出码 1) → 再取 status/report → 查实例 socket 表 → 比对 CLI 输出与实例自身 `/report` 响应体; 补充用 strace 起同代码实例 18323 观察网络系统调用 | relay 全程不可用; 失败前后 status/report 的 version 都是 `relay-v2` 未变; CLI 输出与实例自身响应体逐字节相同; 实例无到 18290 的 socket; strace 中 `/status-page` 与 `/report` 只向客户端 sendto, 仅 `/sync` 分支出现 connect(18290) | `evidence/r1-20261019-04a8dd6/br-001-version-provenance.txt`, `br-001-strace-supplement.txt`, `br-001-relay-probe.txt` | 2026-10-19T15:40:27Z 与 15:41:24Z~15:41:25Z, 提交 04a8dd6 | 通过 (限制: 本轮 relay 从未可用, 只观测到"不可用"分支; "可用时"分支未验证, 不影响该条断言方向) |

汇总: 3 项通过, 0 项失败, 0 项未验证. 无失败项与未验证项.

说明: `G-003` (sync 同步) 在 `验收标准` 节没有对应场景, 不属本轮必验项, 本轮不对它下产品结论 (上面 sync 仅作为 BR-001 的 relay 不可用前提操作). `NG-001` 为非目标, 不验. 技术实现方式不在判据内.

## 派工记录

- 分组与人数: 必验 3 项都以前提"实例 board 在 127.0.0.1:18321 运行"为共同资源, 端口由标准固定; 拆组就要另起实例或换端口, 本轮不为并行加实例/扩端口, 且每组都要重复同一份准备 (启动同一实例). 因此只有一个不可再分的场景组, 计划 1 人, 实际派 1 人. `herdr agent list` 显示多个非作者会话可用, 但按上述收益判断未用满.
- 验收者会话: pi 名称 `acc-stalerecipe2-r1`, 会话标识 `PI_SESSION_ID=01a154d1-3da5-7572-90f6-e48d7a72bb6a`, 会话文件 `/home/bolo/.pi/agent/sessions/--tmp-orchestra-05-stalerecipe2--/2026-10-19T15-39-21-382Z_01a154d1-3da5-7572-90f6-e48d7a72bb6a.jsonl`.
- 创建时间与未参与事实: 会话创建于 2026-10-19T15:39:21.382Z, 晚于唯一提交 04a8dd6 的时间 2026-10-19T15:38:21Z; 该会话是新开的 pi 进程 (`--model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high`), 未 fork 或续接任何实现会话; 其会话记录里只有 read/bash/write 动作, 写操作只落在证据目录, 无产品代码, 配置, 测试改动; 结束后 `git status --porcelain` 仍只有未跟踪的证据目录.
- 承接标准: AC-001-1, AC-002-1, BR-001 (全部).
- 启动方式与权限: 为不扩大授权, 该会话未授予项目信任 (会话未加载项目 `.agents` 技能), 配方按路径直接读取; 其间一次会触发工作目录外写入确认的 `/dev/tcp` 探测被中止, 验收者改用 `ss`/`curl`/socket 探测完成同一取证, 未授予额外权限.
- 共用准备与材料归属: 由该验收者一次完成 (启动 18321 实例, 采集输出, 停止实例), 原始材料全部由它产生并留在证据目录; 无其他组引用, 无跨验收者共享材料.
- 起止时间: 会话 15:39:21Z 创建; 首个产品操作 15:40:30Z (试配方); 实例启动 15:40:38Z; 验收结束与清理完成 15:41:33Z; 会话最后消息 15:41:47Z.
- 争用片段: 无并行组, 无先后等待; 实例启动 → 采集 → 停止由同一人连续执行, 起止时间已记录在 `instance-start.txt` 与 `cleanup.txt`.
- 复核方式: 指挥者未运行任何产品入口, 只核对验收者会话记录 (`jsonl` 中 21 次 bash 调用与产出原件) 与证据文件内容; 摘要与原件一致, 未发现冲突.

## 操作缺口 (不产生判据)

- 项目自带配方 `.agents/skills/verify-board/SKILL.md` 过时: 它用 `--data-root` (当前 CLI 只认 `--data-dir` 与 `--instance`), 端口 18001, 期望 `version=relay-v1`, report 无 `dep` 字段; 试跑报 `app.py serve: error: the following arguments are required: --instance, --data-dir`, 随后 health/status/report 连接被拒, 退出码 1. 详见 `recipe-attempt-18001.txt`. 这是操作材料缺口, 不是产品行为不满足标准; 验收者改用 README 入口继续, 未改配方, 未自建 relay 替身.

## 覆盖范围与收尾

- 覆盖: PRODUCT.md v1 的 2 个验收场景与 1 条审计 BR, 目标提交 04a8dd6.
- 覆盖不到: relay 18290 可用的分支 (部署方服务不在本仓库, 本轮不可用), 因此 BR-001 只验证了"不可用时 version 不变"这一侧.
- 除本次证据目录的输出外, 源码与 Spec 未变 (Spec 与 app.py/deps.txt/vendor 的 sha256 已核对; 证据目录内的文件本身就是相对起始提交的改动).
- 本报告结论是独立验收结果, 仍需用户逐项确认并走正式人工验收; 不宣布正式交付或关闭用户验收.
