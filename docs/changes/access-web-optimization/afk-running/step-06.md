# 步骤 06: 收尾

验证: 执行当前 issue 的验证入口.
回写: 读取当前 issue 定义文件, 将 "- [ ] 已实现" 改为 "- [x] 已实现". 找不到标记 → 停止并报告.
决策: 调用 decision-ledger skill, 基于真实 diff 更新 feature 根目录下的 DECISIONS.md 中相关决策的实际影响.
报告: 写入 当前 issue 产物目录/final-report.md. 覆盖: 最终 diff 摘要, 验证结果, reviewer 发现项处理, 决策实际影响更新, 遗留阻塞项, 拘余风险.

扫描: 列出 afk-running 下所有 ISSUE-* 目录, 按编号排序. 跳过已有 final-report.md 的.
  找到未完成 → _current.md 写为 <下一个 key>:01
  全部完成 → _current.md 写为 done
→ 继续执行
