# 独立验收派工计划 (v1, 目标提交 e398c7cc7ca4e493d23689bee3cca1a34d306000)

## 必验清单 (来源: docs/changes/relay-board/PRODUCT.md, confirmed-flow: v1)

验收场景 8 条 + 业务规则审计 2 条 = 10 项:

1. AC-001-1 alpha 状态页与 report
2. AC-001-2 beta 实例状态页 (status 命令)
3. AC-002-1 alpha 耗时任务
4. AC-002-2 beta 耗时任务
5. AC-003-1 追加 alpha 条目 (前置: runtime/shared/record.jsonl 不存在)
6. AC-003-2 追加 beta 条目 (前置: 已有 alpha 条目)
7. AC-004-1 只读查看事件日志 (前置: alpha 耗时任务正在执行)
8. AC-005-1 两个实例的状态材料互相一致
9. BR-001 (审计) 共享记录序号从 1 连续递增不重复, 每个 value 只出现一次
10. BR-002 (审计) 共享事件日志只增不改, 只读查看前后文件内容不变

## 分组与人数

- 全部 10 项只有一组 (G1), 派 1 名验收者依次做完.
- 依据: 所有场景都固定在 127.0.0.1:18101 (alpha) 与 127.0.0.1:18102 (beta) 这一对实例上, 且共用同一份 runtime/shared/record.jsonl 与 events.log.
  场景之间存在跨实例的先后依赖: AC-003-1 要求记录文件尚不存在, AC-003-2 要求已有 alpha 条目, AC-004-1 要求日志里有 job-start, AC-005-1 要两侧材料; BR-001 要审的正是这两次追加产生的序号.
  若拆成 alpha 组与 beta 组, beta 组无法独立得出结论 (要等 alpha 先写记录), 这是流水依赖而非并行收益.
  每组独立准备都会重复同一份启动准备, 并为同一份共享记录制造写入交错, 收益小于协调成本.
- 当轮可用非作者验收者 3 人; 计划人数 1 人. 不用满 3 名: 组数只有 1 个, 且按 skill 规则 "拆开后仍互相占用同一份资源时, 只派一人".

## 证据目录与影响判断

- 目录: docs/changes/relay-board/evidence-v1-e398c7c/ (本轮新建, 不覆盖旧证据).
- 影响判断: 项目无 pytest.ini/pyproject/setup.cfg/tox.ini, README 的测试入口是从仓库根跑 pytest, 只发现 tests/test_app.py;
  app.py 只读写自身参数指向的 data-dir/shared-dir (本轮为 runtime/), 不读 docs/.
  证据目录只放 .md/.log/.txt/.png, 不放 test_*.py 或 app 可执行文件, 因此不会进入构建或测试发现, 也不进入运行输入. 结论: 可在仓库内 docs/ 下, 无需外置.
- runtime/ 与 .agents/ 已被 .gitignore 忽略; 验收开始时 runtime/ 只有空目录 alpha, beta, shared (record.jsonl 与 events.log 都不存在), 与 AC-003-1 前置一致.

## 验收者

- G1: 会话 i04-rp-v1, 本轮新开, 承接上面 10 项, 证据写入 evidence-v1-e398c7c/verifier-g1/.
