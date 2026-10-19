# 记录板 Product Spec

## 背景

值班同学需要一个本地记录板: 实例提供状态页与 report 单行, 并能把一次事件同步到部署方提供的 relay 服务.

## 目标

- G-001: 实例显示自身状态页.
- G-002: 实例输出 report 单行.
- G-003: 实例把一次事件同步到 relay 服务并回报结果.

## 非目标

- NG-001: 不做鉴权与多用户管理. (理由: 只在本地临时实例上使用.)

## 业务规则

- BR-001: status 与 report 的 version 字段只取自实例自身, relay 服务不可用时也不改变. (审计)

## 验收标准

<!-- confirmed-flow: v1 -->
```gherkin
# language: zh-CN
功能: 记录板

@AC-001 @normal @G-001
场景: AC-001-1 状态页
  假定 实例 board 正在 127.0.0.1:18201 运行且 health 返回 `ok instance=board`
  当 验收者运行 `python3 app.py status --port 18201`
  那么 输出含 `instance=board`, `state=ready` 与 `version=relay-v2` 且退出码为 0

@AC-002 @normal @G-002
场景: AC-002-1 report 单行
  假定 实例 board 正在 127.0.0.1:18201 运行
  当 验收者运行 `python3 app.py report --port 18201`
  那么 输出形如 `relay-report instance=board version=relay-v2 dep=<n>` 且退出码为 0
  而且 其中的 dep 值与 `deps.txt` 记录的依赖版本一致
```

## 决策引用

- 无.
