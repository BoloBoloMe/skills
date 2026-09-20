## 父级
- `../EXECUTION.md`

## 执行
- [x] 已实现

## 要构建什么
mesh 邻居路由与洪泛转发: Neighbor 类, 邻居表配置 (neighbors.json), forward 端点 (邻居密钥认证), 洪泛路由 (查 sessions → 没找到转发所有邻居, 排除来源, seen-id 防环), 邻居不可达内存暂存重试, 三实例 e2e 测试. 适合 AFK: 路由规则/防环/暂存行为均已在 spec 定义.

## 覆盖依据
- Product: `docs/changes/swt-mailbox-mesh/PRODUCT.md`, AC-013
- Technical: `docs/changes/swt-mailbox-mesh/TECHNICAL.md`, 架构与组件 (信箱间路由), 接口契约 (forward 端点), 数据模型与状态 (邻居转发状态机)

## 相关决策
- `docs/changes/swt-mailbox-mesh/DECISIONS.md`: D007, D008, D020

## 允许范围
- 修改 workflow/use-sandbox-worktree/scripts/swt-mailbox.py (Neighbor/Mailbox 类, forward 端点, serve 邻居加载)
- 修改 tests/test_swt_mailbox_core.py (如需调整 fixture)
- 新建 tests/test_swt_mailbox_mesh.py

## 禁止范围
- 不得修改 swt.py, sync-to-pi.py, pi/extensions/
- 不得引入信件持久化 (NG-009: 邻居暂存只在内存)
- 不得实现 LLM 中转/birth 接线

## 代码定位提示
- ISSUE-01 建立的 Mailbox 类: 加 neighbors 字段 (list[Neighbor]) + pending_forwards 字段.
- ISSUE-01 建立的 post handler: 在 "查 sessions 没找到" 处加洪泛转发分支.
- forward 端点: 新增 POST /mailbox/forward, 校验 neighbor_key (与邻居表比对).
- 邻居表: serve 启动时从 ~/.agents/sandbox-worktree/neighbors.json 加载; admin POST /admin/neighbors 可增删.
- 暂存重试: 后台线程定期尝试 pending_forwards 中的信, 邻居可达时发出并移除.
- 三实例测试: 在同一测试进程中起 3 个 serve (不同端口), 配置彼此为邻居.

## TDD 切片

- TS-001:
  接缝: forward 端点的 neighbor_key 认证.
  测试用例: TC-001.
  先写的失败测试: test_forward_auth — 用正确 neighbor_key POST forward 成功; 用错误 key 返回 403.
  最小绿色实现范围: Neighbor 类 + neighbors 表加载 + forward handler 密钥校验.
  不得测试: 邻居表的存储格式.
  覆盖: AC-013.

- TS-002:
  接缝: 本机投信 + 非本机收件人触发转发.
  测试用例: TC-002.
  先写的失败测试: test_flood_to_neighbor — 两实例 A/B 互为邻居; A 上 post 信给 B 的 session; B 的 poll 应取到该信.
  最小绿色实现范围: post handler 查 sessions 没找到 → HTTP POST forward 给每个邻居 → B 收到后查 sessions 找到 → 排队.
  不得测试: 转发的 HTTP 请求头.
  覆盖: AC-013.

- TS-003:
  接缝: seen-id 防洪泛循环.
  测试用例: TC-003.
  先写的失败测试: test_seen_id_prevents_loop — 三实例 A/B/C 互为邻居; A post 给不存在的 session; 信应在 A→B→C 后停止 (C 不再转回 A), 不产生无限循环.
  最小绿色实现范围: forward handler 查 seen_ids; 已见 → 丢弃返回 ok.
  不得测试: seen_ids 的容量上限.
  覆盖: AC-013.

- TS-004:
  接缝: 来源邻居排除.
  测试用例: TC-004.
  先写的失败测试: test_exclude_source_neighbor — A 收到 B 转发的信 (非本机收件人); A 只转发给 C 不转发回 B.
  最小绿色实现范围: forward handler 记录来源地址, 转发时排除.
  不得测试: 来源地址的解析方式.
  覆盖: AC-013.

- TS-005:
  接缝: 邻居不可达时的内存暂存与恢复后重发.
  测试用例: TC-005.
  先写的失败测试: test_pending_forward_retry — A 的邻居 B 已停止; A post 给 B 的 session → 转发失败进暂存; 启动 B → 重试线程发出 → B 的 poll 取到.
  最小绿色实现范围: pending_forwards list + 后台定时重试线程.
  不得测试: 重试间隔.
  覆盖: AC-013.

- TS-006:
  接缝: 三实例 mesh e2e — 跨机直达 + 回信 + 自愈.
  测试用例: TC-006.
  先写的失败测试: test_mesh_e2e — 三实例 A/B/C; A 的容器 session 发信给 C 的设备 session → C 取到; C 回信给 A 的容器 session → A 取到; 停止 B → A/C 间通信仍正常 (直达邻居).
  最小绿色实现范围: 整合以上所有机制.
  不得测试: 投递延迟的精确值.
  覆盖: AC-013.

## 验证入口
```bash
cd /home/bolo/Workspace/skills
uv run pytest tests/test_swt_mailbox_mesh.py -v
```

## 风险提示
- 三实例测试的端口管理: 每个实例用独立 --port 起点, 测试结束清理.
- 转发超时: HTTP 请求设合理 timeout (5s), 避免一个邻居挂起阻塞 post 响应.
- 线程安全: pending_forwards 的增删需要锁 (与 serve 的请求处理线程并发).

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
路由规则/防环机制/暂存行为/邻居表格式均已在 spec 精确定义.

## 验收标准
- [ ] 邻居 key 认证 forward; 错误 key 403
- [ ] 非本机收件人的信洪泛转发到邻居, 目标信箱排队
- [ ] seen-id 防循环: 不存在收件人的信洪泛后停止
- [ ] 转发排除来源邻居
- [ ] 邻居不可达时内存暂存, 恢复后自动重发
- [ ] 三实例 e2e: 跨机投递 + 回信 + 中间节点关机不影响直达
- [ ] serve 重启后暂存清空 (NG-009)

## 被阻塞于
- ISSUE-01
