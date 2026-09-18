## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已实现

## 要构建什么
birth 接线改造: swt.py birth 改连本机信箱 — session 注册 (<容器名>-<8hex>), 密钥申领, 新 env 变量 (SWT_MAILBOX_URL / SWT_SESSION_ID / SWT_SESSION_SIGNING_KEY / SWT_SESSION_RESPONSE_KEY), terminate 时 session 注销. 探测本机信箱 (探测不到降级 skipped 不阻断 birth). 适合 AFK: 接线协议与新 env 变量名已在 spec 定义.

## 覆盖依据
- Product: `docs/changes/swt-mailbox-mesh/PRODUCT.md`, AC-007, AC-008
- Technical: `docs/changes/swt-mailbox-mesh/TECHNICAL.md`, 接口契约 (环境变量/容器), 数据模型与状态

## 相关决策
- `docs/changes/swt-mailbox-mesh/DECISIONS.md`: D005, D013

## 允许范围
- 修改 workflow/use-sandbox-worktree/scripts/swt.py (birth/resume/terminate 的信箱接线)
- 新建 tests/test_swt_mailbox_birth.py

## 禁止范围
- 不得修改 swt-mailbox.py (只消费其 admin 端点)
- 不得实现跨机 ssh 申领 (D013: 全本机)
- 不得修改 pi/extensions/, agent-prompts/ (ISSUE-09)

## 代码定位提示
- swt.py 的 wire_container_mailbox 函数 (行 2251 起): 现有接线逻辑, 改为连本机信箱 admin (127.0.0.1:38416).
- swt.py 的 MAILBOX_ENV_URL/MAILBOX_ENV_KEY/MAILBOX_ENV_NAME 常量 (行 2178-2180): 替换为新 env 变量名.
- swt.py 的 probe_base_server (行 2198 起): 探测逻辑改为探测本机 38417-38426 + __identity__ 应答 "swt-mailbox".
- session 注册: admin POST /admin/sessions (无 body 时自动生成 id 和密钥对, 返回三元组).
- session id: birth 生成 <容器名>-<8hex随机>, admin 注册时传入 id 或让服务端生成.
- terminate: admin POST /admin/sessions/revoke {id}.
- 测试参考: tests/test_swt_birth_mailbox.py 现有形态 (mock admin 端点).

## TDD 切片

- TS-001:
  接缝: birth 后容器 env 中的信箱变量.
  测试用例: TC-001.
  先写的失败测试: test_birth_env_vars — mock 本机信箱 admin; birth 完成后容器 env 应含 SWT_MAILBOX_URL (host.containers.internal:38417+), SWT_SESSION_ID (<容器名>-<8hex>), SWT_SESSION_SIGNING_KEY, SWT_SESSION_RESPONSE_KEY.
  最小绿色实现范围: wire_container_mailbox 改造 → 探测 → admin 注册 → env 烘入.
  不得测试: env 烘入的 podman 调用细节 (mock).
  覆盖: AC-007.

- TS-002:
  接缝: 容器内用 env 凭证取信.
  测试用例: TC-002.
  先写的失败测试: test_container_fetch_with_env — 设置 SWT_MAILBOX_URL/SWT_SESSION_* env; 运行取信 CLI; 目标 session 收到投给它的信.
  最小绿色实现范围: swt-mailbox.py 的凭证探测逻辑已支持 env (ISSUE-01 建); 此处验证 birth 烘入的变量与取信 CLI 对得上.
  不得测试: 容器内的实际运行 (本机模拟).
  覆盖: AC-007.

- TS-003:
  接缝: 容器发信回归.
  测试用例: TC-003.
  先写的失败测试: test_container_send — 用 env 凭证 send 一封 notify; 目标 session poll 取到.
  最小绿色实现范围: send CLI 的 env 凭证探测路径 (ISSUE-04 建); 此处验证 birth 烘入变量与 send 对得上.
  不得测试: send 的 HTTP 细节.
  覆盖: AC-007.

- TS-004:
  接缝: terminate 后 session 不可取信.
  测试用例: TC-004.
  先写的失败测试: test_terminate_revokes_session — birth 注册 session; terminate; 该 session 的 poll 应被拒绝 (401/403).
  最小绿色实现范围: terminate 流程中加 admin revoke 调用.
  不得测试: revoke 的 HTTP 细节.
  覆盖: AC-008.

- TS-005:
  接缝: 信箱不在场时 birth 降级.
  测试用例: TC-005.
  先写的失败测试: test_birth_skips_when_no_mailbox — 本机信箱未启动; birth 应正常完成, runtime 记录 mailbox=skipped, 容器无信箱 env.
  最小绿色实现范围: probe 失败 → stderr 告警 → 跳过接线, 不阻断 birth.
  不得测试: 告警文案.
  覆盖: AC-007.

## 验证入口
```bash
cd /home/bolo/Workspace/skills
uv run pytest tests/test_swt_mailbox_birth.py -v
uv run pytest tests/test_swt_m04.py -v  # 既有回归不破坏
```

## 风险提示
- swt.py 是大文件 (2800+ 行), 只改 wire_container_mailbox 和相关常量/探测, 不动其他部分.
- 旧 env 变量名 (SWT_BASE_URL/SWT_MAILBOX_KEY/SWT_CONTAINER_NAME) 不再烘入; 但存量容器仍带旧变量, 由 ISSUE-09 的 "不追溯" 口径覆盖.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
新 env 变量名/session id 格式/降级行为均已在 spec 定义.

## 验收标准
- [ ] birth 后容器 env 含 4 个新变量, 取信 CLI 凭 env 可收信
- [ ] 容器凭 env 可 send, 目标 session 取到
- [ ] terminate 后 session 被 revoke, poll 拒绝
- [ ] 信箱不在场时 birth 正常完成, 信箱接线降级 skipped

## 被阻塞于
- ISSUE-01
