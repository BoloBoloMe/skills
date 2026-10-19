---
name: verify-board
description: 记录板项目本地验证配方: 启动实例后核对状态页与 report.
disable-model-invocation: true
---

# 记录板验证配方

## 启动实例

```bash
mkdir -p runtime/board
python3 app.py serve --port 18001 --data-root runtime/board &
python3 app.py health --port 18001
```

`/health` 返回 `ok instance=board` 表示实例可用.

## 核对状态页

```bash
python3 app.py status --port 18001
```

输出含 `instance=board` 与 `version=relay-v1` 即通过.

## 核对 report

```bash
python3 app.py report --port 18001
```

输出形如 `relay-report instance=board version=relay-v1` 即通过.

## 取证

把命令输出存到 `runtime/` 下. 结束时 `kill` 掉实例进程.
