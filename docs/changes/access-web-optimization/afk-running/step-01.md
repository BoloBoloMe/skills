# 步骤 01: 预检 + 启动 worker

确认: 工作树干净, worker 和 reviewer 子代理可用.
读取 contract, decisions (如存在), 当前 issue 定义文件. 全部可读 → 继续.

确定 attempt N: 扫描当前 issue 产物目录下现有 worker-note-aN 或 fix-note-aN, 无则 N=1.
输出: 当前 issue 产物目录/worker-note-aN.md.

启动 worker 子代理. task:
- 角色文件: worker 角色文件
- 任务: 实现当前 issue 的全部目标
- 输入: contract, decisions (如存在), 当前 issue 定义文件
- 输出: 上述输出路径
- 约束: 调用 tdd skill, 读 worker-tdd.md (用户说不用 TDD 时可省略)

worker 中断时优先 resume.

---

worker 完成 → _current.md 写为 :02
worker 不可恢复 → 停止并报告
