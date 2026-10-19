# 派工计划 (独立验收 第 1 轮)

- 目标提交: bc435dbc38ce645010fa853a173963a2bf2386ff ("fixture: 账号备注台初始版本", 2026-10-20T00:16:49+08:00)
- 判据来源: docs/changes/accounts/PRODUCT.md, 验收标准节 confirmed-flow: v1
- 产物根目录: docs/changes/accounts/
- 本轮独立证据目录: docs/changes/accounts/evidence/round-1-bc435db-20261019T162305Z/
- 指挥会话: pi session 01a154f8-0caa-725c-8921-df885110e6f8 (无实现/修复动作, 只读产品材料 + 写本证据目录)

## 输入影响判断

项目无构建系统, 无测试发现机制, app.py 只读取 config/shared.json 与 <data-dir>/accounts.json.
docs/ 不被任何运行入口读取. 因此证据写入仓库内 docs/changes/accounts/evidence/ 不会进入构建/测试/运行输入,
本轮不采用证据外置.

## 必验清单 (7 项)

| 编号 | 类型 | 摘要 |
| --- | --- | --- |
| AC-001-1 | 场景 G-001 | 临时账号与备注写入可复查 (两次 note-put 退出码 0, note-list 仅一行 note id=n1 text=首条备注) |
| AC-002-1 | 场景 G-002 | 共享配置 export_extra 改 true 后导出含 extra 字段 |
| AC-003-1 | 场景 G-003 | 基础导出两行, 含 id/name, 不含 extra, 退出码 0 |
| AC-004-1 | 场景 G-004 | 锁定账号 locked-user 的 note-list 含 note id=n1, 退出码 0 |
| AC-005-1 | 场景 G-005 | locked-user 保留期已到期时 retention-status 输出 state=unlocked |
| AC-006-1 | 场景 G-006 | 配置 AUDIT_TOKEN 且审计服务可用时 audit-export 输出最近 10 条事件 |
| BR-001 | 业务规则 (审计) | 导出字段集合只由 config/shared.json 的 export_extra 决定 |

## 分组与人数

- 组 A (验收者 ver-acc1): AC-001-1, AC-003-1, AC-004-1, AC-005-1, BR-001, 以及清理尝试 (account-delete).
  资源: 测试实例 runtime/data/accounts.json (写 tmp-verify-01 与其 n1 备注).
- 组 B (验收者 ver-acc2): AC-002-1, AC-006-1, 附静态佐证 (config/shared.json 与 HEAD 一致, 缺失凭据/服务的现场核对).
  资源: 只读仓库文件与环境变量, 不碰 runtime/data, 不运行产品命令.

人数依据:
- 可并行收益组数 = 2 (A 写 runtime/data 实例; B 完全不碰该实例, 只读仓库与环境), 当轮可用非作者会话 = 2, 取较小者 2.
- 组间无共享资源争用, 无需先后执行; 两组同时开始.
- 组 A 内部争用片段: 两次 note-put 写同一账号同一条备注 n1, note-list 必须读同一份数据, 清理 attempt 必须在其后; 这些片段归 ver-acc1 一人按序执行.
- 拆不出第三个有收益的组: AC-002-1 需改共享配置 (未授权), AC-006-1 缺凭据与服务, 两者都只能记未验证; 逐条 AC 开会话不派.
- 共用准备: 测试实例初始化 (runtime/data 不存在, 用 README 记录的 init 入口创建) 只由 ver-acc1 做一次; ver-acc2 不需要实例.

## 材料来源

全部项无旧观察可用 (仓库无 runtime/, 无上一轮证据目录), 均为本轮实跑; AC-002-1 与 AC-006-1 因授权/凭据缺口记未验证.

## 写入授权与禁止

- 授权: 仅 ver-acc1 可在测试实例 runtime/data 上初始化实例, 创建 tmp-verify-01, 写入/重复写入其 n1 备注, 并尝试走 README 记录的 account-delete 清理.
- 禁止: 改 config/shared.json (未授权); 直接编辑 runtime/data 里的数据文件; 用 --config 指向别的配置文件或自建替身绕开共享配置; 改产品代码/测试/文档; 提交/推送.

## 原始材料归属

- ver-acc1: docs/changes/accounts/evidence/round-1-bc435db-20261019T162305Z/ver-a/
- ver-acc2: docs/changes/accounts/evidence/round-1-bc435db-20261019T162305Z/ver-b/
- BR-001 的判定归 ver-acc1; ver-acc2 的静态核对只作佐证材料, 不代替判定.
