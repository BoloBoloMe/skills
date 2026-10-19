# AC-001-2 beta 实例状态页

- 判据原文: 假定 beta 在 127.0.0.1:18102 运行且 health 返回 `ok instance=beta`; 当运行 `python3 app.py status --port 18102`; 那么输出含 `instance=beta`, `state=ready`, `version=relay-v1` 且退出码 0.
- 材料类型: 当前观察.

## 前提核对 (health-pre.txt)

- 命令: `python3 app.py health --port 18102`
- 时间: 2026-10-19T22:15:08+08:00
- 输出: `ok instance=beta`, exit=0

## 被测命令

```
cd /tmp/orchestra-04/parallel
t0=$(date +%s%N)
python3 app.py status --port 18102
rc=$?
t1=$(date +%s%N)
```

- 执行时间: 2026-10-19T22:15:10+08:00
- 原始输出: out.txt
- 退出码: 0
- 耗时: 65 ms

## 输出核对

- 含 `instance=beta`: 是 (`<p>instance=beta</p>`)
- 含 `state=ready`: 是 (`<p>state=ready</p>`)
- 含 `version=relay-v1`: 是 (`<p>version=relay-v1</p>`)
- 退出码为 0: 是

## 结论: 通过
