# 派工计划 (round r1)

- 目标提交: `c0505dee33c9c78ffaaf61f88e05e041a7e29402` (HEAD)
- 判据来源: `docs/changes/tool-cli/PRODUCT.md` (`验收标准` 节 `<!-- confirmed-flow: v1 -->`, 以及标 `(审计)` 的业务规则)
- 证据目录: `docs/changes/tool-cli/evidence-c0505de-r1/` (项目内, 见下影响判断)
- 计划生成时间: 2026-10-19T20:44:11+08:00

## 必验清单 (9 项)

场景 (8): AC-001-1, AC-001-2, AC-001-3, AC-002-1, AC-002-2, AC-002-3, AC-003-1, AC-003-2
审计 BR (1): BR-002 (依赖清单/锁文件/构建材料与上一提交逐项一致)

BR-001 无独立审计标记, 由 AC-001-1/2/3 与 AC-003-1/2 的场景判据覆盖, 不另立条目.

## 分组

| 组 | 承接标准 | 工作量 | 独占资源 |
| --- | --- | --- | --- |
| A (verifier-a) | AC-001-1, AC-001-2, AC-001-3, AC-003-1, AC-003-2 | 4 次单点运行 + 452 次批量运行 (greet 250 + export 200) | `data/greet/names.txt`, `data/export/names.txt` |
| B (verifier-b) | AC-002-1, AC-002-2, AC-002-3, BR-002 | 2 次单点运行 + 250 次批量运行 + 1 次静态比对 | `data/count/docs/`, `data/count/expected.tsv`, git 历史比对 |

## 收益与人数依据

- 拆开后的实际收益: 两组输入数据互不共享 (README 明确三组数据互不引用), 两组都不需要预构建 (build.sh 只 compileall tool.py, 无前置产物), 因此两次会话没有重复准备成本; 批量子场景 (250/200 条) 是主要耗时, 分成两路可并行缩短墙钟时间.
- 当轮可用非作者验收者人数: 2 (本轮授权上限 2 个新子会话).
- 计划人数: 2 = min(有并行收益的组数 2, 可用人数 2).
- 未采用 3 组: 授权上限只有 2, 且把 greet 与 export 再拆会引入第三份重复的单点准备而不增加收益.
- 未只派 1 人: 两组资源独立且均无预构建开销, 并行收益真实存在.

## 证据目录影响判断

- `build.sh`: 只 `python3 -m compileall -q tool.py`, 不扫描证据目录.
- 测试发现: 无 pytest 配置 (无 pytest.ini/pyproject/setup.cfg), 默认只收集 `test_*.py` 或 `*_test.py`; 证据目录内只有 `.md/.txt/.log/.tsv` 与子目录, 不进入收集.
- 运行输入: `tests/test_tool.py` 只引用 `tool.py` 与 `notes.txt`; 证据目录不被任何测试或脚本读取.
- 结论: 写进项目内不影响构建与测试, 实际写入位置即上述证据目录; 该目录是本轮相对起始提交唯一的新增物 (未被 .gitignore 覆盖, 会在 `git status` 里显示为未跟踪).
