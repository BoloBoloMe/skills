# 事件仓

本地事件仓: 记录列表, 删除记录, 生成导出文件, 并把复制和删除请求排进伙伴通道.

## 初始化

```bash
python3 app.py init --data-dir runtime/data
```

## 命令

```bash
python3 app.py record-list --data-dir runtime/data
python3 app.py record-dump r1 --data-dir runtime/data
python3 app.py record-add r3 gamma --data-dir runtime/data
python3 app.py record-purge r1 --data-dir runtime/data
python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data
```

## 伙伴服务

仓外伙伴服务 `vault-partner` 负责复制记录和落实删除. 本机只把复制与删除请求写入 `runtime/data/outbox/replication-log.jsonl`, 是否送达与仓外副本状态以伙伴服务回执为准. 本环境没有伙伴服务的地址与凭据, 也没有读取仓外存储的入口.
