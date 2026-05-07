# 蓝图审批检查表

用于判断 `phase-03/implementation-blueprint@vN` 是否可以批准。

## 必须全部为“是”

1. 蓝图是否明确引用了已批准设计？
2. 会改哪些文件或文件域、绝对不能改哪些文件或文件域是否清楚？
3. 每个 execution unit 的目标、依赖、验证方法和停止条件是否明确？
4. 验证口径是否足以证明设计目标达成？
5. 并行、迁移、共享状态或高风险操作是否被标成 strict？
6. 是否给出唯一批准命令：`模板：批准蓝图：批准 phase-03/implementation-blueprint@vN；正式示例：批准蓝图：批准 phase-03/implementation-blueprint@v2`？

## 不能批准的情况

- 蓝图偷偷改变了已批准设计。
- 文件范围不清，或禁止越界项缺失。
- 验证方法缺失或依赖未来执行时临时决定。
- 失败后应该停在哪里不明确。

下一步：批准后进入 [交接审核检查表](handoff-review-checklist.md)。
