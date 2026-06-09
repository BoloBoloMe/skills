# run-afk-workflow 改进建议

## 目标

本文件记录对 `workflow/run-afk-workflow/SKILL.md` 的审核建议. 重点是让 router 保持轻量, 可迁移, 不暴露本机路径, 不引用即将删除的旧链, 并把长篇运行手册拆到参考文件.

## 必改项

### 1. 移除旧链名

`workflow-afk-implement-review` 将彻底移除, router 不应再显式提到该链.

理由:

- 避免父会话或子代理误以为存在兼容入口.
- 避免搜索旧链名时出现假阳性.
- 保持 router 只登记当前可用链.

建议处理:

- 删除旧链停用说明.
- README 和 chains 中也同步移除旧链资产或说明.

### 2. 移除本机绝对路径

router 当前不应写入任何设备专属路径示例.

理由:

- skill 需要跨系统, 跨设备可迁移.
- 本机用户名, 用户目录, 安装路径都不应进入 skill 文档.
- 运行时路径应由父会话解析后传入.

建议处理:

- 用 `<system-temp>/pi-afk-runs/<run-id>` 表示运行目录.
- 用 `<system-temp>/pi-afk-sessions` 表示 session 目录.
- 禁止写用户级 pi 配置目录, 但不写具体本机路径.

### 3. 缩短主 SKILL.md

当前 `SKILL.md` 承载了 router, runbook, 调用模板和产品化建议, 体量偏大.

建议主文件只保留:

- description.
- 不变量.
- 合法链路由表.
- 每条链的调用前置条件.
- 指向参考文件的链接.

建议拆出:

- `AFK-RUNBOOK.md`: 状态机, preflight, artifact 布局, failure recovery, 调用模板.
- 如后续需要专用 agent, 另建 `AGENT-CONFIG.md` 或放入 runbook.

### 4. 明确 saved chain 发现前提

当前调用模板提到 `/run-chain`, 但本仓库顶层 `chains/` 只是源码资产, 不一定被 pi 自动发现.

建议补充:

- `subagent` tool 直接调用时, 父会话读取 `chains/*.chain.json` 的 `chain` 数组并传入 `chain`.
- `/run-chain` 只有在 chain 已安装到运行时可发现目录后可用.
- 项目级发现目录应由目标项目负责, 不写用户级目录.

## 建议改进项

### 5. 更新 description

当前 description 主要强调 AFK 编码, 没有充分覆盖 review-only 和 fix-only.

建议描述包含:

- 只读 scout 链.
- AFK implement-only 链.
- AFK review-only 链.
- AFK fix-only 链.
- 触发前提是 `orchestrate` 已完成分类, 父会话仍保留调度权.

### 6. 收紧 chainDir 和 AFK_RUN_DIR 关系

建议 router 明确:

- 父会话创建 `<AFK_RUN_DIR>`.
- 调用 AFK 链时必须设置 `chainDir:<AFK_RUN_DIR>`.
- chain 相对 output 均落入同一 checkpoint 目录.
- task 中的 AFK_RUN_DIR 与 `chainDir` 必须一致.

理由:

- 避免 output artifact 分散到默认 chain 临时目录.
- 失败恢复时只需按一个 run id 复盘.

### 7. 明确 scout 不是需求事实源

`workflow-context-scout` 是只读代码事实压缩链, 不应替代 PRD, PLAN 或 issue.

建议补充:

- scout 输出仅作为代码事实和验证线索.
- 需求事实源仍由父会话掌握.
- scout 不需要 AFK_RUN_DIR, 可使用普通 chainDir.

### 8. 精简调用模板

主 `SKILL.md` 中不宜保留三段完整 JSON 模板.

建议:

- 主文档只写最小调用原则.
- 详细 JSON 模板放到 `AFK-RUNBOOK.md`.
- 模板中避免本机路径, 只使用 `<repo>`, `<AFK_RUN_DIR>`, `<AFK_SESSION_DIR>`.

### 9. 可选专用 agent 移出主文档

`workflow.afk-worker` 当前只是建议, 未在仓库中真正提供.

建议:

- 从主 `SKILL.md` 移到 runbook 的可选章节.
- 如果要落地, 后续单独创建项目级 agent 配置或说明.
- 不在 router 中暗示该 agent 已可用.

### 10. 补充不启动 fix-only 的条件

父会话 synthesis 后, 应明确以下条件:

- `accepted_now` 为空: 直接 final validation.
- `needs_human_decision` 非空: 停止并询问用户.
- finding 无证据: 不进入 fix worker.
- 修复会越过 allowed files: 不进入 fix worker.

## 最小改动方案

如果只做一轮小改, 建议顺序:

1. 删除 `workflow-afk-implement-review` 旧链引用.
2. 移除本机绝对路径.
3. 新增 `AFK-RUNBOOK.md`, 迁移状态机, preflight, artifact 布局, failure recovery 和调用模板.
4. 精简 `SKILL.md` 到 router 职责本身.
5. 更新 README 中的 chain 清单, 删除旧链.

## 验收标准

- `workflow/run-afk-workflow/SKILL.md` 不再出现旧链名.
- skill 文档不包含本机绝对路径.
- 主 `SKILL.md` 保持短小, 不承载完整 runbook.
- AFK 链路明确使用 `chainDir:<AFK_RUN_DIR>`.
- `/run-chain` 说明包含发现前提.
- reviewer findings 到 fix worker 的边界清晰.
