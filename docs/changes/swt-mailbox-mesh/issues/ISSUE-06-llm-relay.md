## 父级
- `../EXECUTION.md`

## 执行
- [x] 已实现

## 要构建什么
LLM 中转集成: Relay 类从 swt-base-server.py 搬迁到 swt-mailbox.py, serve --upstream 参数启用, 中转端口区间 38427-38436, relay_keys admin 管理, OpenAI 兼容端点. 适合 AFK: 中转协议/端口/管理接口沿用现有实现, 只换宿主.

## 覆盖依据
- Product: `docs/changes/swt-mailbox-mesh/PRODUCT.md`, AC-013 (容器 LLM 走本机中转)
- Technical: `docs/changes/swt-mailbox-mesh/TECHNICAL.md`, 接口契约 (中转面 HTTP 端点, serve 环境变量)

## 相关决策
- `docs/changes/swt-mailbox-mesh/DECISIONS.md`: D011

## 允许范围
- 修改 workflow/use-sandbox-worktree/scripts/swt-mailbox.py (Relay 类 + 中转端点)
- 新建 tests/test_swt_mailbox_relay.py

## 禁止范围
- 不得修改 swt.py, sync-to-pi.py, pi/extensions/, swt-base-server.py (旧文件在 ISSUE-09 删)
- 不得改变中转协议语义 (NG-006 精神: 既有行为保持)

## 代码定位提示
- swt-base-server.py 的 RelayStore 类 (行 458-556): key 管理/quota/用量/过期/吊销, 直接搬用.
- swt-base-server.py 的 handler 中 /v1/chat/completions 和 /v1/models 逻辑 (行 699-728): 搬用.
- serve 子命令: 加 --relay-port 参数 + SWT_UPSTREAM_BASE/SWT_UPSTREAM_KEY env 检测; 有上游配置才启动中转端口.
- 中转端口区间 38427-38436 首空闲, 独立于信箱端口.
- 测试: 用假上游 (本地 HTTP server 返回固定响应) 验证全链.

## TDD 切片

- TS-001:
  接缝: serve --upstream-base 后中转端口的 /v1/models.
  测试用例: TC-001.
  先写的失败测试: test_relay_models — serve 带上游配置启动; admin 发 relay key (限模型列表); GET /v1/models 应返回该模型列表.
  最小绿色实现范围: RelayStore + 中转 HTTP handler + relay key 校验.
  不得测试: 模型列表的排序.
  覆盖: AC-013.

- TS-002:
  接缝: POST /v1/chat/completions 全链.
  测试用例: TC-002.
  先写的失败测试: test_relay_chat — 用 relay key POST chat completion; 假上游收到请求并返回; 响应转回客户端.
  最小绿色实现范围: Bearer key 校验 → 上游转发 → 响应透传 (不支持 stream).
  不得测试: 上游请求的精确 body.
  覆盖: AC-013.

- TS-003:
  接缝: relay key 的 quota/吊销.
  测试用例: TC-003.
  先写的失败测试: test_relay_key_revocation — 发限额 key, 超额后请求被拒; 吊销 key 后请求被拒.
  最小绿色实现范围: RelayStore.check_key/acquire + admin revoke.
  不得测试: 用量计数的持久化格式.
  覆盖: AC-013.

## 验证入口
```bash
cd /home/bolo/Workspace/skills
uv run pytest tests/test_swt_mailbox_relay.py -v
```

## 风险提示
- 假上游测试: 本地起一个简单 HTTP server 返回固定 OpenAI 格式响应, 避免真实 API 调用.
- 中转与信箱在同一进程但不同端口: 确保互不干扰 (独立 ThreadingHTTPServer 实例).

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
中转协议/admin 接口/端口规则均已在现有代码和 spec 中定义, 本 issue 是搬迁不是新设计.

## 验收标准
- [ ] serve --upstream 启动中转端口; 无上游配置则跳过
- [ ] relay key 认证 + 模型白名单 + quota + 吊销
- [ ] POST /v1/chat/completions 请求转发上游, 响应透传, 不支持 stream
- [ ] 中转端口区间 38427-38436, 独立于信箱端口

## 被阻塞于
- ISSUE-01
