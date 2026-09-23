# mailbox 信箱: 独立 skill, pi 连接器与无感自组网 Execution Spec

## 权威输入与决策引用
- Product Spec: `docs/changes/mailbox-standalone/PRODUCT.md`
- Technical Spec: `docs/changes/mailbox-standalone/TECHNICAL.md`
- 决策引用 (只读, 非意图来源): `docs/changes/mailbox-standalone/DECISIONS.md`

## 全局允许范围
- `workflow/mailbox/` (新建: scripts/mailbox.py, pi-extension/, reference/, SKILL.md)
- `workflow/use-sandbox-worktree/` (scripts/swt.py, SKILL.md, reference/, agent-prompts/)
- `sync-to-pi.py`
- `tests/` (仓库根, 含测试改名与新增)
- 运行时部署形态: `~/.agents/skills/mailbox/` 与 `~/.agents/mailbox/` 运行时目录 (由迁移逻辑产生)

## 全局禁止范围
- PRODUCT.md NG-001..NG-009 全部非目标
- 容器契约 env 名 (SWT_MAILBOX_URL/SWT_SESSION_*), BR-005
- 不引入第三方依赖 (BR-001, mailbox.py 纯 stdlib)
- mailbox 扩展不得放入 `pi/extensions/`, 只得经 settings.json extensions 数组指向 skill 目录
- 真远端 git 对容器暴露的任何改动
- 信箱协议签名/时间窗语义不改 (仅新增 from==session 校验)

## 完成定义
- `uv run pytest tests/ -q` 全绿
- `uv run python sync-to-pi.py` 幂等 (重复运行 extensions 数组不重复追加)
- 手工冒烟: sync 后 `mailbox.py serve` 起服, 本机自注册, 双实例互投互取, `/mail-listen` 在 pi 中来信注入
- 每个 issue 的 验证入口 全部通过

## 测试策略
- AC 由 pytest 承接 (双 Mailbox 实例内存互联 / handler 级 / CLI 级, 接缝与适配器见 TECHNICAL.md 测试接缝); pi 扩展的会话注入行为走人工验证清单 (pi TUI 无测试基建), 其余全自动化.
- BR (审计): BR-001/003/005/007/009 静态扫描与权限断言进 pytest; BR-002 权限测试; BR-004/008 文档 grep 测试.
- 非功能: 投信应答预算 (2s/10s) 由 AC-008/AC-010 对应测试承接 (假邻居 + 时间注入).

## 任务图
- ISSUE-01: `issues/ISSUE-01-mailbox-skill-bootstrap.md`; 覆盖: AC-023, AC-024; 依赖: 无.
- ISSUE-02: `issues/ISSUE-02-machine-subcommands-swt-cutover.md`; 覆盖: AC-025, AC-026; 依赖: ISSUE-01.
- ISSUE-03: `issues/ISSUE-03-send-visibility.md`; 覆盖: AC-006..AC-010, AC-021, AC-022; 依赖: ISSUE-01.
- ISSUE-04: `issues/ISSUE-04-neighbor-pending-ops.md`; 覆盖: AC-011..AC-013, AC-037(邻居转发失败行); 依赖: ISSUE-01.
- ISSUE-05: `issues/ISSUE-05-fetch-status-explicit.md`; 覆盖: AC-014..AC-017, AC-036; 依赖: ISSUE-01.
- ISSUE-06: `issues/ISSUE-06-receipts-ttl.md`; 覆盖: AC-018..AC-020, AC-037(滞留丢弃行); 依赖: ISSUE-03, ISSUE-04.
- ISSUE-07: `issues/ISSUE-07-pi-extension.md`; 覆盖: AC-001..AC-005; 依赖: ISSUE-05, ISSUE-06.
- ISSUE-08: `issues/ISSUE-08-container-integration.md`; 覆盖: AC-027, AC-028; 依赖: ISSUE-02.
- ISSUE-09: `issues/ISSUE-09-pull-window-docs.md`; 覆盖: AC-029, AC-030; 依赖: ISSUE-01.
- ISSUE-10: `issues/ISSUE-10-self-organizing-mesh.md`; 覆盖: AC-031..AC-035, AC-037(邻居换址行); 依赖: ISSUE-04.

领取纪律: ISSUE-02/03/04/05/06/08/09/10 均改 `mailbox.py`, 同一时刻只领其中一个, 完成合入后再领下一个.

## 覆盖矩阵
- AC-001 -> ISSUE-07 -> TC-037 -> 人工验证清单 (pi 中来信注入)
- AC-002 -> ISSUE-07 -> TC-038 -> 人工验证清单 (忙时排队)
- AC-003 -> ISSUE-07 -> TC-039 -> 人工验证清单 (重启恢复)
- AC-004 -> ISSUE-07 -> TC-040 -> 人工验证清单 (软提示)
- AC-005 -> ISSUE-07 -> TC-041 -> 人工验证清单 (回执不唤醒)
- AC-006 -> ISSUE-03 -> TC-011 -> pytest -k send
- AC-007 -> ISSUE-03 -> TC-012 -> pytest -k send
- AC-008 -> ISSUE-03 -> TC-013 -> pytest -k send
- AC-009 -> ISSUE-03 -> TC-014 -> pytest -k send
- AC-010 -> ISSUE-03 -> TC-015 -> pytest -k send
- AC-011 -> ISSUE-04 -> TC-018 -> pytest -k admin
- AC-012 -> ISSUE-04 -> TC-020/TC-021 -> pytest -k pending
- AC-013 -> ISSUE-04 -> TC-022 -> pytest -k pending
- AC-014 -> ISSUE-05 -> TC-024 -> pytest -k fetch
- AC-015 -> ISSUE-05 -> TC-025 -> pytest -k fetch
- AC-016 -> ISSUE-05 -> TC-026/TC-027 -> pytest -k fetch
- AC-017 -> ISSUE-05 -> TC-028 -> pytest -k status
- AC-018 -> ISSUE-06 -> TC-030/031/032 -> pytest -k receipt
- AC-019 -> ISSUE-06 -> TC-033 -> pytest -k receipt
- AC-020 -> ISSUE-06 -> TC-034 -> pytest -k receipt
- AC-021 -> ISSUE-03 -> TC-016 -> pytest -k post
- AC-022 -> ISSUE-03 -> TC-017 -> pytest -k post
- AC-023 -> ISSUE-01 -> TC-002 -> pytest -k standalone
- AC-024 -> ISSUE-01 -> TC-001 -> pytest -k migrate
- AC-025 -> ISSUE-02 -> TC-008 -> pytest -k birth
- AC-026 -> ISSUE-02 -> TC-006/TC-007 -> pytest -k machine
- AC-027 -> ISSUE-08 -> TC-044 -> pytest -k birth
- AC-028 -> ISSUE-08 -> TC-045/TC-046 -> pytest -k sessions
- AC-029 -> ISSUE-09 -> TC-047/TC-048 -> pytest -k pullwindow
- AC-030 -> ISSUE-09 -> TC-049 -> pytest -k pullwindow
- AC-031 -> ISSUE-10 -> TC-051 -> pytest -k mesh_auto
- AC-032 -> ISSUE-10 -> TC-052 -> pytest -k mesh_auto
- AC-033 -> ISSUE-10 -> TC-053 -> pytest -k mesh_auto
- AC-034 -> ISSUE-10 -> TC-054 -> pytest -k mesh_auto
- AC-035 -> ISSUE-10 -> TC-055 -> pytest -k mesh_auto
- AC-036 -> ISSUE-05 -> TC-029 -> pytest -k queued
- AC-037 -> ISSUE-04 (TC-023) + ISSUE-06 (TC-036) + ISSUE-10 (TC-054) -> pytest -k log
- BR-001 (审计) -> ISSUE-01 -> TC-003 (import 静态扫描)
- BR-002 (审计) -> ISSUE-01 -> TC-004 (落盘权限断言)
- BR-003 (审计) -> ISSUE-01 -> TC-005 (命名函数单测)
- BR-004 (审计) -> ISSUE-06 -> 文档 grep (PRODUCT/领域语言措辞一致)
- BR-005 (审计) -> ISSUE-02 -> TC-010 (env 常量 grep)
- BR-006 -> 已转场景 AC-021
- BR-007 (审计) -> ISSUE-07 -> TC-043 (扩展源码扫描: 仅 subprocess 调脚本)
- BR-008 (审计) -> ISSUE-09 -> TC-050 (reference/ 文档 grep)
- BR-009 (审计) -> ISSUE-10 -> TC-056 (fleet.key 0600 + join-fleet 仅 ssh 扫描)
- 非功能要求 (TECHNICAL.md 非功能要求节) -> ISSUE-03 -> TC-015 (2s 预算/10s 上限)

## 全局风险和停止条件
- 需要改变 PRODUCT/TECHNICAL/DECISIONS 时停止.
- 需要扩大允许范围或触碰禁止范围时停止.
- Spec 与代码事实冲突或无法提供完成证据时停止.
- 同文件领取纪律被破坏 (两个 mailbox.py issue 并行) 时停止并串行化.
