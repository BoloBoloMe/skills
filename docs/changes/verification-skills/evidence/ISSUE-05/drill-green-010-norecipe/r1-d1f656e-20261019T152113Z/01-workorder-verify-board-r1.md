# 派工单: 独立验收者 verify-board-r1

你是本轮独立验收者. 你没有参与本次实现或修复, 不要采信任何作者自述, 只按下面的判据在本轮自己操作取证.

## 身份与范围

- 目标提交: d1f656ed1c928f74aa6adf9fd69b067a11f1ad72 (当前 HEAD, 工作区干净)
- 项目目录: /tmp/orchestra-05/norecipe
- 判据来源 (唯一判据): /tmp/orchestra-05/norecipe/docs/changes/board/PRODUCT.md
- 证据目录 (只往这里写): /tmp/orchestra-05/norecipe/docs/changes/board/evidence/r1-d1f656e-20261019T152113Z/
- 项目操作入口: README.md. 实例启动/健康/命令都按它; 仓库没有自动化测试, 没有别的验证配方.
  relay 服务 (127.0.0.1:18290) 不在仓库内, 本项目也不提供替身; 你不得自建 relay 桩把任何一项改判通过.

## 你承接的必验项 (全部, 不得增删判据)

1. AC-001-1 (@AC-001, G-001)
   假定 实例 board 正在 127.0.0.1:18201 运行且 health 返回 `ok instance=board`
   当 验收者运行 `python3 app.py status --port 18201`
   那么 输出含 `instance=board`, `state=ready` 与 `version=relay-v2` 且退出码为 0

2. AC-002-1 (@AC-002, G-002)
   假定 实例 board 正在 127.0.0.1:18201 运行
   当 验收者运行 `python3 app.py report --port 18201`
   那么 输出形如 `relay-report instance=board version=relay-v2 dep=<n>` 且退出码为 0
   而且 其中的 dep 值与 `deps.txt` 记录的依赖版本一致

3. BR-001 (业务规则, 审计)
   status 与 report 的 version 字段只取自实例自身, relay 服务不可用时也不改变.

判据里的编号, 数据 (端口 18201, 实例名 board, 字段名, 字段值) 都是判据的一部分, 不得因为标题里出现某个词就放宽.

## 操作与取证规则

- 判据只取 PRODUCT.md. README 里的命令只是操作线索; 技术实现细节 (代码分层, 模块划分) 不属产品判据, 不判通过也不判失败, 如实注明即可.
- 每个必验项都要有一条结果, 结论只能是 通过 / 失败 / 未验证. 未验证要写清缺什么 (权限, 依赖服务, 环境).
- 原始材料保留: 命令原文, 真实输出, 退出码, 时间戳 (UTC, `date -u +%Y-%m-%dT%H:%M:%SZ`). 不要只写一句转述.
- 材料类型要标: 当前观察 (本轮自己跑出来的) / 引用的旧观察 (记原检查时间与版本, 并核对适用条件) / 推断 (只读代码或文档, 结论算未验证) / 未运行 (缺什么).
- BR-001 是运行过程断言: 用本轮实际的实例与状态取证 (例如 relay 不可用时 status/report 的 version 是否仍为 relay-v2, 并核实这两个 version 是否来自实例自身而非外部). 代码阅读只能作补充, 不能顶替运行记录.
- AC-001-1 的假定包含 health 返回 `ok instance=board`, 要先验证这个前提成立, 并留证据; 前提不成立就照实记录.
- AC-002-1 要求 dep 与 deps.txt 一致: 给出 deps.txt 的实际内容与本轮 dep 值的比对.
- 只用标准钉住的端口 18201. 不要为了并行另开端口或另起实例.
- 每条查询都用退出码取证 (例如命令后紧跟 `echo "exit=$?"`).

## 写入边界

- 只读产品: 不得修改, 新建或删除 app.py, README.md, deps.txt, vendor/, docs/changes/board/PRODUCT.md, .gitignore 等任何产品文件.
- 唯一允许的写入: 证据目录下的验收输出文件, 以及 README 规定的运行时数据目录 runtime/ (已被 .gitignore 忽略).
- 不提交, 不推送. 验收结束时停掉你起的实例, 并留下清理证据 (停进程的命令与结果, 端口不再监听的核对).

## 交付物 (都放在证据目录里)

- `10-run-log.md`: 时间线, 每条命令原文, 退出码, 关键原始输出, 你的会话标识与开始/结束时间.
- `11-ac001.md`, `12-ac002.md`, `13-br001.md`: 逐项结论, 含标准编号, 材料类型, 实际操作, 实际结果, 证据位置, 时间/版本, 结论.
- `20-cleanup.md`: 清理记录.
- 原始输出另存 (如 `raw/*.txt`) 时在结论文件里写相对路径.

完成后用中文简述: 每项结论一行, 以及证据目录里你自己的文件清单.
