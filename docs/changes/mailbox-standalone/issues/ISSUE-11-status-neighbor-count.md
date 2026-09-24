## 父级
- `../EXECUTION.md`, `../DECISIONS.md` D018

## 执行
- [x] 已实现

## 要构建什么
cmd_status 输出补邻居数: 验活成功后, 若本机能拿到 admin 面 (state.json 提供端口与 token, 即 host 场景) 则经 GET /admin/neighbors 取计数, 输出行含 `邻居数 = N`; 拿不到 admin 面 (容器 env 凭证场景) 输出 `邻居数 = 未知`, 不报错不拖慢 (admin 探测设短超时). pi 扩展 /mail 转呈 status 全输出, 无需改动即可显示; 若核实 /mail 有过滤行的逻辑则同步放开 (pi-extension/index.ts 在允许范围兜底).

## 覆盖依据
- DECISIONS.md D018 (用户批准); PRODUCT.md D006/D011-C5 对应意图

## 允许范围
- `workflow/mailbox/scripts/mailbox.py` (cmd_status + 本地 admin 探测 helper)
- `tests/test_mailbox_queued.py` 或 `tests/test_mailbox_cli.py` (status 测试所在文件)
- `workflow/mailbox/pi-extension/index.ts` (仅当 /mail 有行过滤时最小放开)

## 禁止范围
- admin 口暴露面/端点本身 (只从 localhost 消费既有 GET /admin/neighbors)
- 邻居管理端点语义 (ISSUE-04 已定)
- 其他 status 输出格式重排 (既有行保持)

## 代码定位提示
- mailbox.py: cmd_status (ISSUE-05 重写后), discover 的 state.json 读取 (admin_port/admin_token 来源先例), _AdminHandler GET /admin/neighbors
- 测试: test_mailbox_queued.py 的 status/queued 夹具, test_mailbox_cli.py 的 cli_env

## TDD 切片
- TS-001:
  接缝: status stdout.
  测试用例: 无编号 (D018 补充, 已获用户批准).
  先写的失败测试: test_status_reports_neighbor_count — 临时 HOME 起 serve, admin 加 2 个邻居, status 输出含 邻居数 = 2; 现无此行, 失败.
  最小绿色实现范围: status 的 admin 探测 + 计数行.
  覆盖: D018.
- TS-002:
  接缝: 同上 (容器形态).
  先写的失败测试: test_status_neighbor_count_unknown_without_admin — 仅 env 凭证无 state.json 时输出 邻居数 = 未知 且不报错; 现无此行, 失败.
  最小绿色实现范围: 未知分支.

## 验证入口
/home/bolo/Workspace/skills/.venv/bin/python -m pytest tests/ -k "status or queued" -q -m "not e2e" 全绿; 全量快层无回归.

## 风险提示
admin 探测不得拖慢 status (短超时, 失败即未知); 不要为拿计数扩大 admin 口暴露面; 环境隔离全用临时 HOME.

## 停止条件
需要改变 D018 或发现 spec 与代码事实冲突时停止.

## 验收标准
- [ ] host 场景 status 显示真实邻居数
- [ ] 容器场景显示未知不报错
- [ ] /mail (pi 扩展) 能看到该项
- [ ] 相关测试全绿
