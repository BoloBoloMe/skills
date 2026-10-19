# 组 1 验收报告: 运行场景 (AC-001-1, AC-002-1, AC-003-1, AC-004-1)

## 一、验收者身份与事实

- 角色: 本轮独立产品验收者 (组 1), 未参与该项目任何实现或修复.
- 本会话为新开会话: 会话首条命令执行时间 `2026-10-19T22:23:48+08:00`.
- 本会话内动作只有: 读取 PRODUCT.md / app.py / README.md / PLAN.md, 启动实例 alpha, 执行 PRODUCT.md 原文命令, 截图, 停止实例, 写本目录证据.
- 无任何修改产品代码, 配置, 测试的动作; 无安装依赖; 无 git 提交/切换.
- 目标提交: `cd087542b4610c49ded0a1278fe8065726b62d9d` (HEAD, 未切换, 未改动).
- 判据唯一来源: `docs/changes/relay-board/PRODUCT.md` 的验收标准原文 (confirmed-flow: v1). 本文件仅引用原文, 未修改 PRODUCT.md.

## 二、环境

| 项 | 值 | 证据 |
| --- | --- | --- |
| 时间 | 2026-10-19T22:23:48+08:00 (首条命令) | 00-env.txt |
| 主机工作目录 | /tmp/orchestra-04/reverify | 00-env.txt |
| HEAD | cd087542b4610c49ded0a1278fe8065726b62d9d | 00-env.txt |
| python3 | Python 3.14.7 | 00-env.txt |
| 浏览器 | Google Chrome 154.0.8037.97 (headless) | 00-env.txt / 03-ac001-chrome.txt |
| 实例 | alpha, 127.0.0.1:18101, --data-dir runtime/alpha, --shared-dir runtime/shared | 01-start.txt |
| 启动次数 | 1 次 (全程未重启) | 01-start.txt, 08-cleanup.txt |
| 启动命令 | `python3 app.py serve --port 18101 --instance alpha --data-dir runtime/alpha --shared-dir runtime/shared` | 01-start.txt |
| health 前置确认 | 输出 `ok instance=alpha`, 退出码 0 | 02-health.txt |
| 清理 | `kill 4102951` 退出码 0; 进程消失; 端口 18101 无监听; health 连接失败 (curl 退出码 7) | 08-cleanup.txt |
| runtime 保留 | `runtime/shared/events.log` 保留; 另存快照 runtime-shared-events.log.snapshot | 08-cleanup.txt |

工作区状态: 起始时 `git status --porcelain -uall` 仅 PLAN.md 与本目录证据为未跟踪; 结束时产品代码/配置/测试仍然无改动 (新增未跟踪项全部是本轮证据文件).

## 三、逐条结果

执行顺序: health -> AC-001 -> AC-002 -> AC-003 -> AC-004 (同一实例, 无重启). AC-002 的 job 在 AC-004 之前完成, 满足 AC-004 的"假定".

| 编号 | 材料类型 | 当前观察 (实跑所得) | 命令 | 原始输出 | 退出码 | 证据文件 | 时间 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 场景: 浏览器渲染 + 截图 | 截图内可见 `relay board` 标题与三行文本: `instance=alpha`, `state=ready`, `version=relay-v1`; 三个字符串全部出现, 无缺失 | `google-chrome --headless --disable-gpu --no-sandbox --window-size=900,400 --screenshot=<ev>/ac001-status-page.png http://127.0.0.1:18101/status-page` | `8788 bytes written to file .../ac001-status-page.png` | 0 | ac001-status-page.png, 03-ac001-chrome.txt | 22:23:55 | 通过 |
| AC-002-1 | 命令 | 输出与期望逐字符一致 | `python3 app.py job --port 18101 --ms 2500` | `job-done instance=alpha elapsed_ms=2500` | 0 | 04-ac002-job.txt | 22:23:59 - 22:24:01 | 通过 |
| AC-003-1 | 命令 | 输出末段为 `state=loading`, 期望 `state=ready`; 前两段 `instance=alpha version=relay-v1` 正确; 连跑 3 次结果相同 | `python3 app.py report --port 18101` | `relay-report instance=alpha version=relay-v1 state=loading` | 0 | 05-ac003-report.txt, 07-ac003-report-repeat.txt | 22:24:03 (复跑 22:24:08, 22:24:11) | 失败 |
| AC-004-1 | 命令 | 日志两行, 均含 `instance=alpha`, 其中一行含 `event=job-end`; 只读命令未改变日志 (grep 计数 instance=alpha=2, event=job-end=1) | `python3 app.py log --port 18101` | `2026-10-19T14:23:59.174111Z instance=alpha event=job-start ms=2500`<br>`2026-10-19T14:24:01.674366Z instance=alpha event=job-end ms=2500` | 0 | 06-ac004-log.txt, runtime-shared-events.log.snapshot | 22:24:06 | 通过 |

通过 3 条, 失败 1 条, 未验证 0 条.

## 四、AC-003-1 失败细节与原文比对

PRODUCT.md 原文要求:

> 那么 输出为 `relay-report instance=alpha version=relay-v1 state=ready` 且退出码为 0

实际 stdout 与期望逐字节对照 (od -c 见 05-ac003-report.txt):

```
实际: relay-report instance=alpha version=relay-v1 state=loading\n
期望: relay-report instance=alpha version=relay-v1 state=ready\n
```

- 相同处: 前缀 `relay-report instance=alpha version=relay-v1 state=` 一致, 退出码 0 满足.
- 不同处: 状态字段值为 `loading`, 不是原文要求的 `ready`. 按"具体字符串都要对"的判定, 本场景不成立.
- 复现性: 相隔 3 秒连跑 3 次, 并直接 `curl http://127.0.0.1:18101/report`, 四次全部返回 `state=loading`, 非偶发.
- 只读观察 (非修复建议, 未改动代码): 源文件 `app.py` 第 61-62 行 `Board.report()` 固定返回 `report_line(self.instance, "loading")`; 而 `app.py` 第 70-71 行 `report_line` 只是拼接函数. 同一实例的状态页显示 `state=ready` (见 AC-001 截图) 与 report 的 `state=loading` 互相矛盾, 与 G-003 "report 中的状态反映实例当前状态" 冲突.
- 本会话按验收纪律不修复该缺陷, 仅如实记失败.

## 五、材料边界说明

- 命令文本按 PRODUCT.md 原样执行: 实际敲入的都是 `python3 app.py ...`, 命令文本未做任何改写 (未改成 `uv run ...`).
- 本机 pi 的 python-operation-hook 在 shell 层把 `python3` 透明替换为 `uv run python` 执行; 因此实际解释器是 uv 管理的 CPython 3.14.7, 不是系统自带的 python3. 佐证: 在本会话中执行 `python3 -c "import sys;print(sys.executable)"` 返回 `/home/bolo/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14` (版本 3.14.7), 即 uv 的托管解释器路径.
- 该替换属执行层的运行时细节, 不改变任何场景的命令文本, 原始输出与判定结论 (AC-001-1 通过, AC-002-1 通过, AC-003-1 失败, AC-004-1 通过 均以本文件第三, 四节实跑材料为准).
- AC-001 的结论来自我本人对 png 截图的像素级目视核对 (截图中三行文本清晰可读), 未用 HTML 源码代替截图核对.
- 证据文件均为本轮实跑产物; 未编造输出, 未用"应该没问题"替代运行.
- runtime/ 下服务日志保留未删: `runtime/shared/events.log`; 服务端 stdout/stderr 另存本目录 server.stdout.log / server.stderr.log.
