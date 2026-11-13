# milestone-14 独立反方复核报告

- 任务标识: workflow-stack-review-m14-opposition
- 审查目标: 提交 1dba5a2 ("doc: milestone-14 确认 present 常驻局域网交付决策"), 绑定该提交树
- 报告人: 未参与盘问与落盘的独立会话 (mailbox session id `01a19504-0d00-73e6-aff3-5e710c734306`)
- 授权边界: 只读代码/文档, 允许读 git diff/show; 仅新建本文件; 未运行产品, 未启停共享服务, 未改实现/账本/ROADMAP.json, 未 commit/push
- 输入: milestone-14/REQUIREMENTS.md, milestone-14/DECISIONS.md, ../ACCEPTANCE.md AC-14/AC-15, 1dba5a2 全量 diff, 以及任务给定线索 (3dc49c6 删 TTL, check_page 无状态对象要求, 控制面源地址守卫)

## 检查范围与检索记录

实际读取: `general/present/{SKILL.md,REMOTE.md,scripts/browser_session.py,scripts/check_page.py,scripts/web_server.py,tests/test_skill_contract.py}`; `general/present/scripts/web_server.py` 逐段精读 (运行时目录/锁/_serve/run_start/run_status/_rebuild_spawn/_rebuild_status/run_stop/run_add_dir/_Handler/_guard_control_namespace/_serve_static/_send_dir_listing); `general/present/tests/test_web_server_lifecycle.py` 关键用例; `workflow/navigate/scripts/web_server.py` 运行时目录段; `workflow/to-spec/tests/test_ac_draft.py` 与 `workflow/to-spec/ac-draft.py` 相关行; `tests/test_swt_web_access.py` 全文; `docs/changes/present-web-server/{DECISIONS,PRODUCT,TECHNICAL,EXECUTION,UNAUTHORIZED_DECISIONS}.md` 相关节; `docs/language/UBIQUITOUS_LANGUAGE.md` 全文; ADR0005/0006/0012; `docs/changes/agent-env-followups/DECISIONS.md` D003/D004/D010/F015; `workflow/use-sandbox-worktree/scripts/env_docs.py` `_web_ports`; `docs/proposals/2026-10-31-host-port-mapping-self-check.md`; ROADMAP.json milestone-13/14/15 (经守门脚本 query); pytest.ini; README.md present 行; sync-to-pi.py 与 `general/present/agents/openai.yaml`.

检索: 全仓 grep `browser_session`/`__PRESENTATION_STATE__`/`PI_PRESENT_WEB_TTL`/`pi-present-web`/`present` 引用面; `git log -S "ip == self.bind"` 定位守卫引入提交 aa9a693; `git show 3dc49c6` 核实 TTL 删除.

未找到的说明: `browser_session.py` 除 present 自身 (SKILL.md, test_browser_session*.py) 与历史文档 (docs/changes, docs/adr) 外无其他调用方; access-web 的 `browser_agent/session.py` (`stop_browser_session` 等) 是另一套同名概念实现, 与 present 的 browser_session.py 无引用关系, 不受 D001 影响. 未发现除下述清单外的遗漏调用方.

## 正方还原 (steelman)

- 定义: milestone-14 是纯决策节点. 交付物 = DECISIONS.md D001-D010 + REQUIREMENTS.md 原始确认记录 + ACCEPTANCE.md AC-14/AC-15, 外加旧账本/规格/ADR/领域语言的替代指针同步. 不实施, 不判验收通过.
- 前提假设:
  - P1: 用户对 Q1-Q10 全选 A 加 "结束", 构成 D001-D010 全部内容的授权; 决策文本与选项文本逐条对齐, 无私加规则.
  - P2: 事实 F001-F009 准确描述当前代码/文档状态.
  - P3: milestone-15 仅凭本账本 + AC-15 + 旧规格的适用范围标注即可实施, 无需再向用户索取产品裁决 (协调方收口语 "当前无剩余待裁决项").
- 论据: 每条 D 标注 Q 来源; 每条 F 标注文件/提交出处; 旧账本被替代条目均附指针.
- 推理链: 用户逐项选择 → 决策映射 → 验收标准 → 实施输入.

四要素中无法从我收到的陈述确定、需标注 `未知` 的: 用户是否逐字确认过 AC-15-07 的展开措辞 (Q10 清单是用户确认原文, AC-15 是协调方转写; 历史会话未提供, 无法排除早有约定). 见发现 B-07.

## 主战场

选 P3 (实施完备性). 理由: P1 有 REQUIREMENTS 逐项原文印证, P2 我已逐条核对为真 (见下 "幸存"), 唯 P3 是全称命题 — 只要找到一个 milestone-15 必须做、但没有任何已确认规则能推出的选择点, "当前无剩余待裁决项" 的收口就被击穿. 且 P3 承载全部下游: P3 错则 D001-D010 即使内容正确也不足以让 milestone-15 开工不返工.

## 反方反驳 (逐项发现)

分级: A = 证实缺陷 (有直接代码/文档证据, 协调方核实后可处理, 不改决策内容); B = 未证实疑点/缺口 (需协调方核实, 部分可能须交用户); C = 边界事实 (记录供追溯, 不构成缺陷).

### A-01 D003 预计影响漏记 test_web_server_lifecycle.py 的 TC-027, 该测试钉住的正是 D003 要取消的行为

- 证据: `general/present/tests/test_web_server_lifecycle.py:874-899` `TestTC027HostFromSSHConnection`: 注入 `SSH_CONNECTION` 后断言 `obj["url"] == f"http://{sip}:{port}/"` 且 `obj["lan_ip"] == sip` — 即旧 D011 的 "SSH_CONNECTION 第 3 字段作 URL host". milestone-14 D003 明文 "不再把 SSH_CONNECTION 的地址直接视为局域网地址", 且预计影响声明改 `_detect_lan_host/_url_host 与输出逻辑`, 但其预计影响清单 (`milestone-14/DECISIONS.md:28`) 只列 `test_web_server_cli.py` 与 `test_skill_contract.py`.
- 论证: D003 改的函数正是 TC-027 断言的行为, 该测试必然要改; 账本枚举受影响测试时漏掉它. AC-15-07 只写 "与改动直接相关的 present 测试...通过", 字面不点名此文件. 漏记的后果: m15 输入准备时可能漏改, 或被误判 "无相关测试可删".
- 处置建议: 协调方核实后在 D003 需要调整或反方处理记录中补记该测试位置; 不需用户再裁决 (不改决策内容).

### A-02 workflow/to-spec 测试直接依赖 present web_server.py 的 _Handler 内部结构, 预计影响未列

- 证据: `workflow/to-spec/tests/test_ac_draft.py:360-366`: `spec_from_file_location(... general/present/scripts/web_server.py)` 后取 `module._Handler` 构造 `ProbeHandler`, 显式注入 `roots/roots_lock/runtime_dir/bind` 四个类属性, 起 ThreadingHTTPServer 验证预览可达.
- 论证: present 的实现是 to-spec 测试的实际依赖 (跨 skill 耦合). D001-D010 预计影响均未列 `workflow/to-spec/`. 若 m15 调整 `_Handler` 结构 (例如随 D007 复核控制面守卫, 或改类属性组织), to-spec 测试会碎, 而 AC-15-07 字面只覆盖 "present 测试". 耦合现在无害 (ProbeHandler 走 loopback, 与守卫兼容), 属受影响却漏记的调用方.
- 处置建议: 补记为已知耦合; m15 动 `_Handler` 时把 to-spec 相关用例纳入回归. 不需用户裁决.

### A-03 test_web_server_lifecycle.py:780 仍注入 PI_PRESENT_WEB_TTL_SECONDS, 实现已无该语义, 账本未记残留位置

- 证据: `general/present/tests/test_web_server_lifecycle.py:780-781` `os.environ["PI_PRESENT_WEB_TTL_SECONDS"] = "0.2"`; 全仓检索该变量仅存于此测试与旧文档 (EXECUTION/TECHNICAL/DECISIONS 历史文); `web_server.py` 无任何引用 (3dc49c6 已删实现, 本次精读 `_serve` 为直接 `serve_forever`). D006 明文 "不设空闲自动退出及其 TTL 环境变量语义"; 旧账本 D026 适用范围更新也宣布 TTL 注入取消.
- 论证: 测试 `test_idle_server_stays_available_until_stop` 设了死变量再断言闲置存活 — 客观上是防 TTL 复活的绊线, 行为方向与 D006 一致, 但变量引用是死语义. 账本宣布 "取消注入" 却未记录现存残留点, m15 清理时可能漏掉或误判变量仍有效.
- 处置建议: m15 清理时移除该注入或改写为显式 "环境变量已无效" 断言; 协调方补记位置即可.

### A-04 领域语言 "控制面" 词条 ("仅 loopback 来源") 落后于实际规则 (loopback 或源 == bind, U-009)

- 证据: `docs/language/UBIQUITOUS_LANGUAGE.md:24-27` 控制面词条写 "仅 loopback 来源"; 实际守卫 `general/present/scripts/web_server.py:499-545` (`_is_loopback_client(ip) or ip == self.bind`); 规则出处 `docs/changes/present-web-server/UNAUTHORIZED_DECISIONS.md:69-73` (U-009, 引入提交 aa9a693); 旧账本 D020 原文同样只写 loopback. 任务线索 "控制接口可能存在源地址兼容守卫" 即此.
- 论证: D007 "保留管理接口仅本机可调用" 语义上兼容 U-009 (源 == bind 的包只有本机自身能发出, 握手不可远程完成, U-009 已论证), 不构成安全判定错误; 但 milestone-14 D009 声称 "同步领域定义", 而这一词条的既有漂移未被处理, 与账本 "新旧规则可追溯" 的口径有出入. 属旧变更遗留, 非 milestone-14 引入.
- 处置建议: 词条补一句 "含 U-009 的源 == bind 放行分支" 或加指针; 不改决策.

### B-05 宿主侧 "明确配置的局域网 IP" 的具体来源未指明 (未证实疑点, 需裁决或补确认)

- 证据: milestone-14 D003 只写 "宿主优先使用明确配置的局域网 IP, 否则探测网卡地址". 已存在同源机制: 宿主 swt 的 `records_root/lan-address` 已确认值文件 (`tests/test_swt_web_access.py` `TestConfirmedLanAddress`; `docs/changes/agent-env-followups/DECISIONS.md` D010 "值取宿主 records_root 里已确认的局域网地址"), 容器的 `SWT_HOST_LAN_IP` 正源于它. milestone-14 全账本未提 lan-address 或宿主侧任何具体配置源.
- 论证: 若 m15 另造配置 (新 env/新文件), present 宿主交付地址可能与 swt 交付链 (birth/status 双 URL 行) 的已确认地址不同源, 同一宿主两套 "已确认". 探测+问用户的兜底路径使实施不被阻塞, 但这是 "当前无剩余待裁决项" 声明下的一个真实留白 — 主战场攻击在此成立.
- 处置建议: 交用户一句确认 (倾向: 沿用 lan-address 已确认值, 与容器 SWT_HOST_LAN_IP 同源), 或明示留到 m15 输入准备按 drive-execution 处理.

### B-06 宿主/容器判定触发器未记录 (缺口, 可推导, 非阻塞)

- 证据: 旧分支由 SSH 变量触发 (SKILL.md 选择模式), 容器分支由 `/run/.containerenv` 触发 (REMOTE.md 容器分支); D001 取消 SSH 分支后, 账本 D003/D005 只写容器规则 (8800, SWT_HOST_*), 未写 "如何判定当前是容器".
- 论证: 可从 D001 需要调整 "将 REMOTE.md 的有效规则并入统一流程" 推导沿用 /run/.containerenv, 故不阻塞; 但触发器是 m15 改 SKILL.md 主流程的必写项, 账本作为 "实施输入" 未点名.
- 处置建议: m15 输入准备时点名即可, 或协调方补一句注记.

### B-07 AC-15-07 的证据形态细则比 Q10 清单字面多出内容 (偷加未确认规则的边缘案例, 置信度中)

- 证据: REQUIREMENTS.md Q10 清单第 7 条原文 "present 相关测试与 skill 格式检查通过; 不修改真实已安装 skills, 不运行同步." ACCEPTANCE.md AC-15-07 额外写 "宿主与容器的局域网实际访问结果分别有证据, 不能以容器自测或源码推断代替宿主场景; 缺环境报缺口, 不虚报通过."
- 论证: 该句可读作 Q10 第 2 条 "宿主/容器都只交付已确认可用的局域网 URL" 的操作化 ("已确认可用" 蕴含实际可达证据), 方向与用户确认一致; 但 "分别有证据/不能以容器自测代替" 的细则措辞是协调方转写, 未见用户逐字确认, 且本节点声明历史会话未提供, 无法排除该约定另有来源. AC-15-01 至 AC-15-06 我逐条对回 Q1-Q10 原文均无溢出, 唯 07 有此一处.
- 处置建议: 协调方确认此细则确为用户本意; 若无据, 在 m15 启动时向用户复述一句. 这不改变决策主体.

### B-08 D003 "未确认可用的探测结果先核实" 在宿主场景无操作定义 (低优先疑点)

- 证据: 容器有 SWT_* 自查链 (env_docs.py `_web_ports` 已含 "先查后问" 三步与 /proc 扫描配方, D003 的 "容器自查顺序沿用环境文档" 前提成立); 宿主探测网卡地址后, 代理无法从本机证实 "用户设备可达", 实际只能回到用户确认.
- 论证: Q3=A 原文 "缺值先自查再问宿主/你" 已提供兜底, 实施不阻塞; 但 "先核实" 一词在宿主侧没有可执行定义, m15 文档化时需要落到 "交用户点开确认" 这类具体动作.
- 处置建议: m15 输入准备时落死; 不需现在裁决.

### C-09 边界事实: to-spec 生成页自带状态对象

- 证据: `workflow/to-spec/ac-draft.py:235` 生成 `<script>window.__PRESENTATION_STATE__ = ...`; `workflow/to-spec/tests/test_ac_reading.py:216`, `test_ac_draft.py:210` 断言其存在. D002 "取消强制不等于禁止旧页面保留无害状态对象" 使其合法, 无冲突. 记录以防 m15 误把 to-spec 当清理对象.

### C-10 边界事实: SKILL.md/REMOTE.md 本体未加里程碑注记

- 过渡期内旧流程文字 (SSH 分支, 文件路径失败出口, 强制状态对象) 仍是字面生效指令. milestone-14 范围声明 "不改 present 实现" 与 F001 "待 milestone-15 改造" 覆盖此点, 属已接受过渡风险, 非缺陷. 收口与 m15 之间若有人调用 present, 将按旧规则执行.

### C-11 边界事实: ROADMAP.json 状态

- milestone-14 仍 "进行中", artifacts 未含反方报告/处理记录 — AC-14-02 未闭环前属正常; 收口时需补 artifacts 与状态, 并处理本报告发现 (D010 预计影响已含此项).

### C-12 边界事实: 旧 D013 适用范围注的指针粒度

- 注文 "第 1/2 项输出/重建的容器例外按 milestone-14 D004/D005 对齐": 第 1 项输出 JSON 的端口部分确由 D004 接管 ("不写宿主发布端口替代它"), 但其 URL 部分实际由 D003 接管 (经旧 D011 的替代指针可达). 可追溯性成立, 粒度略粗.

## 正方核对结果 (反方自证攻击前先验证承重结构)

以下经独立核实全部成立, 构成 "幸存" 部分:

- P1 映射无偷换: Q1-Q10 选项文本与 D001-D010 逐条对读, 未发现决策内容超出选项确认范围 (唯 B-07 一处 AC 转写细则存疑). REQUIREMENTS 来源边界声明 ("历史会话未提供...应报缺口, 不编造") 诚实, 与 ROADMAP milestone-14 引文逐字一致 (经守门脚本 query 核对).
- P2 事实清单属实: F001 (双流程/文件路径失败出口, SKILL.md:49-61, REMOTE.md:14); F002 (_detect_lan_host 优先级 web_server.py:163-178; REMOTE.md 宿主组装旧配方); F003 (运行时目录/字段/0700/0600/原子写/探活, web_server.py:69-75, 336-337, 713-719, 748-757); F004 (check_page.py 无 `__PRESENTATION_STATE__`/state 引用, 全仓 grep 证实); F005 (agent-env-followups D003/D004/D010 与 ADR0012 逐条核对); F006 (navigate 独立运行时目录 `navigate-web-<uid>`, 与 D004 "不共用" 一致); F007 (3dc49c6 删 present/navigate 空闲退出, diff 核实; REMOTE.md 已写持续运行); F008 (旧 D001/D002/D005/D006/D007/D008/D012/D020-D023 在场, 内容相符); F009 (确认记录与 REQUIREMENTS 一致).
- 追溯链: 旧账本 D001/D003/D004/D011/D014 标 "已替代" 附指针, D013/D026/D027/D028 加适用范围更新, 指针目标与内容对得上; 其余旧条目 (D002/D005-D010/D012/D015-D025) 与新决策无矛盾, 无需标注.
- 范围合规: 1dba5a2 纯文档 8 文件, 无实现/ROADMAP/安装目录改动; web_server.py 现行为 (幂等复用, bind_conflict, 保序重建, 越界 containment, 控制面守卫) 与 D004/D005/D008/D007 "保留" 类决策相符, 未发现决策与代码矛盾被隐瞒.
- 任务给定三条线索核实结果: 3dc49c6 删 TTL 属实; check_page 未要求状态对象属实; 控制面源地址守卫存在且有据 (U-009), 属已授权修订, 不构成对 D007 的反驳.

## 反方立论 (替代主张)

不推翻 D001-D010 本身; 立场是: 本节点可以按现有决策推进, 但 "决策完整, 无剩余待裁决项" 的收口表述过强. 替代主张:

1. 收口前做 3 件记录类修补 (A-01/A-02/A-03 + 顺手 A-04), 全部不触碰决策内容, 协调方核实后即可补.
2. B-05 与 B-07 是仅有的两处应回到用户或至少明确记录处置的东西: 前者一句 "宿主地址来源 = lan-address 已确认值" 即可消除; 后者一句确认即可消除.
3. B-06/B-08 显式移交 m15 输入准备清单, 不构成本节点关闭的障碍.

若协调方采纳 1-3, 本反方对关闭 milestone-14 无进一步反对; 若不补 B-05, 则 m15 大概率要在输入准备阶段为宿主地址来源再盘问一轮, 提前发生的成本低于事后返工.

## 幸存与比较

正方幸存: 用户授权链完整且与我核对的代码事实一致; 决策的产品选择 (统一交付, 删本地路径, 取消状态对象, 缺值不降级, 单例/单记录, 端口区别, 不自停, 接受长期开放, 保留旧目录规则, 新账本) 每一条都有用户选择背书, 反方在产品层面未找到可推翻点. 旧规则追溯完整度高于一般账本 (含适用范围更新的细分处理).

反方剩余分量: 全部落在实施输入完备性与账本卫生, 影响范围 = m15 输入准备, 发生概率 = 中 (A-01 几乎必发, B-05 视实现者而定), 不可逆性 = 低 (补记/补问成本极低, 最坏后果是 m15 中途一轮澄清). 即使接受正方最强的幸存论点 (所有产品决策已获授权), "无剩余待裁决项" 仍被 A-01 与 B-05 显著约束: 前者是账本自认 "预计影响" 清单的漏项, 后者是已确认机制 (lan-address) 与账本措辞之间的对接缺口.

## 置信度

- A-01/A-02/A-03/A-04: 高 (代码与文档直接证据, 行号可复核).
- B-05: 缺口存在性高; 处置建议置信度中.
- B-06: 账本未记录为高; 影响评估低-中.
- B-07: 中 (可能存在未提供的确认来源).
- B-08: 中.
- C-09 至 C-12: 高 (事实记录).
- 未知: AC-15-07 展开措辞的原始确认状态; 历史会话内容 (来源边界已声明未提供, 本报告不猜测).

## 结论

未找到足以推翻 D001-D010 的强反方; 找到 4 项证实缺陷 (A-01 至 A-04, 均为记录/追溯层) 与 2 项建议补裁决或补确认的缺口 (B-05/B-07), 另有 2 项可移交 m15 的留白 (B-06/B-08). 建议协调方逐项核实处理后再关闭 milestone-14; 新增或改变决定的处置按 AC-14-02 交用户.
