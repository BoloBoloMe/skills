# milestone-05 实施自检证据

- 任务: workflow-stack-review/milestone-05 措辞与 SAFETY 指针修正. 本文件记录实施者自检, 不是独立产品验收.
- 基线提交: 57e93dc (doc: milestone-05 固化已确认验收标准).
- 实现提交: 14c624f (doc: milestone-05 修正措辞与安全指针).
- 权威判据: docs/changes/workflow-stack-review/ACCEPTANCE.md 的 AC-05-01 至 AC-05-07 (随基线提交固化), 以及 roadmap.py query milestones.milestone-05 的已更新 question.

## AC 对应改动 (实现提交 14c624f 的 diff 可逐项核对)

- AC-05-01 (`workflow/verify-change/SKILL.md` 第 5 步, 原 59-60 行): 删掉复述 SAFETY 写入与授权节的两句 (需写测试资源开跑前交我批准/说明资源对象操作/免审批不授权; 批准绑定范围/同范围复跑直接执行/换范围新批准/旧批准不作新范围依据), 指针改为指向 `verification-contract/SAFETY.md` 的 **写入与授权** 节并声明本节不复述. 保留: 获批前相关项记未检查, 不先做后补 (验收报告语义); 派工单原样写入批准范围; 要求验收者逐次记录写入对象/命令/时间/结果/数据位置; 需超范围时验收者停下报告且不替其扩权. "旧批准不作新范围依据" 由 SAFETY 重新授权规则承接, 未复述.
- AC-05-02 (`workflow/blast-radius/SKILL.md` 第 4/5 节): 第 4 节授权句 "写仓库或运行有副作用的应用前, 先问我" 改为按 SAFETY **写入与授权** 节获批; 第 5 节首段 "动手前确认调用方已批准范围" 同改; 清理 bullet 改为清理与数据保留按 SAFETY **写入与授权** 及 **原始数据** 两节执行. 只读调查不需额外授权, 临时目录放置, 交接写清理结果等原有要求均保留, 未新增另一套安全规则.
- AC-05-03 (`workflow/maintain-verification-skill/SKILL.md` 新子会话复跑完成标准, 原 67 行): "不为复跑另开 verify-change 产品验收层" 改为正面表述 "结论范围是配方当前可执行与本次复跑结果", 不点名 verify-change, 保留本次结论只覆盖配方复跑的边界.
- AC-05-04 (`workflow/blast-radius/SKILL.md` 引言第 9 行): 删去 "验收指挥者" 称谓, 改为 "若你按调用方分工组织产品验收, 不借本技能亲自验收, 须派实际验收子会话", 分工语义不变. `reference/PROVENANCE.md` 同步更新 "上游无写入授权句" 与 "上游无角色句" 两行的本地落点描述, 使其与正文一致; 历史决策引用 (D024/D025) 与上游列未改.
- AC-05-05 (`README.md`): 在 `## 目录` 标题下, 第一张 skill 表 (通用技能) 之前新增一段: "调用关系口径: 调用图只画执行调用; 引用, 分工声明与重新派活不算调用边."

## check_skill.py 实际执行记录

执行时间 (UTC): 2026-10-30T10:23:46Z. 所查版本: 基线 HEAD=57e93dc 之上已应用全部编辑的工作区 (即实现提交 14c624f 的内容).
命令 (在仓库根目录 /home/bolo/Workspace/refactor-skill-around-verification 执行, PYTHONDONTWRITEBYTECODE=1 防写字节码缓存):

```
export PYTHONDONTWRITEBYTECODE=1
for f in workflow/verify-change/SKILL.md workflow/blast-radius/SKILL.md workflow/maintain-verification-skill/SKILL.md; do echo "== $f"; uv run python general/writing-for-llm/check_skill.py "$(pwd)/$f"; echo "exit=$?"; done
```

原始输出 (逐字):

```
== workflow/verify-change/SKILL.md
/home/bolo/Workspace/refactor-skill-around-verification/workflow/verify-change/SKILL.md: OK
exit=0
== workflow/blast-radius/SKILL.md
/home/bolo/Workspace/refactor-skill-around-verification/workflow/blast-radius/SKILL.md: OK
exit=0
== workflow/maintain-verification-skill/SKILL.md
/home/bolo/Workspace/refactor-skill-around-verification/workflow/maintain-verification-skill/SKILL.md: OK
exit=0
```

退出码: 三次调用均 0 (由紧跟 uv run 的 `echo "exit=$?"` 取得).

## 范围与未验证项

- 未运行 sync-to-pi.py, 未修改已安装 skills 或全局配置 (仓库 AGENTS.md 边界, AC-05-07).
- 本检查只证明仓库文档符合 check_skill.py 的静态约束; 模型实际遵从率, 安装目录同步效果未验证, 不宣称已验证.
- 改动仅限上述 5 个已有文件; ROADMAP.json 的未提交改动属主协调方, 未包含在本里程碑提交内. 不 push.
