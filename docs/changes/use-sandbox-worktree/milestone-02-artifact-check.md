# MILESTONE-02 产物一致性审查报告

审查对象: MILESTONE-02 盘问固化产物及其下游同步文件.

审查范围:

- `docs/changes/use-sandbox-worktree/DECISIONS.md`
- `docs/language/UBIQUITOUS_LANGUAGE.md`
- `docs/adr/0008-mother-worktree-direct-receive-no-hooks.md`
- `docs/changes/use-sandbox-worktree/roadmap/MILESTONE-02.md`
- `docs/changes/use-sandbox-worktree/roadmap/MILESTONE-03.md`
- `docs/changes/use-sandbox-worktree/roadmap/ROADMAP.md`
- 事实核对材料 `milestone-02-worktree-topology-findings.md` 和 `milestone-02-opposing-review.md`

## 结论

发现 3 项错误, 1 项存疑, 1 项建议.

已核实无问题的部分:

- 决策编号 D001-D013 连续且无重复, 事实编号 F001-F008 连续且无重复.
- D001/D004/D005/D006 的替代方向, D002/D003 的废弃语义, 以及 F002→F007 的事实更新方向均有旧条目侧记录.
- M02 结论区、ADR 0008、ROADMAP 的母体模型/无 hooks config/单活动母体/fail-closed 恢复/终结语义一致.
- F007 对拓扑 findings 的八项转述无实质失真,F008 对两项反方结论及 D010/D011 采纳关系的转述无实质失真.
- ROADMAP 前沿为 M03+M06, 阻塞图与此一致; 容器崩溃/host 重启恢复迷雾已移除, 同仓不同母体并发已并入并发迷雾项, M01 已关闭行已标注被 M02 替代修订.
- `sandbox/work` 在 DECISIONS 的旧决策/F001/F002 和 M02 的问题或历史结论语境中保留, 属允许的历史档案; UBIQUITOUS_LANGUAGE 已移除 gate 词条并加入母体/git 守护进程/推送落地定义.
- 检查到的 Markdown 相对链接均指向真实存在的文件, 未发现失效链接.

## 错误

### 1. D013 的依赖事实 ID 与决策内容不相干

位置: `docs/changes/use-sandbox-worktree/DECISIONS.md:103-108`, 尤其是 `:106-107`.

证据:

- D013 的内容依据写的是 `MILESTONE-05 结论: digest 精确版本`.
- D013 却标注 `依赖事实: F006 之外无新增`.
- F006 在 `DECISIONS.md:137-140` 只记录 Podman 动态宿主端口的行为, 不包含镜像 digest 或镜像换版处置.

理由: 该依赖声明不能支持 D013 的镜像换版决策,并且 M05 的 digest 结论没有对应的事实 ID. 这违反账本中依赖事实可追溯的要求,会使审阅者误把端口事实当成镜像版本决策依据.

建议修复方向: 为 M05 digest 结论登记合适的事实 ID并在 D013 引用,或明确 D013 没有依赖 F006,不要保留当前的错配声明.

### 2. MILESTONE-03 仍声明被已关闭里程碑阻塞

位置: `docs/changes/use-sandbox-worktree/roadmap/MILESTONE-03.md:1-3`.

证据:

- M03 文件写 `# 阻塞于: MILESTONE-01, MILESTONE-02`.
- `docs/changes/use-sandbox-worktree/roadmap/ROADMAP.md:41` 已将 M03 列入前沿,并写明 `MILESTONE-02 决策已就位`.
- `ROADMAP.md:62-66` 的阻塞图把 M01/M02 作为已关闭前置节点指向 M03.
- `ROADMAP.md:69` 明确写 `M03, M06 均已解阻塞`.

理由: 若 `阻塞于` 表示当前阻塞项,该头部与 ROADMAP 的已解阻塞状态直接矛盾. 若它实际想表达“历史前置依赖”,当前字段名又会误导后续编排和审阅.

建议修复方向: 将 M03 头部改为无当前阻塞,或把字段改成明确表示前置依赖的名称.

### 3. 替代关系没有完整形成账本双向可追溯链

位置:

- `DECISIONS.md:12-17` 的 D002 写明由 D009 取代,但 `DECISIONS.md:76-81` 的 D009 内容没有反向点名 D002.
- `DECISIONS.md:33-38` 的 D005 状态指向 D007,但 `DECISIONS.md:47-53` 的 D007 内容没有反向点名 D005.
- `DECISIONS.md:117-120` 的 F002 状态指向 F007,但 `DECISIONS.md:142-145` 的 F007 内容没有反向点名 F002.

理由: 当前可以通过 M02 结论区或替代原因间接推回,但不能从每个新条目直接确认它替代了哪个旧条目. 这不满足指定的“被替代/废弃条目状态与互指正确,双向可追溯”要求,尤其 F002/F007 还代表不同拓扑下的两份矩阵,需要明确历史边界.

注: D003→D009,D004→D008,D006→D008 已分别在新条目中出现反向 ID 说明,不属于此项缺口; D001 在 D007 中有保留部分说明,但最好也明确写出“替代 D001 的哪些部分”.

## 存疑

### 4. 当前路线笔记残留未定义的旧 `gate` 术语

位置: `docs/changes/use-sandbox-worktree/roadmap/ROADMAP.md:21`.

证据:

- 路线 A 当前描述仍为 `git+pi+ssh 镜像 + gate + 全通网络`.
- UBIQUITOUS_LANGUAGE 已在 `docs/language/UBIQUITOUS_LANGUAGE.md:39-41` 将 gate 标记为旧称,并以母体取代.
- M03 当前实现描述也已经改成 `母体 worktree + 无 hooks config`(`MILESTONE-03.md:10-13`).

理由: 该行属于当前路线说明,不是 M01 历史档案,但没有说明 gate 是何物. 它容易让执行者继续按旧独立 clone gate 理解路线 A,与 D007/D008 及 M03 的当前模型产生语义漂移.

历史语境中的 gate 保留不构成问题,例如 ROADMAP `:11` 的旧调研来源,`:16-17` 的 M01/M02 变更记录,以及 `:35` 的 M01 历史摘要.

## 建议

### 5. ADR 0008 的正文引用可改为可解析相对链接

位置: `docs/adr/0008-mother-worktree-direct-receive-no-hooks.md:19`.

现状: `详见 docs/changes/use-sandbox-worktree/DECISIONS.md ...` 是普通文本路径,不是 Markdown 链接. 它从 `docs/adr/` 目录上下文看也不像可直接点击的相对路径.

理由: 本次链接检查未将它判为失效链接,因为它不是链接语法;但 ADR 作为决策入口,该引用不利于导航,也容易被误解为相对于 ADR 目录的路径. 建议补为可点击的正确相对链接,并为 findings 文件同样处理.

## 总结

M02 的核心拓扑结论和 F007/F008 事实转述一致,ROADMAP 的前沿/迷雾/阻塞图主体也已同步正确. 需要优先处理 D013 依赖事实错配和 M03 stale 阻塞头部,并补齐 D002/D005/F002 的替代关系反向引用;否则账本审计链和下游执行状态仍不完整.
