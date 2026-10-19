# BR-001 伙伴回执审计

性质: 当前观察, 独立验收者 B 本轮实际操作. 工作目录: `/tmp/orchestra-10/methods-red`.
判据只取 PRODUCT.md 的 confirmed-flow v1. 无旧观察, 不用实现者说明或作者自证, 未读产品代码推断结果.

原文: 伙伴复制与删除状态以伙伴服务回执为准, 本机 outbox 日志不能代替回执. (审计)

## 本轮实际 outbox 写入与快照

本轮唯一 init 于 `2026-10-19T16:20:01,143095741+00:00` 至 `2026-10-19T16:20:01,185978407+00:00` 执行, 退出码 0, 产生前两条 replicate 记录, 原件 `00-init.replication-log.jsonl`, 运行证据 `00-init.md`.

本轮 purge 于 `2026-10-19T16:21:58,976739901+00:00` 至 `2026-10-19T16:21:59,026295652+00:00` 执行, 退出码 0, 运行证据 `02-purge.md`. 操作后快照命令与记录:

完整命令:
```bash
cp -- runtime/data/outbox/replication-log.jsonl docs/changes/vault/evidence/r1-ea94082/verifier-b/05-after-purge.replication-log.jsonl
```
原始元数据:
```text
command: cp -- runtime/data/outbox/replication-log.jsonl docs/changes/vault/evidence/r1-ea94082/verifier-b/05-after-purge.replication-log.jsonl
start: 2026-10-19T16:21:59,107697301+00:00
end: 2026-10-19T16:21:59,111134009+00:00
exit_code: 0
```
原始 stdout:
空, 0 字节.
原始 stderr:
空, 0 字节.

复制所得 replication-log.jsonl 原始全文:
```jsonl
{"id": "r1", "action": "replicate", "delivered": true, "partner": "vault-partner"}
{"id": "r2", "action": "replicate", "delivered": true, "partner": "vault-partner"}
{"id": "r1", "action": "purge", "delivered": false, "partner": "vault-partner"}
```

条目字段逐条核对:

| 条目 | id | action | delivered | partner |
| --- | --- | --- | --- | --- |
| 1 | r1 | replicate | true | vault-partner |
| 2 | r2 | replicate | true | vault-partner |
| 3 | r1 | purge | false | vault-partner |

上述字段为本轮实际文件事实. 相比 init 后原件, purge 后有新增的第三条请求. 这部分是运行观察, 不是静态代码推断.

## 伙伴回执可得性

未获得伙伴服务实际回执, 因此无回执位置或正文可附. 查找命令, 时间, 原始输出和范围均在 `04-external-unreadable.md` 与对应原始文件: README 无地址/凭据/读取入口; 当前环境变量名未发现相关配置; 项目候选配置文件搜索为空; runtime/data 只有 records 与 outbox.

区别: outbox 是本机生成的请求/日志材料; 伙伴回执是实际伙伴服务对复制或删除状态的确认. 本机字段 `delivered: true` 不提供独立服务来源, 不能凭字段把 r1 复制状态判为已确认; `delivered: false` 也不能独立证明真实伙伴上的最终删除状态. 本轮没有任何伙伴实际回复可供对照.

## 审计结论

- 静态材料核对结果: README 描述以伙伴回执为准, 文字与 BR-001 一致. 这是静态文档核对, 不是运行行为通过.
- 运行材料核对结果: 本轮 init/purge 实际产生了上述 outbox; 只证明本机记录, 不证明伙伴复制或删除状态. 未观察到可供核验的真实回执, 不能验证运行时是否以真实回执为准.
- **BR-001: 未验证.** 缺实际伙伴服务连接配置/权限以及本轮 r1 复制与删除回执. 不把 outbox 代为回执判符合, 也不因缺服务材料判产品不符合.
