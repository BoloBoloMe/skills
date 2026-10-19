# ISSUE-04 演练记录: 并行验收, 证据共享与修复后复验

本目录是 `docs/changes/verification-skills/issues/ISSUE-04-verify-change-parallel-reverify.md` 的行为证据. 全部结论来自真实 pi 会话在临时 Git 项目上的实际运行, 不是源码关键词断言.

## 待测对象

- 源文件: 本工作树 `workflow/verify-change/SKILL.md` (分支 `issue/04`).
- 改动前版本 (红演练): md5 `9ac67b01f3e9a5d3714e3292dcba6277`, 原件 `logs/SKILL-v2-red.md`.
- 改动后版本 (绿演练): md5 `82cb7913d710dfaf3b898c56d17c618c`, 原件 `logs/SKILL-v3-green.md`; 哈希见 `logs/skill-hashes-red.txt`.
- 只覆盖这版源文件与下列加载方式, 不表示任何全局部署副本已更新; 未运行 `sync-to-pi.py`.

## 宿主与加载方式

- 宿主: Ubuntu 26.04 LTS (x86_64); herdr 0.9.4 (client 与 server 同版); pi 1.3.0; Python 3.14.7; Google Chrome 154.
- 模型与深度: `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`.
- 启动形态: `herdr agent start <会话名> --kind pi --pane <窗格ID> -- --model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high -a`; `-a` 只给该次会话做一次性项目信任, 未改全局配置.
- 加载方式: 待测目录复制到临时项目的 `.agents/skills/verify-change/`, 在项目 cwd 开新 pi 会话, 用 `/skill:verify-change <任务>` 点名加载. 正确加载时, 会话记录的首条用户消息是 `<skill name="verify-change" location="/tmp/orchestra-04/<夹具>/.agents/skills/verify-change/SKILL.md">...`; 用 md5 核对加载的是待测版本.
- 任务提交渠道: `herdr pane send-text <窗格ID> '<任务文本>'` 加 `herdr agent send-keys <会话名> "alt+\\"`; 读回用 `herdr agent read`.
- 重要发现: `/skill:名称` 必须与任务文字在同一行, 否则 pi 不展开技能, 只把原文交给模型. 红演练第一版就踩过这个坑, 见"缺口与风险"第 1 条.

## 夹具

脚本 `setup-drills.sh`: `init` 建全部夹具, `rebuild-parallel` 重建并行夹具, `install-skill <项目> <技能目录>`, `reset-runtime` 停实例并清 `runtime/`. 全部只写 `/tmp/orchestra-04/`.

| 夹具 | 用途 | 起始提交 | 目标提交 |
| --- | --- | --- | --- |
| `/tmp/orchestra-04/parallel` | 并行与共享证据 (修订版产品标准) | `b2d3aed` | `e398c7cc7ca4e493d23689bee3cca1a34d306000` |
| `/tmp/orchestra-04/parallel` (第一版标准) | 跨验收者争用顺序 | `5d6b4b9` | `773fc6bf093c3b17f18a8817f924536902f13d2b` |
| `/tmp/orchestra-04/red-parallel` | 红演练 (旧技能) | `b2d3aed` | `e398c7c` |
| `/tmp/orchestra-04/reverify` | 首次验收与复验 | `8438934` | 缺陷版 `cd087542b4610c49ded0a1278fe8065726b62d9d`; 修复版 `59069130494139f96994f144c1ba09d3b51876d6` |
| `/tmp/orchestra-04/red-reverify` | 红演练 (旧技能, 复验) | `8438934` | 缺陷版 `cd08754`; 修复版 `ad2ed33496a31c59333dccdd6422e69a89bbbc19` |

产品标准经 `workflow/to-spec/ac-draft.py preview/promote` 真实转正, 带 `<!-- confirmed-flow: v1 -->`, 转正后跑 `check-ac.py` 通过. 产品代码 `app.py` 只有标准库依赖: 两个实例各自独立端口与数据目录, 共享 `runtime/shared/record.jsonl` 与 `events.log`; `append` 有 1.2 秒写窗口且不加锁, 两个写者同时写会得到重复 seq (实测 `seq=1 value=alpha` 与 `seq=1 value=beta` 同时出现), 所以争用必须由验收安排解决.

## 验收标准对应证据

| 验收标准 | 证据 |
| --- | --- |
| AC-006-1 可隔离的两组真实并行, 计划写明各组操作, 共用准备执行人与原始材料归属 | `drill-green-parallel/evidence-e398c7c-r1/plan.md` 的"场景组与承接""共用准备与原始材料归属"; `VERIFY-REPORT.md` 的"各可隔离组的开始与结束" (G1 22:14:58, G2 22:15:03, G3 22:15:03.7); `runtime-shared/events.log` 里 beta 的 4 秒 job (14:15:12.59-16.59) 与 alpha 的 append (14:15:14.38) 真实重叠. 失败对照: `drill-red-parallel-load2/plan.md` 把 10 项并成 1 人串行. |
| AC-006-2 争用同一记录的两段先后执行并留顺序记录, 无关只读检查继续 | 跨验收者: `drill-green-parallel-run1/evidence-773fc6b-r1/ver-beta/RESULT.md` 记明等 `coord/record-alpha-done.txt` (22:06:24) 后才 append, ver-alpha 先写 seq=1, ver-beta 后写 seq=2; 只读组同时拍截图跑 report. 同夹具修订版的顺序记录: `drill-green-parallel` 的 `tail/order.md` 与报告"争用片段执行顺序记录"表. |
| AC-006-3 共享材料保留产生者, 版本, 位置, 各验收者独立结论 | `drill-green-parallel` 的 `VERIFY-REPORT.md` "共享材料的产生者 / 版本 / 位置 / 接收方"表: alpha/beta 截图与 report 由 rev-alpha/rev-beta 在 22:15:20-23 产生, 版本 `e398c7c`/`relay-v1`, rev-shared 22:17:08 自己判读 PNG 并另跑 health/report 旁证后独立下结论; `tail/notes.md` 写明"本节只引用原件, 不采信其 summary 结论". 失败对照: `drill-red-parallel-load2/verifier-g1/results-g1.md` 1 人自产自判, 无移交与产生者字段. |
| AC-007-1 复验绑定新提交, 恢复原会话或新开非作者, 按影响重验并复核旧证据适用性 | 恢复分支: `drill-reverify-round2/VERIFY-REPORT.md` (绑定 `5906913`, 指挥 `i04-v1` 恢复, 影响范围一节, 第 5 节旧证据适用性, 5 项结论). 不恢复分支: `drill-reverify-round3/VERIFY-REPORT.md` 与 `PLAN.md` (全新指挥与验收者, 未阻塞, 5 项本轮实跑). |
| AC-007-2 参与修复的验收者不再承担独立验收, 旧证据只作材料 | `drill-reverify-round2/VERIFY-REPORT.md` 第 6.1 节: `i04-a1-ac` 在 22:27 改 `app.py` 并提交 `5906913`, 换成新开 `i04-a2-ac`; 其旧证据只作材料. 失败对照: `drill-red-reverify/verify-r1/verifier-b/REVERIFY-ad2ed33.md` 由修复者本人出具通过结论. |
| AC-007-3 调用方未选择恢复时新开非作者, 不阻塞, 不沿用旧结论 | `drill-reverify-round3/NOTES.md` 与 `VERIFY-REPORT.md`: 新指挥 `i04-v3` 22:36:20, 新验收者 22:37:20, 5 项本轮实跑. |
| AC-007-4 作者日志只作材料, 受影响关键路径由非作者本轮实跑 | `drill-reverify-round2/VERIFY-REPORT.md` "复验重点: AC-003-1": 作者材料 `author-materials/green/report-status-verify.log` 只作参考, 通过依据是验收者本轮 `05-ac003-report.txt` 与 3 次复跑; 副本在 `drill-reverify-author-materials/`. |

## 红演练 (先失败)

| 切片 | 目录 | 旧版实际行为 |
| --- | --- | --- |
| TS-001 并行与证据共享 | `drill-red-parallel-load2/` (正确 `/skill` 加载) 与 `drill-red-parallel/` (首版, 加载方式有偏差) | 两次都把可用 3 人并成 1 人串行: `plan.md` 写"全部 10 项只有一组 (G1), 派 1 名验收者依次做完", 理由是场景共用同一对实例与同一份记录; 没有并行组, 没有争用片段顺序记录, 没有共享材料移交与产生者字段. 1 人 22:48:05 开始, 22:49:16 结束, 逐项按编号串行. |
| TS-002 修复后复验 | `drill-red-reverify/` (首版, 加载方式有偏差) | 修复由第 1 轮验收者 `verify-g2` 完成并提交 `ad2ed33`; 复验仍由同一会话承担, 绑定新提交但只重跑 3 项, 对已关闭的 `verify-g1` 会话只做轮询等待 (先 10 分钟, 再准备等第 2 个 10 分钟), 等不到就放弃 AC-001, 最后自述"无流程偏差". |

## 会话一览

| 轮次 | 会话 | pi session id | 目录 |
| --- | --- | --- | --- |
| 红 (并行) | `i04-r1` + `verify-relay-1` | `01a15450-b887-...`, `01a15452-4156-...` | `sessions/red-parallel/` |
| 红 (并行, 修正加载) | `i04-r1c` + `i04-rp-v1` | `01a154a0-50dd-...`, `01a154a1-6ac1-...` | `sessions/red-parallel-v1/` |
| 红 (复验) | `i04-r2` + `verify-g1` + `verify-g2` | `01a15455-83b2-...`, `01a15457-d661-...`, `01a15457-d660-...` | `sessions/red-reverify/` |
| 绿 (并行第一版) | `i04-g1b` + `ver-alpha/beta/read` | 见 `sessions/green-parallel-run1/` | 同左 |
| 绿 (并行修订版) | `i04-g1c` + `rev-alpha/beta/shared` | 见 `sessions/green-parallel/` 与报告名册 | 同左 |
| 绿 (首次验收) | `i04-v1` + `i04-a1-ac` + `i04-a1-br` | `01a1548b-*` | `sessions/reverify/` |
| 绿 (复验恢复) | 同 `i04-v1` + `i04-a2-ac` + `i04-a2-br` | `01a15491-*` | 同左 |
| 绿 (复验新开) | `i04-v3` + `i04-a3-verify` | `01a15498-7776-...` | 同左 |

作废或需要说明的会话: `i04-g1` (多行提交未触发 `/skill` 展开, 自行搜索后废弃), `probe-skill-load` (验证单行 `/skill` 可加载), `i04-g1b` 首轮 (未触发共享材料, 保留为 `drill-green-parallel-run1`). 全部已在演练结束后用 `herdr tab close` 关闭, 收尾时 `herdr agent list` 中没有本 ISSUE 的会话.

## 清理与残留

- 演练夹具: `/tmp/orchestra-04/` 保留到证据抄完, 之后删除.
- 实例: 每轮结束都由验收者停止, `ss -ltn` 里 18101/18102 无监听; 收尾用 `setup-drills.sh reset-runtime` 复查.
- 未运行 `sync-to-pi.py`, 未写 `~/.agents`, `~/.pi` 或任何全局部署副本.
