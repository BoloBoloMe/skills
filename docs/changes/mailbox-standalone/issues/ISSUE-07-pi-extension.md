## 父级
- `../EXECUTION.md`

## 执行
- [x] 已实现

## 要构建什么
pi 扩展 (mailbox skill 内 `pi-extension/index.ts`) + 装载链路: (1) 三命令 `/mail` (总览: serve 活否/配置/邻居数/待取数) `/mail-listen start|stop|status` `/mail-send` (缺参交互补全); (2) 取信守护: 后台循环子进程调取信脚本逐封取, 来信 `pi.sendUserMessage(deliverAs:"followUp", triggerTurn:true)` 注入, `agent_settled` 后取下一封; 不阻塞前台; (3) 回执信识别标记后不注入, 汇入 /mail 总览与 widget; (4) `listen.json` 状态落盘, `session_start` 自动恢复, 多会话 listen 软提示不拦截; (5) 取信脚本加 `--cli-state <路径>` (env `MAILBOX_CLI_STATE` 同义), 扩展守护用专属路径修 pending_ack 竞态; (6) sync-to-pi.py 合并 settings.json `extensions` 数组 (幂等, 写前 .bak). 扩展只调脚本, 禁止重实现. 部分 HITL: pi TUI 内行为走人工验证清单, 无测试基建.

## 覆盖依据
- Product: `../PRODUCT.md`, AC-001, AC-002, AC-003, AC-004, AC-005
- Technical: `../TECHNICAL.md`, 模块接口 (pi 扩展/取信 CLI)/接缝与适配器

## 相关决策
- `../DECISIONS.md`: D004, D005, D006, D007, D008, D009, D014

## 允许范围
- `workflow/mailbox/pi-extension/` (新建)
- `workflow/mailbox/scripts/mailbox.py` (仅 --cli-state 参数)
- `sync-to-pi.py` (settings.json 合并)
- `tests/test_sync_to_pi.py`, 取信 CLI 测试

## 禁止范围
- 扩展内任何协议重实现 (BR-007): 签名/轮询/回执一律调脚本
- `pi/extensions/` 目录
- 注册 LLM 工具 (D006)

## 代码定位提示
- 扩展示例: pi 官方 examples/extensions/ (send-user-message.ts 等); API: `pi.registerCommand`, `pi.sendUserMessage`, `agent_settled`, `session_start`/`session_shutdown`, `ctx.ui.notify/setWidget`
- mailbox.py: `cmd_fetch` 尾部 (cli-state 读写点), `cli_state_path()`
- sync-to-pi.py: `_merge_models` 先例 (合并+备份)

## TDD 切片
- TS-001:
  接缝: 取信脚本 --cli-state.
  测试用例: TC-037 的前置自动化部分.
  先写的失败测试: `test_fetch_cli_state_override` — `--cli-state` 指定路径时 pending_ack/seen_ids 落该文件; 参数不存在, 失败.
  最小绿色实现范围: 参数 + 路径替换.
  覆盖: AC-001 (底层依赖, D009).
- TS-002:
  接缝: sync-to-pi.py settings.json 合并.
  测试用例: TC-042.
  先写的失败测试: `test_merge_extensions_idempotent` — 合并 extensions 数组, 重复运行不重复追加, 写前 .bak; 功能不存在, 失败.
  最小绿色实现范围: 合并函数 + 主流程挂载.
  覆盖: AC-001..AC-005 的装载前提.
- TS-003:
  接缝: 扩展源码扫描.
  测试用例: TC-043 (BR-007).
  先写的失败测试: `test_extension_pure_connector` — 扫描 index.ts 不含签名/协议实现 (只允许 spawn 脚本), 扩展未写时失败.
  最小绿色实现范围: 扫描断言.
  覆盖: BR-007 (审计).
- TS-004 (人工验证, 不进 pytest):
  测试用例: TC-037..TC-041 — pi 中 `/mail-listen start` → 投信 → 注入唤醒 (AC-001); agent 忙时排队 (AC-002); pi 重启自动恢复 (AC-003); 双会话软提示 (AC-004); 回执信不唤醒只入总览 (AC-005).
  覆盖: AC-001..AC-005.

## 验证入口
`uv run pytest tests/ -k "sync_to_pi or cli" -q` 全绿; 人工验证清单: sync 后 pi 内三命令可用, 来信注入唤醒, 回执不唤醒, 重启恢复, 双 listen 软提示.

## 风险提示
后台子进程生命周期: session_shutdown 必须杀干净; 取信脚本阻塞中 stop 要立即生效 (kill); followUp 注入失败时守护不退, 记状态.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
命令面/注入参数/状态文件位置全部已定; 仅 pi TUI 内观感需人工确认.

## 验收标准
- [ ] 三命令可用, 底层全部调脚本
- [ ] 来信 followUp 注入唤醒, settled 后取下一封
- [ ] 回执不唤醒, 汇入 /mail 与 widget
- [ ] listen.json 自动恢复, 多 listen 软提示
- [ ] sync-to-pi.py 幂等合并 settings.json
- [ ] --cli-state 生效
- [ ] 自动化测试全绿 + 人工清单通过

## 被阻塞于
- ISSUE-05, ISSUE-06
