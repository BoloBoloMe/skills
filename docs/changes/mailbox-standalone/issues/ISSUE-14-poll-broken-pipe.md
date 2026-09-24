## 父级
- `../EXECUTION.md`, TECHNICAL.md 非功能要求 (取信 --timeout/长轮询 hold)

## 执行
- [x] 已实现

## 要构建什么
实地验收发现的缺陷: 客户端以短于服务端 hold (缺省 20s) 的超时取信 (如 --timeout 5, AC-016 明文场景) 时, 客户端超时挂断连接, 服务端 hold 到期后往已断开 socket 写应答, socketserver 打出整屏 BrokenPipeError 堆栈 (serve 窗口被噪声淹没). 修复: 服务端 HTTP 处理路径对客户端提前断开做优雅处理 — 捕获 BrokenPipeError/ConnectionResetError (含 _json 写出与 hold 唤醒后的应答路径), 静默或打一行短日志, 不再吐堆栈. 既有功能行为零变化.

## 覆盖依据
- 实地验收证据 (用户 serve 窗口两次 BrokenPipeError, 源于 timeout 8 < hold 20 的正常用法)
- TECHNICAL.md 取信 CLI (--timeout 到时退出) 与非功能要求 (长轮询 hold 20s 沿用)

## 允许范围
- `workflow/mailbox/scripts/mailbox.py` (HTTP handler 应答写出路径)
- `tests/test_mailbox_cli.py` 或 `tests/test_mailbox_core.py` (回归测试)

## 禁止范围
- hold/timeout 语义与数值
- 协议端点行为 (响应内容不变, 只是客户端消失时不炸)
- 其他日志体系

## 代码定位提示
- mailbox.py: `_json` (写应答处, 约 1318), `_handle_poll` (hold 唤醒后应答, 约 1569), do_POST/do_GET 的 socketserver handle_error 路径
- 复现: 起 serve 后 `timeout 5 mailbox.py fetch --timeout 5`(或裸取信加 shell timeout), hold 20s 到期即炸

## TDD 切片
- TS-001:
  接缝: 子进程 serve + 短超时客户端.
  先写的失败测试: test_poll_client_disconnect_no_traceback — 起真 serve (临时 HOME), 发一个 hold 期中途断开的 poll 请求, 随后正常投信/取信仍工作, 且 serve 的 stderr 不含 "BrokenPipeError"/"Traceback"; 现状堆栈出现, 失败.
  最小绿色实现范围: 应答写出路径捕获客户端断开异常.

## 验证入口
/home/bolo/Workspace/skills/.venv/bin/python -m pytest tests/ -k "cli or core" -q -m "not e2e" 全绿; 全量快层无回归.

## 风险提示
不要吞掉真正的服务端错误 (只捕客户端断开类异常); 既有测试的应答断言不能变.

## 停止条件
需要改 hold/timeout 语义或扩大范围时停止.

## 验收标准
- [ ] 短超时客户端断开不再产生堆栈
- [ ] 正常投递/取信行为不变
- [ ] 相关测试全绿
