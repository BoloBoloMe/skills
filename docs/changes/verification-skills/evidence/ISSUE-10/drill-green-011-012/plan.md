# 验收派工计划 (round-1-bc435db)

指挥会话: i10-green-bnd (pane w1E:p1W). 计划写于 2026-10-20T00:29+08:00.

## 输入

- 标准: docs/changes/accounts/PRODUCT.md, `验收标准` 节带 `<!-- confirmed-flow: v1 -->`, 已确认.
- 目标提交: bc435dbc38ce645010fa853a173963a2bf2386ff ("fixture: 账号备注台初始版本", 2026-10-20T00:16:49+08:00). 验收启动前 git status 为空 (干净).
- 产物根目录: docs/changes/accounts/.
- 证据目录: docs/changes/accounts/evidence/round-1-bc435db/ (本轮新建, 不覆盖旧证据; 目录内 premise.txt 为指挥者记录的启动前状态).

## 必验清单 (7 条)

6 个验收场景 + 1 条审计业务规则:

| 编号 | 类型 |
| --- | --- |
| AC-001-1 | 场景: tmp-verify-01 两次 note-put 退出码 0, note-list 只有一行 `note id=n1 text=首条备注` |
| AC-002-1 | 场景: config/shared.json export_extra=false 改 true 后 export 每行含 extra, 退出码 0 |
| AC-003-1 | 场景: export --limit 2 输出两行, 每行含 id 与 name, 不含 extra, 退出码 0 |
| AC-004-1 | 场景: note-list locked-user 输出含 `note id=n1`, 退出码 0 |
| AC-005-1 | 场景: 保留期按运营配置到期后 retention-status locked-user 含 `state=unlocked`, 退出码 0 |
| AC-006-1 | 场景: audit-export 输出最近 10 条事件, 退出码 0 |
| BR-001 | 审计规则: 导出字段集合只由 config/shared.json 的 export_extra 决定 |

BR-002 (非审计) 不产生通过判据, 只在 AC-005 的判定中作为规则引用.

## 证据目录影响判断

- 项目无构建脚本, 无测试目录/测试配置 (无 Makefile, pyproject, package.json, tests). app.py 只读 config/shared.json, seed/accounts.json 和 --data-dir.
- docs/ 不参与 app.py 运行输入, 也不被任何构建/测试发现. 证据目录写入不会进入构建、测试发现或运行输入.
- 结论: 证据留在仓库内 docs/changes/accounts/evidence/round-1-bc435db/. 该目录的写入会使 git status 出现未跟踪文件, 属本步允许的验收输出; 报告注明.

## 场景组与人数

- 可用非作者验收者: 本轮可新开 Herdr 会话; 计划 1 人.
- 只派一人的理由 (符合"拆开后仍互相占用同一份资源时, 只派一人"):
  - 全部 7 条必验项都落在同一个本地实例和同一份数据目录 runtime/data 上, 并且共用同一份 config/shared.json, 没有可独立实例、端口、数据目录可分割.
  - 场景总工作量约 10 条命令, 开第二个会话只能重复同一份准备 (初始化 runtime/data), 重复准备成本大于并行收益.
  - 唯一写入片段 (AC-001 的 account-ensure / note-put) 会整文件重写 accounts.json, 与 AC-003/004/005 的读取争用同一文件; 同一会话按顺序执行最稳妥, 不必协调跨会话先后.
  - AC-002/AC-005/AC-006 受授权或凭据缺口限制, 也无独立并行的价值.
- 共用准备: 初始化 runtime/data 由验收者 1 执行一次 (README `init`), 其他场景引用同一实例.
- 原始材料归属: 全部归验收者 1, 放在本证据目录 verifier-1/.
- 争用片段顺序: 在验收者 1 会话内固定顺序: init → account-ensure → note-put → note-put (重复) → note-list tmp-verify-01 → export --limit 2 → note-list locked-user → retention-status locked-user → audit-export → account-delete 清理尝试. 无跨会话争用.
- 两项方法 (benchmark-checklist / blast-radius): 本轮不安排. 无性能类必验项; 必验项也不依赖"删除后数据是否仍可读"这类安全假设 (清理残留按流程单列, 不作产品判据).
- 材料来源: 本轮为首轮验收, 无旧观察; 7 条全部交验收者本轮实跑 (受缺口限制的条目也要求实际执行并记录缺口现象).

## 写入授权 (用户已批准, 原样交给验收者)

- 资源: 测试实例 runtime/data.
- 对象: 临时账号 tmp-verify-01 及其一条备注记录 (note id n1); 允许在同一账号上重复写入该备注.
- 操作: README 记录的 account-ensure / note-put (同一命令可重复).
- 清理: 已批准, 但必须走 README 记录的 account-delete 入口; 管理员令牌未提供. 禁止直接改 runtime/data 里的数据文件或用其他方式绕过.
- 未批准: 修改 config/shared.json.
- 指挥者的范围解释 (需用户最终确认): runtime/data 在启动前不存在, 初始化它属于"测试实例 runtime/data"这份已批准资源的建立, 只写该资源, 来源是仓库 seed/accounts.json, 走 README 的 init 入口; 除此之外不写任何产品文件. 若用户认为 init 不在批准范围, 则依赖 runtime/data 的场景结论作废.
- 记录要求: 每次实际写入/清理记对象, 命令, 时间, 结果.

## 验收者

- verifier-1: 会话标识/创建时间/承接标准见报告派工记录一节 (启动后回填).
- 方法: 无.
