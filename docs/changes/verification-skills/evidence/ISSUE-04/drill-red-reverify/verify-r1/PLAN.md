# 独立验收派工计划 (verify-r1)

- 目标提交: cd087542b4610c49ded0a1278fe8065726b62d9d (HEAD)
- 判据来源: docs/changes/relay-board/PRODUCT.md, `验收标准` 节 (确认标记 `<!-- confirmed-flow: v1 -->`)
- 产物根目录: docs/changes/relay-board/
- 本轮证据目录: docs/changes/relay-board/verify-r1/ (新目录, 不覆盖旧证据)

## 必验清单 (来自 PRODUCT.md 原文, 共 5 项)

| 编号 | 类型 | 原文要点 |
| --- | --- | --- |
| AC-001 (场景 AC-001-1) | 场景 | 实例 alpha 在 127.0.0.1:18101 运行且 health 返回 `ok instance=alpha`; 浏览器渲染 `/status-page` 并截图; 截图显示 `instance=alpha`, `state=ready`, `version=relay-v1` |
| AC-002 (场景 AC-002-1) | 场景 | `python3 app.py job --port 18101 --ms 2500` 输出 `job-done instance=alpha elapsed_ms=2500`, 退出码 0 |
| AC-003 (场景 AC-003-1) | 场景 | `python3 app.py report --port 18101` 输出 `relay-report instance=alpha version=relay-v1 state=ready`, 退出码 0 |
| AC-004 (场景 AC-004-1) | 场景 | 耗时任务已执行后 `python3 app.py log --port 18101` 输出含 `instance=alpha` 与 `event=job-end`, 退出码 0 |
| BR-001 | 业务规则 (审计) | 本次变更不新增第三方依赖, `deps.txt` 与上一提交逐项一致 |

清单条数 = 场景 4 条 + 审计 BR 1 条 = 5, 与原文一致.

## 场景组划分

| 组 | 承接标准 | 工具链 | 资源 |
| --- | --- | --- | --- |
| G-A | AC-001, BR-001 | 无头浏览器截图 + 渲染结果读图; 静态 git 逐提交比对 | 只读消费 18101 上的实例; 静态比对不需要端口 |
| G-B | AC-002, AC-003, AC-004 | HTTP 客户端命令 + 实例生命周期管理 | 独占 18101 上的实例 (启动/保持/最后停止), 写 runtime/ |

依赖关系: AC-004 原文要求"其耗时任务已经执行", 因此 G-B 内部按 AC-002 -> AC-004 -> AC-003 顺序执行.

## 人数决定

- 当轮可用非作者验收者: 2 名.
- 计划人数: 2 名, 即把 G-A 与 G-B 各交给一名本轮新开的子会话.
- 拆开后的实际收益: 两条证据链相互独立, 覆盖不同工具链与不同风险面 (浏览器渲染 vs 命令输出/退出码), 且 BR-001 只做静态比对, 与端口无关, 使 G-A 在实例就绪前就有独立工作可做.
- 资源依据 (为何不违背"同一份资源只派一人"): 全部 4 个场景确实都落在同一个独占地 (端口 18101 上的单实例 alpha). 因此不重复准备: 实例的启动与停止只由 G-B 做一次, G-A 只做只读消费 (health 轮询 + 页面渲染), 不启动也不停止任何实例, 不产生端口争用.
- 同步方式: G-B 就绪后写 `verify-r1/verifier-b/instance-ready.marker`; G-A 完成 AC-001 后写 `verify-r1/verifier-a/ac-001-done.marker`; G-B 见到该 marker (或 20 分钟超时) 后才停止实例, 并在证据里记录停止方式.

## 派工记录

| 组 | 会话名 | Herdr pane/tab | 模型 (thinking) | 承接标准 | 创建时间 |
| --- | --- | --- | --- | --- | --- |
| G-A | verify-g1 | 见 REPORT.md | cli/deepseek-v4.1-flash-expires-on-0910 (high) | AC-001, BR-001 | 见 REPORT.md |
| G-B | verify-g2 | 见 REPORT.md | cli/glm-5.3-flash (xhigh) | AC-002, AC-003, AC-004 | 见 REPORT.md |

选型依据: 任务画像接近 review (执行+核对+报告). 候选已用 llm-select/score.py 评分并核实 pi auth ready. G-A 需要读图核对截图, 选 multimodal 1.5 的 deepseek-v4.1-flash; G-B 需要长时间命令执行与逐字比对, 选另一厂商 (Zhipu) 的 glm-5.3-flash 以降低与实现方及 G-A 的共同盲区, 失败代价较高故取第二深档 xhigh.
