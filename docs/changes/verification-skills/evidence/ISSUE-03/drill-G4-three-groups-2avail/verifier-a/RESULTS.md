# 验收结果 (verifier-a)

- 目标提交: `c0505dee33c9c78ffaaf61f88e05e041a7e29402`
- 实测时 `git rev-parse HEAD` = `c0505dee33c9c78ffaaf61f88e05e041a7e29402` (一致, 见 `head.txt`)
- 工作区: `git status --porcelain --untracked-files=all` 仅有 `docs/changes/tool-cli/evidence-c0505de-r1/` 下的未跟踪文件 (分发文件, verifier-a/, verifier-b/), 无任何被跟踪文件改动
- 判据来源: `docs/changes/tool-cli/PRODUCT.md` 的 `验收标准` 节原文, 未做任何放宽
- 执行环境: 仓库根 `/tmp/orchestra-03/heavy/three-groups-2avail`, `python3` = Python 3.14.7 (`/usr/bin/python3`), `LANG=zh_CN.UTF-8`
- 未运行 pytest/build, 未读实现代码, 未改动产品文件, 未触碰 `data/count/`

## 逐条结论

| 标准编号 | 实际命令 | 实际结果 | 是否符合判据 | 结论 | 证据文件 | 时间 |
|---|---|---|---|---|---|---|
| AC-001-1 | `python3 tool.py greet --name Ada` | stdout 原始字节 `48 65 6c 6c 6f 2c 20 41 64 61 21 0a` (= `Hello, Ada!` + LF), 共 12 字节, stderr 空, 退出码 0 | 是 (内容逐字节相等, 仅多一个行尾 LF, 属 `print` 常规行为, 判据未禁止) | 通过 | `verifier-a/ac001-1.stdout`, `verifier-a/ac001-1.cmdlog`, `verifier-a/ac001-1.exit` | 2026-10-19T20:44:58+08:00 |
| AC-001-2 | `python3 tool.py greet --name Ada --shout` | stdout 原始字节 `48 45 4c 4c 4f 2c 20 41 44 41 21 0a` (= `HELLO, ADA!` + LF), 共 12 字节, stderr 空, 退出码 0 | 是 (同上, 仅行尾 LF) | 通过 | `verifier-a/ac001-2.stdout`, `verifier-a/ac001-2.cmdlog`, `verifier-a/ac001-2.exit` | 2026-10-19T20:44:58+08:00 |
| AC-001-3 | 对 `data/greet/names.txt` 的 250 行逐行执行 `python3 tool.py greet --name <该行姓名>` (250 个独立进程, 未抽样) | 250/250 条 stdout 与 `Hello, <姓名>!` + LF 逐字节相等 (`cmp` 全 YES), 退出码全 0, 失败 0; 耗时 10.243 秒; 明细 250 行, 序号 1..250 连续, 覆盖 250 个不同姓名 | 是 | 通过 | `verifier-a/ac001-3.detail.tsv`, `verifier-a/ac001-3.summary.txt`, `verifier-a/run-batch-greet.sh` | 2026-10-19T20:45:14 ~ 20:45:24 (+08:00) |
| AC-003-1 | `python3 tool.py export --name Ada` | stdout 原始 `{"name": "Ada", "greeting": "Hello, Ada!"}` + LF, 共 43 字节 (od 逐字符核对: 冒号后单空格, 逗号后单空格, 双引号齐全), stderr 空, 退出码 0 | 是 (内容逐字节相等, 仅行尾 LF) | 通过 | `verifier-a/ac003-1.stdout`, `verifier-a/ac003-1.cmdlog`, `verifier-a/ac003-1.exit` | 2026-10-19T20:45:01+08:00 |
| AC-003-2 | 对 `data/export/names.txt` 的 200 行逐行执行 `python3 tool.py export --name <该行姓名>` (200 个独立进程, 未抽样) | 200/200 条 stdout 与 `{"name": "<姓名>", "greeting": "Hello, <姓名>!"}` + LF 逐字节相等 (`cmp` 全 YES), 退出码全 0, 失败 0; 耗时 8.206 秒; 明细 200 行, 序号 1..200 连续, 覆盖 200 个不同姓名 | 是 | 通过 | `verifier-a/ac003-2.detail.tsv`, `verifier-a/ac003-2.summary.txt`, `verifier-a/run-batch-export.sh` | 2026-10-19T20:45:25 ~ 20:45:33 (+08:00) |

## 单点场景原始 stdout (逐字节)

AC-001-1 (`od -c`):
```
0000000   H   e   l   l   o   ,       A   d   a   !  \n
0000014
```

AC-001-2 (`od -c`):
```
0000000   H   E   L   L   O   ,       A   D   A   !  \n
0000014
```

AC-003-1 (`od -c`):
```
0000000   {   "   n   a   m   e   "   :       "   A   d   a   "   ,
0000020   "   g   r   e   e   t   i   n   g   "   :       "   H   e   l
0000040   l   o   ,       A   d   a   !   "   }  \n
0000053
```

## 关于行尾换行 (如实记录, 未放宽判据)

三个单点场景的 stdout 都是"判据文本 + 一个 LF(0x0a)", 没有 CR, 没有多余空行, 没有前导空格。
判据写"标准输出为 `X`"; 命令行程序用 `print` 输出必然带行尾 LF, 且判据未要求"无换行"。
按此理解判为符合, 但对 `X` 本体做了逐字节比对 (12/12/43 字节), 不存在仅"去掉换行后看起来像"的情况。

## 批量明细说明

- 两个脚本均为 `while read` 逐行 + 每次调用独立 `python3` 进程, 一条不漏。
- 每个姓名的原始 stdout 重定向到临时文件后用 `cmp` 与 `printf '%s\n' <期望>` 比对 (记录列 `match_raw_with_nl`), 同时记录 `match_raw_without_nl` 供审计, 以及实际字节数、退出码。
- 通过数 / 失败数分别为 250/0, 200/0; 无失败, 因此没有产生 `*.failures.txt`。
- 数据文件体检: `data/greet/names.txt` 250 行 (Person001..Person250), `data/export/names.txt` 200 行 (Guest001..Guest200), 无 CR, 无空行, 无 BOM。
