## 父级
- `../EXECUTION.md`

## 执行
- [x] 已实现

## 要构建什么
邻居与滞留可管可控: (1) admin 口邻居 GET (列出含状态) / DELETE / PATCH; 邻居加 `name` 字段, 同名 upsert 覆盖地址不累积; (2) 滞留信 `GET /admin/pending` (id/目标/邻居/最后错误/重试次数/年龄) + `POST /admin/pending/retry|drop`; 滞留上限缺省 100 (env 可调), 超限丢最老; (3) 邻居存储语义统一: admin 加的进 DB 持久, 文件加的只作启动种子, 文档写清; (4) 邻居转发失败/不可达打 UTC 时间戳日志行. 适合 AFK: 端点与语义已定.

## 覆盖依据
- Product: `../PRODUCT.md`, AC-011, AC-012, AC-013, AC-037 (邻居转发失败行)
- Technical: `../TECHNICAL.md`, 模块接口 (admin 口)/非功能要求

## 相关决策
- `../DECISIONS.md`: D011 (B1/B2/B4/B8)

## 允许范围
- `workflow/mailbox/scripts/mailbox.py` (Neighbor 结构, admin handler, 暂存重试)
- `workflow/mailbox/reference/mailbox.md` (存储语义文档)
- `tests/test_mailbox_admin.py`, `test_mailbox_mesh.py`

## 禁止范围
- 自组网换址宣告 (ISSUE-10)
- 信件 TTL (ISSUE-06); 本 issue 只做滞留**数量**上限
- 邻居健康检查自动暂停 (NG-004 缓)

## 代码定位提示
- mailbox.py: `Neighbor` 类, `Mailbox.add_neighbor`/`stage_forward`/`retry_pending`, `_AdminHandler` 的 `/admin/neighbors` 与 `/admin/stats`, serve 启动的邻居表合并 (cmd_serve 内 known 去重段)
- 测试: test_mailbox_admin.py 现成 admin 夹具

## TDD 切片
- TS-001:
  接缝: admin HTTP 端点.
  测试用例: TC-018.
  先写的失败测试: `test_neighbors_get_delete_patch` — 三端点工作; 现只有 POST add, 失败.
  最小绿色实现范围: 三端点 + DB 同步.
  不得测试: handler 内部拼装.
  覆盖: AC-011.
- TS-002:
  接缝: 同上.
  测试用例: TC-019.
  先写的失败测试: `test_neighbor_upsert_by_name` — 同名再登记覆盖地址不新增条目; 现按地址追加, 失败.
  最小绿色实现范围: Neighbor 加 name + upsert 语义.
  覆盖: AC-011 (同名再登记行).
- TS-003:
  接缝: admin pending 端点.
  测试用例: TC-020.
  先写的失败测试: `test_pending_list_fields` — 列出 id/to/邻居/最后错误/重试次数/年龄; 现只有计数, 失败.
  最小绿色实现范围: pending 结构丰富化 + GET.
  覆盖: AC-012 (列出行).
- TS-004:
  接缝: 同上.
  测试用例: TC-021.
  先写的失败测试: `test_pending_retry_and_drop`; 无端点, 失败.
  最小绿色实现范围: retry/drop 端点.
  覆盖: AC-012 (重投/丢弃行).
- TS-005:
  接缝: 暂存路径.
  测试用例: TC-022.
  先写的失败测试: `test_pending_cap_drops_oldest` — 超上限丢最老且 admin 可见; 现无限涨, 失败.
  最小绿色实现范围: 上限检查.
  覆盖: AC-013.
- TS-006:
  接缝: stderr/日志捕获.
  测试用例: TC-023.
  先写的失败测试: `test_neighbor_failure_utc_log` — 转发失败日志行含 UTC 时间戳; 现无日志, 失败.
  最小绿色实现范围: 关键事件日志行.
  覆盖: AC-037 (邻居转发失败行).

## 验证入口
`uv run pytest tests/ -k "admin or pending or neighbor" -q` 全绿; reference/mailbox.md 邻居节更新.

## 风险提示
Neighbor 结构变更影响 neighbors.json 与 DB 两行读取 (name 缺省兼容); pending 结构从 tuple 变记录, 影响 ISSUE-06 的 TTL 清扫衔接.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
端点/字段/上限默认值全部已定.

## 验收标准
- [ ] 邻居 GET/DELETE/PATCH + 同名 upsert
- [ ] 滞留列出/重投/丢弃 + 上限 100 丢最老
- [ ] 存储语义写进 reference/mailbox.md
- [ ] 邻居失败 UTC 日志行
- [ ] 相关测试全绿

## 被阻塞于
- ISSUE-01
