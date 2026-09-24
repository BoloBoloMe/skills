## 父级
- `../EXECUTION.md` (验收期发现, 候选 issue, 未排期)

## 执行
- [ ] 已实现

## 要构建什么
pi 扩展守护子进程生命周期的两个已知限制 (ISSUE-15 验收期记录, 按 "不重构生命周期" 纪律未修):
1. 迟到 close 事件误杀新守护: stop/会话替换后立即 start, 被杀子进程的迟到 close 事件会误杀新守护并报 "异常退出 (exit SIGKILL)" — child close handler 未校验被关闭的是否仍是当前子进程. 当前测试以 400ms 间隔绕开.
2. 守护 pid 存活不校验: D021 "进程已死才恢复" 只查内存标志, 不验标记所记 pid 存活; pi 被 SIGKILL 留孤儿守护时同会话恢复会双活 (旧码同此洞).
另 (ISSUE-14 验收观察): relay 中转面 _forward 的成功路径裸写 wfile, 客户端断开仍会吐堆栈 (poll 面已修).

## 允许范围
- `workflow/mailbox/pi-extension/index.ts` (close handler 校验 child === currentChild; start 前按标记 pid 存活判定)
- `tests/test_mailbox_listen_mark.py` (对应断言)

## 禁止范围
- mailbox.py; 其他 docs; D021 语义本身.

## 验收标准
- [ ] stop/替换后立即 start 不被迟到事件误杀
- [ ] 同会话恢复不产生双活守护
- [ ] 相关测试全绿
