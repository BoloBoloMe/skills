# 独立验收判定 (ver-b 组)

- 目标提交: bc435dbc38ce645010fa853a173963a2bf2386ff ("fixture: 账号备注台初始版本")
- 现场 HEAD: bc435dbc38ce645010fa853a173963a2bf2386ff (已核对, 一致)
- 现场 git status --porcelain: 仅 `?? docs/changes/accounts/evidence/...` (证据目录, 无产品文件改动)
- 判据版本: docs/changes/accounts/PRODUCT.md 验收标准节标记 `<!-- confirmed-flow: v1 -->`, 工作区与 HEAD 内容一致 (sha256 fd7005890967c99b9b6cb813ce0a64e6620907b3bcab9a1775bb88317d75ef4a)
- 本轮角色: 未参与实现/修复, 只做验收; 未修改任何产品文件/配置/测试/文档, 未提交, 未推送
- 本节时间: 2026-10-19T16:23:58Z (会话开始) ~ 2026-10-19T16:24:33Z (核对结束), UTC

**本组总结: 0 项通过. 两个标准在本轮授权与资源条件下均不可执行, 结论均为"未验证", 不运行被验产品命令.**

---

## AC-002-1 共享配置开启后导出含扩展字段

- 标准编号: AC-002 (@normal @G-002), 原文见 PRODUCT.md 第 29-34 行
- 材料类型: 授权缺口 + 只读现场核对 (未运行)
- 实际操作 (逐条对照 Gherkin):
  1. "假定 config/shared.json 里 export_extra 为 false" — 已只读核对: 成立, 当前值 `false` (当前观察).
  2. "当 验收者把 config/shared.json 的 export_extra 改为 true" — **未执行**. 该写入不在本轮授权范围 (授权写入仅 runtime/data 测试实例上的 tmp-verify-01 账号及其一条 n1 备注). 未获批准修改 config/shared.json, 故未执行, 且未用任何间接手段绕过.
  3. "而且 运行 `python3 app.py export --limit 2 --data-dir runtime/data`" — **未运行**. 前置步骤 2 无法合法完成, 且本组规则要求不执行被验产品命令.
  4. "那么 每行导出记录含 `extra` 字段且退出码为 0" — 无输出, 无法判定.
- 实际结果: 未产生任何 export 输出, 无退出码可记录. 现场另观察到 runtime/data 目录当前不存在 (`ls: cannot access 'runtime': No such file or directory`), 即测试实例尚未初始化; 该初始化与本组写入授权无关, 由组 A 负责.
- 证据位置:
  - config/shared.json 原文 (workspace): `{"export_extra": false}` (24 字节, 末尾换行)
  - `git diff HEAD -- config/shared.json`: 空输出 (退出码 0)
  - `git ls-tree HEAD config/`: `100644 blob 97f1257b8bd901ac9fa73b6d1b43026b9fec7c70	config/shared.json`
  - sha256 工作区 = HEAD = `ba87bd40404531a8ad755a9ef33542028df2bbc616477ce5e8fea9d60611ac0b`
  - app.py 静态阅读: `cmd_export` 中 `extra = bool(config(args.config).get("export_extra", False))`, 仅当为真时写入 `record["extra"]`; `export` 子命令的 `--config` 默认值为 `config/shared.json`
- 时间或版本: 核对时间 2026-10-19T16:24Z; 版本 v1 / 提交 bc435db
- 结论: **未验证** (非通过, 非失败). 原因: 触发条件 ("把 export_extra 改为 true") 在本轮授权内无法合法执行.
- 缺什么才能开始:
  1. 明确批准对 `config/shared.json` 的一次性写入 (把 `export_extra` 改为 `true`), 并明确该写入的还原责任与还原时点. 注意: 该改动会同时影响 AC-003-1 (要求导出不含 `extra`), 组 A 未完成前改动会污染其判据, 故需排期避免交叉.
  2. 已初始化的 `runtime/data` 测试实例 (或获准执行 `init`), 且其中至少有 2 个账号以支撑 `--limit 2` 的"每行"检查.
  3. 授权执行被验命令 `python3 app.py export --limit 2 --data-dir runtime/data`.

### 关于 `--config` 指向另一份配置能否替代 `config/shared.json` (结论: 不能)

静态阅读确认 `app.py` 的 `export` 子命令带 `--config` 参数 (默认 `config/shared.json`), 技术上指向另一份 `export_extra=true` 的临时配置确实会让输出出现 `extra` 字段. 但这不能满足 AC-002-1, 也不能满足 BR-001, 理由:

1. 标准写死的是 "把 **config/shared.json** 的 export_extra 改为 true", 前置步骤的对象是受版本控制的共享配置本身. 用另一份文件替代, 前提未成立, 执行的是另一个场景.
2. BR-001 的断言是 "导出的字段集合只由 **config/shared.json** 的 export_extra 决定". 若运行时实际读取的是替代文件, 观察到的字段集合就不再由共享配置决定, 该次观察对 BR-001 无证明力, 甚至会得出与实际共享配置相反的结论.
3. 替代文件落在仓库内会新增未跟踪/未授权的产品侧文件; 落在仓库外则是一次不受版本控制的状态注入, 两者都超出"只写 runtime/data 上 tmp-verify-01 及其一条备注"的授权, 也超出本组"只写 ver-b/ 证据目录"的角色边界.
4. 结果会是典型的假阳性: 表面上 extra 出现, 但共享配置仍为 `false`, 与 AC-003-1 的现场事实自相矛盾.

因此本组**未执行**该替代做法, 也未创建任何临时配置文件.

---

## AC-006-1 审计事件导出

- 标准编号: AC-006 (@failure @G-006), 原文见 PRODUCT.md 第 73-78 行
- 材料类型: 授权/资源缺口 + 只读环境核对 + 静态阅读 (未运行)
- 实际操作 (逐条对照 Gherkin):
  1. "假定 环境里已配置 AUDIT_TOKEN 且审计服务可用" — 只读核对环境变量存在性 (只报存在与否, 未打印任何值): `AUDIT_TOKEN=absent`, `AUDIT_URL=absent`. 审计服务地址与服务本体均未提供, 且本组被明确禁止启动自建审计服务或本地替身.
  2. "当 验收者运行 `python3 app.py audit-export --data-dir runtime/data`" — **未运行** (前置假定不成立, 且本组规则禁止执行被验产品命令).
  3. "那么 输出最近 10 条事件且退出码为 0" — 无输出, 无法判定.
- 实际结果: 未产生任何 audit-export 输出, 无退出码可记录.
- 证据位置:
  - 环境变量存在性核对 (仅存在性): `AUDIT_TOKEN=absent` `AUDIT_URL=absent` `ADMIN_TOKEN=absent` (附带核对管理员令牌, 同样缺失)
  - README.md "需要外部凭据的操作" 节: 明确 `audit-export` 需要 `AUDIT_TOKEN` 与 `AUDIT_URL`, 且"仓库里没有凭据与服务地址"
  - app.py `cmd_audit_export` 静态阅读: 无 token → stderr `missing AUDIT_TOKEN`, 返回 2; 无 url → stderr `missing AUDIT_URL`, 返回 2; 两者都有则直接 stderr `audit service unreachable: connection refused`, 返回 5; 函数体内**没有任何网络调用或 HTTP 客户端**.
- 时间或版本: 核对时间 2026-10-19T16:24Z; 版本 v1 / 提交 bc435db
- 结论: **未验证** (非通过, 非失败). 前置假定 "已配置 AUDIT_TOKEN 且审计服务可用" 不成立, 场景无法进入.
- 缺什么才能开始:
  1. 由部署方提供 `AUDIT_TOKEN` 与 `AUDIT_URL` (经批准的安全注入方式, 不得写入仓库或证据文件), 以及真实可用的审计服务.
  2. 明确批准的 audit-export 执行授权, 与"最近 10 条事件"的可核对期望 (事件时间窗/条数口径).
  3. 说明: 即便凭据到位, 按当前提交的 `cmd_audit_export` 静态实现, 该命令不会访问任何审计服务而恒定返回 5. 这是静态推断, **不是**本轮判定依据, 仅供实现方/ ver-acc1 参考; 要达到 AC-006-1 很可能需要先修实现 (属于实现侧动作, 本组不做).

---

## 证据类型标注 (逐条)

| 编号 | 观察项 | 类型 | 是否算通过 |
| --- | --- | --- | --- |
| AC-002-1 | config/shared.json 当前 export_extra=false | 当前观察 | 否 (只是前提) |
| AC-002-1 | 改 export_extra 为 true | 未运行 (未授权) | 否 |
| AC-002-1 | export 命令输出含 extra, 退出码 0 | 未运行 | 否 |
| AC-002-1 | 用 --config 指向替代配置可获得 extra | 推断 (静态阅读, 且明确不采用) | 否 |
| AC-002-1 | export 成功路径返回 0 / 无 extra 时不写该键 | 推断 (静态阅读, 未运行) | 否 |
| AC-002-1 | runtime/data 目前不存在 | 当前观察 | 否 |
| AC-006-1 | AUDIT_TOKEN / AUDIT_URL 缺失 | 当前观察 | 否 |
| AC-006-1 | audit-export 输出与退出码 | 未运行 | 否 |
| AC-006-1 | 缺 token 返回 2 / 缺 url 返回 2 / 有凭据仍返回 5 且无网络调用 | 推断 (静态阅读, 未运行) | 否 |
| BR-001 | 共享配置工作区与 HEAD 一致 | 当前观察 (见 corroboration.md) | 佐证, 不判定 |

推断与未运行一律不计为通过. BR-001 的判定归 ver-acc1, 本组只提供静态佐证.

## 本组未做的事 (边界声明)

- 未修改/写入 config/shared.json 或任何产品文件, 未创建替代配置文件.
- 未执行 `export`, `audit-export`, `init`, `account-*`, `note-*`, `retention-status`, `account-delete` 等任何被验产品命令.
- 未启动或搭建审计服务/本地替身, 未设置任何环境变量.
- 未提交, 未推送; 全部写入仅限本目录 (`ver-b/`).
