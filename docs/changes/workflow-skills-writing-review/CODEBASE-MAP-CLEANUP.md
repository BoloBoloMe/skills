# codebase-map 正文账本清理

用户 2026-11-01 发现: `codebase-map` 的交付正文 (SKILL.md, README.md) 写着本次航行的账本信息, 而不是使用这个 skill 需要的内容.

## 问题

- 里程碑编号: m13 / m21 / m23 / m24 / m25 / m26, milestone-13/21/24/26 的叙述与"保留 / v1 已实现"这类版本史.
- 决策与条文编号: D001 / D002 / D004 / D009 / D010 / D014 / D015 / D016 / D017 / D021 / D022 / D023 / D024 / D025 / D027 / D030, U001 到 U004, BR-013 到 BR-037, NG-001 / NG-009, AC-001, F001 / F002 / F011 / F012 / F014, ISSUE-04.
- 本仓库路径: `docs/changes/workflow-stack-review/milestone-13/DECISIONS.md`, `../milestone-24/DECISIONS.md`.

坏处: 这些编号对使用该 skill 的会话没有意义; skill 同步到 `~/.agents/skills/` 后, 那些 `docs/changes/...` 指针指向 skill 目录之外的本仓库历史, 换机器直接断; 每改一次决策要连带改 skill 正文.

## 处置 (2026-11-01)

- `SKILL.md`: 删掉全部编号与版本史叙述, 补上原本缺失的 H1; `## m21 汉化构建链 (保留)` 改为 `## 汉化构建链`. 操作内容 (三子命令, 交付纪律, 地址来源, 失败出口清单, 状态复原, 版本口径, 使用纪律, 汉化链) 一字未减.
- `README.md`: 删掉全部编号与 `docs/changes` 指针; 把"v1 服务就位前 ... 已作废"的删除线段落改写成正向禁令 (不要用 `python3 -m http.server` 顶替 `serve`, 会占住 8090 导致 `port_in_use`).
- 追溯: 决策与实测依据仍在本仓库 `docs/changes/workflow-stack-review/` 与提交历史里, 不再写进 skill 正文.

## 未动

- `scripts/*.py` (约 130 处) 与 `tools/*` (约 12 处) 的注释与 docstring 里仍有编号. 它们是维护者读的代码注释, 且与实现细节相邻, 改动风险高于收益; 需要清理时另开一次.
- `tests/` 未改; `workflow/codebase-map/tests` 85 项全过 (2026-11-01, 21 秒).
