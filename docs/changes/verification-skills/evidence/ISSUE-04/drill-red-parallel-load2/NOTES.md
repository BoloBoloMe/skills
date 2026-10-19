# drill-red-parallel-load2: 旧版技能的并行与证据共享失败演练 (TS-001 红, AC-006)

## 目的

证据起点: 确认改动前的 `workflow/verify-change/SKILL.md` (md5 `9ac67b01f3e9a5d3714e3292dcba6277`) 在"可隔离资源并行"和"共享原始材料"两处不成立, 且这次确实用 `/skill:verify-change` 点名加载.

## 待测版本与加载方式

- 源文件: `../logs/SKILL-v2-red.md`; 复制进夹具后 md5 相同.
- 加载: `/tmp/orchestra-04/red-parallel/.agents/skills/verify-change/` + 单行 `/skill:verify-change <任务>`; 指挥者会话首条消息含 `<skill name="verify-change" location="/tmp/orchestra-04/red-parallel/.agents/skills/verify-change/SKILL.md">`.

## 夹具与输入

- `/tmp/orchestra-04/red-parallel`, 目标提交 `e398c7cc7ca4e493d23689bee3cca1a34d306000`, 8 个场景 + 2 条审计 BR; 端口 18101/18102 各自独立, 共享 `runtime/shared/`.
- 可用非作者验收者 3 名.
- 会话: 指挥者 `i04-r1c` (`01a154a0-50dd-...`), 验收者 `i04-rp-v1` (`01a154a1-6ac1-...`).

## 实际结果

- `plan.md` 第 "分组与人数" 节: "全部 10 项只有一组 (G1), 派 1 名验收者依次做完"; 依据是场景固定在两个端口上并共用同一份记录, 把互不相同的端口与数据目录也算成同一份资源, 还判定"beta 组无法独立得出结论".
- `verifier-g1/results-g1.md`: 1 名验收者 22:48:05 启动实例, 按编号逐项跑完 10 项, 22:49:16 清理结束; 每项时间戳首尾相接, 没有并行区间.
- 没有"共用准备执行人", 没有"原始材料归属", 没有争用片段先后记录, 也没有跨验收者的材料移交: 截图与 report 由同一个人在 22:48:10-22:48:48 自己产生, 自己判读.

## 结论

- AC-006-1 不满足: 可隔离的两个端口与数据目录被并成 1 人串行.
- AC-006-2 不满足: 没有争用片段与顺序安排, 只读检查也不与写者并行.
- AC-006-3 不满足: 没有材料移交, 报告里没有产生者/版本/位置的交接字段.

## 限制

- 该轮指挥者在收尾时反复找已退出的验收者会话, 我作为操作者关闭了它的 tab 并保留已产出的 `plan.md` 与 `verifier-g1/`; 收尾阶段的空转不计入结论, 结论只取已落盘的计划与逐项结果.
