# ISSUE-15 交接报告

## 交付了什么

只做最终整合审计, 不新增运行时行为. 两处允许的写入:

- `README.md` 工作流技能表新增 5 行索引: `benchmark-checklist`, `blast-radius`, `create-verification-skill`, `maintain-verification-skill`, `verify-change`. 只新增行, 没有删除或改写既有行.
- 新增 `docs/changes/verification-skills/evidence/ISSUE-15/`:
  - `AUDIT.md`: 最终审计报告, 逐项对应 AC-032, BR-009, BR-010, BR-011, 安全策略 (TC-105), 演练记录边界 (TC-106), 含全量 AC/BR 证据索引与 10 条缺口.
  - `audit_final.py`: 只读审计清单, 五项检查 (TS-001 到 TS-005). 只做机械项, 不伪造行为结果.
  - `red/red-audit-run1.log`: 先写的失败运行 (README 索引缺失 + 1 条措辞过严的假失败).
  - `green-audit-run2.log`: 修好后退出 0 的运行, WARN 3 项写入报告缺口节.
  - `logs/`: 机械检查原始输出 (六个技能 check_skill, 全角标点扫描, pytest 两项, BR-010 复跑机检, 差异范围, 部署目录只读检查, HANDOFF 路径引用抽样).

没有做的事 (范围外或本 ISSUE 明确不需要):

- 没有改五个技能, `tdd-as-orchestra`, `PRODUCT.md`, `TECHNICAL.md`, `DECISIONS.md`, ADR, 既有 Spec 或 `general/` 下任何技能.
- 没有运行 `sync-to-pi.py`, 没有写 `~/.agents`, `~/.pi` 或任何部署副本.
- 没有新开 agent 会话 (本 ISSUE 无真会话演练要求); 只读核对既有会话证据.
- 没有在 ISSUE 文件或 EXECUTION.md 勾选复选框; 没有提交/推送/开 PR/合并到主分支.

## 每个验收标准对应的证据

| 验收标准 | 证据文件 |
| --- | --- |
| README 索引包含五个新技能 | `AUDIT.md` 第 6 节; `logs/scope-git.log`; `audit_final.py` 的 `audit-scope` (README 只允许新增五行) |
| 五个技能通过 `check_skill.py`, frontmatter 与项目级配方证据合格 | `logs/check-skill-six.log` (六行 OK); `AUDIT.md` 第 4 节; 配方证据 `evidence/ISSUE-11/generated/*.md`, `evidence/ISSUE-12/*/final-recipe/SKILL.md`, `evidence/ISSUE-11/TC-017.md` |
| BR-010 许可, 固定 SHA, 差异记录齐全 | `logs/br010-provenance.log` (复跑 ISSUE-13 机检 `checks=50 failures=0`, 三份 LICENSE sha256 相同); `AUDIT.md` 第 5 节; `evidence/ISSUE-13/TS-001.md`, `TS-002-drill.md` |
| 最终差异只在允许范围, 权威输入字节不变, 未同步/部署 | `logs/scope-git.log` (改动目录统计, 冻结路径 diff 为空); `logs/deployment-readonly-check.log` (五个技能在 `~/.agents/skills` 与 `~/.pi/skills` 全部 absent); `AUDIT.md` 第 6 节 |
| 交付无自动 Git 动作; 安全策略与演练记录边界有证据 | `AUDIT.md` 第 3, 7, 8 节; `evidence/ISSUE-10/drill-green-011-012/plan.md` 与 `report.md`; `evidence/ISSUE-08/green-ts003/docs/green3.md`; `evidence/ISSUE-14/logs/green-ts002-fix-git-log.txt` |

## 跑了哪些命令与退出码

| 命令 | 退出码 | 结果 | 原始输出 |
| --- | --- | --- | --- |
| `uv run python docs/changes/verification-skills/evidence/ISSUE-15/audit_final.py` (加 README 索引前) | 1 | 2 FAIL (README 缺五行, ISSUE-07 措辞假失败), 3 WARN | `red/red-audit-run1.log` |
| 同上 (提交 README 后) | 0 | 五项 required 全通过, 3 WARN | `green-audit-run2.log` |
| `for s in verify-change create-verification-skill maintain-verification-skill blast-radius benchmark-checklist tdd-as-orchestra; do uv run python general/writing-for-llm/check_skill.py workflow/$s/SKILL.md; done` | 0 | 六行 `OK` | `logs/check-skill-six.log` |
| 全角标点扫描 (README.md 与本目录全部 md/py/log) | 0 命中 | `TOTAL_HITS 0` | `logs/fullwidth-scan.log` |
| `uv run python docs/changes/verification-skills/evidence/ISSUE-13/check-provenance-artifacts.py` | 0 | `checks=50 failures=0` | `logs/br010-provenance.log` |
| `sha256sum` 两个 LICENSE 与上游副本 | 0 | 三份同为 `bc957ca6...b200e` | `logs/br010-provenance.log` |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | 0 | `7 passed, 18 subtests passed` | `logs/pytest-writing-for-llm.log` |
| `uv run --with pytest python -m pytest -m "not e2e" -q` | 1 | `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed in 274.02s`, 失败集合与 `evidence/BASELINE.md` 逐条一致 | `logs/pytest-full-not-e2e.log` |
| `git diff --name-only ec9d55f..HEAD`, `git diff -- ...` 冻结路径, `git diff -- README.md` | 0 | 全部改动在允许路径; 冻结路径为空; README 只有新增行 | `logs/scope-git.log` |
| `~/.agents/skills` 与 `~/.pi` 只读检查 | 0 | 五个技能全部 absent; `~/.agents/skills` 仍 34 项 | `logs/deployment-readonly-check.log` |
| HANDOFF 路径引用抽样 (296 条) | 0 | 242 条直接可解析, 36 条需补轮次子目录, 3 条同名, 15 条需按实际文件名修正 | `logs/handoff-path-sample.log`, `logs/handoff-path-sample-suffix.log` |

## 会话与临时项目

- 本 ISSUE 不新开会话, 不建临时演练项目 (ISSUE 明确"没有真会话演练要求"). 没有会话名与提交渠道需要记录.
- 审计只读既有证据: 14 个 ISSUE 的会话原件, 加载来源记录, 演练项目 `git log`, 清理记录, 冻结路径 diff. 各 ISSUE 的宿主同为一台机器: Ubuntu 26.04.1 LTS x86_64, `pi 1.3.0`, `herdr 0.9.4`, 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`.
- 被审现场: 工作树 `/home/bolo/Workspace/skills/skills-v2.worktrees/ISSUE-15`, 分支 `issue/15`, 开工基线 `b378e4b`.
- 清理: 本 ISSUE 没有创建临时项目或会话, 因此无回收动作; 审计脚本使用系统临时目录 (`tempfile`) 存放配方 frontmatter 检查副本, 退出即删.

## 缺口, 风险与未验证项

1. 没有重跑 ISSUE-01..14 的真实会话 (临时项目已删, 会话已关), 审计核对的是可追溯性与一致性, 不是第二次行为验收.
2. ISSUE-06 顶层记录缺"提交渠道"字段 (TECHNICAL 证据固定记录要求), 见 `AUDIT.md` 第 9 节第 2 条.
3. ISSUE-04, 06, 08, 10 的顶层记录没有写"无自动 Git 动作"那一句; 同技能其他 ISSUE 有, 技能正文也有原文, 所以 AC-032 判定通过但记录一致性不齐.
4. HANDOFF 引用路径精度: 3 处真实漂移 (ISSUE-07 的 `source-record.md` 已被 ISSUE-13 改名, `ts003-wide-raw/report.md` 与 `merge.md` 实际文件名带 `ts003-wide-` 前缀), 另有 36 条省略中间目录. 材料都在, 只是路径写法不精确.
5. 未验证: 其他运行时/模型/宿主的加载与行为; `/skill:` 点名入口在 ISSUE-10 方法调用与 ISSUE-14 验收指挥中的行为; 性能数字的真实产品含义 (受控材料); 全局部署生效.
6. 已知工具缺口: `check_skill.py` 放行 description 里"冒号+空格", 会让 pi 整份丢弃技能 (ISSUE-01 事故). 修它属 `general/` 范围, 本 ISSUE 禁止改, 只记录.
7. 本报告是代理审计结论, 不关闭正式人工验收; ISSUE-10 的 `runtime/data` init 是否在批准范围内仍待用户复核.

## 提交哈希

- `8d715cb` `feat: ISSUE-15: 补齐 README 技能索引并新增只读最终审计清单` (README.md, audit_final.py, red 日志).
- 本文件与 `AUDIT.md`, `logs/`, `green-audit-run2.log` 随其后的 `docs: ISSUE-15: 最终审计报告与证据` 提交入库, 哈希以 `git log -1` 为准.
