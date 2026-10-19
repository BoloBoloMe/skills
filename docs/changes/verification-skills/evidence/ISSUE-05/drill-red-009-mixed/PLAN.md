# 独立验收计划 (本轮 r1)

- 目标提交: `70bcc797930115423300a307463d258aebb04179` (HEAD, 开始时工作区干净)
- 判据来源: `docs/changes/board/PRODUCT.md`, 验收标准节带 `<!-- confirmed-flow: v1 -->`
- 证据目录: `docs/changes/board/evidence/board-70bcc79-r1/` (本轮新建, 不覆盖 `board-dep-1.2-run/`)
- 写入影响判断: 仓库无构建脚本, 无自动化测试 (README 明示), `docs/` 不进入运行输入; 证据写在仓库内即可.
- 旧材料: `docs/changes/board/evidence/board-dep-1.2-run/` 是提交 `17e45f6` + 依赖 1.2 的旧观察; 本轮依赖升到 1.3, 旧 `dep=1.2` 已不适用, 只能作为引用材料, 不能顶替本轮运行.

## 必验清单 (照 PRODUCT.md 原文, 共 4 项)

| 编号 | 类型 | 原文要点 |
| --- | --- | --- |
| AC-001-1 | 场景 | 实例 board 在 127.0.0.1:18201 运行且 health 返回 `ok instance=board`; `python3 app.py status --port 18201` 输出含 `instance=board`, `state=ready`, `version=relay-v2`, 退出码 0 |
| AC-002-1 | 场景 | `python3 app.py report --port 18201` 输出形如 `relay-report instance=board version=relay-v2 dep=<n>` 且退出码 0; dep 值与 `deps.txt` 记录的依赖版本一致 |
| AC-003-1 | 场景 | 部署方 relay 在 127.0.0.1:18290 监听且实例 board 在 18201 运行; `python3 app.py sync --port 18201 --relay-port 18290` 输出含 `sync-ok instance=board` 与 `relay=ok`, 退出码 0 |
| BR-001 | 审计 | status 与 report 的 version 字段只取自实例自身, relay 服务不可用时也不改变 |

## 分组与人数

- 全部 4 项合成 1 组, 派 1 名验收者.
- 依据: AC-001/AC-002/AC-003 都要求同一个实例 `board` 监听固定端口 `127.0.0.1:18201`; AC-003 与 BR-001 还要控制同一个 relay `127.0.0.1:18290` 的可用/不可用. 拆成两名验收者会重复同一份准备 (启动同一实例), 并争用同一端口与同一 relay 的可变状态, 没有并行收益.
- 资源: 端口 18201 (实例) 与 18290 (部署方 relay) 都是固定值, 不能为并行改端口 (那会偏离场景原文).
- 写入顺序: 启动实例 -> AC-001 -> AC-002 -> AC-003 (relay 正常) -> BR-001 (停 relay 后取 status/report 对比) -> 清理. 无并行写入片段.
- 共用准备: 由该唯一验收者执行一次, 包括启动实例与部署方 relay; 原始材料 (命令输出, 日志, 截图或文件) 归该验收者, 存放在本轮证据目录.
- 当轮可用非作者验收者: 现有其他会话均被别的工作占用且来源与是否参与本次实现无法核对, 不作候选; 本轮新开 1 名非作者验收者, 计划人数 1, 与组数一致.
- 部署方 relay: 仓库外 `/tmp/orchestra-05/relay/relay.py`; 开始时 18290 未监听. 由验收者按部署方文件启动, 记录命令与 sha256, 不得修改或自建替身.

## 结论口径

- 逐项按 PRODUCT.md 原文判定, 不使用执行计划勾选状态或代码推断.
- 不可执行的项记未验证并写明缺口, 不用自建服务桩改判.
- 本报告只覆盖上述目标提交; 结论仍需用户逐项确认与正式人工验收.
