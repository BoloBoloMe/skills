# 派工计划 (acceptance-v1-ceda596)

## 输入

- 判据: `docs/changes/tool-cli/PRODUCT.md` (`验收标准` 节带 `<!-- confirmed-flow: v1 -->`).
- 目标提交: `ceda596ed3a3e96d4348a466a98c5d1c625921dd` (HEAD, 提交时间 2026-10-19T20:27:16+08:00).
- 版本前提: `git status --porcelain` 为空, 工作区与该提交一致.
- 产物根目录: `docs/changes/tool-cli/`.

## 必验清单 (4 条 = 3 个场景 + 1 条审计 BR)

| 编号 | 原文要点 |
| --- | --- |
| AC-001-1 | 运行 `python3 tool.py greet --name Ada`, 标准输出 `Hello, Ada!`, 退出码 0 |
| AC-001-2 | 运行 `python3 tool.py greet --name Ada --shout`, 标准输出 `HELLO, ADA!`, 退出码 0 |
| AC-002-1 | 文本文件 `notes.txt` 内容为 `alpha beta gamma` 加一个换行, 运行 `python3 tool.py count --file notes.txt`, 标准输出 `3`, 退出码 0 |
| BR-002 (审计) | 本变更不新增第三方依赖, 依赖清单, 锁文件和构建材料与上一提交 (`253a873`) 逐项一致 |

## 证据目录影响判断

写入位置: 仓库内 `docs/changes/tool-cli/acceptance-v1-ceda596/`.

- `build.sh`: `python3 -m compileall -q tool.py`, 只编译 `tool.py`, 不扫本目录.
- `prepare.sh` -> `tools/build_manifest.py`: 只读 `tool.py`, 只写 `dist/app.txt`, 不扫本目录.
- `python3 -m pytest -q`: 从仓库根递归收集 `test_*.py` / `*_test.py`. 本目录只写 `.md` / `.log` / `.txt` / `.sh`, 不会被收集; 已禁止在本目录创建 `test_*.py` / `*_test.py` / `conftest.py`.
- 结论: 留在仓库内, 不进入构建, 测试发现或运行输入.
- 本目录相对起始提交属于新增未跟踪文件, 除此之外无源码与 Spec 改动.

## 分组与人数

可用非作者新会话上限: 2.

| 组 | 承接标准 | 资源 | 准备 |
| --- | --- | --- | --- |
| A (groupA-greet) | AC-001-1, AC-001-2 | 只运行 `tool.py greet`, 只读 `tool.py` 中 greet 相关路径, 证据写 `groupA-greet/` | 无需构建 |
| B (groupB-count-audit) | AC-002-1, BR-002 | 运行 `tool.py count` + 只读 git 静态比对 (`deps.txt`, `deps.lock`, `build.sh`, `prepare.sh`, `tools/build_manifest.py` vs `253a873`), 证据写 `groupB-count-audit/` | 无需构建 |

- 拆开收益: 两组命令, 读写文件与证据目录互不重叠, 各自独立出结论, 可同时进行; 每组 2 条标准, 工作量足以独立承担, 不是一条 AC 一开.
- 重复准备: 无共享构建或准备步骤 (PRODUCT.md 未把 `dist/app.txt` 构造检查列为验收场景, BR-002 是静态文件比对), 所以不存在"重复准备成本大于并行收益"的情形.
- 计划人数: 2 (= 有并行收益的组数 2, 不超过可用人数 2).
- 不派一人的理由: 两组资源完全隔离且无共同前置, 单人依次做要多一轮串行时间, 没有换取到隔离或成本上的好处.
