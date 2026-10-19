# payout-service

订单写入服务. 金额解析使用 vendored 的 amountlib 2.4.0, 订单原文存放在
SQLite 的 orders.payload 列, 由另一个仓库的 Node 消费者读取.
