# 移除项目验证配方的生成与维护工作流

按我本次明确要求, 删除 `create-verification-skill` 与 `maintain-verification-skill` 两项工作流 skill, 同时移除其目录与 README 入口. 两者专属规则不迁移, 不为已移除的入口另建替代流程.
本决策取代 [ADR 0021](0021-project-verification-recipes-not-acceptance-authority.md) 中将配方生成与维护职责分配给这两项 skill 的部分. ADR 0021 关于项目配方不作为另一套产品验收标准的边界不变; 旧 ADR 与历史变更记录原文保留.
`verify-change` 对项目既有配方的可选支持保留. 移除这两项工作流, 不表示项目不能已有或自行编写配方, 也不要求删除项目里的配方.
