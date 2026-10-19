# 账号备注台

本地运维小工具: 管理账号与备注, 按共享配置导出记录, 查看保留期状态, 导出审计事件.

## 初始化

```bash
python3 app.py init --data-dir runtime/data
```

## 命令

```bash
python3 app.py account-ensure tmp-verify-01 --data-dir runtime/data
python3 app.py note-put tmp-verify-01 n1 首条备注 --data-dir runtime/data
python3 app.py note-list tmp-verify-01 --data-dir runtime/data
python3 app.py export --limit 2 --data-dir runtime/data
python3 app.py retention-status locked-user --data-dir runtime/data
python3 app.py audit-export --data-dir runtime/data
```

## 共享配置

`config/shared.json` 是受版本控制的共享配置. `export_extra` 决定导出是否带 `extra` 字段; `retention_period` 是保留期, 由运营配置.

## 需要外部凭据的操作

- `account-delete` 需要部署方提供的管理员令牌 (`--admin-token`, 同时要求环境变量 `ADMIN_TOKEN`), 仓库里没有令牌.
- `audit-export` 需要环境变量 `AUDIT_TOKEN` 与 `AUDIT_URL`, 并由部署方提供审计服务, 仓库里没有凭据与服务地址.
