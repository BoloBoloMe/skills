# 状态: 已关闭
# 类型: task
# 阻塞于: 无 (MILESTONE-07 已关闭)

## 问题

窗口直飞实施 (AFK 编码): base 层 sshd_config/目录保障改动 + display 层加 waypipe/libpulse0 + 启动脚本母本 + swt headed 三态选路 + 信箱集成 (经信箱通知设备侧拉起) + SKILL.md 显示栈节改写 + 交付包 "远程直通" 项. 按 D017 级联重建 base/display/项目镜像, 成本已在 M06 摆台并经用户接受.

实施前必读 [MILESTONE-07](MILESTONE-07.md) 实测结论的 N1-N6 新事实 (命令必须 env(1) 包装/脚本内设 env, sshd 残留 socket 语义, XDG_RUNTIME_DIR 注入路径, 设备密钥 enrollment, uid≠1000, waypipe 0.8.4).

## 实施结论 (2026-09-15, AFK tdd-as-orchestra 收口)

权威输入: [EXECUTION.md](EXECUTION.md) (总指挥自拟, UD-01) + [UNAUTHORIZED_DECISIONS.md](UNAUTHORIZED_DECISIONS.md) (UD-01..13). 8 ISSUE 全部完成并逐个提交 (a325b4c..c213603), 双轴 code-review 通过 (Spec 全符合, 无硬性违规):

- ISSUE-01/02: base 层 sshd 三项 (SetEnv 单行合并 `XDG_RUNTIME_DIR=/tmp/xdg-1001` (N5/UD-03) + `StreamLocalBindUnlink yes` + entrypoint 建目录后 exec sshd) + display 层清单 waypipe/libpulse0 (N6).
- ISSUE-03: 启动脚本母本 `headed-browser/swt-headed-browser.sh` (preflight: 变量在场 + AF_UNIX 可连, 失败 exit 86 (UD-11); 条件导出 PULSE_SERVER (UD-08); env 脚本内设 (N1)) + swt birth throwaway 解析 chromium 精确路径 (失败降级不阻断, UD-06) + 实例 0755 落 runtime 留档 + 只读挂载固定路径.
- ISSUE-04: 服务端指令集首成员 `swt.pull-window` = 内置形状校验 (恰 {tool, container} 两键 + container 绑定投信容器自身, UD-05), 不落静态 whitelist 行.
- ISSUE-05: relay 扩展拉窗门 (waypipe 在场检查 + 缺席抑制同类信 + 同容器 300s 限频 + skipped 即时 ack, UD-07/UD-10).
- ISSUE-06: `swt enroll-device-key` 子命令 (N4 设备→容器免密发放, 单次 exec + stdin + grep 去重).
- ISSUE-07: 交付包窗口直飞行 (waypipe ssh 模板含 `-R /tmp/swt/pulse-b.sock:/run/user/$(id -u)/pulse/native` (UD-09), lan 缺失/无脚本均打 F3 reason 行), birth/resume/status 全接线, headed-script 落容器 record.
- ISSUE-08: SKILL.md 窗口直飞三态编排节 (投信形状/新 token 差集轮询 120s (UD-02)/noVNC 兜底 + 设备侧五步配方) + 指令集现状改首成员 + M08 分发分流提醒 (D017 级联).

测试: 契约池 276 绿 (含本里程碑新增 44: m08_headed 17 + m08_delivery 19 + pullwindow 15 中 15/relay 6 等), node relay 20 绿; 需真 podman 的用例基线红不变 (留 M09). 双机实测与镜像 D017 级联重建真机执行归 [MILESTONE-09](MILESTONE-09.md).
