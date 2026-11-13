# present 统一局域网交付决策账本

本账本是 milestone-15 的实施输入. 确认来源见 [盘问记录](REQUIREMENTS.md): 用户对 Q1-Q10 全选 A, 随后明确回复 "结束"; 反方复核后对 Q11/Q12 也全选 A. 本轮不实施 present, 不代表 milestone-08 终点验收通过.

## 决策

### D001 宿主和容器统一经 web 服务展示
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: present 不再按 SSH_TTY/SSH_CONNECTION 或用户所在环境分成本地浏览器与远程 web 两条主流程. 宿主和容器都生成页面, 起或复用常驻展示服务, 交付已确认可用的局域网 URL; 不交付 loopback URL 或文件路径作为展示结果. 删除 present 的本地自动打开 Chromium, 页面状态回读流程与专用 scripts/browser_session.py, 不保留备用分支. 反馈与最终确认全部在 chat 完成. 理由: 用户要求宿主/容器一致, 只保留一条交付路径, 不为已取消路径留依赖和维护成本. Q1=A, Q3=A.
- 依赖事实: F001, F002
- 预计影响: general/present/SKILL.md, general/present/REMOTE.md, general/present/scripts/browser_session.py, general/present/tests/test_browser_session.py, general/present/tests/test_browser_session_integration.py, general/present/tests/test_skill_contract.py, README.md
- 需要调整: milestone-15 删除专用脚本及其已失效的配套测试, 将 REMOTE.md 的有效规则并入统一流程或改为统一流程的参考, 不留下默认分支歧义; 不借此改变 access-web 自身浏览器能力.

### D002 取消页面状态对象的强制要求
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 不再强制每页提供 window.__PRESENTATION_STATE__, 不为其增加 HTTP 状态回传端点. 页面可按展示需要保留筛选/缩放/选择等交互, 自行管理必要状态, 无交互页无需空对象. 最终确认在 chat. 理由: 自动状态回读通道已随 D001 删除, 不为不存在的通道保留必填项. Q2=A, Q10=A. 取消强制不等于禁止旧页面保留无害状态对象, 不重写历史页面.
- 依赖事实: F001, F004
- 预计影响: general/present/SKILL.md, general/present/REMOTE.md, general/present/tests/test_skill_contract.py; general/present/scripts/check_page.py 与 test_check_page.py 按实际旧约束核对
- 需要调整: milestone-15 不再由文档或相关检查要求旧状态对象; F004 表明当前 check_page.py 本就未强制此对象, 不凭本决策虚构必须修改的检查器代码.

### D003 局域网地址须来自已确认信息, 缺值不降级交付
- 状态: 已替代 (→ D011, 原文保留)
- 约束性: 必须遵守
- 内容: present 统一流程默认监听 0.0.0.0. 容器交付地址使用已确认的 SWT_HOST_LAN_IP 和当前容器 8800 对应的宿主映射端口 SWT_HOST_WEB_PORT, 不能把服务自报的容器 IP/hostname/url 原样交付. 缺值先依当前环境说明自查, 仍缺则经可用信箱向创建容器的宿主会话索取, 信箱不可用才问用户; 不猜地址或宿主端口. 宿主优先使用明确配置的局域网 IP, 否则探测网卡地址; 未确认可用的探测结果先核实, 不直接作为已可用链接交付. 不再把 SSH_CONNECTION 的地址直接视为局域网地址; 不回落主机名/localhost/文件链接冒充交付. 地址或映射缺失时明确报告阻塞, 不制造成功结果. 理由: 统一交付的是用户设备能访问的局域网地址, 本机存在网卡或监听成功不证明设备可达. Q3=A, Q10=A.
- 依赖事实: F002, F005
- 预计影响: general/present/SKILL.md, general/present/REMOTE.md, general/present/scripts/web_server.py 的 _detect_lan_host/_url_host 与输出逻辑, general/present/tests/test_web_server_cli.py, general/present/tests/test_skill_contract.py
- 需要调整: milestone-15 区分本机服务成功与地址确认成功, 更新地址来源和失败出口; 容器自查顺序沿用环境文档及 milestone-18 的相应规则, 不在本节点改其生成器. start 的 --bind 必填命令接口不因统一流程默认选 0.0.0.0 而自动取消.

### D004 保留用户级单例和唯一 server.json 端口记录
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 同一机器同一 uid 的 present 共用一个存活服务, 多会话/多页复用并增挂目录. 运行时信息唯一维护在 <系统临时目录>/pi-present-web-<uid>/server.json, 不额外建 port 文件或第二份端口真值. 保留现有 pid, port, bind, roots, started_at, fixed_port 等服务信息; port 记录实际监听端口, 容器此处是 8800, 不写宿主发布端口替代它. 启动/重建和目录变化时同步维护记录, 读取后仍需真实探活, 不把残留 JSON 当存活证明. present 自身命令及需要查询 present 的宿主/调用会话使用同一记录与命令结果, 不各造端口记录. navigate 可沿用记录格式, 但它是另一种服务, 不与 present 共用实例/状态文件; 其身份与路径由 milestone-17 按自身隔离要求决定. 测试使用独立运行时目录, 不接管/停止真实展示实例. 理由: 延续现有幂等复用, 保持单一真值, 同时避免不同服务和测试互相误伤. Q4=A, Q8=A, Q10=A.
- 依赖事实: F003, F005, F006
- 预计影响: general/present/scripts/web_server.py, general/present/SKILL.md, general/present/tests; milestone-17 的兼容上下文
- 需要调整: milestone-15 核对现有记录/锁/权限/探活逻辑并补缺口, 不因决定沿用就宣称代码已满足全部要求; 保留 PI_PRESENT_WEB_RUNTIME_DIR 测试隔离能力和现有 0700/0600 权限约束.

### D005 端口选择和重建策略保留宿主/容器区别
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 首次启动时, 宿主由代理在 49152-65534 选择端口, 被占则换端口, 最多 10 次, 不额外改成脚本自动选首次启动端口. 容器监听固定 8800, 沿用 --fixed-port, 被占报错不擅自换口. 复用已有存活实例时使用其实际端口, 不把新请求的端口当现有监听. status 重建先试原端口; 宿主普通实例原端口被占可换端口, 成功后原子更新 server.json 并报告/交付新的已确认 URL; 容器锁定实例不能换端口. 实际监听端口和宿主映射端口分开取得, 不混写. 理由: 宿主随机端口无需固定映射, 容器端口一换就与既有映射脱节. Q5=A, Q8=A.
- 依赖事实: F003, F005
- 预计影响: general/present/SKILL.md, general/present/REMOTE.md, general/present/scripts/web_server.py, general/present/tests/test_web_server_fixed_port.py, general/present/tests/test_web_server_lifecycle.py
- 需要调整: milestone-15 以实际记录和探活结果维护 URL; 本决策允许宿主重建后 URL 改变, 不把 milestone-17 的 navigate 地址稳定目标倒灌给 present.

### D006 服务不自行退出, 不承诺跨重启恢复
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: present 调用结束, 代理收工或会话断开都不停止服务; 不设空闲自动退出及其 TTL 环境变量语义. 主动关闭只走显式 stop, 系统重启/容器销毁也会终止服务, 不承诺跨这些生命周期恢复. status 只在运行时记录仍在且服务已死时按既有清单重建, 不新增系统服务或常驻监控器. stop 影响同 uid 共享实例的全部已挂载页面, 调用方须说明影响, 不在收工清理中执行. 理由: 用户明确要求长期运行, 并接受长期开放的后果; 不把常驻解释成跨系统重启持久化. Q5=A, Q6=A, Q7=A, Q10=A.
- 依赖事实: F003, F007
- 预计影响: general/present/SKILL.md, general/present/REMOTE.md, general/present/tests/test_web_server_lifecycle.py; 旧账本/规格的 TTL 叙述
- 需要调整: 当前代码已在 3dc49c6 删除空闲退出, 本轮只核实并记录, 不把已存在行为算作新实现. milestone-15 保护该行为, 不恢复旧 TTL 自退断言. test_web_server_lifecycle.py 的闲置存活测试仍注入已废弃变量, 见 F012; 这是防止旧自退行为复活的保护, 不应只为消除变量名就删掉有效行为检查, 可保留并澄清变量已无效. 系统临时目录被第三方清理造成记录丢失的旧限制仍保留, 不扩展成本次后台自愈项目.

### D007 接受无认证无 TLS 的长期局域网开放
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 宿主/容器都接受监听 0.0.0.0 的无认证无 TLS 展示服务; 同网段主体可读取全部已挂载目录, 不限当前页面, 旧内容会持续可读. 首次使用说明风险一次, 只挂愿意公开且供展示的目录, 不把仓库根目录或敏感目录整棵挂出, 不写密钥/登录态/无关内容. 保留管理接口仅本机可调用与目录越界防护, 不借开放内容放开管理接口. 不增加自动到期清理/认证/TLS. 理由: 用户明确接受长期开放, 以最少维护提供局域网直达展示, 用挂载内容范围守住暴露边界. Q6=A, Q10=A.
- 依赖事实: F001, F008, F013
- 预计影响: general/present/SKILL.md, general/present/REMOTE.md, general/present/tests/test_web_server_control_plane.py, general/present/tests/test_web_server_content.py; 若改 _Handler, 还须核对 workflow/to-spec/tests/test_ac_draft.py 的跨 skill 依赖 (F011)
- 需要调整: milestone-15 保留既有安全检查并验证未回退, 不因文件输出目录位于仓库内就整棵挂载仓库.

### D008 保留多目录扁平并集与显式 stop 的共享影响
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 继续通过 start 复用/add-dir 增挂目录, 同目录幂等; 多目录路径采用现有扁平并集, 同名文件返回先挂载者, 目录 listing 仍保留, 不新增每目录 URL 前缀. 页面用不重复的文件名, 保留既有按日期生成新文件不覆盖旧版本的规则. stop 关闭全部共用页面, 不是关闭某个页面. 本轮不新增 remove-dir 接口, 不把调用结束当撤挂授权. 理由: 用户选择保留已有目录语义, 不借交付方式改造重做命名空间. Q7=A, Q6=A.
- 依赖事实: F008
- 预计影响: general/present/SKILL.md, general/present/REMOTE.md, general/present/tests/test_web_server_content.py
- 需要调整: milestone-15 保留同名首挂载命中/幂等复用/挂载清单保序重建等既有行为, 并显式说明共享 stop 的影响.

### D009 新账本记录完整决策, 旧文保留历史并标明新适用范围
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 决策落在本文件, 不是续写旧 present-web-server 账本. 旧账本原文保留, 被取代条目标替代指针, 只有部分条款变化时保留其余部分效力并逐项指明新来源. 同步 docs/language/UBIQUITOUS_LANGUAGE.md, 对旧 ADR/规格补适用范围指针, 不改历史证据或将旧版本验收记录重写成新要求. 旧 PRODUCT.md/TECHNICAL.md 与执行输入受影响部分只标待 milestone-15 对齐, 未经核对不当作本轮权威判据. 理由: 新旧取舍必须可追溯, 后续实现不能同时消费相互矛盾的要求. Q9=A.
- 依赖事实: F001, F007, F008
- 预计影响: docs/changes/present-web-server/DECISIONS.md, PRODUCT.md, TECHNICAL.md, docs/language/UBIQUITOUS_LANGUAGE.md, docs/adr/0005-remote-present-via-resident-web-server.md
- 需要调整: milestone-15 准备当前已确认 PRODUCT/TECHNICAL/EXECUTION/issues 时使用本账本与 ACCEPTANCE.md AC-15, 不直接复用旧执行输入; 若缺编码前必需输入, 先按 drive-execution 规则准备, 不绕过缺口开始编码.

### D010 本节点关闭条件和后续实施标准已经确认
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: milestone-14 关闭条件是决策完整落盘/新旧规则可追溯/领域文档同步, 未参与盘问与落盘的独立子会话完成反方检查且所有发现经协调方核实处理, 涉及新增或改变决定的事项须再交用户. 标准逐项维护在 ACCEPTANCE.md AC-14, 后续实现标准在 AC-15; 不复制成第二套标准. Q10=A. 当前只处理文档/决策, 不改 present 实现或安装目录, 不运行同步; 不拿静态核对充当宿主/容器页面实测或 milestone-08 人工验收.
- 依赖事实: F009
- 预计影响: docs/changes/workflow-stack-review/ACCEPTANCE.md, 本目录反方报告/处理记录, roadmap/ROADMAP.json 的 milestone-14/15/17 上下文与 artifacts
- 需要调整: milestone-15 以已确认标准准备其执行输入, 若转入 PRODUCT.md 逐项对照既有标准, 不借转正擅改判据. milestone-13 仅把本账本作为交付规则参考, 不代替该节点未决产品选择.

### D011 明确宿主地址来源, 完整承接并替代 D003
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 本条完整替代 D003, 保留其已确认边界并补齐宿主地址来源. present 统一流程默认监听 0.0.0.0, start 的 --bind 必填接口不因此取消. 宿主本次调用明确指定的局域网地址优先; 否则复用宿主现有 records_root/lan-address 中已确认的地址, 不另造配置文件. 两者皆无时探测候选网卡地址, 请用户确认后使用, 不把候选/SSH_CONNECTION 第三字段/主机名/localhost 当成已确认可达地址交付. 容器仍使用已确认的 SWT_HOST_LAN_IP 和当前 8800 对应的宿主映射端口 SWT_HOST_WEB_PORT, 不原样交付服务自报的容器 IP/hostname/url. 容器缺值依当前环境说明先自查, 仍缺经可用信箱向创建容器的宿主会话索取, 信箱不可用才问用户, 不猜地址或映射. 地址/映射未确认时明确报告阻塞, 不用文件路径或 loopback 链接冒充交付. 已确认地址只解决地址来源, 不自动证明本次服务/端口能被用户设备访问, 实际访问证据按 AC-15 与 D012. 理由: 用户 Q11=A 选择与 swt 注入链同源的现有地址记录, 避免一台宿主维护两份不同的已确认地址; 原 Q3/Q10 约定的缺值出口与确认边界不变.
- 依赖事实: F002, F005, F010, F014, F015
- 预计影响: general/present/SKILL.md, general/present/REMOTE.md, general/present/scripts/web_server.py 的 _detect_lan_host/_url_host 与输出逻辑, general/present/tests/test_web_server_cli.py, general/present/tests/test_web_server_lifecycle.py 的 TC-027, general/present/tests/test_skill_contract.py
- 需要调整: milestone-15 必须修改 TC-027 对 SSH_CONNECTION 第三字段直接作为 URL/lan_ip 的旧断言, 不再以旧测试为新要求. 容器自查顺序沿用环境文档及 milestone-18 规则, 不改其生成器. 宿主读取现有地址文件的定位/接入实现由 milestone-15 准备执行输入时核实, 不另加新配置源; 容器识别沿用现有 /run/.containerenv 的配方, 不能再因 SSH 环境变量缺失而误走宿主端口规则.

### D012 明确两种环境分别提供实际访问证据
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 用户 Q12=A 明确确认 AC-15-07 中的证据展开要求: 宿主与容器两种场景分别留下真实局域网访问证据, 缺哪个场景就记未验证, 不以源码推断或仅容器本机测试代替宿主场景. 本条补明确认来源, 不将 Q10 原始清单伪称为逐字包含这段细则, 不改变其他已确认标准. 验收标准仍唯一维护在 ACCEPTANCE.md, 本条不宣称实际访问已经完成. 理由: 服务能启动不等于用户设备能打开, 两种环境的地址/映射不同, 不能以一种环境替另一种.
- 依赖事实: F015
- 预计影响: ACCEPTANCE.md AC-15-07 的确认依据, milestone-15 的执行输入与证据计划, milestone-08 的终点证据汇集
- 需要调整: milestone-15 准备验证入口时落到实际设备/确认动作, 缺环境应报告缺口, 不补写虚假通过; 本节点不自行补跑产品来制造后续实施证据.

## 事实

### F001 present 当前存在本地/远程两条流程
- 状态: 当前有效
- 来源: general/present/SKILL.md 的 选择模式/本地展示流程/页面状态要求, general/present/REMOTE.md; 本轮只读检查
- 内容: 旧主流程检测 SSH 变量, 本地用专用 browser_session.py 打开 Chromium 并回读状态, 交付绝对文件路径; 远程走 web, 仍要求状态对象但不回读. 失败出口仍交文件路径. 这些是待 milestone-15 改造的旧行为, 当前尚未实施 D001/D002/D003.

### F002 当前 URL 探测与目标存在差异
- 状态: 当前有效
- 来源: general/present/scripts/web_server.py 的 _detect_lan_host/_url_host; general/present/REMOTE.md 容器分支; docs/adr/0012-container-web-direct-access.md
- 内容: 脚本当前优先 SSH_CONNECTION 第三字段, 其次默认路由接口, 最后主机名/localhost. REMOTE.md 已区分容器视角地址与 SWT_HOST_LAN_IP, 但仍有宿主组装 URL 的旧配方. 不能据此声称当前宿主已按新规则交付确认的局域网地址.

### F003 运行时单例/端口记录/锁端口能力已经存在
- 状态: 当前有效
- 来源: general/present/scripts/web_server.py 的 _runtime_dir/_serve/run_start/run_status/_rebuild_spawn/_rebuild_status; tests/test_web_server_fixed_port.py
- 内容: 运行时目录采用 <系统临时目录>/pi-present-web-<uid>, PI_PRESENT_WEB_RUNTIME_DIR 可覆盖基目录. _serve 写 server.json 的 pid/port/bind/roots/started_at/fixed_port. 文件与探活共同用于复用/重建, 容器可 --fixed-port. 此处为源码核对, 不是本轮运行验证.

### F004 check_page.py 未强制状态对象
- 状态: 当前有效
- 来源: general/present/scripts/check_page.py 的 analyse/run_check, tests/test_skill_contract.py; 本轮 rg 检索 __PRESENTATION_STATE__/presentation_state/state_object
- 内容: 当前 check_page.py 未要求 __PRESENTATION_STATE__; 此要求位于 SKILL.md/REMOTE.md 与文本契约测试. 实施应按实际约束删改, 不为满足清单无意义修改检查器.

### F005 容器映射与两个服务的边界已有依据
- 状态: 当前有效
- 来源: docs/changes/agent-env-followups/DECISIONS.md D003/D004/D010/F015; docs/adr/0012-container-web-direct-access.md; 本轮 Q4/Q8
- 内容: 8800 归 present, 8801 起预留给 navigate 等不同服务; 宿主发布端口随容器创建动态分配. 已确认地址经 SWT_HOST_LAN_IP 注入, SWT_HOST_WEB_PORT 对应 8800. present 静态目录服务与 navigate 的动态路线图接口不是同一实例.

### F006 当前路线图稳定性工作由其他里程碑承接
- 状态: 当前有效
- 来源: 经守门脚本 query 的 workflow-stack-review 路线图 milestone-16/17 与 notes
- 内容: 已记录 navigate 主检出与测试检出共用运行时单例/默认端口造成误杀和固定桥失效; 修复归 milestone-17. 本节点不借共享格式要求合并两个服务的运行时身份, 不领取该实施工作.

### F007 空闲退出早已删除, 旧账本未完全同步
- 状态: 当前有效
- 来源: 提交 3dc49c679b6bfa6c66e25c0d125e106f887eed63 (Keep present and navigate web servers running until stopped), general/present/scripts/web_server.py 的 _serve; docs/changes/present-web-server/DECISIONS.md D014, TECHNICAL.md, docs/adr/0005-remote-present-via-resident-web-server.md
- 内容: 该提交已删除 present/navigate 的空闲退出实现, present 当前 _serve 直接 serve_forever, REMOTE.md 写持续运行到手动 stop. 旧 D014/规格/ADR 仍讲 24h TTL, 属历史冲突. 本轮未运行服务, 不将源码事实写成新行为测试通过.

### F008 旧安全/多目录规则的权威来源
- 状态: 当前有效
- 来源: docs/changes/present-web-server/DECISIONS.md D001/D002/D005/D006/D007/D008/D012/D020-D023, docs/adr/0006-flat-union-url-namespace.md; general/present/scripts/web_server.py
- 内容: 旧规则包含无认证无 TLS, 用户级单例, 挂载保序, 幂等增挂, 同名静默遮蔽, 目录 listing, 路径越界拒绝和本机管理接口. 新决策保留的内容见 D004/D007/D008, 不是假定旧规则全部都已满足新标准.

### F009 确认范围与验证边界
- 状态: 当前有效
- 来源: 本轮用户 Q1-Q6 全 A, Q7-Q10 全 A, 最后回复 "结束"; REQUIREMENTS.md
- 内容: 用户确认了规则与验收标准, 授权本节点落盘和独立反方检查. 未授权提前执行 milestone-15, 也未对其尚未实现的行为作验收通过确认. 本节点采用文档差异/链接/规则覆盖核对与独立反方验证, 不需要为未改的产品运行路径启动真实服务或跑整套 pytest.

### F010 生命周期测试仍钉住旧 SSH 地址优先级
- 状态: 当前有效
- 来源: general/present/tests/test_web_server_lifecycle.py 的 TestTC027HostFromSSHConnection/test_url_host_uses_ssh_connection_server_ip (本轮核对行 874-899); OPPOSITION.md A-01
- 内容: TC-027 注入 SSH_CONNECTION 并断言 url/lan_ip 直接取第三字段. 这是 D011 需要调整的实际旧测试, 初版 D003 预计影响未点名该文件, 本轮补记. 不在决策节点修改测试.

### F011 to-spec 直接依赖 present handler, 状态对象并非必须清理
- 状态: 当前有效
- 来源: workflow/to-spec/tests/test_ac_draft.py 的 test_preview_and_original_are_reachable_through_present_handler (本轮核对行 360-409), workflow/to-spec/ac-draft.py 和 tests/test_ac_reading.py; OPPOSITION.md A-02/C-09
- 内容: to-spec 测试直接 import present web_server.py 的 _Handler, 注入 roots/roots_lock/runtime_dir/bind 并用隔离 loopback HTTP 检查页面可访问. milestone-15 若触碰该类结构/目录服务行为, 相关用例应纳入直接相关回归, 不借此重构 to-spec. to-spec 自带状态对象不违背 D002 的取消强制要求, 不应为消除字符串而删除其合法交互/测试.

### F012 旧 TTL 变量仍作为闲置存活测试输入
- 状态: 当前有效
- 来源: general/present/tests/test_web_server_lifecycle.py 的 test_idle_server_stays_available_until_stop (本轮核对行 777-797); OPPOSITION.md A-03; 3dc49c6
- 内容: 测试设置 PI_PRESENT_WEB_TTL_SECONDS=0.2 后等待 1 秒并核对服务存活. 实现已不读取该变量, 因此这不是仍支持 TTL, 而是可用于防旧行为复活的输入. 原记录漏掉此位置属实; 不能据变量名命中就认定应删除有效的存活检查或要求恢复自退语义.

### F013 本机管理接口的实际来源规则含具体 bind 地址分支
- 状态: 当前有效
- 来源: general/present/scripts/web_server.py 的 _guard_control_namespace/_is_loopback_client (本轮核对行 499-539), docs/changes/present-web-server/UNAUTHORIZED_DECISIONS.md U-009, 提交 aa9a693; OPPOSITION.md A-04
- 内容: 实际守卫放行 loopback 来源或源 IP 等于服务绑定的具体本机地址, 其余拒绝, 允许具体 IP bind 时 CLI 从本机访问控制接口. 领域语言只写仅 loopback 落后于此规则, 应改为本机专用并指向 U-009. 本条记录旧规则而非新增安全放行, 不以只读核对声称重新完成安全实测.

### F014 宿主已有已确认地址文件, 无需新造来源
- 状态: 当前有效
- 来源: workflow/use-sandbox-worktree/scripts/swt.py 的 confirmed_lan_address_path/read_confirmed_lan_address (本轮核对行 661-672), docs/changes/agent-env-followups/DECISIONS.md D010; OPPOSITION.md B-05
- 内容: swt 已从 records_root/lan-address 读取已确认局域网地址, 容器 SWT_HOST_LAN_IP 源于这一宿主记录. 初版 D003 未明确接入何种宿主来源, 用户现已通过 Q11=A 选择复用, 决策见 D011.

### F015 反方后的两项新增确认
- 状态: 当前有效
- 来源: 本轮用户回复原文 Q11: A / Q12: A; REQUIREMENTS.md 的反方后补充确认
- 内容: 用户确认本次明确指定地址优先, 否则复用现有 lan-address, 不另建配置文件, 无值则探测候选并请用户确认; 同时明确确认宿主与容器分别提供真实局域网访问证据的标准展开. 这关闭 B-05/B-07 的确认缺口, 不代表实际行为已通过验收.
