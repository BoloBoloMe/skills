# IMPACT-NOTES (m07-rev-imp 调查过程原件)

旧行为影响方向审核者的过程记录. 结论写在仓库内 `docs/changes/to-spec-grilling-and-chinese-ids/IMPACT-REVIEW.md`, 本文件只留过程, 命令与原件位置, 供复核重跑.

- 任务标识: m07-rev-imp. 会话身份: 独立审核者, 未参与本变更的实现与修复.
- 仓库: /home/bolo/Workspace/improve
- 评审起点: 9e8dd1dfe92b3b446c88c2cb8fce33cb0c67a77a
- 目标提交: 1e3c9844c6f2aea8df7135214c5225fcc2d3d766 (HEAD, `git rev-parse HEAD` 实取)
- diff 命令: `git diff 9e8dd1df...HEAD` (三点)
- commit 列表: `git log 9e8dd1df..HEAD --oneline` (12 条, 见下)
- 上轮报告: 无 (首轮). 产物根目录 `docs/changes/to-spec-grilling-and-chinese-ids/` 下首轮无 IMPACT-REVIEW.md, 本轮新建.
- 授权范围: 只读仓库, 只写 IMPACT-REVIEW.md. 全部实验文件放 /tmp/m07-rev-imp 与本证据目录, 不改产品源码, 测试与项目配置, 未提交.

## 1. 时间线与做了什么

| 时间 (UTC) | 动作 | 结果位置 |
| --- | --- | --- |
| 2026-11-27T04:5x | 取 HEAD, commit 列表, diff 范围与文件清单 | 本文件第 2 节 |
| 05:0x | 读产品差异: ac-draft.py / check-ac.py / to-spec 三文档 / verify-change 两文档 / navigate 两文档 / TEMPLATES / GHERKIN | 报告"代码依据"列 |
| 05:0x | 全仓搜索旧契约调用方与文档引用 (含 tests, general, pi, agent-prompts, README, docs/changes) | `logs/grep-contract-residue.log` |
| 05:0x | 从 9e8dd1df 抽出旧版工具对 (ac-draft/check-ac/check-tech/SKILL/GHERKIN/TEMPLATES/两个测试) 到 /tmp/m07-rev-imp/old | `git show 9e8dd1df:workflow/to-spec/<f>` 可复现 |
| 05:03 | 新旧工具对同一输入实跑对比 (契约差异, 跨版本产物兼容, 报错文案, 标记版本) | `logs/probe3.log`, `logs/marker-probe.log` |
| 05:04 | 按新版 SKILL.md 第 3 节命令清单端到端实跑 | `logs/recipe.log` |
| 05:05 | 既有检查: to-spec 测试, check_skill.py, 产品路径空白检查, 被组合技能差异 | `logs/pytest-to-spec.log`, `logs/check-skill.log`, `logs/diff-check-product.log`, `logs/capability-diff.log` |
| 05:05 | 已安装技能库对比 (`~/.agents/skills/to-spec`) 与旧副本对当前产物的实跑 | `logs/installed-copy.log`, `logs/installed-old-check-on-new-product.log` |
| 05:0x | 读证据根: issue-01/INDEX.md, run5 trace-* 原件, integration/run1/audit-renumbering.md | 引用见报告证据列 |

## 2. commit 列表 (git log 9e8dd1df..HEAD --oneline)

```
1e3c984 doc: milestone-07 评审门槛判定
7dea214 doc: milestone-07 证据归档
1bc15f6 doc: milestone-07 集成与执行记录
1dfc38a merge: issue/03
f9bfe71 merge: issue/02
9eedb3a merge: issue/01
1e64e6c docs: ISSUE-01: 记录最终提交与绑定复跑
3229525 docs: ISSUE-01: 填写交付证据与验收标准
8ce78be feat: ISSUE-01: 补回 GHERKIN 机检项的固定标记原文
fd26618 feat: ISSUE-01: 实施盘问确认与机械转正
34ae059 feat: ISSUE-02: 记录候选条文与基础检查证据
b260081 feat: ISSUE-02: 按验证方式盘问并核对方案
70ae157 feat: ISSUE-03: 对齐领航与 README 调用说明
775b5a2 doc: milestone-07 评审起点与证据根登记
```

## 3. 非产品文件的处理

`git diff --stat 9e8dd1df...HEAD` 共 1227 文件, 其中 `docs/changes/to-spec-grilling-and-chinese-ids/evidence/` 下 1212 个是证据归档, 按任务约定不计产品改动. 实际产品差异 15 文件:

```
workflow/navigate/ACCEPTANCE-GUIDE.md |  10 +-
workflow/navigate/SKILL.md            |  12 +-
workflow/to-spec/GHERKIN.md           |   6 +-
workflow/to-spec/SKILL.md             | 120 +--
workflow/to-spec/TEMPLATES.md         |   4 +-
workflow/to-spec/ac-draft.py          |  41 +-
workflow/to-spec/check-ac.py          |   8 +-
workflow/to-spec/tests/test_ac_draft.py   | 140 +--
workflow/to-spec/tests/test_ac_reading.py |  60 +--
workflow/verify-change/REVERIFY.md    |   6 +-
workflow/verify-change/SKILL.md       |  57 +-
README.md                             |  (条目与阶段说明)
docs/changes/to-spec-grilling-and-chinese-ids/*.md (本变更产物)
```

注: `workflow/to-spec/check-tech.py` 在 `git diff 9e8dd1df...HEAD` 中无差异 (空输出), 任务点里的 "check-tech 退出码与输出格式变化" 实为无变化, 已列报告已排除项.

## 4. 重跑方法

```bash
# 旧版工具对 (基准点快照)
mkdir -p /tmp/old && cd /home/bolo/Workspace/improve
for f in ac-draft.py check-ac.py check-tech.py GHERKIN.md SKILL.md TEMPLATES.md; do
  git show 9e8dd1df:workflow/to-spec/$f > /tmp/old/$f; done
mkdir -p /tmp/old/tests
for f in test_ac_draft.py test_ac_reading.py; do
  git show 9e8dd1df:workflow/to-spec/tests/$f > /tmp/old/tests/$f; done

# 契约差异与兼容探测 (需 gherkin-official, 判断错非零退出)
uv run --with gherkin-official python <本目录>/probe3.py
uv run --with gherkin-official python <本目录>/marker_probe.py
# 新版 SKILL 第 3 节命令清单端到端
uv run --with gherkin-official python <本目录>/recipe.py
```

`probe3.py` 的 H 段故意断言"仓库测试仍覆盖三条转正保护", 现状为 FAIL, 即本报告的覆盖回退发现; 其余段全 PASS. `probe3.py` 中 OLD 指向 `/tmp/m07-rev-imp/old`, 复跑时按上块重建该目录或改常量.

## 5. 原件清单 (本目录)

| 文件 | 内容 |
| --- | --- |
| `probe3.py` | 契约差异, stale 保护消失, --review 去处, 跨版本产物兼容, 报错文案, 检查顺序, 测试覆盖探测 |
| `marker_probe.py` | 确认标记版本兼容 (v1/v2/v9) |
| `recipe.py` | 按新版 SKILL.md 第 3 节命令逐条实跑 (check-ac/check-tech/promote/cp/cmp/正式机检) |
| `logs/probe3.log` | 上述探测原始输出 (probe3 exit=1, 因 H 段预期失败) |
| `logs/marker-probe.log` | v1/v2/v9 全部 exit 0 |
| `logs/recipe.log` | RECIPE OK |
| `logs/pytest-to-spec.log` | 39 passed + 39 subtests, exit 0 |
| `logs/check-skill.log` | to-spec / verify-change / navigate 三个 SKILL.md 均 OK |
| `logs/diff-check-product.log` | 产品路径 `git diff --check` exit 0 (证据目录内的空白告警除外) |
| `logs/capability-diff.log` | 被组合技能差异为空 |
| `logs/grep-contract-residue.log` | 旧契约残留清单 (仓库内 0 调用方, 历史文档 16 文件) |
| `logs/installed-copy.log` | 已安装技能库旧版文件与行号 |
| `logs/installed-old-check-on-new-product.log` | 旧版 check-ac 对当前 PRODUCT.md 报错 (exit 1) |
| `logs/pytest-ini.log` | 根 pytest.ini testpaths 不含 workflow/to-spec/tests |

## 6. 清理

- /tmp/m07-rev-imp 下运行产物 (`m07probe-*`, `recipe-*`, `marker-*`, `v2`, `dbg-*`) 已删; 仅留 `old/` (基准点快照, 可由第 4 节命令重建) 与探针脚本副本.
- 未在仓库内留临时文件; 未改产品文件; 未提交任何内容.
- 证据目录内新增仅本目录 (review1/), 不改旧轮次.