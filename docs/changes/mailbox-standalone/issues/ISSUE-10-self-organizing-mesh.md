## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已实现

## 要构建什么
无感自组网 (M5): (1) 舰队密钥 `~/.agents/mailbox/fleet.key` (0600); (2) `join-fleet <老设备ssh地址>` — 新设备主动 ssh 拉取舰队密钥; (3) UDP 广播信标 (端口 38437, 载荷 地址/hostname/指纹), serve 周期收发; (4) `POST /mailbox/hello` 握手: 舰队密钥 HMAC 挑战应答互证, 通过后协商两两独立链路密钥自动建邻居 (同名 upsert, 复用 ISSUE-04); (5) 认证换址: 本机地址变化用旧链路密钥签名宣告, 邻居验签通过即更新; (6) 换址事件 UTC 日志行; (7) 无舰队密钥者一律拒入. 适合 AFK: 机制与端口已定.

## 覆盖依据
- Product: `../PRODUCT.md`, AC-031..AC-035, AC-037 (邻居换址行)
- Technical: `../TECHNICAL.md`, 模块接口 (自组网)/安全策略/关键流程 (自组网时序)

## 相关决策
- `../DECISIONS.md`: D016; ADR `docs/adr/0016-fleet-key-self-organizing-mesh.md`

## 允许范围
- `workflow/mailbox/scripts/mailbox.py` (信标/hello/换址/join-fleet)
- `workflow/mailbox/reference/mailbox.md` (自组网节)
- `tests/test_mailbox_mesh_auto.py` (新建)

## 禁止范围
- 零确认入群 (NG-009)
- 自动反向隧道 (缓)
- 舰队密钥轮换 (缓)
- 邻居健康检查自动暂停 (NG-004)

## 代码定位提示
- mailbox.py: `Neighbor` (ISSUE-04 后含 name), `_AdminHandler` 邻居端点 (复用语义), serve 启动 (信标线程挂靠), `sign()` 复用 HMAC
- join-fleet: subprocess ssh `cat ~/.agents/mailbox/fleet.key`, 写本地 0600
- 测试: 双 Mailbox 实例互联先例 (test_mailbox_mesh.py); 信标用注入 socket; 时间注入先例在 lease 测试

## TDD 切片
- TS-001:
  接缝: 信标 socket 注入 + hello 端点.
  测试用例: TC-051.
  先写的失败测试: `test_beacon_auto_neighbor` — 双实例互信标后自动互建邻居可互投; 机制不存在, 失败.
  最小绿色实现范围: 信标收发 + 握手 + 建邻居.
  不得测试: 信标编码内部格式.
  覆盖: AC-031.
- TS-002:
  接缝: hello 端点.
  测试用例: TC-052.
  先写的失败测试: `test_hello_rejects_without_fleet_key` — 无/错舰队密钥握手被拒, 邻居表不变; 失败.
  最小绿色实现范围: HMAC 挑战应答校验.
  覆盖: AC-032.
- TS-003:
  接缝: 换址宣告 (邻居间消息).
  测试用例: TC-053.
  先写的失败测试: `test_signed_address_update` — 旧链路密钥签名的换址宣告被接受, 邻居地址更新, 投递恢复; 失败.
  最小绿色实现范围: 宣告 + 验签 + upsert.
  覆盖: AC-033.
- TS-004:
  接缝: 同上 + 日志捕获.
  测试用例: TC-054.
  先写的失败测试: `test_forged_address_update_rejected_and_logged` — 签名无效拒更新且打 UTC 日志行; 失败.
  最小绿色实现范围: 验签失败分支 + 日志.
  覆盖: AC-034, AC-037 (邻居换址行).
- TS-005:
  接缝: 假 ssh 适配器.
  测试用例: TC-055.
  先写的失败测试: `test_join_fleet_pulls_key_over_ssh` — join-fleet 后本地 fleet.key 就位 0600; 子命令不存在, 失败.
  最小绿色实现范围: join-fleet 子命令.
  覆盖: AC-035.
- TS-006:
  接缝: 源码/权限扫描.
  测试用例: TC-056 (BR-009).
  先写的失败测试: `test_fleet_key_0600_ssh_only` — fleet.key 落盘 0600 且 join-fleet 实现仅经 ssh 传输; 失败.
  最小绿色实现范围: 断言.
  覆盖: BR-009 (审计).

## 验证入口
`uv run pytest tests/ -k "mesh_auto" -q` 全绿; 手工: office+yoga 各 serve, 同网段自动互发现互投; 换址愈合实测.

## 风险提示
信标只覆盖同网段 (广播不出网段) — 文档写明边界; 链路密钥协商经舰队密钥认证通道, 密钥本身不上 wire; 换址宣告须防重放 (时间窗签名沿用 ±5min).

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
端口/密钥分层/握手语义/拒绝策略全部已定.

## 验收标准
- [ ] 同网段已入群设备自动互发现互建邻居
- [ ] 无舰队密钥者入群被拒
- [ ] 认证换址自愈, 伪造被拒并记日志
- [ ] join-fleet 一次动作完成入群
- [ ] 相关测试全绿

## 被阻塞于
- ISSUE-04
