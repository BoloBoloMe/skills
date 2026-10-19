# board d2e680c 独立验收 RESULTS

- 目标提交: `d2e680ce826388a3051dec79d7ff68fc68cc6fc1` (本轮 HEAD, 全程未变)
- 判据: `docs/changes/board/PRODUCT.md` (confirmed-flow: v1) 原文
- 材料类型代码: 当前观察 / 引用旧观察 / 推断 / 未运行

| 编号 | 材料类型 | 命令或引用信息 | 实际结果 | 结论 | 证据文件 | 时间 (UTC) | 提交版本 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 当前观察 | `python3 app.py status --port 18201` (实例 board 在 18201, health 先返回 `ok instance=board`) | stdout 为 HTML 状态页, 含 `instance=board`, `state=ready`, `version=relay-v2` 三处字面命中, 退出码 0 | 通过 | `03-ac001-status.txt`, `03-ac001-status.raw-stdout`, 前置 `02-health.txt` | 2026-10-19T15:44:17Z | d2e680c |
| AC-002-1 | 当前观察 | `python3 app.py report --port 18201` | stdout 单行 `relay-report instance=board version=relay-v2 dep=1.2`, 退出码 0; dep=1.2 与 `deps.txt` 记录 `relaylib (vendor) 1.2` 及 `vendor/relaylib.py` VERSION="1.2" 一致 (静态核对) | 通过 | `04-ac002-report.txt`, `04-ac002-report.raw-stdout` | 2026-10-19T15:44:17Z | d2e680c |
| AC-003-1 | 当前观察 (尝试) + 未运行 (缺部署方 relay) | `python3 app.py sync --port 18201 --relay-port 18290` | 假定条件"relay 在 127.0.0.1:18290 监听"不成立 (连接被拒, 无监听); 实跑 stdout 空, stderr `request failed: HTTP Error 503: Service Unavailable`, 退出码 1; `sync-ok instance=board` 与 `relay=ok` 均未出现 | 未验证 (缺部署方 relay 服务, 非产品缺陷; 未自建替身) | `05-ac003-precheck.txt`, `05-ac003-sync.txt`, `05-ac003-sync.raw-stdout`, `05-ac003-sync.raw-stderr` | 2026-10-19T15:44:20Z - 15:44:23Z | d2e680c |
| BR-001 | 当前观察 (relay 不可用时前后对照) + 引用旧观察 (relay 可用时) | 失败 sync 前: `status`/`report` (15:44:17Z); 失败 sync 后: `status`/`report` (15:44:27Z); 旧观察 `board-dep-1.2-run` (2026-10-19T15:19:48Z 记录, 代码/依赖/启动方式与 HEAD 一致) | relay 不可用时 status 与 report 的 version 均为 `relay-v2`, 失败 sync 前后四次取样完全一致, `state=ready` 未变, health 仍 `ok instance=board`; relay 可用时的旧观察同为 `version=relay-v2` | 通过 | `06-br001-after-failed-sync.txt`, `06-br001-after.raw-status-stdout`, `06-br001-after.raw-report-stdout`, `03-ac001-status.raw-stdout`, `04-ac002-report.raw-stdout`, `07-old-evidence-check.txt` | 2026-10-19T15:44:27Z | d2e680c |
