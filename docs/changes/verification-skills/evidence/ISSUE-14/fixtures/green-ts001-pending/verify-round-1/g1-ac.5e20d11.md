# G1 验收结论: 运行行为 (AC-001-1, AC-002-1) @ 5e20d11

## 会话标识

- agent 名: g1 (派工单 G1, 独立验收者 1, 未参加本次实现与修复)
- 窗格/会话 ID: herdr 工作区 `w1E` / 标签 `w1E:t3R` / 窗格 `w1E:p3R`; pi session `01a15551-4c3e-735d-b1c5-54a2a53a51a5`
- 工作目录: `/tmp/orchestra-14/ts001-review-pending` (分支 `main`)

## 时间

- 开始: `2026-10-20T01:59:27+08:00` (首次 `date -Is`), 日志内记录 begin_time `2026-10-20T01:59:53+08:00`
- 结束: `2026-10-20T01:59:57+08:00`
- 日志内 end_time: `2026-10-20T01:59:53+08:00` (命令全部在同一秒窗口内跑完)

## 目标提交核对

`git rev-parse HEAD` 实际输出:

```
5e20d11c94bfbab1ebd037ac95d9e1ccacfebdb4
```

与派工单目标提交一致, 分支 `main`。执行前 `git status --porcelain` 仅有一条 `?? docs/changes/wordcount/verify/` (证据目录本身, 未跟踪), 无其它改动。

## 判定结果表

### AC-001-1 统计标准输入词数 (G-001)

| 项 | 内容 |
| --- | --- |
| 标准编号 | AC-001-1 |
| 材料类型 | 当前观察 |
| 实际操作 | `printf 'alpha beta gamma\n' | bin/wordcount` (由 `eval` 执行, 命令字符串与日志回显同一份) |
| 实际结果 | stdout 原文: `3` (逐字节 `0000000   3  \n`, 即仅 "3" 加一个换行); 退出码 `0`; stderr 为空 (丢弃 stderr 后 stdout 仍为 `3`) |
| 证据位置 | `g1-ac.5e20d11.log` 第 39-42 行 (主执行), 第 45-49 行 (od -c 逐字节), 第 52-55 行 (stderr 分离) |
| 时间 | `2026-10-20T01:59:53+08:00` |
| 结论 | 通过 |

判据比对: 期望 `输出为 3, 退出码为 0`; 实测 stdout 就是 `3`, 退出码 `0`, 一致。

### AC-002-1 统计文件词数 (G-002)

| 项 | 内容 |
| --- | --- |
| 标准编号 | AC-002-1 |
| 材料类型 | 当前观察 |
| 实际操作 | `bin/wordcount --file samples/notes.txt` |
| 实际结果 | stdout 原文: `2` (逐字节 `0000000   2  \n`); 退出码 `0`; stderr 为空 (丢弃 stderr 后 stdout 仍为 `2`) |
| 证据位置 | `g1-ac.5e20d11.log` 第 29-32 行 (`od -c samples/notes.txt` 证明前提: `alpha beta` 加一个换行, 共 11 字节), 第 63-66 行 (主执行), 第 69-73 行 (od -c 逐字节), 第 76-79 行 (stderr 分离) |
| 时间 | `2026-10-20T01:59:53+08:00` |
| 结论 | 通过 |

判据比对: 前提成立 (`samples/notes.txt` 为 `alpha beta\n`); 期望 `输出为 2, 退出码为 0`; 实测 stdout 就是 `2`, 退出码 `0`, 一致。

## 补充观察 (不参与判定)

README 登记的两条测试命令, 原样执行结果:

- `sh tests/run.sh` -> stdout `ok`, 退出码 `0` (日志第 86-88 行)
- `sh tests/cli_errors_test.sh` -> 30 条 `ok` 加末尾 `ok`, 退出码 `0` (日志第 91-123 行)

说明: `tests/cli_errors_test.sh` 内部自己用 `mktemp` 建临时文件并 `trap` 清理, 这是被执行的测试脚本自身行为, 不是我为构造场景在仓库外建的临时文件。

## 声明

本次验收全程只读: 我没有修改任何产品代码, 测试, `PRODUCT.md`, `EXECUTION.md`, `.agents/`, 未执行任何 `git add/commit/push/merge/checkout/restore`; 唯一写入是证据目录内新增 `g1-ac.5e20d11.md` 与 `g1-ac.5e20d11.log` 两个文件。收尾时 `git status --porcelain` 仍只有 `?? docs/changes/wordcount/verify/`, `git rev-parse HEAD` 仍是 `5e20d11c94bfbab1ebd037ac95d9e1ccacfebdb4` (日志第 126-135 行)。

## 未验证项

无。两条 AC 都按 PRODUCT.md 原文命令实跑并比对过实际 stdout 与退出码。

RESULT: AC-001-1=通过 AC-002-1=通过
