# 编排日志 (tdd-as-orchestra)

- 权威输入: `EXECUTION.md`, `PRODUCT.md`, `TECHNICAL.md`, `DECISIONS.md`, `issues/ISSUE-*.md`.
- 主分支: `v2`. 工作树根: `/home/bolo/Workspace/skills/skills-v2.worktrees/`. 分支: `issue/<NN>`.
- 基线: 见 `BASELINE.md`. AFK 自主决定: 见 `UNAUTHORIZED_DECISIONS.md`.
- 演练记录: 各 `evidence/ISSUE-<NN>/`.

## 波次完成记录

### 波次 1 (ISSUE-01, 06, 07, 11, 12) - 已合并

- 合并提交: 73fcd76 (01), ed3dda3 (06), afef773 (07), 3c862d4 (11), af02638 (12); 勾选提交 e757a10; 编排记录提交 47ca0bf.
- 全量测试: 6 failed / 659 passed / 2 skipped, 失败集合与基线逐条一致.
- 清理: 5 个工作树 remove, 5 个分支 branch -d, prune, 空目录已删.
- 执行者自报缺口 (留给评审与后续 ISSUE 核对):
  - ISSUE-01: `check_skill.py` 放行 description 里 "冒号+空格", 而 pi 的 YAML 解析拒绝, 技能会静默不加载; `general/` 属禁止改动, 只记录.
  - ISSUE-07: AC-023-4 用受控单模型材料检验 (本机多模型可用), 已如实标注; 许可全文待 ISSUE-13.
  - ISSUE-11: 结论只对 pi 1.3.0 + 本机组合成立; p2 历史导入真实上游数据与网页表单提交两条判据仍是未验证.
  - ISSUE-12: AC-020-1 的失败迭代与新增配方分别由两次演练承接.

### 波次 2 (ISSUE-02, 08) - 已合并

- 合并提交: 2c36d52 (02), 9896d9f (08); 勾选与日志提交见本文件所在提交.
- 全量测试: 6 failed / 659 passed / 2 skipped / 103 deselected / 33 subtests passed, 失败集合与基线逐条一致, 无新增.
- 清理: 2 个工作树 remove (未用 --force), 2 个分支 branch -d, prune, 空目录已删.
- 执行者自报缺口 (留给评审与后续 ISSUE 核对):
  - ISSUE-02: 旧观察材料只给转写说明时与 "摘要无原件" 形态相近, 原件最低形态待 Spec 明确; 冲突检测与带原件旧观察两条对照在旧版也能通过, 无红轮对照; 角色隔离与场景组派工未验证 (属 ISSUE-03/04); 加载方式只覆盖项目 `.agents/skills/` 一种; 宿主写入检查曾误拦一次批量脚本 (宿主扩展行为, 非技能结论); 失败演练用 v1 夹具, 通过演练用 v3 夹具, 未混成一次结论; 未做端到端接入与真实产品验收.
  - ISSUE-08: 红轮覆盖不完整 (AC-030-2/4/5/6 与 AC-031 三条在该模型未跑红, AC-024-4 只部分跑红), 已如实标注; 演练数字来自受控模拟材料, 不代表真实产品性能; 线程并发超上限案例已改用独立进程重测; v3 轮临时项目残留上一轮 `docs/green2.md`; 只在单一宿主与 pi 1.3.0 + herdr 0.9.4 上验证; MIT 许可全文待 ISSUE-13.
