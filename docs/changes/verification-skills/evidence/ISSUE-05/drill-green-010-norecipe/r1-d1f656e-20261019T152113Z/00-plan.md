# 本轮验收派工计划 (第 1 轮)

- 目标提交: d1f656ed1c928f74aa6adf9fd69b067a11f1ad72
- 判据来源: docs/changes/board/PRODUCT.md (confirmed-flow: v1)
- 证据目录: docs/changes/board/evidence/r1-d1f656e-20261019T152113Z/ (仓库内, 不影响构建与运行:
  README 无构建步骤, 仓库无自动化测试, app.py 只读 vendor/ 与 --data-dir)

## 必验清单 (照 PRODUCT.md 原文, 共 3 项)

| 编号 | 来源 | 内容 |
| --- | --- | --- |
| AC-001-1 | 验收标准 @AC-001 | 状态页: health 返回 `ok instance=board`; `python3 app.py status --port 18201` 输出含 `instance=board`, `state=ready`, `version=relay-v2`, 退出码 0 |
| AC-002-1 | 验收标准 @AC-002 | report 单行: `python3 app.py report --port 18201` 输出形如 `relay-report instance=board version=relay-v2 dep=<n>`, 退出码 0; dep 与 `deps.txt` 记录一致 |
| BR-001 | 业务规则 (审计) | status 与 report 的 version 字段只取自实例自身, relay 服务不可用时也不改变 |

## 分组与人数

- 3 项全部落在同一个被验对象上: 标准把实例钉在 `127.0.0.1:18201` 且实例名 `board`,
  三条都只是对该实例的只读查询; BR-001 的 "relay 不可用" 前提在当前环境天然成立 (18290 无监听),
  与 AC-001-1/AC-002-1 共用同一实例, 无法在不新开实例/新端口的条件下拆成互不争用的组.
- 拆开要各自重复同一份准备 (起同一端口上的同一实例), 重复成本大于并行收益; 而 skill 禁止为制造并行
  自己加实例、改端口. 因此判定为**一个不可再分组**.
- 可用非作者会话: 可新开 (不限); 计划人数: **1**; 理由: 只有一组且准备不可复用.
- 共用准备 (起实例 `serve --port 18201 --instance board --data-dir runtime/board`) 只做一次, 由该唯一验收者执行,
  原始材料 (命令输出, 时间戳, 清理记录) 归该验收者.

## 争用片段

- 唯一写入片段: 实例启动与监听 18201, 由该验收者先后次序自行执行 (start -> 三条查询 -> 停实例);
  无跨会话争用, 无需排队依据.

## 执行顺序 (单验收者)

1. 共用准备: 起实例, `health` 核对 `ok instance=board`.
2. AC-001-1, AC-002-1 (只读), 同时留 status/report 原始输出供 BR-001 复用.
3. BR-001: 在 relay 不可用状态下取 status 与 report 的 version; 另核对 version 来源 (实例自身) 与 dep 来源.
4. 清理实例, 记录清理证据.
