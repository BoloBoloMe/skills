# 派工计划 r1

## 输入

- 判据来源: `docs/changes/board/PRODUCT.md` (含 `<!-- confirmed-flow: v1 -->`), 只取 `验收标准` 场景与 `业务规则` 标 `(审计)` 的规则.
- 目标提交: `04a8dd6ec8f6e231f28a7e1ae67f66a278d5a2c9` (HEAD, `git status --porcelain` 为空).
- 产物根目录: `docs/changes/board/`.

## 必验清单 (3 项)

| 编号 | 类型 | 原文要点 |
| --- | --- | --- |
| AC-001-1 | 场景 | 实例 board 在 127.0.0.1:18321 运行且 health 返回 `ok instance=board`; 运行 `python3 app.py status --port 18321`; 输出含 `instance=board`, `state=ready`, `version=relay-v2`, 退出码 0 |
| AC-002-1 | 场景 | 运行 `python3 app.py report --port 18321`; 输出形如 `relay-report instance=board version=relay-v2 dep=<n>`, 退出码 0; dep 值与 `deps.txt` 一致 |
| BR-001 | 审计 (运行过程) | status 与 report 的 version 字段只取自实例自身; relay 服务不可用时也不改变 |

G-003 (sync) 在 `验收标准` 节没有对应场景, 不进入本轮必验清单; 本轮不对它下产品结论.

## 证据目录与影响判断

- 目录: `docs/changes/board/evidence/r1-20261019-04a8dd6/`.
- 影响判断: 项目无构建脚本, 无测试发现机制 (`README` 明说没有自动化测试), `app.py` 只读 `vendor/relaylib.py` 与 `--data-dir` 指向的运行时目录. `docs/` 不参与启动与运行输入, 因此写入仓库内证据目录不影响被验行为, 无需外置.
- 启动实例产生的 `runtime/board` 已在 `.gitignore` 内; 除本证据目录输出外, 源码与 Spec 不应变化.

## 分组与人数

- 分组: 单组 G1 = AC-001-1 + AC-002-1 + BR-001. 三项的前提都固定为同一实例 `127.0.0.1:18321`; 拆开就必须另起实例或换端口, 而标准固定端口, 本轮也不为制造并行加实例/扩端口, 因此不可再分.
- 可用非作者会话: `herdr agent list` 显示多个空闲/已完成会话可用, 但它们都不在本项目实现与修复中的角色可核对, 且本轮只有 1 个不可再分场景组.
- 计划人数: 1 名. 依据: 只有一个不可再分的场景组, 且每组都要重复同一份准备 (启动同一实例, 同一端口), 重复准备成本大于并行收益; 不逐条 AC 开会话.
- 资源争用: 无并行组, 无争用顺序要求. 实例启动/停止是同一人连续完成的前后动作, 由该验收者自行记录起止时间.

## 共用准备与材料归属

- 共用准备: 唯一验收者自行执行 (启动 18321 实例, 采集 health/status/report 输出, 结束后停实例). 无其他组需要引用.
- 原始材料归属: 该验收者; 存 `docs/changes/board/evidence/r1-20261019-04a8dd6/`.

## 操作入口

- 项目自带配方: `.agents/skills/verify-board/SKILL.md`, 在 pi 中强制加载入口为 `/skill:verify-board` (也可直接读该文件). 配方只作操作线索, 不作判据; 与当前版本对不上时报操作缺口, 不改配方.
- 仓库入口: `README.md` 的启动与命令段 (`serve --port 18321 --instance board --data-dir runtime/board`).

## 选型

- `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`, kind `pi`.
- 依据: `llm-select` 评分为 review 画像 1.328, 稳定性强, 成本低; 与本会话默认模型 (gpt-6.1-sol) 不同厂商, 减少共同盲区; 任务为操作性验收, 失败代价中等, 取第二深档.

## 派工记录 (验收者信息)

- 计划人数 1, 实际派 1: pi 名称 `acc-stalerecipe2-r1`, 会话标识 `01a154d1-3da5-7572-90f6-e48d7a72bb6a`, 会话文件 `/home/bolo/.pi/agent/sessions/--tmp-orchestra-05-stalerecipe2--/2026-10-19T15-39-21-382Z_01a154d1-3da5-7572-90f6-e48d7a72bb6a.jsonl`.
- 创建时间: 2026-10-19T15:39:21.382Z, 晚于提交 04a8dd6 的时间 2026-10-19T15:38:21Z; 新开 pi 进程, 未续接任何实现会话.
- 承接标准: AC-001-1, AC-002-1, BR-001.
- 未参与事实: 会话记录只有 read/bash/证据写动作; 产品源码, 配置, 测试无改动; 结束后 `git status` 只多出未跟踪的证据目录.
- 权限: 未授予项目信任, 配方直接读文件; 一次 `/dev/tcp` 探测被中止后改用 ss/curl/socket 探测.
- 起止: 15:39:21Z 创建, 15:40:38Z 启动实例, 15:41:33Z 清理完成, 15:41:47Z 最后消息.
