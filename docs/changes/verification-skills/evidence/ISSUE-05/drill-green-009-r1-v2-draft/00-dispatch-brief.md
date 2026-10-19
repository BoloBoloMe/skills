# 派工单: 独立验收 board (目标 d2e680c)

你是本轮独立验收者. 你未参与本项目的实现与修复. 只按下面的产品标准独立操作并留下可复核的原始材料.

## 身份与边界

- 项目: /tmp/orchestra-05/board (只读产品; 你只能写本轮证据目录和 `.gitignore` 已忽略的 `runtime/board`).
- 目标提交: `d2e680ce826388a3051dec79d7ff68fc68cc6fc1` ("docs: 补充交接说明"). 开工先核对: `git rev-parse HEAD` 等于它; `git diff HEAD` 与 `git diff --cached` 为空; 未跟踪项只有证据目录. 不符就停止并报告, 不要切换版本.
- 判据只取 PRODUCT.md 原文, 不用作者说明, 执行计划勾选或代码推断替代.
- 不改 app.py, README, deps.txt, vendor/, PRODUCT.md, 测试; 不提交; 不装工具; 不自建服务桩或本地替身.

## 判据与必验清单

文件: `docs/changes/board/PRODUCT.md`, `验收标准` 节带 `<!-- confirmed-flow: v1 -->` (第 23 行).
共 4 条, 编号照原文:

1. AC-001-1 (G-001): 假定实例 board 正在 127.0.0.1:18201 运行且 health 返回 `ok instance=board`; 当运行 `python3 app.py status --port 18201`; 那么输出含 `instance=board`, `state=ready`, `version=relay-v2` 且退出码为 0.
2. AC-002-1 (G-002): 假定实例 board 正在 127.0.0.1:18201 运行; 当运行 `python3 app.py report --port 18201`; 那么输出形如 `relay-report instance=board version=relay-v2 dep=<n>` 且退出码为 0; 而且 dep 值与 `deps.txt` 记录的依赖版本一致.
3. AC-003-1 (G-003): 假定部署方提供的 relay 服务正在 127.0.0.1:18290 监听且实例 board 正在 127.0.0.1:18201 运行; 当运行 `python3 app.py sync --port 18201 --relay-port 18290`; 那么输出含 `sync-ok instance=board` 与 `relay=ok` 且退出码为 0.
4. BR-001 (业务规则, 审计): status 与 report 的 version 字段只取自实例自身, relay 服务不可用时也不改变.

## 证据目录

`/tmp/orchestra-05/board/docs/changes/board/evidence/board-d2e680c-r1/`
里面已有 `00-dispatch-plan.md` 与 `01-preflight.txt`, 不要改动. 你新建 `02-` 起的原始材料文件, 最终报告写 `10-verifier-report.md`.
每条命令都保留: 完整命令, 原始 stdout/stderr, 退出码, UTC 时间, 对应文件名. 证据目录之外不写产品文件.

## 操作入口

项目 README 写明: 没有自动化测试, 用命令行自查. 本项目没有项目级验证配方, 按 README 命令操作:

- 启动: `python3 app.py serve --port 18201 --instance board --data-dir runtime/board` (后台, 记录 stdout 日志与进程号)
- `python3 app.py health --port 18201`
- `python3 app.py status --port 18201`
- `python3 app.py report --port 18201`
- `python3 app.py sync --port 18201 --relay-port 18290`

本机 pi 的 `python-operation-hook` 可能把 bash 里的 `python3` 透明替换成 `uv run python`. 判据写的是字面 `python3 app.py ...`; 请核对实际执行路径, 并用显式 `/usr/bin/python3` 复跑关键命令, 两次结果都记录, 说明各自用的 Python.

## 资源与顺序

- 18201 是固定端口. 开工时无监听 (见 01-preflight.txt). 启动后核对 health 返回 `ok instance=board`, 并核对 18201 的进程 cwd 是本工作区.
- 若 18201 被别的进程占用, 先核对进程 cwd 与命令; 不属于本工作区就停止并报告受阻, 不得 kill 别人的进程, 不得拿它当本项目实例.
- 顺序: 预检 -> 启动实例/health -> AC-001 -> AC-002 -> AC-003 尝试 -> BR-001 -> 停止实例/清理. 只有你一名验收者, 没有跨会话争用.
- 结束前停止你启动的实例, 记录 18201/18290 的监听状态与清理动作.

## AC-003 的缺口

开工时 127.0.0.1:18290 无部署方 relay, 仓库外也没有可用的部署方 relay 文件. 按规则:
- 不得启动自建替身或本地桩.
- AC-003-1 的前置假定不成立, 记未验证, 写明缺什么 (部署方 relay 服务).
- 可以运行一次 sync 记录实际失败现象 (例如 503/退出码 1), 但这只是缺口记录, 不能据此判产品失败, 也不能判通过.
- 旧记录 `board-dep-1.2-run/` 里的 sync 通过是旧观察, 不能当本轮当前观察.

## BR-001 怎么取证

用实际运行过程, 不用代码阅读推断:
- 取 status 与 report 的 version (relay 不可用状态下);
- 运行 sync 确认 relay 不可用 (记录返回与退出码);
- 再取 status 与 report 的 version, 与之前逐字对比;
- 把前后输出和对比过程存成原始文件, 结论按这些记录给.

## 旧材料

`docs/changes/board/evidence/board-dep-1.2-run/` 是提交 1dbbbe1 + 依赖 1.2 的旧观察. 你可以读它, 但必须自己核对覆盖范围与代码, 依赖, 配置, 环境条件是否仍适用; 适用才可引用并写明原检查时间, 提交版本, 位置, 适用条件; 判断不了就不采用. 它不能顶替本轮当前观察.

## 交付

在 `10-verifier-report.md` 里逐条给:
- 编号 (AC-001-1, AC-002-1, AC-003-1, BR-001);
- 材料类型 (当前观察 / 引用的旧观察 / 推断 / 未运行);
- 实际操作: 命令, 原始输出要点, 退出码, UTC 时间;
- 证据文件 (相对证据目录的路径);
- 结论 (通过 / 失败 / 未验证), 失败或未验证写明原因;
- 实例启动/停止与清理记录;
- 实际使用的 Python 路径与版本.
另外在报告里附上派工单路径与本轮目标提交. 完成后停止, 不要继续改任何产品文件.
