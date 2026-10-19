# AC-002-1 purge 操作与假定核对

性质: 当前观察, 独立验收者 B 本轮实际操作. 工作目录: `/tmp/orchestra-10/methods-red`.
判据只取 PRODUCT.md 的 confirmed-flow v1. 无旧观察, 不用实现者说明或作者自证, 未读产品代码推断结果.

## 场景假定

原文: 记录 r1 已经由伙伴服务复制到仓外存储.

本机 r1 存在的当前材料是 `00-init.records.jsonl` 和 `01-record-list.stdout.txt`. 两者只证实本机记录, 不证明伙伴复制. purge 前检查于 `2026-10-19T16:21:39,379985111+00:00` 完成, 原件见 `04-pre-purge-inspection.meta.txt`.

`04-pre-purge.replication-log.jsonl` 虽有 r1 的 `replicate` 与 `delivered: true`, 但这是本机 outbox, 按 BR-001 不能作为伙伴回执. README 文档核对, 当前进程环境变量名枚举, 项目配置路径查找与 runtime 文件枚举见 `04-external-unreadable.md`. 未得到伙伴服务地址, 凭据, 仓外存储读取入口或 r1 的真实复制回执.

**场景假定未验证.** 下面仍实跑本机部分, 不把它升级为完整场景通过. 本机操作严格在 record-list 成功之后执行.

## purge 原始运行记录

完整命令:
```bash
uv run python app.py record-purge r1 --data-dir runtime/data
```
原始元数据:
```text
command: uv run python app.py record-purge r1 --data-dir runtime/data
start: 2026-10-19T16:21:58,976739901+00:00
end: 2026-10-19T16:21:59,026295652+00:00
exit_code: 0
```
原始 stdout:
```text
purge-ok id=r1 local=removed partner-request=queued
```
原始 stderr:
空, 0 字节.

结论: 本机 purge 命令成功, 退出码 0. stdout 的 `partner-request=queued` 只表示本机声称已排入请求, 不表示伙伴落实删除. 后续本机 dump 见 `03-dump-after-purge.md`, 仓外证明见 `04-external-unreadable.md`. AC-002-1 总结论为未验证, 不是已发现产品实现缺陷.
