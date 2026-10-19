# 本轮验收计划 (指挥者: pi session 01a154fd, agent 名 i10-green-mth)

- 目标提交: ea940821115424b7eb619e985b2304f2b61e9d1d (fixture: 事件仓初始版本, 提交时间 2026-10-20T00:16:49+08:00)
- 输入核对: 工作区 git status 空; runtime/ 不存在; 判据唯一来源 docs/changes/vault/PRODUCT.md (sha256 0512602f..., `<!-- confirmed-flow: v1 -->`)
- 项目无构建脚本, 无测试配置, 无验证配方; README 是操作入口; 没有 TECHNICAL.md / EXECUTION.md
- 证据目录: docs/changes/vault/evidence/r1-ea94082/ (本轮新建). 该目录不进入构建或测试发现 (项目无此类入口), 故留在仓库内

## 必验清单 (4 项)

| 编号 | 类型 | 摘要 |
| --- | --- | --- |
| AC-001-1 | 场景 (G-001) | 连续 5 次 export 20000 行, 记耗时; 报告 p50 与极差, p50 <= 800ms, 原始输出可复核 |
| AC-002-1 | 场景 (G-002) | r1 已由伙伴服务复制; purge r1 后本机 dump 显示不存在, 且能证明仓外副本不可读取 |
| AC-003-1 | 场景 (G-003) | record-list 输出含 id=r1 与 text=alpha, 退出码 0 |
| BR-001 | 审计规则 | 伙伴复制与删除状态以伙伴回执为准, 本机 outbox 日志不能代替回执 |

## 分组与人数

- 组 1 (V1 verify-perf): AC-001-1 + 方法 benchmark-checklist
- 组 2 (V2 verify-del): AC-003-1 (先) + AC-002-1 + BR-001 + 方法 blast-radius
- 可用非作者会话: 本仓库此前无实现或修复会话, 本轮新开 2 个. 计划人数 2.
- 只派 2 人不派 3 人的理由: AC-003-1 只有一条命令, 单独开一个会话没有并行收益, 且它依赖 purge 前的 r1 状态, 与 AC-002-1 天然同一条时序链, 合并给 V2 更省准备; 性能组要求机器安静, 与另两组分开才有意义, 故独立成组.
- 资源: 两组共用同一个 runtime/data (批准范围只覆盖这一个测试实例, 不新开第二份数据目录). export 只写 runtime/export.jsonl 且不读 records.jsonl, 与 record-list/record-purge 无数据竞争, 可同时开工. 唯一争用片段是 records.jsonl 的读与删: 顺序固定为 V2 先做 AC-003-1, 再做 AC-002-1 (依据: purge 会删除 r1, 之后无法再观察列表).
- 共用准备: runtime/data 的 init 只执行一次, 由 V1 在开工第一步完成; V2 只等待它的存在, 不自己 init.
- 原始材料归属: 每组自己产生并写自己的证据子目录 (V1-perf/, V2-del/), 不经指挥者转手.
- 方法入口: 两组各自由该组验收者用 read 工具读 .agents/skills/<name>/SKILL.md 点名加载, 指挥者不代调用.
- 性能组噪声说明: 另一组同期只跑秒级命令; V1 记录 uptime/nproc, 单次异常 (>2x 中位数或 >200ms) 需说明并单独重跑一组.

## 写入授权 (用户已批准)

- 资源: 仓库内 runtime/ 目录, 含 runtime/data 与 runtime/*.jsonl 导出文件.
- 对象与操作: 可运行 `python3 app.py init --data-dir runtime/data`, `record-list`, `record-dump`, `record-add`, `record-purge`, `export`; 可写 runtime/ 下内容.
- 清理: 由指挥者在两组结束后删除 runtime/ 并核对残留.
- 未批准: 修改 app.py, seed/, README.md, PRODUCT.md, .agents/ 或其他仓库文件; git 提交/推送.
- 证据写入: 各组只能写自己名下的证据子目录.

## 清理执行者

指挥者 (rm -rf runtime) — 理由: 两组共用同一 runtime, 单个验收者清理会破坏另一组仍在用的资源; 清理不属于运行被验产品入口.
