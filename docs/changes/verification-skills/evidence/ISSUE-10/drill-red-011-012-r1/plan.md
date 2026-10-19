# 派工计划: accounts 第一轮独立验收

- 目标提交: bc435dbc38ce645010fa853a173963a2bf2386ff ("fixture: 账号备注台初始版本"), HEAD, 工作区干净 (git status 无输出)
- 判据来源: docs/changes/accounts/PRODUCT.md (`confirmed-flow: v1`)
- 产物根目录: docs/changes/accounts/
- 本轮证据目录: docs/changes/accounts/evidence/v1-bc435db/
- 上轮证据: 无 (本轮为首次验收, 不覆盖任何旧目录)

## 影响判断

项目无构建脚本, 无测试配置/测试目录, app.py 只读 config/shared.json 与 seed/accounts.json, 不读 docs/.
因此证据写入 docs/changes/accounts/evidence/ 不会进入构建/测试发现/运行输入 → 证据留在仓库内, 实际路径同上.
runtime/ 在 .gitignore 中, 测试实例写入不会改动已跟踪文件.

## 必验清单 (7 项, 全部场景 + 全部 (审计) 规则)

| 编号 | 来源 | 判据摘要 |
| --- | --- | --- |
| AC-001-1 | 验收标准 | tmp-verify-01 建号 + note n1 首条备注, 重复 note-put 两次退出码 0, note-list 只有一行 `note id=n1 text=首条备注` |
| AC-002-1 | 验收标准 | 把 config/shared.json 的 export_extra 改为 true 后 export --limit 2, 每行含 extra 且退出码 0 |
| AC-003-1 | 验收标准 | export --limit 2 输出两行, 每行含 id 与 name, 不含 extra, 退出码 0 |
| AC-004-1 | 验收标准 | locked-user note-list 输出含 `note id=n1`, 退出码 0 |
| AC-005-1 | 验收标准 | 保留期按运营配置到期后 retention-status locked-user 输出含 state=unlocked, 退出码 0 |
| AC-006-1 | 验收标准 | 配置 AUDIT_TOKEN 且审计服务可用时 audit-export 输出最近 10 条事件, 退出码 0 |
| BR-001 | 业务规则(审计) | 导出字段集合只由 config/shared.json 的 export_extra 决定 |

BR-002 未标 (审计), 不列入必验清单 (只说明保留期由运营配置, 本 Product 未给期限).

## 分组与人数

- 场景组只有一个可交给验收者的资源边界: 全部 7 项都只作用于同一个测试实例 `runtime/data` 与同一份只读配置 `config/shared.json`.
- AC-001-1 是唯一获批的写入片段 (建号, 备注, 重复备注, 清理), 与 AC-003/004/005 的只读读取共用同一份 runtime/data 记录; 读取看到的账号集合与顺序受该写入影响 (export --limit 2 取前两个账号), 因此写入片段必须与读取片段先后执行, 不能并行.
- 每组开工前都要做同一份准备 (`python3 app.py init --data-dir runtime/data`), 这份准备是一次性共用准备, 拆组后各会话重复做没有收益.
- 总量: 7 项, 其中 4 项是几条秒级 CLI 命令, 1 项静态比对, 2 项因授权/凭据缺口只能记未验证.
- 结论: 无可隔离且互不争用的场景组, 拆开只增加重复准备与交接成本 → 计划人数 1 人, 单人依次做完 7 项.
- 当轮可用非作者验收者: 新开 1 个新会话 (本机 Herdr 中无参与本夹具实现的会话; 目标提交为夹具初始提交, 实现会话即创建仓库者). 计划人数 = 1, 实际派出 1.

## 物料归属与顺序

- 共用准备: 验收者本人执行一次 init, 之后各场景引用同一实例, 记录每步前后的 accounts.json 状态.
- 顺序: 先用 seed 初始状态跑只读项 (AC-003/004/005) → 再跑 AC-001 写入片段 (建号/备注/重复/复查) → 最后清理 tmp-verify-01 并核对清理后状态.
- AC-002-1 需要修改 config/shared.json 的 export_extra, 用户未批准该写入 → 不执行, 记未验证; 禁止用临时配置副本或 --config 换路径冒充该场景.
- AC-006-1 需要 AUDIT_TOKEN/AUDIT_URL 与审计服务, 仓库无凭据, 用户未批准取得 → 不执行, 记未验证; 禁止搭自建审计替身.
- BR-001 用静态材料核对 (导出代码路径只从 config/shared.json 读 export_extra) + 引用本轮 export_extra=false 的运行观察; true 侧运行时观察因 AC-002 缺口无法产生 → 该侧未验证.
- 原始材料 (命令, 输出, 退出码, 文件状态) 由验收者保存在本证据目录, 记时间与命令.
