# 状态: 待处理
# 类型: task
# 阻塞于: MILESTONE-11

## 问题

五场景脚本实现: 按 MILESTONE-11 盘问拍板的方案 (DECISIONS.md D025-D038), 实现 host 侧单 module `swt.py` 五子命令 (birth/resume/status/terminate/switch).

AFK 编码任务, 调用 `tdd-as-orchestra` skill 处理.

范围含: net-firewall.py 接口扩展 (按容器源地址删规则, D032); e2e-smoke.py 阶段函数下沉 (D036).

完成判据:

- 五子命令按拍板的四件事 (状态前置/成功后状态/失败清理责任/禁止操作) 实现完整, 决策收据协议 (D026), exit code 协议 (D027), retired 语义 (D033) 均有落点.
- MILESTONE-11 考察点逐项有落点, 脚本实跑通过.
- e2e-smoke 退役门槛 (D036): swt 黑盒测试矩阵逐项等价 M03 证据 (D036 所列条目) 全绿, 且断言独立外部状态不只信 STATE; 未全绿前 e2e-smoke 保留为回归基线.
