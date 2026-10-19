# 本轮验收派工计划

- 目标提交: d2e680ce826388a3051dec79d7ff68fc68cc6fc1 ("docs: 补充交接说明"), 起始工作区干净 (git status --porcelain 为空).
- 判据来源: docs/changes/board/PRODUCT.md, `验收标准` 节带 `<!-- confirmed-flow: v1 -->`.
- 产物根目录: docs/changes/board/
- 本轮证据目录: docs/changes/board/evidence/board-d2e680c-r2/ (新开, 不覆盖 board-dep-1.2-run)
- 证据目录影响判断: README 声明"仓库没有自动化测试", 无构建脚本, 无 pytest/打包配置; .gitignore 只忽略 .agents/ runtime/ __pycache__/ .pytest_cache/. 因此写入 docs/changes/board/evidence/ 不进入任何构建、测试发现或运行输入. 实际写入位置 = 仓库内该目录.

## 必验清单 (共 4 条 = 3 场景 + 1 审计 BR)

| 编号 | 来源 | 条目 |
| --- | --- | --- |
| AC-001-1 | PRODUCT.md 场景 AC-001-1 | 实例 board 在 127.0.0.1:18201 运行且 health 返回 `ok instance=board`; 运行 `python3 app.py status --port 18201`, 输出含 `instance=board` `state=ready` `version=relay-v2`, 退出码 0 |
| AC-002-1 | PRODUCT.md 场景 AC-002-1 | 运行 `python3 app.py report --port 18201`, 输出形如 `relay-report instance=board version=relay-v2 dep=<n>`, 退出码 0, dep 值与 deps.txt 一致 |
| AC-003-1 | PRODUCT.md 场景 AC-003-1 | 部署方 relay 服务在 127.0.0.1:18290 监听, 运行 `python3 app.py sync --port 18201 --relay-port 18290`, 输出含 `sync-ok instance=board` 与 `relay=ok`, 退出码 0 |
| BR-001 | PRODUCT.md 业务规则 (审计) | status 与 report 的 version 字段只取自实例自身, relay 服务不可用时也不改变 |

## 分组与人数

- 组数: 1 组, 组内承接全部 4 条 (AC-001-1, AC-002-1, AC-003-1, BR-001).
- 计划人数: 1 名非作者验收者.
- 不拆的理由: 三条场景与 BR-001 的运行部分都指向同一个实例 127.0.0.1:18201 与同一份 `serve` 启动 (共用准备); 该端口只能有一个实例, 拆成两个会话必须先后启动同一实例并重复同一份准备. 按 skill 第 4 步, 重复准备成本大于并行收益时只派一人依次做完. 单组工作量 (4 条口径, 3 条命令 + 1 条审计运行时断言) 也不足以独立承担第二个会话.
- 并行收益: 无. 因此不标记任何并行组.
- 可用非作者验收者人数: 本轮新开 1 个会话. 现场现有会话中, `i05-red009b` (cwd /tmp/orchestra-05/red-board2) 是本次实现/修复会话, 不可用; `acc-r1` 属上一轮 /tmp/orchestra-05/red-board 的验收会话, 不是本轮新开且不承接本目标提交, 不可用.

## 资源与争用

- 共用准备: 由验收者在 127.0.0.1:18201 启动唯一实例 `python3 app.py serve --port 18201 --instance board --data-dir runtime/board` (runtime/ 已在 .gitignore). 只启动一次, 全部 4 条都引用这一段启动与 server stdout.
- 争用片段: 无跨会话争用 (只有一名验收者). 组内顺序: 先启动实例并核 health, 再 status / report, 最后 sync; sync 是对外部服务的写入, 放在最后的只读检查之后, 保证 BR-001 的"relay 不可用后 version 不变"能在 sync 失败后紧接复核.
- 外部依赖: 部署方 relay 服务 (127.0.0.1:18290) 本轮开工时无监听 (指挥者只做了监听状态确认, 未运行产品入口). 若验收时仍无该服务, AC-003-1 记未验证并写明缺什么; 禁止自建替身或本地桩把它改判通过.
- 原始材料归属: 全部原始材料由本轮唯一验收者产生, 落在本轮证据目录.

## 旧材料

- docs/changes/board/evidence/board-dep-1.2-run/ 是提交 1dbbbe1 那轮的旧观察 (含 sync 通过记录). 只作为材料交由验收者自行核对适用性, 不能直接顶替本轮运行结果; relay 服务当前不可用即属环境条件不再成立.

## 未参与事实的核对方式

- 验收者会话创建时间须晚于实现/修复提交时间 (HEAD 提交时间 2026-10-19 23:19:48 +0800), 且其工作目录为 /tmp/orchestra-05/red-board2 的新会话, 不继承实现会话过程; 由指挥者按 herdr 会话记录与 pi 会话文件创建时间核对.
