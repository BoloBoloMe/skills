# rev-shared G4 段运行记录 (BR-002, AC-005-1)

验收者: rev-shared; pi session: 01a15483-642c-73fc-8bda-578e542ac6d6
目标提交: e398c7cc7ca4e493d23689bee3cca1a34d306000 (main, HEAD)
判据: PRODUCT.md 业务规则 BR-002 与场景 AC-005-1 原文
派工依据: plan.md 组 G4 = 必验清单第 10, 8 项

## BR-002 共享事件日志只增不改 (当前观察)

前置 (引用旧观察): 指挥者通知 G1/G2/G3 已停止写入; 见 tail/order.md.

命令与材料:
1. before (2026-10-19T14:16:55.310453Z):
   `sha256sum runtime/shared/events.log` -> 74230d7416dd9d2a6d3b20540e5c09c136935eb1b10bdc1cb2c37c6f53f3ab58
   `wc -l` -> 8; `wc -c` -> 540; `stat` -> Modify 2026-10-19 22:15:38.746173837 +0800
   `cp runtime/shared/events.log tail/events-before.log` (exit=0, 副本哈希相同)
   原始输出: br002-before.txt
2. 只读查看 (2026-10-19T14:16:57.963226Z -> 14:16:58.282413Z):
   `python3 app.py log --port 18101`, 退出码 0, 输出 8 行 (原始 stdout: br002-log-out.txt; 包装记录: br002-log-log.txt)
   - 含 `instance=alpha` 行 (例如 `2026-10-19T14:15:38.746671Z instance=alpha event=job-end ms=4000`);
     事件种类看到 beta job-start/job-end, alpha job-start/job-end, append seq=1 alpha / seq=2 beta.
3. after (2026-10-19T14:16:58.311808Z):
   `sha256sum` 仍为 74230d7416dd9d2a6d3b20540e5c09c136935eb1b10bdc1cb2c37c6f53f3ab58; `wc -l` 8; `wc -c` 540;
   `stat` Modify 仍为 2026-10-19 22:15:38.746173837 +0800; 副本 tail/events-after.log;
   `cmp tail/events-before.log tail/events-after.log` -> exit=0.
   原始输出: br002-after.txt
4. 输出与文件一致性 (2026-10-19T14:17:01.632263Z):
   去掉包装的 `exit=0` 行后 `diff -u tail/events-before.log tail/log-output-lines.txt` -> exit=0, 各 8 行.
   原始输出: br002-diff.txt

结论: 只读查看前后文件内容 (sha256/字节数/行数/mtime) 完全不变, 且 log 输出与文件内容逐行相同 => BR-002 通过.

说明: `app.py log` 走 GET /log, 产品代码 `Board.events()` 仅 `read_text`, 无写入路径 (读代码核对, 属推断辅证, 结论以上面的实测为准).

## AC-005-1 两侧状态材料互相一致 (当前观察: 我亲自读取并判读原件)

材料来源: rev-alpha 把材料放 alpha/, rev-beta 放 beta/; 本节只引用原件, 不采信其 summary 结论.

alpha 侧 (端口 18101):
- 截图原件: alpha/04-ac005/alpha-status.png (8788 B, 900x400 PNG, mtime 22:15:20.727 +0800,
  sha256 4374f026939db8238ab13de9ed80aad7c997cd3ebc9a89504509d5ac51248803; 与 alpha/01-ac001/alpha-status.png 同哈希)
  我判读图像文字: `instance=alpha`, `state=ready`, `version=relay-v1`.
- report 原件: alpha/04-ac005/report.txt (mtime 22:15:23.822 +0800, sha256 3637f8b...a3cf93)
  内容 `relay-report instance=alpha version=relay-v1 state=ready`, exit=0.
  另有更新一次的 alpha/04-ac005/report-fresh.txt (mtime 22:15:47.555 +0800) 同样是
  `relay-report instance=alpha version=relay-v1 state=ready`, 并附 `ok instance=alpha`.
- 一致: instance=alpha 截图与 report 相同; version=relay-v1 相同; report 含 state=ready.

beta 侧 (端口 18102):
- 截图原件: beta/ac005-1/beta-status.png (8695 B, 900x400 PNG, mtime 22:15:22.499 +0800,
  sha256 d52bb2deb308eeddfba77975795b332827e00f875fc5152641d9efb16ee8f21c)
  我判读图像文字: `instance=beta`, `state=ready`, `version=relay-v1`.
- report 原件: beta/ac005-1/report-and-status.txt (mtime 22:15:20.544 +0800, sha256 058b857...aaea22)
  `--- report raw ---` 下 `relay-report instance=beta version=relay-v1 state=ready`, report_exit=0;
  同文件 status 输出也含 instance=beta, state=ready, version=relay-v1.
- 一致: instance=beta 截图与 report 相同; version=relay-v1 相同; report 含 state=ready.

适用性判断 (我自己下的, 非照抄):
- 截图取自哪个端口: alpha 侧有原始命令记录 alpha/01-ac001/screenshot-cmd.txt, 明确 `http://127.0.0.1:18101/status-page`
  (当前观察, 原文含 exit=0, 8788 bytes); beta 侧截图命令只写在 beta/ac005-1/notes.md 里
  (`--screenshot=...beta-status.png http://127.0.0.1:18102/status-page`), screenshot.log 本身没有 URL
  (这部分属引用旧观察). 端口与实例名对应正确; 两张均为 900x400 有效 PNG, 非占位图.
- 版本数字 `relay-v1` 与目标提交 app.py 的 `VERSION = "relay-v1"` (第 12 行) 一致, 材料覆盖的就是本提交.
- 旁证 (当前观察, 只读, 不影响判据): 2026-10-19T14:17:08Z 我另跑 health/report 两端口,
  得到 `ok instance=alpha` / `ok instance=beta` 与
  `relay-report instance=alpha version=relay-v1 state=ready` /
  `relay-report instance=beta version=relay-v1 state=ready`, 与原件一致.
  原始输出: ac005-1-crosscheck.txt
- 材料元数据与哈希复算: ac005-1-material.txt

结论: 每侧 instance 与 version 在截图和 report 中相同, 两侧 report 都含 state=ready => AC-005-1 通过.

## 只读约束

本段只读: 未改 app.py / README.md / deps.txt / tests/, 未写 alpha/ 或 beta/ 下任何文件,
只在 shared/ 与 tail/ 下新增文件. tail/ 内新增: br002-before.txt, events-before.log,
br002-log-out.txt, br002-log-log.txt, br002-after.txt, events-after.log, br002-diff.txt,
log-output-lines.txt, ac005-1-material.txt, ac005-1-crosscheck.txt, order.md, notes.md.

G4 收尾时间: 2026-10-19T14:17:39.714140Z (tail/final-check.txt 记录的最后一次只读核对; 之后只写本证据目录内的 md 文件).
