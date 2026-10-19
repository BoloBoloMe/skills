# ISSUE-03 交接报告

## 交付了什么

- 在既有 `workflow/verify-change/SKILL.md` 上增量补齐两个切片 (不推翻 ISSUE-01/02 已实现部分):
  - AC-004 非作者委派: 指挥者只读输入, 定计划, 委派并核对材料, 不亲自运行被验产品, 不修复, 不给验收者补跑; 首次验收者必须是本轮新开, 未参与本次实现与修复, 不继承作者过程的子会话; "未参与"要用会话创建时间, 继承关系, 操作记录等可核对事实验证; 无可用非作者时报告受阻并停止, 不回退自验, 不让参与过实现或修复的会话顶替.
  - AC-005 场景组派工: 派工前把全部场景与审计 BR 映射到可独立验收的场景组; 人数取"有并行收益的组数"与"当轮可用非作者人数"的较小者; 单一不可分组, 或重复准备成本大于并行收益时只派一人; 不逐条 AC 开会话, 不为凑人数制造等待; 计划写明组划分, 收益与资源依据, 可用人数, 计划人数与只派一人的理由; 标准与委派权限满足时自主启动, 不例行等审批.
- 报告新增"派工记录"一节的要求 (场景组划分与人数依据, 每名验收者的会话标识, 创建时间, 承接标准, 未参与的可核对事实).
- 新增 `docs/changes/verification-skills/evidence/ISSUE-03/`: 3 个夹具生成脚本, 2 个红演练与 7 个绿演练的会话产出, 24 个 pi 会话原始记录, 会话摘要, 宿主事故与夹具修正记录.
- 没有改 `PRODUCT.md` / `TECHNICAL.md` / `DECISIONS.md` / 既有 Spec, 没有改其他既有技能, 没有写全局部署副本, 没有运行 `sync-to-pi.py`, 没有在 ISSUE 文件或 EXECUTION.md 勾选复选框, 没有改被验项目产品代码, 没有并行 / 证据共享 / 复验的行为承诺 (留给 ISSUE-04).

## 提交

- 实现与证据提交: `1c0f6c66b5882eaed42679b8545adb46b5828fff` (`feat: ISSUE-03: 非作者委派与场景组派工切片及演练证据`). 本报告与该次提交后的少量说明修正在其后的提交里.

## 每个验收标准对应证据

| 验收标准 | 证据 |
| --- | --- |
| 首次验收由未参与实现与修复的新会话执行 | `evidence/ISSUE-03/drill-G1-non-author/`: 指挥者 `i03-g1` 自己 `product_runs=0`, 新会话 `verifier-1` (`01a15426-b0b5-...`, 20:33:04) 承担 6 项并产出逐条原件, 报告写明创建时间晚于实现提交 20:26:12, 未继承实现过程, 无 `edit` / 无提交. 多名验收者的对照: `drill-G2-two-groups/` (2 名), `drill-G3-three-groups-3avail/` (3 名), `drill-G4-three-groups-2avail/` (2 名), `drill-G6-micro-groups/` (1 名). 失败对照: `drill-R1-non-author-red/` (旧版指挥者自己 `product_runs=2`, 不派会话). 指挥者与验收者的机械统计见 `evidence/ISSUE-03/SUMMARY.md`. |
| 无可用非作者时报告受阻, 不回退作者自验 | `evidence/ISSUE-03/drill-G7-blocked/`: `PLAN.md` 写可用非作者 0, 不派工; `REPORT.md` 结论"受阻", 6 项全部"未运行 / 未验证", 派工表"验收者: 无"; 该会话 `product_runs=0`, `prep_runs=0`, 没有运行产品也没有让 `i03-author` 顶替. 受控条件 (任务声明 + 只含实现会话的清单原文) 见 `drill-G7-blocked/NOTES.md`. |
| 派工按场景组与并行收益决定人数, 不逐条 AC 开会话 | `drill-G2-two-groups/` (4 项 / 2 会话, 计划 2), `drill-G3-three-groups-3avail/` (9 项 / 3 会话, 计划 3), `drill-G4-three-groups-2avail/` (9 项 / 2 会话, 计划 2 = min(2, 可用 2)), `drill-G5-single-group/` (3 项 / 1 会话), `drill-G6-micro-groups/` (3 项 / 1 会话). 各自 `PLAN.md` 含组划分, 收益与资源依据, 可用人数, 计划人数; 计划后直接启动 (`drill-G4-three-groups-2avail/dispatch-time.txt` 记 20:44:49, 无等待批准段落). 失败对照: `drill-R2-plan-red/` 旧版无计划, `product_runs=3`, `herdr_calls=0`. |
| 单一组或多组无收益时只派一人, 并写明依据 | 单一组: `drill-G5-single-group/plan.md` 写"1 组 1 人", 理由是同一份成品, 同一命令族, 无资源可隔离, 固定准备成本大于并行收益; 可用 3 人仍只派 1 人. 多组无收益: `drill-G6-micro-groups/PLAN.md` 写三条场景共用同一份 `dist/app.txt` 与同一个 `dist/` 路径, 拆开要各自重跑约 22 秒的 `prepare.sh` 并争用同一产物, 故只派 1 人; 可用 3 人只派 1 人. 第一版微检查夹具 (含审计 BR, 准备约 1 秒) 下技能派了 2 人, 已判定前提不成立并重做, 见 `incidents/fixture-corrections/README.md`. |

## 跑了哪些命令与退出码

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md` | 0 | `OK` |
| 全角标点扫描 (SKILL.md, 三个 setup 脚本, 本目录我写的说明文件) | 1 (无命中) | 无输出; 会话原始材料保留原样, 命中只在原始记录里 |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | 0 | 7 passed, 18 subtests passed |
| `uv run --with pytest python -m pytest -m "not e2e" -q` | 1 | 6 failed, 659 passed, 2 skipped, 103 deselected; 与 ISSUE-02 HANDOFF 记录的既有失败集合一致 (present 浏览器 5 条 + mailbox pending_cap 1 条), 未新增失败 |
| `bash setup-drills.sh <工作树> init` / `... apply-author-change 04be7dd...` | 0 / 0 | 建立 9 个基础夹具并把真实实现提交 cherry-pick 进去, 工作区干净 |
| `bash setup-heavy-drills.sh <工作树> 04be7dd...` | 0 | 建立 2 个批量型夹具, 工作区干净 |
| `bash setup-micro-drill.sh <工作树> 04be7dd...` | 0 | 建立微检查组夹具, `prepare.sh` 实测 22.24 秒 |
| `uv run python summarize-sessions.py` | 0 | 24 个会话写入 `SUMMARY.md` |
| `herdr tab create` / `agent start` / `pane send-text` / `agent send-keys` / `agent read` / `tab close` | 0 | 会话一览见 `README.md`; 关闭前列表存 `logs/agents-after-all.json`, `logs/tabs-after-all.json` |

## 会话与临时项目

- 有效会话: 实现 `i03-author`; 红演练 `i03-r1`, `i03-r2`; 绿演练指挥者 `i03-g1`, `i03-g2`, `i03-h1b`, `i03-h2`, `i03-g4`, `i03-g5b`, `i03-g6`; 验收者 `verifier-1`, `acc-a`, `acc-b`, `verifier-a`, `verifier-b`, `rev-greet`, `rev-count`, `rev-export`, `acc-verify`, `acc-g5b-1`. 会话 ID 与启动时间见 `README.md` 与 `SUMMARY.md`.
- 作废会话: 空任务重开的 `i03-g1` / `i03-g2` (第一版), 中途消失的 `i03-h1`, 只查模型的辅助会话; 见 `incidents/host-incidents/README.md`.
- 临时项目: `/tmp/orchestra-03/{author,red-delegation,red-plan,green-non-author,green-two-groups,green-single-group,green-micro-groups,green-blocked,heavy/...,micro2/...}`, 起始与目标提交见 `README.md` 夹具表. 证据抄完后已删除 (`ls /tmp | grep -c orchestra-03` 为 0).
- 宿主与版本: Ubuntu 26.04, herdr 0.9.4, pi 1.3.0, Python 3.14.7; 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking high, 启动带 `-a` 只做一次性项目信任, 未改全局配置.
- 加载方式: 项目 `.agents/skills/verify-change/` + `/skill:verify-change` 点名.

## 缺口与风险

1. **夹具前提靠人工判断**: 首版三组夹具工作量过小, 技能按收益只派 1 人; 首版微检查夹具带审计 BR 且准备只要 1 秒, 技能派了 2 人. 两次都判定为夹具不满足 AC 前提并重做 (批量场景 / 22 秒准备). 这说明"工作量足以独立承担"和"重复准备成本大于并行收益"没有数值门槛, 判断落在指挥者身上; 本轮未新增任何阈值, 也没测更多规模.
2. **"无可用非作者"是受控条件**: 用任务声明加只含实现会话的清单检验受阻分支, 不是真实配额系统耗尽; 正常路径由其余 7 次真实运行承接.
3. **平行样本少**: 每个场景基本只跑一次真实会话, 个别会话对材料完整性有来回补交 (G4); 未做重复抽样, 不能说明成功率.
4. **模型单一**: 全部演练用同一模型与思考深度, 未验证换模型后的稳定性; 个别指挥者为验收者另选了模型 (见 G6 的 `PLAN.md` 选型节), 这不在本 ISSUE 的判据内.
5. **宿主干扰**: `git-operation-gate` 会把含 `clean` 字样的命令误判为危险操作, 3 个演练被拦后由我作为操作者放行; 另有 1 个指挥会话启动后消失 (`i03-h1`) 需重建. 都是宿主或操作问题, 不是技能行为结论.
6. **一处记录缺口**: `micro2/micro-groups` 的初始提交哈希未单独保存 (临时项目删除时只留了目标提交), 初始化内容由 `setup-micro-drill.sh` 完整可重建, 目标提交的父提交即初始提交; 其余夹具的初始与目标提交都记在 `README.md` 夹具表.
7. **未验证**: 并行执行顺序, 证据共享, 复验 (ISSUE-04); tdd-as-orchestra 接入 (ISSUE-14); 其他运行时或全局部署下的加载与行为; 真实产品项目上的验收.
