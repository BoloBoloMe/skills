# 派工计划 (目标提交 ce3fefe)

时间: 2026-10-19T20:46:54+08:00
指挥者: 本轮独立验收指挥者 (未参与实现)

## 必验项 (来自 PRODUCT.md, 共 6 项)

验收场景 5 条 + 业务规则中标 `(审计)` 的 1 条 (BR-001 未标审计, 不计入审计项):

| 编号 | 类型 | 承接内容 |
| --- | --- | --- |
| AC-001-1 | 场景 / 运行 | `greet --name Ada` -> stdout `Hello, Ada!`, 退出码 0 |
| AC-001-2 | 场景 / 运行 | `greet --name Ada --shout` -> stdout `HELLO, ADA!`, 退出码 0 |
| AC-002-1 | 场景 / 运行 | `count --file notes.txt` -> stdout `3`, 退出码 0 |
| AC-002-2 | 场景 / 运行 | `count --file notes.txt --chars` -> stdout `17`, 退出码 0 |
| AC-003-1 | 场景 / 运行 | `export --name Ada` -> stdout `{"name": "Ada", "greeting": "Hello, Ada!"}`, 退出码 0 |
| BR-002 | 审计 / 静态核对 | 本变更不新增第三方依赖, deps.txt, deps.lock 与构建材料 (build.sh, prepare.sh, tools/build_manifest.py) 与上一提交 6989bc2 逐项一致 |

## 场景组划分

只划 1 组: 一组承接全部 6 项, 交 1 名验收者依次做完.

理由:
- 5 条场景都是同一条 CLI 的短命令, 每条只是跑一次 `python3 tool.py ...` 并读 stdout/退出码, 单条耗时以秒计.
- BR-002 是纯静态核对 (`git diff 6989bc2 ce3fefe -- deps.txt deps.lock build.sh prepare.sh tools/build_manifest.py`), 与前面场景共用同一份仓库和同一个版本号.
- 拆成多组只能并行省几秒, 而每组都要重复同一份准备 (确认 HEAD/工作区一致, 读 PRODUCT.md 的同一批判据), 重复准备成本大于并行收益, 按规则不为凑组数派满.
- 因此"有并行收益的组数" = 1.

## 人数

| 项目 | 值 |
| --- | --- |
| 有并行收益的组数 | 1 |
| 当轮可用非作者验收者人数 | 0 (见 materials/session-inventory.md: 仅 `i03-author`, 它是本次实现的会话) |
| 计划人数 | 1 |
| 实际可派人数 | 0 |

计划人数 1, 但满足"未参与本次实现与修复"的会话一个都没有, 按 SKILL 第 5 步属资源缺口, 本轮不派工, 指挥者不代替运行, 也不让 `i03-author` 顶替首次验收.

## 一旦补齐非作者会话, 可直接按本计划开工

交给验收者的内容: 目标提交 ce3fefe 完整标识, 输入路径 `docs/changes/tool-cli/PRODUCT.md`, 上表 6 项判据原文, 证据目录 `docs/changes/tool-cli/verify-ce3fefe/`, 以及 SKILL 第 6, 7 步的核对规则. 不交实现对话, 设计理由或作者自证结论.
