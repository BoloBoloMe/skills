# milestone-11 实施记录

依据: milestone-10/DECISIONS.md 的 D012, D014, D018, D019, D020, D021; 验收标准见 ../ACCEPTANCE.md 的 AC-11 (2026-11-01 经我确认, 并对三处落法作答: 全部内联, 8 阶段, milestone-07 由另一会话负责).

本轮改动:

- `workflow/diagnosing-bugs/` → `workflow/fix-bugs/` (git mv, 含 scripts/hitl-loop.template.py), frontmatter `name: fix-bugs`, `description: 修 bug 时调用.`
- `workflow/fix-bugs/SKILL.md`: 自述改为统一链条 + 本 skill 定位; 新增 分工 与 取证手段优先级 两节; 阶段链由 6 段改为 8 段 (5 制定修复方案, 6 执行修复与复验, 7 验证没改坏, 8 清理), 阶段 2 内部交叉引用随之改为阶段 6.
- `workflow/verification-contract/SKILL.md` 缺陷修复节: 做法句由"调用 diagnosing-bugs skill"改为按 fix-bugs 统一链条执行, 并写入手段优先级.
- `README.md`: 技能表行改名为 `fix-bugs`, 按字母序移到 `explain-diff` 与 `follow-the-money` 之间, 描述改为详细手法口径.

## 逐项证据

命令均在仓库根 `/home/bolo/Workspace/refactor-skill-around-verification` 执行.

- AC-11-01: `git mv workflow/diagnosing-bugs workflow/fix-bugs`; `rg -n "^name: " workflow/fix-bugs/SKILL.md` → `2:name: fix-bugs`. 目录与 name 一致; 脚本随目录迁移 (`ls workflow/fix-bugs/scripts` → `hitl-loop.template.py`), 正文两处 `scripts/hitl-loop.template.py` 相对路径仍成立.
- AC-11-02: 自述现文: "修 bug 的统一链条对所有 bug 一样, 不分大小: ... 本 skill 是这条链在难 bug 上的详细手法: 阶段 3, 4 ... 可按需跳过, 其余阶段只有理由明确时才允许跳过; 复现与验证没改坏的复核不可省." 原句"本 skill 是一种诊断手段, 不是必经步骤"已删 (`rg -n "不是必经步骤" workflow/` 无命中).
- AC-11-03: 链条五环原文一次写全 (SKILL.md 第 7 行), 并写明不分大小; 与 verification-contract 缺陷修复节新做法句同向, 无第二套阶段要求.
- AC-11-04: 阶段 5 含方案三要素 (改动点/影响范围/备份与回滚考虑), G1 六条触发条件逐条列出, 一句话判据原文在列.
- AC-11-05: 阶段 7 写明复核者未参与诊断与修复, 手段自选 "不强制跑自动化测试", 共享接口/数据格式/跨模块路径调 blast-radius, 结论写检查内容/手段/缺口且不宣称没改坏; 阶段 8 检查项含"阶段 7 复核报告已出".
- AC-11-06: 取证手段优先级节给出三级顺序与"不提交进仓库, 跑完清理", 收尾"不在代码库新增专用脚本".
- AC-11-07: 分工节给出调度方/诊断者/修复者/复核者四角, 诊断者交付根因报告与可复跑复现且说明环境真实程度, 简单 bug 允许合并诊断与修复, 复核者不可省.
- AC-11-08: `rg -n "diagnosing-bugs" --glob '!docs/changes/**' --glob '!docs/adr/**' .` → 退出码 1, 无命中. 剩余命中仅在 docs/changes 历史证据与 milestone-10 账本、docs/adr (原文不改). verification-contract 缺陷修复节与 README 行可在差异中核对.
- AC-11-09: `uv run python general/writing-for-llm/check_skill.py workflow/fix-bugs/SKILL.md` → `OK`; 同命令对 `workflow/verification-contract/SKILL.md` → `OK`. 未运行 sync-to-pi 等会改安装目录的同步, 未修改已安装 skills.

## 环境缺口

- `uv run python -m pytest -m "not e2e"` 在本容器起不来: `tests/conftest.py:236` 的 `pytest_sessionstart` 调用 `podman volume ls`, 容器内无 podman (`FileNotFoundError: podman`). 属环境限制, 与本轮改动无关; 本轮 AC 未要求跑 pytest, 也未据此宣称通过.
- 未做独立复核: 本节点 AC 未要求, 由终点验收 milestone-08 汇总裁决.
