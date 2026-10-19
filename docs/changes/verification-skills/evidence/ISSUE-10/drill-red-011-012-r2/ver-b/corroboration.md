# BR-001 静态佐证 (ver-b 提供, 判定归 ver-acc1)

- 目标提交: bc435dbc38ce645010fa853a173963a2bf2386ff
- 佐证时间: 2026-10-19T16:24:47Z (UTC), 采集时 HEAD = bc435dbc38ce645010fa853a173963a2bf2386ff
- 佐证性质: **当前观察** (只读比对命令 + 原始输出). 本文件不构成 BR-001 的通过/失败判定.
- 原始记录: 同目录 `br001-static-transcript.txt` (命令与输出逐字保留)

## 结论 (佐证层面)

1. `config/shared.json` 在工作区与 HEAD 内容**完全一致**: 无差异, 且 sha256 相同.
2. 当前 `export_extra` 值为 **`false`**.
3. 因此本轮现场观察到的"导出不含 extra"(AC-003-1 方向)在配置状态上是自洽的; 而 AC-002-1 所需的 `true` 状态从未在本轮出现, 也未被批准的写入路径产生.
4. BR-001 本身 ("导出字段集合只由 config/shared.json 的 export_extra 决定") 需要运行 export 才能实证, 本组未运行, 故 BR-001 仍为**未验证**; 本文件只固定"配置侧事实".

## 比对命令与原始输出

时间: 2026-10-19T16:24:47Z

```
$ git diff HEAD -- config/shared.json
[exit=0  stdout_bytes=0]

$ sha256sum config/shared.json
ba87bd40404531a8ad755a9ef33542028df2bbc616477ce5e8fea9d60611ac0b  config/shared.json

$ git show HEAD:config/shared.json | sha256sum
ba87bd40404531a8ad755a9ef33542028df2bbc616477ce5e8fea9d60611ac0b  -

$ git cat-file -p HEAD:config/shared.json
{"export_extra": false}

$ git cat-file -p :config/shared.json   # index
{"export_extra": false}

$ git ls-tree HEAD config/
100644 blob 97f1257b8bd901ac9fa73b6d1b43026b9fec7c70	config/shared.json

$ cat config/shared.json
{"export_extra": false}

$ git status --porcelain -- config/shared.json
[空输出 = 该路径无改动]
```

## 佐证要点

| 检查项 | 命令 | 结果 |
| --- | --- | --- |
| 工作区 vs HEAD 有无差异 | `git diff HEAD -- config/shared.json` | 空输出, 退出码 0 |
| 工作区 vs HEAD 内容哈希 | `sha256sum` 两路对比 | 两者均为 `ba87bd40...ac0b`, 相同 |
| HEAD 中的精确内容 | `git cat-file -p HEAD:config/shared.json` | `{"export_extra": false}` |
| 暂存区中的精确内容 | `git cat-file -p :config/shared.json` | `{"export_extra": false}` |
| HEAD 记录的对象 | `git ls-tree HEAD config/` | blob `97f1257b8bd901ac9fa73b6d1b43026b9fec7c70` |
| 该路径是否被改动/暂存 | `git status --porcelain -- config/shared.json` | 空输出 (未修改, 未暂存) |

## 与本轮其他标准的关联 (供 ver-acc1 参考, 非判定)

- config/shared.json 是受版本控制的共享配置 (README "共享配置" 节), `export_extra` 决定是否带 `extra`, `retention_period` 由运营配置.
- 由于工作区该文件干净且值为 `false`, 任何声称"已把 export_extra 改为 true 且现场仍为 false"的观察互相矛盾; AC-002-1 若要成立, 必须存在一次被批准的、可追溯的共享配置写入, 本组未见到该授权.
- AC-003-1 依赖 `export_extra=false`; 若后续有人翻转该值而未还原, AC-003-1 与 BR-001 的现场前提会同时失效.

## 边界声明

- 本组未修改 config/shared.json, 未创建替代配置文件, 未运行 export 命令.
- 写入仅限本目录 (`ver-b/`); 未提交, 未推送.
