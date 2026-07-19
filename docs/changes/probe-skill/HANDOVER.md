# 交接: probe-skill Backlog 遍历

## 你从哪里接手

本目录 (`docs/changes/probe-skill/`) 包含一张 **Probe Backlog** — 这是我刚画完的地图。你需要遍历它, 逐个解决 Probe Item, 消除不确定性, 最终落地为 `/workflow/probe/SKILL.md`。

## 当前状态

- Backlog 索引: `PROBE.md` — 已写好 Destination, Notes, 前沿列表, 迷雾, 范围外。
- 3 个 Item 已创建, 阻塞链: `01 → 02 → 03`。
- 决策记录: 尚无 (Decisions so far 为空)。

## 你要做什么

1. **加载 Backlog**: 读取 `PROBE.md` — 只需低分辨率索引, 不要一口气读全部 Item 正文。
2. **认领先锋**: 前沿目前只有 `PROBE-01` (Research, AFK)。你直接做。
3. **按需放大**: 读 `PROBE-01.md` 正文, 以及它引用的 wayfinder SKILL.md (路径: `../skills_from_mattpocock/skills/engineering/wayfinder/SKILL.md`)。
4. **解决**: PROBE-01 是 Research (AFK), agent 独立完成。读 wayfinder, 逐条标注依赖 tracker 的机制, 给出 markdown 替代方案建议。产出: 一份分析文件 (路径自定, 推荐 `PROBE-01-findings.md`)。
5. **记录 + 更新 Backlog**:
   - 将答案写入 PROBE.md 的 Decisions so far (一句话摘要 + 链接产物)。
   - 关闭 PROBE-01 (在文件头标注 `状态: 已关闭`)。
   - 检查 PROBE-02 是否解除阻塞 → 是, 移到前沿列表。
   - 检查迷雾是否可转化。
6. **停止** — 本次会话只解决 PROBE-01。

## 规则速查 (wayfinder 提炼, 适用于 markdown 载体)

- **一次一个**: 每次会话最多解决一个 Item。
- **先认领再工作**: 把 Item 文件头的 `状态: 进行中` 写上再开始。
- **以名指代**: 引用 Item 时始终用文件名 (`PROBE-01`), 不用裸编号。
- **答案在 Item, 不在 Backlog**: 完整答案留在 Item 的关闭评论或产物文件中; Backlog 只存一句话摘要 + 链接。
- **阻塞用文件头**: Item 文件用 `阻塞于: PROBE-NN` 声明依赖; 所有阻塞者关闭后自动解除。
- **前沿由 Backlog 维护**: 关闭 Item 后更新 `PROBE.md` 的前沿列表。

## 产物落盘

所有产物放在本目录下 (`docs/changes/probe-skill/`)。不要写到其他 feature 目录。
