# AC-005-1 beta 侧材料 (同一实例同一版本的截图与 report)

- 用途: 供第 8 项 (AC-005-1) 核对两侧 screenshot/report 一致性时引用 beta 侧原件.
- 材料类型: 当前观察.
- 产出时间: 2026-10-19T22:15:20 ~ 22:15:22 +08:00 (report 与截图都在这个窗口内, 实例未重启).

## beta 实例身份

- PID 4090715, 启动 2026-10-19T22:15:03+08:00
- 命令行: `python3 app.py serve --port 18102 --instance beta --data-dir runtime/beta --shared-dir runtime/shared`
- health: `ok instance=beta`

## report 原始输出 (report-and-status.txt)

命令: `python3 app.py report --port 18102`
时间: 2026-10-19T22:15:20+08:00
原文:

```
relay-report instance=beta version=relay-v1 state=ready
```

退出码: 0, 耗时 72 ms.

## 截图 (beta-status.png)

命令:

```
google-chrome --headless --disable-gpu --no-sandbox --window-size=900,400 \
  --screenshot=docs/changes/relay-board/evidence-e398c7c-r1/beta/ac005-1/beta-status.png \
  http://127.0.0.1:18102/status-page
```

时间: 2026-10-19T22:15:22+08:00, chrome_exit=0.
文件: beta-status.png, 8695 字节, sha256=d52bb2deb308eeddfba77975795b332827e00f875fc5152641d9efb16ee8f21c
画面内容 (人眼核对): `relay board` 标题, `instance=beta`, `state=ready`, `version=relay-v1`.

## 同一实例同一版本的对照

| 项 | 截图 | report |
|----|------|--------|
| instance | beta | beta |
| version | relay-v1 | relay-v1 |
| state | ready | ready |

截图取自 /status-page, report 取自 /report, 二者都由 PID 4090715 这个未重启的 beta 进程应答; 期间实例未停止、未重启、未换版本 (两次命令间隔约 2 秒, 实例启动日志仅一行 `listening on 127.0.0.1:18102 instance=beta`).

## 结论: beta 侧材料齐备, 截图与 report 的 instance/version/state 一致 (自证); 跨实例一致性由 G4 判定.
