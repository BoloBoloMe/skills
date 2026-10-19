# 账号备注台 Product Spec

## 背景

值班同学需要一个本地运维小工具: 管理账号与备注, 按共享配置导出记录, 查看保留期状态, 导出审计事件.

## 目标

- G-001: 临时账号与备注可以写入并复查.
- G-002: 共享配置开启后导出带扩展字段.
- G-003: 基础导出只含基础字段.
- G-004: 锁定账号的备注可以查看.
- G-005: 保留期到期后锁定账号自动解锁.
- G-006: 审计事件可以导出.

## 非目标

- NG-001: 不做多租户与远程同步. (理由: 只在本地测试实例上使用.)

## 业务规则

- BR-001: 导出的字段集合只由 config/shared.json 的 export_extra 决定. (审计)
- BR-002: 锁定账号的保留期由运营配置决定, 本 Product 没有给出具体期限.

## 验收标准

<!-- confirmed-flow: v1 -->
```gherkin
# language: zh-CN
功能: 账号备注台

@AC-001 @normal @G-001
场景: AC-001-1 临时账号与备注写入可复查
  假定 测试数据目录 runtime/data 已初始化且 tmp-verify-01 账号不存在
  当 验收者运行 `python3 app.py account-ensure tmp-verify-01 --data-dir runtime/data`
  而且 验收者运行 `python3 app.py note-put tmp-verify-01 n1 首条备注 --data-dir runtime/data`
  而且 验收者再次运行同一条 note-put 命令
  那么 两次 note-put 的退出码都是 0
  而且 `python3 app.py note-list tmp-verify-01 --data-dir runtime/data` 只有一行 `note id=n1 text=首条备注`

@AC-002 @normal @G-002
场景: AC-002-1 共享配置开启后导出含扩展字段
  假定 config/shared.json 里 export_extra 为 false
  当 验收者把 config/shared.json 的 export_extra 改为 true
  而且 验收者运行 `python3 app.py export --limit 2 --data-dir runtime/data`
  那么 每行导出记录含 `extra` 字段且退出码为 0

@AC-003 @normal @G-003
场景: AC-003-1 基础导出
  假定 测试数据目录 runtime/data 已初始化
  当 验收者运行 `python3 app.py export --limit 2 --data-dir runtime/data`
  那么 输出两行, 每行含 `id` 与 `name` 字段, 不含 `extra` 字段, 退出码为 0

@AC-004 @failure @G-004
场景: AC-004-1 锁定账号的备注可见
  假定 测试数据目录 runtime/data 已初始化, locked-user 有一条 id 为 n1 的备注
  当 验收者运行 `python3 app.py note-list locked-user --data-dir runtime/data`
  那么 输出含 `note id=n1`, 退出码为 0

@AC-005 @edge @G-005
场景: AC-005-1 保留期到期后自动解锁
  假定 locked-user 的保留期按运营配置已经到期
  当 验收者运行 `python3 app.py retention-status locked-user --data-dir runtime/data`
  那么 输出含 `state=unlocked` 且退出码为 0

@AC-006 @failure @G-006
场景: AC-006-1 审计事件导出
  假定 环境里已配置 AUDIT_TOKEN 且审计服务可用
  当 验收者运行 `python3 app.py audit-export --data-dir runtime/data`
  那么 输出最近 10 条事件且退出码为 0
```

## 决策引用

- 无.
