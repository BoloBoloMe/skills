# M05 AFK 自主决定记录

## UD-01 EXECUTION.md 由总指挥自拟拆解
- 问题: tdd-as-orchestra 要求 EXECUTION.md 由用户提供, M05 产物目录无任何执行拆解; 用户以 probe 遍历模式指派 M05 且会话为 auto 模式无法回问.
- 决策: 总指挥依据权威输入 (MILESTONE-05.md 任务书 + M04 账本 D001-D013/F001-F008 + 现场勘察事实) 自拟 EXECUTION.md, 拆解 8 个 ISSUE.
- 理由: M05 类型为 task/AFK, 设计与验收均已在 M04 与用户闭环, 拆解不产生新需求; M03 有 AFK 授权先例.
- 影响: ISSUE 粒度与顺序为本记录所定, 用户可事后推翻.
- 风险: 拆解与用户预期粒度不符; 每条 UD 与提交历史可追溯.

## UD-02 测试接缝与用例不再回问用户
- 问题: tdd 要求写测试前向用户确认接缝和用例.
- 决策: 视为已由权威输入回答 — D011 六项验收即验收清单, D011 另指明 M05 的验证手段 (swt 输出 + present 公开命令/HTTP); 不回问.
- 理由: tdd 原文 "如果代码库有决策账本且内容已回答了测试设计需要确认的问题, 就不必再问"; M03 同款处理.
- 影响: 测试设计直接落 EXECUTION.md 各 ISSUE 接缝.
- 风险: 无; D011 未覆盖的用例不写成已确认约束.

## UD-03 LAN 已确认地址机制 = `--lan-ip` flag + 根级持久文件 + birth DECIDE 询问
- 问题: D010 要求 "优先沿用已确认值, 无法确定时才问用户", 但代码无任何已确认地址存取机制 (勘察 A4).
- 决策: (1) swt 增 `--lan-ip <ipv4>` flag; (2) 确认值持久化到 records_root 根级文件 (host 级, 非单 repo); (3) birth 无已确认值且未给 flag 时, 走既有决策收据协议 (新增 kind `lan-address`) 打 DECIDE 行 exit 1, 候选值 = lan_ip() 现算结果仅作提示展示, 不作交付; (4) 交付的局域网 URL 一律只用已确认值.
- 理由: 决策收据是 swt 既定的非交互问人协议 (D026, 勘察 A5), 问地址与问 network-mode 同构; host 级持久化符合 "宿主地址" 语义; lan_ip() 猜测值降为提示正好落实 F006 "不算可达性证明".
- 影响: 首次 birth 多一轮 DECIDE; resume 不新增询问 (新容器必经 birth 已确立); 旧容器无 web URL 不涉及.
- 风险: 用户换网络环境后需重确认 — 提供 flag 覆盖即可; 收据指纹机制防答案错配.

## UD-04 status 交付形态: 有 web-port 的容器附双 URL 行
- 问题: D003 要求 birth/status/resume 交付一致, 但 status 现状只打 STATE JSON, 不打任何交付行 (勘察 A2).
- 决策: status 对每个带 web-port 的容器 (即新规则容器) 在 STATE 之外附本机/局域网双 URL 行, 与 birth/resume 的 web URL 段同源组装; 无 web-port 的旧容器输出不变.
- 理由: "一致的映射信息" 的最小诚实实现; 不给旧容器编造 URL (D009 不处理现有容器).
- 影响: status 输出新增行, 不改变既有行结构.
- 风险: 低; 解析 STATE 的消费者不受影响.

## UD-05 present 锁端口机制: start 增显式锁定, status 重建不得换端口
- 问题: F002 记录的差异 — 容器分支文档禁止换已映射端口, 但通用 status 重建 (_rebuild_spawn) 在端口被占时随机换端口 ≤10 次, 容器内换端口 = 映射失效, 违 D001/D002 的实际运行要求.
- 决策: web_server.py `start` 增显式锁端口标志 (`--fixed-port`), 锁定态持久化进实例状态; status 重建遇锁定实例且原端口被占 → 报错不换端口; 容器分支文档钉 `start 8800 <root> --bind 0.0.0.0 --fixed-port`. 非锁定用法 (远程模式随机端口) 行为不变.
- 理由: 换端口在非容器场景是 feature (随机端口无映射约束), 不能全局禁; 显式锁定最小侵入, 容器分支声明式启用.
- 影响: present 公开命令加一 flag; 新增测试覆盖锁定重建报错路径.
- 风险: 低; 不锁定时不触碰既有逻辑.

## UD-06 当前设备机制落为 skill 指引级, 不新增 swt 存储/服务端端点
- 问题: D012 要求 "工作开始确定当前设备, 能从会话确定就自动记录, 不确定才问一次, 展示信件显式指定该设备"; 代码侧无设备清单可查 (容器只能投信, admin 面仅 host loopback).
- 决策: 实现为 agent 行为指引 (SKILL.md): 容器 agent 工作开始时确定当前设备 (会话已有信息/用户明示优先, 否则问用户一次并记住, 换电脑时更新), 展示相关信件 `to` 显式填该设备名; 信件 body 必带容器名 + 宿主定位 (主机/repo/records identity) + 原会话标识; 设备侧配方: 收信 → 经既有 ssh/herdr 查 host STATE/podman port 得 web URL → 回话原会话 → 该设备 xdg-open 一次. 不新增 URL 查询端点/设备清单接口/存储字段.
- 理由: D006 明确 "不假定 M03 已有未定义的 URL 查询端点", D013 禁止把未提出的接口伪装成已确认设计; 指引级是当前权威输入支持的最大范围; 真链验证 (TC-004 双设备) 归 M09.
- 影响: ISSUE-06 为纯文档+示例; M09 待验收清单加长.
- 风险: 指引不被遵守时链路断 — 用检查清单式写法 + M09 真跑兜底.

## UD-07 测试文件命名 tests/test_swt_web_access.py
- 问题: tests/ 下 test_swt_m04/m07/m09/m12 全是旧 roadmap (use-sandbox-worktree) 里程碑编号, 与本文路 M04-M09 撞号.
- 决策: M05 门禁测试命名 `tests/test_swt_web_access.py`, 按领域命名不沿用 mNN.
- 理由: 避免双 roadmap 编号混淆 (勘察 E13 确认旧文件归属).
- 影响: 无.
- 风险: 无.

## UD-08 镜像重建与 present 规则入容器: 本环境不可执行, 交付改动+步骤文档
- 问题: D013 要求未来新容器实际拿到更新后的 present 规则 — present skill 是 base 构建期 COPY (勘察 D11), 需重建 base (级联 display/项目层, D017); 但本会话在 sandbox 容器内, 无 podman/无 host ~/.agents/skills 写权, 无法执行重建与分发.
- 决策: 本 Milestone 交付 = 仓库内全部代码/文档改动 + SKILL.md 写明分发步骤 (sync-to-pi → host skills → base 重建 → 新容器); 实际重建与真机验证显式留作 host 侧待办, 与 M08/M09 协调; 不把 "仓库已改" 宣称成 "容器已生效".
- 理由: AFK 红线 — 需要外部资源/权限的操作不自行执行; D013 只要求 "按实际修改对象处理分发", 在可行范围内交付.
- 影响: M05 关闭时 "新容器实际取得规则" 为待验收项, 收口汇总明示.
- 风险: 若 host 侧忘记重建, 新容器拿旧 present 规则 — 交付说明与 M09 验收清单双重兜底.

## UD-09 无已确认地址时打显式 "未附发" 提示行
- 问题: 容器有 web-port 但 host 无已确认 LAN 地址时, 交付的局域网 web URL 是省略还是提示 (ISSUE-03 任务书授权执行者选择).
- 决策: 打显式提示行 "web 入口 (局域网) 未附发: host 局域网地址无已确认值", 本机 URL 照打, 不省略不猜测.
- 理由: 与既有 F3 先例 (交付行对缺失项显式说明) 同构; 静默省略会让用户以为没有 web 入口; D010 只禁止交付猜测地址, 不禁止说明缺失.
- 影响: web_delivery_lines 在 lan=None 时产出一行提示.
- 风险: 无; 正常路径 (birth DECIDE 已确立地址) 不触发.

## UD-10 交付用址改已确认值覆盖全部 5 处调用点 (含 ssh/herdr/隧道行)
- 问题: ISSUE-02 提交时 "交付用址一律取已确认值" 未落地 — 5 个 print_delivery_lines 调用点 (birth x3 含显示门禁重交付两处, resume x2) 全部仍传 lan_ip() 现算值; ISSUE-03 实施时发现并一并修正.
- 决策: 5 处调用点统一改 `read_confirmed_lan_address(records_root)`; 附带行为变更: ssh 双入口/herdr/noVNC 隧道行的局域网用址同步改为已确认值 (不再用现算猜测).
- 理由: UD-03(4) 原文 "交付的局域网 URL 一律只用已确认值" 本就覆盖全部交付行, 不只 web URL; D010 同理.
- 影响: 无已确认值时这些行的局域网用址也消失/变化; ISSUE-02 关闭声明追溯以此为准 (其 "交付用址" 部分实际在 ISSUE-03 落地).
- 风险: 用户从未确认过地址时 ssh 局域网行用址缺失 — 与 D010 一致, 可接受; birth DECIDE 流程保证新容器必有确认值.

## UD-11 status 只对 running 容器附 web URL 行
- 问题: Spec 评审观察 — status 经 `podman ps -a` 含已停止容器, print_status_web_lines 会对停止容器打出当时不可达的 web URL.
- 决策: status 只对 state=running 的容器附 web 双 URL 行; 非 running 不附 (不交付不可达链接); resume 后自然恢复.
- 理由: 与 D010 "不把不可用当可用交付" 同一精神; 停止容器的映射虽存续但点击即失败, 附行误导.
- 影响: print_status_web_lines 增运行态过滤 + 对应测试.
- 风险: 低; 停止容器信息仍在 STATE JSON 中可查.

## UD-12 "活跃"语义 = 非 retired (不看运行态), 停止未终结仍拒绝
- 问题: D003 "一母体一个活跃容器" 未定义 "活跃" 是否看运行态; 停止但未终结的容器算不算活跃直接影响 birth 放行.
- 决策: 以 is_active_container 语义为准 — 非 retired 即活跃, 不看运行态; 停止未终结容器照样拒绝新 birth; retired (D033) 豁免. 另加 podman live 实况兜底 (runtime 记录丢失时拦运行中的同母体容器).
- 理由: 词汇表 retired 条 (D033) 反向支撑 "非 retired 即活跃" 读法; 停止未终结容器若放行, 之后 resume 拉起旧容器即成双活, 拒绝是安全方向; 正常流程 (switch 标 retired/terminate 删记录) 不会误伤.
- 影响: 用户想换容器须先 terminate 旧容器 (拒绝信息含指引); 已知边界: live 兜底用 `podman ps` 无 -a, "记录丢失 + 容器停止" 的极端组合漏检, 与 assert_single_active_mother 同限制, 接受.
- 风险: 低; 偏严不偏松, 误拒可通过 terminate 解除.
