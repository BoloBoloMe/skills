# 派工计划 (verify-2080aea-v1)

## 必验清单 (来自 docs/changes/tool-cli/PRODUCT.md, 原文照抄)

验收场景 (`验收标准` 节, 确认标记 `<!-- confirmed-flow: v1 -->`):

- AC-001-1 构建清单第一行: 先 `bash prepare.sh` 生成 `dist/app.txt`, 读第 1 行, 内容为 `tool-cli 1`
- AC-002-1 构建清单第二行: 同上产物, 读第 2 行, 内容为 `commands=greet,count,export`
- AC-003-1 构建清单第三行: 同上产物, 读第 3 行, 内容为 `greet-shout=yes`

审计业务规则 (`业务规则` 节标 `(审计)`):

- BR-002: 本变更不新增第三方依赖, 依赖清单, 锁文件和构建材料与上一提交逐项一致.

合计 4 条 (3 场景 + 1 审计 BR), 与场景数 3 加审计 BR 数 1 相符, 无遗漏. BR-001 未标 `(审计)`, 且已被 AC-003-1 覆盖全大写输出, 不单列.

## 分组

| 组 | 承接标准 | 资源 |
| --- | --- | --- |
| G1 | AC-001-1, AC-002-1, AC-003-1 | 一次 `bash prepare.sh` 产物 `dist/app.txt`, 随后只读三行 |
| G2 | BR-002 | 只读 git: 7bcc692 与 2080aea 的依赖/构建文件对比, 不碰 dist/ |

拆开依据:

- G1 的三条场景共用同一份构建产物, 拆开就要重复跑同一个 prepare.sh, 重复准备成本大于并行收益, 所以三条归一人.
- G2 与 G1 资源不重叠 (G2 只用 git 只读命令, 明确不跑 prepare.sh/build.sh/pytest/tool.py, 不占 dist/), 有真实并行收益.
- 不再拆第三条: 组内工作量小, 逐条 AC 各开一个会话会制造等待和重复劳动.

## 人数

- 当轮可用非作者验收者上限: 3.
- 计划人数: 2 (G1 一人, G2 一人), 取"有并行收益的组数 2"与"可用人数 3"的较小者.
- 不派第三人: 没有第三份互相隔离的资源, 再拆只会重复同一份 prepare.sh 准备.

## 派工记录

| 组 | 验收者名 | 会话 (tab / pane / terminal) | 启动时间 | 承接标准 | 未参与本次实现的可核对事实 |
| --- | --- | --- | --- | --- | --- |
| G1 | acc-g1 | w1J:t4F / w1J:p4H / term_65e30e90296e1a0 | 2026-10-19T20:47 (本地) | AC-001-1, AC-002-1, AC-003-1 | 新建 tab 与 pane, 创建时间晚于实现提交 2080aea (提交时间 2026-10-19 20:26:12 +0800); 启动方式为全新 pi 会话, 未 fork/continue 任何既有会话; 其 argv 只有 `pi --approve --model cli/deepseek-v4.1-flash --thinking high` |
| G2 | acc-g2 | w1J:t4E / w1J:p4G / term_65e30e90287849f | 2026-10-19T20:47 (本地) | BR-002 | 同上, 独立新建 tab/pane; argv 只有 `pi --approve --model cli/glm-5.3-flash --thinking high` |

## 选型依据 (llm-select)

- 任务画像: 简单但要求精确的审查任务, 失败代价中等 (结论要能复核).
- 候选 (已核实 pi 配置内可用): cli/deepseek-v4.1-flash, cli/glm-5.3-flash, cli/gpt-6.1-sol, cli/gpt-6-luna.
- G1 选 cli/deepseek-v4.1-flash, thinking high: review 画像 1.328 (候选最高), 价格低, 速度高; 稳定性为弱依据, 故场景结论要求保留原始输出, 不采信摘要.
- G2 选 cli/glm-5.3-flash, thinking high: review 1.000 达基准, 与该组任务 (机械 diff 比对) 匹配; 与 G1 选不同底层模型, 减少共同盲区.
- 两项都未选 gpt-6.1-sol (已知极慢且昂贵, 任务量不值) 与 gpt-6-luna (编码/知识低于基准).

## 证据目录影响判断

- 目录: docs/changes/tool-cli/verify-2080aea-v1/ (仓库内, 带版本号, 不覆盖旧证据).
- 影响判断: build.sh 只 `compileall tool.py`; prepare.sh 只跑 tools/build_manifest.py; pytest 从 tests/ 收集 test_*.py. 本目录内无 test_*.py, 也不被上述脚本读取, 故不会进入构建或测试发现. 因此留在仓库内, 不外置.
- 允许的额外改动: `dist/` (已在 .gitignore) 与 `__pycache__/`. 其他任何源码/配置/Spec 变化一律视为越界.
