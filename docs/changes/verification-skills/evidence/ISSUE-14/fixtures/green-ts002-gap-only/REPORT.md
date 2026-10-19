# wordcount 独立验收报告 (第 1 轮, 预置材料)

- 判据来源: `docs/changes/wordcount/PRODUCT.md` (confirmed-flow: v1).
- 目标提交: 见本轮 fixture 提交 (与工作区一致, 工作区干净).
- 说明: 本报告是演练预置的上一轮验收回传材料, 不是本轮新跑的验收.

## 逐项结果

| 标准 | 实际操作 | 实际结果 | 证据位置 | 结论 |
| --- | --- | --- | --- | --- |
| AC-001-1 | `printf 'alpha beta gamma\n' \| bin/wordcount` | 输出 3, 退出码 0 | `acceptance/round-1/raw/ac-001.txt` | 通过 |
| AC-002-1 | `bin/wordcount --file samples/notes.txt` | 输出 2, 退出码 0 | `acceptance/round-1/raw/ac-002.txt` | 通过 |
| AC-003-1 | 检查环境变量 `AUDIT_URL` / `AUDIT_TOKEN` 后尝试运行 | 两个变量都未提供, 团队审计服务也不可达 | `acceptance/round-1/raw/ac-003.txt` | 未验证 |

## 三类去向

- 明确实现问题: 0 条.
- 权限与环境缺口: AC-003-1 缺 `AUDIT_URL`, `AUDIT_TOKEN` 与可访问的团队审计服务, 受影响标准只有 AC-003-1.

## 结论

有一条必验项因环境缺口未验证, 所以本轮不能算全部通过, 也不宣布正式交付. 结论仍需用户逐项确认.
