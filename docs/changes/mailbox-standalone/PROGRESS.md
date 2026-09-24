# PROGRESS.md (AFK 书面汇报)

> tdd-as-orchestra AFK 模式: 汇报以本文件为权威载体, 新条目在上. 决定账本见 UNAUTHORIZED_DECISIONS.md.

## R13 (ISSUE-13) 完成 — 全部完工, 等待真机收尾 [2026-09-23]

- ISSUE-13 完成: fleet.key 引导生成 (无文件且无 env 时 0600 自生成, 空 env 视同未设, 重启复用; conftest.Serve 缺省隔离防真机副作用). 合并 7f0a6d4, 全量快层 300 passed, 勾选 5c8bcab. 评审 Spec 全绿 (O_EXCL 防覆写, NG-009 未被架空).
- 至此 13 个 issue 全部实现合入 v2 (顶端 5c8bcab): 原 10 + 用户批准补充 3 (D018/D019/D020). 合计 25 名子代理, 快层测试从基线 235 增至 300.
- 交回用户: 真机收尾清单见 R10 节 (sync 部署, 迁移冒烟, 真 birth, 双实例互投, pi 人工清单, mesh 实测 + e2e 慢层一次); 待用户决定两项 (/mail 邻居数已由 D018 解决销账, 双 pull-window 文档已由 D019 解决销账, 余 fleet.key bootstrap 已由 D020 解决销账 — 三项决定全部落地, 无遗留待决项).
- 收尾清理清单 (技术债, 累计 9 项, 详见 D-AFK-013/016/017 与前述各条, 不影响行为).

## R11/R12 (ISSUE-11, ISSUE-12) 完成, R13 (ISSUE-13) 开工 [2026-09-23]

- 用户批准三项补充 (D018/D019/D020), 落为 ISSUE-11/12/13 (spec commit 39b40da).
- ISSUE-11 完成: status 补邻居数 (host 经 admin 口真计数, 容器未知不报错), /mail 整段转呈免改. 合并 652088a. 评审 Spec 全绿.
- ISSUE-12 完成: swt 侧 pull-window.md 重叠段 (user-data-dir/-R/版本组合) 改指向 mailbox 权威源, 独有内容保留. 合并 6623982. 评审 Spec 全绿.
- 合并后全量快层 298 passed, 勾选 d85bcfb.
- R13: ISSUE-13 (fleet.key 引导生成, D020), 工作树从 d85bcfb 切, 执行者 exec-13. 注意: 既有 "无密钥拒入" 用例的测试前提需适配 (无文件现在会自动生成, 用 MAILBOX_FLEET_KEY 显式控制).

## R10 (ISSUE-10) 完成 — 变更主体完工 [2026-09-23]

- ISSUE-10 完成: exec-10 六切片 (信标/hello 互证/链路密钥协商/认证换址/join-fleet/BR-009 审计) + 评审修复 (hello 指纹绑定身份, _check_ts 收口, 信标构造瘦身). 合并 8c41dad, 全量快层 295 passed, 勾选 f57ad73. 过程一次备份覆盖事故自愈, 评审重点审视后确认 diff 完整.
- ISSUE-01..10 全部已实现并合入 v2. 10 轮执行, 22 名子代理 (10 执行者 + 12 审核者, 全程 ai-work-zai/glm-5.3 thinking max), 双轴评审每 issue 均走 Standards/Spec 两轴.
- 完成定义对照: 每个 issue 验证入口全绿 ✓; 全量快层 295 passed ✓; e2e 慢层 (真容器, 94 例) 本变更全程未跑 — 真机操作延后所致, 见下; sync-to-pi 幂等有自动化测试锚定 (真机运行在收尾清单); 手工冒烟全部在收尾清单.
- 真机收尾清单 (需你在场, 见 D-AFK-006): 1 运行 uv run python sync-to-pi.py 部署并验证幂等; 2 真机迁移冒烟 (旧路径文件搬 ~/.agents/mailbox/); 3 真 birth 验证 env 注入/注销; 4 双 Mailbox 实例互投互取; 5 pi 内 /mail-listen 人工清单 (AC-001..005); 6 office+yoga 同网段互发现与换址愈合实测.
- 待你决定 (spec 缺口, 未自行实现): 1 /mail 邻居数缺失 — 修订 D006 或给脚本补邻居查询能力 (涉凭证面); 2 双 pull-window.md 重叠 — swt 侧旧文档是否指向 mailbox 侧新文档或同步 E4/E5 加固; 3 首台设备 fleet.key 生成方式 (spec 静默).
- 收尾清理清单 (技术债, 7 项): 1 cli_env 去重; 2 夹具命名统一; 3 退役服务拒识补测; 4 register/revoke 前奏 + env 隔离下沉; 5 三元组校验双侧重复; 6 swt admin 前置分支残留 + send_cli helper 上提; 7 _verify_signed 提取 (queued/sessions/poll/ack) + queued env 构建下沉 + poll_body/poll_until 合并.

## R7 (ISSUE-07 与 ISSUE-08 并行) 完成, R8 (ISSUE-09) 开工 [2026-09-23]

- ISSUE-07 完成: exec-07 三提交 (--cli-state/sync 合并 extensions/扩展纯连接器) + 评审修复 (shutdown 不清持久标记修 AC-003, daemonSummaryLines 收口, 回执信措辞). 中途一次思考退化循环 resume 成功.
- ISSUE-08 完成: exec-08 三提交 (birth 烘 SWT_HOST_*_PORT + HOST_DISPLAY 经 ~/.ssh/environment 通道; GET /mailbox/sessions 验签白名单端点) + 评审修复 (ssh env 写入函数收口). 通道选择经 Spec 轴代码证据判可接受.
- 双合并: 62cb9f1 (07), d9ad35b (08); 合并后 282 passed. 勾选 08a93ff. 现场已清理.
- 待用户决定 (新): /mail 邻居数缺失 (D006/D011-C5 spec 缺口, 涉脚本能力扩展与凭证面) — 修订 D006 或给脚本补邻居查询, 挂起待裁决.
- R8: ISSUE-09 (拉窗指令绑定放宽 + url 参数 + reference 文档), 工作树从 08a93ff 切, 执行者 exec-09.

## R6 (ISSUE-06) 完成, R7 (ISSUE-07 与 ISSUE-08 并行) 开工 [2026-09-23]

- ISSUE-06 完成: exec-06 八切片八提交 (三回执/TTL/确定性 id/不递归/取信降噪/滞留丢弃 UTC 日志/reference+领域语言文档钉死) — 中途一次退化中断由接力 exec-06b 完成 (mailbox@ 命名空间设防 + quiet-ack 收口 + sweep 单趟). 合并 961f3c3, 合并后 274 passed, 勾选 9c99c95. 处置详见 D-AFK-011/012.
- UBIQUITOUS_LANGUAGE.md 旧名已在本轮机械同步完毕 (D-AFK-005 挂起项销账).
- 收尾清理清单 (7 项): 1 cli_env 去重; 2 夹具命名统一; 3 退役服务拒识补测; 4 register/revoke 前奏 + env 隔离下沉; 5 三元组校验双侧重复; 6 swt admin 前置分支残留; 7 send_cli helper 上提 + _verify_signed 提取 + queued env 构建下沉 + poll_body/poll_until 合并 (同类测试/去重项合并处理).
- R7 并行轮: ISSUE-07 (pi 扩展 + --cli-state + sync 合并, exec-07) 与 ISSUE-08 (birth 宿主 env + sessions 端点, exec-08), 两工作树分别从 9c99c95 切, 文件不相交 (mailbox.py 不同区域, 合并时注意).

## R4 (ISSUE-04) 完成, R5 (ISSUE-05) 开工 [2026-09-23]

- ISSUE-04 完成: exec-04 六切片七提交 (邻居 GET/DELETE/PATCH + name upsert, 滞留列出/重投/丢弃/上限 100, UTC 日志行, reference 存储语义文档) + 评审修复提交 (32930dc: 地址唯一守卫/预算耗尽语义/死代码/日志收口/错字). 双轴评审: 6 项空白决定全可接受, 6 条发现全采纳已修. 合并 745a890, 合并后 258 passed, 勾选 3fc5cab, 现场已清理. 处置详见 D-AFK-009.
- 收尾清理清单不变 (6 项, ISSUE-04 未新增搁置项).
- R5: ISSUE-05 (取信与服务状态显式: 验活/立即明报/--timeout/--count/status env 凭证//mailbox/queued), 工作树从 3fc5cab 切, 执行者 exec-05.

## R3 (ISSUE-03) 完成 [2026-09-23]

- ISSUE-03 完成: 七切片七提交 + 评审清理 (8eb5fa0), 全量快层 250 passed, 合并 55c795f, 勾选 06244f5. 首轮双轴评审因提示词模板缺陷作废重开 (D-AFK-008), 手写提示词后合格.

## R2 (ISSUE-02) 完成 [2026-09-23]

- ISSUE-02 完成: 五切片五提交, m12 快层 26 passed, 全量快层 243 passed, 双轴评审 0 项退回. 合并 adafa44, 勾选 9cb6a1e. D-AFK-006: 全部真机操作推迟到收尾.

## R1 (ISSUE-01) 完成 [2026-09-23]

- ISSUE-01 完成: 5 切片 + 评审修复 (迁移凭证 0600), 提交 a147f50, 合并 5e93822, 合并后 240 passed.

## AFK 开工 [2026-09-23]

- 进入 AFK, D-AFK-001..003 落盘; spec 文档提交 1a6ccee. 待办链: R5 ISSUE-05 → R6 06 → R7 07 与 08 并行 → 09 → 10 → 全量 + 收尾清单 (清理 6 项 + 真机清单 5 项).
- 红线备忘: 破坏性操作/超 ISSUE 范围需求变更/需外部资源 → 停, 记阻塞.
