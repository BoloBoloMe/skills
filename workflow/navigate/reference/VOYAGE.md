# 航行 Roadmap

navigate 的航行分支, 由 [SKILL.md 的调用模式](../SKILL.md#调用模式) 抵达. 共用的定义, 里程碑完成标准与收口产物见 [SKILL.md](../SKILL.md), 验收依据见 [ACCEPTANCE-GUIDE](../ACCEPTANCE-GUIDE.md).

我带着路线图进行调用. 始终用里程碑 id (形如 `milestone-01`) 指代 Milestone, 禁用裸编号. 每完成一轮 (单个 Milestone, 或一批并行的) 就停下来, 等待我的进一步提示.

## 航行步骤

1. **加载索引.** 经 `query` 读取 `destination`, `notes`, `milestones`. 不展开 Milestone 正文细节. 核对已确认的完成边界及固定验收 Milestone; 旧图已有 `task` 型验收时, 经守门脚本将其 `type` 改为 `acceptance`, 不再新增一个; 旧图没有验收节点时, 先核实旧图的目的地与完成边界是否经我确认; 不清楚就先问我, 再补上验收节点并接入所有已知的必要工作, 然后领取前沿.
   完成标准: 已知当前目的地, 完成边界和前沿 (前沿 = 未关闭且 `blocked_by` 全部已关闭的里程碑, 由数据推导); 验收已在终点前.
2. **选前沿认领.** 按顺序领取前沿的第一个 Milestone; 若前沿还有与它互相独立的 AFK Milestone, 一并领取: 独立即无阻塞关系, 不触碰同一文件, 这样的 AFK 工作串行排队纯属浪费, 并行是免费提速. 验收 Milestone 只有其他必要工作均完成, `unknown_seas` 已厘清且验收标准已确认时才能领取, 不能因阻塞列表暂时为空而提前领取. 每个领取的 Milestone 经脚本把 `status` 记为 `进行中`.
   完成标准: 领取的 Milestone 状态均已改为进行中; 每个未领取的前沿 Milestone 都能说出原因 (HITL, 不独立, 或验收尚未具备开始条件).
3. **放大解决.** 按 Milestone 类型分流, 需要时经 `query` 读取被阻塞者的上下文或已关闭 Milestone 的产物. 本轮领取了多个 → 每个 AFK Milestone 委派一名子代理同时开工; HITL 逐个与我进行. 验收按 [验收终点](../SKILL.md#验收终点) 向我逐项展示已确认标准和对应证据, 并记录我的决定; 未获我逐项确认前保持进行中.
   完成标准见 [Milestone](../SKILL.md#milestone).
4. **收口产物.** 按 [Milestone 节](../SKILL.md#milestone) 的收口产物归集本次产物, 链接写入 `milestones.<id>.artifacts`. 提交信息: 下游 skill 有规定则用其规定; 否则 `doc: <milestone-id> <产物简述>`.
   完成标准: 本 Milestone 产物已提交或已有可追溯链接; 无独立产物/非 git 仓库时已记录原因.
5. **记录关闭.** 经脚本写入 `close_summary` 摘要, 再把 `status` 置为 `已关闭`. 前沿随状态变化自动推导, 无需手工落盘.
   完成标准: 关闭摘要与状态已落地; 下一个 Milestone 可从前沿正确识别.
6. **探明海域.** 解决结果探明了某片海域 → 经脚本从未知海域移除该项并写成新 Milestone (需要阻塞时补 `blocked_by`), 将新 Milestone 加入验收的 `blocked_by` 与前沿; 发现 Milestone 在目的地之外 → 经脚本划入 `off_course`. 若新增工作或验收返工影响已进行中的验收, 保持验收未关闭, 补齐工作与证据后再请我确认.
   完成标准: `unknown_seas` 每项已判断; 该写成 Milestone 的已创建; 验收仍位于所有必要工作之后; 前沿和歧路已同步.
7. **提交路线图.** 提交 ROADMAP.json. 提交信息: `doc: 更新路线图 <milestone-id>`; 批量并行时列出本轮全部里程碑 id.
   完成标准: Roadmap 变更已提交; 或确认非 git 仓库而跳过; 验收已关闭才正式交付, 否则停下等待下一轮.
