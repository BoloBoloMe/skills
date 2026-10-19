# ISSUE-01 交接报告

## 交付了什么

- 新增 `workflow/verify-change/SKILL.md`, 单文件, 无 `reference/`. 内容是本 ISSUE 的第一切片: 单验收者单轮, 只把已确认 PRODUCT.md 的场景与业务规则当判据, 技术/执行材料只作操作线索, 计划勾选不作证据, 缺 PRODUCT.md 报缺口停止, 开始前核对目标提交与干净工作区, 证据目录按影响决定内放还是外置, 结论绑定起始提交, 收尾不声称整体工作区干净.
- 新增 `docs/changes/verification-skills/evidence/ISSUE-01/`: 演练记录, 6 份有效会话原始日志, 3 份会话产物副本, 夹具生成脚本, 1 份无效演练事故记录.
- 没有改 `PRODUCT.md` / `TECHNICAL.md` / `DECISIONS.md` / 既有 Spec, 没有改其他既有技能, 没有写全局部署副本, 没有运行 `sync-to-pi.py`, 没有勾选任何复选框.

## 提交

- `fb3d39707d880b8c76c90ce69c735f3983630657` 实现与证据 (本报告在其后的第二个提交里).

## 每个验收标准对应证据

| 验收标准 | 证据文件 |
| --- | --- |
| 缺已确认 PRODUCT.md 时报输入缺口并停止 | `evidence/ISSUE-01/drill-G1b2-green-missing-product.log` |
| 技术材料与计划勾选不进入产品通过条件 | `evidence/ISSUE-01/drill-G1a2-evidence-dir/REPORT.md` 的 "非产品判据事项" 节; `evidence/ISSUE-01/drill-G2c2-evidence-outside/v-2e868d1/REPORT.md` |
| 报告逐项结果绑定起始提交, 脏工作区不被验收 | 绑定: `drill-G1a2-evidence-dir/REPORT.md` 首段与逐项行; 拒绝: `drill-G2a2-green-dirty-stop.log` |
| 证据目录例外规则可观察, 不声称整体工作区干净 | 内放: `drill-G1a2-evidence-dir/REPORT.md` (证据目录 + 影响判断 + "除证据目录输出外, 源码与 Spec 未变"); 外置: `drill-G2c2-evidence-outside/v-2e868d1/REPORT.md` (含 `check_changes.py` 前后退出码 0 / 1) |

AC 到场景的对应关系, 夹具起始提交, 会话名与加载方式见 `evidence/ISSUE-01/README.md`.

## 跑了哪些命令与退出码

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md` | 0 | `OK` |
| `rg -n "[\x{ff0c}\x{ff1b}\x{ff1a}\x{ff01}\x{ff1f}\x{3001}\x{ff08}\x{ff09}]" workflow/verify-change/SKILL.md` | 1 | 无命中 (rg 无匹配时退出 1) |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | 0 | 7 passed, 18 subtests |
| `uv run --with pytest python -m pytest -m "not e2e" -q` (开工时与收工前各一次) | 1 | 均为 6 failed, 659 passed, 2 skipped: `general/present/tests/test_browser_session.py` 5 条 + `tests/test_mailbox_admin.py::test_pending_cap_drops_oldest` 1 条, 属既有失败, 本次未新增 |
| `bash evidence/ISSUE-01/setup-drills.sh <工作树>` | 0 | 生成 4 个临时 Git 项目; PRODUCT.md 经 `ac-draft.py preview/promote` 转正, `check-ac.py` 通过 |
| `herdr tab create` / `agent start` / `pane send-text` / `agent send-keys` / `pane read` / `tab close` | 0 | 见 `evidence/ISSUE-01/README.md` 会话一览 |

## 会话与临时项目

- 会话名: `v01-red1` (失败演练), `v01-r2b` (失败演练), `v01-g1a2`, `v01-g1b2`, `v01-g2a2`, `v01-g2c2` (通过). 全部已 `herdr tab close`.
- 临时项目: `/tmp/orchestra-01/{a-committed-clean,c-no-product,d-dirty,e-checked-docs}`, 起始提交见 `evidence/ISSUE-01/README.md`. 证据抄完后已删除, 可用 `setup-drills.sh` 重建.
- 宿主与版本: Ubuntu 26.04, herdr 0.9.4, pi 1.3.0, python3 3.14.7; 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking high, 启动带 `-a` 只做一次性项目信任.

## 缺口与风险

1. **机检缺口 (未修, 不在本 ISSUE 范围)**: `check_skill.py` 在 `disable-model-invocation: true` 时允许 `description` 含冒号, 但 pi 的 YAML 解析拒绝裸标量里的 "冒号+空格", 结果是技能静默不注册 (`[Skill conflicts]`). 本 ISSUE 因此把 description 改成不含该组合的写法, 并把事故与日志留在 `evidence/ISSUE-01/incidents/frontmatter-conflict/`. 建议后续 ISSUE 让 `check_skill.py` 一并拒绝这种写法.
2. **加载方式只覆盖一种**: 演练走项目 `.agents/skills/verify-change/` + `/skill:verify-change`; 其他运行时的加载方式未验证, 结论不外推到全局部署副本.
3. **角色隔离未实现**: 本切片没有非作者委派, 演练中被验会话就是验收者本人; 作者自验的隔离要求属 ISSUE-03/04, 本 ISSUE 不承诺.
4. **覆盖范围窄**: 夹具 PRODUCT.md 只有 2 个场景与 1 条审计 BR. 全量场景与审计 BR 逐项覆盖属 ISSUE-02, 本轮未验证.
5. **一次权限弹窗**: 第一批无效演练里有一个会话触发 `find /` 的全盘搜索确认弹窗并被拦下. 有效演练中没有再出现; 未改全局配置, 也未代答权限.
6. **未运行**: 未跑 `sync-to-pi.py`, 未提交/推送任何演练项目, 未做端到端 tdd-as-orchestra 接入 (ISSUE-14).
