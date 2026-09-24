## 父级
- `../EXECUTION.md`

## 执行
- [x] 已实现

## 要构建什么
容器集成: (1) birth 把宿主端口映射 (ssh/web/vnc) 与显示直通状态 (`HOST_DISPLAY=ok/degraded/absent`) 烘进容器 env (或只读文件), 容器内不再发信问 host; (2) 信箱口新增 `GET /mailbox/sessions` 只读端点 (session 签名认证, 回 id+last_poll, 不泄密钥). 适合 AFK: env 清单与端点契约已定.

## 覆盖依据
- Product: `../PRODUCT.md`, AC-027, AC-028
- Technical: `../TECHNICAL.md`, 模块接口 (信箱口)/安全策略

## 相关决策
- `../DECISIONS.md`: D011 (G1/G2/G3)

## 允许范围
- `workflow/use-sandbox-worktree/scripts/swt.py` (birth env 注入段)
- `workflow/mailbox/scripts/mailbox.py` (sessions 端点)
- `tests/test_mailbox_birth.py`, handler 级测试

## 禁止范围
- 容器契约 env 既有名 (BR-005): 只新增, 不改名
- admin 口暴露面不扩大 (端点在信箱口不在 admin 口)
- 邻居拓扑快照进容器 (C3 推测项, 未批准)

## 代码定位提示
- swt.py: birth env 组装 (wire_container_mailbox 附近与 env.conf 注入段), STATE 容器记录的端口字段
- mailbox.py: `_Handler.do_GET` (现 __identity__ 一处), `_verify` 签名复用
- 测试: test_mailbox_birth.py 夹具

## TDD 切片
- TS-001:
  接缝: birth env 字典.
  测试用例: TC-044.
  先写的失败测试: `test_birth_injects_host_ports_and_display` — env 含 ssh/web/vnc 端口与 HOST_DISPLAY; 现无, 失败.
  最小绿色实现范围: birth env 组装扩展.
  覆盖: AC-027.
- TS-002:
  接缝: `/mailbox/sessions` handler.
  测试用例: TC-045.
  先写的失败测试: `test_sessions_requires_signature` — 无签名 403; 端点不存在, 失败.
  最小绿色实现范围: 端点 + 验签.
  覆盖: AC-028 (无签名行).
- TS-003:
  接缝: 同上.
  测试用例: TC-046.
  先写的失败测试: `test_sessions_lists_without_secrets` — 合法签名返回 id+last_poll 且响应不含任何密钥字段; 失败.
  最小绿色实现范围: 列表序列化白名单字段.
  覆盖: AC-028 (合法签名行).

## 验证入口
`uv run pytest tests/ -k "birth or sessions" -q` 全绿.

## 风险提示
sessions 端点在信箱口 (0.0.0.0), 必须验签且不泄密钥; birth env 注入失败沿用 "告警不阻断" 口径.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
env 清单/端点契约/脱敏口径已定.

## 验收标准
- [ ] 容器内 env 可见宿主端口与 HOST_DISPLAY
- [ ] sessions 端点签名认证, 列表不泄密钥
- [ ] 相关测试全绿

## 被阻塞于
- ISSUE-02
