## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已实现

## 要构建什么
信箱从 use-sandbox-worktree 拆出为独立 skill `mailbox`: `workflow/mailbox/` (scripts/mailbox.py 由 swt-mailbox.py 改名, reference/mailbox.md 搬入, 新建 SKILL.md). 全部配置/运行时文件集中 `~/.agents/mailbox/`: config.json (原 mailbox.json) / neighbors.json / cli-state.json (原 mailbox-state.json) / state.json / server.db; 旧路径 (`~/.local/state/swt-mailbox/`, `~/.agents/sandbox-worktree/mailbox.json` 等) 首次运行自动迁移并提示. `__identity__` 服务名改 `mailbox`. 测试注入 env 改 `MAILBOX_*` 前缀; 容器契约 env (SWT_MAILBOX_URL/SWT_SESSION_*) 不变. `tests/test_swt_mailbox_*.py` 改名 `test_mailbox_*` 并改指新路径. use-sandbox-worktree 的 SKILL.md/agent-prompts 改指新 skill. 行为不变, 纯搬迁+迁移. 适合 AFK: 机械迁移, 决策已全部固化.

## 覆盖依据
- Product: `../PRODUCT.md`, AC-023, AC-024
- Technical: `../TECHNICAL.md`, 模块划分/模块接口 (CLI 面)

## 相关决策
- `../DECISIONS.md`: D001, D003, D010, D015

## 允许范围
- `workflow/mailbox/` (新建)
- `workflow/use-sandbox-worktree/`: SKILL.md, agent-prompts/, reference/mailbox.md (搬走)
- `tests/test_swt_mailbox_*.py` (改名+改指), `tests/conftest.py`

## 禁止范围
- swt.py 本体 (ISSUE-02 处理)
- 任何信箱协议/行为变更
- NG-007: 不留旧路径兼容 shim (迁移 ≠ shim)

## 代码定位提示
- 入口: `workflow/use-sandbox-worktree/scripts/swt-mailbox.py` (全文即搬迁对象); 路径函数 `state_path()`/`config_path()`/`neighbors_path()`/`cli_state_path()`/`_migrate_legacy_config()`
- 测试: `tests/test_swt_mailbox_*.py` 11 个, `tests/conftest.py`
- 阅读顺序: 先路径函数与迁移先例, 再 main() 子命令表, 再测试

## TDD 切片
- TS-001:
  接缝: 路径 env 覆盖 (MAILBOX_CONFIG/MAILBOX_STATE 等).
  测试用例: TC-001.
  先写的失败测试: `test_migrate_legacy_paths` — 旧路径放文件, 首次运行后文件在 `~/.agents/mailbox/` 且 stderr 有迁移提示; 当前代码无此迁移, 失败.
  最小绿色实现范围: 迁移函数 + 新路径默认值.
  不得测试: 内部函数调用次数.
  覆盖: AC-024.
- TS-002:
  接缝: 临时 HOME 端到端 (serve + send + fetch).
  测试用例: TC-002.
  先写的失败测试: `test_standalone_full_loop` — 临时 HOME 起 serve, 自注册 `<hostname>-host`, send/fetch 环回成功; 搬迁前无此测试形态.
  最小绿色实现范围: 搬迁后的脚本在独立 HOME 全流程可用.
  不得测试: 协议细节 (已有测试覆盖).
  覆盖: AC-023.
- TS-003:
  接缝: 源码文件读取.
  测试用例: TC-003 (BR-001).
  先写的失败测试: `test_pure_stdlib` — 扫描 mailbox.py 的 import, 出现第三方即失败; 新文件未建时失败.
  最小绿色实现范围: 扫描测试本身.
  覆盖: BR-001 (审计).
- TS-004:
  接缝: 临时目录落盘.
  测试用例: TC-004 (BR-002).
  先写的失败测试: `test_config_files_0600` — config.json/state.json 落盘权限 0600, 父目录 0700; 新路径逻辑未写时失败.
  最小绿色实现范围: 新路径 + write_json_0600 沿用.
  覆盖: BR-002 (审计).
- TS-005:
  接缝: auto_credential 命名函数.
  测试用例: TC-005 (BR-003).
  先写的失败测试: `test_session_id_no_network_address` — 生成的 session id 不含任何 IP 形态字符串; 搬迁后仍绿 (回归锚).
  最小绿色实现范围: 单测.
  覆盖: BR-003 (审计).

## 验证入口
`uv run pytest tests/ -k "mailbox or migrate or standalone" -q` 全绿; 手工: 本机跑一次迁移 (旧路径有文件) 确认提示与结果.

## 风险提示
迁移与已有 `_migrate_legacy_config` 老路径迁移叠加, 注意迁移顺序 (先老老路径再老路径); neighbors.json 与 server.db 的 neighbors 表合并逻辑不变.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
纯搬迁 + 迁移, 无产品/协议决策空间; AC-023/024 边界清晰.

## 验收标准
- [ ] `~/.agents/mailbox/` 集中全部配置/运行时文件, 旧路径自动迁移并提示
- [ ] 独立 skill 在无 swt 环境完成 serve/配置/投/取全流程
- [ ] `uv run pytest tests/ -q` 全绿, 无 test_swt_mailbox_ 残留引用
- [ ] use-sandbox-worktree 文档/母本改指 mailbox skill

## 被阻塞于
- 无
