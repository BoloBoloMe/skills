# 事件仓 Product Spec

## 背景

团队需要一个小型事件仓: 记录事件, 删除事件, 生成导出文件, 并交由仓外伙伴服务复制和落实删除.

## 目标

- G-001: 导出 2 万行并给出可复核的性能结论.
- G-002: 删除记录后数据不可再被读取.
- G-003: 记录列表显示已有记录.

## 非目标

- NG-001: 不做仓外存储自己的管理界面. (理由: 仓外存储由部署方负责.)

## 业务规则

- BR-001: 伙伴复制与删除状态以伙伴服务回执为准, 本机 outbox 日志不能代替回执. (审计)

## 验收标准

<!-- confirmed-flow: v1 -->
```gherkin
# language: zh-CN
功能: 事件仓

@AC-001 @normal @G-001
场景: AC-001-1 导出性能结论
  假定 测试数据目录 runtime/data 已初始化
  当 验收者连续 5 次运行 `python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data` 并记录每次耗时
  那么 报告给出 p50 与极差, p50 不超过 800ms, 原始输出可复核

@AC-002 @failure @G-002
场景: AC-002-1 删除记录后数据不可再被读取
  假定 记录 r1 已经由伙伴服务复制到仓外存储
  当 验收者运行 `python3 app.py record-purge r1 --data-dir runtime/data`
  那么 本机 `python3 app.py record-dump r1 --data-dir runtime/data` 显示记录不存在
  而且 能证明仓外副本已按删除要求不可读取

@AC-003 @normal @G-003
场景: AC-003-1 记录列表
  假定 测试数据目录 runtime/data 已初始化
  当 验收者运行 `python3 app.py record-list --data-dir runtime/data`
  那么 输出含 `id=r1` 与 `text=alpha`, 退出码为 0
```

## 决策引用

- 无.
