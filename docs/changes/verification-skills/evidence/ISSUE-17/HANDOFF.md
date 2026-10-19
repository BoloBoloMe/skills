# HANDOFF ISSUE-17: create/maintain 写入授权与判据去重

## 交付了什么

- `workflow/create-verification-skill/SKILL.md`: 新增 `## 写入授权`. 调查默认只读, 写配方前把资源与对象, 操作, 清理, 验证办法整理成授权说明交用户批准; 同范围可复查, 换范围须新批准; 运行期临时数据单独授权; 派工单原样带批准范围, 子会话越界时停下报告, 生成者不替它扩权; 交付前实跑的派工单字段补上已批准的写入与清理范围.
- `workflow/maintain-verification-skill/SKILL.md`: 新增同样的 `## 写入授权` (改配方与复跑运行期数据的授权, 清理与验证办法, 子会话同范围); 新子会话复跑一节补上"已批准的写入与清理范围"; `## 分类漂移` 段首改为判据以本节为准, 参考文件只放样例.
- `workflow/maintain-verification-skill/reference/drift-classification.md`: 删除与正文重复的三类判据表与判据顺序, 只保留具体混淆样例与证据底线, 并指向 `SKILL.md` 的判据.
- `docs/changes/verification-skills/evidence/ISSUE-17/`: 4 次真实 pi 会话 (create/maintain 各红绿) 与 2 次子会话实跑的原始记录, 夹具脚本, 源差异, 机械检查输出.
- 未改 `PRODUCT.md` / `TECHNICAL.md` / `DECISIONS.md` / 既有 Spec / 其他技能 / `general/`; 未写全局部署副本; 未运行 `sync-to-pi.py`; 未勾选任何复选框; 未提交或推送临时项目.

## 验收标准对应

| 验收标准 | 证据 |
| --- | --- |
| 两个技能写入前都要求说明范围与清理并等批准, 有演练证据 | `TC-TS001.md`; 原始: `raw/create-red/` (1 条用户消息, 0 处批准, 直接写配方), `raw/create-green/` (授权说明 + 停下, 批准后才写), `raw/maint-red/` (直接改 3 个配方), `raw/maint-green/` (授权说明 + 停下, 批准后才改); 汇总 `raw/red-no-approval.txt`, `raw/green-approval-sequence.txt`; 子会话同范围: `raw/green-child-scope.txt`, `raw/create-green/create-green-pane.txt` 派工单, `raw/maint-green/maint-green-pane.txt` 派工单 |
| 判据只保留一份, 有 diff 证据 | `TC-TS002.md`; `raw/red-source-duplication.txt` (两处各写一份), `raw/green-criteria-location.txt` (判据只在 SKILL.md, 参考文件无判据表/顺序), `diffs/drift-classification.patch`, `diffs/maintain-skill.patch`; 行为未退化: `raw/maint-green/maint-green-step1-pane.txt` 分类表, `raw/green-criteria-usage.txt` |

## 跑过的命令与退出码

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `uv run python setup-drills.py --skill create-verification-skill` / `--skill maintain-verification-skill` | 0 | 生成并提交临时夹具, 起始提交与工作区干净状态见 `README.md` |
| `uv run python general/writing-for-llm/check_skill.py workflow/create-verification-skill/SKILL.md` | 0 | `SKILL.md: OK` |
| `uv run python general/writing-for-llm/check_skill.py workflow/maintain-verification-skill/SKILL.md` | 0 | `SKILL.md: OK` |
| `rg` 全角标点扫描 (改动后技能与本次新增文档, 排除 `raw/` 会话原文) | 1 | 无命中, 见 `punct-scan.txt` |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | 0 | 7 passed, 18 subtests passed, 见 `pytest-writing-for-llm.txt` |
| `uv run --with pytest python -m pytest -m "not e2e" -q` (改动前基线) | 1 | 6 failed, 659 passed, 2 skipped, 103 deselected, 见 `baseline-fast-suite.txt` |
| 同上 (改动后) | 1 | 6 failed, 659 passed, 2 skipped, 103 deselected, 失败集合与基线相同, 见 `full-fast-suite-after.txt` |
| `git diff` 导出三个源文件差异 | 0 | `diffs/{create-skill,maintain-skill,drift-classification}.patch` |
| herdr 建 tab, 启动会话, 提交任务, 读屏 | 0 | 四条主会话与子会话操作, 命令见 `README.md` 与各 pane 快照 |

## 会话与临时项目

- 待测源: `workflow/create-verification-skill/` 与 `workflow/maintain-verification-skill/`, 分支 `issue/17`. 红态 = 基点 `5c21b0b` 原文件, 绿态 = 本次改动后文件 (哈希见 `README.md`).
- 宿主: Ubuntu 26.04.1 LTS, Linux 7.0.0-31-generic; pi 1.3.0; herdr 0.9.4; 模型 `cli/deepseek-v4.1-flash-expires-on-0910`; thinking high; 启动加 `-a`; 未改全局配置.
- create 红态: `/tmp/orchestra-17/proj-create` @ `e24732f88de6e03e96aeaa45a98ee215717ffa23`, 会话 `i17-create-red` (tab `w1E:t3Z`), 子会话 `verifier-notes`.
- create 绿态: 同一项目重置 @ `36dd3b7c6ef04a4b86db0256d49cffd65f47b9c1`, 会话 `i17-create-green` (tab `w1E:t46`), 子会话 `verify-notes-runner` (tab `w1E:t4C`).
- maintain 红态: `/tmp/orchestra-17/proj-maintain` @ `d55efe28acfbfc3cbdb246933354b30790d87a66`, 会话 `i17-maint-red` (tab `w1E:t41`), 自行开 6 轮子会话.
- maintain 绿态: 同一项目重置 @ `7e4ba17cb708f8f4c05de62994cb6a1a0aa22a43`, 会话 `i17-maint-green` (tab `w1E:t4G`), 子会话 `verifier` (tab `w1E:t4H`).
- 收尾: 四条演练 tab 已关闭, `herdr agent list` 里没有 `orchestra-17` 相关会话; 红态遗留的 `/tmp/verify-notes-cli-*` 与 `/tmp/verifier-task*.txt` 记录后删除; `/tmp/orchestra-17` 整个删除.

## 缺口, 风险与未验证项

1. 演练只覆盖 pi 1.3.0 + 一个本机模型 + herdr 0.9.4 的组合, 结论不推广到其他运行时或全局部署副本.
2. 子会话越界靠事后发现: maintain 绿态里子会话一轮写了批准范围外的 `/tmp/.verify_*` 草稿文件, 维护者按派工单要求它删净后重跑, 但事前没有自动拦截; create 绿态生成者自己也写过一份 `/tmp/verify-notes-cli-dispatch.md` 派工草稿 (落在批准范围的目录外), 之后随临时目录一起不存在. 属于残余风险, 不声称批准机制能完全阻止越界写入.
3. 夹具只有单项目, 单实例, 无端口; 没有覆盖共享实例, 端口争用, 权限不足等运行时分支, 这些分支只按技能文字约束, 没有真实演练.
4. "判据单一来源" 的验证是结构证据 (两处摘录 + 去重 diff) 加一次真实分类会话, 不是无限次行为采样; 以后改文案仍需保持参考文件不重写判据.
5. 绿态 create 的子会话在报告里写"证据随临时目录删除, 关键输出抄进报告"; 证据目录只在会话转录里可复核, 没有独立留存文件, 这与配方"取证要活过清理"的要求有差距, 属夹具生成物的质量问题, 不影响本 ISSUE 的写入授权结论.
6. 机械检查中的全角标点扫描只覆盖改动后的技能与本次新增文档, `raw/` 下是会话原文 (含全角标点与英文), 按证据保真保留, 不参与扫描.

## 提交哈希

- 本分支 `issue/17`, 提交信息 `feat: ISSUE-17: create/maintain 技能补写入批准并去重 drift 判据`.
- 交付提交哈希见随后一个 docs 提交的回填; 本文件无法包含自身提交哈希, 分支最终 HEAD 以 `git log -1` 为准.
