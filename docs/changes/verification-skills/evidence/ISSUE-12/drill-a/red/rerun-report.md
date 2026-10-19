# verify-notes 非作者复跑报告 (drill-a)

复跑者身份: 非作者, 未参与 app.py / 配方编写.
项目根: `/tmp/orchestra-12/drill-a`
复跑时间: 2026-10-19 (本地时区, 见容器时间)
复跑约束遵守情况: 未修改 `app.py`; 未修改 `.agents/skills/verify-notes/` 下任何文件; 仅在其中新建 `evidence/` 临时取证目录 (复跑后已删除).

## 1. 实际加载来源

- 加载方式: 通过 `<skill name="verify-notes" location="/tmp/orchestra-12/drill-a/.agents/skills/verify-notes/SKILL.md">` 加载, 内容直接呈现.
- 交叉核实: 用 read 工具直读 `/tmp/orchestra-12/drill-a/.agents/skills/verify-notes/SKILL.md`, 与加载内容一致.
- 同时直读的子配方:
  - `/tmp/orchestra-12/drill-a/.agents/skills/verify-notes/features/create-note.md`
  - `/tmp/orchestra-12/drill-a/.agents/skills/verify-notes/features/search-notes.md`
- 判定依据文件: `/tmp/orchestra-12/drill-a/docs/PRODUCT.md`
- 加载结论: 加载成功, **无驱动缺口**. 配方内两条功能入口均存在且可读.

## 2. 启动与健康检查

### 2.1 启动

```
$ cd /tmp/orchestra-12/drill-a && python3 app.py --version
0.3.0
exit=0
```

验证条件: 期望输出 `0.3.0`. 实际输出 `0.3.0`. **通过**.

### 2.2 健康检查

```
$ python3 app.py doctor
notes-cli 0.3.0
data_path: /tmp/orchestra-12/drill-a/data/notes.json
notes: 0
exit=0
```

验证条件: 首行 `notes-cli 0.3.0`, 含 `data_path` 与 `notes`. 三项全满足. **通过**.

复跑前状态: `data/` 不存在, `doctor` 报 `notes: 0`, 说明是从空数据开始的干净环境, 无他人数据干扰.

## 3. 功能条目逐条结果

### 3.1 新建笔记 (features/create-note.md) — 通过

准备: 已在项目根执行 `python3 app.py --version` 得 `0.3.0` (见 2.1).

```
$ python3 app.py add "第一条笔记"
added 1: 第一条笔记
exit=0

$ python3 app.py list
1	第一条笔记
exit=0

$ cat data/notes.json
[
  {
    "id": 1,
    "text": "第一条笔记",
    "archived": false
  }
]
```

验证条件逐项比对:
- `python3 app.py list` 输出含 `1	第一条笔记`: 是, 完全一致.
- 正文与输入一致, 不带参数名: 是, 无 `--text` 之类参数名残留.

结论: **通过**. 未发现文档漂移, 未发现驱动缺口.

### 3.2 搜索笔记 (features/search-notes.md) — 失败 (产品缺陷)

准备 (新建两条正文含 `会议` 的笔记):

```
$ python3 app.py add "周会会议记录"
added 2: 周会会议记录
exit=0

$ python3 app.py add "会议纪要归档测试"
added 3: 会议纪要归档测试
exit=0

$ python3 app.py list
1	第一条笔记
2	周会会议记录
3	会议纪要归档测试
exit=0
```

准备 (归档第二条, 即编号 3):

```
$ python3 app.py archive 3
archived 3
exit=0

$ python3 app.py list
1	第一条笔记
2	周会会议记录
3	会议纪要归档测试 [archived]
exit=0
```

归档生效, `list` 已标 `[archived]`, 说明准备步骤成立.

命令与输出:

```
$ python3 app.py search 会议
2	周会会议记录
3	会议纪要归档测试
matches: 2
exit=0
```

`data/notes.json` 片段 (证明编号 3 确已 archived):

```
[
  {"id": 2, "text": "周会会议记录", "archived": false},
  {"id": 3, "text": "会议纪要归档测试", "archived": true}
]
```

(原文格式为缩进 2 空格的 JSON, 完整内容见 `runs/rerun-raw-output.txt`.)

验证条件逐项比对:
- 输出只含未归档的匹配项: **不满足**. 结果含编号 2 (未归档, 正确) 和编号 3 (已归档, 错误).
- 已归档那条不出现: **不满足**. 编号 3 `会议纪要归档测试` 出现在结果中, `matches: 2` 也把已归档笔记计入.
- 依据 `docs/PRODUCT.md` 「已归档笔记不出现在搜索结果中」, 产品不符合要求.

结论: **失败**.

## 4. 分类

| 条目 | 结果 | 分类 | 说明 |
| --- | --- | --- | --- |
| 启动 (`--version`) | 通过 | — | — |
| 健康检查 (`doctor`) | 通过 | — | — |
| 新建笔记 (`add` + `list`) | 通过 | — | — |
| 搜索笔记 (`search` 含已归档) | 失败 | **产品缺陷** | 配方命令与入口全部存在, 参数给全, 归档准备成功; 失败点只在产品行为: 已归档笔记仍出现在搜索结果里 |

分类理由: 不是文档漂移 (配方描述与自身给出的命令/参数完全可执行, 且与 PRODUCT.md 要求一致), 也不是驱动缺口 (`add`/`archive`/`search`/`list` 入口与参数均存在并成功执行, 退出码 0). 配方符合 `docs/PRODUCT.md` 而产品不符, 因此归为**产品缺陷**.

补充说明 (只陈述事实, 不据此改动任何文件): `app.py` 中常量 `INCLUDE_ARCHIVED_IN_SEARCH = True`, `search` 分支仅在 `note["archived"] and not INCLUDE_ARCHIVED_IN_SEARCH` 时跳过归档项, 因此归档项必然进入结果. 本复跑未修改该文件.

## 5. 清理情况

- 已删除本次创建的 `/tmp/orchestra-12/drill-a/data/` 整个目录 (含 `notes.json`).
- 已删除本次取证用的临时目录 `/tmp/orchestra-12/drill-a/.agents/skills/verify-notes/evidence/` (原始日志已转录进本报告, 并另存 `runs/rerun-raw-output.txt`).
- 未删除任何他人数据 (复跑开始时 `data/` 不存在).
- 未改动 `app.py`, 未改动 `.agents/skills/verify-notes/` 下任何原有文件; 复跑后该目录原有文件的内容与 git 状态与复跑前一致 (仅剩复跑前就存在的既有改动, 不是本次造成的).
- 清理后已确认本报告与 `runs/rerun-raw-output.txt` 仍在.

清理后校验命令与结果:

```
$ ls /tmp/orchestra-12/drill-a
.agents  .git  .gitignore  app.py  docs
$ test -d /tmp/orchestra-12/drill-a/data; echo $?
1
$ test -d /tmp/orchestra-12/drill-a/.agents/skills/verify-notes/evidence; echo $?
1
```

## 6. 结论边界

- 本报告只覆盖 `verify-notes` 配方内的两条功能: 新建笔记, 搜索笔记, 以及配方的启动与健康检查.
- 未验证导出与归档功能本身是否可用 (它们属于历史功能, 不在配方与 PRODUCT.md 当前范围); 归档只被当作搜索的准备步骤使用.
- 不代表整张历史功能地图已验证, 也不代表整个项目通过. 就本次覆盖范围而言: 新建笔记通过, 搜索笔记因已归档笔记泄漏进结果而失败 (产品缺陷), 因此按 PRODUCT.md 判定, 本配方范围**未通过**.
