# 宽重构的扩展-收缩拆分

宽重构无法拆成独立可验证的垂直切片时使用. 一次编辑打断成千上万个调用点, 所以让新旧两种形式并存, 分批迁移, 最后删旧, 每批迁移后项目仍可验证.

- 兼容扩展 issue: 添加新形式, 保留旧形式, 不大批迁移调用者. 完成后现有路径仍然可用
- 分批迁移 issues: 按 package, 目录或调用者类型分批把使用处从旧形式改到新形式. 每批都是一张 issue, 且由兼容扩展 issue 阻塞. 因为旧形式仍存在, 每批完成后都应能通过验证
- 收缩清理 issue: 确认没有调用者再使用旧形式后, 删除旧形式. 这个 issue 由所有分批迁移 issues 阻塞

若某批迁移单独完成后无法保持绿色, 序列不变, 但这些 issue 不再标为可独立领取: 标为 HITL/integration 特例. 整条序列共用一条 integration branch, 分支与工作树名由序列首个特例 issue 编号推出 (`integration/<NN>`, `<仓库名>.worktrees/integration-<NN>`), 每个特例 issue 的 `Integration 特例` 节引用同一名字. 序列在主仓库外的共享工作树内按编号串行推进, 不并行; 每个中间 issue 完成后在该分支提交并留下局部完成证据. 最后由整合验证 issue 跑整体验证, 通过后把 integration branch 一次性合回主分支. 这些 issues 都阻塞最终的整合验证 issue.

HITL/integration 特例写进 issue 的 `Integration 特例` 节 (见 issue 模板), 写共享 integration branch, 本 issue 的局部完成证据, 最终整合验证 issue 的引用, 以及主分支上暂不可见的说明.
