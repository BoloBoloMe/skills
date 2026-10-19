# 独立产品验收报告 (round 1)

- 目标提交: `cd087542b4610c49ded0a1278fe8065726b62d9d` (HEAD)
- 上一提交: `8438934fc81b67ed518dc4ad2e2f7dbd83b0192a`
- 判据来源: `docs/changes/relay-board/PRODUCT.md` (验收标准 `confirmed-flow: v1`, 以及业务规则 `BR-001 (审计)`)
- 证据目录: `docs/changes/relay-board/evidence/v1-cd08754/`
- 验收时间: 2026-10-19 22:23 - 22:25 (+08:00)
- 报告性质: 独立产品验收汇总, 不是正式人工验收, 也不宣布正式交付.

## 1. 版本前提

| 检查 | 结果 |
| --- | --- |
| 目标提交存在且为 HEAD | `git rev-parse HEAD` = `cd087542b4610c49ded0a1278fe8065726b62d9d` |
| 起始工作区与目标提交一致 | 验收开始前 `git status --porcelain --untracked-files=all` 为空; 无已跟踪改动, 无未跟踪产品文件 |
| 元数据 | 提交时间 2026-10-19 21:18:27 +0800, 作者 luojingyan |
| 验收后产品改动 | `git diff --stat` 为空; HEAD 未变; 唯一新增为本次证据目录下的未跟踪文件 |

## 2. 结论摘要

| 项 | 数量 |
| --- | --- |
| 必验项总数 | 5 (4 个验收场景 + 1 条审计 BR) |
| 通过 | 4 |
| 失败 | 1 |
| 未验证 | 0 |

**整体结论: 不通过.** 失败项为 `AC-003-1`, 其余 3 个场景与 `BR-001` 通过. 失败原因见第 3 节.

## 3. 逐项结果

| 编号 | 材料类型 | 实际操作或引用信息 | 实际结果 | 证据位置 | 时间/版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 当前观察 (本轮实跑 + 截图原件) | 实例 alpha 于 127.0.0.1:18101 启动一次, health 返回 `ok instance=alpha` (退出码 0); `google-chrome --headless --disable-gpu --no-sandbox --window-size=900,400 --screenshot=<ev>/ac001-status-page.png http://127.0.0.1:18101/status-page` 退出码 0, 写出 8788 字节 png | 截图可见 `relay board` 标题与 `instance=alpha`, `state=ready`, `version=relay-v1` 三行文本 | `evidence/v1-cd08754/runtime-AC/ac001-status-page.png`, `03-ac001-chrome.txt`, `02-health.txt` | 2026-10-19T22:23:55+08:00, cd08754 | 通过 |
| AC-002-1 | 当前观察 (本轮实跑) | `python3 app.py job --port 18101 --ms 2500` | stdout 为 `job-done instance=alpha elapsed_ms=2500`; 退出码 0; 同一命令的 job-start/job-end 均写入 events.log | `evidence/v1-cd08754/runtime-AC/04-ac002-job.txt` | 2026-10-19T22:23:59 至 22:24:01, cd08754 | 通过 |
| AC-003-1 | 当前观察 (本轮实跑) | health 前置 `ok instance=alpha`; `python3 app.py report --port 18101` | 实际 stdout 为 `relay-report instance=alpha version=relay-v1 state=loading`, 期望 `state=ready`; 退出码 0; 相隔 3 秒连跑 3 次并直接 `curl http://127.0.0.1:18101/report`, 四次全部 `state=loading`, 非偶发 | `evidence/v1-cd08754/runtime-AC/05-ac003-report.txt`, `07-ac003-report-repeat.txt` | 2026-10-19T22:24:03 (复跑 22:24:08, 22:24:11), cd08754 | 失败 |
| AC-004-1 | 当前观察 (本轮实跑) | 在 AC-002 的 job 完成后执行 `python3 app.py log --port 18101` | 输出两行, 均含 `instance=alpha`, 其中一行含 `event=job-end`; grep 计数 instance=alpha=2, event=job-end=1; 退出码 0 | `evidence/v1-cd08754/runtime-AC/06-ac004-log.txt`, `runtime-shared-events.log.snapshot` | 2026-10-19T22:24:06, cd08754 | 通过 |
| BR-001 | 静态材料核对 (不是运行行为) | `git diff 8438934 cd08754 -- deps.txt` 空输出且退出码 0; 两侧 deps.txt 同为 git blob `ff2c99947923198db10083beab39cf783c26e9b0`; `git diff --name-status` 仅 `M app.py`; app.py 全部 import 经 `sys.stdlib_module_names` 与 `find_spec` 核对均在标准库; 仓库无 requirements/pyproject/setup/lock/build 依赖材料 | deps.txt 逐项一致, 本次变更只改 app.py 且无新增文件, 未新增第三方依赖 | `evidence/v1-cd08754/audit-BR-001/REPORT.md` 第 3, 4, 5, 8 节 | 命令时间 2026-10-19T22:23:53+08:00 起, 版本区间 8438934..cd08754 | 通过 (静态材料核对结果) |

### AC-003-1 失败细节

- 判据原文 (PRODUCT.md): 输出为 `relay-report instance=alpha version=relay-v1 state=ready` 且退出码为 0.
- 实际: `relay-report instance=alpha version=relay-v1 state=loading`, 退出码 0.
- 字节级对照 (见 `05-ac003-report.txt`): 前缀一致, 末段 `state=loading\n` 与期望 `state=ready\n` 不同.
- 同一实例的状态页截图显示 `state=ready`, 与 report 的 `state=loading` 矛盾; 这与目标 G-003 "report 中的状态反映实例当前状态" 冲突. 失败项是产品行为不符判据, 不是环境或权限缺口.
- 验收者未修复该缺陷, 只如实记录失败.

## 4. 材料与证据复核

- 所有 5 项材料均为本轮新产生的当前观察或本轮静态核对结果, 没有引用上一轮或旧提交的观察, 没有用推断或未运行顶替.
- 指挥者复核了截图原件 (`ac001-status-page.png`), 可见 `instance=alpha`, `state=ready`, `version=relay-v1`; 复核了各场景原始输出文件, 命令与退出码齐全.
- `AC-003-1` 的失败有三次重复命令与一次 raw HTTP 输出, 材料之间一致, 不是单次偶发.
- 材料更正记录:
  - 组 2 初版 REPORT.md 把首条 `date -Is` 命令时间写成"会话启动时间"; 经核对原生 pi 会话文件, 已要求组 2 更正为会话文件创建时间 2026-10-19T22:23:19+08:00, 并保留 22:23:53 作为首条命令时间. 结论 (通过) 未变.
  - 组 1 初版 REPORT.md 写"解释器为 python3 (未用 uv)"; 经核对本机 `python-operation-hook`, 已要求更正为命令文本仍为 PRODUCT.md 原文 `python3 app.py ...`, 但 shell 层透明替换为 `uv run python`, 实际解释器为 uv 管理 CPython 3.14.7. 四场景输出与结论未变.
- 本机环境: Google Chrome 154.0.8037.97; CPython 3.14.7 (uv 管理); 端口 18101 仅本项目使用; 服务在验收后已停止, 端口无监听.

## 5. 派工记录

### 5.1 分组与人数依据

- 当轮可用非作者验收者 2 名; 计划 2 名.
- 组 1: 运行场景 AC-001-1, AC-002-1, AC-003-1, AC-004-1, 1 人.
- 组 2: 静态依赖审计 BR-001, 1 人.
- 不按 AC 逐条开会话, 不开第三会话.
- 组 1 不拆理由: 四条场景争用同一实例 alpha, 同一端口 18101, 同一 `runtime/alpha` 与 `runtime/shared`; 本轮禁止为并行加实例或扩端口; 单个场景工作量不值得单开会话.
- 组 2 并行理由: 只读 git/文件, 不占用实例, 端口与 runtime/, 无需共用准备, 与组 1 完全隔离; 同时让 BR-001 由未参与实现的会话独立核对, 不取实现方自证.
- 共用准备: 实例只由组 1 启动一次 (22:23:49), health 确认 (22:23:53), 结束 kill (22:24:14); 组 2 不需要实例, 未重复准备.
- 争用与先后: 组 1 内 AC-002 (写 `runtime/shared/events.log`) 先于 AC-004 (只读同一日志), 依据 AC-004 的"假定耗时任务已经执行"; 组 2 与组 1 无共用资源, 无先后约束.
- 原始材料归属: 组 1 的命令输出, 截图, runtime 日志归 `i04-a1-ac`; 组 2 的比对命令与输出归 `i04-a1-br`; 双方各自下自己的结论. 本轮无跨组共享材料.
- 详细计划原件: `evidence/v1-cd08754/PLAN.md`.

### 5.2 验收者身份与未参与事实

| 组 | 验收者 (Herdr 名) | 窗格/标签 | pi 会话标识 | 会话文件创建时间 | 承接标准 | 模型与档位 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `i04-a1-ac` | `w1J:p5C` / `w1J:t5A` | `01a1548b-b975-7213-9d28-db1121880578` | 2026-10-19T22:23:25+08:00 | AC-001-1, AC-002-1, AC-003-1, AC-004-1 | `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high` |
| 2 | `i04-a1-br` | `w1J:p5B` / `w1J:t59` | `01a1548b-a33f-7791-ba88-2ec069ae42e4` | 2026-10-19T22:23:19+08:00 | BR-001 | `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high` |

未参与本次实现与修复的可核对事实:

- 两个会话均为本轮新开: 会话文件首行为新建 `type=session` 记录, 首条 model_change 的 parentId 为 null, 启动参数无 `--continue`/`--fork`; 创建时间 22:23:19 与 22:23:25 均晚于目标提交时间 21:18:27.
- 会话记录中没有任何 `edit` 工具调用; 各只有 1 次 `write`, 目标分别是 `evidence/v1-cd08754/audit-BR-001/REPORT.md` 与 `evidence/v1-cd08754/runtime-AC/REPORT.md`.
- 验收后 `git diff --stat` 为空, HEAD 仍为 cd08754; 已跟踪产品文件 (app.py, deps.txt, tests/, PRODUCT.md) 未变.
- 独立性以原生会话文件, 工具调用记录和 git 状态为证, 不采信验收者自述本身.

### 5.3 执行时间与顺序

| 组 | 开始 (首条命令) | 结束 (会话最后记录) | 说明 |
| --- | --- | --- | --- |
| 1 `i04-a1-ac` | 2026-10-19T22:23:48+08:00 | 2026-10-19T22:25:12+08:00 | 实例 22:23:49 启动, 22:24:14 停止; 场景顺序 health -> AC-001 -> AC-002 -> AC-003 -> AC-004 -> AC-003 复跑 |
| 2 `i04-a1-br` | 2026-10-19T22:23:53+08:00 | 2026-10-19T22:25:12+08:00 | 与组 1 并行, 只读 git 与文件 |

- 组 1 内部写入/读取顺序记录: AC-002 的 job 于 22:24:01 写入 job-end, AC-004 于 22:24:06 读取到 `event=job-end`; 执行者均为 `i04-a1-ac`, 依据 `PLAN.md` 的争用说明.
- 组 2 无写入产品文件, 无争用片段.

### 5.4 共享材料

- 本轮无跨验收者共享的原始材料; 两组各自产生, 各自引用.
- 指挥者只读取原件做复核, 不代替验收者下单条结论, 不补跑产品.

## 6. 覆盖范围与非产品判据

- 覆盖范围: PRODUCT.md `验收标准` 的全部 4 个场景与 `业务规则` 中唯一标 `(审计)` 的 BR-001, 共 5 项, 无遗漏.
- 目标提交 cd08754 新增的共享记录 (`/record`, `/append`) 在 PRODUCT.md 中没有对应验收场景或审计规则, 本轮不作为产品判据, 也不据此给出通过或失败.
- `README.md` 的 pytest 命令与 `tests/test_app.py` 属于运行线索, 不是 PRODUCT.md 的产品通过条件; 本轮未把测试结果当作场景结论, 也不对内部代码划分, 模块拆分做技术评审.
- `BR-001` 的结论是静态材料核对结果, 不是运行行为结果.

## 7. 收尾

- 除本次证据目录 (`docs/changes/relay-board/evidence/v1-cd08754/`) 的输出外, 源码与 Spec 未变; 已跟踪文件相对起始提交无改动, 证据目录中的未跟踪文件是本轮验收留下的预期产物.
- `runtime/` 为 gitignore 目录: 本轮服务在 `runtime/shared/events.log` 留下事件日志, 已停止服务, 端口 18101 无监听.
- 本轮验收会话按调用方要求保留 (指挥会话与 `i04-a1-ac`, `i04-a1-br`), 未关闭, 供后续复验使用.
- 本报告结论仍需用户逐项确认, 并走正式人工验收; 不宣布正式交付或关闭用户验收.
