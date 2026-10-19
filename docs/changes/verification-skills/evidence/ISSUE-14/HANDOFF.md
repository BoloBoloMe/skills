# ISSUE-14 交接报告

## 交付了什么

只改了一份既有技能和新增本 ISSUE 证据目录:

- `workflow/tdd-as-orchestra/SKILL.md` 的执行循环:
  - 新增 `验收` 节点: 最后一轮评审没有新的须重构发现项后才能进入; 另起独立会话调用 `verify-change` 按已确认的 PRODUCT.md 组织验收; 实现指挥者不亲自使用 verify-change; 验收不塞进 code-review 或 explain-diff; 派发单要求写身份, 现场, 范围外, 输出契约与完成证据; 验收会话只发现和回传问题.
  - 新增 `验收回传`: 报告里的明确实现问题拆新 ISSUES, 回到重构/实现/提交/合并/评审, 评审再次收敛后重新派发验收; 环境/权限/标准/证据缺口按原停止条件汇报, 只阻塞依赖项, 不拆成重构 ISSUE, 缺口未处理前不生成收尾讲解页.
  - 更新 `评审` 与 `重构`: 评审结论决定下一步, 修复后仍要重新评审, 不能跳过评审直接验收.
  - 更新 `停止并汇报`: 派工单必须带本轮验收报告路径, 覆盖提交和逐项结果; 讲解页引用报告并显示未验证范围; 没有报告或还有未验证必验项时不生成讲解页, 不走正常收尾; 讲解页不等于关闭人工验收.
  - 执行循环开头加一句节点顺序约束: 评审没收敛不进入验收, 验收证据没齐不进入正常收尾.
- 新增 `docs/changes/verification-skills/evidence/ISSUE-14/`: 演练生成器, 现场原文, 真实会话 jsonl, 红绿对照与说明.
- 没有改 `PRODUCT.md` / `TECHNICAL.md` / `DECISIONS.md` / 既有 Spec; 没有改 `workflow/` 下其他技能或 `general/`; 没有写全局部署副本; 没有运行 `sync-to-pi.py`; 没有在 ISSUE 文件或 EXECUTION.md 勾选复选框; 演练目标项目没有改产品代码, 测试或配置 (只有证据目录新增和技能安装提交, 都在临时项目内).

## 每个验收标准对应的证据

| 验收标准 | 证据文件 |
| --- | --- |
| 最后一轮评审无新须重构项后, 停止前另开独立 verify-change 会话 (AC-014-1) | 红: `sessions/red-ts001/`, `logs/red-ts001-pane-final.txt` (只派 explainer, 0 次 verify-change). 绿: `sessions/green-ts001/` (指挥 `i14-green1` -> 验收指挥 `acc-wc-1` -> 验收者 `acc-wc-1-1`), `fixtures/green-ts001/acceptance-round-1/report.md` (3 项全通过, 绑定 `b519339`), `fixtures/green-ts001/prompt-acc-wc-1.txt` (验收派工单), `logs/green-ts001-pane-final.txt` |
| 实现指挥者不亲自使用 verify-change, 验收不塞进 code-review/explain-diff (AC-014-1) | `TS-001.md` 的绿演练链路; 指挥会话 bash 调用里没有执行产品入口, 也没有 `/skill:verify-change`; 验收报告与讲解页由另外的会话产生: `fixtures/green-ts001/page.html`, `logs/green-ts001-pane-final.txt` |
| 评审仍有须重构项时不启动验收 (AC-014-2) | `sessions/green-ts001-pending/` (4 轮评审, 每轮拆 ISSUE-02..05, 没有 verify-change); `logs/green-ts001-pending-git-log.txt`; `logs/green-ts001-pending-pane-final.txt`; 第 4 轮收敛 (`5e20d11`) 后才出现 `wc-accept-1` 与 `fixtures/green-ts001-pending/verify-round-1/report.md` |
| 代理产品检查通过即收尾但仍待用户确认, 不关闭正式验收 (AC-014-3) | `fixtures/green-ts001/acceptance-round-1/report.md` (全通过), `fixtures/green-ts001/page.html` (证据节引用 `verify/round-1/report.md`, 落 `b519339...`, 写明未验证范围), `logs/green-ts001-pane-final.txt` (指挥者声明仍需人工逐项确认); `fixtures/green-ts001-pending/page.html` 同规则 |
| 收尾引用验收报告路径, 覆盖提交和逐项结果 (AC-014-3) | `fixtures/green-ts001/prompt-explain-wc-1.txt` (派工单写了报告路径, `b519339db7d0d1ec723aef311fef7d17f2810bce`, 三项结论); 页面核对见 `TS-001.md` 绿演练第 6 条 |
| 无报告或必验项证据未齐不得正常收尾 (AC-014-3 / 收盘门) | v2 反例: `fixtures/green-ts002-gap-v2/page-v2.html` 在 AC-003-1 未验证时仍生成讲解页; v3 正确: `sessions/green-ts002-gap-only/`, `logs/green-ts002-gap-only-pane-final.txt` 明确"未派 explain-diff, 不宣布交付"; 红反例: `logs/red-ts002-pane-final.txt` |
| 验收发现实现问题拆新 ISSUES 回重构, 重新评审/验收 (AC-015-1) | `sessions/green-ts002-fix/`; `fixtures/green-ts002-fix/REPORT-round-1.md` (AC-002 失败); ISSUE-02 时间线在 `logs/green-ts002-fix-git-log.txt` (`3dbba65` 新增 ISSUE-02, `0a7166f` 修复, `9e578b2` 合并, `89ea49e` 评审第 2 轮); `fixtures/green-ts002-fix/REPORT-round-2.md` 绑定新提交 `89ea49e...` 并重新验收 |
| 环境缺口不进重构 (AC-015-2) | 绿主轮: `fixtures/green-ts002-fix/REPORT-round-2.md` 只有 AC-003-1 未验证, 没有对应 ISSUE (`git log` 里 ISSUE 只有 01/02); 绿缺口门: `fixtures/green-ts002-gap-only/REPORT.md` 与 `logs/green-ts002-gap-only-pane-final.txt` (实现问题 0 条, 不建 ISSUE, 缺口单列) |
| 验收节点调用 verify-change 而非另起一套 (范围约束) | 验收指挥会话按项目 `.agents/skills/verify-change/SKILL.md` 的 1-9 步执行: `fixtures/green-ts001/acceptance-round-1/plan.md` 标题 `verify-change 派工计划`, `report.md` 标题 `verify-change round-1`; `fixtures/green-ts001-pending/verify-round-1/report.md` 同结构. 没有出现自造的验收步骤或另一套判据 |

## 跑了哪些命令与退出码

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `uv run python general/writing-for-llm/check_skill.py workflow/tdd-as-orchestra/SKILL.md` | 0 | `workflow/tdd-as-orchestra/SKILL.md: OK` |
| 全角标点扫描 (U+3000-U+303F, U+FF01-U+FF5E, U+FFE0-U+FFEE), 对本 ISSUE 自写文档与脚本 (SKILL.md, README, TS-001, TS-002, setup-drills.sh, 自写夹具文件) | 0 命中 | 6 个自写文件全部 0 命中. 原始材料 (会话 jsonl, 指挥者终屏, 派工单, 演练生成报告, 讲解页) 里有全角标点, 按原样保留, 未改写 |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | 0 | `7 passed, 18 subtests passed` (`logs/pytest-writing-tests.log`) |
| `uv run --with pytest python -m pytest -m "not e2e" -q` | 1 | `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed in 275.45s`; 失败集合与 `evidence/BASELINE.md` 的 6 条完全一致, 没有新增失败 (`logs/pytest-full-not-e2e.log`) |
| `bash setup-drills.sh init` / `skill v1` / `skill v3` / `status` | 0 | 建 1 个模板与 8 个现场, 装入技能, 打印每个现场的 HEAD 与干净状态 |
| `herdr tab create` / `agent start` / `pane send-text` / `agent send-keys` / `agent read` / `agent wait` / `tab close` | 0 (个别命令被审批钩子拦下, 由我确认后继续) | 会话清单见 `README.md`; 收尾无本 ISSUE 存活会话与标签, 见 `logs/cleanup.txt` |
| `git clone` / `git log` / `git status` / `git rev-parse` (临时项目) | 0 | 每个现场工作区干净, 时间线可核对; 目标提交与验收报告绑定一致 |

## 会话与临时项目

- 8 轮演练, 会话名/pi session id/项目/起始提交见 `README.md` 的运行总表, 每个会话的原始 jsonl 在 `sessions/<轮次>/`.
- 临时项目都在 `/tmp/orchestra-14/`, 已整体删除; 现场由 `setup-drills.sh` 与 `fixtures/` 可重建. 删除与关会话记录在 `logs/cleanup.txt`.
- 宿主与版本: Ubuntu 26.04.1 LTS, pi 1.3.0, herdr 0.9.4, 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking high, `-a` 一次性信任; 明细 `logs/host-versions.txt`.

## 缺口, 风险与未验证项

1. **verify-change 的调用方式**: 三个验收指挥会话是按项目 `.agents/skills/verify-change/SKILL.md` 的步骤执行的, 不是用 `/skill:verify-change` 点名加载. 报告结构与 9 步流程能对上, 没有另造判据; 但"点名入口"下的行为没有在本次演练中证明.
2. **红 TS-002 不是干净失败**: 派工单为了交上一轮报告必须提到"独立验收", 旧技能下指挥者据此自行补了一轮验收, 所以"实现问题拆 ISSUE"这一点在红演练里没有失败. 决定性的红失败在收盘门: 有未验证必验项仍生成讲解页并按收尾处理. AC-015-1 的正面行为主要靠绿演练证明.
3. **绿主轮出了讲解页**: `green-ts002-fix` 的派工单提前写了"缺口不整轮停下等我", 等于预授权继续收尾, 与 v3 的收盘门冲突. 该轮不作为收盘门通过证据; 收盘门由 `ts002-gap-only` 单独证明. 这也是演练设计上的教训, 不是技能文本的失败.
4. **v2 快照是回推的**: 早期没单独保存 v2 文件, 后来按 v3 的两处替换反向还原, md5 与当时记录 (`60bcde71...`) 一致; 只用于对照说明, 不参与最终交付.
5. **夹具越界**: `ts002-gap-only` 场景暴露了夹具本身的标准缺口 (PRODUCT.md 的 AC-003 标了未定义的 @G-003; EXECUTION 任务图没有 AC-003 的 ISSUE). 指挥者按停止条件报告, 没有自行改标准; 这是夹具的限制, 不是被测技能的问题.
6. **样本与宿主**: 每个场景基本一次运行, 只覆盖一个模型, 一个宿主和一个加载入口. 不推论其他运行时, 其他模型或全局部署副本.
7. **未验证**: 其他缺口类型 (缺产品规则) 没有单独构造现场; 验收报告引用旧观察的适用性路径没有专门演练; 页面展示 (present) 的实际浏览器效果没有逐页人工核对, 只核对了 HTML 内容与指挥者终屏的交付地址.
8. **临时项目已删**: 不能直接从 /tmp 复跑, 但 `setup-drills.sh`, `fixtures/` 与全部原始材料保留, 结论不依赖临时项目存活.

## 提交哈希

- 实现与证据提交: `50ff4f30732d1796e74a8eaff9604d3ce2f6c488` (`feat: ISSUE-14: 在执行循环加入独立验收节点与验收回传`)
- 回填修改提交: 本文件最后修改所在的 docs 提交 (分支顶端, `git log -1` 可核对)
