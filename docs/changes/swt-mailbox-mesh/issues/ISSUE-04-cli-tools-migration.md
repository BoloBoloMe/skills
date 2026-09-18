## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已实现

## 要构建什么
send/config/status CLI 与配置迁移: send 子命令 (凭证自动探测 容器 env / 设备 config), config set (密钥 stdin 交互), status (密钥脱敏前 8 位), 老路径 ~/.config/swt/mailbox.json 自动迁移. 适合 AFK: 全部参数与格式已在 spec 定义.

## 覆盖依据
- Product: `docs/changes/swt-mailbox-mesh/PRODUCT.md`, AC-006, AC-010
- Technical: `docs/changes/swt-mailbox-mesh/TECHNICAL.md`, 接口契约 (CLI), 配置文件/状态文件

## 相关决策
- `docs/changes/swt-mailbox-mesh/DECISIONS.md`: D001, D015

## 允许范围
- 修改 workflow/use-sandbox-worktree/scripts/swt-mailbox.py (CLI 子命令)
- 新建 tests/test_swt_mailbox_cli_tools.py

## 禁止范围
- 不得修改 swt.py, sync-to-pi.py, pi/extensions/
- 不得走命令行参数传密钥 (BR-006)
- 不得在 status 中亮密钥全文 (BR-006)

## 代码定位提示
- ISSUE-01 建立的凭证探测逻辑: send 复用同一探测 (env 优先 → config 文件).
- config set 的 stdin 交互: 用 getpass.getpass() (不回显) 读密钥值.
- 老路径迁移: 脚本启动时检查 Path.home()/".config/swt/mailbox.json" 存在且新路径缺失 → os.rename + stderr 提示一行.
- 文件权限: 配置文件写完后 os.chmod(0o600), 目录 os.chmod(0o700).

## TDD 切片

- TS-001:
  接缝: send 子命令的 HTTP 请求与目标信箱的 poll 响应.
  测试用例: TC-001.
  先写的失败测试: test_send_notify — 用设备凭证 send --to <已注册session> --type notify --body "测试"; 目标 session 的 poll 应取到该信.
  最小绿色实现范围: argparse send 子命令 + 凭证探测 + HMAC 签名 POST /mailbox/post.
  不得测试: HTTP 请求头细节.
  覆盖: AC-006.

- TS-002:
  接缝: config set 子命令对配置文件的修改.
  测试用例: TC-002.
  先写的失败测试: test_config_set_server — config set server http://...; 读配置文件验证 server 字段已更新.
  最小绿色实现范围: argparse config 子命令 + JSON 读写 + 0600 权限.
  不得测试: JSON 序列化格式.
  覆盖: AC-010.

- TS-003:
  接缝: config set 密钥项的 stdin 输入.
  测试用例: TC-003.
  先写的失败测试: test_config_set_secret_via_stdin — config set signing_key (不带值参数); 模拟 stdin 输入新值; 配置文件更新且命令行参数中不出现密钥值.
  最小绿色实现范围: getpass 读 stdin + 参数校验 (密钥项带值参数时报错拒绝).
  不得测试: getpass 的终端行为.
  覆盖: AC-010, BR-006.

- TS-004:
  接缝: status 子命令的 stdout.
  测试用例: TC-004.
  先写的失败测试: test_status_masked — status 输出含 session.id / server / signing_key 前 8 位 + "..." / response_key 前 8 位 + "..."; 不含完整密钥.
  最小绿色实现范围: 读配置 + 格式化输出 + 脱敏截断.
  不得测试: 输出的精确格式 (只断言关键子串和不含全文).
  覆盖: AC-010, BR-006.

- TS-005:
  接缝: 配置文件自动迁移.
  测试用例: TC-005.
  先写的失败测试: test_auto_migration — 在老路径写一个合法配置文件; 运行任意子命令; 新路径应存在该配置且老路径已移除; stderr 有迁移提示.
  最小绿色实现范围: 启动时路径检查 + os.rename + 提示.
  不得测试: 迁移提示的精确文案.
  覆盖: AC-010.

## 验证入口
```bash
cd /home/bolo/Workspace/skills
uv run pytest tests/test_swt_mailbox_cli_tools.py -v
```

## 风险提示
- 测试中配置路径: 全部用 env SWT_MAILBOX_CONFIG 指向 tmp_path, 不污染真实配置.
- getpass 在非终端环境 (CI) 的行为: 测试用 monkeypatch 替换 stdin.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
CLI 参数/文件路径/脱敏规则/迁移行为均已在 spec 精确定义.

## 验收标准
- [ ] send 投信到已注册 session, 目标 poll 取到
- [ ] config set server/device 走参数; signing_key/response_key 走 stdin 不回显
- [ ] status 输出密钥只显前 8 位
- [ ] 老路径配置自动迁移到新路径并提示
- [ ] 配置文件 0600, 目录 0700

## 被阻塞于
- ISSUE-01
