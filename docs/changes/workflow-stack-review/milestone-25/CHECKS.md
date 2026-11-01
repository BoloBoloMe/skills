# milestone-25 准备物检查记录

本记录由本节点主持会话写入, 不代替终点验收. 它覆盖 milestone-25 自己的完成标准: codebase-map v1 的 PRODUCT/TECHNICAL/EXECUTION/issues 可读, 无未处理的标准或验证契约缺口, milestone-26 可按 drive-execution 派工.

## 产物

- 决策账本: [DECISIONS.md](DECISIONS.md) (D001-D020, F001-F008)
- 产品规格: [PRODUCT.md](PRODUCT.md) (48 场景 / 9 组 AC, 对应 AC-001..AC-009; 用户 2026-11-01 采纳 v4, review_id `39f34602d5adb1d94ea98acbd9621a55ec37c3a39cad65cc77155eb98c6264a8`)
- 技术规格: [TECHNICAL.md](TECHNICAL.md)
- 执行输入: [EXECUTION.md](EXECUTION.md) 与 [issues/](issues/) (ISSUE-01 至 ISSUE-07)
- 关联改动: `docs/language/UBIQUITOUS_LANGUAGE.md` 的"结构地图 / 结构地图服务 / 数据键"词条, `docs/adr/0026-codebase-map-host-resident-service.md` 的适配指针, `../milestone-24/DECISIONS.md` 的 U002 替代指针 (m25 D011/D016)

## 实际检查

1. 领域感知: `domain-awareness` 只读核对 `docs/language/UBIQUITOUS_LANGUAGE.md` 与 `docs/adr/0026-*`; 发现两处措辞与 m24 U002/U003, m13 D027 冲突 (原写"高度=层号", 汉化算在 v1), 已按 m25 D011 改正, 见 "关联改动".
2. 验收草稿迭代与机检 (每版都跑 `uv run workflow/to-spec/check-ac.py <暂存稿> --draft <草稿>`):
   - v1 38 场景 -> v2 40 (主会话验收意见 7 条) -> v3 45 (第一轮独立检查返工) -> v4 48 (第二轮独立检查返工); 每版退出码 0.
   - 起草与改写都由独立子会话完成 (`/tmp/to-spec-ac-h4wg2n7u`, `/tmp/to-spec-ac-wget2lkq`, `/tmp/to-spec-ac-m__bupov`), 主会话只做验收与决策, 未代写正文.
3. 转正与机检: `uv run workflow/to-spec/ac-draft.py promote ... --review 39f34602...` 返回 `success: true`; 正式 `check-ac.py` 通过 - 48 个场景, 9 个 AC; `check-tech.py` 通过 - 7 节. 两个脚本自带 PEP 723 依赖, `uv run` 直接跑即可.
4. 第一轮独立只读检查 (`/tmp/m25-spec-check/REPORT.md`, 未参与编写): 17 条发现 (2 阻断 + 15 建议), 主持会话逐条核实全部成立, 返工:
   - 阻断 1 镜像 digest 口径冲突 -> 新增 D016 (细化 m24 U002 的字段口径) + BR-016/AC-007 改写 + m24 U002 状态补替代指针.
   - 阻断 2 分析类验收无宿主侧证据来源 -> D016 (b) 定验证分工 + TECHNICAL 接缝与依赖/非功能要求 + EXECUTION 完成定义与验证策略.
   - 15 条建议: 门禁失败补分母与零声明清单, `--json`/env/超时标为实现选择, `_serve-daemon` 标内部入口, G-001 去"一条命令", 24h 改"隔一段真实时间", 新增 `serve --port`, `delivery_notes` 承载交付说明, `unsupported_extensions` 补 reason, 副本不删 + 清理入口, pid 活但端口无人应答, `BLOCKED` 语义, 两道静态守卫 + `check_skill.py` 入口, 连字符脚本 import 措辞, 调用式与 `cache/cache.json` 字段, 地址占位.
5. 第二轮独立只读复查 (`/tmp/m25-spec-recheck/REPORT.md`, 另一名未参与会话): 第一轮 17 条判定为 11 条已闭环 / 6 条部分闭环 / 0 条未闭环; 新发现 1 阻断 + 9 建议, 核实全部成立, 返工:
   - 阻断 N-01 地址缺口后"谁拼 URL"互斥 -> 新增 D017 (`serve --address <IP>`, URL 仍由 serve 组装) + AC-008 新增场景.
   - N-02 换端口语义空缺 -> 新增 D018 (端口留痕 `last_port`/`last_url`, stop 只置空 pid, 换后沿用新端口, 有存活实例报 `instance_running`) + AC-003 两条场景.
   - N-03 排除集与分母不同源 -> D019 (glob 转正则, 工具默认过滤单列) + BR-015/BR-024.
   - N-04 判空口径 -> D020 (清单与磁盘交集, 两类文案) + AC-004 两条场景.
   - N-05 文档责任漏清理入口, N-06 缺错误码, N-08 build 慢操作无字段, N-09 原因维度写反, N-10 假定里留具体地址: 均按建议改 TECHNICAL 或 AC.
   - N-07 账本登记不规范 -> D016 移入决策节并补确认来源, m24 U002 加替代指针.
6. 执行输入抽查:
   - 每个 issue 都有 父级 / 要交付什么 / 覆盖依据 / 相关决策 / 允许范围 / 禁止范围 / 代码定位提示 / 验证契约 / 验证入口 / 交付证据 / 风险提示 / 停止条件 / 验收标准 / 被阻塞于; ISSUE-07 是纯核验模板 (要核验什么 / 验证入口 / 完成证据 / 适合 AFK 的原因).
   - 覆盖矩阵把 AC-001..AC-009 与 BR-001..BR-037 逐条落到 issue 或人工核验; 审计 BR-033/034/035 走人工核验; 容器内 pytest 项与只能在宿主执行的项分开写.
   - 抽查 ISSUE-05 验证入口: 6 个 TC 都是从真实入口 (CLI 子进程 / 隔离 HOME 与运行时目录) 取结果, 缺地址分支断言退出码 0 且无 `url`, `keys` 只给键名.
7. 评审起点核实 (本会话复跑, 不采信子会话口述):
   - HEAD 在写本记录前为 `e5918a5`; 权威输入提交为 `075665a`. EXECUTION.md 已改为"以含本文件的提交为起点, 派工时 `git rev-parse HEAD` 复核".
   - 收集基线: `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 连跑两次均 **865 条** (navigate 37 + present 103 + tests 725); `workflow/to-spec/tests` 另有 41 条不在 testpaths. 之前记的 905 条复现不出, EXECUTION.md 已作废该数.
   - 机检复跑: check-ac 48 场景 / 9 AC, check-tech 7 节, 均退出码 0.
   - 文件哈希 (可复算锚点): PRODUCT.md `103b42e4…`, TECHNICAL.md `760af00f…`, DECISIONS.md `5b8d6671…`, 与 EXECUTION.md 登记一致.
8. 未跑 `sync-to-pi.py`, 未改真实安装目录, 未写实现代码, 未动 ROADMAP.json.

## 边界与未验证

- 本节点只准备输入, 没有实现 `workflow/codebase-map/`, 因此 AC-001..AC-009 全部仍是待实现项, 不声称任何一条已通过.
- 本容器没有 podman, 仓库根 `tests/conftest.py` 的 `pytest_sessionstart` 会因此 INTERNALERROR; 全量 pytest 属环境缺口. 容器内只可跑新树与带 `PYTEST_XDIST_WORKER=gw0` 的单文件; 真实分析, 真实渲染, 局域网设备打开, 长期常驻只能由宿主证据承接 (m25 D016).
- 两份独立检查报告都是第三方模型的只读检查, 不构成用户验收; 用户对 v4 的采纳只覆盖验收标准正文, 其余裁决来自"你帮我决定吧"的授权 (账本已如实记录).
- review_id 绑定的是转正当时的暂存稿与草稿字节, 无法从最终三份文件复算 (转正后账本又追加过 D016-D020 的补记); 因此另登记文件哈希作锚点.
- `~/.agents/sandbox-worktree/lan-address` 与 8090 空闲等宿主事实是本节点查询所得 (F002/F003), 实施时须复核, 不作为长期不变的常量.
