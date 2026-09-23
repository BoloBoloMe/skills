## 父级
- `../EXECUTION.md`

## 执行
- [x] 已实现

## 要构建什么
mailbox.py 新增机器子命令 `discover` / `register-session <id>` / `revoke-session <id>` (stdout JSON, exit 3 失败, 语义 = 现 swt.py 的 probe+admin 客户端); swt.py 删除自带信箱客户端实现 (MAILBOX_STATE_PATH/probe_mailbox/identity_probe/_admin_post/register_container_session/revoke_container_session 等 ~150 行), birth/terminate 改为 subprocess 调用上述子命令, 脚本路径经 `Path(__file__).resolve().parents[2] / "mailbox/scripts/mailbox.py"` 定位. 容器接线行为对外不变 (env 注入照旧). 适合 AFK: 契约已在 TECHNICAL 定义.

## 覆盖依据
- Product: `../PRODUCT.md`, AC-025, AC-026
- Technical: `../TECHNICAL.md`, 模块接口 (机器子命令)/接缝与适配器

## 相关决策
- `../DECISIONS.md`: D002, D003

## 允许范围
- `workflow/mailbox/scripts/mailbox.py` (新增子命令)
- `workflow/use-sandbox-worktree/scripts/swt.py` (删信箱实现, 改调用)
- `tests/test_mailbox_birth.py`, `tests/test_mailbox_cli_tools.py` 等相关测试

## 禁止范围
- 信箱协议端点本身
- 容器契约 env 名 (BR-005)
- 其他 swt 子命令行为

## 代码定位提示
- swt.py 信箱段: 2175-2360 行附近 (MAILBOX_* 常量到 revoke_container_session), birth 调用点 2878-2892, terminate 3542 附近
- mailbox.py: `main()` 子命令表, `http_post`, `bind_first_free`, admin handler
- 测试: `tests/test_mailbox_birth.py` (现 test_swt_mailbox_birth.py 改名后)

## TDD 切片
- TS-001:
  接缝: 机器子命令 JSON 输出 (subprocess).
  测试用例: TC-006.
  先写的失败测试: `test_discover_outputs_json` — 起临时 serve 后 `discover` 输出 port/admin_port/admin_token; 子命令不存在, 失败.
  最小绿色实现范围: discover 子命令 (状态文件验活 + 区间扫描兜底).
  不得测试: 内部探测顺序.
  覆盖: AC-026.
- TS-002:
  接缝: 同上.
  测试用例: TC-007.
  先写的失败测试: `test_register_and_revoke_session` — register-session 输出三元组, revoke 后可重复注销语义明确; 子命令不存在, 失败.
  最小绿色实现范围: 两个子命令经 admin 口.
  覆盖: AC-026.
- TS-003:
  接缝: swt.py → 子命令 (假脚本适配器).
  测试用例: TC-008.
  先写的失败测试: `test_birth_wires_via_subcommand` — birth 接线断言 subprocess 调用 discover/register-session 且 env 四元组烘入; 现为内部函数调用, 失败.
  最小绿色实现范围: wire_container_mailbox 改调子命令.
  不得测试: subprocess 具体参数拼写以外部行为为准.
  覆盖: AC-025.
- TS-004:
  接缝: 同上.
  测试用例: TC-009.
  先写的失败测试: `test_terminate_revokes_via_subcommand` — terminate 经子命令注销; 失败 (未实现).
  最小绿色实现范围: revoke_container_session 改调子命令.
  覆盖: AC-025.
- TS-005:
  接缝: 源码常量扫描.
  测试用例: TC-010 (BR-005).
  先写的失败测试: `test_container_env_names_unchanged` — swt.py/mailbox.py 中 SWT_MAILBOX_URL/SWT_SESSION_* 字面常量仍在; 删除实现时若误删则失败 (守护测试, 先红后绿).
  最小绿色实现范围: grep 断言.
  覆盖: BR-005 (审计).

## 验证入口
`uv run pytest tests/ -k "machine or birth or cli" -q` 全绿; 手工: 真机 birth 一个容器确认 env 注入与注销正常.

## 风险提示
子命令必须处理 serve 未起/旧状态文件失活 (exit 3 + stderr); swt.py 删除代码时注意别误删非信箱逻辑; birth 失败窗口 (注册成功但创建失败) 的 session 泄漏语义保持现状不扩大.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
契约/路径定位/exit code 已在 TECHNICAL 钉死, 无产品决策空间.

## 验收标准
- [ ] 三个机器子命令按契约工作 (JSON/exit 3)
- [ ] swt.py 无信箱客户端实现, birth/terminate 经子命令完成接线
- [ ] birth 信箱缺席仍只告警不阻断
- [ ] 相关测试全绿

## 被阻塞于
- ISSUE-01
