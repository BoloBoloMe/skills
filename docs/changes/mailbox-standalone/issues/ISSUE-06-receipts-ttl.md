## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已实现

## 要构建什么
回执信 + 信件 TTL: (1) Letter 增 `expires_at` (缺省 ts+24h, serve env 可调), 清扫器到期丢弃; (2) 三种回执: 送达 (信进收件人本机队列) / 已读 (ack) / 失败 (TTL 到期丢弃), 由服务端内部注入, from=`mailbox@<hostname>`, type=notify, body JSON `{"receipt":...,"letter_id":...}`; (3) 失败回执确定性 id `<原id>.delivery-failed` (多节点同时超时 seen-id 去重只投一封), 送达/已读同理 `<原id>.delivered`/`.read`; (4) 回执不递归; (5) 取信脚本识别回执信: 自动 ack, 打印紧凑单行, 不呈现给 LLM 不走处理指引. 适合 AFK: 语义与 id 规则已定.

## 覆盖依据
- Product: `../PRODUCT.md`, AC-018, AC-019, AC-020, AC-037 (滞留丢弃行)
- Technical: `../TECHNICAL.md`, 模块接口 (信件 schema)/关键流程 (投递状态机)

## 相关决策
- `../DECISIONS.md`: D012, D013, D014

## 允许范围
- `workflow/mailbox/scripts/mailbox.py` (Letter, 路由, ack, 清扫, 取信呈现)
- `tests/test_mailbox_lease.py`, `test_mailbox_mesh.py` (或新 test_mailbox_receipts.py)

## 禁止范围
- 投递态 route 五态本体 (ISSUE-03 已做, 本 issue 复用其结构)
- pi 扩展侧降噪 (ISSUE-07)
- 物流查询接口 (NG-006)

## 代码定位提示
- mailbox.py: `Letter`/`from_dict`/`to_dict`, `Mailbox._route` (本机排队点), `ack`, `_retry_loop` (清扫器挂靠点), `cmd_fetch` 的拉窗门禁段 (回执紧凑打印先例: skipped 自动 ack 不呈现)
- 语义钉死: best-effort, 收到 = 确定发生, 缺席 = 未知

## TDD 切片
- TS-001:
  接缝: 双 Mailbox 内存互联.
  测试用例: TC-030.
  先写的失败测试: `test_delivered_receipt` — 信进收件人队列后, 发件人队列出现送达回执; 无此机制, 失败.
  最小绿色实现范围: _route 本机排队分支生成回执.
  不得测试: 回执内部字段以外的东西.
  覆盖: AC-018 (送达行).
- TS-002:
  接缝: ack.
  测试用例: TC-031.
  先写的失败测试: `test_read_receipt` — ack 后发件人收到已读回执; 失败.
  最小绿色实现范围: ack 成功分支生成回执.
  覆盖: AC-018 (已读行).
- TS-003:
  接缝: 时间注入 + 清扫器.
  测试用例: TC-032.
  先写的失败测试: `test_ttl_expiry_failed_receipt` — 超 24h 未送达被丢弃且发件人收到失败回执; 失败.
  最小绿色实现范围: expires_at + 清扫 + 失败回执.
  覆盖: AC-018 (失败行).
- TS-004:
  接缝: 多节点同时超时.
  测试用例: TC-033.
  先写的失败测试: `test_failed_receipt_dedup` — 两节点先后丢弃同一封信, 发件人只收一封; 失败.
  最小绿色实现范围: 确定性 id.
  覆盖: AC-019.
- TS-005:
  接缝: 回执信路由.
  测试用例: TC-034.
  先写的失败测试: `test_receipt_no_recursion` — 回执信完成投递后不产生新回执; 失败.
  最小绿色实现范围: 回执标记判定.
  覆盖: AC-020.
- TS-006:
  接缝: cmd_fetch 输出.
  测试用例: TC-035.
  先写的失败测试: `test_fetch_receipt_compact_line` — 回执信自动 ack 并打紧凑单行, 不输出处理指引; 现按普通信呈现, 失败.
  最小绿色实现范围: 取信侧回执分支.
  覆盖: AC-018 (呈现侧).
- TS-007:
  接缝: 日志捕获.
  测试用例: TC-036.
  先写的失败测试: `test_pending_drop_utc_log` — 滞留丢弃打 UTC 日志行; 失败.
  最小绿色实现范围: 清扫/丢弃点日志.
  覆盖: AC-037 (滞留丢弃行).
- TS-008:
  接缝: 文档 grep.
  测试用例: BR-004.
  先写的失败测试: `test_receipt_wording_in_docs` — reference/mailbox.md 含 "收到 = 确定发生, 缺席 = 未知"; 未写文档, 失败.
  最小绿色实现范围: 文档一句.
  覆盖: BR-004 (审计).

## 验证入口
`uv run pytest tests/ -k "receipt or ttl or lease" -q` 全绿.

## 风险提示
回执信本身也走洪泛, 注意 seen-id 与路由判定不破坏普通信; serve 重启丢 pending 时失败回执发不出 — 与全内存语义一致, 文档写明.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
回执种类/id 规则/呈现形态全部已定.

## 验收标准
- [ ] 三类回执按场景到达发件人
- [ ] 失败回执幂等, 回执不递归
- [ ] 取信侧回执紧凑单行不扰 LLM
- [ ] 滞留丢弃 UTC 日志
- [ ] 相关测试全绿

## 被阻塞于
- ISSUE-03, ISSUE-04
