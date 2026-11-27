# milestone-07 停止并汇报 (RUN-REPORT)

- 交付对象: milestone-07 实施 to-spec 全程盘问对齐 (盘问即写稿) 与 verify-change 方案盘问条文, navigate/ACCEPTANCE-GUIDE/README 连带说明; 分支 improve, 最终完整提交 f4a45fbc62fbb099e79aca2ba45e11545f579b0c, 已快进推送 origin/improve.
- 逐项改动: ISSUE-01 to-spec 流程与 CLI (切片 1e64e6c, 返工后 e6b7962); ISSUE-02 verify-change 条文 (34ae059); ISSUE-03 navigate/README 对齐 (70ae157); ISSUE-04 返工 H1/H4/R4 (e6b7962); ISSUE-05 返工 Q4 术语 (42456c4); ISSUE-06 记录回填 (676311a); ISSUE-07 返工 Q1+N1 (8e776be); ISSUE-08 返工 F1 (1efb0f0); 集成链 9e8dd1df -> f4a45fb (各轮 merge 与执行记录见 git log).
- 开发验证与评审结果: uv run --with gherkin-official pytest workflow/to-spec/tests = 40 passed + 50 subtests (每轮集成复跑); 变更 SKILL.md (to-spec/verify-change/navigate) check_skill.py 全 OK; ac-draft/check-ac/check-tech 公开 CLI 实跑全覆盖, 原子替换与三并发窗口经 ptrace 真实进程时序证据; 编号/历史审计 (182ff184->集成) 无新违规; 实施前后安装目录摘要一致; 评审 Standards 14/Spec 8/旧行为 10 项起, 经四轮返工与收敛核对全部收敛 (CONVERGENCE.md), 影响方向四轮终局 0 新增 (IMPACT-REVIEW.md 四轮记录). 明确成品独立验证由调用方 (milestone-08) 后续安排.
- 返工轨迹: 四轮; 第一轮评审发现 H1/H2/H3/H4/R4/Q4 及记录类项 -> ISSUE-04/05/06; 第二轮 N1/N2 与 Q1 -> ISSUE-07; F1 经用户授权 -> ISSUE-08; 每轮均经实现/提交/合并/检查与影响方向重跑, CONVERGENCE.md 与 IMPACT-REVIEW.md 逐项闭环.
- 缺口与待决: 全量 uv run pytest 未验证 (容器无 Podman, 交调用方安排环境); R1 机械防串版缺失属决策10 知情接受; R2 已安装技能未同步 (sync-to-pi.py 由用户择时); R5/R9/R10 跨文件措辞与可移植性事项交 milestone-12 用户审改定夺; G 类证据缺口 (安装库未同步窗口, to-spec tests 容器外复核等) 如实登记于 IMPACT-REVIEW.md; 归档快照 check_skill 误报 (evidence 树内 SKILL.md 副本) 四轮判定不改证据原件.
- 现场状态: 工作树与 issue/* 分支全部清理, 主仓 git status 干净; 证据根 /home/bolo/evidence/to-spec-grilling-and-chinese-ids/ 与仓库内归档一致 (1582 文件); 无代用户裁决事项 (F1 范围授权由用户明示).
