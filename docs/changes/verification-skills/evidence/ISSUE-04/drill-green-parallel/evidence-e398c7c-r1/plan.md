# 独立验收派工计划 (第 1 轮)

- 目标提交: e398c7cc7ca4e493d23689bee3cca1a34d306000 (HEAD, main)
- 判据来源: docs/changes/relay-board/PRODUCT.md (`confirmed-flow: v1`)
- 证据目录: docs/changes/relay-board/evidence-e398c7c-r1/
- 派工时间: 2026-10-19 22:1x (见各验收者记录)
- 可用非作者验收者: 3 名; 计划人数: 3 名
- 指挥者不运行产品入口, 只核对材料

## 影响判断 (第 3 步)

证据目录在仓库内 `docs/changes/relay-board/evidence-e398c7c-r1/`:
- README 未声明 docs 参与构建; 无构建脚本.
- pytest 默认只收集 `test_*.py`, 本目录内的 .md/.log/.txt/.jsonl/.png 不会被收集;
  验收者不得在本目录写任何 `test_*.py`.
- app.py 不读取 docs/.
结论: 写进仓库不会进入构建, 测试发现或运行输入, 就地存放.
证据目录之外只允许 runtime/ (产品运行目录, 已被 .gitignore 覆盖) 的变化.

## 必验清单 (场景 8 + 审计 BR 2 = 10 项)

| # | 编号 | 内容 |
|---|------|------|
| 1 | AC-001-1 | alpha 状态页截图 + `report --port 18101` 输出 |
| 2 | AC-001-2 | `status --port 18102` 输出与退出码 |
| 3 | AC-002-1 | `job --port 18101 --ms 4000` 输出, 退出码, 实际耗时 >= 4s |
| 4 | AC-002-2 | `job --port 18102 --ms 4000` 输出, 退出码, 实际耗时 >= 4s |
| 5 | AC-003-1 | 记录不存在时 `append --port 18101 --value alpha` |
| 6 | AC-003-2 | 记录已有 alpha 时 `append --port 18102 --value beta` |
| 7 | AC-004-1 | 耗时任务执行中 `log --port 18101` |
| 8 | AC-005-1 | 两侧截图与 report 的 instance/version 一致, 两侧 report 含 state=ready |
| 9 | BR-001 | 共享记录序号从 1 连续递增不重复, 每个 value 只出现一次 |
| 10 | BR-002 | 事件日志只增不改, 只读查看前后文件内容不变 |

## 场景组与承接

| 组 | 验收者 | 承接标准 | 独立资源 | 并行 |
|----|--------|----------|----------|------|
| G1 alpha | rev-alpha | 1, 3, 7 (+ alpha 截图与 report 作为第 8 项材料) | 端口 18101, runtime/alpha, own evidence | 是 |
| G2 beta | rev-beta | 2, 4 (+ beta 截图与 report 作为第 8 项材料) | 端口 18102, runtime/beta, own evidence | 是 |
| G3 共享记录 | rev-shared | 5, 6, 9 | runtime/shared/record.jsonl (唯一写者) | 是 |
| G4 收尾只读 | rev-shared | 10, 8 | 只在 G1/G2/G3 停止写入后执行 | 否, 必须排在 G1/G2/G3 之后 |

## 共用准备与原始材料归属

- alpha 实例启动/停止: rev-alpha 独自负责 (唯一责任人), 启动后保持运行直到指挥者通知本轮 G4 完成.
- beta 实例启动/停止: rev-beta 独自负责, 同样保持到通知.
- 共享目录 runtime/shared 初始为空 (无 record.jsonl, 无 events.log), 由 rev-shared 在第 5 项开始前自行确认文件不存在.
- 每名验收者的原始材料只写自己子目录: alpha/, beta/, shared/, tail/.
- G4 的两项材料由 rev-shared 产生, 但需引用 rev-alpha / rev-beta 的截图与 report 原件.

## 争用片段与顺序依据

| 争用对象 | 写者 | 顺序要求 | 依据 |
|----------|------|----------|------|
| runtime/shared/record.jsonl | 仅 rev-shared (第 5, 6 项) | 第 5 项必须先于第 6 项; 二者必须同一记录 | AC-003-1 假定记录不存在, AC-003-2 假定已有 alpha |
| runtime/shared/events.log | G1 的 job, G2 的 job, G3 的 append | BR-002 (第 10 项) 前的哈希与 `log` 调用窗口内不得有其他写者 | BR-002 断言"只读查看前后文件内容不变", 有并发写者时无法归因 |
| 两侧截图/report | G1, G2 各自产出 | 第 8 项必须等 G1 与 G2 都完成后开始 | AC-005-1 假定两侧材料已由各自负责人产出 |

执行顺序记录要求: rev-shared 在 tail/ 下写明前一段执行者会话标识, 自己开始/结束时间, 依据本计划哪一条.

## 只读检查不受牵连

第 1, 2, 3, 4, 7 项 (G1/G2) 与其他组无写冲突, 与 G3 同时开工; 第 7 项只需 alpha 自己的 job 在跑.

## 人数依据

- 三组写目标互不相同 (alpha 实例, beta 实例, 共享记录), 端口与数据目录各自独立, 可同时开工.
- 无共同构建或共同启动准备: 两个实例本来就是各组自己的准备, 不存在"重复同一份准备"的成本.
- 平行收益: 第 3, 4 项各 4 秒任务, 第 5, 6 项各约 1.2 秒写入窗口, 与第 1, 2 项重叠.
- 派 3 人而非 2 人: BR-002 需要安静窗口, AC-005-1 需要两侧材料, 这两项必须由不承担写入的第三方在尾部执行, 否则 A/B 互相等待并互相评判材料.
- 不逐条 AC 开会话: 每名验收者承接 2-3 条, 按实例与文件归属成组.

## 实际派工回填 (验收结束后)

| 组 | 验收者 | herdr name / pane / tab | pi session id | 会话创建时间 | 承接标准 | 实际起止 |
|----|--------|--------------------------|---------------|--------------|----------|----------|
| G1 | rev-alpha | rev-alpha / w1J:p57 / w1J:t55 | 01a15483-3add-74a0-a077-1b434d6cb4d0 | 2026-10-19T22:14:08+0800 | 1, 3, 7 + alpha 材料 | 22:14:58 ~ 22:18:31 (含停实例) |
| G2 | rev-beta | rev-beta / w1J:p58 / w1J:t56 | 01a15483-4f6f-70ee-ab4b-8bb426dba77c | 2026-10-19T22:14:14+0800 | 2, 4 + beta 材料 | 22:14:58 ~ 22:18:33 (含停实例) |
| G3+G4 | rev-shared | rev-shared / w1J:p59 / w1J:t57 | 01a15483-642c-73fc-8bda-578e542ac6d6 | 2026-10-19T22:14:19+0800 | 5, 6, 9 → 10, 8 | G3 22:15:03.7~22:15:20; G4 22:16:55.31~22:17:39.71 |

选型: 三名均 pi, model `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `max` (review/vision 画像最高分, 失败代价高取深档).

实际顺序事实:
- 三组并行开工, 无等待; G3 的 append 与 G1/G2 的 job 在时间上重叠 (见 plan.md 争用表).
- G4 由指挥者 22:16:52 通知 "G1/G2/G3 写入结束" 后启动, rev-shared 在 tail/order.md 记录前一段执行者与依据.
- 实例生命周期: alpha 由 rev-alpha 独停 (22:18:31), beta 由 rev-beta 独停 (22:18:33); 停止在 G4 完成之后.
