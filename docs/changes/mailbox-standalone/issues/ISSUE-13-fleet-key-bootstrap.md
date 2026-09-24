## 父级
- `../EXECUTION.md`, `../DECISIONS.md` D020

## 执行
- [ ] 已实现

## 要构建什么
fleet.key 引导生成: cmd_serve 启动时, 若舰队密钥文件缺席且 MAILBOX_FLEET_KEY env 未设, 自动生成随机密钥 (如 os.urandom 32 字节 hex) 落盘到舰队密钥路径, 权限 0600 (父目录 0700), 打 UTC 日志行并在 stderr 提示; 文件已存在或 env 已设则完全照旧. 自生成密钥 = 自成单节点舰队: 信标照发, 异钥舰队握手仍拒 (语义与 NG-009 不变). reference/mailbox.md 自组网节补一句引导说明.

## 覆盖依据
- DECISIONS.md D020 (用户批准); BR-009 (0600 落盘); AC-032 (无对偶密钥仍拒入)

## 允许范围
- `workflow/mailbox/scripts/mailbox.py` (cmd_serve 启动段 + 舰队密钥 helper)
- `tests/test_mailbox_mesh_auto.py`
- `workflow/mailbox/reference/mailbox.md` (自组网节一句话)

## 禁止范围
- 密钥格式/协商公式 (ISSUE-10 已钉, 引导生成只是来源多一种)
- join-fleet 行为 (已有文件时照旧)
- 零确认入群 (NG-009): 生成不等于入群, 握手互证不变

## 代码定位提示
- mailbox.py: cmd_serve 启动段 (FleetBeacon 构造前), 舰队密钥读取 helper (MAILBOX_FLEET_KEY env → 文件)
- 测试: test_mailbox_mesh_auto.py; 注意 test_hello_rejects_without_fleet_key 等既有用例的 "无密钥" 前提需要重新审视 (现在无文件会自动生成): 用 MAILBOX_FLEET_KEY 显式控制测试前提, 不要删安全断言

## TDD 切片
- TS-001:
  接缝: 临时 HOME 落盘.
  先写的失败测试: test_serve_bootstraps_fleet_key — 空 HOME 起 serve 后 fleet.key 存在且 0600, 重启后内容不变 (复用不重新生成); 现缺席, 失败.
  最小绿色实现范围: 启动时生成 + 0600 + 幂等.
- TS-002:
  接缝: 同上 (安全语义回归).
  先写的失败测试或既有用例适配: MAILBOX_FLEET_KEY 未设且文件缺席时生成后, 异钥 hello 仍 403; 显式空 env 场景的信标行为按实现语义钉死并文档化 (若保留 "显式空 = 关信标" 需在测试与文档写明).

## 验证入口
/home/bolo/Workspace/skills/.venv/bin/python -m pytest tests/ -k "mesh_auto" -q -m "not e2e" 全绿; 全量快层无回归.

## 风险提示
生成用 os.urandom/secretse, 不用时间戳; 0600 + 父目录 0700 双断言 (BR-009 审计口径); 既有 "无密钥拒入" 断言一条都不能弱化.

## 停止条件
发现自动生成与 NG-009/BR-009 冲突, 或需要改握手公式时停止.

## 验收标准
- [ ] 首次 serve 自动生成 0600 舰队密钥并日志提示
- [ ] 重启复用不重生成
- [ ] 异钥拒入语义回归通过
- [ ] 相关测试全绿
