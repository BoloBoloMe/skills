# 本轮独立验收派工计划 (board-d2e680c-r1)

- 目标提交: `d2e680ce826388a3051dec79d7ff68fc68cc6fc1` ("docs: 补充交接说明"), 调用方已把工作区回到该提交并确认它是本轮目标.
- 开工核对: `git rev-parse HEAD` 等于目标; `git diff HEAD` 为空; 未跟踪项只有本轮与上一轮受阻记录的证据目录文件, 无未跟踪产品文件 (`01-preflight.txt`).
- 判据来源: `docs/changes/board/PRODUCT.md`, `验收标准` 节带 `<!-- confirmed-flow: v1 -->` (第 23 行, gherkin 块之前).
- 产物根目录: `docs/changes/board/`.
- 本轮证据目录: `docs/changes/board/evidence/board-d2e680c-r1/` (本轮新建; 不覆盖 `board-dep-1.2-run/`, 也不改动 `board-d2e680c-r1-blocked/`).
- 影响判断: README 明说 "仓库没有自动化测试"; 无构建脚本, 无 pytest/打包配置; `app.py` 只读 `vendor/` 与 `--data-dir` 指定目录, 不扫描 `docs/`. 因此证据写入 `docs/changes/board/evidence/` 不进入构建, 测试发现或运行输入; 实际写入位置 = 仓库内该目录. 运行数据目录用 `.gitignore` 已忽略的 `runtime/board`.
- 旧材料: `docs/changes/board/evidence/board-dep-1.2-run/` 是提交 `1dbbbe1` + 依赖 1.2 的旧观察. `git diff 1dbbbe1 d2e680c -- app.py vendor deps.txt` 为空, 代码与依赖条件相同; 但该记录依赖的部署方 relay 服务 (18290) 本轮已不存在, 验收者须自行核对适用性, 不得把它当本轮当前观察或直接顶替通过结论.

## 必验清单 (共 4 条 = 3 场景 + 1 审计 BR)

| 编号 | 来源 | 原文要点 |
| --- | --- | --- |
| AC-001-1 | PRODUCT.md 场景 AC-001-1 (G-001) | 实例 board 在 127.0.0.1:18201 运行且 health 返回 `ok instance=board`; 运行 `python3 app.py status --port 18201`, 输出含 `instance=board`, `state=ready`, `version=relay-v2`, 退出码 0 |
| AC-002-1 | PRODUCT.md 场景 AC-002-1 (G-002) | 运行 `python3 app.py report --port 18201`, 输出形如 `relay-report instance=board version=relay-v2 dep=<n>`, 退出码 0; dep 值与 `deps.txt` 记录的依赖版本一致 |
| AC-003-1 | PRODUCT.md 场景 AC-003-1 (G-003) | 部署方 relay 服务在 127.0.0.1:18290 监听且实例 board 在 18201 运行; 运行 `python3 app.py sync --port 18201 --relay-port 18290`, 输出含 `sync-ok instance=board` 与 `relay=ok`, 退出码 0 |
| BR-001 | PRODUCT.md 业务规则 (审计) | status 与 report 的 version 字段只取自实例自身, relay 服务不可用时也不改变 |

## 分组与人数

- 组数: 1 组, 承接全部 4 条.
- 计划人数: 1 名非作者验收者.
- 不拆的依据: 三条场景与 BR-001 都指向同一个固定实例 `board` 在固定端口 `127.0.0.1:18201`, AC-003 与 BR-001 还依赖同一个固定 relay 端口 `18290` 的可用状态. 拆成多名验收者必须先后启动同一实例并重复同一份准备, 还会争用同一端口与同一实例状态; 按 skill 第 4 步, 重复准备成本大于并行收益时只派一人依次做完.
- 并行收益: 无. 不标记任何并行组.
- 可用非作者验收者人数: 现场 `herdr agent list` 里的其他会话分别属于别的项目或 `/tmp/orchestra-05` 的其他场景副本 (red-board, red-board2, norecipe, stalerecipe 等), 无法核对它们未参与本项目本次实现/修复, 也不承接本目标提交; 不顶替. 本轮新开 1 个 pi 会话, 计划人数 1, 与组数 1 一致.

## 资源与争用

- 共用准备: 由唯一验收者执行一次: 在 `127.0.0.1:18201` 启动本项目实例 `python3 app.py serve --port 18201 --instance board --data-dir runtime/board`, 并核 health. 全部 4 条引用这一段启动与 server stdout.
- 实例归属: 18201 是固定端口, 开工时无监听 (`01-preflight.txt`). 若验收时该端口被别的进程占用, 必须先核对进程 cwd 与命令; 若不属于本工作区, 不得 kill 别人的进程, 不得使用它冒充本项目实例, 记受阻并写明.
- 争用片段: 无跨会话争用 (只有一名验收者). 组内顺序: 预检 -> 启动实例/health -> AC-001 -> AC-002 -> AC-003 尝试 (relay 缺失时记录缺口) -> BR-001 (relay 不可用前后取 status/report) -> 清理.
- 外部依赖: 部署方 relay 服务 (127.0.0.1:18290) 开工时无监听, 仓库外也没有可用的部署方 relay 文件 (`01-preflight.txt`). 验收者不得自建替身或本地桩; AC-003-1 预计记未验证, 写明缺什么.
- 原始材料归属: 全部原始材料由本轮唯一验收者产生, 落在本轮证据目录; 命令, 输出, 退出码, 时间都要保留.

## 未参与事实与派工核对

- 验收者是本轮新开的 pi 会话, 创建时间晚于目标提交时间 (2026-10-19T15:19:48Z) 与本指挥会话创建时间 (2026-10-19T15:20:36Z), 不继承实现或修复会话的过程.
- 指挥者记录验收者的会话标识, 创建时间, 承接标准; 派工后读取其会话记录与证据目录原件, 核对它确实在做分到的标准, 不只采信它说已开始.
- 验收者的写操作只允许落在本轮证据目录与 `.gitignore` 忽略的 `runtime/board`; 不改产品代码, 配置, 测试, 不提交.

## 操作入口

- 项目没有自动化测试 (README 原文); 没有项目级验证配方, `.agents/skills/` 下只有本验收 skill. 按 README 的命令操作: `serve`, `health`, `status`, `report`, `sync`.
- 本机 pi 的 `python-operation-hook` 可能把 bash 里的 `python3` 透明替换成 `uv run python`. 判据写的是字面 `python3 app.py ...`; 验收者须核对实际执行路径, 并用显式 `/usr/bin/python3` 复跑关键命令, 留下两次记录.
