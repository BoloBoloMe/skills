# 步骤 03: review 并行

启动两个 reviewer 子代理 (并行):

1. 正确性 reviewer. task:
   - 角色文件: reviewer 角色文件
   - 审查维度: 正确性 (逻辑/边界/异常/回归/并发/数据一致性/测试覆盖)
   - 输入: contract, decisions (如存在), 当前 issue 定义文件, 当前 issue 产物目录/worker-note-aN.md
   - diff 获取: git diff
   - 输出: 当前 issue 产物目录/review-correctness-aN.md

2. 决策边界 reviewer. task:
   - 角色文件: reviewer 角色文件
   - 审查维度: 决策边界 (contract 目标/非目标/行为边界, decisions 遵守, issue 允许/禁止范围, 是否越界/提前实现/需改决策)
   - 输入: 同上
   - diff 获取: git diff
   - 输出: 当前 issue 产物目录/review-decision-boundary-aN.md

reviewer 中断时优先 resume.

---

两份报告就绪 → _current.md 写为 :04
任一 reviewer 不可恢复 → 停止并报告
