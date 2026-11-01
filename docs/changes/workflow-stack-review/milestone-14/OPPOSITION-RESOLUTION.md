# milestone-14 反方发现处理

原报告: [OPPOSITION.md](OPPOSITION.md), 审查 1dba5a2, 独立会话 01a19504-0d00-73e6-aff3-5e710c734306. 本记录由协调方逐项复核代码/文档后写入, 不把来信或报告直接当决定. 产品选择仍由用户裁决, 新增确认原文见 [REQUIREMENTS.md](REQUIREMENTS.md) Q11/Q12.

## A 类记录缺陷

| 项 | 核实结果与证据 | 处理 |
| --- | --- | --- |
| A-01 | 成立. test_web_server_lifecycle.py 的 TestTC027HostFromSSHConnection 直接断言 URL/lan_ip 使用 SSH_CONNECTION 第三字段, 初版 D003 预计影响漏记该测试. | F010 补记旧行为; 新 D011 预计影响/需要调整明确 TC-027. 留给 milestone-15 改测试, 本节点不改实现/测试. |
| A-02 | 跨 skill 依赖成立, 是否被本次改坏是条件性风险, 未运行不报坏. to-spec/tests/test_ac_draft.py 的 test_preview_and_original_are_reachable_through_present_handler 直接 import present._Handler 并注入类属性. | F011 记录, D007 预计影响补条件回归入口. milestone-15 若触碰 _Handler/目录服务相关行为, 将该测试纳入直接相关检查, 不扩大成重构 to-spec. |
| A-03 | 变量残留成立, 但仅凭变量名不能判测试错误. test_idle_server_stays_available_until_stop 设置 PI_PRESENT_WEB_TTL_SECONDS=0.2 后检查闲置仍存活, 本就可以防旧 TTL 复活; 实现已不读取它. | F012 补记, D006 需要调整澄清保留存活保护/可注明变量已废弃. 不采纳必须删除该注入的强解读, 依据是该用例确在验证 D006 所需行为; 不恢复旧自退测试. 这是记录澄清, 不是新增产品规则. |
| A-04 | 成立. 领域语言仅 loopback 简写漏掉 _guard_control_namespace 的源 IP == 具体 bind 地址分支, 有旧 U-009/aa9a693 依据. | F013 补记, 领域定义与示例改为本机专用并指向 U-009, 旧 D020 补适用说明. 不新增放行, 不声称本轮重做安全实测. |

## B 类疑点/缺口

| 项 | 核实结果与处理 |
| --- | --- |
| B-05 | 宿主地址来源留白成立. 已核对 swt.py confirmed_lan_address_path/read_confirmed_lan_address, 记录在 F014. 用户 Q11=A 选择本次明确指定地址优先, 否则复用现有 lan-address, 不另造配置源, 无值探测候选并请用户确认. 新 D011 完整替代 D003, 旧条保留原文且标替代, AC-15-01 同步. 不以反方推荐代替用户选择. |
| B-06 | 旧 REMOTE.md 明确 /run/.containerenv 触发容器配方. 原决定只取消 SSH 本地/远程分支, 没有取消宿主/容器端口区别. D011 需要调整显式记沿用该既有识别配方, 留 milestone-15 准备输入时核对, 不把它当新产品选择或新增环境适配工程. |
| B-07 | 初版 AC-15-07 的两环境分别留实际证据是协调方展开, Q10 原始清单未逐字包含. 已如实向用户复述这一点, 用户 Q12=A 明确确认. 新 D012 与 F015 记录确认来源, ACCEPTANCE.md 补确认依据, 不改写 Q10 原文或声称此前已经逐字批准. |
| B-08 | 本机监听/网卡探测不能证明用户设备可达, 疑点成立. Q11=A 已把无已确认地址时的核实动作明确为请用户确认候选后使用; Q12=A 仍要求实际访问证据. D011/D012 区分地址来源确认与本次页面真实访问. 具体设备/记录方式由 milestone-15 准备验证入口, 缺环境报缺口, 不提前制造运行证据. |

## C 类边界

- C-09: 接受为事实. to-spec 自带 __PRESENTATION_STATE__ 与 D002 不冲突, F011 明记不为清除字符串而改其合法页面/测试.
- C-10: 接受过渡边界. 当前 present 正文尚未实施新流程, 不能用本节点文档提交冒充运行结果; 实施归 milestone-15.
- C-11: 节点状态在独立复核完成前保持进行中. 收口补 artifacts/close_summary/status 均经守门脚本, 不直接读写 ROADMAP.json.
- C-12: 可追溯但粒度粗的描述已澄清. 旧 D013 适用注补明 URL 来源按 milestone-14 D011, 端口/重建按 D004/D005.

## 下游接口与执行输入

- 当前规则以 D001/D002/D004-D012 为准, D003 是被 D011 替代的历史. 标准唯一在 ACCEPTANCE.md AC-14/AC-15.
- milestone-15 须先有当前 PRODUCT/TECHNICAL/EXECUTION/issues. 已核对 drive-execution 步骤 2: 缺 EXECUTION 必须停止, 在另一个独立会话用 to-execution 准备, 不能领到编码节点后绕过输入缺口. 旧 present-web-server 的执行产物不直接复用. 已将该已知准备工作单列为 HITL task milestone-22, 阻塞于 milestone-14, 并让 milestone-15 和终点验收依赖它; 仅建索引, 本轮不领取/执行准备工作.
- 没有实现代码/测试改动, 不跑产品来补证据. 反方处理只证明决策与记录闭环, 不表示 AC-15 已通过或 milestone-08 已验收.

## 补核

本次修订将交原独立反方会话补核, 以另存 OPPOSITION-FOLLOWUP.md 的结果为准. 补核有未决项则 milestone-14 保持进行中.
