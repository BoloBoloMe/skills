# 00 环境与口径 (验收者 A)

## 待核验的对外结论 (先写结论, 后测量)

"在 2 万行导出 (`python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data`) 上, 连续 5 次运行的 p50 为 74.149 ms, 极差 5.420 ms, 不超过 AC-001-1 的 800ms 上限."

单位: 毫秒 (ms), 端到端墙钟, 见下节计时范围.

## 目标版本

- 目标提交: `ea940821115424b7eb619e985b2304f2b61e9d1d` (`fixture: 事件仓初始版本`)
- 开工核对 (2026-10-20T00:19:26+08:00):
  ```
  $ git -C /tmp/orchestra-10/methods-red rev-parse HEAD
  ea940821115424b7eb619e985b2304f2b61e9d1d
  ```
  与派工单给定 hash 一致.

## 开工前工作区状态

```
$ git -C /tmp/orchestra-10/methods-red status --porcelain --untracked-files=all
?? docs/changes/vault/evidence/r1-ea94082/PLAN.md
?? docs/changes/vault/evidence/r1-ea94082/TASK-A.md
?? docs/changes/vault/evidence/r1-ea94082/TASK-B.md
```

开工时只有本轮派工与计划文件未跟踪, 产品文件 (`app.py`, `seed/`, `README.md`, `docs/changes/vault/PRODUCT.md`) 均无改动 (无 `M` 项). 本次验收全程未修改产品文件; 只在 `runtime/` 与本证据目录写入.

## 解释器

派工单给的项目入口命令形态为 `python3 app.py <子命令> ...` (README 同). 本机 shell 里 `python3` 被 harness 定义成 shell 函数, 实际落到 uv 管理的 CPython:

```
$ python3 -c 'import sys; print(sys.executable)'
/home/bolo/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14
$ python3 -VV
Python 3.14.7 (main, Aug 14 2026, 15:35:28) [Clang 22.1.3 ]
$ uv run python -VV
Python 3.14.7 (main, Aug 14 2026, 15:35:28) [Clang 22.1.3 ]
/home/bolo/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14
```

即: 本 shell 中的 `python3` 与项目约定 `uv run python` 指向同一个解释器 (CPython 3.14.7, uv 管理). 计时采用**逐字命令** `python3 app.py export ...`, 因此结果同时满足"README/AC 的命令形态"和"本机 uv python 约定".

另注: 系统解释器 `/usr/bin/python3` 是 CPython 3.14.4 (GCC 15.2.0), 与本 shell 的 `python3` 不是同一个二进制; 为证明解释器选择不影响判定, 追加 1 次 `/usr/bin/python3` 的对照运行 (标注为对照, 不计入 5 次序列与 p50).

## 机器条件

```
$ nproc
16
$ uptime            # 2026-10-20T00:19:26+08:00
 00:19:26 up 34 days, 10:30,  3 users,  load average: 0.29, 0.17, 0.11
```

16 核, 1 分钟负载 0.29, 机器基本空闲. 计时开始时将再记一次 `uptime` (见 `01-export-perf.md`).

## 计时手段与计时范围

- 计时手段: shell 内嵌时间戳 (`date +%s%N`, 纳秒) 包住被执行的命令, 用整数纳秒差算墙钟; 另用 `/usr/bin/time -f` 对 1 次运行做交叉校验. 不新增产品内计时代码, 不改产品源码.
- 计时范围 (包含): 从调用 `python3 app.py export ...` 起, 到该进程退出并回到 shell 为止. 覆盖 Python 解释器启动, 模块导入, argparse 解析, 20000 行 JSON 序列化与写入 `runtime/export.jsonl`, 关闭文件 (含 flush), 打印 `export-ok`, 进程退出.
- 计时范围 (不包含): 计时用 `date` 子进程自身开销 (时间戳在命令前后各取一次, 约 1-3ms 级别, 不摊入被测命令); 预热/清缓存动作 (本场景不要求清页缓存, 数据目录只被读取, 导出文件每次覆盖写); 后续核对 (`wc -l`, 抽样) 的时间.
- 环境变量: 未设置 `PARTNER_URL` 等会影响代码路径的变量; export 子命令路径不读取环境变量.
- 数据与随机性: `--rows 20000` 固定, 输出路径固定, 无随机种子/无随机扰动. 每次运行前不删除 export 文件, 允许覆盖写 (与 AC 文字一致).

## 5 次运行的口径

- 连续 5 次, 每次完整命令逐字为:
  `python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data`
- 每次单独落盘 stdout / stderr / 退出码到 `02-raw/`, 见 `01-export-perf.md`.
- p50 取 5 个数值的中位数 (第 3 小); 极差 = max - min.
